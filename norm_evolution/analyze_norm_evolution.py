"""
Emergence and Evolution of Norms in LLM Multi-Agent Commons (GovSim)
-------------------------------------------------------------------
Generates publication-ready figures in English following scientific 
visualization best practices (colorblind-friendly palettes, clean typography,
proper contrast, high-resolution rendering).
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

# Set publication style params
plt.rcParams.update({
    "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
    "font.family": "sans-serif",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 1.1,
    "grid.color": "#E5E5E5",
    "grid.linestyle": "--",
    "grid.linewidth": 0.8,
    "xtick.major.size": 4.5,
    "ytick.major.size": 4.5,
    "xtick.color": "#333333",
    "ytick.color": "#333333",
})

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"
OUTPUT_DIR = Path(__file__).resolve().parent

def load_data():
    norms_path = RESULTS_DIR / "contagion" / "norms.csv"
    survival_path = DATA_DIR / "survival.csv"
    per_agent_path = RESULTS_DIR / "contagion" / "per_agent_round.csv"

    norms = pd.read_csv(norms_path)
    survival = pd.read_csv(survival_path)
    per_agent = pd.read_csv(per_agent_path)

    df = norms.merge(
        survival[["condition", "seed", "duration", "event", "max_rounds"]],
        on=["condition", "seed"],
        how="left"
    )
    
    # Round r discussion applies to Month r+2 harvest
    df["month_active"] = df["round"] + 2
    df["survived"] = df["event"] == 0

    return df, per_agent, survival

def compute_run_metrics(df_norms, per_agent):
    rows = []
    
    for (cond, seed), grp in df_norms.groupby(["condition", "seed"]):
        valid = grp.dropna(subset=["agreed_limit"]).sort_values("month_active")
        event = grp["event"].iloc[0]
        duration = grp["duration"].iloc[0]
        survived = event == 0
        n_agreements = len(valid)

        if n_agreements >= 2:
            x = valid["month_active"].values
            y = valid["agreed_limit"].values
            slope, intercept, r_val, p_val, std_err = stats.linregress(x, y)
            initial_limit = y[0]
            final_limit = y[-1]
            limit_delta = final_limit - initial_limit
        elif n_agreements == 1:
            slope = 0.0
            limit_delta = 0.0
            initial_limit = valid["agreed_limit"].iloc[0]
            final_limit = initial_limit
        else:
            slope = np.nan
            limit_delta = np.nan
            initial_limit = np.nan
            final_limit = np.nan

        p_run = per_agent[(per_agent["condition"] == cond) & (per_agent["seed"] == seed)].copy()
        limits_lookup = grp.set_index("round")["agreed_limit"].to_dict()
        p_run["limit_in_force"] = p_run["round"].map(lambda r: limits_lookup.get(r - 1, np.nan))
        
        valid_comp = p_run.dropna(subset=["limit_in_force", "wanted_resource"])
        if len(valid_comp) > 0:
            compliance_rate = (valid_comp["wanted_resource"] <= valid_comp["limit_in_force"]).mean()
            mean_over_limit = (valid_comp["wanted_resource"] - valid_comp["limit_in_force"]).clip(lower=0).mean()
        else:
            compliance_rate = np.nan
            mean_over_limit = np.nan

        rows.append({
            "condition": cond,
            "seed": seed,
            "duration": duration,
            "event": event,
            "survived": survived,
            "n_agreements": n_agreements,
            "initial_limit": initial_limit,
            "final_limit": final_limit,
            "limit_delta": limit_delta,
            "tightening_slope": slope,
            "compliance_rate": compliance_rate,
            "mean_excess_harvest": mean_over_limit
        })

    return pd.DataFrame(rows)

def plot_trajectories(df_norms):
    """
    Figure 1: Longitudinal trajectories of agreed harvest caps.
    Follows high-readability scientific standards.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.2), sharey=True, dpi=300)
    
    # Colorblind safe palette (Wong / Okabe-Ito inspired)
    c_blue = "#0072B2"      # Universalization survived
    c_orange = "#D55E00"    # Newcomer survived
    c_red = "#D55E00"       # Neutral muted dark red/grey for collapsed
    c_collapsed = "#888888" # Grey dashed for collapsed to avoid visual clutter
    
    SUSTAINABLE_CAP = 10.0  # 100t max / (2 * 5 agents)
    
    # Panel A: Universalization (Control)
    ax1 = axes[0]
    ax1.set_title("A  Universalization (Coordinated Control)", fontsize=13, fontweight="bold", pad=12, loc="left")
    
    univ = df_norms[df_norms["condition"] == "universalization"]
    
    # Plot collapsed runs first (background)
    for seed, grp in univ[univ["survived"] == False].groupby("seed"):
        v = grp.dropna(subset=["agreed_limit"]).sort_values("month_active")
        if len(v) == 0:
            continue
        ax1.plot(v["month_active"], v["agreed_limit"], color=c_collapsed, linestyle="--",
                 marker="x", markersize=5, alpha=0.6, lw=1.3, zorder=2)
        
    # Plot surviving runs (foreground)
    for seed, grp in univ[univ["survived"] == True].groupby("seed"):
        v = grp.dropna(subset=["agreed_limit"]).sort_values("month_active")
        if len(v) == 0:
            continue
        ax1.plot(v["month_active"], v["agreed_limit"], color=c_blue, linestyle="-",
                 marker="o", markersize=5.5, alpha=0.9, lw=2.2, zorder=3)
        
    ax1.axhline(SUSTAINABLE_CAP, color="#333333", linestyle=":", linewidth=1.6, zorder=1)
    ax1.text(12.2, SUSTAINABLE_CAP + 0.5, "Maximum sustainable\nquota (10t / agent)", 
             fontsize=9.5, color="#333333", va="center", ha="right",
             bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#CCCCCC", alpha=0.9))
    
    ax1.set_xlabel("Norm Implementation Month (Active Window)", fontsize=11.5, labelpad=8)
    ax1.set_ylabel("Agreed Harvest Limit (Tons / Agent)", fontsize=11.5, labelpad=8)
    ax1.set_xlim(1.6, 12.4)
    ax1.set_ylim(-0.5, 32)
    ax1.set_xticks(range(2, 13))
    ax1.grid(True, zorder=0)

    # Panel B: Newcomer Univ (Perturbed by Greedy Outsider)
    ax2 = axes[1]
    ax2.set_title("B  Newcomer Perturbation (Greedy Defector at Month 4)", fontsize=13, fontweight="bold", pad=12, loc="left")
    
    newc = df_norms[df_norms["condition"] == "newcomer_univ"]
    
    for seed, grp in newc[newc["survived"] == False].groupby("seed"):
        v = grp.dropna(subset=["agreed_limit"]).sort_values("month_active")
        if len(v) == 0:
            continue
        ax2.plot(v["month_active"], v["agreed_limit"], color=c_collapsed, linestyle="--",
                 marker="x", markersize=5, alpha=0.6, lw=1.3, zorder=2)
        
    for seed, grp in newc[newc["survived"] == True].groupby("seed"):
        v = grp.dropna(subset=["agreed_limit"]).sort_values("month_active")
        if len(v) == 0:
            continue
        ax2.plot(v["month_active"], v["agreed_limit"], color=c_orange, linestyle="-",
                 marker="s", markersize=5.5, alpha=0.9, lw=2.2, zorder=3)

    # Event indicator: Newcomer arrival
    ax2.axvline(x=4, color="#B22222", linestyle="-.", linewidth=1.8, zorder=2)
    ax2.text(4.15, 27, "Newcomer\nArrival", fontsize=10, fontweight="bold", color="#B22222", va="top",
             bbox=dict(boxstyle="round,pad=0.25", facecolor="#FFF0F0", edgecolor="#B22222", alpha=0.9))
    
    ax2.axhline(SUSTAINABLE_CAP, color="#333333", linestyle=":", linewidth=1.6, zorder=1)
    ax2.set_xlabel("Norm Implementation Month (Active Window)", fontsize=11.5, labelpad=8)
    ax2.set_xlim(1.6, 12.4)
    ax2.set_xticks(range(2, 13))
    ax2.grid(True, zorder=0)

    # Clean multi-item legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color=c_blue, lw=2.4, marker="o", markersize=6, label="Universalization (Survived 12 Months, n=7)"),
        Line2D([0], [0], color=c_orange, lw=2.4, marker="s", markersize=6, label="Newcomer Condition (Survived 12 Months, n=4)"),
        Line2D([0], [0], color=c_collapsed, lw=1.6, ls="--", marker="x", markersize=6, label="Early Resource Collapse (< 12 Months)"),
        Line2D([0], [0], color="#333333", ls=":", lw=1.8, label="Sustainable Quota Threshold (10 t/agent)"),
        Line2D([0], [0], color="#B22222", ls="-.", lw=1.8, label="Newcomer Enters Lake (Month 4)")
    ]
    
    fig.legend(handles=legend_elements, loc="lower center", bbox_to_anchor=(0.5, -0.06), 
               ncol=3, fontsize=10, frameon=True, facecolor="#FAFAFA", edgecolor="#CCCCCC")
    
    plt.suptitle("Longitudinal Norm Trajectories & Institutional Dynamics in LLM Commons", 
                 fontsize=14.5, fontweight="bold", y=0.99)
    plt.tight_layout(rect=[0, 0.08, 1, 0.96])
    plt.savefig(OUTPUT_DIR / "fig_norm_trajectories.png", dpi=300, bbox_inches="tight")
    plt.close()

