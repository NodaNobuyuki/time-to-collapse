#!/usr/bin/env bash
# setup_govsim_local.sh — prepare GovSim to run against a local Ollama server (Arch Linux, AMD GPU).
# Prior work for the Swarm Alignment Hackathon (built before Nov 6, 2026) — declare it in the report.
#
# Usage:  bash setup_govsim_local.sh [install_dir]
# Default install_dir: ~/govsim-hackathon
set -euo pipefail

INSTALL_DIR="${1:-$HOME/govsim-hackathon}"
GOVSIM_REPO="https://github.com/giorgiopiatti/GovSim.git"

log() { printf '\n[setup %s] %s\n' "$(date +%H:%M:%S)" "$*"; }

# ---------------------------------------------------------------------------
# 1. System packages (Arch). Ollama with ROCm backend + uv for Python 3.11.
# ---------------------------------------------------------------------------
log "Checking system packages"
need_pkgs=()
command -v git    >/dev/null || need_pkgs+=(git)
command -v uv     >/dev/null || need_pkgs+=(uv)
command -v ollama >/dev/null || need_pkgs+=(ollama-rocm)
if ((${#need_pkgs[@]})); then
  log "Installing: ${need_pkgs[*]} (sudo)"
  sudo pacman -S --needed --noconfirm "${need_pkgs[@]}"
fi

# ---------------------------------------------------------------------------
# 2. Ollama service: RX 6650 XT is gfx1032, not officially supported by ROCm.
#    The usual workaround is to present it as gfx1030 (10.3.0).
# ---------------------------------------------------------------------------
DROPIN=/etc/systemd/system/ollama.service.d/override.conf
if [[ ! -f "$DROPIN" ]] || ! grep -q HSA_OVERRIDE_GFX_VERSION "$DROPIN"; then
  log "Writing Ollama systemd override (HSA_OVERRIDE_GFX_VERSION=10.3.0, 1 parallel request)"
  sudo mkdir -p "$(dirname "$DROPIN")"
  sudo tee "$DROPIN" >/dev/null <<'EOF'
[Service]
Environment="HSA_OVERRIDE_GFX_VERSION=10.3.0"
Environment="OLLAMA_NUM_PARALLEL=1"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_KEEP_ALIVE=30m"
Environment="OLLAMA_CONTEXT_LENGTH=8192"
EOF
  sudo systemctl daemon-reload
fi
sudo systemctl enable --now ollama
sudo systemctl restart ollama
sleep 3
groups | grep -qw render || log "WARNING: your user is not in the 'render' group: sudo usermod -aG render,video $USER (then log out/in)"

# ---------------------------------------------------------------------------
# 3. Clone GovSim + PathFinder submodule.
# ---------------------------------------------------------------------------
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"
if [[ ! -d GovSim ]]; then
  log "Cloning GovSim"
  git clone --recurse-submodules "$GOVSIM_REPO"
fi
cd GovSim
git submodule update --init --recursive
GOVSIM_COMMIT=$(git rev-parse HEAD)
PF_COMMIT=$(git -C pathfinder rev-parse HEAD)

# ---------------------------------------------------------------------------
# 4. Patch PathFinder: model names starting with "local-" go to an
#    OpenAI-compatible endpoint (Ollama), read from OPENAI_BASE_URL.
# ---------------------------------------------------------------------------
log "Patching pathfinder/pathfinder/loader.py for local- models"
python3 - <<'PY'
import pathlib, sys
p = pathlib.Path("pathfinder/pathfinder/loader.py")
src = p.read_text()
marker = "# [hackathon-patch] local OpenAI-compatible endpoint"
if marker in src:
    print("  already patched"); sys.exit(0)
old = 'def get_api_model(name, seed):\n'
new = (
    'def get_api_model(name, seed):\n'
    f'    {marker}\n'
    '    if name.lower().startswith("local-"):\n'
    '        return OpenAIAPI(name[len("local-"):], seed)\n'
)
if old not in src:
    sys.exit("  ERROR: get_api_model signature not found; PathFinder changed, patch manually")
p.write_text(src.replace(old, new, 1))
print("  patched")
PY

# ---------------------------------------------------------------------------
# 4b. Patch GovSim's W&B logger: it hard-codes mode="online", which ignores
#     WANDB_MODE=offline and fails with a 401 when no API key is set.
# ---------------------------------------------------------------------------
log "Patching simulation/utils/logger.py to respect WANDB_MODE"
python3 - <<'PY'
import pathlib, sys
p = pathlib.Path("simulation/utils/logger.py")
src = p.read_text()
marker = "# [hackathon-patch] respect WANDB_MODE"
if marker in src:
    print("  already patched"); sys.exit(0)
old = 'mode="online" if not debug else "disabled",'
new = f'mode=os.environ.get("WANDB_MODE", "online") if not debug else "disabled",  {marker}'
if src.count(old) != 1:
    sys.exit("  ERROR: wandb.init mode line not found; GovSim changed, patch manually")
src = src.replace(old, new, 1)
# Offline W&B runs have an empty run.name, so results would land directly in
# results/<experiment>/<group>/ instead of a run subfolder that run_batch.sh expects.
old2 = "        self.run_name = run.name\n"
new2 = '        self.run_name = run.name or f"offline-{run.id}"  # [hackathon-patch] offline runs have no name\n'
if src.count(old2) != 1:
    sys.exit("  ERROR: run_name line not found; GovSim changed, patch manually")
p.write_text(src.replace(old2, new2, 1))
print("  patched")
PY

# ---------------------------------------------------------------------------
# 5. Python 3.11 venv. CPU-only torch: the GPU work happens inside Ollama;
#    torch is only needed for the sentence-transformers embedding model.
# ---------------------------------------------------------------------------
log "Creating Python 3.11 venv with uv"
uv venv --python 3.11 .venv
# shellcheck disable=SC1091
source .venv/bin/activate
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install -r pathfinder/requirements.txt
uv pip install -r requirements.txt
uv pip install "numpy<2" pandas matplotlib lifelines

# ---------------------------------------------------------------------------
# 6. Record versions (goes into the report's Methodology + prior-work note).
# ---------------------------------------------------------------------------
log "Writing environment.txt"
{
  echo "date: $(date -Iseconds)"
  echo "govsim_commit: $GOVSIM_COMMIT"
  echo "pathfinder_commit: $PF_COMMIT (patched: local- prefix)"
  echo "ollama: $(ollama --version 2>&1 | tail -1)"
  echo "python: $(python --version)"
  echo "kernel: $(uname -r)"
  echo "gpu: $(lspci | grep -iE 'vga|display' | head -1)"
  uv pip freeze
} > environment.txt

log "Done. Next: pull a model, then run smoke_test.sh"
echo "  ollama pull qwen2.5:7b"
echo "  ollama run qwen2.5:7b 'hello' && ollama ps   # must show 100% GPU"
