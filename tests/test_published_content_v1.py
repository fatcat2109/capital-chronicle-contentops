"""CC-135 synthetic lifecycle/feed tests; no live store, provider or model calls."""
from copy import deepcopy
from datetime import datetime
from hashlib import sha256

import pytest

from live_contentops.event_article_guard_v1 import (
    CONFLICTS_NOTICE, PUBLIC_NOTICE, PublicOutputError, check_publication_copy, conditional_call_text,
    check_public_event_article,
)
from live_contentops.published_content_v1 import (
    SCHEMA, PublishedContentError, append_record, canonical, read_records, sync_confirmed_piece,
    article_metadata, record_from_corpus, _locked_feed,
)
from live_contentops.publication_coordinator_v1 import normalize_readback_result
from test_event_article_guard_v1 import packet
from test_publication_coordinator_v1 import _coordinator, _plan, _set_mode

NOW = "2026-11-03T01:00:00+00:00"
ORIGINAL = "2026-11-02T17:35:07.590Z"


def sealed(**changes):
    row = {"schema_version": SCHEMA, "content_id": "substack:synthetic-post",
        "type": "ARTICLE", "title": "A synthetic test article", "standfirst": "A test standfirst.",
        "published_at_utc": ORIGINAL, "recorded_at_utc": NOW,
        "outlets": [{"name": "substack", "url": "https://capitalchronicle.substack.com/p/synthetic-post"}],
        "event_id": None, "conditional_calls": [], "rights_class": "CC_OWN_ANALYSIS",
        "visibility": "public", "disclaimer": PUBLIC_NOTICE, "conflicts_notice": None, **changes}
    row["content_sha256"] = sha256(canonical(row)).hexdigest()
    return row


def call():
    return {"condition": "tariffs are removed", "direction": "bullish", "market": "the dollar",
            "horizon": "the following week", "invalidation": "the policy is reinstated"}


def lifecycle(tmp_path, *, body=None, transport=None):
    store, adapter, coordinator = _coordinator(tmp_path, runtime=transport)
    coordinator._clock = lambda: datetime.fromisoformat(NOW)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    article = {"title": "A synthetic test article", "dek": "A test standfirst.",
        "author_identity": "Capital Chronicle", "publisher_identity": "Capital Chronicle",
        "substack_body_markdown": body or "Synthetic factual copy. " + PUBLIC_NOTICE}
    root = tmp_path / "article"
    root.mkdir()
    (root / "article_manifest_v1.json").write_bytes(canonical(article))
    from live_contentops.v1_simple_gemini_newsroom_v1 import _public_copy
    plan = _plan("substack", "telegram", "discord", "x", "facebook_page")
    plan.update(output_dir=str(root), article_content_sha256=sha256(_public_copy(article).encode()).hexdigest())
    coordinator.published_content_path = tmp_path / "published.jsonl"
    return store, adapter, coordinator, plan, article, root


def publish_with_original_clock(tmp_path):
    store, transport, coordinator, plan, article, root = lifecycle(tmp_path)
    original_readback = transport.readback
    def readback(**kwargs):
        result = original_readback(**kwargs)
        result["published_at_utc"] = ORIGINAL
        if kwargs["destination"] == "discord":
            result["public_object_url"] = "https://discord.com/channels/111/222/333"
        return result
    transport.readback = readback
    result = coordinator.execute_plan("work-1", plan)
    return store, transport, coordinator, plan, result


