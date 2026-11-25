"""Replay confirmed Capital Chronicle posts without contacting their transports."""

from copy import deepcopy
from datetime import datetime, time
import json
from pathlib import Path
import re

import pytest

from live_contentops import call_followups_v1 as followups
from live_contentops import plan_call_cards_v1 as plan_cards
from live_contentops import plan_status_posts_v1 as plan_posts
from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _build_rolling_x_publication_plan
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.neo_destination_handoff_v1 import _payload_binding
from live_contentops.plan_analysis_pages_v1 import public_filter, structured_summary
from live_contentops.public_decision_checks_v1 import plan_scenario_flags, plan_target_present
from live_contentops.public_time_v1 import public_datetime, public_timestamp, require_public_time
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
from live_contentops.reader_article_contract_v1 import article_format
from live_contentops.tradingview_snapshot_v1 import validate_snapshot_asset


FIXTURES = Path(__file__).parent / "fixtures" / "cc691"
WRAP_MARKETS = {"XAUUSD", "US500", "EURUSD", "USDJPY", "USOIL", "BTCUSD"}
WRAP_DESTINATIONS = {
    "substack", "telegram", "discord", "facebook_page", "instagram_business",
    "linkedin", "linkedin_company", "x", "threads", "youtube",
}
PLAN_DESTINATIONS = {
    "telegram", "discord", "facebook_page", "instagram_business", "linkedin", "x", "threads", "substack_notes",
}
PLAN_LAYERS = {
    "Macro": "macro", "Priced in": "priced_in", "Positioning": "positioning",
    "Fear": "fear", "Story": "story", "Scenarios": "scenarios",
}


@pytest.fixture(scope="module")
def saved_posts():
    return json.loads((FIXTURES / "posts.json").read_text(encoding="utf-8"))


def _chart(post):
    asset = deepcopy(post["asset"])
    asset["path"] = FIXTURES / asset["path"]
    snapshot = asset["tradingview_snapshot"]
    snapshot["path"] = FIXTURES / snapshot["path"]
    return asset


def test_decision_82_the_attached_tradingview_chart_matches_the_post_market(saved_posts):
    gold, bitcoin = (saved_posts["charts"][market] for market in ("gold", "bitcoin"))
    validate_snapshot_asset(_chart(gold), {"market_asset": gold["market"]})
    bitcoin_chart = _chart(bitcoin)
    validate_snapshot_asset(bitcoin_chart, {"market_asset": bitcoin["market"]})

    with pytest.raises(ValueError, match="TRADINGVIEW_SNAPSHOT_BINDING_INVALID"):
        validate_snapshot_asset(bitcoin_chart, {"market_asset": gold["market"]})


def test_decision_90_the_update_uses_new_york_time(saved_posts):
    update = saved_posts["timed_plan_update"]
    require_public_time(update["text"])
    clock = public_timestamp(update["event_utc"]).split(" on ")[0]
    assert update["rendered_timestamp"].endswith(f" {clock}.")
    assert f"Updated {plan_cards._clock(update['event_utc'])}." == update["rendered_timestamp"]
    assert update["rendered_timestamp"] in update["text"]

    broken = update["text"].replace(clock, "12:36 GMT+7")
    with pytest.raises(ValueError, match="PUBLIC_TIMEZONE_ET_REQUIRED"):
        require_public_time(broken)


@pytest.mark.parametrize("line", [
    "**Target level**: $3,985.10", "Model target level unavailable.",
    "The target is near 3,985.", "TP1: 3,985.", "A $3,985 profit target.",
    "Take-profit at 3,985.", "Our $3,985 target.",
])
def test_decision_157_saved_plan_update_detects_added_targets(saved_posts, line):
    text = saved_posts["timed_plan_update"]["text"]
    assert not plan_target_present(text)
    assert plan_target_present(f"{text}\n{line}")


