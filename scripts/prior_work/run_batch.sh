#!/usr/bin/env bash
# run_batch.sh — run the experiment grid (conditions x seeds), resumable.
# Each finished run is appended to runs_manifest.csv; re-running the script
# skips runs already marked "ok", so a crash or reboot loses at most one run.
#
# Usage:  bash run_batch.sh <seed_start> <seed_end> [model]
#   e.g.  bash run_batch.sh 1 15            # Carlos's machine
#         bash run_batch.sh 101 115         # Alan's machine (disjoint seeds!)
set -uo pipefail

GOVSIM_DIR="${GOVSIM_DIR:-$HOME/govsim-hackathon/GovSim}"
SEED_START="${1:?seed_start}"
SEED_END="${2:?seed_end}"
MODEL="${3:-qwen2.5:7b}"
TEMPERATURE="${TEMPERATURE:-0.7}"
MAX_ROUNDS="${MAX_ROUNDS:-12}"   # same horizon for every condition, so curves are comparable
MACHINE="${MACHINE:-$(hostname)}"

# condition_label:govsim_experiment_id
CONDITIONS=(
  "baseline:fish_baseline_concurrent"
  "universalization:fish_baseline_concurrent_universalization"
  "newcomer_univ:fish_perturbation_outsider_universalization"
)

cd "$GOVSIM_DIR"
# shellcheck disable=SC1091
source .venv/bin/activate
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-http://localhost:11434/v1}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-ollama}"
export WANDB_MODE=offline
export TOKENIZERS_PARALLELISM=false

MANIFEST=runs_manifest.csv
[[ -f $MANIFEST ]] || echo "condition,experiment,model,seed,temperature,max_rounds,machine,status,minutes,results_dir,started_at" > "$MANIFEST"
mkdir -p batch_logs

# Interleave conditions inside each seed: if the weekend runs out, every
# condition has roughly the same number of runs.
for SEED in $(seq "$SEED_START" "$SEED_END"); do
  for entry in "${CONDITIONS[@]}"; do
    COND="${entry%%:*}"; EXP="${entry#*:}"
    MODEL_TAG="${MODEL//[:\/]/-}"
    GROUP="${COND}_${MODEL_TAG}_s${SEED}"

    if grep -q ",${SEED},.*,ok,.*/${GROUP}/" "$MANIFEST" 2>/dev/null; then
      echo "[batch] skip $GROUP (done)"; continue
    fi

    # A run interrupted by a stop/crash leaves a partial log_env.json; remove it so the
    # results-dir lookup below can't pick the stale folder. (Added Nov 7, during the hackathon.)
    rm -rf simulation/results/fishing_*/"$GROUP"

    echo "[batch] $(date +%H:%M) start $GROUP"
    STARTED=$(date -Iseconds); T0=$(date +%s)
    python3 -m simulation.main \
      experiment="$EXP" \
      llm.path="local-$MODEL" \
      llm.is_api=true \
      llm.temperature="$TEMPERATURE" \
      seed="$SEED" \
      group_name="$GROUP" \
      experiment.env.max_num_rounds="$MAX_ROUNDS" \
      > "batch_logs/${GROUP}.log" 2>&1
    RC=$?
    MIN=$(( ($(date +%s) - T0) / 60 ))
    RDIR=$(ls -d simulation/results/fishing_*/"$GROUP"/* 2>/dev/null | head -1)
    if [[ $RC -eq 0 && -f "$RDIR/log_env.json" ]]; then STATUS=ok; else STATUS=failed; fi
    echo "${COND},${EXP},${MODEL},${SEED},${TEMPERATURE},${MAX_ROUNDS},${MACHINE},${STATUS},${MIN},${RDIR},${STARTED}" >> "$MANIFEST"
    echo "[batch] $(date +%H:%M) end   $GROUP status=$STATUS ${MIN}min"
  done
done
