"""CC-403 through the source validator, native reader and actual coordinator."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest

from live_contentops.reader_article_contract_v1 import (
    POLICY, GUIDANCE, article_format, check_article, contract_for, numbers,
    publication_timing, validate_article, validate_payload, validate_publication_clock,
)

NOW = datetime(2026, 11, 10, 14, 30, tzinfo=timezone.utc)


def daily():
    article = {"title": "Lower yields leave gold with the stronger case",
        "dek": "We favour gold if the dollar stays soft.",
        "search_title": "Lower yields leave gold with the stronger case",
        "meta_description": "We favour gold if the dollar stays soft.",
        "social_hook": "We favour gold if the dollar stays soft.",
        "substack_body_markdown": """We think lower yields favour gold while the dollar stays soft. [[SOURCE:SOURCE_1]]

| Market | Our view |
| --- | --- |
| Gold (GC / GLD) | We favour strength if yields fall. |
| S&P 500 (ES / SPY) | We watch earnings against yields. |
| EUR/USD (FXE) | We watch the softer dollar. |
| USD/JPY (FXY) | We watch yen strength. |
| WTI (CL / USO) | We watch the fading risk premium. |
| Bitcoin (IBIT) | We watch the next rebound. |
[[SOURCE:SOURCE_1]]

## What changed since yesterday

US10Y eased to 4.21% from 4.25%. [[SOURCE:SOURCE_1]]

## What we got wrong

We expected a firmer dollar; our source records a weaker dollar. [[SOURCE:SOURCE_1]]

## Scenarios

Lower yields: Capital Chronicle model estimate 60%. We favour gold if yields fall. [[SOURCE:SOURCE_1]]

Inflation surprise: Capital Chronicle model estimate 40%. We change our view if inflation strengthens the dollar. [[SOURCE:SOURCE_1]]

## So what

