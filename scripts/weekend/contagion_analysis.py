"""Does one greedy newcomer change how the incumbents behave? ("defection contagion")

Written during the hackathon (Nov 7, 2026) — weekend work, NOT prior work.

Reads runs_manifest.csv and each finished run's log_env.json. Read-only: it only
opens runs whose manifest status is "ok", so it is safe to run while the batch runs.

Design
------
newcomer_univ runs: months 1-3 have 4 incumbents; the outsider joins at round 3
(0-indexed, = month 4). universalization runs are the control: same prompts,
no newcomer. Every metric is computed on the same round windows in both, so the
comparison is a difference-in-differences:

    pre      rounds 0..2   before the newcomer exists
    arrival  round 3       harvest is concurrent, so incumbents have NOT yet seen
                           the newcomer's catch; the following conversation is
                           their first reaction
    post     rounds >= 4   incumbents decide after seeing the newcomer (only
                           exists if the pool survived the arrival month)

Metrics
-------
- wanted_ratio: what an agent asked for / its sustainable share, where the
  sustainable share is pool_before / (2 * agents_in_round) (the pool doubles
  each month, capped at 100, so taking half the pool keeps it level).
  >1 = over-harvesting. Uses `wanted_resource` (intent), not `resource_collected`,
  which is cut down by GovSim's stochastic allocation when the pool runs out.
- agreed_limit: the per-person limit the group settles on in each round's
  conversation (`conversation_resource_limit`); it applies to the next round.
- hazard: P(collapse in month m | survived to month m-1), per condition.

Outputs (in --outdir)
---------------------
    per_agent_round.csv   one row per agent per round
    norms.csv             agreed limit per run per round
    contagion_runs.csv    one row per run with the window means
    hazard.csv            discrete-time hazard per condition and month
    arrival_dialogue.md   the arrival-month conversation of each newcomer run
    contagion.log         everything printed

Usage (from the GovSim folder):
    python contagion_analysis.py --manifest runs_manifest.csv --outdir contagion
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

NEWCOMER_COND = "newcomer_univ"
CONTROL_COND = "universalization"
ARRIVAL_ROUND = 3  # GovSim insert_outsider `round: 3`; cross-checked against each log
COLLAPSE_THRESHOLD = 5  # same as extract_survival.py

log = logging.getLogger("contagion")


def load_run(log_env: Path) -> pd.DataFrame:
    df = pd.DataFrame(json.loads(log_env.read_text()))
    df["round"] = pd.to_numeric(df["round"])
    for col in ("resource_in_pool_before_harvesting", "resource_in_pool_after_harvesting",
                "resource_collected", "wanted_resource", "resource_limit"):
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def analyse_run(df: pd.DataFrame, meta: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict, list[str]]:
    h = df[df["action"] == "harvesting"].copy()
    n_in_round = h.groupby("round")["agent_id"].transform("nunique")
    h["pool_before"] = h["resource_in_pool_before_harvesting"]
    h["sustainable_share"] = h["pool_before"] / (2 * n_in_round)
    h["wanted_ratio"] = h["wanted_resource"] / h["sustainable_share"]

    first_round = h.groupby("agent_id")["round"].min()
    newcomers = first_round[first_round > 0]
    if meta["condition"] == NEWCOMER_COND and h["round"].max() < ARRIVAL_ROUND:
        newcomer_id = None  # collapsed before the newcomer could join: counts as not reaching arrival
    elif meta["condition"] == NEWCOMER_COND:
        if len(newcomers) != 1 or int(newcomers.iloc[0]) != ARRIVAL_ROUND:
            raise ValueError(f"expected one agent joining at round {ARRIVAL_ROUND}, got {newcomers.to_dict()}")
        newcomer_id = newcomers.index[0]
    else:
        newcomer_id = None
    h["role"] = np.where(h["agent_id"] == newcomer_id, "newcomer", "incumbent")

    pool_after = h.groupby("round")["resource_in_pool_after_harvesting"].min()
    collapsed = pool_after[pool_after < COLLAPSE_THRESHOLD]
    collapse_round = int(collapsed.index[0]) if not collapsed.empty else None
    last_round = int(h["round"].max())

    inc = h[h["role"] == "incumbent"]

    def window_mean(rounds) -> float:
        x = inc[inc["round"].isin(rounds)]["wanted_ratio"]
        return float(x.mean()) if len(x) else np.nan

    # post = rounds after arrival that were actually played (stop at collapse)
    post_rounds = range(ARRIVAL_ROUND + 1, last_round + 1)
    norms = (
        df[df["action"] == "conversation_resource_limit"][["round", "resource_limit"]]
        .rename(columns={"resource_limit": "agreed_limit"})
        .assign(**meta)
    )
    lim = norms.set_index("round")["agreed_limit"]

    nc = h[h["role"] == "newcomer"]
    row = {
        **meta,
        "collapse_round": collapse_round,
        "rounds_played": last_round + 1,
        "reached_arrival": last_round >= ARRIVAL_ROUND,
        "collapsed_at_arrival": collapse_round == ARRIVAL_ROUND,
        "has_post": last_round > ARRIVAL_ROUND,
        "inc_ratio_pre": window_mean(range(0, ARRIVAL_ROUND)),
        "inc_ratio_arrival": window_mean([ARRIVAL_ROUND]),
        "inc_ratio_post": window_mean(post_rounds),
        "newcomer_wanted_arrival": float(nc[nc["round"] == ARRIVAL_ROUND]["wanted_resource"].iloc[0]) if len(nc) else np.nan,
        "newcomer_ratio_arrival": float(nc[nc["round"] == ARRIVAL_ROUND]["wanted_ratio"].iloc[0]) if len(nc) else np.nan,
        # limit agreed in the conversation before arrival vs right after the arrival harvest
        "limit_before_arrival": lim.get(ARRIVAL_ROUND - 1, np.nan),
        "limit_after_arrival": lim.get(ARRIVAL_ROUND, np.nan),
    }
    row["inc_ratio_change_post"] = row["inc_ratio_post"] - row["inc_ratio_pre"]
    row["limit_change"] = row["limit_after_arrival"] - row["limit_before_arrival"]

    dialogue = []
    if meta["condition"] == NEWCOMER_COND and row["reached_arrival"]:
        u = df[(df["action"] == "utterance") & (df["round"] == ARRIVAL_ROUND)]
        dialogue.append(f"## {meta['condition']} seed {meta['seed']} "
                        f"(newcomer = {newcomer_id}, collapse_round = {collapse_round}, "
                        f"limit {row['limit_before_arrival']} -> {row['limit_after_arrival']})\n")
        dialogue += [f"- **{r.agent_name}**: {str(r.utterance).strip()}\n" for r in u.itertuples()]
        dialogue.append("\n")

    keep = ["round", "agent_id", "role", "pool_before", "sustainable_share",
            "wanted_resource", "resource_collected", "wanted_ratio"]
    return h[keep].assign(**meta), norms, row, dialogue


def hazard_table(runs: pd.DataFrame, horizon: int) -> pd.DataFrame:
    rows = []
    for cond, d in runs.groupby("condition"):
        # duration in months: collapse round r -> month r+1; censored runs survive all months
        dur = np.where(d["collapse_round"].notna(), d["collapse_round"].fillna(-1) + 1, horizon)
        ev = d["collapse_round"].notna().to_numpy()
        for m in range(1, horizon + 1):
            at_risk = int((dur >= m).sum())
            events = int(((dur == m) & ev).sum())
            rows.append({"condition": cond, "month": m, "at_risk": at_risk, "collapses": events,
                         "hazard": events / at_risk if at_risk else np.nan})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", nargs="+", required=True)
    ap.add_argument("--root", default=".", help="GovSim dir the results_dir paths are relative to")
    ap.add_argument("--outdir", default="contagion")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(message)s",
                        handlers=[logging.FileHandler(outdir / "contagion.log", mode="w"),
                                  logging.StreamHandler()])

    manifest = pd.concat([pd.read_csv(m) for m in args.manifest], ignore_index=True)
    manifest = manifest.drop_duplicates(["condition", "seed", "model"], keep="last")
    manifest = manifest[manifest["condition"].isin([NEWCOMER_COND, CONTROL_COND])]
    skipped = manifest[manifest["status"] != "ok"]
    manifest = manifest[manifest["status"] == "ok"]

    agents, norms, runs, dialogue, failures = [], [], [], [], []
    for r in manifest.itertuples():
        meta = {"condition": r.condition, "seed": int(r.seed), "model": r.model}
        try:
            a, n, row, dl = analyse_run(load_run(Path(args.root) / r.results_dir / "log_env.json"), meta)
        except Exception as exc:  # report, never silently drop
            failures.append((f"{r.condition}/s{r.seed}", str(exc)))
            continue
        agents.append(a); norms.append(n); runs.append(row); dialogue += dl

    if not runs:
        log.info("no finished %s/%s runs yet", NEWCOMER_COND, CONTROL_COND)
        return
    agents_df = pd.concat(agents, ignore_index=True)
    norms_df = pd.concat(norms, ignore_index=True)
    runs_df = pd.DataFrame(runs).sort_values(["condition", "seed"])
    horizon = int(manifest["max_rounds"].max())
    hz = hazard_table(runs_df, horizon)

    agents_df.to_csv(outdir / "per_agent_round.csv", index=False)
    norms_df.to_csv(outdir / "norms.csv", index=False)
    runs_df.to_csv(outdir / "contagion_runs.csv", index=False)
    hz.to_csv(outdir / "hazard.csv", index=False)
    (outdir / "arrival_dialogue.md").write_text(
        "# Arrival-month conversations (newcomer_univ)\n\n" + "".join(dialogue))

    pd.set_option("display.width", 200)
    log.info("runs analysed: %s", runs_df["condition"].value_counts().to_dict())
    if len(skipped):
        log.info("not ok in manifest (excluded): %s", [f"{r.condition}/s{r.seed}" for r in skipped.itertuples()])
    for key, why in failures:
        log.warning("EXCLUDED %s: %s", key, why)

    cols = ["condition", "seed", "collapse_round", "inc_ratio_pre", "inc_ratio_arrival", "inc_ratio_post",
            "newcomer_wanted_arrival", "limit_before_arrival", "limit_after_arrival"]
    log.info("\nPer run (wanted_ratio >1 = over-harvesting; limits in tons per person):\n%s",
             runs_df[cols].round(2).to_string(index=False))

    # Difference-in-differences, only over runs that have the window in question.
    log.info("\nSummary (mean over runs that reached each window; n in brackets):")
    for cond, d in runs_df.groupby("condition"):
        lc = d.dropna(subset=["limit_change"])["limit_change"]
        pc = d[d["has_post"]]["inc_ratio_change_post"].dropna()
        arr = d[d["reached_arrival"]]
        log.info("  %-17s reached month 4: %d | collapsed in month 4: %d | "
                 "agreed-limit change round 2->3: %s [%d] | incumbent ratio change pre->post: %s [%d]",
                 cond, len(arr), int(arr["collapsed_at_arrival"].sum()),
                 f"{lc.mean():+.1f} t" if len(lc) else "n/a", len(lc),
                 f"{pc.mean():+.2f}" if len(pc) else "n/a", len(pc))

    m4 = hz[hz["month"] == ARRIVAL_ROUND + 1][["condition", "at_risk", "collapses", "hazard"]]
    log.info("\nHazard in month %d (newcomer's first month):\n%s", ARRIVAL_ROUND + 1,
             m4.round(2).to_string(index=False))
    log.info("\nSmall n: report per-run values and effect sizes, not p-values, until the batch is done.")


if __name__ == "__main__":
    main()
