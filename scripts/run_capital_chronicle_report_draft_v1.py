"""One resumable, draft-only Main report opportunity through the existing Simple owner."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    LatestReportDeliveryTracker,
    run_admitted_report_through_simple,
    validate_latest_report_bytes,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.headline_data_root_v1 import canonical_headline_sidecar_glob
from live_contentops.newsroom_assignment_scheduler_v1 import (
    load_rolling_x_headline_sidecars,
)
from live_contentops.published_corpus_read_model_v1 import (
    load_canonical_published_memory_read_only,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle-dir",
        type=Path,
        required=True,
        help="Main schema/report/envelope and producer_binding.json directory",
    )
    parser.add_argument(
        "--store",
        type=Path,
        required=True,
        help="Explicit existing-owner store, isolated for a manual proof",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cutoff-utc", default=None)
    parser.add_argument(
        "--published-memory-store",
        type=Path,
        default=Path(
            r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3"
        ),
    )
    parser.add_argument(
        "--published-memory-output-root",
        type=Path,
        default=Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs"),
    )
    args = parser.parse_args(argv)
    root = args.bundle_dir
    binding = json.loads((root / "producer_binding.json").read_bytes())
    cutoff = args.cutoff_utc or datetime.now(timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    tracker = LatestReportDeliveryTracker(ContentOpsDurableStore(args.store))
    validation = None
    receipt_id = None
    for prefix in ("parent_", ""):
        if prefix and not (root / "parent_envelope.json").is_file():
            continue
        validation = validate_latest_report_bytes(
            (root / (prefix + "envelope.json")).read_bytes(),
            report_bytes=[(root / (prefix + "report.json")).read_bytes()],
            expected_cutoff_utc=cutoff,
            envelope_schema_bytes=(
                root / "CapitalChronicleLatestAnalysisReportEnvelopeV1.schema.json"
            ).read_bytes(),
            report_schema_bytes=(
                root / "CapitalChronicleAssetAnalysisReportV1.schema.json"
            ).read_bytes(),
            producer_binding=binding,
        )
        receipt_id = "manual-main-" + validation["raw_sha256"]
        tracker.consume(validation, receipt_id=receipt_id)
    if not validation or validation["status"] != "ADMITTED":
        print(
            json.dumps(
                {
                    "classification": "REPORT_BLOCKED",
                    "blockers": (validation or {}).get("blockers"),
                }
            )
        )
        return 2
    intake = load_rolling_x_headline_sidecars(
        cutoff_utc=cutoff,
        sidecar_glob=canonical_headline_sidecar_glob(),
        window_hours=24.0,
    )
    memory, proof = load_canonical_published_memory_read_only(
        store_path=args.published_memory_store,
        output_root=args.published_memory_output_root,
    )
    result = run_admitted_report_through_simple(
        validation,
        tracker=tracker,
        receipt_id=receipt_id,
        output_dir=args.output_dir,
        cutoff_utc=cutoff,
        rolling_input=intake,
        published_memory=list(memory),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        k: result.get(k)
        for k in (
            "classification",
            "exact_next_blocker",
            "model_execution_state",
            "report_id",
            "report_version",
            "draft_count",
            "preview_count",
            "logical_model_invocation_count",
            "public_write_performed",
        )
    }
    summary.update(counts=tracker.counts(), published_memory_proof=proof)
    (args.output_dir / "report_draft_cycle_receipt.json").write_bytes(
        (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode()
    )
    print(json.dumps(summary))
    return (
        0
        if result["classification"]
        in {"DRAFT_READY", "NO_MATERIAL_CHANGE_NOOP", "INVALIDATION_WITHDRAWAL_NOOP"}
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
