from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from scripts.verify_cpi_reaction_page_v1 import compare_cells, join_capture_periods, recompute_market, sample_releases
from test_cpi_reaction_page_cc425 import pack
from live_contentops.cpi_reaction_page_v1 import TOKEN, bind_tables, writer_guidance


def test_fixed_seed_keeps_newest_three_and_five_distinct_older_releases():
    events = [{"release_utc": f"2026-{month:02d}-10T12:30:00Z"} for month in range(1, 11)]
    sample = sample_releases(events)
    assert len(set(sample)) == 8
    assert sample[-3:] == [row["release_utc"] for row in events[-3:]]
    assert sample == sample_releases(list(reversed(events)))
    assert sample[:5] == [events[i]["release_utc"] for i in (0, 1, 2, 3, 5)]


def test_missing_release_or_duplicate_never_reduces_verification_sample():
    with pytest.raises(ValueError, match="EIGHT_DISTINCT"):
        sample_releases([{"release_utc": "2026-01-10T12:30:00Z"}] * 8)


def test_recomputed_return_uses_one_series_and_keeps_missing_endpoint():
    released = datetime(2026, 10, 14, 12, 30, tzinfo=timezone.utc)
    stamp = int(released.timestamp())
    endpoint = released + timedelta(minutes=5)
    cpi = SimpleNamespace(endpoints=lambda _: {"5m": endpoint, "30m": released + timedelta(minutes=30)},
        iso=lambda t: t.isoformat(), bar_ref=lambda row: {"id": row["id"]} if row else None)
    bars = {("XAUUSD", "SOURCE_A", "BID"): {stamp: {"close": 100, "id": "a"},
                                                stamp + 300: {"close": 90, "id": "b"}},
            ("XAUUSD", "SOURCE_B", "BID"): {stamp + 1800: {"close": 200, "id": "c"}}}
    actual = recompute_market("XAUUSD", bars, released, released + timedelta(days=1), cpi)
    assert actual["windows"]["5m"]["move_pct"] == -10
    assert actual["windows"]["30m"]["move_pct"] is None
    assert actual["windows"]["30m"]["missing_reason"] == "EXACT_ENDPOINT_ABSENT"
    changed = {**actual, "windows": {**actual["windows"],
        "5m": {**actual["windows"]["5m"], "move_pct": 10}}}
    result = {"checked_cells": 0, "mismatches": []}
    compare_cells(actual, changed, "/release/Gold", result)
    assert [m["cell"] for m in result["mismatches"]] == ["/release/Gold/windows/5m/move_pct"]
    assert "exported_sha256" in result["mismatches"][0]


def test_current_writer_consumer_replaces_superseded_review_and_november_wait():
    guidance = writer_guidance(pack())
    assert "fixed seed" in guidance and "publish through October" in guidance
    assert "Ops Product's table review precedes" not in guidance


def test_capture_recovery_joins_only_one_explicit_month_for_same_measure_and_date():
    rows = [{"source": "investing", "release_date": "2026-08-12", "measure_id": "headline",
             "reference_period": "2026-07"},
            {"source": "myfxbook", "release_date": "2026-08-12", "measure_id": "headline",
             "reference_period": None},
            {"source": "myfxbook", "release_date": "2026-08-12", "measure_id": "core",
             "reference_period": None}]
    recovered = join_capture_periods(rows)
    assert recovered[1]["reference_period"] == "2026-07"
    assert recovered[2]["reference_period"] is None


@pytest.mark.parametrize("cutoff", [None, "2026-11-10T09:31:46Z"])
def test_historical_page_uses_bound_observation_windows_without_inventing_fresh_cutoff(cutoff):
    from live_contentops.reader_article_contract_v1 import POLICY, validate_publication_clock
    article = bind_tables({"substack_body_markdown": TOKEN}, pack())
    article["reader_article_contract"] = {"policy": POLICY, "data_cutoff_utc": cutoff}
    now = datetime(2026, 11, 17, tzinfo=timezone.utc)
    validate_publication_clock(article, now=now, destination="substack")
    # The exception belongs to the exact CPI table page, not a normal stale story.
    article.pop("cpi_reaction_page")
    with pytest.raises(ValueError, match="ARTICLE_DATA_CUTOFF"):
        validate_publication_clock(article, now=now, destination="substack")


