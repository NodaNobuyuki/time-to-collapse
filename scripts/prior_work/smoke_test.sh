#!/usr/bin/env bash
# smoke_test.sh — one timed GovSim fishing run against local Ollama.
# Goal: confirm the pipeline works end to end and measure minutes per run.
#
# Usage:  bash smoke_test.sh [model] [experiment] [seed]
#   model       Ollama model tag            (default qwen2.5:7b)
#   experiment  GovSim experiment id        (default fish_baseline_concurrent_universalization)
#   seed        integer                     (default 1)
set -euo pipefail

GOVSIM_DIR="${GOVSIM_DIR:-$HOME/govsim-hackathon/GovSim}"
MODEL="${1:-qwen2.5:7b}"
EXPERIMENT="${2:-fish_baseline_concurrent_universalization}"
SEED="${3:-1}"
TEMPERATURE="${TEMPERATURE:-0.7}"

cd "$GOVSIM_DIR"
# shellcheck disable=SC1091
source .venv/bin/activate

export OPENAI_BASE_URL="${OPENAI_BASE_URL:-http://localhost:11434/v1}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-ollama}"   # Ollama ignores it, the client requires one
export WANDB_MODE=offline
export TOKENIZERS_PARALLELISM=false

curl -sf "${OPENAI_BASE_URL}/models" >/dev/null \
  || { echo "Ollama is not answering at $OPENAI_BASE_URL — run: sudo systemctl start ollama"; exit 1; }

GROUP="smoke_${EXPERIMENT}_s${SEED}"
echo "[smoke] model=$MODEL experiment=$EXPERIMENT seed=$SEED temperature=$TEMPERATURE"
START=$(date +%s)

python3 -m simulation.main \
  experiment="$EXPERIMENT" \
  llm.path="local-$MODEL" \
  llm.is_api=true \
  llm.temperature="$TEMPERATURE" \
  seed="$SEED" \
  group_name="$GROUP" \
  2>&1 | tee "smoke_${SEED}.log"

END=$(date +%s)
MIN=$(( (END - START) / 60 ))
echo
echo "[smoke] wall clock: ${MIN} min"
echo "[smoke] results: $(ls -d simulation/results/fishing_*/"$GROUP"/* 2>/dev/null | head -1)"
echo "[smoke] GPU check during the run should have shown 100% GPU in: ollama ps"
