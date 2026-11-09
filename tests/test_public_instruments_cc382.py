"""Decision 107 at native requests, article validation, compiler and live write boundary."""
from copy import deepcopy
import json

import pytest

from live_contentops.public_instruments_v1 import (
    GUIDANCE, INSTRUMENTS, POLICY, validate_article, validate_payload,
)
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DesktopInputRequired
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    _reader_safe_native_article, _validate_article_against_source_pack, SimpleGeminiNewsroomError,
)


def article():
    return {"title": "Six markets before the next release", "public_instrument_policy": POLICY,
        "substack_body_markdown": "\n".join([
            "Spot gold: GC futures and GLD ETF are public expressions.",
            "S&P 500: ES futures and SPY ETF.", "WTI: CL futures and USO ETF.",
            "EUR/USD spot: 6E futures and FXE ETF.", "USD/JPY spot: 6J futures and FXY ETF express the yen.",
            "Bitcoin spot: BTC futures and IBIT ETF."]),
        "market_asset": "XAUUSD"}


@pytest.mark.parametrize("market", INSTRUMENTS)
def test_each_covered_market_requires_its_own_instrument(market):
    copy = article()
    name, symbols = INSTRUMENTS[market]
    copy["substack_body_markdown"] = name + ": the market reaction."
    copy["market_asset"] = market
    with pytest.raises(ValueError, match="PUBLIC_FUTURES_OR_ETF_REQUIRED:" + market):
        validate_article(copy)
    copy["substack_body_markdown"] += " Public instrument: " + symbols[0] + " futures."
    validate_article(copy)


@pytest.mark.parametrize("bad", ["CFD", "CFDs", "US500", "USOIL", "XAUUSD", "BTCUSD", "xauusd"])
def test_package_refuses_broker_names_but_preserves_internal_metadata(bad):
    copy = article()
    copy["source_bindings"] = {"support_excerpt": "US500 XAUUSD BTCUSD"}
    validate_article(copy)
    copy["meta_description"] = "Market reaction in " + bad
    with pytest.raises(ValueError, match="PUBLIC_INSTRUMENT_NAME_FORBIDDEN"):
        validate_article(copy)
    with pytest.raises(SimpleGeminiNewsroomError, match="deterministic_article_validation_failed"):
        _validate_article_against_source_pack({"article": copy}, [])


def test_policy_does_not_convert_or_replace_numbers_or_frozen_history():
    copy = article()
    copy["substack_body_markdown"] += " Spot gold was $2,711.30 (source); no GLD flow is supplied."
    before = deepcopy(copy)
    validate_article(copy)
    assert copy == before
    validate_article({"title": "Historical US500 CFD article"})
    validate_article({"title": "How CFDs differ from futures", "public_instrument_policy": POLICY,
                      "substack_body_markdown": "CFDs are contracts for difference."})


def test_instrument_in_seo_or_social_does_not_replace_article_coverage():
    copy = article()
    copy.update(substack_body_markdown="Spot gold reacts to rates.", meta_description="GC futures and GLD ETF",
                social_hook="GC futures and GLD ETF")
    with pytest.raises(ValueError, match="PUBLIC_FUTURES_OR_ETF_REQUIRED:XAUUSD"):
        validate_article(copy)


def test_spot_bitcoin_ticker_alone_does_not_claim_a_futures_instrument():
    copy = {"title": "Bitcoin review", "public_instrument_policy": POLICY,
            "substack_body_markdown": "BTC spot follows the dollar."}
    with pytest.raises(ValueError, match="PUBLIC_FUTURES_OR_ETF_REQUIRED:BTCUSD"):
        validate_article(copy)
    copy["substack_body_markdown"] += " IBIT is an ETF expression."
    validate_article(copy)


def test_sp_global_publisher_name_does_not_mean_the_sp500_market():
    copy = {"title": "Gold and business surveys", "public_instrument_policy": POLICY,
            "substack_body_markdown": "Gold: GC futures. A headline survey figure from S&P Global."}
    validate_article(copy)