def test_decision_157_allows_macro_policy_targets_and_qualitative_outcomes(saved_posts):
    text = saved_posts["timed_plan_update"]["text"]
    assert not plan_target_present(
        text + "\nInflation target: 2%. The Fed's target of 2% remains in place."
        "\nThe plan hit its target. The result was reported at 12:30 ET."
        "\nhttps://example.test/target-level-3985"
    )


def test_decision_158_flags_legacy_voice_and_accepts_a_split_case_label(saved_posts):
    text = saved_posts["plan_analysis_reply"]["text"]
    assert plan_scenario_flags(text) == ("SCENARIO_CASES_MISSING",)
    scenario = "Base case (55%): The decline holds.\nBull case: Gold rebounds if talks fail."
    assert plan_scenario_flags(f"{text}\n{scenario}") == ()
    assert plan_scenario_flags(f"{text}\n{scenario}\nLong first, then sell.") == ("POSITION_WORDS_REPEATED",)


def _assert_wrap_shape(kind, body):
    assert "## Scenarios" in body.splitlines(), "Wrap lost its scenarios"
    if kind == "daily":
        assert re.search(r"(?m)^From the .* close to that capture,", body), "Daily comparison missing"
        rows = re.findall(r"(?m)^\| ([A-Z0-9]+) \| .+", body)
        assert len(rows) == len(WRAP_MARKETS) and set(rows) == WRAP_MARKETS, "Six-market table incomplete"
    else:
        sections = ("Markets closed on Friday", "**What happened.**",
                    "**What markets are weighing at the reopen**", "**The week ahead.**")
        assert all(section in body for section in sections), "Weekend comparison or opening outlook missing"
        assert [body.index(section) for section in sections] == sorted(body.index(section) for section in sections)


@pytest.mark.parametrize(("kind", "reader_format", "line_to_drop", "diagnosis"), [
    ("daily", "DAILY_NOTE", "| XAUUSD |", "Six-market table incomplete"),
    ("weekend", "WEEKLY_REVIEW", "Markets closed on Friday", "Weekend comparison or opening outlook missing"),
])
def test_decision_98_wraps_keep_their_comparison_and_outlook(saved_posts, kind, reader_format, line_to_drop, diagnosis):
    wrap = saved_posts["wraps"][kind]
    evidence = wrap["evidence"]
    assert article_format({"selected_candidate": {"title": wrap["title"]}}, evidence["work_item_id"]) == reader_format
    published_et = public_datetime(evidence["published_at_utc"])
    if kind == "daily":
        assert published_et.weekday() < 5 and published_et.time() < time(9, 30)
    else:
        assert published_et.weekday() == 6
    def check(body):
        _, binding = _payload_binding({
            "native_payload": {"title": wrap["title"], "body_markdown": body},
        }, "substack")
        heading, bound_body = binding["expected_text_segments"]
        assert heading == wrap["title"]
        _assert_wrap_shape(kind, bound_body)

    body = wrap["body_excerpt"]
    check(body)
    broken = "\n".join(line for line in body.splitlines() if not line.startswith(line_to_drop))
    with pytest.raises(AssertionError, match=diagnosis):
        check(broken)


@pytest.mark.parametrize("label", ["An AI-run desk.", "Written by Claude."])
def test_decision_109_the_plan_reply_keeps_internal_authorship_out_of_copy(saved_posts, label):
    text = saved_posts["plan_analysis_reply"]["text"]
    assert public_filter(text)["status"] == "PASS"

    with pytest.raises(ValueError, match="PLAN_ANALYSIS_DESK_AI_LABEL_FORBIDDEN"):
        public_filter(f"{text}\n{label}")


def _assert_bound_plan_reply(text, summary, canonical_url):
    links = re.findall(r"(?m)^Full analysis: (\S+)$", text)
    assert links == [canonical_url], "Confirmed full-analysis link missing or wrong"
    layers = [line.partition(": ")[::2] for line in text.splitlines() if line.partition(": ")[0] in PLAN_LAYERS]
    assert len({label for label, _ in layers}) >= 3, "Fewer than three analysis layers"
    for label, line in layers:
        assert line == summary[PLAN_LAYERS[label]], f"{label} differs from the bound plan summary"


