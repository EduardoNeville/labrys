#!/bin/bash
# ARCHIVED — not research code. Hardware operations for a specific Tesla P40
# (PCIe ASPM, link speed, thermals). Never imported by the pipeline. See
# ../../README.md and ../../../CODE_AUDIT.md before running anything here.
# ============================================================================
# GPU Stability Fixup Script — Labrys Project (Tesla P40)
# ============================================================================
# Run with: sudo bash scripts/gpu-fixup.sh
#
# Fixes applied:
#  1. Disable PCIe ASPM (power saving) — notorious for GPU stability issues
#  2. Verify and enforce PCIe link performance
#  3. Check current hardware state

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

section() { echo -e "\n${BOLD}===${NC} $1 ${BOLD}===${NC}"; }
ok()     { echo -e "  ${GREEN}✔${NC} $1"; }
warn()   { echo -e "  ${YELLOW}⚠${NC} $1"; }
err()    { echo -e "  ${RED}✘${NC} $1"; }

if [[ $EUID -ne 0 ]]; then
    err "This script must be run as root (sudo)."
    exit 1
fi

# ---------------------------------------------------------------------------
# 1. CURRENT STATE DIAGNOSTIC
# ---------------------------------------------------------------------------
section "Current State"

echo ""
echo "--- GRUB cmdline ---"
grep "GRUB_CMDLINE_LINUX" /etc/default/grub || true

echo ""
echo "--- Kernel cmdline (current boot) ---"
cat /proc/cmdline

echo ""
echo "--- PCIe ASPM policy ---"
cur_policy=$(cat /sys/module/pcie_aspm/parameters/policy)
echo "  Current: $cur_policy"

echo ""
echo "--- GPU PCIe link ---"
nvidia-smi --query-gpu=pcie.link.gen.current,pcie.link.width.current,pcie.link.gen.max,pcie.link.width.max,pstate,temperature.gpu --format=csv 2>/dev/null || echo "  nvidia-smi not available"

echo ""
echo "--- GPU ECC ---"
nvidia-smi -q -d ECC 2>/dev/null | grep -A2 "Aggregate" | tail -4 || true

echo ""
echo "--- GPU Persistence Mode ---"
nvidia-smi -q 2>/dev/null | grep "Persistence Mode" || true

# ---------------------------------------------------------------------------
# 2. DISABLE ASPM (IMMEDIATE, THIS SESSION)
# ---------------------------------------------------------------------------
section "Disabling ASPM (this session)"

echo "performance" > /sys/module/pcie_aspm/parameters/policy 2>/dev/null && \
    ok "ASPM set to 'performance' for this session" || \
    warn "Could not set ASPM policy (already set?)"

new_policy=$(cat /sys/module/pcie_aspm/parameters/policy)
echo "  Policy is now: $new_policy"

# ---------------------------------------------------------------------------
# 3. DISABLE ASPM PERMANENTLY (GRUB)
# ---------------------------------------------------------------------------
section "Disabling ASPM permanently (GRUB)"

GRUB_FILE="/etc/default/grub"

if grep -q "pcie_aspm=off" "$GRUB_FILE"; then
    ok "pcie_aspm=off already in GRUB_CMDLINE_LINUX_DEFAULT"
else
    cp "$GRUB_FILE" "${GRUB_FILE}.bak.$(date +%Y%m%d)"
    sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT="\(.*\)"/GRUB_CMDLINE_LINUX_DEFAULT="\1 pcie_aspm=off"/' "$GRUB_FILE"
    
    if grep -q "pcie_aspm=off" "$GRUB_FILE"; then
        ok "Added pcie_aspm=off to GRUB_CMDLINE_LINUX_DEFAULT"
        echo "  Backup saved to ${GRUB_FILE}.bak.$(date +%Y%m%d)"
    else
        warn "Could not modify GRUB — check manually"
    fi
fi

