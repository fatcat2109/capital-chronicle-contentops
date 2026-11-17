"""CC-563 regressions from the CC-548 advisor pre-review (14 Nov 2026).

Retains the advisor's nine inputs and checks durable refusal/restart behaviour
and capture-state isolation. Temporary stores and folders only: no production
store, browser or network.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

from live_contentops import publication_image_contract_v1 as contract
from live_contentops import substack_daily_digest_v1 as digest
from test_publication_image_contract_cc463 import chart, message_with
from test_substack_daily_digest_cc548 import held_digest
from test_substack_daily_digest_v1 import clock


NOW = datetime(2026, 11, 14, 12, 15, tzinfo=timezone.utc)
FIXTURES = Path(__file__).parent / "fixtures/cc548"


def folderless_coordinator():
    return SimpleNamespace(store=None, _clock=lambda: NOW)


def saved_intent():
    return json.loads((FIXTURES / "stored-12nov-intent.json").read_bytes())


# 1. A digest with an empty article list -------------------------------------

def test_refused_digest_with_no_articles_freezes_no_new_digest(tmp_path, monkeypatch):
    store, feed, packet, ids = held_digest(tmp_path)
    real_packets = digest.packets
    # The held refused packet as the owner reads it, with an empty article
    # list. The owner must not invent a digest from it.
    monkeypatch.setattr(digest, "packets", lambda s: [{**p, "articles": []} for p in real_packets(s)])
    result = digest.prepare_daily_digest(store, feed, now=clock("2026-11-14T12:15:00Z"))
    assert result["state"] == "NO_CONFIRMED_ARTICLES"
    assert "packet" not in result
    assert len(real_packets(store)) == 1


def test_folderless_digest_intent_with_no_media_is_outside_the_chart_contract():
    intent = saved_intent()
    intent["media_assets"] = []
    assert contract.validate_write(folderless_coordinator(), intent, "substack") is None


# 2. An intent with output_dir present but no run_context ----------------------

def test_output_dir_without_run_context_is_refused_not_passed(tmp_path):
    intent = saved_intent()
    intent["output_dir"] = str(tmp_path)          # folder exists, run_context_v1.json does not
    with pytest.raises(FileNotFoundError):
        contract.validate_write(folderless_coordinator(), intent, "substack")


def test_deleted_run_folder_is_recorded_as_a_definite_no_write_with_its_first_cause(tmp_path):
    """A missing run folder is refused before any destination probe or write."""
    store, runtime, coordinator, message = message_with(tmp_path / "run", [])
    intent = json.loads(message["payload"])
    shutil.rmtree(intent["output_dir"])
    coordinator._readiness = lambda *a: pytest.fail("a deleted run reached a destination probe")
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == "DEFINITE_NO_WRITE"
    assert result["reason_code"] == "PUBLICATION_IMAGE_CONTRACT_INVALID"
    assert result["image_contract_details"]["exception_type"] == "RuntimeError"
    assert result["image_contract_details"]["first_cause"] == "durable_intent_output_dir_unavailable"
    assert store.get_platform_dispatch(result["dispatch_id"])["status"] == "DEFINITE_NO_WRITE"
    assert store.get_outbox_message(message["message_id"])["status"] == "DEFINITE_NO_WRITE"
    assert runtime.publish_calls == []


@pytest.mark.parametrize("error_type", [RuntimeError, AttributeError, LookupError])
def test_unexpected_image_exception_keeps_its_first_cause_across_restart(tmp_path, monkeypatch, error_type):
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

    store, runtime, coordinator, message = message_with(tmp_path / "run", [])
    intent = json.loads(message["payload"])

    def fail_image_check(*args):
        raise error_type("first image-check cause")

    monkeypatch.setattr(contract, "validate_write", fail_image_check)
    coordinator._readiness = lambda *a: pytest.fail("an image-check failure reached a destination probe")
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == "DEFINITE_NO_WRITE"
    assert result["reason_code"] == "PUBLICATION_IMAGE_CONTRACT_INVALID"
    assert result["image_contract_details"] == {
        "exception_type": error_type.__name__, "first_cause": "first image-check cause"}
    coordinator.store = ContentOpsDurableStore(store.db_path, auto_migrate=False)
    records = coordinator.store.get_reconciliations_for_work_item(intent["work_item_id"])
    record = next(r for r in records if r["reconciliation_id"] == coordinator._ids(
        intent["work_item_id"], intent["plan_hash"], "substack")["reconciliation_id"])
    reason, details = record["status"].split(": ", 1)
    assert reason == "PUBLICATION_IMAGE_CONTRACT_INVALID"
    assert json.loads(details) == result["image_contract_details"]
    assert coordinator.store.get_platform_dispatch(result["dispatch_id"])["status"] == "DEFINITE_NO_WRITE"
    assert coordinator.store.get_outbox_message(message["message_id"])["status"] == "DEFINITE_NO_WRITE"
    monkeypatch.setattr(contract, "validate_write", lambda *a: pytest.fail("restart repeated the image check"))
    again = coordinator._dispatch_message(message, canonical_url=None)
    assert again["reconciliation_status"] == record["status"]
    assert runtime.publish_calls == []


# 3. A market post with a chart from another market ----------------------------

def _retarget(message, market):
    intent = json.loads(message["payload"])
    path = Path(intent["output_dir"]) / "run_context_v1.json"
    context = json.loads(path.read_bytes())
    context["article"]["market_asset"] = market
    path.write_text(json.dumps(context), encoding="utf-8")


def test_gold_post_with_an_sp500_chart_is_refused_at_the_coordinator(tmp_path):
    asset = chart(tmp_path)                       # a valid US500 (SP:SPX) chart
    _, runtime, coordinator, message = message_with(tmp_path / "run", [asset])
    _retarget(message, "XAUUSD")
    coordinator._readiness = lambda *a: pytest.fail("a wrong-market chart reached a destination probe")
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == "DEFINITE_NO_WRITE"
    assert result["reason_code"] == "TRADINGVIEW_MARKET_SYMBOL_MISMATCH"
    assert runtime.publish_calls == []


def test_folderless_gold_post_with_an_sp500_chart_is_refused(tmp_path):
    intent = {"output_dir": None, "article": {"market_asset": "XAUUSD"}, "media_assets": [chart(tmp_path)]}
    with pytest.raises(contract.ImageContractError, match="TRADINGVIEW_MARKET_SYMBOL_MISMATCH"):
        contract.validate_write(folderless_coordinator(), intent, "substack")


# 4. The same class of defect CC-548 fixed: a read relative to the current folder

@pytest.mark.parametrize("folder_fields", [{}, {"output_dir": None}, {"output_dir": ""}])
@pytest.mark.parametrize("article_fallback", [False, True])
def test_folderless_market_post_without_chart_ignores_a_capture_state_in_the_current_folder(
        tmp_path, monkeypatch, folder_fields, article_fallback):
    """Stray capture state cannot grant text fallback (decisions 82 and 124)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tradingview_capture_v1.json").write_text(json.dumps({
        "status": "TEXT_ONLY", "attempts": 2, "market": "XAUUSD", "key": "stray",
        "cause": "stray state from another run", "started_at_utc": "2026-11-14T11:00:00+00:00"}),
        encoding="utf-8")
    article = {"market_asset": "XAUUSD"}
    if article_fallback:
        article.update(publication_image_contract=contract.POLICY, tradingview_text_fallback=True,
                       tradingview_capture_state_path=str(tmp_path / "tradingview_capture_v1.json"),
                       tradingview_capture_key="stray")
    original_read = Path.read_bytes

    def no_capture_read(path):
        if path.name == "tradingview_capture_v1.json":
            pytest.fail("a folderless post read capture state from the current folder")
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", no_capture_read)
    intent = {**folder_fields, "article": article, "media_assets": []}
    with pytest.raises(contract.ImageContractError, match="TRADINGVIEW_FIRST_IMAGE_REQUIRED"):
        contract.validate_write(folderless_coordinator(), intent, "substack")