def plot_tightening_and_compliance(metrics_df):
    """
    Figure 2: Institutional tightening rate and compliance metrics.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.8), dpi=300)
    
    c_blue = "#0072B2"
    c_orange = "#D55E00"
    
    # Subplot 1: Tightening slope vs survival
    m_valid = metrics_df.dropna(subset=["tightening_slope"]).copy()
    
    colors = {"universalization": c_blue, "newcomer_univ": c_orange}
    labels_cond = {"universalization": "Universalization", "newcomer_univ": "Newcomer"}
    
    for cond in ["universalization", "newcomer_univ"]:
        sub = m_valid[m_valid["condition"] == cond]
        # Survived
        s_surv = sub[sub["survived"] == True]
        if len(s_surv) > 0:
            ax1.scatter(s_surv["tightening_slope"], s_surv["duration"],
                        color=colors[cond], marker="o", s=85, alpha=0.9,
                        edgecolor="#222222", linewidth=1.2,
                        label=f"{labels_cond[cond]} (Survived)")
        # Collapsed
        s_col = sub[sub["survived"] == False]
        if len(s_col) > 0:
            ax1.scatter(s_col["tightening_slope"], s_col["duration"],
                        color=colors[cond], marker="X", s=85, alpha=0.55,
                        edgecolor="#222222", linewidth=0.8,
                        label=f"{labels_cond[cond]} (Collapsed)")

    ax1.axvline(0, color="#555555", linestyle="--", linewidth=1.2, alpha=0.8)
    ax1.text(-0.08, 1.2, "← Conservative Tightening (Slope < 0)", fontsize=9.5, fontweight="bold", 
             color="#0072B2", ha="right", va="bottom")
    ax1.text(0.08, 1.2, "Norm Relaxation / Inflation (Slope > 0) →", fontsize=9.5, fontweight="bold", 
             color="#D55E00", ha="left", va="bottom")

    ax1.set_xlabel("Norm Adaptation Rate (Slope: Δ Tons / Month)", fontsize=11, labelpad=8)
    ax1.set_ylabel("Group Survival Duration (Months)", fontsize=11, labelpad=8)
    ax1.set_title("A  Norm Tightening Rate vs. Commons Longevity", fontsize=12, fontweight="bold", loc="left", pad=10)
    ax1.set_ylim(0.5, 12.8)
    ax1.grid(True, zorder=0)
    ax1.legend(fontsize=9, loc="upper right", framealpha=0.95, edgecolor="#DDDDDD")

    # Subplot 2: Norm compliance by survival outcome
    comp_valid = metrics_df.dropna(subset=["compliance_rate"])
    
    data_surv = comp_valid[comp_valid["survived"] == True]["compliance_rate"].values * 100
    data_col = comp_valid[comp_valid["survived"] == False]["compliance_rate"].values * 100
    
    bp = ax2.boxplot([data_surv, data_col], patch_artist=True, widths=0.45,
                     tick_labels=["Survived\n(12 Months)", "Collapsed\n(< 12 Months)"],
                     medianprops=dict(color="black", linewidth=2.0),
                     whiskerprops=dict(color="#444444", linewidth=1.2),
                     capprops=dict(color="#444444", linewidth=1.2))
    
    bp["boxes"][0].set_facecolor("#A6CEE3")
    bp["boxes"][0].set_edgecolor("#1F78B4")
    bp["boxes"][0].set_linewidth(1.5)
    
    bp["boxes"][1].set_facecolor("#FDBF6F")
    bp["boxes"][1].set_edgecolor("#FF7F00")
    bp["boxes"][1].set_linewidth(1.5)
    
    # Overlay individual data points
    np.random.seed(42)
    for i, vals in enumerate([data_surv, data_col], 1):
        jitter = np.random.normal(0, 0.04, size=len(vals))
        ax2.scatter(np.full_like(vals, i) + jitter, vals, 
                    color="#222222", alpha=0.7, s=45, zorder=4, edgecolor="white", linewidth=0.5)
        
    ax2.set_ylabel("Norm Compliance Rate (%)", fontsize=11, labelpad=8)
    ax2.set_ylim(45, 105)
    ax2.set_title("B  Norm Compliance Across Collective Outcomes", fontsize=12, fontweight="bold", loc="left", pad=10)
    ax2.grid(True, zorder=0)

    # Statistical annotation
    u_stat, p_val = stats.mannwhitneyu(data_surv, data_col, alternative="two-sided")
    ax2.text(0.98, 0.05, f"Mann-Whitney U = {u_stat:.1f}\nTwo-sided p = {p_val:.3f}", 
             transform=ax2.transAxes, fontsize=9.5, ha="right", va="bottom",
             bbox=dict(boxstyle="round,pad=0.35", facecolor="#F8F8F8", edgecolor="#CCCCCC", alpha=0.9))

    plt.suptitle("Institutional Governance Mechanisms in Swarm Alignment", 
                 fontsize=14, fontweight="bold", y=0.99)
    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    plt.savefig(OUTPUT_DIR / "fig_tightening_and_compliance.png", dpi=300, bbox_inches="tight")
    plt.close()

def main():
    print("Loading data...")
    df_norms, per_agent, survival = load_data()
    metrics_df = compute_run_metrics(df_norms, per_agent)
    
    print("Rendering Fig 1 (Trajectories)...")
    plot_trajectories(df_norms)
    
    print("Rendering Fig 2 (Tightening & Compliance)...")
    plot_tightening_and_compliance(metrics_df)
    
    print("All figures successfully rendered with high scientific readability standards.")

if __name__ == "__main__":
    main()
