"""Match the exact public article and thread numerals to Main's pinned rows."""

import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from live_contentops import measured_odds_series_v1 as odds
from live_contentops.neo_destination_handoff_v1 import _text
from live_contentops.plan_substack_neo_v1 import body_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared", action="store_true", help="Verify the approved package before public readback")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    piece = json.loads((root / "piece-4.json").read_bytes())
    rows = odds.validate_piece(piece, root / "source")
    if args.prepared:
        report = root / "number-report.json"
        if json.loads(report.read_bytes()) != rows:
            raise ValueError("PREPARED_NUMBER_REPORT_CHANGED")
        print(json.dumps({"status": "PREPARED_NUMBERS_PASS", "numerical_occurrences": len(rows),
                          "table_hash": piece["table_hash"], "report": str(report)}))
        return

    records = json.loads((root / "public-number-observations.json").read_bytes())
    canonical, thread = records["substack"], records["x"]
    observed = {
        "substack_body_markdown": _text(canonical["article_text"]),
        "social_summary": _text("\n".join(post["observed_text"] for post in thread["observed_thread"])),
    }
    for field, text in observed.items():
        content = re.sub(r"https?://\S+", "", text)
        expected = [match.group() for match in odds._numbers(piece["article"][field], piece["table_hash"])]
        actual = [match.group() for match in odds._numbers(content, piece["table_hash"])]
        if actual != expected:
            raise ValueError("PUBLIC_NUMBER_SEQUENCE_DIFFERS:" + field)
    for row in rows:
        field = row["field"]
        if field not in observed or _text(body_text(row["public_span"])) not in observed[field]:
            raise ValueError("PUBLIC_NUMBER_SPAN_NOT_OBSERVED:" + row["public_span"])
        row["observed_on_page"] = True
        row["public_object_url"] = (canonical if field == "substack_body_markdown" else thread)["public_object_url"]

    report = root / "public-number-report.json"
    report.write_bytes((json.dumps(rows, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": "PASS", "numerical_occurrences": len(rows),
                      "table_hash": piece["table_hash"], "report": str(report)}))


if __name__ == "__main__":
    main()
