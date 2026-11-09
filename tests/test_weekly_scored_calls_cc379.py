"""The actual native writer/validator/reader projection consumes every weekly outcome."""
from copy import deepcopy
import json

import pytest

from live_contentops import weekly_scored_calls_v1 as weekly
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import DesktopInputRequired, NativeDesktopTurn
from live_contentops import v1_simple_gemini_newsroom_v1 as newsroom

CUTOFF = "2026-11-14T15:00:00Z"


def scored(name, result, at, *, asset="XAUUSD", known="2026-11-14T12:00:00Z"):
    return {"plan_id": name, "asset_id": asset, "direction": "BEARISH",
            "zone": {"minimum": "4070.00", "maximum": "4085.00"},
            "outcome": {"state": "SCORED", "result": result, "outcome_id": name + "-outcome",
                "score": {"result": result, "plan_id": name, "asset_id": asset, "direction": "BEARISH",
                    "outcome_id": name + "-outcome", "content_hash": "c" * 64,
                    "resolved_at_utc": at, "scored_at_utc": known,
                    "comment": "100% win rate, lots, money, alpha, account 123456", "r_multiple": 99}}}


def export():
    plans = [scored("hit", "HIT", "2026-11-09T14:00:00Z"),
             scored("stop1", "STOPPED", "2026-11-10T14:00:00Z"),
             scored("stop2", "STOPPED", "2026-11-11T14:00:00Z"),
             scored("close", "EXPIRED", "2026-11-14T04:59:59Z", asset="EURUSD"),
             scored("old", "STOPPED", "2026-11-09T04:59:59Z"),
             scored("next", "HIT", "2026-11-14T05:00:00Z"),
             scored("late", "HIT", "2026-11-12T14:00:00Z", known="2026-11-15T14:00:00Z"),
             {"plan_id": "untriggered", "outcome": {"state": "NOT_SCORED_UNTRIGGERED"}}]
    return {"status": {"content_hash": "e" * 64, "generated_at_utc": CUTOFF,
                       "scored_call_count": 7, "plans": plans}, "transitions": {"transitions": []}}


