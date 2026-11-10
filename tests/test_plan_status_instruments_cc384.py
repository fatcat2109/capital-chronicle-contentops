"""CC-383 declared shape -> existing queue, image facts and sole publisher."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

from live_contentops import plan_status_posts_v1 as p
from live_contentops.event_article_guard_v1 import check_publication_copy
from test_plan_status_posts_cc306 import NOW, event, main_root, plan, write_export  # noqa: F401, F811
from test_plan_status_publication_cc306 import fake_host, no_real_snapshot  # noqa: F401
from test_plan_status_rationale_cc353 import export_plan
from test_publication_coordinator_v1 import _coordinator, _set_mode


def source(*, mapped=True, dual=True, rationale=True):
    value = plan("plan_instrument", "US500", "BULLISH", 6900, 6910, invalid=6880)
    if rationale:
        reasons = export_plan()
        value.update({k: reasons[k] for k in (*p.REASON_FIELDS, "scenario_analysis") if k in reasons})
    value["entries"] = [{"kind": "LIMIT", "zone_low": 6900, "zone_high": 6910}]
    if dual:
        value["entries"].append({"kind": "BREAKOUT", "level": 6930})
    value["public_instrument"] = {"name": "S&P 500", "symbol": "ES", "kind": "FUT",
        "exchange": "CME", "contract_month": "2026-12", "zone_low": 7000 if mapped else None,
        "zone_high": 7010 if mapped else None, "invalidation_level": 6980 if mapped else None,
        "levels_first_cause": None if mapped else "IBKR_TICKET_NOT_SUBMITTED",
        "entries": [{"kind": "LIMIT", "zone_low": 7000 if mapped else None, "zone_high": 7010 if mapped else None}]}
    if dual:
        value["public_instrument"]["entries"].append({"kind": "BREAKOUT", "level": 7030 if mapped else None})
    return value


def composed(value, state="WAITING", first=False):
    row = p._row(plan_id=value["plan_id"], symbol=value["asset_id"], to=state,
                 at_utc=NOW.isoformat(), cause=state, plan=p._built_plan(value, state=state))
    return {"symbol": row["symbol"], "state": state, **p.compose(row, first_plan_post=first)}


@pytest.mark.parametrize("mapped", [True, False])
@pytest.mark.parametrize("rationale", [True, False])
@pytest.mark.parametrize("direction", ["BULLISH", "BEARISH"])
def test_both_conditions_one_bounded_post_per_destination(mapped, rationale, direction):
    value = source(mapped=mapped, rationale=rationale)
    value["direction"] = direction
    if direction == "BEARISH":
        value["invalidation_conditions"] = [{"field": "close", "operator": "GT", "threshold": 6960}]
        value["public_instrument"]["invalidation_level"] = 7060 if mapped else None
    before = deepcopy(value)
    post = composed(value)
    assert value == before
    assert "S&P 500 (ES futures, Dec 2026)" in post["text"]
    assert len(post["conditional_calls"]) == 1
    call = post["conditional_calls"][0]
    assert call["direction"] == direction.lower()
    for token in (("7,000–7,010", "7,030") if mapped else ("6,900–6,910", "6,930")):
        assert token in call["condition"]
    assert "(limit)" in call["condition"] and "(breakout)" in call["condition"]
    for destination, payload in p.destination_payloads(post, card_id="card", chart_credit=True).items():
        assert not payload.get("parts")
        parts = [part["text"] for part in payload.get("posts") or []] or [payload["text"]]
        assert all((p._x_length(part) if destination == "x" else len(part)) <= p.LIMITS[destination] for part in parts)
        check_publication_copy({"post": payload["full_text"]}, conditional_calls=post["conditional_calls"])
        assert "ES futures, Dec 2026" in payload["full_text"]
        assert "(limit)" in payload["full_text"] and "(breakout)" in payload["full_text"]
        if destination in p.API_DESTINATIONS:
            assert len(parts) == 1


def test_null_and_partial_mapping_keep_all_original_plan_prices():
    for missing in ("zone_low", "invalidation_level", "entry"):
        value = source()
        public = value["public_instrument"]
        if missing == "entry":
            public["entries"][1]["level"] = None
        else:
            public[missing] = None
        post = composed(value)
        assert post["price_basis"] == "plan"
        assert "Levels use the plan's prices." in post["text"]
        assert all(n in post["text"] for n in ("6,900–6,910", "6,930", "6,880"))
        assert all(n not in post["text"] for n in ("7,000", "7,010", "7,030", "6,980"))
        assert public["entries"][1]["level"] is None if missing == "entry" else public[missing] is None


def test_single_entry_preserves_legacy_condition_and_missing_fields_preserve_bytes():
    legacy = plan("plan_old", "US500", "BULLISH", 6900, 6910, invalid=6880)
    original = composed(legacy)
    single = {**legacy, "entries": [{"kind": "LIMIT", "zone_low": 6900, "zone_high": 6910}]}
    post = composed(single)
    assert post["text"].replace("\n", " ") == original["text"].replace("\n", " ")
    assert post["conditional_calls"] == original["conditional_calls"]
    assert composed(legacy) == original


@pytest.mark.parametrize("state,first", [("TRIGGERED", False), ("FILLED", False), ("TRIGGERED", True)])
def test_fill_names_same_instrument_and_never_uses_execution_fields(state, first):
    value = source()
    value.update(fill_price=7999.888, account="secret-account", size=998877, order_id="private-order")
    value["public_instrument"].update(fill_price=7999.888, account="secret-account")
    value["entries"][0].update(size=998877, order_id="private-order")
    built = p._built_plan(value)
    assert "secret-account" not in json.dumps(built)
    assert "private-order" not in json.dumps(built)
    assert "fill_price" not in json.dumps(built)
    post = composed(value, state, first)
    assert "ES futures, Dec 2026" in post["text"]
    assert "position is open" in post["text"]
    assert not any(v in post["text"] for v in ("7999.888", "998877", "CFD", "US500"))
    payloads = p.destination_payloads(post, card_id="card", chart_credit=True)
    assert len(payloads["threads"]["text"]) <= 500


def test_spot_name_and_missing_month_are_not_invented():
    value = source(mapped=False)
    value["asset_id"] = "EURUSD"
    value["public_instrument"].update(name="Euro", symbol="EUR.USD", kind="SPOT", exchange="IDEALPRO", contract_month=None)
    assert "Euro (EUR.USD spot)" in composed(value)["text"]
    value["public_instrument"].update(name="WTI crude oil", symbol="CL", kind="FUT", exchange="NYMEX")
    text = composed(value)["text"]
    assert "WTI crude oil (CL futures)" in text and "Dec 2026" not in text


def test_inverse_instrument_uses_the_producers_direction_and_prices():
    value = source()
    value.update(asset_id="USDJPY", direction="BEARISH")
    value["public_instrument"].update(name="Japanese yen", symbol="6J", direction="BULLISH")
    post = composed(value)
    call = post["conditional_calls"][0]
    assert call["direction"] == "bullish" and call["market"] == "6J"
    assert "price moves below 6,980" == call["invalidation"]
    assert "Japanese yen (6J futures, Dec 2026)" in post["text"]


def test_delayed_first_post_keeps_both_conditions_and_both_true_clocks():
    value = source(mapped=False)
    row = p._row(plan_id=value["plan_id"], symbol=value["asset_id"], to="WAITING",
                 at_utc=NOW.isoformat(), cause="WAITING", plan=p._built_plan(value))
    post = {"symbol": row["symbol"], "state": row["to"], **p.compose(row, delayed_at=NOW)}
    for destination, payload in p.destination_payloads(post, card_id="card", chart_credit=True).items():
        assert "Registered " in payload["full_text"] and "delayed update" in payload["full_text"]
        assert "(limit)" in payload["full_text"] and "(breakout)" in payload["full_text"]
        if destination in p.API_DESTINATIONS:
            assert len(payload["text"]) <= p.LIMITS[destination]


@pytest.mark.parametrize("case", ["eur_spot", "oil_dual_null", "oil_dual_mapped"])
def test_committed_main_producer_shapes_reach_all_destinations(case):
    export = json.loads((Path(__file__).parent / "fixtures/cc384_public_plan/producer-exports.json").read_bytes())[case]
    rows = p.rows_from_export(export)
    assert len(rows) == 1
    row = rows[0]
    post = {"symbol": row["symbol"], "state": row["to"], **p.compose(row)}
    assert post["status"] == "COMPOSED"
    for d, payload in p.destination_payloads(post, card_id="card", chart_credit=True).items():
        parts = [part["text"] for part in payload.get("posts") or []] or [payload["text"]]
        assert all((p._x_length(part) if d == "x" else len(part)) <= p.LIMITS[d] for part in parts)
        assert not payload.get("parts")
        check_publication_copy({"text": payload["full_text"]}, conditional_calls=post["conditional_calls"])
        assert ("CL futures, Dec 2026" if case.startswith("oil") else "EUR.USD spot") in payload["full_text"]
        if case.startswith("oil"):
            assert "(limit)" in payload["full_text"] and "(breakout)" in payload["full_text"]


def test_export_queue_existing_coordinator_and_repeat_use_one_identity(tmp_path, main_root):  # noqa: F811
    value = source()
    folder = write_export(tmp_path / "export", [value], [event(value["plan_id"], "WAITING", NOW.isoformat())])
    store, transport, coordinator = _coordinator(tmp_path)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    result = p.queue_posts(store, folder, now=NOW, main_root=main_root, python=sys.executable)
    assert len(result["queued"]) == 1
    key = result["queued"][0]["key"]
    row = p._row_payload(store, key)
    assert row["levels"]["zone_low"] == 7000 and row["entries"][1]["level"] == 7030
    assert ("Breakout", "7,030") in p.plan_facts(row)
    assert p.card_article(row)["title"].startswith("S&P 500 (ES futures, Dec 2026)")
    result = p.publish_ready(store, now=NOW, root=tmp_path / "posts", host=fake_host,
                             coordinator_for=lambda *args: coordinator)
    assert result["posts"][0]["status"] == "PUBLISHED", result
    assert sorted(transport.publish_calls) == sorted(p.POST_DESTINATIONS)
    assert not p.queue_posts(store, folder, now=NOW, main_root=main_root, python=sys.executable)["queued"]
    assert not p.publish_ready(store, now=NOW, root=tmp_path / "posts", host=fake_host,
                               coordinator_for=lambda *args: coordinator)["posts"]
    assert len(transport.publish_calls) == len(p.POST_DESTINATIONS)
