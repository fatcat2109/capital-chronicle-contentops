"""A missing Main quote is not a price-scale mismatch (Ops Product, 11 Nov 2026).

On the first live run of the image contract (16:24Z) every TradingView chart was refused with
TRADINGVIEW_CONTEMPORANEOUS_MAIN_QUOTE_UNAVAILABLE, because Main saves a quote only during its own runs.
"""
import pytest

from live_contentops import publication_image_contract_v1 as contract
from live_contentops.tradingview_snapshot_v1 import SYMBOLS


@pytest.fixture(autouse=True)
def isolated_price_sources(tmp_path, monkeypatch):
    from live_contentops import chart_price_reference_v1 as references
    monkeypatch.setattr(references, "PLAN_STATUS_PATH", tmp_path / "status.json")
    monkeypatch.setattr(references, "BAR_STORE", tmp_path / "bars.sqlite3")


def _snapshot(market):
    return {"tv_symbol": SYMBOLS[market], "sha256": "a" * 64, "captured_at_utc": "2026-11-11T16:24:10+00:00",
            "page_title": "not read when there is no quote"}


def test_a_chart_with_no_saved_quote_is_bound_as_not_compared(tmp_path, monkeypatch):
    monkeypatch.setattr(contract, "QUOTE_ROOT", tmp_path)
    bound = contract.bind_scale("EURUSD", _snapshot("EURUSD"))
    check = bound["price_scale_check"]
    assert check["comparison_basis"] == "NOT_COMPARED"
    assert check["quote_absent_cause"] in contract.QUOTE_ABSENT
    assert check["level_offset"] == 0
    assert contract.validate_scale("EURUSD", bound) == check


def test_a_not_compared_binding_follows_its_own_chart(tmp_path, monkeypatch):
    monkeypatch.setattr(contract, "QUOTE_ROOT", tmp_path)
    bound = contract.bind_scale("XAUUSD", _snapshot("XAUUSD"))
    bound["sha256"] = "b" * 64
    with pytest.raises(contract.ImageContractError, match="TRADINGVIEW_PRICE_SCALE_BINDING_CHANGED"):
        contract.validate_scale("XAUUSD", bound)


def test_the_wrong_symbol_is_still_refused_without_a_quote(tmp_path, monkeypatch):
    monkeypatch.setattr(contract, "QUOTE_ROOT", tmp_path)
    snapshot = _snapshot("EURUSD")
    snapshot["tv_symbol"] = SYMBOLS["USDJPY"]
    with pytest.raises(contract.ImageContractError, match="TRADINGVIEW_MARKET_SYMBOL_MISMATCH"):
        contract.bind_scale("EURUSD", snapshot)


def test_a_supplied_quote_that_fails_is_never_waved_through(tmp_path, monkeypatch):
    monkeypatch.setattr(contract, "QUOTE_ROOT", tmp_path)
    with pytest.raises(contract.ImageContractError):
        contract.bind_scale("EURUSD", _snapshot("EURUSD"), quote={"market": "USDJPY", "instrument": "USDJPY"})