@pytest.mark.parametrize("market", INSTRUMENTS)
def test_fresh_chart_captions_use_public_names_and_keep_exact_feed_and_image(tmp_path, market):
    from hashlib import sha256
    from pathlib import Path
    from live_contentops.tradingview_snapshot_v1 import SYMBOLS, NAMES, chart_url, snapshot_asset
    fixture = Path(__file__).parent / "fixtures/cc314/SPX_2026-11-09_17-50-41.png"
    digest = sha256(fixture.read_bytes()).hexdigest()
    snapshot = {"path": str(fixture), "sha256": digest, "tv_symbol": SYMBOLS[market], "interval": "240",
        "interval_label": "4h", "chart_url": chart_url(SYMBOLS[market], "240"),
        "captured_at_utc": "2026-11-09T18:00:00Z"}
    # The same binary fixture tests caption formatting, not the six charts' pixels.
    asset = snapshot_asset(market, "Market review", snapshot, tmp_path)
    validate_payload(article(), asset)
    assert NAMES[market] in asset["caption"]
    assert asset["tradingview_snapshot"]["tv_symbol"] == SYMBOLS[market]
    assert asset["tradingview_snapshot"]["sha256"] == digest
    assert sha256(fixture.read_bytes()).hexdigest() == digest


def test_rendered_article_retains_the_request_bound_policy():
    copy = article()
    rendered = _reader_safe_native_article(copy, article_mode="STANDARD_NEWS_ANALYSIS")
    assert rendered["public_instrument_policy"] == POLICY
    validate_article(rendered)


def test_native_request_and_return_use_policy_without_rewriting_saved_return(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "native.sqlite3")
    work = "cc-opportunity-" + sha256_of("cc382-article")
    store.create_work_item(story_id=work, work_item_id=work, title="test", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id="cc382-article", output_dir=tmp_path)
    args = dict(logical_invocation_id="write", prompt="Write the sourced article.",
                governed_input={}, validator=lambda _: (True, None, None, None))
    with pytest.raises(DesktopInputRequired) as pending:
        turn(**args)
    request = pending.value.request
    assert GUIDANCE in request["prompt"]
    output = {"article": article()}
    output["article"].pop("public_instrument_policy")
    response = {"request_sha256": request["request_sha256"], "output": output,
        "invocation_observation": {"model": "gpt-6.1-sol", "reasoning_effort": "max",
            "surface": "CODEX_EXEC", "invocation_id": "fixture-writer", "observation_source": "test fixture"}}
    turn._put("write", "response", response)
    result, _ = turn(**args)
    assert result["article"]["public_instrument_policy"] == POLICY
    assert turn._get("write", "response") == response
    assert turn.frozen_request("write")["request_sha256"] == request["request_sha256"]


def test_preexisting_frozen_request_does_not_adopt_new_guidance(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "native.sqlite3")
    work = "cc-opportunity-" + sha256_of("old-write")
    store.create_work_item(story_id=work, work_item_id=work, title="test", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id="old-write", output_dir=tmp_path)
    args = dict(logical_invocation_id="write", prompt="Historical exact request.",
                governed_input={}, validator=lambda _: (True, None, None, None))
    with pytest.raises(DesktopInputRequired) as pending:
        turn(**args)
    request = {k: v for k, v in pending.value.request.items() if k not in {"request_path", "request_sha256"}}
    request["prompt"] = request["prompt"].replace("\n" + GUIDANCE, "")
    request["request_sha256"] = sha256_of(request)
    # Simulate an already issued pre-decision request in its original outbox.
    key = turn._key("write", "request")
    with store.get_connection() as conn:
        conn.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?", (json.dumps(request), key))
    with pytest.raises(DesktopInputRequired) as resumed:
        turn(**args)
    assert GUIDANCE not in resumed.value.request["prompt"]
    assert resumed.value.request["request_sha256"] == request["request_sha256"]


@pytest.mark.parametrize("destination", ["substack", "telegram", "discord", "x", "linkedin", "facebook_page",
                                         "instagram_business", "threads", "youtube"])