def test_decision_113_plan_reply_quotes_its_layers_and_links_its_own_analysis(saved_posts):
    reply = saved_posts["plan_analysis_reply"]
    source = reply["source"]
    canonical = reply["public_analysis_url"]
    _assert_bound_plan_reply(reply["text"], source["summary"], canonical)
    packet = {
        "native_payload": {"title": source["title"]},
        "manuscript": {key: source[key] for key in ("reader_contract", "reader_revision")},
        "source_plan": {"asset_id": source["asset_id"]},
        "summary": source["summary"],
    }
    rendered = structured_summary(packet, "telegram", canonical, version=2)
    _assert_bound_plan_reply(rendered, source["summary"], canonical)
    assert public_filter(rendered)["status"] == "PASS"

    no_link = "\n".join(line for line in reply["text"].splitlines() if not line.startswith("Full analysis: "))
    with pytest.raises(AssertionError, match="Confirmed full-analysis link missing or wrong"):
        _assert_bound_plan_reply(no_link, source["summary"], canonical)
    changed_layer = reply["text"].replace(source["summary"]["macro"], "We ignored the upcoming data release.")
    with pytest.raises(AssertionError, match="Macro differs from the bound plan summary"):
        _assert_bound_plan_reply(changed_layer, source["summary"], canonical)


def test_cc788_a_nasdaq_100_plan_reply_follows_the_same_decisions(saved_posts):
    """CC-788: the saved gold reply, rebound to a Nasdaq 100 plan, passes the same decision checks."""
    reply = saved_posts["plan_analysis_reply"]
    source = deepcopy(reply["source"])
    source["asset_id"] = "USTEC"
    source["title"] = source["title"].replace("Gold", "Nasdaq 100").replace("3954", "25,120").replace(
        "3964", "25,180").replace("4004", "24,990")
    canonical = reply["public_analysis_url"]
    packet = {
        "native_payload": {"title": source["title"]},
        "manuscript": {key: source[key] for key in ("reader_contract", "reader_revision")},
        "source_plan": {"asset_id": "USTEC"},
        "summary": source["summary"],
    }
    rendered = structured_summary(packet, "telegram", canonical, version=2)
    _assert_bound_plan_reply(rendered, source["summary"], canonical)
    assert rendered.startswith("Nasdaq 100: Our bearish plan, 25,120") and "USTEC" not in rendered
    assert public_filter(rendered)["status"] == "PASS"
    assert not plan_target_present(rendered)
    assert plan_target_present(rendered + "\nTarget level: 26,400.")
    assert plan_posts.TITLES["USTEC"] == "Nasdaq 100"


def _assert_new_correction(request, original_url, new_url):
    assert request["action"] == "PUBLISH", "Correction opened an edit or delete path"
    assert not request.get("public_object_id") and not request.get("public_object_url"), "Correction targeted an existing post"
    assert new_url and new_url != original_url, "Correction reused the original public object"