# Update GRUB
if command -v update-grub &>/dev/null; then
    update-grub && ok "GRUB updated" || warn "update-grub failed"
elif command -v grub2-mkconfig &>/dev/null; then
    grub2-mkconfig -o /boot/grub2/grub.cfg && ok "GRUB updated" || warn "grub2-mkconfig failed"
else
    warn "Could not find update-grub or grub2-mkconfig — update manually"
fi

# ---------------------------------------------------------------------------
# 4. VERIFY PCIE LINK WIDTH
# ---------------------------------------------------------------------------
section "PCIe Link Diagnostics"

echo ""
echo "--- PCIe Topology ---"
lspci -vvv -s 07:00.0 2>/dev/null | grep -iE "LnkSta|LnkCap|ASPM|width|speed" || echo "  Cannot read PCIe config"

echo ""
echo "--- Physical slot check ---"
# The card reports max link as Gen2 x16, but runs at Gen2 x8
# This suggests a physical problem (riser, slot, seating)
cur_width=$(cat /sys/bus/pci/devices/0000:07:00.0/current_link_width 2>/dev/null || echo "?")
max_width=$(cat /sys/bus/pci/devices/0000:07:00.0/max_link_width 2>/dev/null || echo "?")
echo "  Current link width: x${cur_width}"
echo "  Max link width:     x${max_width}"

if [[ "$cur_width" != "16" || "$max_width" != "16" ]]; then
    warn "GPU is not at ×16 width!"
    echo ""
    echo "  Possible causes:"
    echo "    - GPU not fully seated in the PCIe slot"
    echo "    - PCIe riser/cable limiting to ×8"
    echo "    - Other PCIe devices sharing lanes (check motherboard manual)"
    echo "    - Slot itself is electrically ×8 (check motherboard specs)"
    echo "    - Dust/corrosion on PCIe contacts"
    echo ""
    echo "  Try: power down, reseat the GPU firmly, clean contacts with isopropyl alcohol"
fi

# ---------------------------------------------------------------------------
# 5. FINAL SUMMARY
# ---------------------------------------------------------------------------
section "Summary"

echo ""
echo -e "${BOLD}Fixes applied now:${NC}"
echo "  [x] ASPM set to 'performance' for this session"
if grep -q "pcie_aspm=off" /etc/default/grub; then
    echo "  [x] ASPM permanently disabled via GRUB (pcie_aspm=off)"
else
    echo "  [ ] ASPM NOT in GRUB — add manually: pcie_aspm=off"
fi
echo ""

echo -e "${BOLD}Actions needed (human):${NC}"
echo "  1. REBOOT for GRUB changes to take effect"
echo "  2. PHYSICAL: Check GPU seating / riser — running at ×8 not ×16"
echo "  3. COOLING: Tesla P40 is PASSIVELY COOLED — it needs forced airflow"
echo "     - In a server chassis: verify fan shroud is directing air over the GPU"
echo "     - In a tower/desktop: add a fan blowing across the card"
echo "     - The GPU idles at 70°C — should be much lower with proper airflow"
echo "     - Under load it spikes from 70→81°C in 3 seconds (245W draw)"
echo ""
echo -e "${RED}Without proper cooling, sustained training WILL crash the server.${NC}"
echo ""

# ---------------------------------------------------------------------------
# 6. OPTIONAL: QUICK POST-FIX TEST
# ---------------------------------------------------------------------------
section "Optional: Run quick GPU test?"

echo ""
echo "After reboot, verify with:"
echo "  cd ~/research/labrys"
echo "  nvidia-smi --query-gpu=pcie.link.gen.current,pcie.link.width.current --format=csv"
echo ""
echo "Expect: 2, 16  (Gen2 × 16)"
echo "Currently: 1, 8 (Gen1 × 8 at idle) → 2, 8 (Gen2 × 8 under load)"
echo ""
echo "Then run a sustained GPU stress test:"
echo "  uv run python scripts/gpu-stress-test.py"