def native_lifecycle(tmp_path):
    from live_contentops.newsroom_production_day_v1 import _logical_hash
    store, transport, coordinator, plan, article, root = lifecycle(tmp_path)
    article.pop("author_identity")
    article.pop("publisher_identity")
    article["schema_version"] = "contentops.v1_simple_article_manifest.v1"
    (root / "article_manifest_v1.json").write_bytes(canonical(article))
    identity = sha256(article["substack_body_markdown"].encode()).hexdigest()
    plan.update(article_identity=identity, editorial_classification="QUALIFIED_NATIVE_DESKTOP_ARTICLE",
        source_provenance_binding_preserved=True, compiler_input_sha256=sha256(b"compiler").hexdigest(),
        accepted_evidence_sha256=sha256(b"admitted sources").hexdigest())
    context = {"schema_version": "contentops.simple_durable_run_context.v1", "run_id": "work-1",
        **{key: plan[key] for key in ("article_identity", "article_content_sha256",
                                    "compiler_input_sha256", "accepted_evidence_sha256")}}
    record = {"schema_version": "contentops.newsroom_qualified_article.v1", "qualified": True,
        "qualification_blockers": [], "public_write_performed": False, "unknown_write_count": 0,
        "derivative_package_intent_count": 8, "derivative_package_intents": [{} for _ in range(8)],
        "newsroom_production_day_id": "2026-11-03", "attempt_run_id": "work-1", "parent_window_id": "work-1",
        "article_identity": identity, "article_body_sha256": identity,
        "accepted_evidence_sha256": plan["accepted_evidence_sha256"],
        "editorial_worker": {"provider": "NATIVE_CODEX_DESKTOP"}}
    record["record_sha256"] = _logical_hash(record)
    (root / "run_context_v1.json").write_bytes(canonical(context))
    (root / "qualified_article_record_v1.json").write_bytes(canonical(record))
    return store, transport, coordinator, plan, article, root


def test_retained_native_original_prose_publishes_and_exports_without_rewriting_its_artifacts(tmp_path):
    _, transport, coordinator, plan, _, root = native_lifecycle(tmp_path)
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    original_readback = transport.readback

    def readback(**kwargs):
        result = {**original_readback(**kwargs), "published_at_utc": ORIGINAL}
        if kwargs["destination"] == "discord":
            result["public_object_url"] = "https://discord.com/channels/111/222/333"
        return result

    transport.readback = readback
    result = coordinator.execute_plan("work-1", plan)
    assert result["canonical_article_real_published"] is True
    assert result.get("published_content_record", {}).get("status") == "APPENDED", result.get("published_content_record")
    assert read_records(coordinator.published_content_path)[0]["rights_class"] == "CC_OWN_ANALYSIS"
    assert {name: (root / name).read_bytes() for name in before} == before


@pytest.mark.parametrize("artifact,key,value", [
    ("plan", "source_provenance_binding_preserved", False),
    ("plan", "editorial_classification", "UNVERIFIED"),
    ("plan", "accepted_evidence_sha256", "0" * 64),
    ("run_context_v1.json", "compiler_input_sha256", "0" * 64),
    ("run_context_v1.json", "article_identity", "0" * 64),
    ("qualified_article_record_v1.json", "record_sha256", "0" * 64),
    ("qualified_article_record_v1.json", "qualified", False),
    ("article_manifest_v1.json", "rights_class", "PRIVATE_ONLY"),
    ("article_manifest_v1.json", "author_identity", "Another publisher"),
    ("article_manifest_v1.json", "schema_version", "unrecognized.article"),
])
def test_native_original_prose_requires_its_exact_qualified_binding_and_preserves_rights_refusals(
    tmp_path, artifact, key, value
):
    _, transport, coordinator, plan, _, root = native_lifecycle(tmp_path)
    if artifact == "plan":
        plan[key] = value
    else:
        import json
        path = root / artifact
        changed = json.loads(path.read_bytes())
        changed[key] = value
        path.write_bytes(canonical(changed))
    with pytest.raises(PublishedContentError, match="PUBLIC_REUSE_RIGHTS_NOT_ADMITTED"):
        coordinator.execute_plan("work-1", plan)
    assert transport.publish_calls == []
    assert not coordinator.published_content_path.exists()


@pytest.mark.parametrize("missing", ["run_context_v1.json", "qualified_article_record_v1.json"])
def test_native_original_prose_never_infers_ownership_from_an_unbound_manifest(tmp_path, missing):
    _, transport, coordinator, plan, _, root = native_lifecycle(tmp_path)
    (root / missing).unlink()
    with pytest.raises(PublishedContentError, match="PUBLIC_REUSE_RIGHTS_NOT_ADMITTED"):
        coordinator.execute_plan("work-1", plan)
    assert transport.publish_calls == []


