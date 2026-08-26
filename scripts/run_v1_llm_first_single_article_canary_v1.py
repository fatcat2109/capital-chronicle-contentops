"""Run one genuine current-headline LLM-first / validate-after zero-write V1 canary."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from live_contentops.codex_desktop_newsroom_operator_v1 import (
    CANONICAL_PRODUCTION_OUTPUT_ROOT,
    CANONICAL_PRODUCTION_STORE_PATH,
    load_terminal_editorial_continuity,
)
from live_contentops.eight_platform_substack_first_pipeline_v1 import (
    run_rolling_x_newsroom_cycle,
)
from live_contentops.headline_data_root_v1 import canonical_headline_sidecar_glob
from live_contentops.llm_first_validate_after_v1 import LlmFirstValidateAfterProvider
from live_contentops.official_codex_provider_v1 import OfficialCodexProviderError
from live_contentops.newsroom_assignment_scheduler_v1 import (
    load_rolling_x_headline_sidecars,
)
from live_contentops.native_desktop_production_handoff_v1 import (
    semantic_resume_bindings_from_probe,
)
from live_contentops.newsroom_production_day_v1 import (
    newsroom_production_day_id,
    qualify_zero_write_article,
)


def _published_memory(continuity: Mapping[str, Any]) -> list[dict[str, Any]]:
    memory = continuity.get("published_memory") or {}
    result = [
        {"story_identity": str(value)}
        for value in memory.get("story_identities") or []
        if str(value)
    ]
    result.extend(
        {"update_chain_identity": str(value)}
        for value in memory.get("update_chain_identities") or []
        if str(value)
    )
    return result


def run(*, output_dir: Path, cutoff_utc: str) -> dict[str, Any]:
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    rolling_input = load_rolling_x_headline_sidecars(
        cutoff_utc=cutoff_utc,
        sidecar_glob=canonical_headline_sidecar_glob(),
        window_hours=24.0,
    )
    continuity = load_terminal_editorial_continuity(
        store_path=CANONICAL_PRODUCTION_STORE_PATH,
        output_root=CANONICAL_PRODUCTION_OUTPUT_ROOT,
    )
    provider = LlmFirstValidateAfterProvider(
        output_dir=output_dir,
        published_memory=_published_memory(continuity),
    )
    activity_path = output_dir / "runtime_activity_v1.json"
    existing_activity = (
        json.loads(activity_path.read_text(encoding="utf-8"))
        if activity_path.exists()
        else {}
    )
    run_id = str(existing_activity.get("work_item_id") or output_dir.name)
    checkpoint_kwargs: dict[str, Any] = {}
    assignment_path = output_dir / "rolling_x_assignment_v1.json"
    story_routing_path = output_dir / "rolling_x_story_routing_v1.json"
    if assignment_path.exists() and story_routing_path.exists():
        try:
            assignment_checkpoint = json.loads(
                assignment_path.read_text(encoding="utf-8")
            )
            bindings = semantic_resume_bindings_from_probe(
                {
                    "assignment": assignment_checkpoint,
                    "story_routing": json.loads(
                        story_routing_path.read_text(encoding="utf-8")
                    ),
                }
            )
            persisted_intake_path = output_dir / "rolling_x_intake_v1.json"
            persisted_intake = json.loads(
                persisted_intake_path.read_text(encoding="utf-8")
            )
        except (OSError, TypeError, ValueError):
            # Presence alone does not make an older checkpoint reusable. If its exact
            # semantic bindings are missing or stale, recompute from current governed
            # intake instead of crashing or weakening the resume contract.
            checkpoint_kwargs = {}
        else:
            checkpoint_kwargs = {
                "leaf_checkpoints": bindings["leaf_checkpoints"],
                "global_checkpoint": bindings["global_checkpoint"],
                "story_type_by_cluster": bindings["story_type_by_cluster"],
                "assignment_override": assignment_checkpoint,
            }
            rolling_input = persisted_intake
            cutoff_utc = str(bindings["global_checkpoint"]["cutoff_time_utc"])
    try:
        result = run_rolling_x_newsroom_cycle(
            run_id=run_id,
            output_dir=output_dir,
            cutoff_utc=cutoff_utc,
            rolling_input=rolling_input,
            published_corpus=[],
            publication_enabled=False,
            operating_mode="SHADOW_ONLY",
            llm_first_editorial_provider=provider,
            **checkpoint_kwargs,
        )
    except OfficialCodexProviderError as exc:
        coordinator_path = output_dir / "llm_first_coordinator_selection_v1.json"
        coordinator = (
            json.loads(coordinator_path.read_text(encoding="utf-8"))
            if coordinator_path.exists()
            else {}
        )
        failure = {
            "schema_version": "contentops.v1_llm_first_single_article_canary_attempt.v1",
            "classification": "BLOCKED_HARD_EXTERNAL_CODEX_PROVIDER",
            "exact_next_blocker": f"OFFICIAL_CODEX_PROVIDER_{exc.phase}:{exc.code}",
            "model_turn_completed": exc.model_turn_completed,
            "coordinator_selection": coordinator.get("selection"),
            "model_calls": [
                {
                    "role": ((coordinator.get("coordinator_receipt") or {}).get(
                        "provider_input_identity"
                    ) or {}).get("role"),
                    "model": (coordinator.get("coordinator_receipt") or {}).get("model"),
                    "reasoning_effort": (
                        coordinator.get("coordinator_receipt") or {}
                    ).get("reasoning_effort"),
                    "usage": dict(
                        (coordinator.get("coordinator_receipt") or {}).get(
                            "turn_result_usage"
                        )
                        or {}
                    ),
                }
            ]
            if coordinator
            else [],
            "maximum_reasoning_effort": "HIGH",
            "above_high_call_count": 0,
            "qualified_article_count": 0,
            "derivative_intent_count": 0,
            "public_writes": 0,
            "provider_publication_writes": 0,
            "unknown_write_count": 0,
            "retry_authorized_after_external_state_change": True,
        }
        failure_path = output_dir / "llm_first_canary_external_blocker_v1.json"
        failure_path.write_text(
            json.dumps(failure, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return {**failure, "receipt_path": str(failure_path)}
    qualification = qualify_zero_write_article(
        result=result,
        output_dir=output_dir,
        production_day_id=newsroom_production_day_id(cutoff_utc),
        parent_window_id=run_id,
    )
    article_path = output_dir / "article_manifest_v1.json"
    article = json.loads(article_path.read_text(encoding="utf-8")) if article_path.exists() else {}
    llm_summary = dict(result.get("llm_first_validate_after") or {})
    packet = {
        "schema_version": "contentops.v1_llm_first_single_article_canary_receipt.v1",
        "classification": (
            "PASS_V1_LLM_FIRST_SINGLE_ARTICLE_ZERO_WRITE_CANARY"
            if qualification.get("qualified") is True
            else "FAIL_V1_LLM_FIRST_SINGLE_ARTICLE_ZERO_WRITE_CANARY"
        ),
        "run_id": run_id,
        "cutoff_utc": cutoff_utc,
        "current_ingested_headline_count": int(
            (rolling_input.get("counts") or {}).get("accepted") or 0
        ),
        "published_memory": continuity.get("published_memory"),
        "chosen_story": (result.get("candidate_walk") or {}).get(
            "selected_publication_candidate"
        ),
        "article": {
            "title": article.get("title"),
            "dek": article.get("dek") or article.get("subtitle"),
            "body": article.get("substack_body_markdown"),
            "mode": article.get("resolved_article_mode")
            or article.get("effective_article_mode"),
            "supported_material_claims": article.get("supported_claims"),
            "accepted_source_bindings": article.get("accepted_source_identities")
            or article.get("source_bindings"),
            "claims_removed_or_narrowed": (
                llm_summary.get("post_generation_verification") or {}
            ).get("unsupported_claims_removed_or_narrowed"),
        },
        "model_calls": llm_summary.get("model_calls"),
        "maximum_reasoning_effort": llm_summary.get("maximum_reasoning_effort"),
        "above_high_call_count": llm_summary.get("above_high_call_count"),
        "candidate_attempts": llm_summary.get("candidate_attempts"),
        "network_requests": llm_summary.get("network_requests"),
        "qualified_article_count": int(qualification.get("qualified") is True),
        "derivative_intent_count": len(
            qualification.get("derivative_package_intents") or []
        ),
        "public_writes": int(bool(result.get("public_write_performed"))),
        "provider_publication_writes": int(
            llm_summary.get("provider_publication_writes") or 0
        ),
        "unknown_write_count": int(bool(result.get("unknown_write_detected"))),
        "actual_article_artifact_path": str(article_path),
        "qualification": qualification,
        "canonical_cycle_classification": result.get("classification"),
        "canonical_cycle_exact_next_blocker": result.get("exact_next_blocker"),
    }
    packet_path = output_dir / "llm_first_single_article_canary_receipt_v1.json"
    packet_path.write_text(
        json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {**packet, "receipt_path": str(packet_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--cutoff-utc",
        default=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    args = parser.parse_args()
    result = run(output_dir=args.output_dir, cutoff_utc=args.cutoff_utc)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result["qualified_article_count"] == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
