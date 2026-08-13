"""Run genuine current newsroom opportunities with public writes mechanically disabled."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import (
    _run_rolling_x_newsroom_cycle,
)
from live_contentops.newsroom_assignment_scheduler_v1 import (
    build_prepared_rolling_x_candidate_state,
)
from live_contentops.visual_asset_discovery_v1 import discover_visual_assets_for_article


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _taxonomy(evidence: Mapping[str, Any]) -> str:
    if evidence.get("classification") == "ELIGIBLE_ARTICLE_READY":
        return "ELIGIBLE_ARTICLE_READY"
    blockers = {
        str(value) for value in (evidence.get("blockers") or [])
    }
    blocker_text = " ".join(sorted(blockers)).casefold()
    exact = str(evidence.get("exact_next_blocker") or "").casefold()
    joined = blocker_text + " " + exact
    if "insufficient_reader_value" in joined:
        return "INSUFFICIENT_READER_VALUE"
    if any(value in joined for value in ("unbound", "binding", "system", "checkpoint")):
        return "SYSTEM_OR_BINDING_BLOCK"
    if any(value in joined for value in ("policy_ceremony", "supported_claims_missing")):
        return "POLICY_CEREMONY_BLOCK"
    if any(value in joined for value in ("access", "http", "dns", "request_budget", "source_unavailable")):
        return "SOURCE_ACCESS_FAILURE"
    if any(value in joined for value in ("risk", "corrobor", "numeric", "factual", "claim")):
        return "FACTUAL_OR_RISK_BLOCK"
    intake = evidence.get("intake") if isinstance(evidence.get("intake"), Mapping) else {}
    if int((intake.get("counts") or {}).get("accepted") or 0) == 0:
        return "DATA_NOT_AVAILABLE"
    editorial = (
        evidence.get("editorial_cycle")
        if isinstance(evidence.get("editorial_cycle"), Mapping)
        else {}
    )
    if editorial.get("status") == "PASS" and len(_release_payloads(evidence)) == 9:
        return "ELIGIBLE_ARTICLE_READY"
    return "FACTUAL_OR_RISK_BLOCK"


def _release_payloads(evidence: Mapping[str, Any]) -> dict[str, Any]:
    preparation = (
        evidence.get("release_candidate_preparation")
        if isinstance(evidence.get("release_candidate_preparation"), Mapping)
        else {}
    )
    payloads = preparation.get("payloads")
    return dict(payloads) if isinstance(payloads, Mapping) else {}


def run(
    *,
    output_dir: Path,
    sidecar_glob: str,
    opportunities: int,
    frozen_rolling_input_path: Path | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    frozen_rolling_input = None
    prepared_candidate_state = None
    if frozen_rolling_input_path is not None:
        frozen_rolling_input = json.loads(
            frozen_rolling_input_path.read_text(encoding="utf-8")
        )
        prepared_candidate_state = build_prepared_rolling_x_candidate_state(
            rolling_input=frozen_rolling_input,
            prepared_at_utc=str(frozen_rolling_input.get("cutoff_time_utc") or ""),
        )
    rows: list[dict[str, Any]] = []
    for number in range(1, opportunities + 1):
        cutoff = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        opportunity_dir = output_dir / f"shadow_opportunity_{number}"
        evidence = _run_rolling_x_newsroom_cycle(
            run_id=f"v1-yield-closeout-shadow-{number}-{cutoff[:19].replace(':', '')}",
            output_dir=opportunity_dir,
            cutoff_utc=cutoff,
            sidecar_glob=sidecar_glob,
            rolling_input=frozen_rolling_input,
            prepared_candidate_state=prepared_candidate_state,
            publication_enabled=False,
            operating_mode="KILL_SWITCH",
        )
        article = evidence.get("article") if isinstance(evidence.get("article"), Mapping) else {}
        visual_discovery: dict[str, Any] = {
            "status": "NOT_ATTEMPTED_NO_ARTICLE",
            "candidate_count": 0,
            "eligible_count": 0,
            "selected_count": 0,
            "provider_failures": [],
            "publication_authority": False,
        }
        if article:
            try:
                visual_discovery = discover_visual_assets_for_article(
                    article, maximum_selected=2
                )
            except Exception as exc:
                visual_discovery = {
                    "status": "ATTEMPTED_PROVIDER_FAILURE",
                    "candidate_count": 0,
                    "eligible_count": 0,
                    "selected_count": 0,
                    "provider_failures": [{"failure_class": type(exc).__name__}],
                    "publication_authority": False,
                }
            _write_json(
                opportunity_dir / "purposeful_visual_discovery_v1.json",
                visual_discovery,
            )
        taxonomy = _taxonomy(evidence)
        release_payloads = _release_payloads(evidence)
        row = {
            "opportunity": number,
            "cutoff_utc": cutoff,
            "classification": evidence.get("classification"),
            "taxonomy": taxonomy,
            "exact_next_blocker": evidence.get("exact_next_blocker"),
            "selected_cluster_id": (evidence.get("ranked_viability") or {}).get(
                "selected_cluster_id"
            ),
            "selected_rank": (evidence.get("ranked_viability") or {}).get("selected_rank"),
            "writer_calls": (evidence.get("critical_path_telemetry") or {}).get(
                "article_writer_semantic_calls", 0
            ),
            "mandatory_semantic_review_calls": (
                evidence.get("critical_path_telemetry") or {}
            ).get("mandatory_semantic_review_calls", 0),
            "media_discovery_status": visual_discovery.get("status"),
            "media_candidate_count": int(visual_discovery.get("candidate_count") or 0),
            "media_eligible_count": int(visual_discovery.get("eligible_count") or 0),
            "media_selected_count": int(visual_discovery.get("selected_count") or 0),
            "media_discovery_evidence_path": (
                str(opportunity_dir / "purposeful_visual_discovery_v1.json")
                if article
                else None
            ),
            "package_count": len(release_payloads),
            "package_destinations": sorted(release_payloads),
            "public_write_performed": bool(evidence.get("public_write_performed")),
            "publishing_adapter_called": bool(evidence.get("publishing_adapter_called")),
            "operating_mode": evidence.get("operating_mode"),
            "evidence_path": str(
                opportunity_dir / "rolling_x_newsroom_cycle_evidence_v1.json"
            ),
        }
        rows.append(row)
        if row["public_write_performed"] or row["publishing_adapter_called"]:
            raise RuntimeError("zero_write_shadow_boundary_violated")
    summary = {
        "schema_version": "contentops.v1_current_yield_shadow_summary.v1",
        "operating_mode": "KILL_SWITCH",
        "publication_enabled": False,
        "genuine_current_sidecar_glob": sidecar_glob,
        "frozen_rolling_input_path": (
            str(frozen_rolling_input_path) if frozen_rolling_input_path else None
        ),
        "prepared_candidate_state_used": prepared_candidate_state is not None,
        "opportunity_count": len(rows),
        "opportunities": rows,
        "zero_public_writes": all(not row["public_write_performed"] for row in rows),
        "publishing_adapter_calls": sum(bool(row["publishing_adapter_called"]) for row in rows),
        "taxonomy_counts": {
            value: sum(row["taxonomy"] == value for row in rows)
            for value in sorted({row["taxonomy"] for row in rows})
        },
        "publication_authority": False,
    }
    _write_json(output_dir / "shadow_summary_v1.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sidecar-glob", required=True)
    parser.add_argument("--opportunities", type=int, default=3, choices=range(1, 6))
    parser.add_argument("--frozen-rolling-input", type=Path)
    args = parser.parse_args()
    summary = run(
        output_dir=args.output_dir.resolve(),
        sidecar_glob=args.sidecar_glob,
        opportunities=args.opportunities,
        frozen_rolling_input_path=(
            args.frozen_rolling_input.resolve() if args.frozen_rolling_input else None
        ),
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