def test_append_only_exactly_once_preserves_every_prior_byte(tmp_path):
    feed = tmp_path / "feed.jsonl"
    first = sealed()
    assert append_record(feed, first)["status"] == "APPENDED"
    before = feed.read_bytes()
    assert append_record(feed, first)["status"] == "ALREADY_RECORDED"
    assert feed.read_bytes() == before
    second = sealed(content_id="substack:second", outlets=[{
        "name": "substack", "url": "https://capitalchronicle.substack.com/p/second"}])
    append_record(feed, second)
    assert feed.read_bytes() == before + canonical(second) + b"\n"
    assert len(read_records(feed)) == 2


def test_retries_and_late_outlets_never_rewrite_the_original_snapshot(tmp_path):
    feed = tmp_path / "feed.jsonl"
    append_record(feed, sealed())
    before = feed.read_bytes()
    later = sealed(recorded_at_utc="2026-11-04T00:00:00Z", outlets=[
        *sealed()["outlets"], {"name": "x", "url": "https://x.com/test/status/123"}])
    assert append_record(feed, later)["outlet_count"] == 1
    assert feed.read_bytes() == before


@pytest.mark.parametrize("change", [
    {"title": "Changed copy"}, {"content_id": "another-identity"},
    {"published_at_utc": "2026-11-02T18:00:00Z"}, {"type": "DESK_NOTE"},
])
def test_identity_conflicts_are_refused_without_changing_any_bytes(tmp_path, change):
    feed = tmp_path / "feed.jsonl"
    append_record(feed, sealed())
    before = feed.read_bytes()
    with pytest.raises(PublishedContentError, match="IDENTITY_CONFLICT"):
        append_record(feed, sealed(**change))
    assert feed.read_bytes() == before


@pytest.mark.parametrize("corruption", ["seal", "torn", "duplicate", "json-key", "nonfinite"])
def test_corrupt_or_ambiguous_feed_is_never_overwritten(tmp_path, corruption):
    data = canonical(sealed()) + b"\n"
    if corruption == "seal":
        data = data.replace(b"A test standfirst.", b"Tampered.")
    elif corruption == "torn":
        data = data[:-1]
    elif corruption == "duplicate":
        data *= 2
    elif corruption == "json-key":
        data = data.replace(b'{"', b'{"type":"ARTICLE","', 1)
    else:
        data = data.replace(b'"event_id":null', b'"event_id":NaN')
    feed = tmp_path / "feed.jsonl"
    feed.write_bytes(data)
    with pytest.raises((PublishedContentError, ValueError)):
        append_record(feed, sealed())
    assert feed.read_bytes() == data


@pytest.mark.parametrize("change", [
    {"rights_class": None}, {"rights_class": "RIGHTS_MISSING"}, {"rights_class": "MARKET_CONSENSUS_PRIVATE_ONLY"},
    {"rights_class": "invented-public-licence"}, {"visibility": "private"},
    {"recorded_at_utc": "2026-11-01T00:00:00Z"}, {"published_at_utc": "2026-11-02T17:35:07"},
    {"outlets": [{"name": "substack", "url": "https://capitalchronicle.substack.com/p/pending-publication"}]},
    {"outlets": [{"name": "substack", "url": "https://capitalchronicle.substack.com/p/test?token=private"}]},
])
def test_invalid_rights_clocks_and_identities_create_no_feed(tmp_path, change):
    feed = tmp_path / "feed.jsonl"
    with pytest.raises((PublishedContentError, PublicOutputError)):
        append_record(feed, sealed(**change))
    assert not feed.exists()


def test_all_four_report_types_and_event_id_are_preserved(tmp_path):
    for index, kind in enumerate(("ARTICLE", "EVENT_PREVIEW", "EVENT_REVIEW", "DESK_NOTE")):
        row = sealed(type=kind, event_id="synthetic-event", content_id=str(index), outlets=[{
            "name": "substack", "url": f"https://capitalchronicle.substack.com/p/piece-{index}"}])
        append_record(tmp_path / "feed.jsonl", row)
    assert [r["type"] for r in read_records(tmp_path / "feed.jsonl")] == [
        "ARTICLE", "EVENT_PREVIEW", "EVENT_REVIEW", "DESK_NOTE"]


