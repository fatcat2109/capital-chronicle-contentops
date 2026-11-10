"""Disposable native packets/transports; never live publication or model proof."""
from copy import deepcopy
import json

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.contentops_editorial_desk_v1 import record_native_article_review
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.destination_transport_registry_v1 import barred_browser_destinations
from live_contentops.native_desktop_editorial_v1 import DesktopInputRequired, require_current_final_visual_review
from live_contentops.native_desktop_publication_v1 import prepare_native_publication
from live_contentops.native_text_first_v1 import (
    POLICY_ID, DESTINATIONS, SKIPPED_IMAGE, SKIPPED_CHANNEL, text_first_brief,
    bind_validated_article, permitted_skips,
)
from live_contentops.v1_simple_gemini_newsroom_v1 import run_v1_simple_gemini_newsroom
from test_native_volume_window_v1 import CUTOFF, make_turn
from test_v1_simple_gemini_newsroom_v1 import _headlines, _selection, _article_output, _evidence_result
from test_native_desktop_publication_v1 import composed, finish


def brief_packet(tmp_path, monkeypatch, *, bad_fact=False, source_missing=False,
        rolling_override=None, evidence_override=None, writer_output=None, cutoff=CUTOFF):
    store = ContentOpsDurableStore(tmp_path / "CONTROLLED_NOT_PRODUCTION.sqlite3")
    run, window, auto = "controlled-text-first", "controlled-recorded-window", "v1-newsroom-new-york-2100"
    from live_contentops.v1_simple_gemini_scheduler_v1 import simple_gemini_slot_id
    day = cutoff[:10]
    run = simple_gemini_slot_id(production_day_id=day, window_id=window, slot_ordinal=1)
    root = tmp_path / "editorial" / day / window / run
    root.parent.mkdir(parents=True)
    turn, binding = make_turn(store, root, run, window_id=window, automation_id=auto, slot_ordinal=1,
        schema_version="contentops.native_desktop_operation_binding.v1", owner_manual_validation=False,
        store_path=str(store.db_path), published_memory_store=str(store.db_path),
        published_memory_output_root=str(tmp_path / "published"), cutoff_utc=cutoff)
    rolling = _headlines(1)
    for row in rolling["headlines"]:
        row["source_timestamp_utc"] = "2026-10-30T09:00:00Z"
    if rolling_override is not None:
        rolling = deepcopy(rolling_override)
    calls = []
    cached_evidence = {}

    def loader(request):
        if request["cluster_id"] in cached_evidence:
            return deepcopy(cached_evidence[request["cluster_id"]])
        calls.append("source")
        value = deepcopy(evidence_override) if evidence_override is not None else _evidence_result(
            status="BLOCKED" if source_missing else "PASS", blocker="OPTIONAL_PAGE_READ_REFUSED")
        cached_evidence[request["cluster_id"]] = deepcopy(value)
        return value

    stages = []
    for _ in range(4):
        try:
            semantic = run_v1_simple_gemini_newsroom(output_dir=root, cutoff_utc=cutoff,
                run_id=run, rolling_input=rolling, llm_invoke=turn, evidence_loader=loader)
            break
        except DesktopInputRequired as pending:
            request = pending.request
            stage = request["stage"]
            stages.append(stage)
            if stage == "select":
                output = _selection(request["governed_input"]["candidates"][0]["candidate_id"])
                output["ordered_candidate_plan"][0].update(article_mode="BREAKING_BRIEF",
                    angle="Specific current report", primary_reader_question="What does this report establish?",
                    evidence_plan="Use the exact retained source and preserve the missing timetable.")
            else:
                assert stage in {"write", "revise"}, stage
                output = deepcopy(writer_output) if writer_output is not None else _article_output(bad_excerpt=bad_fact)
                output["article"]["news_item_kind"] = "NEWS"
                from live_contentops.event_article_guard_v1 import PUBLIC_NOTICE
                output["article"]["substack_body_markdown"] += (
                    "\n\n" + PUBLIC_NOTICE + " [[SOURCE:SOURCE_1]]")
            turn.submit(stage, {"request_sha256": request["request_sha256"], "output": output,
                "invocation_observation": {"surface": "CODEX_NATIVE_SUBAGENT", "model": "gpt-6.1-sol",
                    "reasoning_effort": "low" if stage == "select" else "max",
                    "invocation_id": "CONTROLLED-select" if stage == "select" else "CONTROLLED-writer",
                    "observation_source": "CONTROLLED_FIXTURE_NOT_NATIVE_MODEL_PROOF"}})
    else:
        pytest.fail("Controlled pipeline did not terminate")
    if not semantic.get("qualified_article_count"):
        return store, binding, None, semantic, stages, calls
    article = json.loads((root / "article_manifest_v1.json").read_bytes())
    evidence = json.loads((root / "simple_gemini_evidence_v1.json").read_bytes())["selected_source_pack"]
    previews = json.loads((root / "native_derivative_previews_v1.json").read_bytes())["packages"]
    result = {"article": article, "article_identity": semantic["article_identity"], "simple_result": semantic,
        "media_assets": [], "evidence": evidence, "qualified_article_count": 1,
        "model_execution_state": "NATIVE_DESKTOP_REQUEST_RETURN",
        "previews": [{"destination": d, "payload": p} for d, p in previews.items()]}
    rollout = {"schema_version": "contentops.native_desktop_rollout.v1", "store_path": str(store.db_path),
        "editorial_output_root": str(tmp_path / "editorial"), "public_write_authority": True}
    from live_contentops.daily_app_supervisor_v1 import NATIVE_DESKTOP_AUTOMATION_SESSION_BY_ID
    store.create_work_item(story_id=window, work_item_id=window, title="Controlled window", target_surface="TEST")
    for key, value, work, destination in (
        ("native-operation-binding-" + sha256_of(run), binding, turn.work, "internal:native-desktop-editorial"),
        ("cc-editorial-final-" + sha256_of(run), result, turn.work, "internal:cc-report-simple-result"),
        ("native-window-" + sha256_of(window), {"production_day_id": day, "capacity": 1,
            "rollout_sha256": sha256_of(rollout), "window": {"opportunity_id": window,
                "session": NATIVE_DESKTOP_AUTOMATION_SESSION_BY_ID[auto]}}, window, "internal:native-desktop-editorial"),
    ):
        store.register_outbox_message(message_id=key, work_item_id=work, destination=destination,
            payload=canonical_bytes(value).decode(), status="EDITORIAL_INTERNAL")
    (root / "native_operation_binding.json").write_bytes(canonical_bytes(binding))
    record_native_article_review(store, run_id=run, article_identity=result["article_identity"], decision="KEEP",
        rationale="Controlled fact-checked short newsroom packet; no rendered-pixel judgment asserted.")
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled", lambda: None)
    control = store.get_operating_control()
    store.update_operating_control(operating_mode="AUTONOMOUS_DEFAULT", expected_state_version=control["state_version"],
        control_source="CONTROLLED_TEST")
    return store, binding, rollout, result, stages, calls


