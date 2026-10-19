#!/usr/bin/env python3
"""ARCHIVED — not research code. Synthetic matmul load for GPU stability.
Never imported by the pipeline. See ../../README.md and ../../../CODE_AUDIT.md.

GPU Stress Test — Sustained ML Training Load
============================================
Tests GPU stability under progressively heavier loads.
Monitors temperature, power, and PCIe link during test.

Usage:
    uv run python scripts/gpu-stress-test.py              # default (5 min)
    uv run python scripts/gpu-stress-test.py --duration 300  # 5 minutes
    uv run python scripts/gpu-stress-test.py --size 8192 --iterations 200
"""

import torch
import time
import argparse
import subprocess
import os
import sys
import signal

def gpu_query(fields):
    """Query nvidia-smi for the given comma-separated fields."""
    try:
        result = subprocess.run(
            ["nvidia-smi", f"--query-gpu={fields}", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return "?, ?, ?, ?, ?, ?"

def main():
    parser = argparse.ArgumentParser(description="GPU sustained stress test")
    parser.add_argument("--duration", type=int, default=300, help="Total test duration in seconds")
    parser.add_argument("--size", type=int, default=8192, help="Matrix size for stress (default 8192)")
    parser.add_argument("--iterations", type=int, default=500, help="Matmul iterations per batch")
    args = parser.parse_args()

    if not torch.cuda.is_available():
        print("ERROR: CUDA not available")
        sys.exit(1)

    device = torch.cuda.get_device_name(0)
    mem_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"GPU: {device} ({mem_gb:.1f} GB)")
    print(f"Duration: {args.duration}s | Matrix: {args.size}x{args.size} | Iters/batch: {args.iterations}")
    print(f"{'Time':>8s}  {'Temp':>5s}  {'Pwr':>6s}  {'Util':>5s}  {'PCIe':>7s}  {'PState':>6s}  Status")
    print("-" * 70)

    start = time.time()
    batch = 0
    max_temp = 0
    errors = 0
    crashed = False
    
    def handler(signum, frame):
        nonlocal crashed
        crashed = True
    signal.signal(signal.SIGALRM, handler)

    while time.time() - start < args.duration:
        batch += 1
        batch_start = time.time()
        status = "OK"
        
        try:
            signal.alarm(30)  # If any batch hangs >30s, it's a problem
            a = torch.randn(args.size, args.size, device="cuda")
            b = torch.randn(args.size, args.size, device="cuda")
            
            for _ in range(args.iterations):
                c = torch.mm(a, b)
            
            torch.cuda.synchronize()
            signal.alarm(0)
            
            del a, b, c
            torch.cuda.empty_cache()
            
        except RuntimeError as e:
            signal.alarm(0)
            errors += 1
            status = f"ERROR: {str(e)[:50]}"
            if "out of memory" in str(e).lower():
                status = "OOM"
            torch.cuda.empty_cache()
        
        batch_time = time.time() - batch_start
        elapsed = time.time() - start
        
        # Query GPU state
        q = gpu_query("temperature.gpu,power.draw,utilization.gpu,pcie.link.gen.current,pcie.link.width.current,pstate")
        parts = q.split(", ")
        temp = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
        max_temp = max(max_temp, temp)
        
        pcie = f"{parts[3]}x{parts[4]}" if len(parts) > 4 else "?"
        pstate = parts[5] if len(parts) > 5 else "?"
        
        print(f"{elapsed:7.0f}s  {parts[0]:>5s}°C  {parts[1]:>6s}W  {parts[2]:>5s}%  {pcie:>7s}  {pstate:>6s}  {status} " + 
              (f"(batch {batch_time:.1f}s)" if batch_time > 1.0 else ""))
        
        if temp > 90:
            print(f"\n  ⚠ CRITICAL: GPU at {temp}°C! Past slowdown threshold (92°C). Stopping.")
            break
        if errors > 3:
            print(f"\n  ⚠ Too many errors ({errors}). Stopping.")
            break

    # Final report
    elapsed = time.time() - start
    print("\n" + "=" * 70)
    print(f"TEST COMPLETE: {elapsed:.0f}s | Batches: {batch} | Errors: {errors}")
    print(f"Max GPU temperature: {max_temp}°C")
    
    if max_temp >= 92:
        print("⚠ WARNING: GPU hit thermal slowdown zone (≥92°C)")
        print("  → The server NEEDS better GPU cooling before running real training")
    elif max_temp >= 85:
        print("⚠ CAUTION: GPU temperature high. Consider improving airflow.")
    else:
        print("✓ Temperature stayed within safe range.")

    if errors == 0:
        print("✓ Zero compute errors.")
    else:
        print(f"⚠ {errors} errors occurred.")
    
    if crashed:
        print("✗ GPU appeared to hang during test — PCIe/ASPM is likely the issue")

if __name__ == "__main__":
    main()
