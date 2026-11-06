"""Controlled Main-file fixtures exercise the existing writer and transport consumers."""
from hashlib import sha256
import json
from pathlib import Path

import pytest

from live_contentops.event_public_record_v1 import (
    SCHEMA, attachment_for_article, attachment_readback_matches, load_record,
    record_document, require_preview_deadline, validate_article_record,
)
from live_contentops.contentops_editorial_desk_v1 import record_pre_event_preparation, preview_preparation_research
from live_contentops.event_article_guard_v1 import event_writer_guidance
from live_contentops.event_article_guard_v1 import CONFLICTS_NOTICE, PUBLIC_NOTICE
from tests.test_pre_event_preview_v1 import EVENT, NOW, prepare
from tests.test_capital_chronicle_report_feed_v1 import feed
from tests.test_capital_chronicle_report_editorial_workspace_v1 import controlled_writer

FROZEN = "2026-10-18T16:00:00Z"
RELEASE = "2026-11-06T13:30:00Z"


def frozen_file(tmp_path, **changes):
    binding = {"source_ref": "CONTROLLED Main fixture", "source_sha256": "a" * 64, "known_at_utc": FROZEN}
    doc = {"schema_version": SCHEMA, "event_id": EVENT, "event_time_utc": RELEASE,
           "estimate_label": "Capital Chronicle model estimate", "notice": PUBLIC_NOTICE, "conflicts_notice": CONFLICTS_NOTICE,
           "frozen_at_utc": FROZEN, "resolution_rule": "Main scores the conditional move over the supplied horizon.",
           "reaction_map": [{"condition": "core inflation exceeds 0.3%", "market": "gold", "direction": "bearish",
               "minimum_move": "0.5%", "horizon": "one hour", "invalidation": "the prior high is regained",
               "naive_release_beta": "CONTROLLED estimate: -0.2% per percentage point", **binding}],
           "q1_probabilities": [{"question": "CONTROLLED core inflation bin", "outcome": "above 0.3%",
                                  "probability": "40%", **binding}]}
    doc.update(changes)
    # Keep whitespace, a UTF-8 BOM and CRLF: the reviewed download must be these exact bytes.
    raw = b"\xef\xbb\xbf" + json.dumps(doc, indent=2).replace("\n", "\r\n").encode() + b"\r\n"
    path = tmp_path / "controlled-main-public.json"
    path.write_bytes(raw)
    return {"path": str(path), "sha256": sha256(raw).hexdigest()}, doc


def source(spec):
    return record_document(spec, event_id=EVENT, event_time_utc=RELEASE, cutoff_utc=NOW)


def article(spec, *, kind="EVENT_PREVIEW"):
    record = load_record(spec, event_id=EVENT, event_time_utc=RELEASE, cutoff_utc=NOW)
    return {"article_type": kind, "title": "If core inflation exceeds 0.3%, gold is bearish by at least 0.5% within one hour",
            "substack_body_markdown": f"Frozen: {record['frozen_at_et']}\nSHA-256: {record['sha256']}"}


def test_exact_file_and_converted_freeze_time_reach_real_preview_writer(tmp_path, monkeypatch):
    f = feed(tmp_path)
    spec, _ = frozen_file(tmp_path)
    _, packet, _ = prepare(f.tracker.store, tmp_path)
    record_pre_event_preparation(f.tracker.store, {**packet, "frozen_public_record": spec})
    f.pointer["preview_event_id"] = EVENT
    monkeypatch.setattr(f, "pending", lambda **_: [])
    donor = controlled_writer([])
    observed = []
    class WriterReached(Exception):
        pass
    def invoke(**kwargs):
        governed = kwargs["governed_input"]
        if "candidates" in governed:
            return donor(**kwargs)
        observed.extend(governed["source_pack"])
        raise WriterReached
    with pytest.raises(WriterReached):
        f.opportunity(output_dir=tmp_path / "out", cutoff_utc=NOW, run_id="cc338-preview-consumer",
                      rolling_input={"headlines": []}, llm_invoke=invoke,
                      editorial_request="Write the EVENT_PREVIEW using Main's exact public reaction map.")
    record = next(d["frozen_public_record"] for d in observed if d.get("frozen_public_record"))
    assert record["sha256"] == spec["sha256"]
    assert record["frozen_at_et"] == "2026-10-18 12:00:00 ET"
    assert Path(record["path"]).read_bytes() == Path(spec["path"]).read_bytes()
    guidance = event_writer_guidance({"article_type": "EVENT_PREVIEW", "source_pack": observed})
    assert "CC338_FROZEN_PUBLIC_RECORD" in guidance and "naive_release_beta" in guidance