@pytest.fixture
def substack_first(monkeypatch):
    # Retained Substack-first semantics; site-first continuation has separate tests.
    import live_contentops.v1_simple_gemini_newsroom_v1 as newsroom
    build = newsroom._build_simple_publication_lifecycle_plan
    def historical_plan(**kwargs):
        plan = build(**kwargs)
        plan.pop("distribution_policy", None)
        plan["substack_first_dependency"] = True
        plan["plan_hash"] = newsroom._hash({k: v for k, v in plan.items() if k != "plan_hash"})
        return plan
    monkeypatch.setattr(newsroom, "_build_simple_publication_lifecycle_plan", historical_plan)


def test_text_first_publishes_through_existing_native_owner_to_every_destination(tmp_path, monkeypatch, substack_first):
    store, binding, rollout, result, stages, calls = brief_packet(tmp_path, monkeypatch)
    assert stages == ["select", "write"] and calls == ["source"]
    assert text_first_brief(result) and result["media_assets"] == []
    assert result["article"]["text_first"]["optional_input_gaps"] == ["OPTIONAL_PAGE_READ_REFUSED"]
    assert require_current_final_visual_review(store, run_id=binding["run_id"])["pixels_inspected"] is False
    prepared = prepare_native_publication(store, binding)
    assert prepared["skipped_derivative_destinations"] == []
    operation, executor, transport = composed(store, binding, rollout, monkeypatch)
    value, writes = finish(operation, executor)
    barred = set(barred_browser_destinations())
    assert value["publication"]["state"] == ("DISTRIBUTION_INCOMPLETE" if barred else "RECONCILED")
    assert set(writes + transport.calls) == (DESTINATIONS | {"linkedin_company"}) - barred
    states = {d["destination"]: d for d in value["publication"]["destinations"]}
    assert all(states[d]["reconciliation_status"] == "RECONCILED_CONFIRMED" for d in DESTINATIONS - barred)
    assert all(states[d]["status"] == "DEFINITE_NO_WRITE" for d in barred)
    assert len(store.list_platform_dispatches()) == 10
    prior = len(store.list_platform_dispatches())
    assert operation.resume()["publication"]["state"] == value["publication"]["state"]
    assert len(store.list_platform_dispatches()) == prior


