from copy import deepcopy
from functools import partial
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_reader_copy_v1 as reader
from live_contentops import plan_reader_editorial_v1 as editorial
from live_contentops import plan_state_alerts_v1 as alerts
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.light_model_caller_v1 import call_light
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
from test_plan_analysis_pages_cc432 import source  # noqa: F401
from test_plan_analysis_distribution_cc435 import confirm
from test_plan_status_publication_cc306 import fake_host
from test_plan_call_cards_cc399 import controlled_tradingview  # noqa: F401
from test_plan_state_alerts_cc543 import event, main_root, replay, rows, write  # noqa: F401
from test_publication_coordinator_v1 import FixtureTransport, _set_mode


LAYERS = {
    "macro": {"text": "Real yields rose after the data release.", "evidence_ids": ["rates"]},
    "fundamentals": {"text": "Physical demand slowed in Asia.", "evidence_ids": ["demand"]},
    "positioning_sentiment": {"text": "Longs are crowded after a week of inflows.", "evidence_ids": ["cot"]},
    "options_gamma": {"text": "Gamma data is stale.", "status": "STALE"},
    "technical": {"text": "Price failed to recover last week's range.", "evidence_ids": ["price"]},
}
LINK = "https://capitalchronicle.substack.com/p/controlled-gold-analysis"


def test_only_frozen_quotes_pass_and_failed_gy_drafts_fall_back_per_line(tmp_path):
    alternative = "Price stayed below resistance."
    plan = {"analysis_layers": {**LAYERS, "technical": {"text": LAYERS["technical"]["text"] + " " + alternative}}}
    expected = {"macro", "fundamental", "positioning_sentiment", "technical"}
    assert set(reader.analysis_layer_options(plan)) == expected
    with pytest.raises(ValueError, match="CC688_LAYER_NOT_QUOTED_FROM_PLAN:macro"):
        reader.validate_analysis_line(reader.analysis_layer_options(plan), "macro", "Real yields fell after the data release.")

    def draft(_prompt, **kwargs):
        assert kwargs["callers"] == ("antigravity",)
        return json.dumps({"macro": "Real yields fell after the data release.",
                           "technical": "1", "fundamental": "2"}).encode(), {"status": "RETURNED"}

    quotes = editorial.prepare_plan_layers(plan, output_dir=tmp_path, call=draft)
    assert quotes["macro"] == LAYERS["macro"]["text"]
    assert quotes["fundamental"] == LAYERS["fundamentals"]["text"]
    assert quotes["technical"] == alternative
    assert set(quotes) == expected
    record = json.loads(next(tmp_path.glob("*/light-call.json")).read_bytes())
    assert (record["lines_passed"], record["lines_expected"], record["fallback"]) == (1, 4, "frozen_plan")
    assert reader.verified_analysis_lines(plan, quotes)[0] == "Macro: " + LAYERS["macro"]["text"]


def test_timeout_uses_the_frozen_quote_without_a_second_caller(tmp_path):
    seen = []

    def time_out(args, *, cwd, timeout, input):
        seen.append((args[0], timeout))
        raise subprocess.TimeoutExpired(args, timeout)

    plan = {"analysis_layers": LAYERS}
    quotes = editorial.prepare_plan_layers(plan, output_dir=tmp_path, call=partial(call_light, runner=time_out))
    assert len(quotes) == 4
    assert len(seen) == 1 and seen[0][1] == 65 and seen[0][0].endswith("agy.exe")
    record = json.loads(next(tmp_path.glob("*/light-call.json")).read_bytes())
    assert record["job"] == "plan_layer_lines"
    assert record["result"] == "FALLBACK" and record["cause"] == "AGY_PLAN_LAYER_TIMEOUT_65S"


def test_execution_copy_is_removed_from_layer_choices_before_it_can_starve_an_alert():
    technical = "Price failed to recover last week's range."
    plan = {"analysis_layers": {"technical": {"text": "The stop below the shelf was reviewed. " + technical}}}
    quotes = editorial.prepare_plan_layers(plan)
    assert quotes == {"technical": technical}
    assert reader.verified_analysis_lines(plan, quotes) == ["Technical: " + technical]


