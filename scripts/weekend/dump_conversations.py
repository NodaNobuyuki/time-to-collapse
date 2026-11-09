"""Dump every run's monthly conversations from log_env.json to readable Markdown."""
import csv, json, sys
from pathlib import Path
root, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
for row in csv.DictReader(open(root / "runs_manifest.csv")):
    if row["status"] != "ok": continue
    recs = json.loads((root / row["results_dir"] / "log_env.json").read_text())
    name = f'{row["condition"]}_s{row["seed"]}'
    lines = [f"# {name}\n"]
    for r in recs:
        rd = int(r["round"]) + 1
        if r["action"] == "harvesting":
            lines.append(f'- _month {rd} harvest: **{r["agent_name"] or r["agent_id"]}** wanted {r["wanted_resource"]}, got {r["resource_collected"]} (pool before {r["resource_in_pool_before_harvesting"]})_')
        elif r["action"] == "utterance":
            if r["agent_name"] == "Mayor": lines.append(f"\n## Month {rd} conversation\n")
            lines.append(f'**{r["agent_name"]}:** {r["utterance"]}\n')
        elif r["action"] == "conversation_resource_limit":
            lines.append(f'> **Agreed limit for next month:** {r["resource_limit"]} tons\n')
    (out / f"{name}.md").write_text("\n".join(lines))
    print("wrote", name)