@pytest.mark.parametrize("source_missing,bad_fact", [(True, False), (False, True)])
def test_failed_fact_or_missing_required_source_still_holds(tmp_path, monkeypatch, source_missing, bad_fact):
    store, binding, _, result, stages, _ = brief_packet(tmp_path, monkeypatch, source_missing=source_missing, bad_fact=bad_fact)
    assert result["qualified_article_count"] == 0
    assert "media-plan" not in stages and store.list_platform_dispatches() == []
    with pytest.raises(ValueError, match="QUALIFIED_NATIVE_RESULT_REQUIRED"):
        prepare_native_publication(store, binding)


def test_text_first_kill_switch_and_just_in_time_fact_check_cannot_be_bypassed(tmp_path, monkeypatch):
    store, binding, rollout, _, _, _ = brief_packet(tmp_path, monkeypatch)
    prepare_native_publication(store, binding)
    operation, _, transport = composed(store, binding, rollout, monkeypatch)
    control = store.get_operating_control()
    store.update_operating_control(operating_mode="KILL_SWITCH", expected_state_version=control["state_version"],
        control_source="CONTROLLED_KILL_SWITCH")
    with pytest.raises(ValueError, match="PUBLICATION_OPERATING_MODE_BLOCKED"):
        operation.resume()
    assert transport.calls == [] and store.list_platform_dispatches() == []


@pytest.mark.parametrize("fault", ["source", "copy", "claim"])
def test_changed_fact_binding_blocks_even_with_a_forged_keep(tmp_path, monkeypatch, fault):
    store, binding, _, result, _, _ = brief_packet(tmp_path, monkeypatch)
    if fault == "source":
        result["evidence"][0]["canonical_content_text"] += " Changed after review."
    elif fault == "copy":
        result["article"]["substack_body_markdown"] += " Changed after review."
    else:
        from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn
        turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=binding["output_dir"])
        key = turn._key("write", "response")
        response = turn._get("write", "response")
        response["output"]["material_claim_bindings"][0]["support_excerpt"] = "Unsupported new fact."
        with store.get_connection() as conn:
            conn.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?", (canonical_bytes(response).decode(), key))
    key = "cc-editorial-final-" + sha256_of(binding["run_id"])
    with store.get_connection() as conn:
        conn.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?", (canonical_bytes(result).decode(), key))
    from live_contentops.contentops_editorial_desk_v1 import read_reviews
    prior = read_reviews(store)[-1]
    record_native_article_review(store, run_id=binding["run_id"], article_identity=result["article_identity"],
        decision="KEEP", expected_review_id=prior["review_id"], rationale="Controlled forged review must not bypass actual source and claim checks.")
    with pytest.raises(ValueError):
        require_current_final_visual_review(store, run_id=binding["run_id"])
    assert not store.list_platform_dispatches()


@pytest.mark.parametrize("fault", ["analysis", "long", "private", "trade", "missing_notice"])
def test_fast_track_never_relaxes_analysis_length_or_public_output(fault):
    from live_contentops.native_text_first_v1 import writer_policy
    article = {**_article_output()["article"], "news_item_kind": "NEWS"}
    if fault != "missing_notice":
        article["substack_body_markdown"] += "\n\nAnalysis, not financial advice. Readers decide whether to trade."
    governed = {"article_mode": "BREAKING_BRIEF", "source_pack": [{"CONTROLLED": True}]}
    if fault == "analysis":
        article["news_item_kind"] = "ANALYSIS"
    elif fault == "long":
        article["substack_body_markdown"] = "word " * 501
    elif fault == "private":
        article["private_context"] = "CONTROLLED"
    elif fault == "trade":
        article["substack_body_markdown"] += " Entry price 100, stop-loss 90, take-profit 120."
    request = {"request_sha256": "c" * 64, "governed_input": {**governed, "text_first_policy": writer_policy(governed)}}
    with pytest.raises(ValueError):
        bind_validated_article(article, request=request, source_pack=governed["source_pack"],
            validation={"status": "PASS", "unsupported_material_claim_count": 0})


