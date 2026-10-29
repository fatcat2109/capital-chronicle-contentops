"""Dated text-brief routing controls; fixtures are not final MAX/publication proof."""
from copy import deepcopy

import pytest

from live_contentops.native_desktop_editorial_v1 import validate_release_media, final_visual_binding
from live_contentops.native_newsroom_volume_v1 import volume_policy, PHOTOLESS_INSTAGRAM_SKIP, permitted_photo_less_skip
from live_contentops.v1_simple_gemini_newsroom_v1 import _native_preview_bundle
from test_reader_first_data_journalism_v1 import decision
from test_publication_coordinator_v1 import _coordinator, _quality_plan, _set_mode


def article():
    visual = decision("NEWS", 0)
    visual["exception_reason"] = "This narrow attributed policy announcement has no useful admitted quantitative comparison."
    return {"title": "A dated policy announcement", "dek": "The admitted announcement leaves implementation details open.",
        "substack_body_markdown": "## What was announced\n\nThe policy announcement leaves implementation details open.",
        "social_hook": "Implementation details determine what changes.",
        "social_mechanism_summary": "The announcement sets a direction; implementation details remain open.",
        "social_policy_summary": "The timetable and mechanism still need an exact announced instrument.",
        "social_cross_asset_summary": "No causal market reaction is established by the announcement alone.",
        "reader_first_version": "DATA_JOURNALISM_V1", "visual_editorial_decision": visual,
        "resolved_article_mode": "BREAKING_BRIEF", "volume_policy": volume_policy("2026-10-30T10:00:00Z"),
        "volume_policy_cutoff_utc": "2026-10-30T10:00:00Z", "public_source_bindings": []}


def test_photoless_news_can_compile_eight_results_with_instagram_skipped():
    item = article()
    assert validate_release_media({"article": item, "media_assets": []})["photo_count"] == 0
    bundle, _ = _native_preview_bundle(article=item, article_mode="BREAKING_BRIEF",
        article_identity="c" * 64, media_assets=[], media_asset_ids=[])
    assert len(bundle["packages"]) == 8
    assert bundle["packages"]["instagram_business"]["delivery_state"] == PHOTOLESS_INSTAGRAM_SKIP
    for name, payload in bundle["packages"].items():
        if name != "instagram_business":
            assert payload.get("delivery_state") != PHOTOLESS_INSTAGRAM_SKIP


def test_unbound_old_and_analysis_articles_keep_the_photo_rule():
    item = article()
    unbound = {k:v for k,v in item.items() if k not in {"volume_policy", "volume_policy_cutoff_utc"}}
    with pytest.raises(ValueError, match="CONTEXTUAL_PHOTO"):
        validate_release_media({"article": unbound, "media_assets": []})
    analytical = deepcopy(item)
    analytical["resolved_article_mode"] = "STANDARD_NEWS_ANALYSIS"
    with pytest.raises(ValueError, match="CONTEXTUAL_PHOTO"):
        validate_release_media({"article": analytical, "media_assets": []})


def test_coordinator_never_registers_or_dispatches_skipped_instagram(tmp_path):
    store, transport, owner = _coordinator(tmp_path)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    plan = _quality_plan()
    plan.update(volume_policy=article()["volume_policy"], volume_policy_cutoff_utc="2026-10-30T10:00:00Z",
        photo_less_news_policy=True, resolved_article_mode="BREAKING_BRIEF",
        skipped_derivative_destinations=[{"destination":"instagram_business", "status":PHOTOLESS_INSTAGRAM_SKIP,
            "disposition":PHOTOLESS_INSTAGRAM_SKIP}])
    assert permitted_photo_less_skip(plan)
    result = owner.execute_plan("work-1", plan)
    assert result["canonical_article_real_published"] is True
    assert "instagram_business" not in transport.publish_calls
    assert len(transport.publish_calls) == 8
    assert all(row["destination"] != "instagram_business" for row in store.list_outbox_messages())
    assert not result["per_destination"]["instagram_business"]["publish_called"]
    assert result["per_destination"]["instagram_business"]["reconciliation_status"] is None


def test_text_brief_still_requires_all_desktop_mobile_rendered_targets():
    bundle, _ = _native_preview_bundle(article=article(), article_mode="BREAKING_BRIEF",
        article_identity="c" * 64, media_assets=[], media_asset_ids=[])
    result = {"article": article(), "article_identity": "c"*64, "media_assets": [],
        "previews": [{"destination":k,"payload":v} for k,v in bundle["packages"].items()],
        "simple_result":{"publication_lifecycle_plan":{"plan_hash":"controlled"}}}
    targets = final_visual_binding(result, renders=None)
    assert len(targets["variants"]) == 9 and targets["required_viewports"] == ["desktop", "mobile"]
    with pytest.raises(ValueError, match="COVERAGE"):
        final_visual_binding(result, renders=[])