@pytest.mark.parametrize("text", [
    "The desk is bullish on gold.", "Buy gold now.", "Our DEMO account earned 0.8R.",
    "Position size is one lot.", "Profit target: 2500.", "Kalshi is at 55%.",
    "Prediction-market odds are 0.6.", "MARKET_CONSENSUS_PRIVATE_ONLY: 100.",
])
def test_decisions_35_and_40_refuse_private_unconditional_or_market_odds_copy(text):
    with pytest.raises(PublicOutputError):
        check_publication_copy({"body": text + " " + PUBLIC_NOTICE})


def test_decision40_conditional_call_has_the_same_gate_in_copy_and_record(tmp_path):
    c = call()
    authored = conditional_call_text(c)
    copy = {"body": authored + " " + PUBLIC_NOTICE + " " + CONFLICTS_NOTICE}
    assert check_publication_copy(copy, conditional_calls=[c])["status"] == "PASS"
    row = sealed(standfirst=authored, conditional_calls=[c], conflicts_notice=CONFLICTS_NOTICE)
    append_record(tmp_path / "feed.jsonl", row)
    assert read_records(tmp_path / "feed.jsonl")[0]["conditional_calls"] == [c]
    for key in ("condition", "direction", "market", "horizon", "invalidation"):
        missing = deepcopy(c)
        missing.pop(key)
        with pytest.raises(PublicOutputError):
            check_publication_copy(copy, conditional_calls=[missing])
    for text in (PUBLIC_NOTICE, CONFLICTS_NOTICE, authored):
        with pytest.raises(PublicOutputError):
            check_publication_copy({"body": copy["body"].replace(text, "")}, conditional_calls=[c])


@pytest.mark.parametrize("key", ["size", "target", "stop_loss", "demoAccount", "orders", "positions"])
def test_conditional_call_never_waives_private_fields(key):
    c = {**call(), key: "PRIVATE_SENTINEL"}
    with pytest.raises(PublicOutputError) as failure:
        check_publication_copy({"body": PUBLIC_NOTICE}, conditional_calls=[c])
    assert "PRIVATE_SENTINEL" not in str(failure.value)


def test_event_template_accepts_the_same_conditional_call_without_new_numbers():
    article, evidence = packet()
    article["conditional_calls"] = [call()]
    article["copy"]["context"] = conditional_call_text(call()) + " " + CONFLICTS_NOTICE
    assert check_public_event_article(article, evidence=evidence)["status"] == "PASS"


def test_original_publication_clock_is_retained_only_when_explicitly_observed():
    assert normalize_readback_result({"id": "x", "verified": True}, public_object_id="x").get(
        "observed_published_at_utc") is None
    value = normalize_readback_result({"id": "x", "verified": True, "published_at_utc": ORIGINAL},
                                      public_object_id="x")
    assert value["observed_published_at_utc"] == "2026-11-02T17:35:07.590000+00:00"


def test_publication_appends_one_piece_with_five_exact_confirmed_outlets_and_no_repeat(tmp_path):
    store, transport, coordinator, plan, result = publish_with_original_clock(tmp_path)
    assert result["published_content_record"]["status"] == "APPENDED"
    feed = coordinator.published_content_path
    records = read_records(feed)
    assert len(records) == 1 and len(records[0]["outlets"]) == 5
    assert records[0]["published_at_utc"] == "2026-11-02T17:35:07.590000+00:00"
    before = feed.read_bytes()
    calls = list(transport.publish_calls)
    coordinator.execute_plan("work-1", plan)
    assert feed.read_bytes() == before and transport.publish_calls == calls
    assert sync_confirmed_piece(store, feed, "work-1")["status"] == "ALREADY_RECORDED"


