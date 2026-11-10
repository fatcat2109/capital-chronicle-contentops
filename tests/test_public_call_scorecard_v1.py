from copy import deepcopy
from hashlib import sha256
import json
import sqlite3

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.public_call_scorecard_v1 import build_scorecard, record_article_call_annotation, render_scorecard

AT = "2026-11-06T08:20:00Z"
END = "2026-11-07T00:00:00Z"
CALL = {"condition": "inflation is above the stated threshold", "market": "gold",
        "direction": "bearish", "horizon": "one day", "invalidation": "the prior high is regained"}


@pytest.fixture
def corpus(tmp_path):
    path = tmp_path / "store.sqlite3"
    store = ContentOpsDurableStore(str(path))
    store.create_work_item(story_id="posts", title="Posts", target_surface="MULTI_PLATFORM", work_item_id="posts")
    feed = tmp_path / "published.jsonl"
    feed.write_bytes(b"")
    return store, path, feed


def post(corpus, key, *, plan="plan-one", state="WAITING", status="PUBLISHED", call=None, confirmed=True,
         at=AT, dispatch_status="DISPATCH_CONFIRMED"):
    store, path, _ = corpus
    packet = {"plan_id": plan, "state": state, "at_utc": at,
              "conditional_calls": [deepcopy(CALL if call is None else call)] if state == "WAITING" else []}
    store.register_outbox_message(message_id=key, work_item_id="posts", destination="internal:plan-status-post",
                                  payload=json.dumps(packet), status=status)
    if confirmed:
        store.create_work_item(story_id=key, title="Public post", target_surface="MULTI_PLATFORM", work_item_id=key)
        store.register_outbox_message(message_id=key + "-channel", work_item_id=key, destination="TELEGRAM",
                                      payload="{}", status="SENT")
        with sqlite3.connect(path) as conn:
            conn.execute("INSERT INTO platform_dispatches (dispatch_id,message_id,platform,status,dispatched_at,"
                         "public_object_id,public_object_url) VALUES (?,?,?,?,?,?,?)",
                         (key + "-dispatch", key + "-channel", "TELEGRAM", dispatch_status, at, key,
                          "https://t.me/CapitalChronicle/" + str(len(key))))


def snapshot(corpus, **kwargs):
    return build_scorecard(corpus[0], feed_path=corpus[2], as_of_utc=END, **kwargs)


def test_every_public_call_keeps_original_and_full_denominator(corpus):
    for i, terminal in enumerate(["TRIGGERED", "INVALIDATED", "CANCELLED", "EXPIRED", "VIEW_CHANGED", "WAITING"]):
        post(corpus, f"setup-{i}", plan=f"plan-{i}")
        if terminal != "WAITING":
            post(corpus, f"state-{i}", plan=f"plan-{i}", state=terminal, at="2026-11-06T09:00:00Z")
    result = snapshot(corpus)
    assert result["total_calls"] == 6
    assert result["state_counts"] == {"TRIGGERED": 1, "INVALIDATED": 1, "WITHDRAWN": 2, "NOT_TRIGGERED": 1, "UNRESOLVED": 1}
    assert all(row["call"] == CALL and row["score"] is None for row in result["calls"])
    assert render_scorecard(result).count("If inflation") == 6


def test_partial_distribution_and_removed_posts_stay_in_population(corpus):
    post(corpus, "partial", status="PUBLISHING")
    post(corpus, "removed", plan="removed", dispatch_status="EXTERNAL_REMOVAL_REPORTED_NO_RETRY")
    post(corpus, "queued", plan="queued", status="READY_FOR_PUBLISHER", confirmed=False)
    post(corpus, "ambiguous", plan="ambiguous", status="PUBLISHING", dispatch_status="UNKNOWN_WRITE")
    assert snapshot(corpus)["total_calls"] == 2


