"""Tests for the pre-alpha content seed library and editorial calendar (0103).

Local-only, deterministic. No network/provider/LLM/platform/credential access.
"""

import os

from live_contentops import pre_alpha_seed_library as lib

FIXTURE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "fixtures",
    "pre_alpha_seed_library",
    "valid_seed_library_with_one_blocked.json",
)


def _load():
    import json
    with open(os.path.abspath(FIXTURE), "r", encoding="utf-8") as f:
        return json.load(f)


def test_schemas_load():
    assert lib.load_library_schema()["title"] == "PreAlphaContentSeedLibrary"
    assert lib.load_calendar_schema()["title"] == "PreAlphaEditorialCalendarPlan"


def test_library_validation_marks_safe_and_blocked():
    result = lib.validate_library_file(FIXTURE)
    # Top-level library is structurally valid.
    assert result["valid"] is True
    sr = result["seed_results"]
    assert sr["seed_macro_edu_001"]["valid"] is True
    assert sr["seed_build_in_public_001"]["valid"] is True
    assert sr["seed_data_sufficiency_001"]["valid"] is True
    # The signal/market-note seed must be blocked.
    assert sr["seed_blocked_signal_001"]["valid"] is False
    assert sr["seed_blocked_signal_001"]["errors"]


def test_blocked_seed_has_guardrail_reasons():
    result = lib.validate_library_file(FIXTURE)
    errs = result["seed_results"]["seed_blocked_signal_001"]["errors"]
    # Forbidden language and/or numeric market claim must be flagged.
    joined = " ".join(errs)
    assert (
        "forbidden_language" in joined
        or "numeric_market_claim" in joined
        or "market_note" in joined
    )


def test_content_zone_not_allowed_blocks_seed():
    library = _load()
    library["seeds"][0]["content_zone"] = "not_a_zone"
    result = lib.validate_library(library)
    assert result["seed_results"]["seed_macro_edu_001"]["valid"] is False
    assert "content_zone_not_allowed" in result["seed_results"]["seed_macro_edu_001"]["errors"]


def test_duplicate_seed_id_is_top_level_error():
    library = _load()
    library["seeds"].append(dict(library["seeds"][0]))
    result = lib.validate_library(library)
    assert any(e.startswith("duplicate_seed_id:") for e in result["errors"])


def test_empty_library_blocks():
    result = lib.validate_library({"library_id": "x", "seeds": []})
    assert result["valid"] is False
    assert "missing_or_empty_seeds" in result["errors"]


def test_calendar_plan_is_deterministic():
    p1 = lib.build_calendar_plan_from_file(FIXTURE)
    p2 = lib.build_calendar_plan_from_file(FIXTURE)
    assert p1 == p2


def test_calendar_plan_preserves_order_and_counts():
    plan = lib.build_calendar_plan_from_file(FIXTURE)
    items = plan["planned_items"]
    assert [i["seed_id"] for i in items] == [
        "seed_macro_edu_001",
        "seed_build_in_public_001",
        "seed_data_sufficiency_001",
        "seed_blocked_signal_001",
    ]
    assert plan["safe_item_count"] == 3
    assert plan["blocked_item_count"] == 1


def test_blocked_seed_preserved_not_dropped():
    plan = lib.build_calendar_plan_from_file(FIXTURE)
    blocked = [i for i in plan["planned_items"] if i["review_status"] == "blocked"]
    assert len(blocked) == 1
    assert blocked[0]["seed_id"] == "seed_blocked_signal_001"
    assert blocked[0]["publish_status"] == "not_published"
    assert blocked[0]["blocked_reasons"]
    # Mirrored into blocked_items.
    assert any(b["seed_id"] == "seed_blocked_signal_001" for b in plan["blocked_items"])


def test_safe_items_are_manual_only_and_null_metrics():
    plan = lib.build_calendar_plan_from_file(FIXTURE)
    safe = [i for i in plan["planned_items"] if i["review_status"] == "needs_manual_review"]
    assert safe
    for i in safe:
        assert i["publish_status"] == "manual_only"
        assert i["manual_publish_url"] is None
        assert i["manual_publish_timestamp"] is None
        assert i["manual_metrics"] is None


def test_plan_level_flags_pinned_false():
    plan = lib.build_calendar_plan_from_file(FIXTURE)
    assert plan["local_only"] is True
    assert plan["manual_publish_only"] is True
    assert plan["platform_publish_allowed_now"] is False
    assert plan["live_execution_allowed_now"] is False
    assert plan["scheduler_allowed"] is False
    assert plan["metrics_ingestion_allowed"] is False


def test_summary_is_safe_and_reports_default_counts():
    s = lib.summary()
    assert s["local_only"] is True
    assert s["provider_call_made"] is False
    assert s["network_call_made"] is False
    assert s["credential_read"] is False
    assert s["public_postable_output"] is False
    assert s["scheduler_allowed"] is False
    assert s["metrics_ingestion_allowed"] is False
    assert s["default_safe_item_count"] == 3
    assert s["default_blocked_item_count"] == 1
