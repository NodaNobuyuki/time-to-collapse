# Time to Collapse: Institutional Fragility and Norm Evolution in LLM Swarms under Predatory Defection

Code and data for our submission to the Swarm Alignment Hackathon (Apart Research, November 2026), by Carlos Nobuyuki Noda Júnior and Alan S. Profeta. The paper is in [`paper/`](paper/Apart_Research_hackathon_submission_EN.pdf).

We run the [GovSim](https://github.com/giorgiopiatti/GovSim) fishing commons with `qwen2.5:7b` and ask what happens when a greedy agent joins a group governed by universalization prompts in Month 4. The analysis covers 40 completed runs over a 12-month horizon.

## Experimental design

These values are taken from the raw logs and the GovSim configs.

| Condition | GovSim experiment | Runs (seeds) | Active agents | Persona goal text |
|---|---|---|---|---|
| `baseline` | `fish_baseline_concurrent` | 14 (1–14) | 5 in every month | none |
| `universalization` (control) | `fish_baseline_concurrent_universalization` | 13 (1–13) | 5 in every month | none |
| `newcomer_univ` | `fish_perturbation_outsider_universalization` | 13 (1–13) | 4 in Months 1–3, 5 from Month 4 | incumbents: `traditional_fisherman`; newcomer (Luke): `outsider_fisherman` |

- All runs: temperature 0.7, concurrent harvesting, initial stock and capacity of 100 t, stock doubles monthly (capped at 100 t), collapse when the stock falls below 5 t.
- The newcomer arm therefore differs from the control in Months 1–3 in group size and in the incumbents' persona text. The Month 4 landmark analysis addresses the group-size difference only in part, because it conditions on surviving those months.
- GovSim's prompts hard-code "four other fishermen", so incumbents in the newcomer arm are told about Luke before Luke is active.
- All runs were executed on a single machine.

## Repository layout

```
paper/                    Submitted paper (PDF)
data/
  runs_manifest.csv       One row per run: condition, seed, model, status, timing
  survival.csv            One row per run: duration in months, collapse event
  raw_runs/<run>/         log_env.json (full GovSim log) and main.log
  conversations/          Readable monthly dialogues and harvests for each run
results/
  km/                     Kaplan-Meier curves, RMST, log-rank tests
  month4_checks/          Month 4 landmark analysis and tonnage checks
  contagion/              Per-agent-per-round table, agreed limits, hazards, arrival dialogues
  verification/           Recomputed paper statistics and audit of agreed_limit
norm_evolution/           Norm-dynamics analysis, figures and per-run metrics
scripts/
  prior_work/             Written before the hackathon (see below)
  weekend/                Written during the hackathon
  verification/           paper_numbers.py
apart/                    Earlier drafts of the submission (superseded by paper/)
reproduce.sh              Regenerates all derived tables and figures
```

## Where the paper's numbers come from

| Paper | Claim | Source |
|---|---|---|
| §4.1, Fig. 1 | Overall survival, RMST, log-rank vs. baseline | `results/km/` |
| §4.1, Fig. 2 | Landmark at Month 4: 33.3% vs. 87.5%, Fisher p = 0.028, log-rank p = 0.024 | `results/month4_checks/` |
| §4.2, Fig. 3 | Norm slopes −0.238 vs. +0.684, Fisher p = 0.003, Mann-Whitney p = 0.006 | `norm_evolution/`, `results/verification/paper_numbers.log` |
| §4.2, Fig. 4 | Compliance 78.1% vs. 83.1%, p = 0.263 | `norm_evolution/`, `results/verification/paper_numbers.log` |

## Reproducing the analysis

No GPU or LLM is needed. Python 3.11:

```bash
uv venv --python 3.11 .venv && source .venv/bin/activate
uv pip install -r requirements.txt
bash reproduce.sh
```

The script rebuilds everything from `data/raw_runs/` into `reproduced/`, then compares each regenerated table and log with the shipped one.

## Re-running the simulations

See [`scripts/prior_work/README_original.md`](scripts/prior_work/README_original.md). `setup_govsim_local.sh` clones GovSim and applies two small patches, and `run_batch.sh` runs the grid. The results here used GovSim `1d11adf`, PathFinder `69b8d64` and Ollama 0.40.7.

Changes relative to upstream GovSim:

- Models named `local-*` are routed to an OpenAI-compatible endpoint (Ollama).
- Temperature is 0.7 instead of 0.0, so seeds produce different trajectories.
- The `newcomer_univ` horizon is 12 months instead of 15, to match the other conditions.
- W&B runs offline.

## Known caveats

Found while preparing this repository. `results/verification/paper_numbers.log` has the full output.

**False agreed limits.** GovSim extracts the agreed limit with `regex.search(r"\d+")`. When the model replies "Answer: N/A" followed by a numbered list, the parser returns the "1" of "1.".

- This affects 19 of the 161 parsed limits (18 read as 1 t, one as 20 t; 10 in the newcomer arm, 9 in the control). They are flagged in `results/verification/limit_parse_audit.csv`.
- GovSim writes the parsed value into every agent's memory ("The community agreed on a maximum limit of 1 tons of fish per person"). All 19 appear verbatim in the next month's prompts.
- In all 13 runs that ever record a 1-ton limit, the first such limit is false, and all 23 genuine 1-ton agreements come after one. The lowest quotas should not be read as purely spontaneous.
- Treating the false limits as "no agreement" gives: control slope ≤ 0 in 6 of 7 runs (not 7 of 7), mean slopes −0.257 vs. +0.586, Fisher p = 0.015, Mann-Whitney p = 0.012. The direction of the effect holds. This corrects the metric only; removing the influence on agent behavior would require re-running with a fixed parser.

**Compliance denominator.** The published compliance rates count every agent, including the newcomer, while the formula in §3.3 is written for incumbents. On incumbents alone the rates are 82.2% (surviving) vs. 88.0% (collapsed), p = 0.155. With the false limits also removed they are 84.6% vs. 96.4%, p = 0.009: collapsed groups were the more compliant ones.

**Other notes.**

- The slope β is an OLS fit over the agreed limits, not an endpoint difference.
- Over the full 12 months, the newcomer vs. control log-rank test is not significant (p = 0.63; `results/km/logrank.csv`). In Months 1–3 the newcomer arm has one agent fewer and survives better, which is why the landmark analysis is used.
- Final agreed limits in surviving control runs range from 1 to 7 t (6 of 7 runs at 1–4 t).
- `norm_evolution/norm_evolution_report.md` gives the compliance p-value as 0.8821. That is the one-sided test; the paper's 0.263 is two-sided.
- Seven runs drift partly into Chinese. Numeric fields remain valid.

## Prior work and hackathon work

`scripts/prior_work/` was written before the hackathon (November 6–8, 2026), with later small edits to `run_batch.sh` and `km_analysis.py` on November 7. Everything in `scripts/weekend/`, `norm_evolution/` and `scripts/verification/`, and all simulation runs, date from the hackathon.