@pytest.mark.parametrize("change,cause", [
    ({"event_id": "different-event"}, "EVENT_OR_SCHEMA"),
    ({"frozen_at_utc": RELEASE}, "CLOCK_INVALID"),
    ({"reaction_map": []}, "CONDITIONAL_REACTION_MAP"),
    ({"fills": ["PRIVATE MUST NOT LEAK"]}, "EVENT_OR_SCHEMA"),
])
def test_raw_private_wrong_event_and_unfrozen_files_are_not_public_subsets(tmp_path, change, cause):
    spec, _ = frozen_file(tmp_path, **change)
    with pytest.raises(ValueError, match=cause):
        source(spec)


def test_source_bindings_and_exact_bytes_cannot_change(tmp_path):
    spec, doc = frozen_file(tmp_path)
    Path(spec["path"]).write_bytes(Path(spec["path"]).read_bytes() + b" ")
    with pytest.raises(ValueError, match="BYTES_MISMATCH"):
        source(spec)
    doc["reaction_map"][0]["known_at_utc"] = "2026-11-06T14:00:00Z"
    spec, _ = frozen_file(tmp_path, **doc)
    with pytest.raises(ValueError, match="SOURCE_BINDING_INVALID"):
        source(spec)


def test_preview_copy_carries_exact_hash_freeze_and_reaction_headline(tmp_path):
    spec, _ = frozen_file(tmp_path)
    copy = article(spec)
    record = validate_article_record(copy, [source(spec)])
    assert record["sha256"] == spec["sha256"]
    with pytest.raises(ValueError, match="HASH_AND_FREEZE"):
        validate_article_record({**copy, "substack_body_markdown": "Changed hash"}, [source(spec)])
    with pytest.raises(ValueError, match="REACTION_MAP"):
        validate_article_record({**copy, "title": "Inflation preview"}, [source(spec)])
    assert validate_article_record({"article_type": "EVENT_PREVIEW"}, []) is None


def test_review_retains_original_download_bytes_inside_own_media_folder(tmp_path):
    spec, _ = frozen_file(tmp_path)
    copy = article(spec, kind="EVENT_REVIEW")
    copy["frozen_public_record"] = validate_article_record(copy, [source(spec)])
    media = tmp_path / "own-article" / "media"
    attachment = attachment_for_article(copy, media_dir=media)
    assert Path(attachment["path"]).is_relative_to(media.resolve())
    assert Path(attachment["path"]).read_bytes() == Path(spec["path"]).read_bytes()
    assert attachment_for_article(copy, media_dir=media) == attachment
    Path(spec["path"]).unlink()  # Only a controlled fixture; the retained original download remains.
    assert attachment_for_article(copy, media_dir=media) == attachment
    url = "https://capitalchronicle.substack.com/p/controlled-review"
    observed = {"sha256": attachment["sha256"], "bytes": attachment["bytes"], "download_verified": True,
                "public_object_url": url, "url": "https://substackcdn.com/controlled-file.json"}
    assert attachment_readback_matches([attachment], [observed], url)
    for altered in [{"sha256": "0" * 64}, {"bytes": 1}, {"download_verified": False}, {"public_object_url": url + "-other"}]:
        assert not attachment_readback_matches([attachment], [{**observed, **altered}], url)


