"""Extract survival data (time-to-collapse) from GovSim runs.

Reads runs_manifest.csv (written by run_batch.sh), opens each run's
log_env.json and produces one row per run:

    condition, seed, model, machine, duration, event, ...

Definitions (match Piatti et al., 2024):
- A round is one month. Rounds in log_env.json are 0-indexed.
- Collapse = the pool falls below C=5 after harvesting.
- duration = number of months survived, counting the collapse month
  (collapse in round 0 -> duration 1, as in the paper's "survival time 1").
- event = 1 if the run collapsed, 0 if it reached max_rounds (right-censored).

Usage:
    python extract_survival.py --manifest runs_manifest.csv --out survival.csv
    # merge manifests from two machines:
    python extract_survival.py --manifest carlos.csv alan.csv --out survival.csv
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

COLLAPSE_THRESHOLD = 5

log = logging.getLogger("extract")


def survival_from_log(log_env: Path, max_rounds: int) -> dict:
    records = json.loads(log_env.read_text())
    df = pd.DataFrame(records)
    harvest = df[df["action"] == "harvesting"]
    if harvest.empty:
        raise ValueError("no harvesting rows")

    per_round = (
        harvest.groupby("round")
        .agg(
            pool_before=("resource_in_pool_before_harvesting", "first"),
            pool_after=("resource_in_pool_after_harvesting", "min"),
            total_collected=("resource_collected", "sum"),
        )
        .sort_index()
    )

    collapsed = per_round[per_round["pool_after"] < COLLAPSE_THRESHOLD]
    if not collapsed.empty:
        collapse_round = int(collapsed.index[0])
        return {
            "duration": collapse_round + 1,
            "event": 1,
            "rounds_logged": int(per_round.index.max()) + 1,
            "total_harvest": float(per_round.loc[:collapse_round, "total_collected"].sum()),
        }

    rounds_logged = int(per_round.index.max()) + 1
    if rounds_logged < max_rounds:
        # Run stopped early without a collapse: a crash, not a censoring event.
        raise ValueError(f"only {rounds_logged}/{max_rounds} rounds and no collapse")
    return {
        "duration": max_rounds,
        "event": 0,
        "rounds_logged": rounds_logged,
        "total_harvest": float(per_round["total_collected"].sum()),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", nargs="+", required=True)
    ap.add_argument("--root", default=".", help="GovSim dir the results_dir paths are relative to")
    ap.add_argument("--out", default="survival.csv")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    manifest = pd.concat([pd.read_csv(m) for m in args.manifest], ignore_index=True)
    # Keep the last attempt of each (condition, seed, model).
    manifest = manifest.drop_duplicates(["condition", "seed", "model"], keep="last")

    rows, failures = [], []
    for _, run in manifest.iterrows():
        key = f"{run.condition}/s{run.seed}"
        if run.status != "ok" or pd.isna(run.results_dir):
            failures.append((key, "status=" + str(run.status)))
            continue
        log_env = Path(args.root) / run.results_dir / "log_env.json"
        try:
            surv = survival_from_log(log_env, int(run.max_rounds))
        except Exception as exc:  # report, never silently drop
            failures.append((key, str(exc)))
            continue
        rows.append(
            {
                "condition": run.condition,
                "seed": int(run.seed),
                "model": run.model,
                "machine": run.machine,
                "temperature": run.temperature,
                "max_rounds": int(run.max_rounds),
                "minutes": run.minutes,
                **surv,
            }
        )

    out = pd.DataFrame(rows).sort_values(["condition", "seed"])
    out.to_csv(args.out, index=False)
    log.info("wrote %d runs to %s", len(out), args.out)
    if failures:
        log.warning("%d runs excluded (report this number in the paper):", len(failures))
        for key, why in failures:
            log.warning("  %s: %s", key, why)


if __name__ == "__main__":
    main()
