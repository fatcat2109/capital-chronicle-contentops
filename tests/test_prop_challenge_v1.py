from copy import deepcopy
import hashlib
import json

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.prop_challenge_v1 import (
    evaluate, held_dataset, load_rules, position_reference, source_document, verified_source_metadata,
)
from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack


@pytest.fixture
def rules():
    return load_rules()


def dataset(*trades, **kw):
    return {"month": "2026-11", "cutoff_utc": "2026-11-11T09:00:00Z",
            "source_known_at_utc": "2026-11-11T09:00:00Z", "trades": list(trades),
            "excluded_operations_tests": [], "excluded_cash_record_count": 0,
            "equity_path_complete": False, "equity_path_cause": "NORMALISED_INTRADAY_EQUITY_PATH_ABSENT", **kw}


def trade(tid="a", opened="2026-11-06T12:00:00Z", closed="2026-11-06T13:00:00Z", net_r="1", cost_r="0"):
    events = [{"at_utc": opened, "net_r": cost_r}]
    if closed:
        events.append({"at_utc": closed, "net_r": net_r})
    return {"trade_id": tid, "opened_at_utc": opened, "closed_at_utc": closed, "events": events}


def verdicts(report):
    return {r["rule"]: r["verdict"] for r in report["rules"]}


def test_actual_phase_exemptions_and_sourced_rules(rules):
    out = evaluate(dataset(trade()), rules)
    assert verdicts(out) == {"profit_target": "NOT_MET", "maximum_daily_loss": "UNKNOWN",
        "maximum_loss": "UNKNOWN", "minimum_trading_days": "NOT_MET",
        "news_window": "NOT_APPLICABLE", "weekend_holding": "NOT_APPLICABLE"}
    assert all(r["source"] in rules["sources"] for r in out["rules"])
    assert rules["subsequent_standard_account"]["news_restricted_minutes_before"] == 2
    assert rules["subsequent_standard_account"]["market_break_hours_greater_than"] == "2"


def test_fixed_half_percent_risk_and_cost_clock(rules):
    out = evaluate(dataset(trade(net_r="2", cost_r="-0.2")), rules)
    assert out["booked_model_change_pct"] == "0.90"
    assert out["open_trade_count"] == 0


@pytest.mark.parametrize("r,expected", [("20", "PASS"), ("19.999", "NOT_MET")])
def test_closed_target_boundary(rules, r, expected):
    assert verdicts(evaluate(dataset(trade(net_r=r)), rules))["profit_target"] == expected


def test_verification_resets_target_not_challenge_return(rules):
    ds = dataset(trade(net_r="10"))
    assert verdicts(evaluate(ds, rules))["profit_target"] == "NOT_MET"
    assert verdicts(evaluate(ds, rules, phase="verification"))["profit_target"] == "PASS"


def test_floating_profit_cannot_pass_closed_profit_target(rules):
    ds = dataset(trade(closed=None), equity_points=[{"at_utc": "2026-11-07T12:00:00Z", "equity_index": "120"}])
    assert verdicts(evaluate(ds, rules))["profit_target"] == "NOT_MET"


def test_sampled_good_marks_never_prove_loss_pass(rules):
    ds = dataset(trade(), equity_points=[{"at_utc": "2026-11-06T12:30:00Z", "equity_index": "99"}])
    assert verdicts(evaluate(ds, rules))["maximum_daily_loss"] == "UNKNOWN"


def test_single_observed_breach_is_failure_even_with_gaps(rules):
    ds = dataset(trade(closed=None), equity_points=[{"at_utc": "2026-11-06T12:30:00Z", "equity_index": "89.99"}])
    out = evaluate(ds, rules)
    assert verdicts(out)["maximum_daily_loss"] == "FAIL"
    assert verdicts(out)["maximum_loss"] == "FAIL"
    assert out["overall"] == "FAIL"


