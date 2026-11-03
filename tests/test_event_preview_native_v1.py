"""The native acceptance gate binds real public copy, not a detached safe packet."""
from copy import deepcopy
from hashlib import sha256

import pytest

from live_contentops.event_article_guard_v1 import DISCLAIMER, REACTION_ASSETS, SECTIONS
from live_contentops.event_preview_source_v1 import validate_native_event_preview
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore


def controlled_packet():
    copy = {key: "Synthetic qualitative controlled copy." for key in SECTIONS["EVENT_PREVIEW"]}
    copy["market_reactions"] = {key: "The response remains conditional." for key in REACTION_ASSETS}
    copy["disclaimer"] = DISCLAIMER
    copy["scenarios"] = "The synthetic poll reports 51.1%."
    start = copy["scenarios"].index("51.1%")
    event = {"schema_version": "contentops.event_article.v1", "article_type": "EVENT_PREVIEW",
             "event_id": "US_MIDTERMS_20261103", "event_time_utc": "2026-11-03T23:00:00Z",
             "cutoff_utc": "2026-11-03T06:00:00Z", "written_at_utc": "2026-11-03T06:01:00Z",
             "copy": copy, "numeric_bindings": [{"copy_path": "copy.scenarios", "start": start,
             "end": start + 5, "evidence_ref": "controlled-poll"}]}
    body = "\n\n".join([v for k, v in copy.items() if k not in {"market_reactions", "headline", "dek"}]
                          + list(copy["market_reactions"].values()))
    article = {"article_type": "EVENT_PREVIEW", "event_article": event,
               "title": copy["headline"], "dek": copy["dek"], "substack_body_markdown": body,
               "search_title": copy["headline"], "meta_description": copy["dek"], "social_hook": copy["dek"]}
    evidence = {"schema_version": "contentops.event_article_evidence.v1", "event_id": event["event_id"],
                "facts": {"controlled-poll": {"display": "51.1%", "source_ref": "https://source.invalid/test",
                "source_sha256": "a" * 64, "known_at_utc": "2026-11-02T23:00:00Z",
                "rights_class": "SYNTHETIC_PUBLIC_TEST_ONLY", "public_use_allowed": True,
                "rights_evidence_ref": "controlled-rights", "use_label": "PUBLIC"}}, "private_text": []}
    return {"cutoff_utc": event["cutoff_utc"], "public_event_evidence": evidence}, {"article": article}


def test_valid_event_matches_canonical_and_ordinary_stories_keep_their_contract():
    governed, output = controlled_packet()
    assert validate_native_event_preview(governed, output)["status"] == "PASS"
    assert validate_native_event_preview({}, {}) is None


@pytest.mark.parametrize("fault,cause", [
    ("missing", "PACKET_REQUIRED"), ("title", "COPY_CHANGED"),
    ("section", "SECTION_MISSING"), ("cutoff", "FROZEN_CLOCK_REQUIRED"),
    ("extra_number", "NUMBER_UNBOUND"), ("private_body", "PRIVATE_OR_EXECUTION_COPY_FORBIDDEN"),
    ("market_odds", "PREDICTION_MARKET_NUMBER_FORBIDDEN"),
])
def test_separate_safe_packet_cannot_cover_unsafe_or_different_canonical_copy(fault, cause):
    governed, output = controlled_packet()
    article = output["article"]
    if fault == "missing":
        del article["event_article"]
    elif fault == "title":
        article["title"] = "A different synthetic claim"
    elif fault == "section":
        article["substack_body_markdown"] = DISCLAIMER
    elif fault == "cutoff":
        article["event_article"]["cutoff_utc"] = "2026-11-03T05:00:00Z"
    elif fault == "extra_number":
        article["social_hook"] += " A forecast of 99%."
    elif fault == "private_body":
        article["substack_body_markdown"] += "\nBuy gold now."
    else:
        article["social_hook"] = "Kalshi gives Democrats 51.1%."
    with pytest.raises(ValueError, match=cause):
        validate_native_event_preview(governed, output)


