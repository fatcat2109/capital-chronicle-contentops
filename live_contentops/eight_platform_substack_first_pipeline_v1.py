"""Import-safe compatibility surface for the canonical ContentOps orchestrator.

No provider, browser, platform adapter, or private implementation is imported until
``ContentOpsProductionOrchestrator`` accepts and dispatches an exact operation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.headline_data_root_v1 import canonical_headline_sidecar_glob
from live_contentops.production_orchestrator_v1 import ContentOpsProductionOrchestrator

TASK_LABEL = "TASK_CONTENTOPS_FINAL_TEXT_IMAGE_PLATFORM_LIVE_LOCK_AND_V1_0_RELEASE_V1"
SCHEMA_VERSION = "contentops.eight_platform_substack_first_pipeline.v1"
OUTPUT_ROOT = Path("docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1")
DESKTOP_PRIMARY_EDITORIAL_ROUTE = "DESKTOP_PRIMARY"
SDK_FALLBACK_EDITORIAL_ROUTE = "SDK_FALLBACK"
SDK_DIRECT_EDITORIAL_ROUTE = "SDK_DIRECT"
SDK_BENCHMARK_EDITORIAL_ROUTE = "SDK_BENCHMARK"
_EDITORIAL_EXECUTION_ROUTES = frozenset(
    {
        DESKTOP_PRIMARY_EDITORIAL_ROUTE,
        SDK_FALLBACK_EDITORIAL_ROUTE,
        SDK_DIRECT_EDITORIAL_ROUTE,
        SDK_BENCHMARK_EDITORIAL_ROUTE,
    }
)


def _execute(operation: str, **kwargs: Any) -> Any:
    return ContentOpsProductionOrchestrator().execute(operation, **kwargs)


def prepare_text_image_release_candidate(
    *, run_id: str, output_dir: Path, cdp_port: int = 9223, llm_provider: str = "auto"
) -> dict[str, Any]:
    return _execute(
        "prepare_text_image_release_candidate",
        run_id=run_id,
        output_dir=output_dir,
        cdp_port=cdp_port,
        llm_provider=llm_provider,
    )


def prepare_generic_text_image_release_candidate(
    *,
    run_id: str,
    output_dir: Path,
    capital_chronicle_root: Path | None = None,
    evidence_packet_path: Path | None = None,
    as_of_utc: str | None = None,
    cdp_port: int = 9223,
    llm_provider: str = "auto",
) -> dict[str, Any]:
    return _execute(
        "prepare_generic_text_image_release_candidate",
        run_id=run_id,
        output_dir=output_dir,
        capital_chronicle_root=capital_chronicle_root,
        evidence_packet_path=evidence_packet_path,
        as_of_utc=as_of_utc,
        cdp_port=cdp_port,
        llm_provider=llm_provider,
    )


def build_operator_manual_audit_packet(*, output_dir: Path, cdp_port: int = 9223) -> dict[str, Any]:
    return _execute("build_operator_manual_audit_packet", output_dir=output_dir, cdp_port=cdp_port)


def ensure_canonical_edge_publishing_runtime(
    *,
    urls: Sequence[str] = ("https://substack.com/",),
    wait_seconds: float = 12.0,
) -> dict[str, Any]:
    return _execute(
        "ensure_canonical_edge_publishing_runtime",
        urls=urls,
        wait_seconds=wait_seconds,
    )


def run_eight_platform_substack_first_pipeline(
    *,
    run_id: str,
    output_dir: Path,
    cdp_port: int = 9223,
    llm_provider: str = "auto",
    operator_approved_full_live_run: bool = True,
    recover_substack_draft_id: str | None = None,
) -> dict[str, Any]:
    return _execute(
        "run_eight_platform_substack_first_pipeline",
        run_id=run_id,
        output_dir=output_dir,
        cdp_port=cdp_port,
        llm_provider=llm_provider,
        operator_approved_full_live_run=operator_approved_full_live_run,
        recover_substack_draft_id=recover_substack_draft_id,
    )


def run_rolling_x_newsroom_cycle(
    *,
    run_id: str,
    output_dir: Path,
    cutoff_utc: str,
    sidecar_glob: str = canonical_headline_sidecar_glob(),
    window_hours: float = 24.0,
    cdp_port: int = 9223,
    assignment_timeout_seconds: float = 120.0,
    assignment_provider_call: Any = None,
    rolling_input: Any = None,
    prepared_candidate_state: Any = None,
    leaf_checkpoints: Any = None,
    global_checkpoint: Any = None,
    capital_chronicle_root: Path | None = None,
    evidence_acquirer: Any = None,
    story_type_by_cluster: Any = None,
    story_type_classifier: Any = None,
    story_type_provider_call: Any = None,
    story_type_timeout_seconds: float = 300.0,
    article_builder: Any = None,
    editorial_reviewer: Any = None,
    article_reviser: Any = None,
    publication_enabled: bool = True,
    operating_mode: str = "AUTONOMOUS_DEFAULT",
    published_corpus: Sequence[Any] | None = None,
    cc_catalog: Mapping[str, Any] | None = None,
    learning_policy: Mapping[str, Any] | None = None,
    material_event_priority: Mapping[str, Any] | None = None,
    sourceability_observations: Mapping[str, Any] | None = None,
    source_route_health: Mapping[str, Any] | None = None,
    source_discoverer: Any = None,
    autonomous_source_discovery_enabled: bool = False,
    evidence_only_target_count: int | None = None,
    newsroom_production_day_id: str | None = None,
    quota_discovery_prior_accounting: Mapping[str, Any] | None = None,
    quota_discovery_budget: Mapping[str, Any] | None = None,
    quota_discovery_fresh_unseen_available: bool = False,
    destination_readiness_override: Mapping[str, Any] | None = None,
    editorial_execution_route: str = DESKTOP_PRIMARY_EDITORIAL_ROUTE,
    hybrid_arbitration_receipt: Mapping[str, Any] | None = None,
    native_desktop_prepare: bool = False,
) -> dict[str, Any]:
    kwargs = {
        "run_id": run_id,
        "output_dir": output_dir,
        "cutoff_utc": cutoff_utc,
        "sidecar_glob": sidecar_glob,
        "window_hours": window_hours,
        "cdp_port": cdp_port,
        "assignment_timeout_seconds": assignment_timeout_seconds,
        "assignment_provider_call": assignment_provider_call,
        "rolling_input": rolling_input,
        "prepared_candidate_state": prepared_candidate_state,
        "leaf_checkpoints": leaf_checkpoints,
        "global_checkpoint": global_checkpoint,
        "capital_chronicle_root": capital_chronicle_root,
        "evidence_acquirer": evidence_acquirer,
        "story_type_by_cluster": story_type_by_cluster,
        "story_type_classifier": story_type_classifier,
        "story_type_provider_call": story_type_provider_call,
        "story_type_timeout_seconds": story_type_timeout_seconds,
        "editorial_reviewer": editorial_reviewer,
        "article_reviser": article_reviser,
        "publication_enabled": publication_enabled,
        "operating_mode": operating_mode,
        "published_corpus": published_corpus,
        "cc_catalog": cc_catalog,
        "learning_policy": learning_policy,
        "material_event_priority": material_event_priority,
        "sourceability_observations": sourceability_observations,
        "source_route_health": source_route_health,
        "source_discoverer": source_discoverer,
        "autonomous_source_discovery_enabled": autonomous_source_discovery_enabled,
        "evidence_only_target_count": evidence_only_target_count,
        "newsroom_production_day_id": newsroom_production_day_id,
        "quota_discovery_prior_accounting": quota_discovery_prior_accounting,
        "quota_discovery_budget": quota_discovery_budget,
        "quota_discovery_fresh_unseen_available": (
            quota_discovery_fresh_unseen_available
        ),
        "destination_readiness_override": destination_readiness_override,
    }
    route = str(editorial_execution_route or "").strip().upper()
    if route not in _EDITORIAL_EXECUTION_ROUTES:
        raise ValueError("editorial_execution_route_invalid")

    def execute_with_receipt(builder: Any, arbitration: Mapping[str, Any] | None = None) -> Any:
        result = _execute(
            "run_rolling_x_newsroom_cycle", article_builder=builder, **kwargs
        )
        if not isinstance(result, Mapping):
            return result
        annotated = dict(result)
        annotated["editorial_execution_route"] = route
        annotated["desktop_primary_routine_authority"] = True
        if arbitration is not None:
            annotated["hybrid_editorial_arbitration"] = dict(arbitration)
        return annotated

    if article_builder is not None:
        if route != DESKTOP_PRIMARY_EDITORIAL_ROUTE:
            raise ValueError("injected_article_builder_is_desktop_primary_only")
        if publication_enabled and not callable(editorial_reviewer):
            raise ValueError("desktop_primary_editorial_reviewer_required")
        return execute_with_receipt(article_builder)

    if route == DESKTOP_PRIMARY_EDITORIAL_ROUTE:
        # The native Desktop PREPARE phase intentionally reaches the canonical viable-candidate
        # boundary without an in-process writer.  The implementation returns the exact governed
        # worker request and performs no article generation or public write.  COMPLETE later
        # supplies a hash-bound injected builder through this same public facade.
        if not publication_enabled or native_desktop_prepare is True:
            return execute_with_receipt(None)
        raise ValueError("desktop_primary_editorial_builder_required")

    validated_arbitration: Mapping[str, Any] | None = None
    if route == SDK_FALLBACK_EDITORIAL_ROUTE:
        if not isinstance(hybrid_arbitration_receipt, Mapping):
            raise ValueError("sdk_fallback_arbitration_receipt_required")
        from live_contentops.codex_desktop_newsroom_operator_v1 import (
            validate_hybrid_editorial_arbitration_receipt,
        )

        validated_arbitration = validate_hybrid_editorial_arbitration_receipt(
            hybrid_arbitration_receipt,
            expected_runtime_run_id=run_id,
        )
        if (
            validated_arbitration.get("decision") != "START_SDK_FALLBACK"
            or validated_arbitration.get("sdk_fallback_start_authorized") is not True
            or validated_arbitration.get("sdk_fallback_state") != "NOT_STARTED"
        ):
            raise ValueError("sdk_fallback_not_authorized_by_arbitration")
    elif hybrid_arbitration_receipt is not None:
        raise ValueError("hybrid_arbitration_receipt_only_valid_for_sdk_fallback")

    if route == SDK_BENCHMARK_EDITORIAL_ROUTE and publication_enabled:
        raise ValueError("sdk_benchmark_requires_zero_public_write_mode")

    # The official SDK provider is instantiated only for an explicit direct/benchmark route or a
    # hash-validated missed/failed-Desktop fallback. It remains inside the canonical runtime and
    # creates no second orchestrator, scheduler, store, queue, or publisher.
    from live_contentops.official_codex_provider_v1 import (
        OfficialCodexEditorialArticleBuilder,
    )

    with OfficialCodexEditorialArticleBuilder(output_dir=output_dir) as direct_builder:
        return execute_with_receipt(direct_builder, validated_arbitration)


def reconcile_public_substack_for_derivative_resume(
    *, output_dir: Path, cdp_port: int = 9223
) -> dict[str, Any]:
    return _execute(
        "reconcile_public_substack_for_derivative_resume", output_dir=output_dir, cdp_port=cdp_port
    )


def resume_eight_platform_derivatives(
    *, output_dir: Path, cdp_port: int = 9223, platforms: Sequence[str] | None = None
) -> dict[str, Any]:
    return _execute(
        "resume_eight_platform_derivatives",
        output_dir=output_dir,
        cdp_port=cdp_port,
        platforms=platforms,
    )


def reconcile_existing_derivative_readbacks(
    *, output_dir: Path, cdp_port: int = 9223
) -> dict[str, Any]:
    return _execute(
        "reconcile_existing_derivative_readbacks", output_dir=output_dir, cdp_port=cdp_port
    )


def repair_exact_substack_caption_fragment(*, output_dir: Path, cdp_port: int) -> dict[str, Any]:
    return _execute("repair_exact_substack_caption_fragment", output_dir=output_dir, cdp_port=cdp_port)


def repair_exact_treasury_release_candidate_editorial(
    *, output_dir: Path, cdp_port: int
) -> dict[str, Any]:
    return _execute(
        "repair_exact_treasury_release_candidate_editorial", output_dir=output_dir, cdp_port=cdp_port
    )


def repair_final_treasury_auction_logic(*, output_dir: Path, cdp_port: int) -> dict[str, Any]:
    return _execute("repair_final_treasury_auction_logic", output_dir=output_dir, cdp_port=cdp_port)


def reconcile_linkedin_activity_pair(
    *,
    output_dir: Path,
    cdp_port: int,
    accepted_url: str,
    accepted_id: str,
    latest_url: str,
    latest_id: str,
) -> dict[str, Any]:
    return _execute(
        "reconcile_linkedin_activity_pair",
        output_dir=output_dir,
        cdp_port=cdp_port,
        accepted_url=accepted_url,
        accepted_id=accepted_id,
        latest_url=latest_url,
        latest_id=latest_id,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Delegate the complete module CLI before loading any dangerous implementation."""
    return int(_execute("module_cli", argv=argv))


if __name__ == "__main__":
    raise SystemExit(main())
