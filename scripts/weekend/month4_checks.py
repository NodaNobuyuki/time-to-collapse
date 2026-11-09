"""Two follow-up checks on newcomer_univ vs universalization (weekend work, Nov 8 2026).

A. Landmark analysis at the start of month 4: keep only runs that survived
   months 1-3, restart the clock there. Removes the 4-vs-5-agent confound of
   months 1-3, where the newcomer condition has one agent fewer.
B. Tonnage check for "contagion": does the incumbents' *absolute* request
   (tons) rise after the newcomer arrives, or only the ratio to a shrinking
   sustainable share? Also: do incumbents break the limit they agreed on?

Inputs: survival.csv (extract_survival.py), per_agent_round.csv and norms.csv
(contagion_analysis.py). Read-only on the GovSim results.

Usage: python month4_checks.py --survival S.csv --contagion-dir DIR --outdir OUT
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test
from lifelines.utils import restricted_mean_survival_time
from scipy import stats

NEW, CTRL = "newcomer_univ", "universalization"
LANDMARK = 3      # months survived before the newcomer harvests (arrival = round 3)
HORIZON = 12
PRE, ARRIVAL = range(0, 3), 3   # 0-indexed rounds

ap = argparse.ArgumentParser()
ap.add_argument("--survival", required=True)
ap.add_argument("--contagion-dir", required=True)
ap.add_argument("--outdir", required=True)
a = ap.parse_args()
out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
lines = []
def say(*x):
    s = " ".join(str(i) for i in x); print(s); lines.append(s)

# ---------------------------------------------------------------- A. landmark
s = pd.read_csv(a.survival)
s = s[s.condition.isin([NEW, CTRL])]
say("=" * 70, "\nA. LANDMARK AT MONTH 4 (runs that survived months 1-3)\n" + "=" * 70)
lm = s[s.duration > LANDMARK].copy()
lm["lm_duration"] = lm.duration - LANDMARK
rows = []
for c in [NEW, CTRL]:
    x, all_c = lm[lm.condition == c], s[s.condition == c]
    rows.append(dict(condition=c, runs=len(all_c), at_risk_month4=len(x),
                     collapsed_month4=int(((x.duration == LANDMARK + 1) & (x.event == 1)).sum()),
                     collapsed_later=int(((x.duration > LANDMARK + 1) & (x.event == 1)).sum()),
                     survived_12=int((x.event == 0).sum()),
                     rmst_months4to12=restricted_mean_survival_time(
                         KaplanMeierFitter().fit(x.lm_duration, x.event), t=HORIZON - LANDMARK)))
tab = pd.DataFrame(rows)
say(tab.to_string(index=False))
tab.to_csv(out / "landmark_summary.csv", index=False)

n, c_ = lm[lm.condition == NEW], lm[lm.condition == CTRL]
ft = stats.fisher_exact([[(n.event == 0).sum(), (n.event == 1).sum()],
                         [(c_.event == 0).sum(), (c_.event == 1).sum()]])
lr = logrank_test(n.lm_duration, c_.lm_duration, n.event, c_.event)
m4 = stats.fisher_exact([[rows[0]["collapsed_month4"], rows[0]["at_risk_month4"] - rows[0]["collapsed_month4"]],
                         [rows[1]["collapsed_month4"], rows[1]["at_risk_month4"] - rows[1]["collapsed_month4"]]])
say(f"\nSurvived to month 12 given alive at month 4: Fisher exact p = {ft.pvalue:.4f} (OR = {ft.statistic:.2f})")
say(f"Collapse in month 4 itself:                   Fisher exact p = {m4.pvalue:.4f}")
say(f"Landmark log-rank (months 4-12):              chi2 = {lr.test_statistic:.2f}, p = {lr.p_value:.4f}")

fig, ax = plt.subplots(figsize=(6, 4))
for c, col in [(CTRL, "#2b7bba"), (NEW, "#d6604d")]:
    x = lm[lm.condition == c]
    KaplanMeierFitter().fit(x.lm_duration + LANDMARK, x.event, label=f"{c} (n={len(x)})",
                            timeline=np.arange(LANDMARK, HORIZON + 1)).plot_survival_function(ax=ax, color=col, ci_show=True)
ax.set_xlim(LANDMARK, HORIZON); ax.set_ylim(0, 1.05)
ax.set_xlabel("Months survived"); ax.set_ylabel("P(not collapsed | alive at month 4)")
ax.axvline(LANDMARK, ls=":", c="grey"); ax.text(LANDMARK + 0.1, 0.03, "newcomer joins", color="grey", fontsize=8)
ax.set_title("Survival from the newcomer's arrival"); ax.legend(loc="upper right", fontsize=8)
fig.tight_layout(); fig.savefig(out / "landmark_km.png", dpi=200)

# ---------------------------------------------------------------- B. tonnage
say("\n" + "=" * 70, "\nB. TONNAGE CHECK: incumbents' absolute requests, pre vs post arrival\n" + "=" * 70)
p = pd.read_csv(Path(a.contagion_dir) / "per_agent_round.csv")
norms = pd.read_csv(Path(a.contagion_dir) / "norms.csv")
p = p[p.condition.isin([NEW, CTRL]) & (p.role == "incumbent")]
# limit agreed in round r's conversation is in force for round r+1's harvest
norms["round"] = norms["round"] + 1
p = p.merge(norms.rename(columns={"agreed_limit": "limit_in_force"}), on=["condition", "seed", "model", "round"], how="left")
p["over_limit"] = np.where(p.limit_in_force.notna(), p.wanted_resource > p.limit_in_force, np.nan)

def per_run(df):
    r = []
    for (c, seed), g in df.groupby(["condition", "seed"]):
        if g["round"].max() <= ARRIVAL:
            continue  # no post window
        pre, post = g[g["round"].isin(PRE)], g[g["round"] > ARRIVAL]
        r.append(dict(condition=c, seed=seed,
                      tons_pre=pre.wanted_resource.mean(), tons_post=post.wanted_resource.mean(),
                      pool_pre=pre.pool_before.mean(), pool_post=post.pool_before.mean(),
                      ratio_pre=pre.wanted_ratio.mean(), ratio_post=post.wanted_ratio.mean(),
                      overlimit_pre=pre.over_limit.mean(), overlimit_post=post.over_limit.mean()))
    r = pd.DataFrame(r)
    for k in ["tons", "pool", "ratio", "overlimit"]:
        r[f"{k}_change"] = r[f"{k}_post"] - r[f"{k}_pre"]
    return r

def compare(r, label):
    say(f"\n--- {label}")
    for k, unit in [("tons", "t"), ("pool", "t"), ("ratio", "x"), ("overlimit", "share")]:
        a_, b_ = r[r.condition == NEW][f"{k}_change"].dropna(), r[r.condition == CTRL][f"{k}_change"].dropna()
        mw = stats.mannwhitneyu(a_, b_, alternative="two-sided") if len(a_) and len(b_) else None
        say(f"{k:>9} change post-pre | newcomer: median {a_.median():+.2f}, up in {(a_ > 0).sum()}/{len(a_)}"
            f" | control: median {b_.median():+.2f}, up in {(b_ > 0).sum()}/{len(b_)}"
            + (f" | MWU p = {mw.pvalue:.4f}" if mw else ""))

r_all = per_run(p)
r_all.round(3).to_csv(out / "tonnage_per_run.csv", index=False)
say(r_all[["condition", "seed", "tons_pre", "tons_post", "pool_pre", "pool_post", "overlimit_pre", "overlimit_post"]].round(2).to_string(index=False))
compare(r_all, "control = all 5 agents")
# same four personas in both conditions (persona_4 is the newcomer in newcomer_univ)
compare(per_run(p[p.agent_id != "persona_4"]), "control = persona_0..3 only (same agents as newcomer incumbents)")
say("\nNotes: post = rounds after arrival up to and including the collapse round; only runs that got past month 4."
    "\n'overlimit' = share of incumbent requests above the limit agreed in the previous month's conversation"
    " (only rounds where a limit was agreed).")
(out / "month4_checks.log").write_text("\n".join(lines) + "\n")
