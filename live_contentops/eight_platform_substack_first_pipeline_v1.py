"""Import-safe compatibility surface for the canonical ContentOps orchestrator.

No provider, browser, platform adapter, or private implementation is imported until
``ContentOpsProductionOrchestrator`` accepts and dispatches an exact operation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from live_contentops.production_orchestrator_v1 import ContentOpsProductionOrchestrator

TASK_LABEL = "TASK_CONTENTOPS_FINAL_TEXT_IMAGE_PLATFORM_LIVE_LOCK_AND_V1_0_RELEASE_V1"
SCHEMA_VERSION = "contentops.eight_platform_substack_first_pipeline.v1"
OUTPUT_ROOT = Path("docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1")


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
    sidecar_glob: str = "headline_ingestion/data/intake/headline_sidecars/*.jsonl",
    window_hours: float = 24.0,
    cdp_port: int = 9223,
    assignment_timeout_seconds: float = 120.0,
    assignment_provider_call: Any = None,
    evidence_acquirer: Any = None,
    story_type_by_cluster: Any = None,
    article_builder: Any = None,
    editorial_reviewer: Any = None,
    article_reviser: Any = None,
    publication_enabled: bool = True,
) -> dict[str, Any]:
    return _execute(
        "run_rolling_x_newsroom_cycle",
        run_id=run_id,
        output_dir=output_dir,
        cutoff_utc=cutoff_utc,
        sidecar_glob=sidecar_glob,
        window_hours=window_hours,
        cdp_port=cdp_port,
        assignment_timeout_seconds=assignment_timeout_seconds,
        assignment_provider_call=assignment_provider_call,
        evidence_acquirer=evidence_acquirer,
        story_type_by_cluster=story_type_by_cluster,
        article_builder=article_builder,
        editorial_reviewer=editorial_reviewer,
        article_reviser=article_reviser,
        publication_enabled=publication_enabled,
    )


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