def test_prague_midnight_resets_balance_not_previous_floating_equity(rules):
    ds = dataset(trade(opened="2026-11-06T20:00:00Z", closed=None), equity_path_complete=True,
        equity_points=[{"at_utc": "2026-11-06T22:59:59Z", "equity_index": "106"},
                       {"at_utc": "2026-11-06T23:00:00Z", "equity_index": "100"}])
    assert verdicts(evaluate(ds, rules))["maximum_daily_loss"] == "PASS"


def test_daily_reset_uses_previous_booked_gain(rules):
    ds = dataset(trade(net_r="8"), trade("b", "2026-11-07T00:00:00Z", None),
        equity_points=[{"at_utc": "2026-11-07T00:01:00Z", "equity_index": "98.99"}])
    assert verdicts(evaluate(ds, rules))["maximum_daily_loss"] == "FAIL"


def test_equality_to_current_published_limit_is_not_below_it(rules):
    out = evaluate(dataset(trade(net_r="-10")), rules)
    assert verdicts(out)["maximum_daily_loss"] == "UNKNOWN"
    assert verdicts(evaluate(dataset(trade(net_r="-10.01")), rules))["maximum_daily_loss"] == "FAIL"


def test_prague_trading_days_count_openings_not_exits(rules):
    out = evaluate(dataset(trade(opened="2026-11-05T23:30:00Z", closed="2026-11-07T01:00:00Z"),
        trade("b", "2026-11-06T12:00:00Z", "2026-11-06T13:00:00Z")), rules)
    assert out["trading_days"] == 1


def test_simultaneous_deals_settle_before_flat_checkpoint(rules):
    out = evaluate(dataset(trade(net_r="22"), trade("b", net_r="-24")), rules)
    assert verdicts(out)["profit_target"] == "NOT_MET"
    assert out["booked_model_change_pct"] == "-1.0"


def fixture_files(tmp_path):
    ref = position_reference(701)
    def row(entry, at, profit, commission, volume="1"):
        fact = {"effective_at_utc": at, "deal_type": 0 if entry == 0 else 1,
            "deal_entry": entry, "position_reference": ref, "normalized_comment": "cc_genuine_fixture",
            "profit": profit, "commission": commission, "swap": "0", "fee": "0",
            "volume": {"executed": volume}}
        return {"fact": fact, "fact_hash": sha256_of(fact),
                "source_record": {"account_fingerprint_hash": "per-observation-not-stable"}}
    rows = {"entry": row(0, "2026-11-06T12:00:00Z", "0", "-2"),
            "exit": row(1, "2026-11-06T13:00:00Z", "200", "-2")}
    statement = {"known_at_utc": "2026-11-11T09:00:00Z", "account_binding": "fixture-account", "complete_since_baseline": True,
        "unobserved_intervals": [{"reason": "TEST_PATH_GAP"}], "broker_records": rows,
        "source_observation": {"coverage_from_utc": "2026-10-12T00:00:00Z", "coverage_to_utc": "2026-11-11T09:00:00Z",
            "environment": "DEMO", "currency": "USD", "account_binding": "fixture-account",
            "reconciliation": {"account_binding": "fixture-account"}}}
    journal = {"position_ticket": 701, "intent_identity": {"initial_risk_cash": "200",
        "stable_account_identity_hash": "fixture-account", "initial_risk_currency": "USD",
        "risk_frozen_at_utc": "2026-11-06T11:59:00Z"}}
    root = tmp_path / "private-inputs"
    root.mkdir()
    (root / "risk.json").write_bytes(canonical_bytes(journal))
    path = tmp_path / "economic.json"
    path.write_bytes(canonical_bytes({"statement": statement}))
    return path, root, statement, journal


def test_held_inputs_reach_real_writer_consumer_without_private_fields(tmp_path, rules):
    path, root, statement, journal = fixture_files(tmp_path)
    original = path.read_bytes()
    ds = held_dataset(path, root, month="2026-11", cutoff_utc="2026-11-11T09:00:00Z")
    report = evaluate(ds, rules)
    doc = source_document(report, rules)
    pack = _source_pack([doc])
    assert len(pack) == 1
    assert pack[0]["canonical_content_text"] == doc["canonical_content_text"]
    assert pack[0]["prop_challenge_binding"] == doc["prop_challenge_binding"]
    assert report["booked_model_change_pct"] == "0.490"
    encoded = canonical_bytes(pack).decode()
    for private in ("fixture-account", "initial_risk_cash", "position_ticket", "position_reference", str(path)):
        assert private not in encoded
    assert path.read_bytes() == original


