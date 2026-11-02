"""Offline CC-109 policy replay of the recorded London window; no external calls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def replay(packet):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from live_contentops.native_desktop_editorial_v1 import validate_pre_writer_outcome
    from live_contentops.native_text_first_v1 import writer_policy

    binding, window = packet["binding"], packet["window"]["window"]
    if (binding["window_id"] != window["opportunity_id"]
            or binding["run_id"] != packet["pre_writer_outcome"].get("run_id", binding["run_id"])
            or packet["selected_plan"]["candidate_id"] != packet["pre_writer_outcome"]["candidate_id"]
            or packet["original_qualified_article_count"] != 0):
        raise ValueError("EXACT_RECORDED_WINDOW_AND_REFUSAL_REQUIRED")
    refusal = validate_pre_writer_outcome(packet["pre_writer_outcome"],
        max_source_requests=packet["source_request_limit"])
    policy = writer_policy({"article_mode": packet["selected_plan"]["article_mode"],
        "source_pack": packet["selected_source_pack"]})
    if policy is not None or refusal["primary_cause"] != "SOURCE_MISSING":
        raise ValueError("RECORDED_ANALYSIS_OR_SOURCE_HOLD_WAS_RELAXED")
    return {"schema_version": "contentops.cc109.recorded_window_dry_run.v1",
        "run_id": binding["run_id"], "window_id": binding["window_id"],
        "recorded_cutoff_utc": binding["cutoff_utc"], "snapshot_sha256": sha256_of(packet),
        "recorded_article_mode": packet["selected_plan"]["article_mode"],
        "source_packet_sha256": sha256_of(packet["selected_source_pack"]),
        "accepted_source_count": len(packet["selected_source_pack"]),
        "source_requests_used": packet["source_requests_used"],
        "text_first_eligible": False, "outcome": refusal["outcome"],
        "primary_cause": refusal["primary_cause"], "reason": refusal["reason"],
        "original_refusal_preserved": True, "new_model_invocations": 0,
        "new_source_requests": 0, "public_transport_calls": 0, "public_write_performed": False,
        "scope": "Offline replay of a real recorded window. The selected analysis lacks substantive source text; "
                 "text-first cannot reclassify it or bypass that hold. Six-destination success is proven separately "
                 "with disposable controlled transports, not as a live result."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, default=ROOT / "docs/publisher/CC-109/recorded-window.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = replay(json.loads(args.packet.read_bytes()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("run_id", "outcome", "primary_cause", "public_write_performed")}))


if __name__ == "__main__":
    main()