@pytest.mark.parametrize("confirmed", [True, False])
def test_minute_queue_and_all_status_payloads_use_the_same_frozen_lines(replay, main_root, monkeypatch, confirmed):
    store, folder, raw, now = replay
    # Match the public CC-687 export, including its layer names and state field.
    raw["analysis_layers"] = {name: {"state": "USED", "text": LAYERS[source]["text"], "first_cause": None}
                              for name, source in (("macro", "macro"), ("fundamental", "fundamentals"),
                                                   ("positioning_and_sentiment", "positioning_sentiment"),
                                                   ("technical", "technical"))}
    raw["analysis_layers"]["options_and_gamma"] = {
        "state": "USED" if confirmed else "UNAVAILABLE",
        "text": "Dealer gamma turns positive above the nearest strike." if confirmed else None,
        "first_cause": None if confirmed else "NOT_WRITTEN",
    }
    if not confirmed:
        raw["scenario_analysis"] = {"gamma": "Dealer gamma is positive above the nearest strike."}
    write(folder, [raw], [event(raw["plan_id"], "WAITING", raw["registered_at_utc"])],
          generated_at_utc=now.isoformat())
    monkeypatch.setattr(pages, "confirmed_publication", lambda *_: {
        "plan_id": raw["plan_id"], "registration_hash": raw["registration_hash"],
        "canonical_url": LINK, "summary": {"macro": "Real yields rose."},
    } if confirmed else None)
    result = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
    assert result["status"] == "OK"
    assert result["active_page_plan_ids"] == [raw["plan_id"]]
    row, = rows(store)
    assert row["analysis_copy_contract"] == reader.ANALYSIS_COPY
    alerts.validate(row, store=store)
    rendered = cards.destination_payloads(row, card_id="fixture-chart", chart_credit=True, complete_levels=True)
    assert set(rendered) == set(cards.DESTINATIONS)
    layer_lines = reader.verified_analysis_lines(raw, row["analysis_layer_quotes"])
    assert len(layer_lines) == (5 if confirmed else 4)
    for destination, copy in rendered.items():
        assert copy["text"].startswith(layer_lines[0]), destination
        assert all(copy["full_text"].count(line) == 1 for line in layer_lines), destination
        assert (LINK in copy["full_text"]) == confirmed, destination
        assert "Target level:" in copy["full_text"], destination
        assert copy["media_asset_ids"] == ["fixture-chart"]
    if confirmed:
        assert LINK in rendered["x"]["reply_texts"][0]
    assert all(posts._x_length(part["text"]) <= 280 for part in rendered["x"]["posts"])
    assert all(len(part) <= 500 for part in [rendered["threads"]["text"], *rendered["threads"]["reply_texts"]])
    row["analysis_layer_quotes"]["macro"] = "Real yields fell after the data release."
    with pytest.raises(ValueError, match="CC688_LAYER_NOT_QUOTED_FROM_PLAN"):
        alerts.validate(row, store=store)


def _selection(prompt):
    packet = json.JSONDecoder().raw_decode(prompt.split("\n", 1)[1])[0]
    return {key: [len(items) - 1] for key, items in packet.items()}


