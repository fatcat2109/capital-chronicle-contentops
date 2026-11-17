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


def test_exact_cpi_history_reference_reaches_scenario_checks_without_invented_forecast():
    from live_contentops.article_scenarios_v1 import validate_article_scenarios, validate_social_scenarios
    from live_contentops.cpi_reaction_page_v1 import TITLE
    documents = pack()
    article = bind_tables({"title": TITLE, "substack_body_markdown": TOKEN}, documents)
    validate_article_scenarios(article, documents)
    validate_social_scenarios(article, {"text": "Our historical CPI comparisons retain their observation gaps."})
    changed = {**article, "substack_body_markdown": article["substack_body_markdown"].replace("-0.2353%", "+0.2353%")}
    with pytest.raises(ValueError, match="TABLE_CHANGED"):
        validate_article_scenarios(changed, documents)
    with pytest.raises(ValueError, match="SCENARIOS_REQUIRED"):
        validate_article_scenarios({**article, "title": "Today's gold forecast"}, documents)
    with pytest.raises(ValueError, match="SCENARIOS_REQUIRED"):
        validate_article_scenarios({**article, "cpi_reaction_page": {}}, documents)
    with pytest.raises(ValueError, match="SOURCE_CHANGED"):
        validate_article_scenarios({**article, "cpi_reaction_page": {**article["cpi_reaction_page"], "export_bytes_sha256": "wrong"}}, documents)


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


@pytest.mark.parametrize("fault", [None, "unconfirmed", "wrong_target", "changed_original"])
def test_existing_reader_revision_appends_only_the_confirmed_cpi_reference(monkeypatch, fault):
    import json
    from live_contentops import native_desktop_editorial_v1 as native
    from live_contentops.cpi_reaction_page_v1 import LINK_POLICY
    target_article = bind_tables({"substack_body_markdown": TOKEN}, pack())
    if fault == "wrong_target":
        target_article["cpi_reaction_page"]["record_id"] = "report:another-page"
    original = {"dispatch_id": "original", "message_id": "original-message", "platform": "substack",
                "public_object_id": "100", "public_object_url": "https://capitalchronicle.substack.com/p/cpi-preview",
                "status": "DISPATCH_CONFIRMED"}
    target = {"dispatch_id": "reference", "message_id": "reference-message", "platform": "substack",
              "public_object_id": "101", "public_object_url": "https://capitalchronicle.substack.com/p/cpi-history",
              "status": "UNKNOWN_WRITE" if fault == "unconfirmed" else "DISPATCH_CONFIRMED"}
    result = {"article_identity": "original-article", "qualified_article_count": 1,
              "article": {"title": "Our CPI review", "substack_body_markdown": "Original CPI review, unchanged."},
              "evidence": [], "previews": [{"destination": d, "payload": {"text": "Original CPI copy."}}
                    for d in sorted(native.FINAL_VISUAL_CHANNELS - {"substack"})], "media_assets": [],
              "simple_result": {"publication_lifecycle_plan": {"plan_hash": "CONTROLLED-plan"}}}
    messages = {"final": {"payload": json.dumps(result)},
                "reference-message": {"payload": json.dumps({"article": target_article})}}
    store = SimpleNamespace(get_platform_dispatch=lambda key: {"original": original, "reference": target}.get(key),
                            get_outbox_message=lambda key: messages.get(key))
    monkeypatch.setattr(native, "native_artifact_key", lambda *args: "final")
    after = result["article"]["substack_body_markdown"] + "\n\n## Historical CPI comparisons\n\n[Compare the market reactions in our CPI history tables](" + target["public_object_url"] + ")."
    proposal = {"policy": LINK_POLICY, "run_id": "cc338-cpi-preview", "reference_dispatch_id": "reference",
                "reference_url": target["public_object_url"], "objects": {"substack": original},
                "body_after": after + (" Changed claim." if fault == "changed_original" else "")}
    if fault:
        with pytest.raises(ValueError, match="CPI_REFERENCE_LINK"):
            native.build_reader_presentation_revision(store, run_id=proposal["run_id"], proposal=proposal,
                                                      owner_authority_ref="human:BACKLOG_CC425")
    else:
        revision = native.build_reader_presentation_revision(store, run_id=proposal["run_id"], proposal=proposal,
                                                              owner_authority_ref="human:BACKLOG_CC425")
        view = native.reader_presentation_revision_view(store, run_id=proposal["run_id"], result=result, revision=revision)
        assert view["article"]["substack_body_markdown"] == after
        assert view["article"]["title"] == result["article"]["title"]
        assert view["evidence"] == result["evidence"]
        assert result["article"]["substack_body_markdown"] == "Original CPI review, unchanged."
        class ReviewTurn:
            run_id = proposal["run_id"]
            def _get(self, *args):
                return {"invocation_observation": {"invocation_id": "CONTROLLED-original"}}
            def __call__(self, **kwargs):
                return {"governed_input": kwargs["governed_input"]}
        turn = ReviewTurn()
        turn.store = store
        request = native.request_final_visual_review(turn, renders=None, reader_presentation_revision=revision)
        assert request["governed_input"]["binding"]["renders"] == []
        response = {"invocation_observation": {"invocation_id": "CONTROLLED-current", "model": "gpt-6.1-sol", "reasoning_effort": "max"},
                    "output": {"decision": "ACCEPT", "rationale": "Controlled exact confirmed reference link; original source, body and media retained."}}
        native.validate_final_visual_return(turn, request, response)
        request["governed_input"]["reader_presentation_revision"]["body_after"] += " New unapproved claim."
        with pytest.raises(ValueError, match="APPEND_ONLY"):
            native.validate_final_visual_return(turn, request, response)