def test_unknown_canonical_never_enters_feed(tmp_path):
    from test_publication_coordinator_v1 import FixtureTransport
    store, transport, coordinator, plan, _, _ = lifecycle(tmp_path, transport=FixtureTransport(ambiguous=True))
    coordinator.execute_plan("work-1", plan)
    assert not coordinator.published_content_path.exists()
    assert sync_confirmed_piece(store, coordinator.published_content_path, "work-1")["status"] == "CANONICAL_NOT_CONFIRMED_NO_RECORD"


def test_original_date_gap_is_named_and_never_replaced_with_dispatch_time(tmp_path):
    store, transport, coordinator, plan, _, _ = lifecycle(tmp_path)
    result = coordinator.execute_plan("work-1", plan)
    assert result["canonical_article_real_published"]
    assert result["published_content_record"]["cause"] == "ORIGINAL_PUBLICATION_CLOCK_READBACK_REQUIRED"
    assert not coordinator.published_content_path.exists()


def test_the_shared_gate_runs_before_any_publication(tmp_path):
    _, transport, coordinator, plan, _, _ = lifecycle(tmp_path, body="Buy gold now. " + PUBLIC_NOTICE)
    with pytest.raises(PublicOutputError):
        coordinator.execute_plan("work-1", plan)
    assert transport.publish_calls == []


def test_reviewed_artifact_cannot_change_before_publication(tmp_path):
    _, transport, coordinator, plan, article, root = lifecycle(tmp_path)
    article["title"] = "Changed after review"
    (root / "article_manifest_v1.json").write_bytes(canonical(article))
    with pytest.raises(PublishedContentError, match="EXACT_REVIEWED_ARTICLE_HASH_REQUIRED"):
        coordinator.execute_plan("work-1", plan)
    assert not transport.publish_calls


def test_one_identity_cannot_be_reused_for_a_different_canonical(tmp_path):
    feed = tmp_path / "feed.jsonl"
    append_record(feed, sealed())
    before = feed.read_bytes()
    with pytest.raises(PublishedContentError, match="IDENTITY_CONFLICT"):
        append_record(feed, sealed(outlets=[{"name": "substack",
            "url": "https://capitalchronicle.substack.com/p/another"}]))
    assert feed.read_bytes() == before


def test_competing_feed_lock_fails_without_a_second_append_or_wait_loop(tmp_path):
    feed = tmp_path / "feed.jsonl"
    with _locked_feed(feed):
        with pytest.raises(PublishedContentError, match="PUBLISHED_FEED_BUSY"):
            append_record(feed, sealed())
    assert feed.read_bytes() == b""
    append_record(feed, sealed())
    assert len(read_records(feed)) == 1


@pytest.mark.parametrize("condition", ["always", "none", "unconditional", "true", "no condition", "n/a"])
def test_a_placeholder_condition_does_not_waive_the_unconditional_call_rule(condition):
    c = {**call(), "condition": condition}
    with pytest.raises(PublicOutputError):
        check_publication_copy({"body": conditional_call_text(c) + " " + PUBLIC_NOTICE + " " + CONFLICTS_NOTICE},
                               conditional_calls=[c])


def test_backfill_on_a_copied_store_is_read_only_once_and_keeps_the_original_date(tmp_path):
    import sqlite3
    from scripts.backfill_published_content_v1 import backfill
    store, _, _, _, _ = publish_with_original_clock(tmp_path)
    copied = tmp_path / "copied.sqlite3"
    with store.get_read_only_connection() as source, sqlite3.connect(copied) as target:
        source.backup(target)
    before = copied.read_bytes()
    observations = [{"canonical_url": "https://capitalchronicle.substack.com/p/fixture-article-1",
        "public_object_id": "substack-object-1", "published_at_utc": ORIGINAL,
        "observation_recorded_at_utc": NOW, "observation_source": "BROWSEROS_NEO_EXACT_PUBLIC_PAGE"}]
    output = tmp_path / "backfill.jsonl"
    dry = backfill(copied, output, observations, now=NOW)
    assert dry["piece_count"] == 1 and not output.exists()
    result = backfill(copied, output, observations, now=NOW, apply=True)
    assert result["pieces"][0]["outlet_count"] == 5
    raw = output.read_bytes()
    assert read_records(output)[0]["published_at_utc"] == ORIGINAL
    assert backfill(copied, output, observations, now=NOW, apply=True)["pieces"][0]["status"] == "ALREADY_RECORDED"
    assert copied.read_bytes() == before and output.read_bytes() == raw
    for bad in ([{**observations[0], "public_object_id": "other"}], [],
                [{**observations[0], "published_at_utc": "2027-01-01T00:00:00Z"}]):
        untouched = tmp_path / "invalid.jsonl"
        with pytest.raises(ValueError):
            backfill(copied, untouched, bad, now=NOW, apply=True)
        assert not untouched.exists()