@pytest.mark.parametrize("terminal_writer", ["antigravity", "codex", "frozen_plan"])
def test_page_attempts_are_checked_and_minute_consumer_reads_the_draft(source, tmp_path, monkeypatch, terminal_writer):
    run_root, _, plan, _ = source
    now = posts._utc("2026-11-20T04:30:00Z")
    plan.update(analysis_layers=LAYERS, registered_at_utc="2026-11-20T04:28:00Z", status="WAITING",
                scenario_analysis={"base_case": {"probability_pct": 55}})
    store = ContentOpsDurableStore(tmp_path / "draft.sqlite3")
    export = {"status": {"plans": [plan]}}
    root = tmp_path / "pages"
    seen = []

    def draft(prompt, **options):
        caller, = options["callers"]
        seen.append(caller)
        if caller == "codex":
            assert options["codex_effort"] == "high" and options["timeout_seconds"] == 120
        else:
            assert options["timeout_seconds"] == editorial.PAGE_AGY_TIMEOUT
        if terminal_writer == "codex" and caller == "antigravity":
            return b'{"macro":[1024]}', {"status": "RETURNED"}
        if terminal_writer == "frozen_plan":
            return b"", {"status": "FAILED", "cause": "CLI_QUOTA"}
        return json.dumps(_selection(prompt)).encode(), {"status": "RETURNED", "answered_by": caller}

    def forbidden(*args, **kwargs):
        raise AssertionError("minute must not launch an authoring call")

    monkeypatch.setattr(editorial, "prepare_page", forbidden)
    pending = editorial.run_due(store, export, root=root, rollout={}, now=now, publish=False, cached_only=True)
    assert pending["draft_due"] and pending["pages"] == []
    result = editorial.draft_due_page(store, lambda: export, root=root, now=now, call=draft, run_root=run_root)
    assert result["status"] == "PAGE_DRAFT_READY" and result["writer"] == terminal_writer
    assert seen == (["antigravity"] if terminal_writer == "antigravity" else ["antigravity", "antigravity", "codex"])
    records = [json.loads(file.read_bytes()) for file in root.glob("*/*/*/*/light-call.json")]
    assert len(records) == len(seen)
    assert all(record["job"] == "plan_analysis_page" for record in records)
    packet_path, = root.glob("*/" + editorial.DRAFT_MANUSCRIPT)
    draft_bytes = packet_path.read_bytes()
    render = pages.render
    monkeypatch.setattr(pages, "render", partial(render, run_root=run_root))
    outcome = editorial.run_due(store, export, root=root, rollout={}, now=now, publish=False, cached_only=True)
    assert not outcome["draft_due"] and outcome["pages"][0]["publication"]["status"] == "PREPARED", outcome
    packet = editorial.publication_packet(store, plan)
    assert packet["authorship"]["writer"] == terminal_writer
    assert "Main scenario (55%)" in packet["native_payload"]["body_markdown"]
    assert "Alternative scenario" not in packet["native_payload"]["body_markdown"]
    assert packet_path.read_bytes() == draft_bytes
    manuscript = deepcopy(packet["manuscript"])
    manuscript["sections"]["macro"]["paragraphs"][0]["text"] = "Real yields fell after the data release."
    with pytest.raises(ValueError, match="CC688_PAGE_COPY_CHANGED_FROM_FROZEN_PLAN"):
        pages.validate_manuscript(plan, manuscript, pages.load_run(plan, run_root=run_root))


def test_minute_detaches_the_page_worker_and_active_lease_prevents_duplicate(tmp_path, monkeypatch):
    now = posts._utc("2026-11-20T04:30:00Z")
    store = ContentOpsDurableStore(tmp_path / "worker.sqlite3")
    monkeypatch.setattr(store, "_get_now", lambda: now)
    launched = []

    class Worker:
        pid = 99

    def popen(args, **options):
        launched.append((args, options))
        return Worker()

    monkeypatch.setattr(editorial.subprocess, "Popen", popen)
    launch = partial(editorial.start_page_draft_worker, store, python=sys.executable, export_dir=tmp_path / "export",
                     main_root=tmp_path / "fixture-main", root=tmp_path / "pages", now=now)
    assert launch(active_plan_ids=())["status"] == "NO_DUE_PAGE_DRAFT"
    drafted = tmp_path / "pages" / "plan-analysis-drafted" / editorial.DRAFT_MANUSCRIPT
    drafted.parent.mkdir(parents=True)
    drafted.touch()
    assert launch(active_plan_ids=("drafted",))["status"] == "NO_DUE_PAGE_DRAFT"
    assert launch(active_plan_ids=("new",))["pid"] == 99
    args, options = launched[0]
    assert args[2] == "draft-due" and Path(args[1]).name == "plan_analysis_pages.py"
    assert options["stdout"] == subprocess.DEVNULL
    store.acquire_lease(editorial.PAGE_DRAFT_LEASE, "other-worker", ttl_seconds=360)
    assert launch()["status"] == "ACTIVE_PAGE_DRAFT" and len(launched) == 1


