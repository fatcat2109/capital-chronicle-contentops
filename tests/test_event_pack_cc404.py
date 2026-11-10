from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

import pytest

from live_contentops import event_pack_v1 as packs
from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from tests.test_event_public_record_v1 import frozen_file, EVENT, RELEASE
from tests.test_publication_coordinator_v1 import _coordinator, _set_mode, FixtureTransport

PREVIEW = datetime(2026, 11, 6, 10, tzinfo=timezone.utc)
ARRIVAL = datetime(2026, 11, 6, 13, 32, tzinfo=timezone.utc)
REVIEW = datetime(2026, 11, 7, 12, tzinfo=timezone.utc)


def write(tmp_path, name, value, seal=False):
    if seal:
        value["content_hash"] = sha256_of(value)
    path = tmp_path / name
    path.write_bytes(canonical_bytes(value))
    return {"path": str(path), "sha256": sha256(path.read_bytes()).hexdigest()}


def packet(tmp_path):
    freeze, _ = frozen_file(tmp_path)
    doc = json.loads(Path(freeze["path"]).read_bytes())
    for row in doc["reaction_map"]:
        row["source_ref"] = "Main frozen plan; plan_sha256=" + "a" * 64
    freeze = write(tmp_path, "freeze-plan-bound.json", doc)
    official = tmp_path / "official.txt"
    official.write_text("BLS: the payroll change was 200,000.", encoding="utf-8")
    arrival = {"schema_version": "contentops.event_arrival.public.v1", "event_id": EVENT,
        "event_time_utc": RELEASE, "known_at_utc": "2026-11-06T13:31:00Z", "frozen_sha256": freeze["sha256"],
        "matched_branches": [0], "armed_plan_ids": ["plan-a"],
        "print": {"display": "200,000", "label": "payroll change", "publisher": "BLS",
            "source_url": "https://www.bls.gov/news.release/empsit.htm",
            "source": {"path": str(official), "sha256": sha256(official.read_bytes()).hexdigest()},
            "excerpt": "the payroll change was 200,000", "rights_class": "BLS_US_FEDERAL_PUBLIC_DOMAIN_TEXT"}}
    ledger = {"schema": "CapitalChronicleCallsLedgerPublicV1", "calls": [{"public_call_id": "call-a", "market": "Gold", "direction": "BULLISH", "source_plan_hash": "a"*64},
              {"public_call_id": "call-b", "market": "EUR/USD", "direction": "BEARISH", "source_plan_hash": "a"*64}],
        "registrations": [], "results": [], "state_changes": [], "generated_at_utc": "2026-11-06T09:59:00Z",
        "chain_tip": "a" * 64, "notice": packs.PUBLIC_NOTICE}
    status = {"plans": [{"plan_id": "plan-a", "asset_id": "Gold", "status": "TRIGGERED"}],
        "generated_at_utc": "2026-11-06T13:31:30Z", "scored_calls": [{"public_call_id": "call-a", "result": "STOPPED"}]}
    return {"title": "November employment", "event_id": EVENT, "planned_release_utc": RELEASE,
        "frozen_public_record": freeze, "event_arrival_record": write(tmp_path, "arrival.json", arrival),
        "calls_ledger_record": write(tmp_path, "ledger.json", ledger, True),
        "plan_status_record": write(tmp_path, "status.json", status, True), "public_call_ids": ["call-a", "call-b"]}


def test_three_code_rendered_stages_preserve_bound_map_print_and_every_score(tmp_path):
    inputs = packet(tmp_path)
    preview = packs.compose(inputs, "preview", now=PREVIEW)
    arrival = packs.compose(inputs, "arrival", now=ARRIVAL)
    review = packs.compose(inputs, "review", now=REVIEW)
    assert inputs["frozen_public_record"]["sha256"] in preview["body_markdown"]
    assert "40%" in preview["body_markdown"]
    assert preview["body_markdown"].startswith("We are bearish on gold if ")
    assert "200,000" in arrival["body_markdown"] and "Plans armed: Gold." in arrival["body_markdown"]
    assert "UTC" not in preview["body_markdown"] and "ET" in preview["body_markdown"]
    assert len(review["review_rows"]) == 2
    assert "STOPPED" in review["body_markdown"] and "Unresolved" in review["body_markdown"]
    assert "Total event calls: 2. Scored by Main: 1." in review["body_markdown"]
    assert "Chain tip: " + "a" * 64 in preview["body_markdown"]