def test_decision_136_gold_correction_is_a_new_post(saved_posts, tmp_path):
    correction = saved_posts["correction"]
    original = correction["original"]
    store = ContentOpsDurableStore(tmp_path / "correction.sqlite3")
    for key in (original["status_key"], original["note_work_id"]):
        store.create_work_item(story_id=key, work_item_id=key, title="Original Gold analysis",
                               target_surface="MULTI_PLATFORM")
    original_row = json.dumps({"key": original["status_key"], "symbol": "XAUUSD",
                               "schema_version": plan_posts.SCHEMA, "text": original["status_public_text"]})
    store.register_outbox_message(message_id=original["status_key"], work_item_id=original["status_key"],
                                  destination=plan_posts.DESTINATION, payload=original_row)
    store.register_outbox_message(message_id="original-note", work_item_id=original["note_work_id"],
                                  destination="substack_notes", payload="{}")
    store.register_platform_dispatch(dispatch_id="original-note", message_id="original-note",
                                     platform="substack_notes", status="DISPATCH_CONFIRMED",
                                     public_object_id=correction["original_object_id"],
                                     public_object_url=correction["original_url"])

    row = followups.prepare_gold_correction(store, now=datetime.fromisoformat(correction["prepared_at_utc"]))
    assert row["key"] == correction["row"]["key"] != original["status_key"]
    assert row["kind"] == "correction" and row["new_post_only"] is True
    assert store.get_outbox_message(original["status_key"])["payload"] == original_row
    assert store.get_platform_dispatch("original-note")["public_object_url"] == correction["original_url"]
    new_url = correction["evidence"]["public_url"]
    _assert_new_correction(correction["request"], correction["original_url"], new_url)
    chart_id = saved_posts["charts"]["gold"]["asset"]["asset_id"]
    payload = followups.destination_payloads(row, card_id=chart_id, chart_credit=True)["substack_notes"]
    assert payload["text"] == correction["public_text"]
    assert payload["media_asset_ids"] == [chart_id]
    assert not payload.get("reply_to_id")

    broken_request = {**correction["request"], "action": "EDIT_EXISTING",
                      "public_object_url": correction["original_url"],
                      "public_object_id": correction["original_object_id"]}
    with pytest.raises(AssertionError, match="Correction opened an edit or delete path"):
        _assert_new_correction(broken_request, correction["original_url"], new_url)


def _assert_coverage(expected_destinations, outcomes):
    absent = expected_destinations - {
        route for route, outcome in outcomes.items()
        if outcome["status"] == "DISPATCH_CONFIRMED" and outcome["public_object_id"]
    }
    assert not absent, f"Named destinations lack confirmed copies: {sorted(absent)}"


def test_coverage_every_named_article_destination_gets_its_copy(saved_posts, tmp_path):
    coverage = saved_posts["wrap_coverage"]
    work_id = coverage["readbacks"]["substack"]["work_item_id"]
    plan = _build_rolling_x_publication_plan(
        run_id=work_id, output_dir=tmp_path, viability={}, readiness={},
        preparation={
            "release_candidate_lock": coverage["release_lock"],
            "context": {"article": coverage["article"],
                        "media": {"assets": [{"asset_id": value} for value in coverage["media_asset_ids"]]}},
        },
    )
    # The coordinator owns the canonical and the individually selected company-page copy.
    assert {row["destination"] for row in plan["destinations"]} == WRAP_DESTINATIONS - {"linkedin_company"}
    assert all(row["payload_hash"] for row in plan["destinations"])
    assert not plan["pre_substack_blockers"]

    store = ContentOpsDurableStore(tmp_path / "golden.sqlite3")
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None)
    plan_hash = plan["plan_hash"]
    store.create_work_item(story_id=work_id, work_item_id=work_id, title=coverage["article"]["title"],
                           target_surface="MULTI_PLATFORM")
    for route, readback in coverage["readbacks"].items():
        ids = coordinator._ids(work_id, plan_hash, route)
        store.register_outbox_message(message_id=ids["message_id"], work_item_id=work_id, destination=route,
                                      payload=json.dumps({"work_item_id": work_id, "plan_hash": plan_hash}),
                                      status="DISPATCH_CONFIRMED")
        store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
                                         platform=route, status="DISPATCH_CONFIRMED",
                                         public_object_id=readback["public_object_id"],
                                         public_object_url=readback["public_url"])
    outcomes = coordinator.publication_state(work_id, plan)["per_destination"]
    _assert_coverage(WRAP_DESTINATIONS, outcomes)

    broken_plan = {**plan, "destinations": [row for row in plan["destinations"] if row["destination"] != "discord"]}
    broken = coordinator.publication_state(work_id, broken_plan)["per_destination"]
    with pytest.raises(AssertionError, match="Named destinations lack confirmed copies: .*discord"):
        _assert_coverage(WRAP_DESTINATIONS, broken)


