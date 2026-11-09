r"""Recompute the paper's norm-dynamics statistics and audit the agreed_limit values.

norm_evolution/analyze_norm_evolution.py draws the figures but does not run the tests reported
in Section 4.2 of the paper. This script runs them, using that file's compute_run_metrics so the
run-level metrics are the same ones behind norm_metrics_summary.csv.

It then audits agreed_limit. GovSim extracts the limit with regex.search(r"\d+") over the text the
model generates after "Answer:". When qwen2.5:7b replies "Answer: N/A" and carries on with a
numbered list, the parser returns the "1" of "1." (or another number further along). GovSim then
stores the value in every agent's memory as "The community agreed on a maximum limit of 1 tons of
fish per person.", so a false limit also influences the following months.

Outputs (in --outdir): paper_numbers.log, limit_parse_audit.csv

Usage: python scripts/verification/paper_numbers.py [--root .] [--raw-runs data/raw_runs]
                                                    [--outdir results/verification]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

CONTROL, NEWCOMER = "universalization", "newcomer_univ"
RUN_NAME = re.compile(r"(?P<condition>.+)_qwen.*_s(?P<seed>\d+)$")
NOT_APPLICABLE = re.compile(r"\**\s*N\s*/?\s*A\b", re.IGNORECASE)

lines: list[str] = []


def say(text: str = "") -> None:
    print(text)
    lines.append(text)


def load_norm_module(root: Path):
    spec = importlib.util.spec_from_file_location(
        "analyze_norm_evolution", root / "norm_evolution" / "analyze_norm_evolution.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def html_text(record: dict) -> str:
    html = record["html_interactions"]
    return html if isinstance(html, str) else " ".join(html)


def model_answer(record: dict) -> str:
    """Return what the model wrote after its first 'Answer:' when asked for the agreed limit."""
    html = record["html_interactions"]
    html = html if isinstance(html, str) else html[-1]
    response = re.sub(r"<[^>]+>", "", html[html.rfind("ASSISTANT"):])
    match = re.search(r"Answer:\s*([^\n]*)", response)
    return match.group(1).strip() if match else ""


def audit_limits(raw_runs: Path) -> tuple[pd.DataFrame, int, int]:
    """Classify every parsed limit; also count false limits that reach next month's prompts."""
    rows = []
    followed, in_next_prompts = 0, 0
    for log_env in sorted(raw_runs.glob("*/log_env.json")):
        name = RUN_NAME.match(log_env.parent.name)
        if name["condition"] not in (CONTROL, NEWCOMER):
            continue
        records = json.loads(log_env.read_text())
        for r in records:
            if r["action"] != "conversation_resource_limit":
                continue
            answer = model_answer(r)
            is_false = r["resource_limit"] is not None and bool(NOT_APPLICABLE.match(answer))
            rows.append({
                "condition": name["condition"],
                "seed": int(name["seed"]),
                "round": int(r["round"]),
                "parsed_limit": r["resource_limit"],
                "model_answer": answer[:80],
                "false_limit": is_false,
            })
            if is_false:
                next_month = [
                    html_text(x) for x in records
                    if int(x["round"]) == int(r["round"]) + 1 and x["action"] in ("harvesting", "utterance")
                ]
                if next_month:
                    followed += 1
                    sentence = f"community agreed on a maximum limit of {int(r['resource_limit'])} tons"
                    in_next_prompts += any(sentence in h for h in next_month)
    return pd.DataFrame(rows), followed, in_next_prompts