We watch the next inflation release before changing our view. [[SOURCE:SOURCE_1]]""",
        "scenario_analysis": [{"name": "Lower yields", "probability": "60%"},
                              {"name": "Inflation surprise", "probability": "40%"}]}
    source = "\n".join(str(article[k]) for k in ("title", "dek", "substack_body_markdown"))
    documents = [{"source_id": "SOURCE_1", "document_id": "main-current", "publisher": "Capital Chronicle",
        "url": "https://example.org/report", "published_at_utc": "2026-11-10T14:20:00Z",
        "data_cutoff_utc": "2026-11-10T14:00:00Z", "canonical_content_text": source,
        "canonical_content_sha256": sha256(source.encode()).hexdigest(),
        "source_reuse_constraints": {"rights_class": "CC_MODEL_ESTIMATE", "public_expression_reuse_allowed": True}}]
    article["reader_article_contract"] = contract_for({"selected_candidate": {"reader_format": "DAILY_NOTE"},
                                                      "source_pack": documents})
    return article, documents


def test_daily_note_has_one_source_bound_set_and_keeps_its_exact_data_clock():
    article, documents = daily()
    before = deepcopy(article)
    validate_article(article, documents)
    validate_publication_clock(article, now=NOW, destination="substack")
    assert article == before
    assert article["reader_article_contract"]["data_cutoff_utc"] == "2026-11-10T14:00:00+00:00"


@pytest.mark.parametrize("field", ["title", "dek", "substack_body_markdown"])
@pytest.mark.parametrize("phrase", ["DATED CAPITAL CHRONICLE REVIEW", "the review records", "capture"])
def test_internal_phrase_is_named_at_source_validation(field, phrase):
    from live_contentops.v1_simple_gemini_newsroom_v1 import _validate_article_against_source_pack, SimpleGeminiNewsroomError
    article, documents = daily()
    article[field] += " " + phrase
    with pytest.raises(SimpleGeminiNewsroomError, match="INTERNAL_EDITORIAL_LABEL:" + phrase):
        _validate_article_against_source_pack({"article": article}, documents)


@pytest.mark.parametrize("opening", ["The market looks better.", "We reviewed the source today.",
                                     "Gold is stronger. We think the dollar will weaken."])
def test_first_sentence_contains_our_call(opening):
    article, docs = daily()
    article["substack_body_markdown"] = opening + "\n\n" + article["substack_body_markdown"]
    assert "FIRST_SENTENCE_OUR_CALL_REQUIRED" in check_article(article, docs)


def test_second_scenario_heading_or_repeated_probability_set_is_refused():
    article, docs = daily()
    article["substack_body_markdown"] += "\n\n## Earlier scenarios\n\nA second set."
    assert "SINGLE_SCENARIO_SET_REQUIRED" in check_article(article, docs)
    article, docs = daily()
    article["substack_body_markdown"] = article["substack_body_markdown"].replace(
        "## So what", "Another base case is 60%. [[SOURCE:SOURCE_1]]\n\n## So what")
    assert "SINGLE_SCENARIO_SET_REQUIRED:60%" in check_article(article, docs)


@pytest.mark.parametrize("field,value,reason", [("scenario_analysis", ["wrong schema"], "SCENARIOS_REQUIRED"),
    ("social_scenarios", ["wrong schema"], "SOCIAL_SCENARIOS_OBJECT_REQUIRED")])
def test_malformed_model_fields_return_named_findings(field, value, reason):
    article, docs = daily()
    article[field] = value
    assert reason in check_article(article, docs)


@pytest.mark.parametrize("value", ["4.31%", "-4.21%", "4.21 bps"])
def test_each_number_sign_and_unit_must_be_in_its_own_bound_source(value):
    article, docs = daily()
    # An unrelated source containing the new number cannot support SOURCE_1.
    docs.append({"source_id": "SOURCE_2", "context_only": True, "canonical_content_text": value})
    article["reader_article_contract"] = contract_for({"reader_format": "DAILY_NOTE", "source_pack": docs})
    article["substack_body_markdown"] = article["substack_body_markdown"].replace("4.21%", value)
    assert any(e.startswith("NUMBER_NOT_IN_BOUND_SOURCE:") for e in check_article(article, docs))


def test_links_and_source_ids_do_not_supply_fake_numbers():
    assert not numbers("[[SOURCE:SOURCE_99]] [The release](https://example.org/999)")
    assert numbers("4.21 percent and 4,100 and -0.3%") == {"4.21%", "4100", "-0.3%"}
    assert numbers("+0.3% and 0.3%") == {"0.3%"}
    assert not numbers("S&P 500, 6E futures and 6J futures")


def test_daily_limit_counts_prose_but_keeps_the_six_market_table():
    article, docs = daily()
    article["substack_body_markdown"] += "\n\n" + " ".join(["We watch the next release."] * 80)
    assert any(e.startswith("DAILY_NOTE_TOO_LONG:") for e in check_article(article, docs))
    article, docs = daily()
    article["substack_body_markdown"] += "\n\n" + " ".join(["word"] * 36) + "."
    assert any(e.startswith("SENTENCE_TOO_LONG:36:") for e in check_article(article, docs))


@pytest.mark.parametrize("heading,reason", [("What changed since yesterday", "DAILY_CHANGE_SECTION_REQUIRED"),
                                           ("What we got wrong", "DAILY_ERROR_SECTION_REQUIRED"),
                                           ("So what", "SO_WHAT_LINE_REQUIRED")])
def test_daily_sections_are_substantive(heading, reason):
    article, docs = daily()
    article["substack_body_markdown"] = article["substack_body_markdown"].replace("## " + heading, "## Other section")
    assert reason in check_article(article, docs)


def test_clock_is_not_reset_by_generation_context_media_or_mutable_contract():
    article, docs = daily()
    docs.append({"source_id": "SOURCE_2", "context_only": True, "published_at_utc": NOW.isoformat()})
    contract = contract_for({"source_pack": docs, "cutoff_utc": NOW.isoformat()})
    assert contract["data_cutoff_utc"] == article["reader_article_contract"]["data_cutoff_utc"]
    article["reader_article_contract"] = contract
    article["reader_article_contract"]["data_cutoff_utc"] = NOW.isoformat()
    assert "ARTICLE_DATA_CLOCK_CHANGED" in check_article(article, docs)


@pytest.mark.parametrize("age,allowed", [(0, True), (3600, True), (3601, False), (-1, False)])
def test_one_hour_is_checked_at_the_actual_new_canonical_write(age, allowed):
    article, _ = daily()
    article["reader_article_contract"]["data_cutoff_utc"] = (NOW - timedelta(seconds=age)).isoformat()
    if allowed:
        validate_publication_clock(article, now=NOW, destination="substack")
    else:
        with pytest.raises(ValueError, match="ARTICLE_DATA_CUTOFF_"):
            validate_publication_clock(article, now=NOW, destination="substack")
    # Late derivative recovery cannot erase or block a published canonical.
    validate_publication_clock(article, now=NOW + timedelta(days=1), destination="telegram")


def test_source_generation_is_not_substituted_for_an_unknown_retained_data_clock():
    article, docs = daily()
    docs[0].pop("data_cutoff_utc")
    docs[0]["published_at_source"] = "RETAINED_MAIN_REPORT_KNOWN_AT_NOT_PUBLICATION_CLOCK"
    article["reader_article_contract"] = contract_for({"source_pack": docs})
    with pytest.raises(ValueError, match="ARTICLE_DATA_CUTOFF_NOT_SUPPLIED_BY_SOURCE"):
        validate_publication_clock(article, now=NOW, destination="substack")


def test_historical_frozen_copy_stays_exact_and_readback_is_unconditional():
    article = {"title": "DATED CAPITAL CHRONICLE REVIEW", "substack_body_markdown": "The review records the capture."}
    before = deepcopy(article)
    validate_article(article, [])
    validate_payload(article, {"title": article["title"]})
    validate_publication_clock(article, now=NOW, destination="substack")
    assert article == before


def test_native_reader_keeps_clean_title_and_policy_without_relabelling_provenance():
    from live_contentops.v1_simple_gemini_newsroom_v1 import _reader_safe_native_article
    article, _ = daily()
    state = {"reader_visible_epistemic_label": "DATED CAPITAL CHRONICLE REVIEW"}
    rendered = _reader_safe_native_article(article, article_mode="STANDARD_NEWS_ANALYSIS", epistemic_state=state)
    assert rendered["title"] == article["title"]
    assert rendered["reader_article_contract"] == article["reader_article_contract"]
    assert state["reader_visible_epistemic_label"] == "DATED CAPITAL CHRONICLE REVIEW"


def test_our_voice_does_not_promote_an_unconfirmed_event_to_a_fact():
    from live_contentops.main_report_projection_source_v1 import projection_evidence
    from live_contentops.v1_simple_gemini_newsroom_v1 import _epistemic_copy_blockers
    state = projection_evidence([{"document": {"document_id": "current"}, "source_identity": "current",
                                  "headline_text": "A sourced view"}], {})["epistemic_state"]
    state["event_proposition"] = "The central bank raised interest rates."
    article, docs = daily()
    article["title"] = "The central bank raised interest rates."
    article["substack_body_markdown"] += "\n\n" + state["report_scope_notice"]
    assert "epistemic_certainty_inflation:title" in _epistemic_copy_blockers(article, [], state, source_pack=docs)


def test_weekly_reuses_cc379_without_a_daily_word_limit():
    assert article_format({"selected_candidate": {"headline_text": "Weekly review"}}) == "WEEKLY_REVIEW"
    article, docs = daily()
    article["reader_article_contract"] = contract_for({"reader_format": "WEEKLY_REVIEW", "source_pack": docs})
    assert "WEEKLY_CALL_RECORD_REQUIRED" in check_article(article, docs)
    docs[0]["weekly_scored_calls"] = {"counts": {"scored_calls": 1}}
    article["reader_article_contract"] = contract_for({"reader_format": "WEEKLY_REVIEW", "source_pack": docs})
    article["substack_body_markdown"] += "\n\n" + " ".join(["We review our earlier call."] * 80)
    assert not any(e.startswith("DAILY_NOTE_TOO_LONG") for e in check_article(article, docs))


@pytest.mark.parametrize("destination", ["substack", "telegram"])
@pytest.mark.parametrize("bad", [False, True])
def test_live_coordinator_uses_the_reader_check_before_its_real_transport(tmp_path, destination, bad):
    from test_article_publication_quality_cc333 import publication, NOW as FIXTURE_NOW
    _, transport, coordinator, message, _, _, _ = publication(tmp_path, destination=destination)
    path = tmp_path / "article/run_context_v1.json"
    context = json.loads(path.read_bytes())
    copy, docs = context["article"], context["source_documents"]
    docs[0].update(source_id="SOURCE_1", data_cutoff_utc=(FIXTURE_NOW - timedelta(minutes=30)).isoformat())
    copy["substack_body_markdown"] = "We think the conditional policy path matters.\n\n" + copy["substack_body_markdown"] + "\n\nSo what: We watch the next official release."
    copy["reader_article_contract"] = contract_for({"source_pack": docs})
    if bad:
        copy["title"] += " DATED CAPITAL CHRONICLE REVIEW"
    path.write_text(json.dumps(context), encoding="utf-8")
    intent = json.loads(message["payload"])
    intent["native_payload"] = {"title": copy["title"], "text": "\n".join(copy["social_scenarios"].values())}
    result = coordinator._dispatch_message({**message, "payload": json.dumps(intent)},
        canonical_url=None if destination == "substack" else "https://capitalchronicle.substack.com/p/test")
    if bad:
        assert "INTERNAL_EDITORIAL_LABEL:DATED CAPITAL CHRONICLE REVIEW" in str(result)
        assert not transport.publish_calls
    else:
        assert result["status"] == "DISPATCH_CONFIRMED", result
        assert transport.publish_calls == [destination]


def test_observed_publication_uses_the_source_clock():
    article, _ = daily()
    record = publication_timing(article, published_at_utc=NOW.isoformat())
    assert record["seconds_from_data"] == 1800
    assert record["within_60_minutes"] is True
    assert publication_timing(article, published_at_utc=None)["within_60_minutes"] is None


@pytest.mark.parametrize("published,read_at,within", [
    ("2026-11-10T14:35:00Z", "2026-11-10T14:40:00Z", True),
    (None, "2026-11-10T14:40:00Z", True),
    (None, "2026-11-10T15:30:00Z", None),
    ("2026-11-10T15:05:00Z", "2026-11-10T15:30:00Z", False),
])
def test_existing_publication_status_separates_exact_clock_from_readback_upper_bound(published, read_at, within):
    from live_contentops.native_publication_latency_v1 import publication_timing as status_timing
    article, _ = daily()
    reviews = [{"reviewer_ref": "NATIVE_DESKTOP_ARTICLE_REVIEW", "decision": "KEEP",
                "notes": json.dumps({"run_id": "note", "reader_article_contract": article["reader_article_contract"]})}]
    destination = {"destination": "substack", "dispatch_id": "dispatch", "public_object_id": "post",
                   "status": "DISPATCH_CONFIRMED", "reconciliation_status": "RECONCILED_CONFIRMED"}
    proof = {"verified": True, "identity_match": True, "observed_public_object_id": "post", "observed_at_utc": read_at}
    if published:
        proof["observed_published_at_utc"] = published
    rows = [{"dispatch_id": "dispatch", "read_at": read_at, "readback_data": json.dumps({"readback": proof})}]
    timing = status_timing([], reviews, run_id="note", destinations=[destination], readbacks=rows)["data_to_publication"]
    assert timing["within_60_minutes"] is within
    assert timing["published_at_utc"] == published
    if not published:
        assert timing["publication_upper_bound_utc"]
        assert timing["seconds_from_data"] is None


@pytest.mark.parametrize("fault", [None, "internal_title", "missing_error"])
def test_substack_readback_checks_the_clean_title_and_daily_note_text(tmp_path, fault):
    from test_native_neo_executor_v1 import setup, intent, pending_readback, response
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
    from live_contentops.v1_simple_gemini_newsroom_v1 import _reader_safe_native_article
    article, _ = daily()
    rendered = _reader_safe_native_article(article, article_mode="STANDARD_NEWS_ANALYSIS",
        epistemic_state={"reader_visible_epistemic_label": "DATED CAPITAL CHRONICLE REVIEW"})
    _, executor = setup(tmp_path)
    adapter = NeoDestinationHandoff(native_executor=executor)
    value = intent(native_payload={"title": rendered["title"], "body_markdown": rendered["substack_body_markdown"]})
    packet, object_id, url = pending_readback(adapter, value=value)
    lines = []
    for line in rendered["substack_body_markdown"].splitlines():
        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if all(set(cell) <= {"-", ":", " "} for cell in cells):
                continue
            lines.append(" ".join(cells))
        else:
            lines.append(line.removeprefix("## "))
    text = rendered["title"] + "\n" + "\n".join(lines)
    if fault == "internal_title":
        text = text.replace(rendered["title"], "DATED CAPITAL CHRONICLE REVIEW", 1)
    elif fault == "missing_error":
        text = text.replace("We expected a firmer dollar; our source records a weaker dollar.", "")
    observed = response(executor, packet, {"observed_identity": "capitalchronicle.substack.com",
        "public_object_id": object_id, "public_object_url": url, "content_verified": True, "observed_text": text})
    executor.submit(packet["request"]["request_sha256"], observed)
    result = adapter.readback(destination="substack", intent=value, public_object_id=object_id, public_object_url=url)
    assert result["verified"] is (fault is None)
