# Migration Guide: Labrys Linear A Project

## Overview

Moving the entire Labrys project to a new server with a **Tesla P40 GPU** for Phase 4 (ML Decipherment).
Total project size: ~15 MB (source + data).

---

## Step 1: Prerequisites on New Server

### System Requirements
- **OS**: Ubuntu 20.04+ / Debian 11+ (or any Linux with NVIDIA drivers)
- **GPU**: NVIDIA Tesla P40 (24GB VRAM) — sufficient for BERT-style models, smaller transformers
- **Storage**: At least 5 GB for project + Python venv + model caches
- **RAM**: 16 GB minimum, 32 GB recommended
- **CUDA**: 11.8+ (Tesla P40 supports up to CUDA 12.x with compute capability 6.1)

### Install NVIDIA Drivers & CUDA

```bash
# Check if drivers exist
nvidia-smi

# If not, install (Ubuntu/Debian example)
sudo apt update
sudo apt install -y nvidia-driver-535 nvidia-utils-535
# Reboot after driver install

# Install CUDA 12.1 (compatible with P40)
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run
sudo sh cuda_12.1.0_530.30.02_linux.run --toolkit --silent

# Add to PATH
echo 'export PATH=/usr/local/cuda-12.1/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

### Verify GPU

```bash
nvidia-smi
# Should show: Tesla P40, ~22930MiB
python3 -c "import torch; print(torch.cuda.get_device_name(0)); print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')"
```

---

## Step 2: Transfer the Project

### Method A: Git Clone (Recommended)

Push to remote and clone on the new server:

```bash
# On old server (if you have a remote)
git remote add origin <your-git-remote-url>
git push -u origin master

# On new server
git clone <your-git-remote-url> labrys
cd labrys
```

### Method B: Rsync (Direct Transfer)

```bash
# On new server, from old server:
rsync -avz --progress \
  --exclude='.git/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='data/raw/sigla/' \
  user@old-server:/path/to/labrys/ \
  /path/to/labrys/
```

### What to Transfer (Essential)

| Item | Size | Required? | Notes |
|------|------|-----------|-------|
| `pipeline/` | ~800 KB | ✅ Essential | All 26 Python modules |
| `data/database/lineara_full.db` | 3.6 MB | ✅ Essential | Master corpus (can be rebuilt) |
| `data/analysis/` | ~9 MB | ✅ Recommended | All pre-computed analysis outputs |
| `data/corpus/` | 132 KB | ✅ Essential | Text inventory CSV |
| `docs/` | ~200 KB | ✅ Recommended | Schema, TEI ODD, examples |
| `*.md` reports | ~300 KB | ✅ Recommended | Phase reports |
| `pyproject.toml` | small | ✅ Essential | Project metadata |
| `requirements.txt` | small | ✅ Essential | Python dependencies |
| `data/raw/sigla/` | 2 MB | ⬜ Optional | Raw source data (can be re-fetched) |
| `__pycache__/` | ~500 KB | ❌ Skip | Platform-specific bytecode |

To regenerate `lineara_full.db` from scratch on the new server:
```bash
python3 ingest_lineara.py
```

To regenerate the raw SigLA data:
```bash
curl -O https://raw.githubusercontent.com/mwenge/lineara.xyz/master/items_analysis/inscriptions.json
curl -O https://raw.githubusercontent.com/mwenge/lineara.xyz/master/items_analysis/supplement.json
```

---

## Step 3: Set Up Python Environment

```bash
cd /path/to/labrys

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install project dependencies (CPU-compatible first)
pip install -r requirements.txt

