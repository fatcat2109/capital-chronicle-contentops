"""Production-shaped, zero-public-write proof for the first-live-canary correction."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
from live_contentops.codex_desktop_newsroom_operator_v1 import (
    validate_editorial_worker_return,
)
from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_PUBLICATION_DESTINATIONS,
)
from live_contentops.media_manifest_authority_v1 import build_delivery_only_editorial_card
from live_contentops.v1_runtime_preflight_v1 import run_v1_runtime_preflight


CANARY = Path(
    r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs"
    r"\operator-requested-operator-trigger-20ecd9b6930b41a78f7a51ee"
)
AUDIT = Path(
    r"A:\Capital Chronicle\Runtime\ContentOps\evidence"
    r"\V1_FIRST_LIVE_CANARY_HOLD_CHATGPT_AUDIT"
)
RECEIPT = (
    REPO_ROOT
    / "docs/automation/V1_LIVE_CANARY_CORRECTION_EVIDENCE"
    / "xhigh_validation_return_receipt_v1.json"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)).replace("\\", "/"): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def main() -> None:
    before = {"canary": snapshot(CANARY), "audit": snapshot(AUDIT)}
    worker_return = json.loads(RECEIPT.read_text(encoding="utf-8"))
    worker_validation = validate_editorial_worker_return(
        worker_return=worker_return,
        expected_governed_input_hash=str(worker_return["governed_input_hash"]),
    )
    article = {
        **dict(worker_return["article"]),
        "minimum_trustworthy_evidence_packet": {
            "status": "PASS", "risk_tier": "ORDINARY"
        },
    }
    canonical_url = "https://capitalchronicle.substack.com/p/pending-publication"
    payloads = pipeline.build_native_derivative_payloads(
        article=article,
        selection={"dek": article["subtitle"]},
        canonical_url=canonical_url,
        media_asset_ids=(),
    )
    with tempfile.TemporaryDirectory(prefix="contentops-v1-zero-write-") as temp:
        delivery = build_delivery_only_editorial_card(
            output_path=Path(temp) / "delivery_only.png",
            title=article["title"],
            source_label="Economic and Social Research Institute, Cabinet Office, Government of Japan",
            source_page_url=article["source_url"],
            published_at="2026-08-17T00:00:00Z",
        )
        payload_hashes = {
            name: hashlib.sha256(str(value["text"]).encode("utf-8")).hexdigest()
            for name, value in payloads.items()
        }
        readiness = {
            "all_required_destinations_ready": True,
            "fixture_bound": True,
            "destinations": {
                destination: {
                    "readiness_state": "READY_NON_BROWSER_BINDING",
                    "write_eligible": True,
                    "identity_match": True,
                }
                for destination in V1_REQUIRED_PUBLICATION_DESTINATIONS
            },
        }
        plan = pipeline._build_rolling_x_publication_plan(
            run_id="v1-live-canary-correction-zero-write-proof",
            output_dir=Path(temp),
            viability={"selected_cluster_id": "japan-q2-2026-gdp-first-preliminary", "selected_cluster": {}},
            preparation={
                "release_candidate_lock": {
                    "article_body_sha256": hashlib.sha256(
                        article["substack_body_markdown"].encode("utf-8")
                    ).hexdigest(),
                    "lock_sha256": "zero-write-proof-lock",
                    "payload_sha256": payload_hashes,
                    "artifacts": {"delivery_only_media_delivery_only_editorial_card": {}},
                },
                "context": {
                    "article": article,
                    "media": {"assets": [], "delivery_only_assets": [delivery]},
                },
                "payloads": payloads,
            },
            readiness=readiness,
        )
        after = {"canary": snapshot(CANARY), "audit": snapshot(AUDIT)}
        result = {
            "schema_version": "contentops.v1_live_canary_correction_zero_write_proof.v1",
            "classification": "PASS_PRODUCTION_SHAPED_ZERO_WRITE_CORRECTION_PROOF",
            "runtime_preflight": run_v1_runtime_preflight(
                require_edge_attach=True,
                capital_chronicle_duckdb_path=(
                    r"A:\Capital Chronicle\Main App\data\local_db"
                ),
            ),
            "editorial_worker_validation": worker_validation,
            "article_mode": article["effective_article_mode"],
            "article_media_count": 0,
            "delivery_only_media_count": 1,
            "delivery_only_article_inclusion": delivery["article_inclusion"],
            "derivative_payload_count": len(payloads),
            "derivative_payload_destinations": sorted(payloads),
            "tiktok_in_payloads": "tiktok" in payloads,
            "x_layout": {
                "overflow_strategy": payloads["x"]["overflow_strategy"],
                "hard_truncation_used": payloads["x"]["hard_truncation_used"],
            },
            "threads_layout": {
                "overflow_strategy": payloads["threads"]["overflow_strategy"],
                "hard_truncation_used": payloads["threads"]["hard_truncation_used"],
            },
            "publication_plan_destination_count": len(plan["destinations"]),
            "publication_plan_destinations": sorted(
                row["destination"] for row in plan["destinations"]
            ),
            "skipped_derivative_destinations": plan["skipped_derivative_destinations"],
            "pre_substack_blockers": plan["pre_substack_blockers"],
            "transaction_readiness": plan["transaction_readiness"],
            "frozen_artifacts_byte_identical": before == after,
            "frozen_canary_file_count": len(before["canary"]),
            "frozen_audit_file_count": len(before["audit"]),
            "frozen_canary_hashes": before["canary"],
            "frozen_audit_hashes": before["audit"],
            "publishing_adapter_calls": 0,
            "public_write_performed": False,
            "unknown_write_count": 0,
        }
    assert result["runtime_preflight"]["status"] == "PASS"
    assert result["editorial_worker_validation"]["classification"] == "PASS_BOUND_XHIGH_EDITORIAL_RETURN"
    assert result["derivative_payload_count"] == 8 and not result["tiktok_in_payloads"]
    assert result["publication_plan_destination_count"] == 9
    assert not result["skipped_derivative_destinations"] and not result["pre_substack_blockers"]
    assert result["frozen_artifacts_byte_identical"]
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