def test_page_worker_shortlist_uses_current_plan_rows(source):
    _, _, plan, _ = source
    now = posts._utc("2026-11-20T04:30:00Z")
    active = {**plan, "status": "FILLED", "registered_at_utc": "2026-11-20T04:28:00Z"}
    ended = {**active, "plan_id": "ended", "status": "EXPIRED"}
    outside = {**active, "plan_id": "earlier", "registered_at_utc": "2026-11-12T00:00:00Z"}
    missing_analysis = {**active, "plan_id": "missing", "analysis_result_hash": None}
    export = {"status": {"plans": [active, ended, outside, missing_analysis]}}
    assert editorial.active_page_plan_ids(export, now) == [active["plan_id"]]


def test_page_consumer_reads_the_sealed_mid_horizon_archive(source, tmp_path):
    _, folder, plan, _ = source
    daily = tmp_path / pages.RUN_ROOT.name
    mid = daily.with_name("horizon-research-mid-279805139")
    (mid / "requests").mkdir(parents=True)
    folder.rename(mid / "requests" / plan["run_id"])
    plan["analysis_layers"] = LAYERS
    run = pages.load_run(plan, run_root=daily)
    manuscript = editorial.draft_plan_page(plan, run, output_dir=tmp_path / "draft",
        call=lambda prompt, **_: (json.dumps(_selection(prompt)).encode(), {"status": "RETURNED"}))
    packet = pages.render(plan, manuscript, run_root=daily, output_dir=tmp_path / "page")
    assert Path(packet["run_root"]) == mid
    store = ContentOpsDurableStore(tmp_path / "mid.sqlite3")
    registered = pages.register_page(store, packet)
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None)
    coordinator.register_plan(registered["page_id"], registered["plan"])
    intent, = store.list_outbox_messages(destination="substack")
    checked = pages.validate_intent(store, json.loads(intent["payload"]))
    assert checked["native_payload"] == packet["native_payload"]
    with pytest.raises(ValueError, match="PLAN_ANALYSIS_RESULT_HASH_MISMATCH"):
        pages.load_run({**plan, "analysis_result_hash": "0" * 64}, run_root=daily)


