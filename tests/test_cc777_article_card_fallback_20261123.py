"""CC-777, decision 82 on ordinary articles (Builder H, 23 Nov 2026).

An article whose own bounded TradingView capture fails goes out led by its own data card (the article's facts, never
a title alone, never a target), bound to that capture and its cause; never text only. Temporary stores and files only:
no network, no browser, no capture, no public write.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from PIL import Image
import pytest

from live_contentops import publication_image_contract_v1 as contract
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops.article_publication_quality_v1 import before_article_write, image_register
from live_contentops.published_images_v1 import ImagePolicyError
from test_article_publication_quality_cc333 import publication
from test_market_wrap_cc689 import cash, pack  # noqa: F401  (pytest fixtures)

NOW = datetime(2026, 11, 12, 16, tzinfo=timezone.utc)
CAUSE = "TRADINGVIEW_SNAPSHOT_TIMEOUT"


def data_card(folder, *, facts=("The S&P 500 closed 0.8% lower on Thursday.",), kind=None, asset_id="post-facts-1"):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (asset_id + ".png")
    Image.new("RGB", (1080, 1350), (16, 29, 45)).save(path)
    packet = {"policy": "CC144_EVERY_POST_VISUAL_V1", "title": "Stocks slip", "dated_line": "Capital Chronicle, 12 Nov",
              "facts": [{"text": text, "document_id": "main-report"} for text in facts]}
    return {"asset_id": asset_id, "path": str(path), "sha256": sha256(path.read_bytes()).hexdigest(),
            "width": 1080, "height": 1350, "modality": "source_bound_data_card", "media_role": "post_key_facts",
            "caption": "Key facts from the article.", "alt_text": " ".join(facts), "data_card_packet": packet,
            **({"card_kind": kind} if kind else {})}


def failing(calls):
    def capture(market, interval, folder, **kwargs):
        calls.append(market)
        raise tv.SnapshotError(CAUSE)
    return capture


def card_article(tmp_path, monkeypatch, cards=None):
    """The real cc333 article run, prepared through the real capture owner with a capture that always fails."""
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    store, runtime, coordinator, message, _, article, documents = publication(tmp_path, assets=False)
    coordinator._clock = lambda: NOW
    intent = json.loads(message["payload"])
    folder = Path(intent["output_dir"])
    calls = []
    cards = [data_card(folder / "media_assets")] if cards is None else cards
    prepared, assets = tv.prepare_contract_article({**article, "market_asset": "US500"}, cards, output_dir=folder,
                                                   snapshot=failing(calls))
    assert len(calls) == tv.PLAN_ATTEMPTS
    (folder / "run_context_v1.json").write_text(json.dumps({"article": prepared, "media": {"assets": assets},
                                                            "source_documents": documents}), encoding="utf-8")
    return coordinator, intent, prepared, assets


def test_article_whose_capture_fails_leads_with_its_own_card_and_passes_the_write_checks(tmp_path, monkeypatch):
    coordinator, intent, article, assets = card_article(tmp_path, monkeypatch)
    card, = assets
    assert card["article_chart_fallback"] == {"key": article["tradingview_capture_key"], "market": "US500",
                                              "ratio": "16:9", "cause": CAUSE}
    assert article["tradingview_card_fallback"]["cause"] == CAUSE and "tradingview_text_fallback" not in article
    assert article["lead_image_asset_id"] == card["asset_id"]
    assert set(map(tuple, article["native_destination_media"].values())) == {(card["asset_id"],)}
    outcome = json.loads((tmp_path / "outcomes.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert (outcome["status"], outcome["cause"]) == ("ARTICLE_FACT_CARD", CAUSE)

    checked = contract.validate_write(coordinator, intent, "substack")
    assert checked["first_image_type"] == contract.ARTICLE_CARD_FALLBACK
    assert checked["article_chart_fallback_causes"] == [CAUSE]
    assert before_article_write(coordinator, intent, "substack")["lead_asset_id"] == card["asset_id"]
    # The social copy names no TradingView chart, because none is shown; the card lead passes the attribution check.
    intent.update(native_payload={"text": "\n".join(article["social_scenarios"].values()),
                                  "media_asset_ids": [card["asset_id"]]},
                  canonical_url="https://capitalchronicle.substack.com/p/fixture-article-1")
    before_article_write(coordinator, intent, "telegram")
    record = image_register(coordinator).records()[-1]
    assert record["images"][0]["image_type"] == contract.ARTICLE_CARD_FALLBACK


def test_a_tradingview_lead_still_owes_its_chart_credit(tmp_path, monkeypatch):
    from test_publication_image_contract_cc463 import chart

    coordinator, intent, article, _ = card_article(tmp_path, monkeypatch)
    folder = Path(intent["output_dir"])
    context = json.loads((folder / "run_context_v1.json").read_bytes())
    lead = chart(tmp_path / "chart")
    context["article"]["lead_image_asset_id"] = lead["asset_id"]
    context["media"]["assets"] = [lead]
    (folder / "run_context_v1.json").write_text(json.dumps(context), encoding="utf-8")
    intent.update(native_payload={"text": "\n".join(article["social_scenarios"].values())},
                  canonical_url="https://capitalchronicle.substack.com/p/fixture-article-1")
    with pytest.raises(ImagePolicyError, match="TRADINGVIEW_ATTRIBUTION_REQUIRED"):
        before_article_write(coordinator, intent, "telegram")


@pytest.mark.parametrize(("change", "cause"), [
    ("cause", "ARTICLE_CHART_FALLBACK_BINDING_INVALID"),
    ("record", "ARTICLE_CHART_FALLBACK_BINDING_INVALID"),
    ("window", "ARTICLE_CHART_FALLBACK_BINDING_INVALID"),
    ("bytes", "ARTICLE_CHART_FALLBACK_BYTES_CHANGED"),
])
def test_the_card_is_refused_when_its_binding_or_bytes_change(tmp_path, monkeypatch, change, cause):
    coordinator, intent, article, assets = card_article(tmp_path, monkeypatch)
    folder = Path(intent["output_dir"])
    context = json.loads((folder / "run_context_v1.json").read_bytes())
    card = context["media"]["assets"][0]
    if change == "cause":
        card["article_chart_fallback"]["cause"] = "OTHER"
    elif change == "record":
        context["article"]["tradingview_card_fallback"]["asset_id"] = "another-card"
    elif change == "window":
        # The capture had not yet used its attempts or its five-minute window.
        state_path = Path(article["tradingview_capture_state_path"])
        state = json.loads(state_path.read_bytes())
        state.update(attempts=1, started_at_utc=NOW.isoformat())
        state_path.write_text(json.dumps(state), encoding="utf-8")
    else:
        Image.new("RGB", (1080, 1350), "red").save(card["path"])
    (folder / "run_context_v1.json").write_text(json.dumps(context), encoding="utf-8")
    with pytest.raises(contract.ImageContractError, match=cause):
        contract.validate_write(coordinator, intent, "substack")


@pytest.mark.parametrize(("cards", "refused"), [
    ([], {"": "ARTICLE_CHART_FALLBACK_NO_CARD"}),
    ("title", {"post-title-1": "ARTICLE_CHART_FALLBACK_TITLE_ONLY"}),
    ("target", {"post-facts-1": "ARTICLE_CHART_FALLBACK_TARGET_REFUSED"}),
])
def test_without_an_own_fact_card_the_article_stays_text_only_and_records_why(tmp_path, monkeypatch, cards, refused):
    if cards == "title":
        cards = [{**data_card(tmp_path / "cards", facts=(), asset_id="post-title-1"), "card_kind": "TITLE_ONLY"}]
    elif cards == "target":
        cards = [data_card(tmp_path / "cards", facts=("Our target for the S&P 500 is 7,800.",))]
    coordinator, intent, article, assets = card_article(tmp_path, monkeypatch, cards)
    assert assets == [] and article["tradingview_text_fallback"] is True
    assert article["tradingview_card_fallback_refused"] == refused
    assert contract.validate_write(coordinator, intent, "substack")["text_fallback"] is True


def test_a_stored_text_only_article_keeps_its_bytes_and_its_text_fallback(tmp_path, monkeypatch):
    # A run prepared before CC-777 has no card; nothing rewrites it and its bounded text fallback still holds.
    coordinator, intent, article, _ = card_article(tmp_path, monkeypatch, [])
    folder = Path(intent["output_dir"])
    stored = {name: (folder / name).read_bytes() for name in ("run_context_v1.json", "article_manifest_v1.json")}
    state = Path(article["tradingview_capture_state_path"]).read_bytes()
    assert contract.validate_write(coordinator, intent, "substack")["text_fallback"] is True
    before_article_write(coordinator, intent, "substack")
    assert {name: (folder / name).read_bytes() for name in stored} == stored
    assert Path(article["tradingview_capture_state_path"]).read_bytes() == state


def test_the_wrap_leads_with_its_own_market_moves_card_when_its_capture_fails(tmp_path, monkeypatch, pack):
    from live_contentops import market_wrap_editorial_v1 as editorial, market_wrap_job_v1 as job

    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    calls = []
    monkeypatch.setattr(tv, "capture", failing(calls))
    markets = pack["markets"]
    article = {"title": "Gold slips before GDP", "subtitle": "Pre-US wrap", "market_asset": "XAUUSD",
               "substack_body_markdown": "Gold fell 0.25 normal days."}
    prepared, assets = job.prepare_media(pack, article, markets, tmp_path)
    card, = assets
    assert calls and card["asset_id"] == pack["slot"]["id"] + "-moves"
    assert card["article_chart_fallback"]["cause"] == CAUSE
    assert prepared["lead_image_asset_id"] == card["asset_id"] and "tradingview_text_fallback" not in prepared
    assert Path(card["path"]).resolve().is_relative_to((tmp_path / "media").resolve())
    assert editorial.derivative_payload(prepared, card, "https://capitalchronicle.substack.com/p/w", "x")[
        "media_asset_ids"] == [card["asset_id"]]


@pytest.mark.parametrize(("media", "status", "cause"), [
    (True, "FACT_CARD_FALLBACK", "MARKET_TRADINGVIEW_FACT_CARD_FALLBACK"),
    (False, "FAIL", "MARKET_TRADINGVIEW_CHART_MISSING"),
])
def test_decision_82_check_counts_an_article_card_with_its_cause_and_still_fails_text_only(tmp_path, media, status,
                                                                                          cause):
    from test_prerelaunch_decision_checks_20261123 import NOTICES, by_decision, checks, posted

    audit = checks(tmp_path)
    card = {"asset_id": "post-facts-1", "modality": "source_bound_data_card",
            "article_chart_fallback": {"key": "k", "market": "US500", "ratio": "16:9", "cause": CAUSE}}
    posted(audit, "article-1", "telegram", text="Stocks slip.\n" + NOTICES, source={}, object_id="300",
           native={"media_asset_ids": [card["asset_id"]] if media else []},
           intent={"market_asset": "US500", "media_assets": [card] if media else []},
           readback_fields={"image_delivery": "IMAGE_ATTACHED" if media else "TEXT_ONLY"})
    result = audit.finish({}, {})
    assert ("telegram", status, cause) in by_decision(result, "82")
    summary = next(item for item in result["checks"] if item["decision"] == "82")
    if media:
        row = next(row for row in result["issues"] if row["decision"] == "82")
        assert row["chart_causes"] == [CAUSE]
        assert summary["failed"] == 0 and summary["fact_card_fallback"] == 1
    else:
        assert summary["failed"] == 1


def test_the_daily_image_audit_allows_a_card_post_but_never_counts_it_as_a_chart(tmp_path):
    from test_publication_image_audit_cc463 import NOW as AUDIT_NOW, audit, register
    from datetime import timedelta

    path = register(tmp_path, kind=contract.ARTICLE_CARD_FALLBACK)
    later = AUDIT_NOW + timedelta(days=1)
    result = audit(path, "2026-11-12", now=later)
    # Like a day of only text fallbacks: allowed, no violation, and no chart observed.
    assert result["status"] == "NO_MARKET_CHART_OBSERVED" and result["violations"] == []
    assert result["fact_card_fallback_posts"] == 1 and not result["all_market_posts_have_chart"]
    row = json.loads(path.read_text(encoding="utf-8"))
    row.update(record_id="chart", piece_id="chart", images=[{**row["images"][0], "image_type": "TRADINGVIEW_MARKET_CHART"}])
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")
    assert audit(path, "2026-11-12", now=later)["status"] == "FACT_CARD_FALLBACK_OBSERVED"
    assert audit(register(tmp_path, kind="DRAWN_CARD"), "2026-11-12", now=AUDIT_NOW)["status"] == "FAIL"