def test_repeated_updates_do_not_edit_or_multiply_a_call_and_fills_never_escape(corpus):
    post(corpus, "setup")
    post(corpus, "same-setup")
    post(corpus, "trigger", state="TRIGGERED", at="2026-11-06T09:00:00Z")
    post(corpus, "private-execution", state="FILLED", at="2026-11-06T10:00:00Z")
    result = snapshot(corpus)
    assert result["total_calls"] == 1
    assert result["calls"][0]["state"] == "TRIGGERED"
    assert "FILLED" not in json.dumps(result)
    assert "plan-one" not in json.dumps(result)
    assert result["calls"][0]["first_published_at_utc"] is None  # dispatch is not publication


def test_changed_wording_retains_both_versions(corpus):
    post(corpus, "first")
    changed = {**CALL, "invalidation": "the weekly high is regained"}
    post(corpus, "changed", call=changed)
    result = snapshot(corpus)
    assert result["total_calls"] == 2
    assert {r["call"]["invalidation"] for r in result["calls"]} == {CALL["invalidation"], changed["invalidation"]}


def test_only_observed_publication_time_supplies_publication_clock(corpus):
    post(corpus, "clock")
    published = "2026-11-06T08:21:12Z"
    with sqlite3.connect(corpus[1]) as conn:
        conn.execute("INSERT INTO readbacks (readback_id,dispatch_id,readback_data,read_at) VALUES (?,?,?,?)",
                     ("clock-readback", "clock-dispatch", json.dumps({"readback": {"published_at_utc": published}}),
                      "2026-11-06T08:25:00Z"))
    row = snapshot(corpus)["calls"][0]
    assert row["first_published_at_utc"] == published
    assert row["publications"][0]["dispatch_at_utc"] == AT


def test_public_date_is_converted_and_missing_public_clock_is_not_invented(corpus):
    post(corpus, "no-clock", confirmed=False)
    result = snapshot(corpus)
    text = render_scorecard(result)
    assert result["calls"][0]["first_published_at_utc"] is None
    assert "Time not retained" in text
    assert "2026-11-06 19:00:00 ET" in text
    assert "GMT+7" not in text and "UTC" not in text


def test_real_feed_reader_is_consumed_and_source_files_are_unchanged(corpus, monkeypatch):
    from live_contentops import public_call_scorecard_v1 as module
    row = {"conditional_calls": [CALL], "content_id": "substack:123", "published_at_utc": AT,
           "outlets": [{"name": "substack", "url": "https://capitalchronicle.substack.com/p/test"}]}
    observed = []
    def read(path):
        observed.append(path)
        return [deepcopy(row)]
    monkeypatch.setattr(module, "read_records", read)
    before = corpus[2].read_bytes()
    result = snapshot(corpus)
    assert observed == [corpus[2]]
    assert result["total_calls"] == 1 and result["calls"][0]["call"] == CALL
    assert corpus[2].read_bytes() == before


def test_post_event_and_pre_population_calls_do_not_change_as_of_denominator(corpus):
    post(corpus, "current")
    post(corpus, "future", plan="future", at="2026-11-08T08:20:00Z")
    post(corpus, "before", plan="before", at="2026-11-05T08:20:00Z")
    assert snapshot(corpus)["total_calls"] == 1


