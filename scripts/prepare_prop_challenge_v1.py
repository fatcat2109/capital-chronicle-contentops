"""CC-427: freeze held inputs privately and feed aggregate facts to the newsroom.

No broker connection, account operation, schedule or publication is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.prop_challenge_v1 import evaluate, held_dataset, instant, load_rules, source_document
from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack


def immutable(path, blob):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != blob:
        raise ValueError("PROP_EXISTING_EDITION_CHANGED:" + str(path))
    if not path.exists():
        path.write_bytes(blob)


def prepare(state_root, *, month, private_out, public_out, phase="challenge"):
    state_root = Path(state_root).resolve()
    private_out, public_out = Path(private_out).resolve(), Path(public_out).resolve()
    repository = Path(__file__).resolve().parents[1]
    # Statements contain execution identifiers and account values. They never
    # enter a repository or an input producer's directory.
    if (private_out == repository or repository in private_out.parents
            or private_out == state_root or state_root in private_out.parents):
        raise ValueError("PROP_PRIVATE_OUTPUT_MUST_BE_SEPARATE")
    raw = (state_root / "pilot_economic_inputs.json").read_bytes()
    statement = json.loads(raw)["statement"]
    cutoff = max((statement["known_at_utc"], statement["source_observation"]["coverage_to_utc"]), key=instant)
    root = private_out / ("source-" + hashlib.sha256(raw).hexdigest()[:16])
    immutable(root / "economic.json", raw)
    journal_dir = root / "journals"
    journal_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted((state_root / "intent_journal/current").glob("*.json")):
        blob = path.read_bytes()
        # Content-addressed risk files also preserve later journal revisions.
        immutable(journal_dir / (hashlib.sha256(blob).hexdigest() + ".json"), blob)
    rules = load_rules()
    dataset = held_dataset(root / "economic.json", journal_dir, month=month, cutoff_utc=cutoff)
    report = evaluate(dataset, rules, phase=phase)
    document = source_document(report, rules)
    pack = _source_pack([document])
    if (len(pack) != 1 or pack[0]["canonical_content_text"] != document["canonical_content_text"]
            or pack[0].get("prop_challenge_binding") != document["prop_challenge_binding"]):
        raise ValueError("PROP_NEWSROOM_CONSUMER_NOT_WIRED")
    edition = public_out / (phase + "-" + sha256_of(report)[:16])
    immutable(root / (phase + "-dataset.json"), canonical_bytes(dataset))
    for name, value in (("report.json", report), ("source-document.json", document), ("source-pack.json", pack)):
        immutable(edition / name, canonical_bytes(value))
    immutable(edition / "writer-facts.txt", document["canonical_content_text"].encode())
    trace = {"schema_version": "contentops.prop_private_trace.v1", "report_sha256": sha256_of(report),
             "dataset_sha256": sha256_of(dataset), "report_path": str(edition / "report.json"),
             "sources": dataset["source_manifest"], "excluded_tests": dataset["excluded_operations_tests"],
             "held_account_equity_gap_count": dataset["held_account_equity_gap_count"],
             "held_account_equity_gap_reasons": dataset["held_account_equity_gap_reasons"]}
    immutable(root / (phase + "-trace.json"), canonical_bytes(trace))
    return {"item": "CC-427", "month": month, "phase": phase, "data_cutoff_utc": cutoff,
            "public_edition": str(edition), "private_trace": str(root / (phase + "-trace.json")),
            "report_sha256": sha256_of(report), "trade_count": report["trade_count"],
            "overall": report["overall"], "rules": {r["rule"]: r["verdict"] for r in report["rules"]},
            "consumer": "held_dataset -> evaluate -> source_document -> existing newsroom _source_pack",
            "consumer_readback_exact": True, "publication_state": "NOT_DISPATCHED"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-root", required=True, type=Path)
    parser.add_argument("--month", required=True)
    parser.add_argument("--private-out", required=True, type=Path)
    parser.add_argument("--public-out", required=True, type=Path)
    parser.add_argument("--phase", choices=("challenge", "verification"), default="challenge")
    args = parser.parse_args()
    print(json.dumps(prepare(args.state_root, month=args.month, private_out=args.private_out,
                             public_out=args.public_out, phase=args.phase), indent=2))
