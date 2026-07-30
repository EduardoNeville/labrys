#!/bin/bash
set -e

# ==============================================================================
# Labrys Bootstrap Script — run on the new GPU server after transferring files
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "  Labrys — Linear A Decipherment Project"
echo "  Bootstrap Script"
echo "=============================================="
echo ""

# ── 1. System checks ─────────────────────────────────────────────────────────
echo "[1/6] Checking system..."

OS="$(uname -s)"
echo "  OS: $OS"

# Python
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    echo "  ❌ Python not found. Install Python 3.10+ first."
    exit 1
fi
echo "  Python: $($PYTHON --version)"

# NVIDIA GPU
if command -v nvidia-smi &> /dev/null; then
    echo "  GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)"
    echo "  VRAM: $(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1) MiB"
else
    echo "  ⚠️  nvidia-smi not found — GPU not detected. ML Phase 4 will not work."
    echo "     Install NVIDIA drivers first."
fi

echo ""

# ── 2. Verify project files ──────────────────────────────────────────────────
echo "[2/6] Checking project files..."

REQUIRED=(
    "pipeline/__init__.py"
    "pipeline/models.py"
    "pipeline/database.py"
    "pipeline/unicode_utils.py"
    "data/database/lineara_full.db"
    "data/corpus/linear_a_inventory.csv"
    "requirements.txt"
    "pyproject.toml"
)
MISSING=0
for f in "${REQUIRED[@]}"; do
    if [ ! -f "$f" ]; then
        echo "  ❌ Missing: $f"
        MISSING=$((MISSING + 1))
    fi
done
if [ "$MISSING" -eq 0 ]; then
    echo "  ✅ All required files present"
else
    echo "  ⚠️  $MISSING files missing — some features may not work"
fi
echo ""

# ── 3. Create virtual environment ────────────────────────────────────────────
echo "[3/6] Setting up Python virtual environment..."

if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
    echo "  ✅ Created venv/"
else
    echo "  ✓ venv/ already exists"
fi

source venv/bin/activate
echo "  ✅ Virtual env activated"
echo "  Python: $(python3 --version)"
echo "  pip: $(pip --version | cut -d' ' -f2)"
echo ""

# ── 4. Install dependencies ──────────────────────────────────────────────────
echo "[4/6] Installing Python packages..."

echo "  → Upgrading pip..."
pip install --quiet --upgrade pip setuptools wheel

echo "  → Installing core dependencies..."
pip install --quiet -r requirements.txt

echo "  → Installing PyTorch with CUDA support..."
pip install --quiet torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121

echo "  → Installing ML/Phase 4 dependencies..."
pip install --quiet transformers datasets tokenizers accelerate sentencepiece
pip install --quiet scikit-learn pandas matplotlib seaborn tqdm

echo "  ✅ All packages installed"
echo ""

# ── 5. Verify installation ───────────────────────────────────────────────────
echo "[5/6] Verifying installation..."

python3 -c "
import sys
sys.path.insert(0, '.')
print('  stdlib:', end=' ')
try:
    import sqlite3, csv, json, math
    print('✅')
except: print('❌')

print('  pipeline:', end=' ')
try:
    from pipeline.models import Inscription
    from pipeline.database import LinearADatabase
    from pipeline.unicode_utils import validate_mapping
    from pipeline.cli import cli
    print('✅')
except Exception as e:
    print(f'❌ {e}')

print('  Unicode mapping:', end=' ')
try:
    from pipeline.unicode_utils import validate_mapping
    errors = validate_mapping()
    print(f'✅ ({len(errors)} errors)')
except Exception as e:
    print(f'❌ {e}')

print('  PyTorch:', end=' ')
try:
    import torch
    print(f'✅ v{torch.__version__}')
    print(f'  CUDA available: {torch.cuda.is_available()}')
    if torch.cuda.is_available():
        print(f'  GPU: {torch.cuda.get_device_name(0)}')
        print(f'  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
except Exception as e:
    print(f'❌ {e}')

print('  transformers:', end=' ')
try:
    import transformers
    print(f'✅ v{transformers.__version__}')
except Exception as e:
    print(f'❌ {e}')
"

echo ""

# ── 6. Run demo ──────────────────────────────────────────────────────────────
echo "[6/6] Running pipeline demo..."

if python3 demo.py 2>&1 | tail -5; then
    echo "  ✅ Demo pipeline runs successfully"
else
    echo "  ⚠️  Demo had issues — check output above"
fi

echo ""
echo "=============================================="
echo "  Bootstrap Complete!"
echo "=============================================="
echo ""
echo "  Activate:  source venv/bin/activate"
echo "  Explore:   python3 -m pipeline.cli --help"
echo "  DB stats:  python3 -m pipeline.cli db stats data/database/lineara_full.db"
echo ""
echo "  Next: Begin Phase 4 ML Decipherment"
echo "=============================================="