# Add ML dependencies for Phase 4
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers datasets tokenizers accelerate sentencepiece
pip install scikit-learn pandas matplotlib seaborn tqdm
pip install wandb mlflow  # optional: experiment tracking
pip install jupyter jupyterlab  # optional: notebooks
```

### Verify the Environment

```bash
python3 -c "
import sqlite3, csv, json, math, sys
print('✓ stdlib modules OK')
from pipeline.models import Inscription
print('✓ pipeline.models OK')
from pipeline.database import LinearADatabase
from pipeline.unicode_utils import validate_mapping
errors = validate_mapping()
print(f'✓ Unicode mapping valid: {len(errors)} errors')
import torch
print(f'✓ PyTorch {torch.__version__}')
print(f'✓ CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✓ GPU: {torch.cuda.get_device_name(0)}')
    print(f'✓ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
from transformers import AutoModel
print('✓ transformers OK')
print()
print('=== Environment Ready ===')
"
```

---

## Step 4: Verify Data Integrity

```bash
source venv/bin/activate
cd /path/to/labrys

# 1. Check database
python3 -m pipeline.cli db stats data/database/lineara_full.db
# Expected: inscriptions: 1719, signs: 11018, unique_signs: 312, sites: 62

# 2. Verify Unicode mapping
python3 -m pipeline.cli unicode validate
# Expected: 0 errors

# 3. Run the full demo
python3 demo.py

# 4. Run a quick analysis to verify pipeline works
python3 pipeline/positional_analysis.py --min-occurrences 5
# Expected: completes in <30s

# 5. Verify Phase 3 outputs exist
ls data/analysis/linguistic/falsification_matrix.csv
ls data/analysis/linguistic/phase3_synthesis.md

# 6. Verify Phase 5 outputs exist
ls data/analysis/comparative/refined_phonetic_grid.csv
ls data/analysis/comparative/phase5_synthesis.md
```

---

## Step 5: Set Up for Phase 4 ML Work

### Directory Structure for ML Artifacts

```bash
mkdir -p models/checkpoints
mkdir -p models/experiments
mkdir -p data/analysis/ml
```

### PyTorch with Tesla P40 Optimizations

The P40 has compute capability 6.1 (Pascal). Add this to any training script:

```python
# Optimizations for Tesla P40
torch.backends.cudnn.benchmark = True
torch.set_float32_matmul_precision('medium')  # TF32 where supported

# Mixed precision (P40 supports fp16 natively)
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()
```

### Memory Notes for P40 (24 GB)

| Model Size | Batch Size | Feasible? |
|-----------|------------|-----------|
| BERT-base (110M params) | 32-64 | ✅ Yes |
| BERT-large (340M params) | 16-32 | ✅ Yes |
| GPT-2 small (124M) | 16-32 | ✅ Yes |
| Custom transformer (4-6 layers) | 64-128 | ✅ Yes |
| Cross-attention decip. model | 32-64 | ✅ Yes |

---

## Step 6: Migration Checklist

### Pre-Flight (Before Transfer)
- [ ] `git status` shows clean working tree
- [ ] All pipeline modules compile (`python3 -m py_compile pipeline/*.py`)
- [ ] Database file exists and has correct stats
- [ ] Rsync/git remote configured

### On New Server
- [ ] NVIDIA drivers installed (`nvidia-smi` works)
- [ ] CUDA 12.1 installed
- [ ] Python 3.10+ available
- [ ] Project cloned/rsynced
- [ ] Virtual environment created and activated
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `pip install torch --index-url https://download.pytorch.org/whl/cu121` succeeds
- [ ] `python3 -c "import torch; print(torch.cuda.is_available())"` → `True`
- [ ] `python3 demo.py` runs without errors
- [ ] `python3 -m pipeline.cli db stats data/database/lineara_full.db` returns correct stats
- [ ] `python3 pipeline/positional_analysis.py` completes in <30s
- [ ] Phase 3/5 output files are present
- [ ] `models/checkpoints/` and `data/analysis/ml/` directories created

---

## Quick-Start Script

Save this as `bootstrap.sh` on the new server:

```bash
#!/bin/bash
set -e

echo "=== Labrys Bootstrap ==="

# 1. Clone or rsync
if [ ! -d "labrys" ]; then
    echo "Clone the repo first, then run this from inside labrys/"
    exit 1
fi
cd labrys

# 2. Python venv
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 3. Install deps
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers datasets tokenizers accelerate sentencepiece
pip install scikit-learn pandas tqdm

# 4. Verify
echo ""
echo "=== Verification ==="
python3 -c "
import torch, sqlite3, sys
sys.path.insert(0, '.')
from pipeline.unicode_utils import validate_mapping
errors = validate_mapping()
print(f'Unicode: {len(errors)} errors')
print(f'CUDA: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
print('✓ All OK')
"

echo ""
echo "=== Bootstrap Complete ==="
echo "Run: source venv/bin/activate"
echo "Then: python3 demo.py"
```