def test_first_person_call_keeps_all_five_fields_and_rejects_an_unbound_direction(tmp_path):
    from live_contentops.event_article_guard_v1 import check_publication_copy, reader_conditional_call_text
    view = packs.compose(packet(tmp_path), "preview", now=PREVIEW)
    wording = reader_conditional_call_text(view["conditional_calls"][0])
    check_publication_copy({"body": wording+"\n"+packs.PUBLIC_NOTICE+"\n"+packs.CONFLICTS_NOTICE},
                           conditional_calls=view["conditional_calls"])
    with pytest.raises(ValueError, match="UNCONDITIONAL_CALL"):
        check_publication_copy({"body": view["body_markdown"]+" We are bullish regardless."},
                               conditional_calls=view["conditional_calls"], require_call_text=False)


@pytest.mark.parametrize("kind,change,reason", [
    ("arrival", lambda d:d.update(frozen_sha256="f" * 64), "EVENT_OR_CLOCK"),
    ("arrival", lambda d:d.update(matched_branches=[99]), "MATCHED_BRANCH"),
    ("arrival", lambda d:d["print"].update(display="999,999"), "PUBLIC_PRINT_BINDING"),
    ("arrival", lambda d:d.update(armed_plan_ids=["absent"]), "ARMED_PLAN_NOT_RECOGNISED"),
    ("arrival", lambda d:d["print"].update(rights_class="PRIVATE_ONLY"), "PUBLIC_PRINT_BINDING"),
])
def test_source_mismatches_and_unsupported_event_claims_fail_before_publication(tmp_path, kind, change, reason):
    inputs = packet(tmp_path)
    value = json.loads(Path(inputs["event_arrival_record"]["path"]).read_bytes())
    change(value)
    inputs["event_arrival_record"] = write(tmp_path, "changed-arrival.json", value)
    with pytest.raises(ValueError, match=reason):
        packs.compose(inputs, kind, now=ARRIVAL)


def test_no_matching_branch_is_reported_without_inventing_one(tmp_path):
    inputs = packet(tmp_path)
    value = json.loads(Path(inputs["event_arrival_record"]["path"]).read_bytes())
    value.update(matched_branches=[], armed_plan_ids=[])
    inputs["event_arrival_record"] = write(tmp_path, "no-match.json", value)
    view = packs.compose(inputs, "arrival", now=ARRIVAL)
    assert "No branch matched" in view["body_markdown"]
    assert "Plans armed: none" in view["body_markdown"]


def test_timing_preserves_pre_release_and_next_morning_semantics(tmp_path):
    inputs = packet(tmp_path)
    with pytest.raises(ValueError, match="DEADLINE_MISSED"):
        packs.compose(inputs, "preview", now=ARRIVAL)
    with pytest.raises(ValueError, match="NEXT_MORNING_NOT_DUE"):
        packs.compose(inputs, "review", now=ARRIVAL)
    with pytest.raises(ValueError, match="OLDER_THAN_15_MINUTES|SOURCE_INVALID_OR_STALE"):
        packs.compose(inputs, "arrival", now=REVIEW)


def test_real_coordinator_registers_exact_event_payload_and_refuses_preview_edits(tmp_path):
    store, runtime, coordinator = _coordinator(tmp_path)
    inputs = packet(tmp_path)
    value = packs.register_pack(store, inputs, "preview", root=tmp_path / "packs", now=PREVIEW)
    result = coordinator.register_plan(value["identity"], value["plan"])
    assert len(result["registered"]) == 1
    intent = json.loads(store.get_outbox_message(result["registered"][0]["message_id"])["payload"])
    assert intent["native_payload"] == value["native_payload"]
    assert packs.validate_intent(store, intent)["identity"] == value["identity"]
    with pytest.raises(ValueError, match="PUBLIC_PREVIEW_IMMUTABLE"):
        coordinator._reader_presentation_intent(store.get_outbox_message(result["registered"][0]["message_id"]), "unneeded")
    again = packs.register_pack(store, inputs, "preview", root=tmp_path / "packs", now=PREVIEW)
    assert again == value and not runtime.publish_calls
    with pytest.raises(ValueError, match="STAGE_IMMUTABLE"):
        packs.register_pack(store, {**inputs, "title": "Changed title"}, "preview", root=tmp_path / "packs", now=PREVIEW)


def test_live_public_ledger_is_consumed_with_its_exact_hash(tmp_path):
    inputs = packet(tmp_path)
    doc = packs.public_ledger(inputs["calls_ledger_record"])
    assert len(doc["calls"]) == 2
    raw = Path(inputs["calls_ledger_record"]["path"]).read_bytes()
    Path(inputs["calls_ledger_record"]["path"]).write_bytes(raw+b" ")
    with pytest.raises(ValueError, match="SOURCE_BYTES_CHANGED"):
        packs.compose(inputs, "preview", now=PREVIEW)