# 5. Saturday's shape: two missed days, the held article rides once ------------

def test_saturday_freezes_one_digest_with_the_held_article_and_both_missed_days(tmp_path):
    """The live store holds only the refused 12 Nov packet (13 Nov froze none).
    Saturday's digest takes the held article plus everything published after
    the 12 Nov cut-off, each once."""
    from test_substack_daily_digest_v1 import row
    from live_contentops.published_content_v1 import append_record
    store, feed, refused, _ = held_digest(tmp_path, with_feed=True)
    for identity, published in (("fri", "2026-11-13T03:00:00Z"), ("sat", "2026-11-14T01:00:00Z"),
                                ("late", "2026-11-14T12:30:00Z")):
        append_record(feed, row(identity, published))
    result = digest.prepare_daily_digest(store, feed, now=clock("2026-11-14T12:15:00Z"))
    packet = result["packet"]
    assert packet["digest_id"] == "cc143-digest-2026-11-14"
    assert [a["content_id"] for a in packet["articles"]] == ["substack:224293572", "fri", "sat"]
    body = packet["native_payload"]["body_markdown"]
    assert body.count(refused["articles"][0]["url"]) == 1


def test_saturday_digest_carries_the_held_article_once_after_a_missed_friday(tmp_path):
    store, feed, refused, _ = held_digest(tmp_path, with_feed=True)
    friday = digest.prepare_daily_digest(store, feed, now=clock("2026-11-13T12:15:00Z"))
    # Friday's packet was frozen but (as on the live code) never sent. Saturday
    # must resume Friday's still-pending packet, not freeze a second copy.
    saturday = digest.prepare_daily_digest(store, feed, now=clock("2026-11-14T12:15:00Z"))
    assert saturday["packet"]["digest_id"] == friday["packet"]["digest_id"]
    ids = [a["content_id"] for p in digest.packets(store) for a in p["articles"]
           if p["digest_id"] != refused["digest_id"]]
    assert ids.count("substack:224293572") == 1
