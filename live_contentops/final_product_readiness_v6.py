"""TASK 0059 final product readiness packet builder.

Local-only summary over existing V6 readiness bundle outputs and TASK 0057
Substack acceptance evidence. No network, browser, env, credential, or platform
reads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_0059"
SCHEMA_VERSION = "1.0.0"
DEFAULT_OUTPUT = Path("docs/automation/V6_FINAL_PRODUCT_READINESS/final_product_readiness_packet.json")
DEFAULT_BUNDLE = Path("docs/automation/V6_READINESS_EVIDENCE_BUNDLE/readiness_evidence_bundle_packet.json")
DEFAULT_MATRIX = Path("docs/automation/V6_READINESS_EVIDENCE_BUNDLE/v6_pipeline_status_matrix.json")
DEFAULT_SUBSTACK_ACCEPTANCE = Path("docs/automation/V6_SUBSTACK_OPERATOR_DRAFT_COMMAND/task_0057_substack_live_publish_acceptance_reconciliation.json")


def _load_json(path: str | Path) -> dict[str, Any] | list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _safe_exists(path: str | Path) -> bool:
    return Path(path).is_file()


def build_final_product_readiness_packet(
    bundle_path: str | Path = DEFAULT_BUNDLE,
    matrix_path: str | Path = DEFAULT_MATRIX,
    substack_acceptance_path: str | Path = DEFAULT_SUBSTACK_ACCEPTANCE,
) -> dict[str, Any]:
    missing = [
        str(path)
        for path in (bundle_path, matrix_path, substack_acceptance_path)
        if not _safe_exists(path)
    ]
    bundle = _load_json(bundle_path) if _safe_exists(bundle_path) else {}
    matrix = _load_json(matrix_path) if _safe_exists(matrix_path) else []
    acceptance = _load_json(substack_acceptance_path) if _safe_exists(substack_acceptance_path) else {}

    lane_count = len(matrix) if isinstance(matrix, list) else 0
    blocked_lanes = [
        row.get("lane_name", "UNKNOWN")
        for row in matrix
        if isinstance(row, dict) and row.get("unresolved_blockers")
    ]
    live_success_accepted = bool(acceptance.get("can_accept_substack_live_publish_success"))
    public_url_verified = bool(acceptance.get("public_url_verified"))

    readiness_status = (
        "FINAL_PRODUCT_READY_FOR_LOCAL_OPERATOR_REVIEW_ONLY"
        if not missing and live_success_accepted
        else "FINAL_PRODUCT_READINESS_BLOCKED"
    )
    digest_payload = json.dumps(
        {
            "task": TASK_LABEL,
            "bundle": bundle.get("readiness_evidence_bundle_packet_id"),
            "lane_count": lane_count,
            "live_success_accepted": live_success_accepted,
            "public_url_verified": public_url_verified,
            "missing": missing,
        },
        sort_keys=True,
    ).encode("utf-8")

    return {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "packet_id": "final_product_readiness_" + hashlib.sha256(digest_payload).hexdigest()[:16],
        "readiness_status": readiness_status,
        "final_product_phase": "v6_final_product_readiness_packet_and_v5_read_only_panel",
        "source_readiness_bundle": str(bundle_path).replace("\\", "/"),
        "source_pipeline_matrix": str(matrix_path).replace("\\", "/"),
        "source_substack_acceptance": str(substack_acceptance_path).replace("\\", "/"),
        "lanes_summarized": lane_count,
        "blocked_lanes": blocked_lanes,
        "substack_live_publish_success_accepted": live_success_accepted,
        "substack_public_url_verified": public_url_verified,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "browser_or_cdp_action_performed": False,
        "network_call_performed": False,
        "env_or_credential_read_performed": False,
        "public_postable": False,
        "raw_secret_output": False,
        "private_url_or_dom_recorded": False,
        "missing_inputs": missing,
        "operator_next_action": "Review V5 Final Product Readiness panel; do not rerun live publish; optionally supply public URL for later safe audit.",
        "ui_panel": {
            "surface": "ui/contentops_v5/",
            "view_id": "final_product_readiness",
            "read_only": True,
            "network_free": True,
        },
    }


def write_packet(output_path: str | Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    packet = build_final_product_readiness_packet()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build TASK 0059 final product readiness packet")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    packet = write_packet(args.output)
    print(json.dumps({"packet_id": packet["packet_id"], "readiness_status": packet["readiness_status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
