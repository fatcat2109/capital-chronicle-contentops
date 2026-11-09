"""Synthetic guard cases, never drafts or market evidence."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import socket

import pytest

from live_contentops.event_article_guard_v1 import (
    ARTICLE_TYPES, DISCLAIMER, EVIDENCE_SCHEMA, REACTION_ASSETS, SCHEMA, SECTIONS,
    PublicOutputError, check_public_event_article, main,
)


def packet(kind="EVENT_PREVIEW"):
    article = {
        "schema_version": SCHEMA, "article_type": kind, "event_id": "synthetic-event",
        "event_time_utc": "2026-11-06T13:30:00Z",
        "cutoff_utc": "2026-11-06T12:00:00Z",
        "written_at_utc": "2026-11-06T12:05:00Z",
        "copy": {key: "Synthetic qualitative test copy." for key in SECTIONS[kind]},
        "numeric_bindings": [],
    }
    if kind == "EVENT_REVIEW":
        article.update(cutoff_utc="2026-11-06T15:00:00Z", written_at_utc="2026-11-06T15:05:00Z")
    article["copy"]["market_reactions"] = {
        asset: "The response depends on the broader mix of evidence."
        for asset in REACTION_ASSETS
    }
    article["copy"]["disclaimer"] = DISCLAIMER
    evidence = {"schema_version": EVIDENCE_SCHEMA, "event_id": "synthetic-event",
                "facts": {}, "private_text": ["PRIVATE_SENTINEL"]}
    return article, evidence


def bind(article, evidence, text="50%", *, path="copy.scenarios", ref="synthetic-public-field"):
    key = path.removeprefix("copy.")
    article["copy"][key] = "Source-bound test figure: " + text + "."
    start = article["copy"][key].index(text)
    article["numeric_bindings"].append({"copy_path": path, "start": start,
        "end": start + len(text), "evidence_ref": ref})
    evidence["facts"][ref] = {
        "display": text, "source_ref": "https://source.invalid/synthetic-fixture",
        "source_sha256": "a" * 64, "known_at_utc": "2026-11-06T11:00:00Z",
        "rights_class": "SYNTHETIC_PUBLIC_TEST_ONLY", "public_use_allowed": True,
        "rights_evidence_ref": "synthetic-rights-fixture", "use_label": "PUBLIC",
        "kind": "PRE_EVENT_FORECAST",
    }
    return evidence["facts"][ref]


def refused(article, evidence, cause=None):
    with pytest.raises(PublicOutputError) as failure:
        check_public_event_article(article, evidence=evidence)
    if cause:
        assert failure.value.cause == cause
    return failure.value


@pytest.mark.parametrize("kind", ARTICLE_TYPES)
def test_both_authored_templates_pass_without_granting_publication(kind, monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", lambda *a, **k: pytest.fail("network attempted"))
    article, evidence = packet(kind)
    first = check_public_event_article(article, evidence=evidence)
    assert first == check_public_event_article(article, evidence=evidence)
    assert first["status"] == "PASS"
    assert not first["publication_authority"]
    assert not first["jim_approval_required"]
    assert first["standing_approval"] == "JIM_DECISION_36"
    assert first["final_native_render_review_required"]
    assert first["checked_surfaces"] == len(SECTIONS[kind]) + len(REACTION_ASSETS) - 1


@pytest.mark.parametrize("kind", ARTICLE_TYPES)
def test_event_resolution_sections_are_checked_as_public_copy(kind):
    from live_contentops.event_article_guard_v1 import EVENT_FRAME_SECTIONS
    article, evidence = packet(kind)
    for key in EVENT_FRAME_SECTIONS[kind]:
        article["copy"][key] = "The dated observation remains conditional."
    assert check_public_event_article(article, evidence=evidence)["status"] == "PASS"
    key = next(iter(EVENT_FRAME_SECTIONS[kind]))
    article["copy"][key] = "Buy gold."
    refused(article, evidence, "PRIVATE_OR_EXECUTION_COPY_FORBIDDEN")


def test_incomplete_frame_is_not_silently_accepted():
    article, evidence = packet()
    article["copy"]["pre_event_range"] = "Source-owned range."
    refused(article, evidence, "EVENT_SECTIONS_REQUIRED")


@pytest.mark.parametrize("key", [
    "entry", "entryPrice", "entries", "stop_loss", "stopLoss", "sl", "take_profit",
    "target", "price-target", "targets", "size", "position_size", "lots", "volume",
    "account", "account_id", "DEMO", "demoAccount", "mt5_login", "positions",
    "balance", "equity", "pnl", "fills", "order_ticket", "DEMO_results",
])
def test_private_structured_fields_are_refused_even_when_nested(key):
    article, evidence = packet()
    article["hidden"] = {"nested": [{key: "PRIVATE_SENTINEL"}]}
    failure = refused(article, evidence, "PRIVATE_FIELD_FORBIDDEN")
    assert "PRIVATE_SENTINEL" not in str(failure)


@pytest.mark.parametrize("text", [
    "Buy gold after the release.", "Sell the dollar.", "Go long gold.",
    "We recommend buying gold.", "You should sell gold.", "Consider buying gold.",
    "Traders could short bonds.", "We hold gold.", "Entry: 2412.35.", "Stop at 2400.",
    "Target 2500.", "Price target is 2500.", "Position sizing is conservative.",
    "Use 0.05 lots.", "Our positions performed well.", "Portfolio results improved.",
    "DEMO account details are omitted.", "The MT5 account balance is unavailable.",
    "The result was 0.8R.", "Our P&L improved.", "**B**uy gold.", "B\u200buy gold.",
])
def test_execution_or_account_prose_is_refused_on_every_public_surface(text):
    article, evidence = packet()
    article["copy"]["market_reactions"]["gold"] = text
    refused(article, evidence, "PRIVATE_OR_EXECUTION_COPY_FORBIDDEN")


@pytest.mark.parametrize("text", [
    "The sell-off may reflect competing influences.",
    "Buy-side expectations remain qualitative.",
    "Sell-off concerns remain qualitative.",
    "Long-term policy consequences remain uncertain.",
    "The inflation target remains part of the policy debate.",
    "Lower yields could support gold, subject to dollar moves.",
])
def test_general_market_analysis_is_not_treated_as_a_trading_call(text):
    article, evidence = packet()
    article["copy"]["context"] = text
    assert check_public_event_article(article, evidence=evidence)["status"] == "PASS"


@pytest.mark.parametrize("text", ["2412.35", "2,412.35", "2412.4", "2412.3", "50%", "0.8", "987654321", "٢٤١٢.٣٥", "id987654321"])
@pytest.mark.parametrize("section", ["headline", "dek", "probability_basis"])
def test_private_reformatted_or_unsupported_numbers_cannot_enter_any_copy(text, section):
    article, evidence = packet()
    article["copy"][section] = "An unsupported figure is " + text + "."
    refused(article, evidence, "UNBOUND_PUBLIC_NUMBER")


def test_pinned_public_probability_keeps_its_exact_value_and_rights():
    article, evidence = packet()
    bind(article, evidence)
    before = deepcopy((article, evidence))
    assert check_public_event_article(article, evidence=evidence)["numeric_bindings"] == 1
    assert (article, evidence) == before


@pytest.mark.parametrize("change", [
    {"rights_class": None}, {"rights_class": ""}, {"rights_class": "UNKNOWN"},
    {"rights_class": "NOT_GRANTED"}, {"rights_class": "LICENSE_REQUIRED"},
    {"rights_class": "MARKET_CONSENSUS_PRIVATE_ONLY"}, {"rights_class": "GEX_PRIVATE_ONLY"},
    {"rights_class": "DEMO_PRIVATE_ONLY"}, {"public_use_allowed": False},
    {"public_use_allowed": "true"}, {"rights_evidence_ref": ""},
])
def test_a_private_or_unlicensed_number_is_not_waived_by_a_label(change):
    article, evidence = packet()
    bind(article, evidence).update(change)
    refused(article, evidence, "PUBLIC_REUSE_RIGHTS_NOT_ADMITTED")


def test_private_capture_label_is_preserved_when_existing_terms_owner_allows_public_reuse():
    article, evidence = packet()
    fact = bind(article, evidence)
    fact.update(use_label="PRIVATE_RESEARCH_CAPTURE", rights_class="SYNTHETIC_QUOTATION_PERMITTED",
                rights_evidence_ref="CC-104/synthetic-approved-terms-decision")
    assert check_public_event_article(article, evidence=evidence)["status"] == "PASS"
    assert fact["use_label"] == "PRIVATE_RESEARCH_CAPTURE"
    fact["public_use_allowed"] = False
    refused(article, evidence, "PUBLIC_REUSE_RIGHTS_NOT_ADMITTED")


@pytest.mark.parametrize("change", [
    {"source_ref": ""}, {"source_sha256": "not-a-hash"}, {"use_label": ""}, {"display": ""},
])
def test_source_and_original_capture_bindings_are_required(change):
    article, evidence = packet()
    bind(article, evidence).update(change)
    refused(article, evidence, "SOURCE_BINDING_REQUIRED")


@pytest.mark.parametrize("changed", ["51%", "50", "-50%", "50.0%", "50 jobs"])
def test_writer_cannot_change_source_number_sign_precision_or_unit(changed):
    article, evidence = packet()
    bind(article, evidence, changed)["display"] = "50%"
    refused(article, evidence, "SOURCE_DISPLAY_MISMATCH")


def test_grouping_is_a_presentation_change_only():
    article, evidence = packet()
    bind(article, evidence, "2,412.35")["display"] = "2412.35"
    assert check_public_event_article(article, evidence=evidence)["status"] == "PASS"


def test_evidence_cannot_cover_an_unrelated_private_number_in_the_same_sentence():
    article, evidence = packet()
    bind(article, evidence)
    article["copy"]["scenarios"] += " An unrelated private figure was 2412.35."
    refused(article, evidence, "UNBOUND_PUBLIC_NUMBER")


def test_missing_or_forged_inline_rights_do_not_replace_the_owner_context():
    article, evidence = packet()
    bind(article, evidence)
    article["rights_waiver"] = True
    refused(article, evidence, "ARTICLE_SCHEMA_INVALID")
    del article["rights_waiver"]
    evidence["facts"].clear()
    refused(article, evidence, "PUBLIC_EVIDENCE_MISSING")


@pytest.mark.parametrize("kind", ARTICLE_TYPES)
def test_existing_private_text_backstop_covers_all_sections(kind):
    article, evidence = packet(kind)
    article["copy"]["headline"] = "A PRIVATE_SENTINEL fact."
    failure = refused(article, evidence, "PRIVATE_TEXT_IN_PUBLIC_COPY")
    assert failure.location == "copy.headline"
    assert "PRIVATE_SENTINEL" not in str(failure)


@pytest.mark.parametrize("mutation,cause", [
    ({"written_at_utc": "2026-11-06T13:30:00Z"}, "PREVIEW_OR_WRITING_CLOCK_INVALID"),
    ({"cutoff_utc": "2026-11-06T12:06:00Z"}, "PREVIEW_OR_WRITING_CLOCK_INVALID"),
    ({"cutoff_utc": "2026-11-06T12:00:00"}, "UTC_CLOCK_REQUIRED"),
    ({"event_time_utc": "2026-11-06T20:30:00+07:00"}, "UTC_CLOCK_REQUIRED"),
])
def test_preview_cutoff_and_writing_are_pre_event_in_utc(mutation, cause):
    article, evidence = packet()
    article.update(mutation)
    refused(article, evidence, cause)


def test_review_cannot_claim_a_future_event_result():
    article, evidence = packet("EVENT_REVIEW")
    article["cutoff_utc"] = "2026-11-06T12:00:00Z"
    refused(article, evidence, "REVIEW_BEFORE_EVENT")


def test_later_evidence_and_retrofitted_forecast_are_refused():
    article, evidence = packet()
    fact = bind(article, evidence)
    fact["known_at_utc"] = "2026-11-06T12:01:00Z"
    refused(article, evidence, "EVIDENCE_AFTER_CUTOFF")
    article, evidence = packet("EVENT_REVIEW")
    fact = bind(article, evidence, path="copy.forecast_score")
    fact["known_at_utc"] = article["event_time_utc"]
    refused(article, evidence, "FORECAST_NOT_FROZEN_BEFORE_EVENT")
    fact["kind"] = "CC106_SCORE"
    assert check_public_event_article(article, evidence=evidence)["status"] == "PASS"


@pytest.mark.parametrize("key", ["rates", "dollar", "gold", "oil", "indices", "sectors"])
def test_no_required_reaction_market_can_silently_disappear(key):
    article, evidence = packet()
    del article["copy"]["market_reactions"][key]
    refused(article, evidence, "ALL_MARKET_REACTION_ASSETS_REQUIRED")


@pytest.mark.parametrize("kind", ARTICLE_TYPES)
def test_missing_disclaimer_and_missing_required_section_are_refused(kind):
    article, evidence = packet(kind)
    article["copy"]["disclaimer"] = "A generic footer."
    refused(article, evidence, "GENERAL_ANALYSIS_DISCLAIMER_REQUIRED")
    del article["copy"]["disclaimer"]
    refused(article, evidence, "EVENT_SECTIONS_REQUIRED")


@pytest.mark.parametrize("change", [
    {"copy_path": "copy.unknown"}, {"start": -1}, {"start": True}, {"end": 9999},
    {"evidence_ref": []},
])
def test_invalid_numeric_spans_fail_closed(change):
    article, evidence = packet()
    bind(article, evidence)
    article["numeric_bindings"][0].update(change)
    refused(article, evidence, "NUMERIC_BINDING_SPAN_INVALID")


def test_overlapping_binding_cannot_double_count_an_admitted_number():
    article, evidence = packet()
    bind(article, evidence)
    article["numeric_bindings"].append(deepcopy(article["numeric_bindings"][0]))
    refused(article, evidence, "OVERLAPPING_NUMERIC_BINDINGS")


def test_cli_pins_evidence_and_never_echoes_private_content(tmp_path, capsys):
    article, evidence = packet()
    bind(article, evidence)
    ap, ep = tmp_path / "article.json", tmp_path / "evidence.json"
    ap.write_text(json.dumps(article), encoding="utf-8")
    raw = json.dumps(evidence).encode()
    ep.write_bytes(raw)
    args = ["--article", str(ap), "--evidence", str(ep), "--evidence-sha256", sha256(raw).hexdigest()]
    assert main(args) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "PASS" and report["evidence_sha256"] == sha256(raw).hexdigest()
    assert not report["publication_authority"]
    ep.write_bytes(raw + b" ")
    assert main(args) == 2
    assert json.loads(capsys.readouterr().out)["cause"] == "EVIDENCE_BYTES_MISMATCH"
    ep.write_bytes(raw)
    article["copy"]["headline"] = "PRIVATE_SENTINEL"
    ap.write_text(json.dumps(article), encoding="utf-8")
    assert main(args) == 2
    output = capsys.readouterr().out
    assert json.loads(output)["cause"] == "PRIVATE_TEXT_IN_PUBLIC_COPY"
    assert "PRIVATE_SENTINEL" not in output


@pytest.mark.parametrize("raw,cause", [
    (b'{"schema_version":"first","schema_version":"second"}', "DUPLICATE_JSON_KEY"),
    (b'{"private":NaN}', "NONFINITE_JSON_VALUE"),
])
def test_cli_refuses_ambiguous_or_nonfinite_json_without_echoing_it(raw, cause, tmp_path, capsys):
    ap, ep = tmp_path / "article.json", tmp_path / "evidence.json"
    ap.write_bytes(raw)
    _, evidence = packet()
    data = json.dumps(evidence).encode()
    ep.write_bytes(data)
    assert main(["--article", str(ap), "--evidence", str(ep), "--evidence-sha256", sha256(data).hexdigest()]) == 2
    assert json.loads(capsys.readouterr().out)["cause"] == cause