def test_reconciled_page_supplies_one_exact_reply_per_issued_status_and_route(source, tmp_path):
    run_root, _, plan, manuscript = source
    store = ContentOpsDurableStore(tmp_path / "links.sqlite3")
    packet = pages.register_page(store, pages.render(plan, manuscript, run_root=run_root, output_dir=tmp_path / "page"))
    roots = {"setup": "setup-status", "update": "fill-status", "result": "target-status"}
    snapshots = {}
    reply_routes = set(cards.DESTINATIONS) - {"linkedin"}
    for kind, key in roots.items():
        row = {"key": key, "plan_id": plan["plan_id"], "source_plan_registration": plan["registration_hash"],
               "kind": kind, "symbol": "EURUSD", "schema_version": posts.SCHEMA,
               "analysis_copy_contract": reader.ANALYSIS_COPY}
        store.create_work_item(story_id=key, work_item_id=key, title=kind, target_surface="MULTI_PLATFORM")
        store.register_outbox_message(message_id=key, work_item_id=key, destination=posts.DESTINATION,
                                      payload=json.dumps(row), status="PUBLISHED")
        snapshots[key] = store.get_outbox_message(key)["payload"]
        for destination in reply_routes:
            confirm(store, key, sha256(("plan-status-post:" + key).encode()).hexdigest(), destination,
                    key + "-" + destination, "https://example.test/" + destination + "/" + key)
    assert pages.register_link(store, packet, original_key=roots["setup"], destination="x")["state"] == (
        "PLAN_ANALYSIS_CANONICAL_NOT_CONFIRMED")
    confirm(store, packet["page_id"], packet["plan"]["plan_hash"], "substack", "confirmed-page", LINK)

    first = pages.distribute_links(store, publish=False)["links"]
    assert len(first) == 3 * len(reply_routes), first
    assert len({value["link_id"] for value in first}) == len(first)
    assert set(value["destination"] for value in first) == reply_routes
    for item in first:
        value = json.loads(store.get_outbox_message(item["link_id"])["payload"])
        native = value["native_payload"]
        assert native["reply_to_id"] == value["original_key"] + "-" + value["destination"]
        assert LINK in native["text"]
        assert not native.get("reply_texts")
        assert pages.validate_link_plan(store, value["link_id"], value["plan"]) == value
    assert pages.distribute_links(store, publish=False)["links"] == first
    assert all(store.get_outbox_message(key)["payload"] == payload for key, payload in snapshots.items())

    result_link = next(item for item in first if item["destination"] == "discord" and
                       json.loads(store.get_outbox_message(item["link_id"])["payload"])["original_key"] == roots["result"])
    plan = json.loads(store.get_outbox_message(result_link["link_id"])["payload"])["plan"]
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    transport = FixtureTransport()
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=transport,
        readiness_provider=lambda _: {"readiness_state": "READY_AUTHENTICATED"})
    coordinator.register_plan(result_link["link_id"], plan)
    outcome = pages.resume_discord_links(store, latest_states={packet["plan_id"]: "RESULT"},
        now=posts._utc(store.get_outbox_message(result_link["link_id"])["created_at"]),
        coordinator_for=lambda *_: coordinator)
    assert outcome[0]["status"] == "DISPATCH_CONFIRMED", outcome
    assert transport.publish_calls == ["discord"]


def test_linkedin_uses_the_late_confirmed_link_with_existing_chart_and_frozen_siblings(
    replay, main_root, monkeypatch, tmp_path, controlled_tradingview,
):
    store, folder, raw, now = replay
    monkeypatch.setattr(cards, "LINKEDIN_PLAN_LINK_EFFECTIVE", now)
    raw["analysis_layers"] = LAYERS
    write(folder, [raw], [event(raw["plan_id"], "WAITING", raw["registered_at_utc"])],
          generated_at_utc=now.isoformat())
    observed = {}
    monkeypatch.setattr(pages, "confirmed_publication", lambda *_: observed or None)
    queued = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
    assert queued["status"] == "OK"
    row, = rows(store)
    assert "linkedin" not in cards._ready_destinations(store, row)
    root = tmp_path / "posts"
    prepared = cards.prepare_post(store, row["key"], root=root, host=fake_host, destinations=("telegram", "linkedin"))
    assert [value["destination"] for value in prepared["destinations"]] == ["telegram"]
    assert prepared["deferred_destinations"][0]["cause"] == "CC684_LINKEDIN_PLAN_PAGE_NOT_CONFIRMED"
    before = posts._expected(store, row["key"], prepared["output_dir"])[1]["telegram"]
    store.create_work_item(story_id=row["key"], work_item_id=row["key"],
                           title=row["lead"], target_surface="MULTI_PLATFORM")
    confirm(store, row["key"], prepared["plan_hash"], "telegram", "post-1", "https://t.me/CapitalChronicle/1")
    observed["canonical_url"] = LINK
    assert "linkedin" in cards._ready_destinations(store, row)
    prepared = cards.prepare_post(store, row["key"], root=root, host=fake_host, destinations=("linkedin",))
    payloads = posts._expected(store, row["key"], prepared["output_dir"])[1]
    assert payloads["telegram"] == before
    assert LINK in payloads["linkedin"]["text"]
    assert payloads["linkedin"]["media_asset_ids"] == before["media_asset_ids"]
