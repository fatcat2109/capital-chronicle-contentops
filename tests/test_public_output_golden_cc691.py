"""Replay confirmed Capital Chronicle posts without contacting their transports."""

from copy import deepcopy
from datetime import datetime, time
import json
from pathlib import Path
import re

import pytest

from live_contentops import call_followups_v1 as followups
from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _build_rolling_x_publication_plan
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.plan_analysis_pages_v1 import public_filter, structured_summary
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
    assert update["rendered_timestamp"] in update["text"]

    broken = update["text"].replace(clock, "12:36 GMT+7")
    with pytest.raises(ValueError, match="PUBLIC_TIMEZONE_ET_REQUIRED"):
        require_public_time(broken)


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
    body = wrap["body_excerpt"]
    _assert_wrap_shape(kind, body)

    broken = "\n".join(line for line in body.splitlines() if not line.startswith(line_to_drop))
    with pytest.raises(AssertionError, match=diagnosis):
        _assert_wrap_shape(kind, broken)


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

    no_link = "\n".join(line for line in reply["text"].splitlines() if not line.startswith("Full analysis: "))
    with pytest.raises(AssertionError, match="Confirmed full-analysis link missing or wrong"):
        _assert_bound_plan_reply(no_link, source["summary"], canonical)
    changed_layer = reply["text"].replace(source["summary"]["macro"], "We ignored the upcoming data release.")
    with pytest.raises(AssertionError, match="Macro differs from the bound plan summary"):
        _assert_bound_plan_reply(changed_layer, source["summary"], canonical)


def _assert_new_correction(request, original_url, new_url):
    assert request["action"] == "PUBLISH", "Correction opened an edit or delete path"
    assert not request.get("public_object_id") and not request.get("public_object_url"), "Correction targeted an existing post"
    assert new_url and new_url != original_url, "Correction reused the original public object"


def test_decision_136_gold_correction_is_a_new_post(saved_posts):
    correction = saved_posts["correction"]
    row = correction["row"]
    assert row["new_post_only"] is True
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


def _assert_coverage(outcomes):
    absent = WRAP_DESTINATIONS - {
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
    _assert_coverage(outcomes)

    broken_plan = {**plan, "destinations": [row for row in plan["destinations"] if row["destination"] != "discord"]}
    broken = coordinator.publication_state(work_id, broken_plan)["per_destination"]
    with pytest.raises(AssertionError, match="Named destinations lack confirmed copies: .*discord"):
        _assert_coverage(broken)