def test_coordinator_publishes_once_then_readbacks_and_all_registered_derivatives(tmp_path):
    store, runtime, coordinator = _coordinator(tmp_path)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    parent = packs.register_pack(store, packet(tmp_path), "preview", root=tmp_path / "packs", now=PREVIEW)
    outcome = coordinator.publish_plan(parent["identity"], parent["plan"])
    assert outcome["per_destination"]["substack"]["status"] == "DISPATCH_CONFIRMED", outcome
    status = packs.stage_status(store, parent)
    assert status["canonical_url"].startswith("https://capitalchronicle.substack.com/p/")
    coordinator.publish_plan(parent["identity"], parent["plan"])
    assert runtime.publish_calls == ["substack"]
    store.register_outbox_message(message_id="observed-native-image", work_item_id=parent["identity"],
        destination="internal:native-neo-tool", status="EDITORIAL_INTERNAL", payload=json.dumps({"result": {
            "public_object_url": status["canonical_url"], "observed_media_sha256": [parent["media_assets"][0]["sha256"]],
            "public_image_urls": ["https://substack-post-media.s3.amazonaws.com/public/images/controlled.png"]}}))
    derived = packs.register_derivatives(store, parent)
    assert len(derived["plan"]["destinations"]) == 7
    coordinator.allow_prior_confirmed_distribution = True
    outcome = coordinator.publish_plan(derived["identity"], derived["plan"])
    assert all(v["status"] == "DISPATCH_CONFIRMED" for v in outcome["per_destination"].values()), outcome
    assert len(runtime.publish_calls) == 8
    coordinator.publish_plan(derived["identity"], derived["plan"])
    assert len(runtime.publish_calls) == 8


def test_minute_entry_resumes_same_stage_and_fresh_native_feed_uses_it(tmp_path):
    from tests.test_pre_event_preview_v1 import prepare
    from tests.test_capital_chronicle_report_feed_v1 import feed
    from live_contentops.contentops_editorial_desk_v1 import record_pre_event_preparation
    f = feed(tmp_path)
    _, prepared, _ = prepare(f.tracker.store, tmp_path)
    prepared.update(packet(tmp_path), event_pack_enabled=True)
    record_pre_event_preparation(f.tracker.store, prepared)
    calls = []
    def resume(store, value, **kw):
        calls.append(value["identity"])
        return {"status": "CONTROLLED_COORDINATOR_RETURN"}
    first = packs.run_due_packs(f.tracker.store, now=PREVIEW, root=tmp_path / "packs", publish=True, resume=resume)
    again = packs.run_due_packs(f.tracker.store, now=PREVIEW, root=tmp_path / "packs", publish=True, resume=resume)
    assert first["events"][0]["identity"] == again["events"][0]["identity"]
    assert len(set(calls)) == 1
    f.pointer["preview_event_id"] = EVENT
    result = f.opportunity(output_dir=tmp_path / "unused", cutoff_utc=PREVIEW.isoformat(), run_id="same-event-slot",
        rolling_input={"headlines": []}, llm_invoke=lambda **kw: pytest.fail("Duplicate native writer invoked"))
    assert result["classification"] == "EXISTING_EVENT_PACK"


@pytest.mark.parametrize("mode", ["KILL_SWITCH", "AUTONOMOUS_DEFAULT"])
def test_existing_halt_and_uncertain_write_keep_their_common_protection(tmp_path, mode):
    runtime = FixtureTransport(raise_after_write=True, ambiguous=True)
    store, _, coordinator = _coordinator(tmp_path, runtime=runtime)
    _set_mode(store, mode)
    value = packs.register_pack(store, packet(tmp_path), "preview", root=tmp_path / "packs", now=PREVIEW)
    coordinator.publish_plan(value["identity"], value["plan"])
    coordinator.publish_plan(value["identity"], value["plan"])
    assert len(runtime.publish_calls) == (0 if mode == "KILL_SWITCH" else 1)
    assert packs.stage_status(store, value)["canonical_url"] is None


def test_review_uses_all_exact_plan_calls_and_retains_untriggered_rows(tmp_path):
    inputs = packet(tmp_path)
    inputs["public_call_ids"] = ["call-a"]  # Cannot narrow Main's exact plan join.
    ledger = json.loads(Path(inputs["calls_ledger_record"]["path"]).read_bytes())
    ledger.pop("content_hash")
    ledger["results"] = [{"public_call_id": "call-b", "state": "NOT_SCORED_UNTRIGGERED"}]
    inputs["calls_ledger_record"] = write(tmp_path, "untriggered-ledger.json", ledger, True)
    view = packs.compose(inputs, "review", now=REVIEW)
    assert len(view["review_rows"]) == 2
    assert "Not triggered; not scored" in view["body_markdown"]