def report(metrics: pd.DataFrame, label: str) -> None:
    survivors = metrics[metrics["survived"]]
    ctrl = survivors[survivors["condition"] == CONTROL]
    newc = survivors[survivors["condition"] == NEWCOMER]
    c_slope, n_slope = ctrl["tightening_slope"].dropna(), newc["tightening_slope"].dropna()
    direction = [[int((c_slope <= 0).sum()), int((c_slope > 0).sum())],
                 [int((n_slope <= 0).sum()), int((n_slope > 0).sum())]]
    c_final, n_final = ctrl["final_limit"].dropna(), newc["final_limit"].dropna()
    rated = metrics.dropna(subset=["compliance_rate"])
    kept = rated[rated["survived"]]["compliance_rate"]
    lost = rated[~rated["survived"]]["compliance_rate"]
    compliance = stats.mannwhitneyu(kept, lost, alternative="two-sided")

    say(f"\n--- {label}")
    say(f"Slope <= 0: control {direction[0][0]}/{len(c_slope)}; slope > 0: newcomer {direction[1][1]}/{len(n_slope)}"
        f" (Fisher p = {stats.fisher_exact(direction)[1]:.4f})")
    say(f"Mean slope: control {c_slope.mean():+.3f}, newcomer {n_slope.mean():+.3f} t/agent/month"
        f" (Mann-Whitney p = {stats.mannwhitneyu(c_slope, n_slope, alternative='two-sided').pvalue:.4f})")
    say(f"Final limit: control median {c_final.median():.1f} (range {c_final.min():.0f}-{c_final.max():.0f}),"
        f" newcomer median {n_final.median():.1f} (range {n_final.min():.0f}-{n_final.max():.0f})"
        f" (exact Mann-Whitney p = {stats.mannwhitneyu(c_final, n_final, alternative='two-sided', method='exact').pvalue:.4f})")
    say(f"Compliance: surviving {kept.mean():.1%} (n={len(kept)}), collapsed {lost.mean():.1%} (n={len(lost)})"
        f" (U = {compliance.statistic:.1f}, two-sided p = {compliance.pvalue:.4f})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="tree holding data/survival.csv, results/ and norm_evolution/")
    ap.add_argument("--raw-runs", default="data/raw_runs")
    ap.add_argument("--outdir", default="results/verification")
    args = ap.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    module = load_norm_module(Path(args.root))
    norms, per_agent, _ = module.load_data()
    incumbents = per_agent[per_agent["role"] == "incumbent"]

    say("A. As computed for the paper (compliance counts every agent, including the newcomer)")
    report(module.compute_run_metrics(norms, per_agent), "as published")

    say("\nB. Compliance on incumbent decisions only, as the formula in Section 3.3 is written")
    report(module.compute_run_metrics(norms, incumbents), "incumbents only")

    audit, followed, in_next_prompts = audit_limits(Path(args.raw_runs))
    audit.to_csv(outdir / "limit_parse_audit.csv", index=False)
    parsed = audit[audit["parsed_limit"].notna()]
    false_limits = parsed[parsed["false_limit"]]

    say("\nC. Audit of agreed_limit (model answered N/A, but a number was parsed)")
    say(f"Parsed limits: {len(parsed)}; false: {len(false_limits)}"
        f" (values {false_limits['parsed_limit'].value_counts().to_dict()},"
        f" by condition {false_limits.groupby('condition').size().to_dict()})")
    say(f"False limits followed by another month: {followed};"
        f" stated verbatim in that month's agent prompts: {in_next_prompts}")

    first_one = []
    genuine_after_false = 0
    genuine_ones = parsed[(parsed["parsed_limit"] == 1) & ~parsed["false_limit"]]
    for (cond, seed), run in parsed[parsed["parsed_limit"] == 1].sort_values("round").groupby(["condition", "seed"]):
        first_one.append(bool(run.iloc[0]["false_limit"]))
    for row in genuine_ones.itertuples():
        earlier = false_limits[(false_limits["condition"] == row.condition) & (false_limits["seed"] == row.seed)
                               & (false_limits["round"] < row.round)]
        genuine_after_false += len(earlier) > 0
    say(f"Runs that ever record a 1-ton limit: {len(first_one)}; first such limit is false in: {sum(first_one)}")
    say(f"Genuine 'Answer: 1' records: {len(genuine_ones)}; preceded by a false limit in the same run: {genuine_after_false}")

    flagged = false_limits[["condition", "seed", "round"]].assign(flag=True)
    cleaned = norms.merge(flagged, on=["condition", "seed", "round"], how="left")
    cleaned["agreed_limit"] = cleaned["agreed_limit"].where(cleaned["flag"].isna(), np.nan)
    cleaned = cleaned.drop(columns="flag")

    say("\nD. Sensitivity: false limits treated as 'no agreement'. This corrects the metric only; the false")
    say("limits still influenced the agents during the runs, which only re-running can remove.")
    report(module.compute_run_metrics(cleaned, per_agent), "false limits removed")
    report(module.compute_run_metrics(cleaned, incumbents), "false limits removed + incumbents only")

    (outdir / "paper_numbers.log").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