def test_review_source_pack_contains_frozen_record_and_full_scorecard(tmp_path):
    f = feed(tmp_path)
    spec, _ = frozen_file(tmp_path)
    _, packet, _ = prepare(f.tracker.store, tmp_path)
    record_pre_event_preparation(f.tracker.store, {**packet, "frozen_public_record": spec})
    feed_path = tmp_path / "empty-published-feed.jsonl"
    feed_path.write_bytes(b"")
    research = preview_preparation_research(f.tracker.store, event_id=EVENT, cutoff_utc="2026-11-06T15:00:00Z",
                article_type="EVENT_REVIEW", published_feed_path=feed_path)
    documents = [r["document"] for r in research.records.values()]
    assert any(d.get("frozen_public_record", {}).get("sha256") == spec["sha256"] for d in documents)
    card = next(d for d in documents if d.get("public_call_scorecard"))
    assert card["public_call_scorecard"]["total_calls"] == 0
    copy = article(spec, kind="EVENT_REVIEW")
    with pytest.raises(ValueError, match="FULL_PUBLIC_CALL_SCORECARD"):
        validate_article_record(copy, documents)
    copy["substack_body_markdown"] += "\n\n" + card["canonical_content_text"]
    assert validate_article_record(copy, documents)["sha256"] == spec["sha256"]


def test_two_hour_deadline_is_rechecked_only_for_new_previews(tmp_path):
    spec, _ = frozen_file(tmp_path)
    copy = article(spec)
    copy["frozen_public_record"] = validate_article_record(copy, [source(spec)])
    require_preview_deadline(copy, now_utc="2026-11-06T11:30:00Z")
    with pytest.raises(ValueError, match="TWO_HOUR_DEADLINE"):
        require_preview_deadline(copy, now_utc="2026-11-06T11:30:01Z")
    require_preview_deadline({**copy, "article_type": "EVENT_REVIEW"}, now_utc="2026-11-06T16:00:00Z")


def test_review_attachment_reaches_real_neo_payload_and_readback(tmp_path, monkeypatch):
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff, _payload_binding
    import live_contentops._eight_platform_substack_first_pipeline_impl_v1 as pipeline
    spec, _ = frozen_file(tmp_path)
    copy = article(spec, kind="EVENT_REVIEW")
    copy["frozen_public_record"] = validate_article_record(copy, [source(spec)])
    root = tmp_path / "owned-article"
    root.mkdir()
    monkeypatch.setattr(pipeline, "_durable_intent_inputs", lambda _: {"article": copy, "media_assets": []})
    intent = {"output_dir": str(root), "work_item_id": "test", "payload": "unused",
              "destination_plan": {"payload_hash": "test"}}
    payload, binding = _payload_binding(intent, "substack")
    attachment = binding["attachment_manifest"][0]
    assert Path(attachment["path"]).is_relative_to(root / "media")
    url = "https://capitalchronicle.substack.com/p/controlled-review"
    result = {"status": "SUCCESS", "observed_identity": "capitalchronicle.substack.com", "content_verified": True,
              "public_object_id": "123", "public_object_url": url,
              "observed_text": payload["title"] + "\n" + payload["body_markdown"]}
    def invoke(request):
        return {**result, "request_sha256": request["request_sha256"]}
    adapter = NeoDestinationHandoff(native_executor=invoke)
    value = adapter.readback(destination="substack", intent=intent, public_object_id="123", public_object_url=url)
    assert value["verified"] is False
    result["observed_attachments"] = [{**attachment, "download_verified": True,
                                       "public_object_url": url, "url": "https://substackcdn.com/file.json"}]
    value = adapter.readback(destination="substack", intent=intent, public_object_id="123", public_object_url=url)
    assert value["verified"] is True