def test_skip_policy_cannot_hide_an_extra_destination():
    from live_contentops.native_text_first_v1 import _legacy_skipped_destinations, skipped_destinations
    plan = {"text_first": {"policy_id": POLICY_ID, "article_mode": "BREAKING_BRIEF", "story_kind": "NEWS"},
        "resolved_article_mode": "BREAKING_BRIEF", "media_asset_count": 0,
        "skipped_derivative_destinations": _legacy_skipped_destinations()}
    assert skipped_destinations() == []
    assert permitted_skips(plan) == {"instagram_business", "facebook_page", "youtube"}
    wrong = deepcopy(plan)
    wrong["skipped_derivative_destinations"].append({"destination": "x", "status": SKIPPED_CHANNEL})
    assert permitted_skips(wrong) == set()


def test_text_first_unknown_write_reads_back_the_same_canonical_before_derivatives(tmp_path, monkeypatch, substack_first):
    store, binding, rollout, _, _, _ = brief_packet(tmp_path, monkeypatch)
    prepare_native_publication(store, binding)
    operation, executor, transport = composed(store, binding, rollout, monkeypatch)
    plan, _ = operation.validate()
    operation._authorize_and_bind()
    from live_contentops.v1_simple_publication_handoff_v1 import SimplePublicationHandoffV1
    SimplePublicationHandoffV1(store=store, coordinator=None)._ensure_work_item(slot_id=binding["run_id"], plan=plan)
    operation.coordinator.register_plan(binding["run_id"], plan)
    ids = operation.coordinator._ids(binding["run_id"], plan["plan_hash"], "substack")
    from test_native_desktop_publication_v1 import CANONICAL
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform="substack", status="UNKNOWN_WRITE", public_object_id="controlled-article", public_object_url=CANONICAL)
    value, writes = finish(operation, executor)
    barred = set(barred_browser_destinations())
    assert value["publication"]["state"] == ("DISTRIBUTION_INCOMPLETE" if barred else "RECONCILED")
    assert "substack" not in writes and set(writes + transport.calls) == ((DESTINATIONS - {"substack"}) | {"linkedin_company"}) - barred
    assert len(store.list_platform_dispatches()) == 10


@pytest.mark.parametrize("bad_value", [False, True])
def test_optional_chart_still_requires_its_exact_source_values(tmp_path, bad_value):
    from test_native_editorial_media_standard_v1 import controlled_release_packet
    from live_contentops.native_desktop_editorial_v1 import validate_release_media
    document, _, chart = controlled_release_packet(tmp_path)
    article = {"text_first": {"policy_id": POLICY_ID, "article_mode": "BREAKING_BRIEF", "story_kind": "NEWS"},
        "resolved_article_mode": "BREAKING_BRIEF"}
    if bad_value:
        chart["computed_values"][0][0] = 999999
        with pytest.raises(ValueError):
            validate_release_media({"article": article, "media_assets": [chart], "evidence": [document]})
    else:
        assert validate_release_media({"article": article, "media_assets": [chart], "evidence": [document]})["chart_count"] == 1


def test_already_issued_media_packet_never_gains_a_new_text_writer(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "CONTROLLED-legacy.sqlite3")
    turn, _ = make_turn(store, tmp_path / "legacy", "CONTROLLED-legacy")
    pending = turn.root / "editorial_media_plan_required.json"

    def invoke():
        return turn(logical_invocation_id=turn.run_id + ":write", prompt="Controlled old brief, no model call",
            governed_input={"article_mode": "BREAKING_BRIEF", "source_pack": [{"CONTROLLED": True}],
                "cutoff_utc": CUTOFF}, validator=lambda text: (True, None, json.loads(text), None))

    with monkeypatch.context() as legacy:
        legacy.setattr("live_contentops.native_text_first_v1.writer_policy", lambda _: None)
        with pytest.raises(DesktopInputRequired):
            invoke()
    old = pending.read_bytes()
    with pytest.raises(DesktopInputRequired) as required:
        invoke()
    assert required.value.request["stage"] == "media-plan"
    assert turn.frozen_request("write") is None
    assert pending.read_bytes() == old