def test_new_preview_uploads_the_exact_public_ledger_file(tmp_path):
    from live_contentops.event_public_record_v1 import attachments_for_article
    store, _, _ = _coordinator(tmp_path)
    value = packs.register_pack(store, packet(tmp_path), "preview", root=tmp_path / "packs", now=PREVIEW)
    article = json.loads((Path(value["plan"]["output_dir"])/"article_manifest_v1.json").read_bytes())
    assets = attachments_for_article(article, media_dir=tmp_path/"own-media", timestamp_root=tmp_path/"no-stamps")
    assert len(assets) == 2
    ledger = next(a for a in assets if a["filename"].startswith("calls-ledger-"))
    assert ledger["sha256"] == article["calls_ledger_record"]["sha256"]
    assert len(json.loads(Path(ledger["path"]).read_bytes())["calls"]) == 2


@pytest.mark.parametrize("stage,clock,expected", [("arrival", ARRIVAL, "200,000"), ("review", REVIEW, "1 of 2")])
def test_arrival_and_review_cards_use_their_own_bound_release_or_score(tmp_path, stage, clock, expected):
    store, _, _ = _coordinator(tmp_path)
    value = packs.register_pack(store, packet(tmp_path), stage, root=tmp_path/"packs", now=clock)
    card = value["media_assets"][0]
    assert expected in card["alt_text"]
    assert len(card["source_bindings"]) > 1


def test_arrival_attach_cli_supplies_the_existing_minute_consumer(tmp_path, monkeypatch, capsys):
    from datetime import timedelta
    from scripts import event_public_record as cli
    from tests.test_capital_chronicle_report_feed_v1 import feed
    from tests.test_pre_event_preview_v1 import prepare
    from live_contentops.contentops_editorial_desk_v1 import record_pre_event_preparation, STORY_PREPARATION
    f = feed(tmp_path)
    _, prepared, _ = prepare(f.tracker.store, tmp_path)
    inputs = packet(tmp_path)
    now = datetime.now(timezone.utc)
    released = (now-timedelta(minutes=2)).isoformat()
    frozen = json.loads(Path(inputs["frozen_public_record"]["path"]).read_bytes())
    frozen["event_time_utc"] = released
    inputs["frozen_public_record"] = write(tmp_path, "current-freeze.json", frozen)
    arrival = json.loads(Path(inputs["event_arrival_record"]["path"]).read_bytes())
    arrival.update(event_time_utc=released, known_at_utc=(now-timedelta(minutes=1)).isoformat(),
                   frozen_sha256=inputs["frozen_public_record"]["sha256"])
    arrival_spec = write(tmp_path, "current-arrival.json", arrival)
    status = json.loads(Path(inputs["plan_status_record"]["path"]).read_bytes())
    status.pop("content_hash")
    status["generated_at_utc"] = (now-timedelta(seconds=30)).isoformat()
    status_spec = write(tmp_path, "current-status.json", status, True)
    prepared.update(title=inputs["title"], frozen_public_record=inputs["frozen_public_record"],
        planned_release_utc=released, event_pack_enabled=True)
    record_pre_event_preparation(f.tracker.store, prepared)
    monkeypatch.setattr(packs, "PACK_ROOT", tmp_path/"runtime-packs")
    assert cli.main(["--store", str(f.tracker.store.db_path), "--attach-arrival", EVENT,
        "--arrival-file", arrival_spec["path"], "--arrival-sha256", arrival_spec["sha256"],
        "--plan-status-file", status_spec["path"]]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "EVENT_ARRIVAL_ATTACHED"
    latest = json.loads(f.tracker.store.list_outbox_messages(destination=STORY_PREPARATION)[-1]["payload"])
    assert latest["event_arrival_record"]["sha256"] == arrival_spec["sha256"]
    assert Path(latest["event_arrival_record"]["path"]).is_relative_to(tmp_path/"runtime-packs")
    result = packs.run_due_packs(f.tracker.store, now=now, root=tmp_path/"pack-output")
    assert result["events"][0]["stage"] == "arrival"


def test_existing_pythonw_run_record_keeps_event_identity_and_omits_native_payload(tmp_path):
    from live_contentops.plan_status_posts_v1 import record_run
    result = {"status": "OK", "event_timestamp": {"status": "CALENDAR_PENDING"},
        "event_packs": {"status": "EVENT_PACK_PASS", "events": [{"identity": "event-pack-controlled-preview",
            "stage": "preview", "status": {"per_destination": {"substack": {"status": "NOT_STARTED"}}},
            "publication": {"state": "NATIVE_NEO_TOOL_PENDING", "native_tool_request": {"body": "large retained native payload"}}}]}}
    path = record_run(result, tmp_path/"runs", now=PREVIEW)
    line = json.loads(path.read_text(encoding='utf-8').splitlines()[-1])
    assert line["event_timestamp"]["status"] == "CALENDAR_PENDING"
    event = line["event_packs"]["events"][0]
    assert event["identity"] == "event-pack-controlled-preview" and event["publication_state"] == "NATIVE_NEO_TOOL_PENDING"
    assert "large retained" not in path.read_text(encoding='utf-8')