def test_promotion_checks_exact_store_binding_without_repeated_full_storage_scan(tmp_path, monkeypatch):
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore, DurableStateCorruptionError
    from live_contentops.native_publication_promotion_v1 import ReadOnlyStore, _snapshot, _target_guards
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    source = ContentOpsDurableStore(tmp_path / "source.sqlite3")
    work = "cc-opportunity-" + sha256_of("CONTROLLED-cpi")
    source.create_work_item(story_id=work, work_item_id=work, title="Controlled CPI", target_surface="TEST")
    statements = []
    original = ContentOpsDurableStore.get_read_only_connection
    def traced(store):
        conn = original(store)
        conn.set_trace_callback(statements.append)
        return conn
    monkeypatch.setattr(ContentOpsDurableStore, "get_read_only_connection", traced)
    reader = ReadOnlyStore(source.db_path)
    rows, reviews, item = _snapshot(reader, "CONTROLLED-cpi")
    assert item["work_item_id"] == work and rows == [] and reviews == []
    operation = {"item": {"work_item_id": "CONTROLLED-next"}, "pin": {"article_identity": "CONTROLLED-next"},
                 "rows": [], "reviews": []}
    source.register_outbox_message(message_id="CONTROLLED-settled-note", work_item_id=work,
        destination="substack_notes", payload='{"plan_status_post":"CONTROLLED-prior"}', status="PLAN_POST_SETTLED")
    with source.get_connection() as conn:
        conn.execute("INSERT INTO platform_dispatches (dispatch_id,message_id,platform,status,dispatched_at) VALUES (?,?,?,?,?)",
                     ("CONTROLLED-settled-dispatch", "CONTROLLED-settled-note", "substack_notes", "UNKNOWN_WRITE", "2026-11-17T00:00:00Z"))
    with reader.get_read_only_connection() as conn:
        assert _target_guards(conn, operation, {"run_id": "CONTROLLED-next"}, {"message_id": "CONTROLLED-new"}) is False
        assert conn.execute("SELECT status FROM platform_dispatches WHERE dispatch_id='CONTROLLED-settled-dispatch'").fetchone()[0] == "UNKNOWN_WRITE"
    assert not any("integrity_check" in q.lower() or "foreign_key_check" in q.lower() for q in statements)
    other = source.create_work_item(story_id="CONTROLLED-other", work_item_id="CONTROLLED-other",
                                    title="Controlled existing article", target_surface="TEST")
    source.register_outbox_message(message_id="CONTROLLED-existing-article", work_item_id="CONTROLLED-other",
        destination="internal:cc-report-simple-result", payload='{"article_identity":"CONTROLLED-next"}', status="EDITORIAL_INTERNAL")
    with reader.get_read_only_connection() as conn:
        with pytest.raises(ValueError, match="ARTICLE_IDENTITY_ALREADY_REGISTERED"):
            _target_guards(conn, operation, {"run_id": "CONTROLLED-next"}, {"message_id": "CONTROLLED-new"})
    # Schema and authorization-trigger tampering still fails the import reader.
    with source.get_connection() as conn:
        conn.execute("DROP TRIGGER trg_transition_events_append_authorized")
    with pytest.raises(DurableStateCorruptionError, match="Runtime insert guard"):
        ReadOnlyStore(source.db_path)


def test_recovery_uses_indexed_publication_rows_and_retains_unknown_obligation(tmp_path, monkeypatch):
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    store = ContentOpsDurableStore(tmp_path / "recovery.sqlite3")
    store.create_work_item(story_id="CONTROLLED-cpi", work_item_id="CONTROLLED-cpi", title="Controlled", target_surface="TEST")
    store.register_outbox_message(message_id="CONTROLLED-public", work_item_id="CONTROLLED-cpi",
        destination="substack", payload='{"work_item_id":"CONTROLLED-cpi","plan_hash":"CONTROLLED-plan"}', status="UNKNOWN_WRITE")
    store.register_outbox_message(message_id="CONTROLLED-tool", work_item_id="CONTROLLED-cpi",
        destination="internal:native-neo-tool", payload='{"transcript":"not a dispatch"}', status="EDITORIAL_INTERNAL")
    store.register_outbox_message(message_id="CONTROLLED-note", work_item_id="CONTROLLED-cpi",
        destination="substack_notes", payload='{"work_item_id":"CONTROLLED-cpi","plan_hash":"CONTROLLED-note-plan"}', status="UNKNOWN_WRITE")
    original = store.list_outbox_messages
    def indexed(**kwargs):
        assert kwargs.get("destination"), "Recovery must query the destination index first"
        return original(**kwargs)
    monkeypatch.setattr(store, "list_outbox_messages", indexed)
    co = DurablePublicationCoordinator(store=store, transport_runtime=None)
    rows = co._recovery_messages()
    assert {r["message_id"] for r in rows} == {"CONTROLLED-public", "CONTROLLED-note"}
    assert all(r["status"] == "UNKNOWN_WRITE" for r in rows)
