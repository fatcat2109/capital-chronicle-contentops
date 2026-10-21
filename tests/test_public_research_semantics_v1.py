"""Labelled consumer controls; synthetic descriptors are not Main forecasts."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.capital_chronicle_public_research_semantics_v1 import (
    FIELDS, public_descriptors, claim_semantics, reference_blockers,
    dependence_copy_blockers, descriptor_changes,
)
from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_document
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    _source_pack, _validate_article_against_source_pack, _native_preview_bundle,
    _validate_worker_text, SimpleGeminiNewsroomError,
)

ROOT = Path(__file__).resolve().parents[1] / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal29"


def retained():
    q = json.loads((ROOT / "articles/goal29-brent-transmission/desktop_request_write.json").read_bytes())
    output = json.loads((ROOT / "articles/goal29-brent-transmission/revise_response.json").read_bytes())
    return q["governed_input"], output


def controlled_descriptor(envelope, claim):
    value = {"schema_version": "contentops.public_research_descriptor.v1",
        **{k: envelope[k] for k in ("report_id", "report_version", "report_sha256")},
        "claim_id": claim["claim_id"], "claim_hash": claim["claim_hash"],
        "target_event": {"kind": "TERMINAL_DIRECTION", "definition": "CONTROL_ONLY: terminal direction of retained proxy"},
        "instrument_proxy": {"instrument": "UKOIL", "basis": "CONTROL_ONLY_UNRESOLVED"},
        "horizon": {"trading_sessions": 5}, "knowledge_cutoff_utc": "2026-10-19T12:25:00Z",
        "outcome_resolution": "CONTROL_ONLY_NO_OUTCOMES", "probability_measure": "RISK_NEUTRAL",
        "method": {"version": "CONTROL_ONLY_NOT_A_MODEL_RESULT"},
        "evaluation_scope": {"state": "NOT_EVALUATED"}, "selection": None, "dependence": None,
        "limitations": ["No physical win-rate inference", "Evaluation and selection unknown"],
        "reader_disclosure": "Engineering control only: risk-neutral measure; no physical win-rate inference; evaluation and selection unknown."}
    value["descriptor_sha256"] = sha256_of(value)
    return value


def descriptor_context():
    g, _ = retained()
    c = deepcopy(g["source_pack"][0]["report_lineage"]["claims"][1])
    envelope = {k: g["source_pack"][0]["report_lineage"][k] for k in ("report_id", "report_version", "report_sha256")}
    d = controlled_descriptor(envelope, c)
    admission = {**envelope, "source_report_sha256": envelope["report_sha256"], "public_research_descriptors": {c["claim_id"]: d}, "horizon_blocks": []}
    return c, d, claim_semantics(admission, c)


def test_optional_public_extension_is_exact_bound_and_missing_stays_unknown():
    c, d, _ = descriptor_context()
    envelope = {**{k: d[k] for k in ("report_id", "report_version", "report_sha256")}, "public_safe_claims": [c]}
    assert public_descriptors({}, envelope) == {}
    assert public_descriptors({"public_research_descriptors": [d]}, envelope) == {c["claim_id"]: d}
    for key in ("report_id", "report_version", "report_sha256", "claim_hash"):
        wrong = deepcopy(d)
        wrong[key] = "incorrect"
        wrong["descriptor_sha256"] = sha256_of({k: v for k, v in wrong.items() if k != "descriptor_sha256"})
        with pytest.raises(ValueError, match="DESCRIPTOR_INVALID"):
            public_descriptors({"public_research_descriptors": [wrong]}, envelope)


@pytest.mark.parametrize("key", FIELDS)
def test_target_measure_horizon_cutoff_method_evaluation_selection_dependence_cannot_drift(key):
    _, d, context = descriptor_context()
    reference = {k: deepcopy(d.get(k)) for k in (*FIELDS, "descriptor_sha256")}
    assert not reference_blockers(reference, context)
    reference[key] = "CONTROL_ONLY_WRONG_SEMANTICS"
    assert "public_probability_semantic_mismatch:" + key in reference_blockers(reference, context)


@pytest.mark.parametrize("copy", ["This is a physical probability of profit.", "Đây là tỷ lệ thắng giao dịch.", "This forecasts stop-before-target probability."])
def test_risk_neutral_or_terminal_direction_is_not_a_trade_win_rate(copy):
    _, d, context = descriptor_context()
    ref = {k: deepcopy(d.get(k)) for k in (*FIELDS, "descriptor_sha256")}
    assert "public_probability_target_or_measure_reworded" in reference_blockers(ref, context, claim_text=copy)
    assert not reference_blockers(ref, context, claim_text="This is not a physical probability of profit.")


def test_shared_release_and_main_recirculation_are_not_independent_confirmation():
    _, _, context = descriptor_context()
    assert dependence_copy_blockers("Two independent sources confirm the same retained release.", [context])
    assert not dependence_copy_blockers("Two copies do not establish independent confirmations.", [context])
    assert not dependence_copy_blockers("Hai bản sao không tạo thêm xác nhận độc lập.", [context])


def test_descriptor_changes_invalidate_even_unchanged_claim_text():
    c, d, context = descriptor_context()
    previous = [{**c, "research_semantics": context}]
    assert not descriptor_changes(previous, {"public_research_descriptors": {c["claim_id"]: d}})
    assert descriptor_changes(previous, {"public_research_descriptors": {}}) == [c["claim_id"]]


def test_real_retained_native_article_validates_without_inventing_probability():
    g, output = retained()
    before = deepcopy(output)
    for pack in g["source_pack"]:
        for c in pack.get("report_lineage", {}).get("claims", []):
            admission = {**pack["report_lineage"], "source_report_sha256": pack["report_lineage"]["report_sha256"]}
            c["research_semantics"] = claim_semantics(admission, c)
            assert c["research_semantics"]["probability_metadata_state"] == "UNKNOWN_NOT_SUPPLIED"
    article, validation = _validate_article_against_source_pack(output, g["source_pack"],
        selected_candidate=g["selected_candidate"], article_mode=g["article_mode"], epistemic_state=g["epistemic_state"])
    assert validation["status"] == "PASS" and "public_research_descriptors" not in article
    assert output == before
    assert any(c.get("research_semantics") for c in validation["supported_material_claims"])


def test_labelled_descriptor_reaches_actual_validator_and_all_eight_compiled_previews():
    g, output = retained()
    c, d, context = descriptor_context()
    extra_limit = "Control restriction: outcome availability clock remains unknown."
    d["limitations"].append(extra_limit)
    d["descriptor_sha256"] = sha256_of({k: v for k, v in d.items() if k != "descriptor_sha256"})
    context["probability_descriptor"] = deepcopy(d)
    context["semantics_sha256"] = sha256_of({k: v for k, v in context.items() if k != "semantics_sha256"})
    # CONTROL ONLY: attach explicit typed metadata to the matching retained claim;
    # this does not alter or promote any Main wire/accepted article.
    pack = g["source_pack"][0]
    claim = next(x for x in pack["report_lineage"]["claims"] if x["claim_id"] == c["claim_id"])
    claim["research_semantics"] = context
    ref = {k: deepcopy(d.get(k)) for k in (*FIELDS, "descriptor_sha256")}
    matched = [b for b in output["material_claim_bindings"] if b["support_excerpt"] in c["text"]]
    assert matched
    for binding in matched:
        binding["research_reference"] = ref
    assert _validate_worker_text(json.dumps(output))[0]
    # Omission is a content limitation, not an estimate filled in by the consumer.
    with pytest.raises(SimpleGeminiNewsroomError, match="deterministic_article_validation_failed"):
        _validate_article_against_source_pack(output, g["source_pack"], epistemic_state=g["epistemic_state"])
    output["article"]["substack_body_markdown"] += "\n\n" + d["reader_disclosure"] + " [[SOURCE:SOURCE_1]]"
    pack["canonical_content_text"] += "\n\n" + d["reader_disclosure"]
    pack["report_lineage"]["source_research_metadata"] = [{"text": d["reader_disclosure"]}]
    output["material_claim_bindings"].append({"claim_id": "control-disclosure", "claim_text": d["reader_disclosure"],
        "claim_kind": "FACT", "source_id": "SOURCE_1", "support_excerpt": d["reader_disclosure"], "attribution_required": True})
    with pytest.raises(SimpleGeminiNewsroomError, match="deterministic_article_validation_failed"):
        _validate_article_against_source_pack(output, g["source_pack"], epistemic_state=g["epistemic_state"])
    output["article"]["substack_body_markdown"] += "\n\n" + extra_limit + " [[SOURCE:SOURCE_1]]"
    pack["canonical_content_text"] += "\n\n" + extra_limit
    pack["report_lineage"]["source_research_metadata"].append({"text": extra_limit})
    output["material_claim_bindings"].append({"claim_id": "control-extra-limitation", "claim_text": extra_limit,
        "claim_kind": "FACT", "source_id": "SOURCE_1", "support_excerpt": extra_limit, "attribution_required": True})
    article, _ = _validate_article_against_source_pack(output, g["source_pack"], epistemic_state=g["epistemic_state"])
    assert article["public_research_descriptors"] == [d]
    wrong = deepcopy(output)
    next(b for b in wrong["material_claim_bindings"] if b.get("research_reference"))["research_reference"]["horizon"] = {"trading_sessions": 21}
    with pytest.raises(SimpleGeminiNewsroomError) as error:
        _validate_article_against_source_pack(wrong, g["source_pack"], epistemic_state=g["epistemic_state"])
    assert "public_probability_semantic_mismatch:horizon" in error.value.details
    previews, _ = _native_preview_bundle(article=article, article_mode=g["article_mode"], article_identity="labelled-control",
        epistemic_state=g["epistemic_state"], media_asset_ids=[])
    assert len(previews["packages"]) == 8
    for p in previews["packages"].values():
        text = p.get("full_text") or p.get("text") or ""
        assert d["reader_disclosure"] in text
        assert extra_limit in text


def test_labelled_public_wire_extension_survives_admission_document_and_source_pack():
    import hashlib
    from live_contentops.capital_chronicle_public_manifest_v1 import PublicMainFileSource
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import validate_latest_report_bytes, canonical_bytes
    pointer = json.loads((ROOT / "provider_resume_binding.json").read_bytes())
    pointer["public_export_root"] = str(ROOT / "main_public_handoff/public-handoff")
    source = PublicMainFileSource(pointer)
    source.refresh(cutoff_utc="2026-10-21T00:00:00Z")
    bundle = source.bundle(source.manifest["latest_by_asset"]["UKOIL"])
    env, public = json.loads(bundle["envelope"]), json.loads(bundle["public_export"])
    c = env["public_safe_claims"][1]
    descriptor = controlled_descriptor(env, c)
    public["latest_reports"][0]["public_research_descriptors"] = [descriptor]
    public["projection_sha256"] = sha256_of({k: v for k, v in public.items() if k != "projection_sha256"})
    raw = canonical_bytes(public)
    admitted = validate_latest_report_bytes(bundle["envelope"], expected_cutoff_utc="2026-10-21T00:00:00Z",
        envelope_schema_bytes=bundle["envelope_schema"], public_export_bytes=raw,
        producer_binding={**bundle["binding"], "public_report_raw_sha256": hashlib.sha256(raw).hexdigest()})
    assert admitted["status"] == "ADMITTED"  # Labelled consumer contract, not a new real Main report.
    assert admitted["public_research_descriptors"][c["claim_id"]] == descriptor
    pack = _source_pack([report_document(admitted)])
    matched = next(c for c in pack[0]["report_lineage"]["claims"] if c["claim_id"] == descriptor["claim_id"])
    assert matched["research_semantics"]["probability_descriptor"] == descriptor
    assert descriptor["reader_disclosure"] in pack[0]["canonical_content_text"]


def test_writer_cannot_attach_self_certified_descriptor_to_legacy_article():
    g, output = retained()
    output["article"]["public_research_descriptors"] = [{"reader_disclosure": "Not a permitted producer descriptor"}]
    article, _ = _validate_article_against_source_pack(output, g["source_pack"], epistemic_state=g["epistemic_state"])
    assert "public_research_descriptors" not in article


def test_same_release_components_keep_distinct_claims_without_independence_credit():
    g, _ = retained()
    lineage = g["source_pack"][0]["report_lineage"]
    admission = {**lineage, "source_report_sha256": lineage["report_sha256"]}
    contexts = [claim_semantics(admission, c) for c in lineage["claims"]]
    assert len({s["dependence"]["component_claim_hash"] for s in contexts}) == len(contexts)
    assert len({tuple(s["dependence"]["source_hashes"]) for s in contexts}) < len(contexts)
    assert all(s["dependence"]["independence"] == "NOT_ESTABLISHED" for s in contexts)


def test_descriptor_withdrawal_invalidates_existing_prepared_review_without_rewriting(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker, canonical_bytes
    from live_contentops.contentops_editorial_desk_v1 import record_story_source_review
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.native_desktop_editorial_v1 import prepare_reviewed_handoff
    c, _, context = descriptor_context()
    store = ContentOpsDurableStore(tmp_path / "control.sqlite3")
    store.create_work_item(story_id="control", work_item_id="control", title="Labelled consumer control", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    value = {"article_identity": "a" * 64, "report_id": context["report_id"], "qualified_article_count": 1,
        "model_execution_state": "NATIVE_DESKTOP_REQUEST_RETURN",
        "article": {"title": "Labelled consumer control", "substack_body_markdown": "Original text remains immutable."},
        "evidence": [{"report_lineage": {"claims": [{**c, "research_semantics": context}]}}]}
    key = "cc-editorial-final-" + sha256_of("control")
    store.register_outbox_message(message_id=key, work_item_id="control", destination="internal:cc-report-simple-result",
        payload=canonical_bytes(value).decode(), status="EDITORIAL_INTERNAL")
    main = {"report_id": context["report_id"], "receipt_id": "control-main", "status": "ADMITTED",
        "known_at_cutoff_utc": "2026-10-19T12:25:00Z", "claims": [c], "public_research_descriptors": {}}
    monkeypatch.setattr(LatestReportDeliveryTracker, "receipts", lambda self: [main])
    args = dict(run_id="control", article_identity="a" * 64, review_operation_id="descriptor-withdrawal",
        research=SimpleNamespace(revision="control-only", records={}), source_ids=[],
        attempts=[{"status": "PASS", "url": "urn:labelled-engineering-control"}], cutoff_utc="2026-10-21T00:00:00Z",
        reason="Exact descriptor removed although claim prose remains unchanged.", main_receipt_id="control-main")
    review = record_story_source_review(store, **args)
    assert review["decision"] == "CORRECTION_OR_WITHDRAWAL"
    assert review["changed_research_descriptor_claim_ids"] == [c["claim_id"]]
    assert review["invalidates_prepared_review"] is True
    assert record_story_source_review(store, **args) == review
    with pytest.raises(ValueError, match="PREPARED_REVIEW_INVALIDATED"):
        prepare_reviewed_handoff(store, run_id="control", output_dir=tmp_path)
    assert json.loads(store.get_outbox_message(key)["payload"]) == value