@pytest.mark.parametrize("change,cause", [
    ("risk_absent", "INITIAL_RISK_RECORD_ABSENT"), ("account", "ACCOUNT_BINDING_CHANGED"),
    ("currency", "RISK_IDENTITY_CURRENCY_OR_CLOCK_CONFLICT"), ("cost", "NUMBER_ABSENT"),
    ("duplicate", "DUPLICATE_DEAL"), ("future", "SOURCE_AFTER_CUTOFF"),
])
def test_no_guessed_join_currency_cost_or_dropped_deal(tmp_path, change, cause):
    path, root, statement, journal = fixture_files(tmp_path)
    if change == "risk_absent":
        (root / "risk.json").unlink()
    elif change == "account":
        statement["account_binding"] = "other-account"
    elif change == "currency":
        journal["intent_identity"]["initial_risk_currency"] = "EUR"
        (root / "risk.json").write_bytes(canonical_bytes(journal))
    elif change == "cost":
        statement["broker_records"]["entry"]["fact"]["commission"] = None
    elif change == "duplicate":
        statement["broker_records"]["another"] = statement["broker_records"]["entry"]
    else:
        statement["known_at_utc"] = "2026-11-11T10:00:00Z"
    path.write_bytes(canonical_bytes({"statement": statement}))
    with pytest.raises(ValueError, match=cause):
        held_dataset(path, root, month="2026-11", cutoff_utc="2026-11-11T09:00:00Z")


def test_exact_exclusion_of_labelled_ops_test_not_losing_desk_trade(tmp_path):
    path, root, statement, journal = fixture_files(tmp_path)
    for row in statement["broker_records"].values():
        row["fact"]["normalized_comment"] = "ops_test_example"
    statement["broker_records"]["desk-entry"] = deepcopy(statement["broker_records"]["entry"])
    statement["broker_records"]["desk-entry"]["fact"].update(position_reference=position_reference(702), normalized_comment="cc_genuine_2")
    statement["broker_records"]["desk-entry"]["fact_hash"] = "different"
    journal["position_ticket"] = 702
    (root / "risk.json").write_bytes(canonical_bytes(journal))
    path.write_bytes(canonical_bytes({"statement": statement}))
    ds = held_dataset(path, root, month="2026-11", cutoff_utc="2026-11-11T09:00:00Z")
    assert len(ds["trades"]) == 1 and len(ds["excluded_operations_tests"]) == 1


def test_partial_exit_remains_open(tmp_path, rules):
    path, root, statement, _ = fixture_files(tmp_path)
    statement["broker_records"]["exit"]["fact"]["volume"]["executed"] = "0.5"
    path.write_bytes(canonical_bytes({"statement": statement}))
    ds = held_dataset(path, root, month="2026-11", cutoff_utc="2026-11-11T09:00:00Z")
    out = evaluate(ds, rules)
    assert out["open_trade_count"] == 1
    assert out["observed_flat_checkpoint_count"] == 0


def test_source_binding_rejects_changed_writer_facts(rules):
    doc = source_document(evaluate(dataset(trade()), rules), rules)
    doc["canonical_content_text"] = doc["canonical_content_text"].replace("UNKNOWN", "PASS")
    with pytest.raises(ValueError, match="PUBLIC_SOURCE_CHANGED"):
        _source_pack([doc])


def test_foreign_fingerprint_is_not_confused_with_stable_account(tmp_path):
    path, root, statement, journal = fixture_files(tmp_path)
    # The adapter's real contract uses an observation fingerprint and a stable
    # account binding for different identities. Their inequality is expected.
    assert held_dataset(path, root, month="2026-11", cutoff_utc="2026-11-11T09:00:00Z")["trades"]
