"""Kaplan-Meier analysis of time-to-collapse per condition.

Input: survival.csv from extract_survival.py (one row per run).
Output (in --outdir):
    km_curves.png        KM curves with 95% CI, one per condition
    km_summary.csv       n, collapses, censored, median survival, RMST (+SE), S(t) at chosen months
    logrank.csv          global and pairwise log-rank tests (Holm-corrected)
    analysis.log         everything printed, for the research log

Usage:
    python km_analysis.py survival.csv --outdir results --months 3 6 12
"""
from __future__ import annotations

import argparse
import itertools
import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test, multivariate_logrank_test
from lifelines.utils import restricted_mean_survival_time

SEED = 0  # nothing here is random; fixed for any future bootstrap

# GovSim's insert_outsider perturbation fires at round 3 (0-indexed), i.e. the
# newcomer harvests from month 4 on. On the KM axis (duration = months survived)
# that is the boundary x=3: a drop at x=4 is a collapse in the newcomer's first month.
NEWCOMER_JOINS_AFTER_MONTH = 3


def holm(pvals: list[float]) -> list[float]:
    order = np.argsort(pvals)
    m = len(pvals)
    adj = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * pvals[idx])
        adj[idx] = min(1.0, running)
    return adj.tolist()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("survival_csv")
    ap.add_argument("--outdir", default="results")
    ap.add_argument("--months", nargs="+", type=int, default=[3, 6, 12])
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.FileHandler(outdir / "analysis.log", mode="w"), logging.StreamHandler()],
    )
    log = logging.getLogger("km")
    np.random.seed(SEED)

    df = pd.read_csv(args.survival_csv)
    horizon = int(df["max_rounds"].max())
    if df["max_rounds"].nunique() > 1:
        log.warning("WARNING: runs have different max_rounds %s — curves are not comparable",
                    sorted(df["max_rounds"].unique()))
    conditions = list(dict.fromkeys(df["condition"]))  # keep file order
    log.info("runs: %d | conditions: %s | horizon: %d months", len(df), conditions, horizon)

    # --- KM per condition -------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 4.5))
    summary = []
    for cond in conditions:
        d = df[df["condition"] == cond]
        kmf = KaplanMeierFitter(label=f"{cond} (n={len(d)})")
        kmf.fit(d["duration"], event_observed=d["event"], timeline=np.arange(0, horizon + 1))
        kmf.plot_survival_function(
            ax=ax, ci_show=True, drawstyle="steps-post",
            show_censors=True, censor_styles={"marker": "|", "ms": 10, "mew": 1.5},
        )
        # Restricted mean survival time up to the horizon: the area under the KM
        # curve, valid with censoring (a plain mean treats censored runs as exact).
        rmst, rmst_var = restricted_mean_survival_time(kmf, t=horizon, return_variance=True)
        row = {
            "condition": cond,
            "n": len(d),
            "collapses": int(d["event"].sum()),
            "censored": int((1 - d["event"]).sum()),
            "median_survival": kmf.median_survival_time_,  # inf if <50% collapse
            f"rmst_{horizon}": float(rmst),
            # lifelines returns NaN variance when every run has the same duration; it is 0 there.
            "rmst_se": 0.0 if d["duration"].nunique() == 1 else float(np.sqrt(rmst_var)),
        }
        for t in args.months:
            row[f"S({t})"] = float(kmf.survival_function_at_times(t).iloc[0])
        summary.append(row)
        if d["event"].nunique() == 1 and d["duration"].nunique() == 1:
            log.warning("WARNING: %s has zero variance (all runs duration=%s) — floor/ceiling effect",
                        cond, d["duration"].iloc[0])

    if any(c.startswith("newcomer") for c in conditions):
        ax.axvline(NEWCOMER_JOINS_AFTER_MONTH, color="0.35", ls="--", lw=1)
        ax.text(NEWCOMER_JOINS_AFTER_MONTH + 0.1, 0.04, "newcomer joins\n(start of month 4)",
                fontsize=8, color="0.35", va="bottom")
    ax.set_xlabel("Months survived")
    ax.set_ylabel("P(resource not collapsed)")
    ax.set_xlim(0, horizon + 0.4)  # room for censor ticks at the horizon
    ax.set_xticks(range(0, horizon + 1))
    ax.set_ylim(0, 1.02)
    ax.set_title("Time to collapse (Kaplan-Meier, 95% CI; | = survived to horizon)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(outdir / "km_curves.png", dpi=200)

    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(outdir / "km_summary.csv", index=False)
    log.info("\n%s", summary_df.to_string(index=False))

    # --- Log-rank tests ---------------------------------------------------
    tests = []
    if len(conditions) > 1:
        g = multivariate_logrank_test(df["duration"], df["condition"], df["event"])
        tests.append({"comparison": "global", "chi2": g.test_statistic, "p": g.p_value, "p_holm": g.p_value})
        pairs = list(itertools.combinations(conditions, 2))
        raw = []
        for a, b in pairs:
            da, db = df[df["condition"] == a], df[df["condition"] == b]
            r = logrank_test(da["duration"], db["duration"], da["event"], db["event"])
            raw.append((f"{a} vs {b}", r.test_statistic, r.p_value))
        for (name, chi2, p), padj in zip(raw, holm([p for *_, p in raw])):
            tests.append({"comparison": name, "chi2": chi2, "p": p, "p_holm": padj})
        tests_df = pd.DataFrame(tests)
        tests_df.to_csv(outdir / "logrank.csv", index=False)
        log.info("\n%s", tests_df.to_string(index=False))
    log.info("\nNote: months are discrete, so many ties; log-rank handles ties but report it.")


if __name__ == "__main__":
    main()