def test_historical_publication_still_refuses_changed_cells():
    from live_contentops.reader_article_contract_v1 import POLICY, validate_publication_clock
    article = bind_tables({"substack_body_markdown": TOKEN}, pack())
    article["reader_article_contract"] = {"policy": POLICY, "data_cutoff_utc": None}
    article["substack_body_markdown"] = article["substack_body_markdown"].replace("-0.2353%", "+0.2353%")
    with pytest.raises(ValueError, match="TABLE_CHANGED"):
        validate_publication_clock(article, now=datetime.now(timezone.utc), destination="substack")


def test_current_visual_reviewer_keeps_exact_binding_and_unresolved_issue_guard(monkeypatch):
    import json
    from live_contentops import native_desktop_editorial_v1 as native
    binding = {"assets": [], "renders": [{"render_id": "canonical", "sha256": "a" * 64}],
               "renderer_sha256": {"renderer": "b" * 64}}
    monkeypatch.setattr(native, "native_artifact_key", lambda *args: "exact-article")
    monkeypatch.setattr(native, "final_visual_binding", lambda *args, **kwargs: binding)
    turn = SimpleNamespace(run_id="CONTROLLED-run", store=SimpleNamespace(
        get_outbox_message=lambda key: {"payload": json.dumps({"article_identity": "CONTROLLED-article"})}),
        _get=lambda *args: {"invocation_observation": {"invocation_id": "CONTROLLED-original-writer"}})
    request = {"governed_input": {"binding": binding}}
    response = {"invocation_observation": {"surface": "CODEX_NATIVE_SUBAGENT",
        "invocation_id": "CONTROLLED-current-reviewer", "model": "gpt-6.1-sol", "reasoning_effort": "max"},
        "output": {"decision": "ACCEPT", "asset_findings": [], "render_findings": [{
            "render_id": "canonical", "sha256": "a" * 64, "pixels_inspected": True,
            "checks": dict.fromkeys(native.FINAL_VISUAL_LAYOUT_CHECKS, "PASS"), "findings": [],
            "evidence_notes": "Controlled exact-assembly contract test; no real visual judgment claimed."}]}}
    native.validate_final_visual_return(turn, request, response)
    response["output"]["render_findings"][0]["findings"] = ["Controlled unresolved clipping defect"]
    with pytest.raises(ValueError, match="UNRESOLVED_ISSUE"):
        native.validate_final_visual_return(turn, request, response)


def test_cpi_social_compiler_uses_writer_copy_instead_of_unconfirmed_news_template():
    from live_contentops.v1_simple_gemini_newsroom_v1 import _native_preview_bundle
    article = bind_tables({"title": "What CPI history says", "dek": "A dated reference with gaps.",
        "social_hook": "The first move can differ from the close.",
        "substack_body_markdown": "We compare separate horizons.\n\nSo what: Keep each sample separate.\n\n" + TOKEN}, pack())
    bundle, _ = _native_preview_bundle(article=article, article_mode="DATA_OR_DOCUMENT_LENS",
        article_identity="CONTROLLED-cpi", epistemic_state={"event_confirmation_state": "UNCONFIRMED"})
    for payload in bundle["packages"].values():
        text = payload.get("full_text") or payload.get("text") or ""
        assert "not been independently confirmed" not in text
        assert "conditional on verification" not in text
        assert "Independent confirmation or denial" not in text
    assert "A dated reference with gaps." in bundle["packages"]["linkedin"]["text"]
