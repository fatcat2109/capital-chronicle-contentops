from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "docs/status/current_project_status.json"
MASTER = ROOT / "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md"
CONTRACT = ROOT / "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/platform_delivery_contract_v1.json"
EVIDENCE = ROOT / "docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/run_evidence_v1.json"
MATRIX = ROOT / "docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/final_platform_matrix_v1.json"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_status_promotes_live_substack_first_authority() -> None:
    status = _json(STATUS)
    assert status["latest_accepted_task"] == "TASK_CONTENTOPS_HEAVY_NORTH_STAR_MASTER_PLAN_REBUILD_AND_MULTI_PLATFORM_LIVE_OUTPUT_REPAIR_V2"
    assert status["current_run_classification"] == "PASS_SUBSTACK_FIRST_TEXT_IMAGE_DISTRIBUTION_V1"
    assert status["canonical_substack_url"].startswith("https://capitalchronicle.substack.com/p/")
    assert status["canonical_backend_runner"] == "live_contentops.eight_platform_substack_first_pipeline_v1"


def test_live_evidence_and_status_agree() -> None:
    status = _json(STATUS)
    evidence = _json(EVIDENCE)
    assert evidence["run_id"] == status["current_run_id"]
    assert evidence["classification"] == status["current_run_classification"]
    assert evidence["results"]["substack"]["public_url"] == status["canonical_substack_url"]
    assert evidence["results"]["youtube"]["public_url"] == status["platform_matrix"]["youtube"]["url"]
    assert evidence["results"]["tiktok"]["status"] == "BLOCKED_TIKTOK_CANONICAL_PROFILE_NOT_AUTHENTICATED"


def test_delivery_contract_is_community_only_for_default_youtube() -> None:
    contract = _json(CONTRACT)
    youtube = contract["destinations"]["youtube"]
    assert youtube["default_surface"] == "community_post"
    assert {"video", "short"}.issubset(set(youtube["forbidden_default_surfaces"]))
    assert contract["overflow_policy"] == "ordered_root_reply_chain_no_hard_truncation"


def test_final_matrix_normalizes_frozen_and_corrected_readbacks() -> None:
    matrix = _json(MATRIX)
    for platform in ("substack", "telegram", "discord", "x", "threads", "linkedin", "facebook_page", "instagram_business", "youtube"):
        row = matrix["destinations"][platform]
        assert row["status"] == "SUCCESS"
        assert row["provider_readback_verified"] is True
        assert row["public_text_verified"] is True
        assert row["canonical_link_verified"] is True
    assert matrix["destinations"]["tiktok"]["status"] == "BLOCKED_TIKTOK_CANONICAL_PROFILE_NOT_AUTHENTICATED"
    assert matrix["primary_media_sha256"] == "b83584745931f60d976bde11b383ef3ca75c5cfed254c2c59af7a7513572a7af"


def test_master_rejects_click_only_success_and_dom_media_selection() -> None:
    text = MASTER.read_text(encoding="utf-8").lower()
    assert "no success from a click" in text
    assert "do not scrape the public substack dom" in text
    assert "hard truncation" in text
    assert "youtube community" in text