@pytest.fixture
def article_annotation(corpus, tmp_path):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from live_contentops.event_article_guard_v1 import CONFLICTS_NOTICE, PUBLIC_NOTICE
    from live_contentops.published_content_v1 import SCHEMA, append_record, canonical

    store, _, feed = corpus
    run, url = "article-run", "https://capitalchronicle.substack.com/p/retained"
    body = "If inflation rises, gold falls and the dollar rises."
    store.create_work_item(story_id=run, title="Retained article", target_surface="MULTI_PLATFORM", work_item_id=run)
    (tmp_path / "run_context_v1.json").write_text(json.dumps({"source_documents": [{
        "document_id": "held-main", "canonical_content_text": body}]}))
    (tmp_path / "article_manifest_v1.json").write_text(json.dumps({"substack_body_markdown": body}))
    public = tmp_path / "public-readback-dom.json"
    public.write_text(json.dumps({"body": body}))
    for key, payload in [("canonical", {"output_dir": str(tmp_path)}),
            ("native-operation-binding-" + sha256_of(run), {"output_dir": str(tmp_path)})]:
        store.register_outbox_message(message_id=key, work_item_id=run, destination="substack",
            payload=json.dumps(payload), status="SENT")
    store.register_platform_dispatch(dispatch_id="article-dispatch", message_id="canonical", platform="substack",
        status="DISPATCH_CONFIRMED", public_object_id="123", public_object_url=url)
    record = {"schema_version": SCHEMA, "content_id": "substack:123", "type": "EVENT_PREVIEW",
        "title": "Conditional inflation map", "standfirst": "A retained public conditional map.",
        "published_at_utc": AT, "recorded_at_utc": AT, "outlets": [{"name": "substack", "url": url}],
        "event_id": "held-event", "conditional_calls": [], "rights_class": "CC_OWN_ANALYSIS",
        "visibility": "public", "disclaimer": PUBLIC_NOTICE, "conflicts_notice": CONFLICTS_NOTICE}
    record["content_sha256"] = sha256(canonical(record)).hexdigest()
    append_record(feed, record)
    calls = [{"call_id": market, "market": market, "direction": direction, "original_text": body,
        "horizon": None, "invalidation": None,
        "public_span": {"start": 0, "end": len(body), "text": body},
        "material_claim_binding": {"document_id": "held-main", "support_excerpt": body}}
        for market, direction in [("XAUUSD", "DOWN"), ("DXY", "UP")]]
    return {"run_id": run, "confirmed_post_id": "123", "canonical_url": url,
        "article_identity": sha256(body.encode()).hexdigest(),
        "public_dom_sha256": sha256(public.read_bytes()).hexdigest(), "allcall_count": 2, "calls": calls}


def test_confirmed_span_annotation_reaches_scorecard_without_rewriting_feed(corpus, article_annotation):
    before = corpus[2].read_bytes()
    first = record_article_call_annotation(corpus[0], article_annotation, feed_path=corpus[2])
    repeated = record_article_call_annotation(corpus[0], article_annotation, feed_path=corpus[2])
    post(corpus, "separate-plan")
    result = snapshot(corpus)
    rows = [r for r in result["calls"] if r.get("annotation_source")]
    assert first["message_id"] == repeated["message_id"]
    assert result["total_calls"] == 3 and len(rows) == 2
    assert {r["market"] for r in rows} == {"XAUUSD", "DXY"}
    assert all(r["first_published_at_utc"] == AT and r["score"] is None for r in rows)
    assert all(r["call"]["horizon"] is None and r["call"]["invalidation"] is None for r in rows)
    assert render_scorecard(result).count(article_annotation["calls"][0]["original_text"]) == 2
    assert corpus[2].read_bytes() == before
    assert build_scorecard(corpus[0], feed_path=corpus[2],
        as_of_utc="2026-11-06T08:19:00Z")["total_calls"] == 0


@pytest.mark.parametrize("fault", ["body", "span", "source", "duplicate", "count", "public_hash"])
def test_annotation_rejects_changed_public_words_sources_or_denominator(corpus, article_annotation, fault):
    changed = deepcopy(article_annotation)
    if fault == "body":
        changed["article_identity"] = "f" * 64
    elif fault == "span":
        changed["calls"][0]["original_text"] += " New words."
    elif fault == "source":
        changed["calls"][0]["material_claim_binding"]["support_excerpt"] = "Unsupported source."
    elif fault == "duplicate":
        changed["calls"][1]["call_id"] = changed["calls"][0]["call_id"]
    elif fault == "count":
        changed["allcall_count"] = 1
    else:
        changed["public_dom_sha256"] = "f" * 64
    before = corpus[0].list_outbox_messages()
    with pytest.raises(ValueError, match="CALL_ANNOTATION_"):
        record_article_call_annotation(corpus[0], changed, feed_path=corpus[2])
    assert corpus[0].list_outbox_messages() == before
