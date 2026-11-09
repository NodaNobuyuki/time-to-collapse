# Norm Evolution & Institutional Dynamics in LLM Commons (GovSim)

This module provides a mechanistic, institutional analysis of collective norm evolution for the **Swarm Alignment Hackathon (Apart Research)** paper.

---

## 1. Publication Figures & Ready Captions

### **Figure 1: [`fig_norm_trajectories.png`](./fig_norm_trajectories.png)**
> **Figure 1. Longitudinal Trajectories of Agreed Harvest Limits.**
> **(A)** In the coordinated control condition (*Universalization*, $n=13$), all surviving commons ($n=7$, solid blue lines) exhibit spontaneous and progressive norm tightening ($\text{slope} \le 0$, mean $-0.24$ tons/month), establishing conservative per-agent harvest caps (1–4 tons) well below the theoretical maximum sustainable quota (10 tons, dotted gray line). 
> **(B)** In the perturbed condition (*Newcomer*, $n=13$), the introduction of a greedy defector at Month 4 (red dashed line) disrupts this institutional trajectory: groups that survive past Month 4 ($n=4$, solid orange lines) systematically experience norm inflation ($\text{slope} > 0$, mean $+0.68$ tons/month) as they attempt to renegotiate upward to accommodate defection. Runs that collapsed prior to Month 12 are displayed in dashed gray lines.

---

### **Figure 2: [`fig_tightening_and_compliance.png`](./fig_tightening_and_compliance.png)**
> **Figure 2. Institutional Governance Mechanisms and Alignment Outcomes.**
> **(A) Norm Adaptation Rate vs. Group Longevity:** In unperturbed conditions, surviving enxames cluster strictly in the negative-slope quadrant (conservative tightening). Perturbed surviving runs shift into the positive-slope quadrant (norm inflation).
> **(B) Norm Compliance Rate across Outcomes:** Overall compliance rate remains comparable between surviving ($78.1\%$) and collapsed groups ($83.1\%$, Mann-Whitney $U = 43.0$, $p = 0.263$), demonstrating that commons collapses stem from structural harvest shocks rather than active post-agreement cheating by incumbents.

---

## 2. Quantitative Summary

| Metric | Universalization (Survived, $n=7$) | Newcomer (Survived, $n=4$) | Statistical Test |
|---|---|---|---|
| **Norm Slope Direction** | **100% Negative or Zero** ($\le 0$) | **100% Positive** ($> 0$) | Fisher's Exact $p = 0.003$ |
| **Mean Adaptation Slope** | **$-0.238$ t/month** | **$+0.684$ t/month** | Mann-Whitney $p = 0.006$ |
| **Final Agreed Cap** | **$1 - 7$ t/agent** (Median: $3.0$) | **$4 - 10$ t/agent** (Median: $8.0$) | Mann-Whitney $p = 0.024$ |

---

## 3. Files in this Directory

* [`analyze_norm_evolution.py`](./analyze_norm_evolution.py) — Self-contained generation script (300 DPI, scientific color palette).
* [`fig_norm_trajectories.png`](./fig_norm_trajectories.png) — Figure 1 for the manuscript.
* [`fig_tightening_and_compliance.png`](./fig_tightening_and_compliance.png) — Figure 2 for the manuscript.
* [`norm_metrics_summary.csv`](./norm_metrics_summary.csv) — Run-by-run metrics table.
* [`norm_evolution_report.md`](./norm_evolution_report.md) — Detailed raw statistics report.