def test_native_submit_refuses_unbound_packet_before_sealing_return(tmp_path):
    governed, output = controlled_packet()
    output.update(schema_version="contentops.v1_simple_gemini_article.v1", public_write_attempted=False,
                  cited_sources=[{"source_id": "SOURCE_1", "url": "https://source.invalid/test",
                  "publisher": "Controlled synthetic source", "published_at_utc": "2026-11-02T23:00:00Z"}],
                  material_claim_bindings=[{"claim_id": "controlled", "claim_kind": "FACT",
                  "claim_text": "Synthetic qualitative controlled copy.", "source_id": "SOURCE_1",
                  "support_excerpt": "Synthetic qualitative controlled copy.", "attribution_required": True}])
    store = ContentOpsDurableStore(tmp_path / "test.sqlite3")
    turn = NativeDesktopTurn(store, run_id="controlled-native-event", output_dir=tmp_path)
    store.create_work_item(story_id=turn.work, work_item_id=turn.work,
                           title="Controlled synthetic event", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn._put("write", "request", {"stage": "write", "request_sha256": "b" * 64, "governed_input": governed})
    response = {"request_sha256": "b" * 64, "output": deepcopy(output), "invocation_observation": {
        "surface": "CODEX_NATIVE_SUBAGENT", "invocation_id": "controlled-test-writer", "model": "gpt-6.1-sol",
        "reasoning_effort": "max", "observation_source": "CONTROLLED_TEST_NOT_RUNTIME_PROOF"}}
    response["output"]["article"]["social_hook"] += " 99%."
    with pytest.raises(ValueError, match="CANONICAL_NUMBER_UNBOUND"):
        turn.submit("write", response)
    assert turn._get("write", "response") is None
    response["output"] = output
    turn.submit("write", response)
    assert turn._get("write", "response")["output"] == output


def test_public_preview_is_not_forced_to_invent_a_main_report_notice(tmp_path, monkeypatch):
    import live_contentops.event_preview_source_v1 as adapter
    from live_contentops.v1_simple_gemini_newsroom_v1 import _epistemic_copy_blockers
    _, output = controlled_packet()
    article = output["article"]
    raw = b"Controlled synthetic polling figure: 51.1%."
    path = tmp_path / "PREVIEW.md"
    path.write_bytes(raw)
    monkeypatch.setattr(adapter, "FROZEN_PREVIEW", path)
    doc = {"document_id": "controlled", "source_identity": "controlled",
           "url": "https://source.invalid/test", "canonical_content_text": raw.decode(),
           "canonical_content_sha256": sha256(raw).hexdigest(), "source_reuse_constraints": {
           "scope": "EXACT_OPS_REVIEWED_CAPITAL_CHRONICLE_PUBLIC_PREVIEW_ONLY",
           "public_expression_reuse_allowed": True, "source_capture_sha256": sha256(raw).hexdigest(),
           "approval_capture_sha256": "c" * 64}}
    state = adapter.approved_preview_evidence([{"document": doc}], {}, revision="test")["epistemic_state"]
    facts = adapter.public_preview_event_evidence([doc])["facts"]
    article["event_article"]["numeric_bindings"][0]["evidence_ref"] = next(
        key for key, fact in facts.items() if fact["display"] == "51.1%")
    assert "report_horizon_proxy_cost_limits_missing" not in _epistemic_copy_blockers(
        article, [], state, source_pack=[doc])
    # A writer's event label alone cannot exempt an ordinary or changed Main source.
    changed = deepcopy(doc)
    changed["canonical_content_text"] = "Unrelated Main projection"
    assert "report_horizon_proxy_cost_limits_missing" in _epistemic_copy_blockers(
        article, [], state, source_pack=[changed])
    assert "report_horizon_proxy_cost_limits_missing" in _epistemic_copy_blockers(article, [], state)
    assert "report_horizon_proxy_cost_limits_missing" in _epistemic_copy_blockers(
        article, [], {**state, "report_scope_notice": "Actual Main limits must survive."}, source_pack=[doc])