def test_coverage_every_named_plan_alert_destination_gets_its_copy(saved_posts):
    coverage = saved_posts["plan_coverage"]
    planned = set(plan_cards.destinations_for(coverage["row"]))
    assert planned == PLAN_DESTINATIONS
    evidence = coverage["readbacks"]
    _assert_coverage(planned, evidence)

    unknown = {**evidence, "substack_notes": {**evidence["substack_notes"], "status": "UNKNOWN_WRITE"}}
    with pytest.raises(AssertionError, match="Named destinations lack confirmed copies: .*substack_notes"):
        _assert_coverage(planned, unknown)


def test_cc822_managed_exit_renders_closed_by_plan_rule_with_no_target():
    """CC-822: MANAGED_EXIT outcomes bind cleanly and carry the public label 'closed by its plan rule'."""
    from live_contentops import plan_state_alerts_v1 as alerts

    resolved_at = "2026-11-23T16:35:41.547000Z"
    plan_id = "plan_add6d62299828744939aafc1"
    outcome_id = "outcome_673db05e49ce248f9c0ff67cb932fbb0"
    score = {
        "asset_id": "BTCUSD", "plan_id": plan_id, "outcome_id": outcome_id, "direction": "BEARISH",
        "result": "MANAGED_EXIT", "score_basis": "DETERMINISTIC_THESIS_INVALIDATION",
        "exit_slices": [{"score_basis": "DETERMINISTIC_THESIS_INVALIDATION",
                         "resolved_at_utc": resolved_at, "gross_r_contribution": 0.5}],
        "frozen_at_utc": "2026-11-22T19:19:27Z", "triggered_at_utc": "2026-11-22T19:27:00Z",
        "horizon_end_utc": "2026-12-09T18:00:00Z", "resolved_at_utc": resolved_at,
        "scored_at_utc": "2026-11-23T16:35:43Z", "content_hash": "a" * 64,
    }
    plan = {
        "plan_id": plan_id, "asset_id": "BTCUSD", "direction": "BEARISH", "status": "CLOSED",
        "zone": {"minimum": 60500.0, "maximum": 61500.0}, "expires_at_utc": "2026-12-09T18:00:00Z",
        "registered_at_utc": "2026-11-22T19:19:27Z",
        "invalidation_conditions": [{"field": "high", "operator": "GTE", "threshold": 66800.0}],
        "outcome": {"state": "SCORED", "result": "MANAGED_EXIT", "outcome_id": outcome_id,
                    "result_r": 0.12, "score": score},
    }
    export = {
        "status": {"schema": "CapitalChroniclePlanStatusV1", "schema_version": "1.0.0",
                   "contract_version": "2.0.0", "generated_at_utc": "2026-11-23T16:36:00Z",
                   "content_hash": "b" * 64, "scored_call_count": 1, "plans": [plan], "scored_calls": [score]},
        "transitions": {"schema": "CapitalChroniclePlanTransitionsV1", "schema_version": "1.0.0",
                        "generated_at_utc": "2026-11-23T16:36:00Z", "status_content_hash": "b" * 64,
                        "transitions": [{"plan_id": plan_id, "status": "CLOSED",
                                         "at_utc": resolved_at, "reason_code": "DETERMINISTIC_THESIS_INVALIDATION"}]},
    }
    row, = plan_posts.result_rows_from_export(export)
    assert row["result"] == "MANAGED_EXIT"
    composed = plan_posts.compose_result(row)
    assert "closed by its plan rule" in composed["text"]
    assert "MANAGED_EXIT" not in composed["text"] and not plan_target_present(composed["text"])
    assert plan_cards.ending_words({"result": "MANAGED_EXIT", "score_basis": "REDUCE_HALF"}) == "closed by its plan rule"
    headline = alerts.result_headline({
        "instrument_title": "Bitcoin", "result": "MANAGED_EXIT", "scored": True,
        "result_frame": {"policy": "RESULT_FRAME_V1", "plan_dates": "22–23 Nov", "correction": False},
        "outcome_source_plan": plan,
    })
    assert headline == "Bitcoin, plan of 22–23 Nov: closed by its plan rule. Result: +0.1R."
    assert not plan_target_present(headline)