def test_discord_url_enrichment_requires_the_existing_channel_and_exact_message(tmp_path):
    from dataclasses import replace
    from live_contentops.published_corpus_read_model_v1 import load_published_corpus
    store, _, _, plan, _ = publish_with_original_clock(tmp_path)
    article = load_published_corpus(store)["articles"][0]
    objects = tuple({**o, "public_object_url": None, "public_object_id": "333"}
                    if o["destination"] == "discord" else o for o in article.derivative_public_objects)
    article = replace(article, derivative_public_objects=objects)
    metadata = article_metadata(plan)
    row = record_from_corpus(article, metadata, published_at_utc=ORIGINAL, recorded_at_utc=NOW)
    discord = next(o for o in row["outlets"] if o["name"] == "discord")
    assert discord["url"] == "https://discord.com/channels/1519310996030750782/1519311669216673802/333"
    with pytest.raises(PublishedContentError, match="URL_IDENTITY_MISMATCH"):
        record_from_corpus(article, metadata, published_at_utc=ORIGINAL, recorded_at_utc=NOW,
                          outlet_urls={"discord": discord["url"][:-3] + "999"})


def test_new_native_requests_ask_for_original_time_and_historical_hashes_stay_unchanged():
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
    from test_native_neo_executor_v1 import intent
    adapter = NeoDestinationHandoff()
    value = intent()
    def request(v):
        return adapter.request(destination="substack", action="READBACK", intent=v,
            public_object_id="123", public_object_url="https://capitalchronicle.substack.com/p/test")
    before = request(value)
    after = request({**value, "published_content_export": SCHEMA})
    assert "publication_clock_readback" not in before
    assert "published_at_utc" in after["publication_clock_readback"]
    assert request(value) == before


def test_historical_intents_and_published_copy_remain_readback_only_without_a_new_notice(tmp_path):
    _, transport, coordinator, plan, _, _ = lifecycle(tmp_path, body="Historical general analysis.")
    coordinator.published_content_path = None
    coordinator.execute_plan("work-1", plan)
    before = [r["payload"] for r in coordinator.store.list_outbox_messages()]
    calls = list(transport.publish_calls)
    coordinator.published_content_path = tmp_path / "legacy-feed.jsonl"
    coordinator.execute_plan("work-1", plan)
    assert [r["payload"] for r in coordinator.store.list_outbox_messages()] == before
    assert transport.publish_calls == calls


def test_postwrite_export_error_is_reported_without_another_public_send(tmp_path, monkeypatch):
    import live_contentops.published_content_v1 as feed_module
    _, transport, coordinator, plan, _ = publish_with_original_clock(tmp_path)
    coordinator.published_content_path.unlink()
    calls = list(transport.publish_calls)
    with monkeypatch.context() as patch:
        def no_space(*_args):
            raise OSError("private path must not be printed")
        patch.setattr(feed_module, "append_record", no_space)
        result = coordinator.execute_plan("work-1", plan)
        assert result["published_content_record"] == {"status": "PUBLICATION_RECORD_PENDING", "cause": "OSError"}
    assert transport.publish_calls == calls
    repaired = coordinator.execute_plan("work-1", plan)
    assert repaired["published_content_record"]["status"] == "APPENDED"
    assert transport.publish_calls == calls
