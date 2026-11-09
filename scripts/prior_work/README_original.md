# Time to Collapse — local GovSim kit

Prior work for the Swarm Alignment Hackathon (Apart Research, Nov 6–8, 2026).
Everything in this folder was written before Nov 6 and must be declared as prior work.

## Order of operations

| Step | Command | Done when |
|---|---|---|
| 1. Setup | `bash setup_govsim_local.sh` | `environment.txt` exists |
| 2. Model | `ollama pull qwen2.5:7b` then `ollama run qwen2.5:7b hi` and `ollama ps` | `ollama ps` shows **100% GPU** |
| 3. Smoke test | `bash smoke_test.sh` | finishes, prints minutes and a results dir with `log_env.json` |
| 4. Floor check | `bash smoke_test.sh qwen2.5:7b fish_baseline_concurrent 1` | you know if baseline collapses at month 1 |
| 5. Weekend grid | `bash run_batch.sh 1 15` (Carlos), `bash run_batch.sh 101 115` (Alan) | `runs_manifest.csv` filling up |
| 6. Extract | `python extract_survival.py --manifest runs_manifest.csv --out survival.csv` | excluded runs listed |
| 7. Analyse | `python km_analysis.py survival.csv --outdir results` | `km_curves.png`, `km_summary.csv`, `logrank.csv` |

Copy `extract_survival.py` and `km_analysis.py` into the GovSim folder (or pass `--root`).

## Conditions (all 5 agents, fishery, 12 months)

| Label | GovSim experiment | Role |
|---|---|---|
| `baseline` | `fish_baseline_concurrent` | floor reference (expected ~month 1 collapse for 7–8B) |
| `universalization` | `fish_baseline_concurrent_universalization` | gives small models a chance to survive |
| `newcomer_univ` | `fish_perturbation_outsider_universalization` | greedy agent joins at the start of month 4 (GovSim `round: 3`, 0-indexed); months 1–3 run with 4 agents ("one bad apple") |

Group size is hard-coded to 5 in GovSim (agent list, persona names and "four other fishermen" in prompts), so it is not a factor here.

## Modifications to GovSim (state them in Methodology)

- PathFinder `get_api_model`: names prefixed `local-` are sent to `OPENAI_BASE_URL` (Ollama).
- Temperature 0.7 instead of 0.0, so seeds produce different trajectories.
- `newcomer_univ` horizon reduced from 15 to 12 months for comparability.
- W&B in offline mode.

## If the GPU is not used

`ollama ps` showing CPU, or a crash on the first prompt: gfx1032 + recent ROCm can fail with the override.
Fallback: llama.cpp with the Vulkan backend running `llama-server --port 11434`, then
`export OPENAI_BASE_URL=http://localhost:11434/v1`. Model name must match what the server reports.