def test_live_coordinator_rejects_bad_copy_before_transport(tmp_path, destination):
    from test_article_publication_quality_cc333 import publication
    store, transport, coordinator, message, _, _, _ = publication(tmp_path, destination=destination)
    intent = json.loads(message["payload"])
    context_path = tmp_path / "article" / "run_context_v1.json"
    context = json.loads(context_path.read_bytes())
    context["article"].update(public_instrument_policy=POLICY, title="Gold: GC futures and GLD ETF")
    if destination == "substack":
        context["article"]["substack_body_markdown"] += "\nUS500 reaction."
    else:
        intent["native_payload"] = {"posts": [{"text": "A CFD reaction"}]}
    context_path.write_text(json.dumps(context), encoding="utf-8")
    if destination != "substack":
        # Reach the destination-copy check with the existing source-bound scenarios.
        intent["native_payload"]["posts"][0]["text"] += "\n" + "\n".join(context["article"]["social_scenarios"].values())
    result = coordinator._dispatch_message({**message, "payload": json.dumps(intent)},
        canonical_url=None if destination == "substack" else "https://capitalchronicle.substack.com/p/test")
    assert "PUBLIC_INSTRUMENT_NAME_FORBIDDEN" in str(result)
    assert not transport.publish_calls


def test_eight_destination_compiler_preserves_public_names():
    from test_article_publication_quality_cc333 import scenario_article
    from live_contentops.v1_simple_gemini_newsroom_v1 import _native_preview_bundle
    copy, _ = scenario_article()
    copy.update(article())
    copy.update(social_mechanism_summary="Gold: GC futures and GLD ETF express the market.",
                social_policy_summary="S&P 500: ES futures and SPY ETF.",
                social_cross_asset_summary="EUR/USD: 6E futures and FXE ETF.")
    bundle, _ = _native_preview_bundle(article=copy, article_mode="STANDARD_NEWS_ANALYSIS",
                                     article_identity="a" * 64, media_asset_ids=["image-1"])
    assert len(bundle["packages"]) == 8
    for payload in bundle["packages"].values():
        validate_payload(copy, payload)


@pytest.mark.parametrize("destination", ["substack", "telegram"])
def test_valid_new_article_reaches_existing_transport_with_source_bound_scenarios(tmp_path, destination):
    from hashlib import sha256
    from test_article_publication_quality_cc333 import publication
    _, transport, coordinator, message, _, _, _ = publication(tmp_path, destination=destination)
    context_path = tmp_path / "article" / "run_context_v1.json"
    context = json.loads(context_path.read_bytes())
    # Relabel only the synthetic fixture's display strings, leaving raw market keys exact.
    def display(text):
        for market, (name, symbols) in INSTRUMENTS.items():
            text = text.replace(market, name + " (" + symbols[0] + " futures)")
        return text
    copy = context["article"]
    copy["public_instrument_policy"] = POLICY
    copy["substack_body_markdown"] = display(copy["substack_body_markdown"])
    for scenario in copy["scenario_analysis"]:
        scenario["market_moves"] = {key: display(value) for key, value in scenario["market_moves"].items()}
        for binding in scenario["source_bindings"].values():
            binding["support_excerpt"] = display(binding["support_excerpt"])
    for doc in context["source_documents"]:
        doc["canonical_content_text"] = display(doc["canonical_content_text"])
        doc["canonical_content_sha256"] = sha256(doc["canonical_content_text"].encode()).hexdigest()
    context_path.write_text(json.dumps(context), encoding="utf-8")
    intent = json.loads(message["payload"])
    if destination != "substack":
        intent["native_payload"] = {"text": "Gold: GC futures and GLD ETF.\n" +
            "\n".join(copy["social_scenarios"].values()), "media_asset_ids": ["image-1"]}
    outcome = coordinator._dispatch_message({**message, "payload": json.dumps(intent)},
        canonical_url=None if destination == "substack" else "https://capitalchronicle.substack.com/p/test")
    assert outcome["status"] == "DISPATCH_CONFIRMED"
    assert transport.publish_calls == [destination]