def turn(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    run = "cc124-weekend-wrap-20261114"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Weekly wrap", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    return NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)


def test_whole_record_ignores_selective_feed_and_uses_et_resolution_week():
    record = weekly.project(export(), cutoff_utc=CUTOFF)
    assert [r["plan_id"] for r in record["rows"]] == ["hit", "stop1", "stop2", "close"]
    assert record["counts"] == {"scored_calls": 4, "hits": 1, "stops": 2}
    assert record["export_scored_call_count"] == 7  # Cumulative is never presented as this week's count.
    assert "closed at the end of its window" in record["text"]
    assert "entry zone 4,070.00–4,085.00" in record["text"]
    assert "9 Nov–13 Nov 2026 ET" in record["text"]
    for forbidden in ("win rate", "lots", "money", "alpha", "123456", "r_multiple", "99"):
        assert forbidden not in record["text"]
    assert weekly.PUBLIC_NOTICE in record["text"] and weekly.CONFLICTS_NOTICE in record["text"]


def test_empty_week_is_explicit_without_invented_results():
    data = export()
    data["status"].update(plans=[], scored_call_count=0)
    record = weekly.project(data, cutoff_utc=CUTOFF)
    assert record["counts"] == {"scored_calls": 0, "hits": 0, "stops": 0}
    assert "No conditional model calls were scored" in record["text"]


@pytest.mark.parametrize("change", ["count", "duplicate", "score", "direction", "zone"])
def test_inconsistent_export_cannot_silently_drop_or_relabel_a_call(change):
    data = export()
    p = data["status"]["plans"][0]
    if change == "count":
        data["status"]["scored_call_count"] = True
    elif change == "duplicate":
        data["status"]["plans"].append(deepcopy(p))
        data["status"]["scored_call_count"] += 1
    elif change == "score":
        p["outcome"]["score"]["result"] = "STOPPED"
    elif change == "direction":
        p["direction"] = "BULLISH"
    else:
        p["zone"]["minimum"] = "NaN"
    with pytest.raises(ValueError, match="WEEKLY_CALL"):
        weekly.project(data, cutoff_utc=CUTOFF)


def test_corrections_use_mains_current_outcome_once():
    data = export()
    p = data["status"]["plans"][0]
    p["outcome"]["result"] = p["outcome"]["score"]["result"] = "STOPPED"
    p["outcome"]["score"]["corrects_outcome_id"] = "old-outcome"
    record = weekly.project(data, cutoff_utc=CUTOFF)
    assert record["counts"] == {"scored_calls": 4, "hits": 0, "stops": 3}
    assert len(record["rows"]) == 4


def test_dst_boundaries_and_monday_wrap_use_the_completed_week():
    start, end = weekly.week_window("2026-11-02T13:00:00Z")
    assert start.isoformat() == "2026-10-26T00:00:00-04:00"
    assert end.isoformat() == "2026-10-31T00:00:00-04:00"
    assert weekly.week_window(CUTOFF)[0].isoformat() == "2026-11-09T00:00:00-05:00"


def test_native_source_packet_and_writer_use_retained_record_on_restart(tmp_path, monkeypatch):
    native = turn(tmp_path)
    calls = []
    monkeypatch.setattr(weekly, "read_export", lambda: (calls.append(True) or export()))
    kwargs = {"source_pack": [], "selected_candidate": {"title": "Weekend wrap"}, "cutoff_utc": CUTOFF}
    docs = native.weekly_call_sources(**kwargs)
    assert len(calls) == 1
    assert native.weekly_call_sources(**kwargs) == docs and len(calls) == 1
    governed = {"source_pack": docs, "selected_candidate": kwargs["selected_candidate"], "cutoff_utc": CUTOFF}
    prompt = newsroom._worker_prompt(governed)
    assert "CC379_WHOLE_WEEK_RECORD" in prompt
    assert all(r["line"] in prompt for r in docs[0]["weekly_scored_calls"]["rows"])
    assert "CC379_WHOLE_WEEK_RECORD" in newsroom._revision_prompt(governed, {}, ["missing section"])
    # Use the production NativeDesktopTurn request owner, with controlled source-only input.
    args = dict(logical_invocation_id=native.run_id + ":write", prompt=prompt,
                governed_input={"weekly_record_source": docs}, validator=lambda raw: (True, None, json.loads(raw), None))
    with pytest.raises(DesktopInputRequired) as pending:
        native(**args)
    assert pending.value.request["governed_input"]["weekly_record_source"] == docs
    with pytest.raises(DesktopInputRequired) as resumed:
        native(**args)
    assert resumed.value.request["request_sha256"] == pending.value.request["request_sha256"]


def article_for(doc):
    sentence = "Results refer to resolved conditional model calls."
    body = "\n\n".join(p + " [[SOURCE:SOURCE_1]]" for p in doc["canonical_content_text"].split("\n\n"))
    article = {k: sentence for k in ("title", "dek", "search_title", "meta_description", "social_hook")}
    article["substack_body_markdown"] = body
    claims = [{"claim_id": "record", "claim_kind": "FACT", "claim_text": sentence,
               "source_id": "SOURCE_1", "support_excerpt": sentence, "attribution_required": True}]
    return {"article": article, "cited_sources": [{"source_id": "SOURCE_1", "url": doc["url"]}],
            "material_claim_bindings": claims}


def test_complete_record_reaches_article_validation_and_reader_compiler():
    doc = weekly.document(weekly.project(export(), cutoff_utc=CUTOFF), "SOURCE_1")
    output = article_for(doc)
    article, validation = newsroom._validate_article_against_source_pack(output, [doc])
    assert validation["status"] == "PASS"
    assert article["weekly_scored_calls"]["counts"]["stops"] == 2
    # Actual canonical reader projection, before the existing compiler/publication owner.
    reader = newsroom._reader_safe_native_article(article, article_mode="STANDARD_NEWS_ANALYSIS")
    assert reader["weekly_scored_calls"] == article["weekly_scored_calls"]
    for row in doc["weekly_scored_calls"]["rows"]:
        assert row["line"] in reader["substack_body_markdown"]


@pytest.mark.parametrize("change", ["omit_loss", "wrong_number", "duplicate", "source_changed"])
def test_actual_article_validator_refuses_selective_or_changed_record(change):
    doc = weekly.document(weekly.project(export(), cutoff_utc=CUTOFF), "SOURCE_1")
    output = article_for(doc)
    body = output["article"]["substack_body_markdown"]
    if change == "omit_loss":
        body = body.replace(doc["weekly_scored_calls"]["rows"][1]["line"], "")
    elif change == "wrong_number":
        body = body.replace("Stops: 2", "Stops: 1")
    elif change == "duplicate":
        body += "\n\n" + body
    else:
        doc["canonical_content_text"] = doc["canonical_content_text"].replace("Stops: 2", "Stops: 1")
    output["article"]["substack_body_markdown"] = body
    with pytest.raises(newsroom.SimpleGeminiNewsroomError, match="deterministic_article_validation_failed"):
        newsroom._validate_article_against_source_pack(output, [doc])


def test_ordinary_articles_and_historical_frozen_wraps_stay_byte_stable(tmp_path, monkeypatch):
    native = turn(tmp_path)
    monkeypatch.setattr(weekly, "read_export", lambda: pytest.fail("must not refresh frozen or unrelated input"))
    docs = [{"source_id": "SOURCE_1", "canonical_content_text": "Original."}]
    # Unrelated daily article, even in this controlled run.
    monkeypatch.setattr(native, "run_id", "daily-market")
    assert native.weekly_call_sources(source_pack=docs, selected_candidate={"title": "Daily markets"}, cutoff_utc=CUTOFF) is docs
    monkeypatch.setattr(native, "frozen_request", lambda stage: {"prompt": "Original frozen request"})
    assert native.weekly_call_sources(source_pack=docs, selected_candidate={"title": "Weekend wrap"}, cutoff_utc=CUTOFF) is docs
