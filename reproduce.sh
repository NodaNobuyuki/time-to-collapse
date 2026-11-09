#!/usr/bin/env bash
# Regenerate every derived table and figure from the raw logs in data/raw_runs/.
# Output goes to ./reproduced/, which mirrors the repo layout. Nothing shipped is modified.
# Needs no GPU and no LLM. Usage: bash reproduce.sh   (PYTHON=/path/to/python to override)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
PY="${PYTHON:-python}"
OUT=reproduced

rm -rf "$OUT"
mkdir -p "$OUT/data" "$OUT/results" "$OUT/norm_evolution"

# runs_manifest.csv records where GovSim wrote each log on the machine that ran it.
# In this repo the logs are in data/raw_runs/<run>/, so build a working copy that points there.
"$PY" - "$OUT/runs_manifest.csv" <<'EOF'
import csv, pathlib, sys

with open("data/runs_manifest.csv", newline="") as f:
    rows = list(csv.DictReader(f))
for r in rows:
    run = f"{r['condition']}_{r['model'].replace(':', '-')}_s{r['seed']}"
    r["results_dir"] = str(pathlib.Path("data/raw_runs", run).resolve())
with open(sys.argv[1], "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
EOF
MANIFEST="$OUT/runs_manifest.csv"

"$PY" scripts/prior_work/extract_survival.py --manifest "$MANIFEST" --out "$OUT/data/survival.csv"
"$PY" scripts/prior_work/km_analysis.py "$OUT/data/survival.csv" --outdir "$OUT/results/km" >/dev/null
"$PY" scripts/weekend/contagion_analysis.py --manifest "$MANIFEST" --outdir "$OUT/results/contagion" >/dev/null
"$PY" scripts/weekend/month4_checks.py --survival "$OUT/data/survival.csv" \
    --contagion-dir "$OUT/results/contagion" --outdir "$OUT/results/month4_checks" >/dev/null
"$PY" scripts/weekend/dump_conversations.py "$OUT" "$OUT/data/conversations" >/dev/null

# analyze_norm_evolution.py resolves its paths from its own location, so run a copy inside reproduced/.
cp norm_evolution/analyze_norm_evolution.py "$OUT/norm_evolution/"
"$PY" "$OUT/norm_evolution/analyze_norm_evolution.py" >/dev/null

"$PY" scripts/verification/paper_numbers.py --root "$OUT" --raw-runs data/raw_runs \
    --outdir "$OUT/results/verification"

# Compare the regenerated tables and logs with the shipped ones. PNGs are skipped: their bytes
# depend on the matplotlib build.
echo
same=0; diff=0
while IFS= read -r f; do
    rel="${f#"$OUT"/}"
    if cmp -s "$f" "$rel"; then
        same=$((same + 1))
    else
        diff=$((diff + 1)); echo "DIFFERS: $rel"
    fi
done < <(find "$OUT" -type f \( -name '*.csv' -o -name '*.log' -o -name '*.md' \) ! -path "$MANIFEST" | sort)
echo "Compared with shipped outputs: $same identical, $diff different."
[[ $diff -eq 0 ]]
