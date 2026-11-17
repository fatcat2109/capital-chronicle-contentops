"""List each approved public numeral beside its exact Main value and readback."""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from live_contentops import measured_odds_series_v1 as odds
from live_contentops.neo_destination_handoff_v1 import _text
from live_contentops.plan_substack_neo_v1 import body_text

root = Path(__file__).resolve().parent
piece = json.loads((root / "piece-3.json").read_bytes())
records = json.loads((root / "public-number-observations.json").read_bytes())
canonical = records["substack"]
thread = records["x"]
observed = {
    "substack_body_markdown": _text(canonical["article_text"]),
    "social_summary": _text("\n".join(p["observed_text"] for p in thread["observed_thread"])),
}
rows = odds.number_report(piece, root / "source")
for row in rows:
    row["observed_on_page"] = _text(body_text(row["public_span"])) in observed[row["field"]]
    row["public_object_url"] = (canonical if row["field"] == "substack_body_markdown" else thread)["public_object_url"]
    if not row["observed_on_page"]:
        raise ValueError("PUBLIC_NUMBER_SPAN_NOT_OBSERVED:" + row["public_span"])
path = root / "public-number-report.json"
path.write_bytes((json.dumps(rows, indent=2) + "\n").encode())
print(json.dumps({"status": "PASS", "numerical_occurrences": len(rows),
                  "table_hash": piece["table_hash"], "report": str(path)}))
