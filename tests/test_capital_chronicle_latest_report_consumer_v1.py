"""Synthetic controls plus an exact local Main export rejection/readback.

Synthetic success cases deliberately disable the absent upstream machine schema.
They establish consumer mechanics, never real Main admission or writer execution.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    CANONICALIZATION,
    CONTRACT_REVISION,
    EDITORIAL_INPUT,
    INBOX,
    MAIN_ENVELOPE_SCHEMA,
    MAIN_REPORT_SCHEMA,
    LatestReportConsumerError,
    LatestReportDeliveryTracker,
    NeoNamedGapRecovery,
    build_report_editorial_input,
    canonical_bytes,
    resolve_report_research_gaps,
    sha256_of,
    validate_latest_report_bytes,
)
from live_contentops.durable_operational_store_v1 import (
    ContentOpsDurableStore,
    LeaseConflictError,
)

NOW = "2026-10-18T12:45:00Z"
CUTOFF = "2026-10-18T12:40:00Z"
FIXTURES = Path(__file__).parent / "fixtures" / "main_goal17_report"


def seal(value, field):
    value[field] = sha256_of({key: item for key, item in value.items() if key != field})
    return value


def make_bundle(version=1, change="NEW_REPORT", event="same-event", parent=None):
    evidence = {
        "evidence_id": "public-source-1",
        "source_identity": "https://www.eia.gov/naturalgas/weekly/",
        "source_hash": "a" * 64,
        "known_at_utc": "2026-10-18T10:00:00Z",
        "observation_time_utc": "2026-10-18T10:00:00Z",
        "retrieval_time_utc": "2026-10-18T10:30:00Z",
        "rights_state": "PUBLIC_DOMAIN_EIA_ORIGINAL_WITH_ATTRIBUTION",
        "freshness_state": "CURRENT",
        "exact_or_proxy": "PROXY",
        "query_id": "test-query",
        "query_sha256": "b" * 64,
        "rights_evidence_sha256": "c" * 64,
        "public_claim_use": True,
        "pit_state": "PASS",
    }
    claim = {
        "claim_id": "XNGUSD:context",
        "text": "The admitted report describes supply conditions as a conditional influence on prices.",
        "evidence_refs": [evidence["evidence_id"]],
        "epistemic_layer": "CC_ANALYSIS",
        "exact_or_proxy": "PROXY",
        "basis_risk": "Regional gas context does not establish Exness CFD direction.",
        "rights_state": "PUBLIC_DOMAIN_EIA_ORIGINAL_WITH_ATTRIBUTION",
        "public_safe": True,
    }
    claim["claim_hash"] = sha256_of(claim)
    report = {
        "schema": MAIN_REPORT_SCHEMA,
        "version": "1.0.0",
        "contract_revision": CONTRACT_REVISION,
        "canonicalization": CANONICALIZATION,
        "authority_flags": {"publication_authority": False, "external_effects": 0},
        "report_id": "latest-report-v1",
        "case": "FOUNDATION_DEEP_ASSET_ANALYSIS",
        "run_id": "test-control-run",
        "report_version": version,
        "asset": {"asset_id": "XNGUSD"},
        "known_at_cutoff_utc": "2026-10-18T12:00:00Z",
        "as_of_utc": "2026-10-18T12:00:00Z",
        "generated_at_utc": "2026-10-18T12:10:00Z",
        "claims": [claim],
        "evidence": [evidence],
    }
    envelope = {
        "schema": MAIN_ENVELOPE_SCHEMA,
        "version": "1.0.0",
        "contract_revision": CONTRACT_REVISION,
        "canonicalization": CANONICALIZATION,
        "authority_flags": deepcopy(report["authority_flags"]),
        "report_id": "latest-report-v1",
        "report_version": version,
        "event_id": event,
        "case": "FOUNDATION_DEEP_ASSET_ANALYSIS",
        "change_kind": change,
        "supersedes_report_id": parent,
        "parent_report_sha256": None,
        "supersedes_envelope_id": None,
        "asset_ids": ["XNGUSD"],
        "affected_symbols": ["XNGUSD"],
        "horizon_blocks": [
            {"horizon": "swing", "direction": "CONDITIONAL", "trading_sessions": 5}
        ],
        "as_of_utc": "2026-10-18T12:00:00Z",
        "generated_at_utc": "2026-10-18T12:10:00Z",
        "known_at_cutoff_utc": "2026-10-18T12:00:00Z",
        "source_snapshot": {"catalog_sha256": "b" * 64},
        "run_id": "test-control-run",
        "report_sha256": None,
        "public_safe_claims": [deepcopy(claim)],
        "limitations": ["No current CFD direction is established."],
        "hold_conditions": ["Review if supply conditions contradict the thesis."],
        "invalidation_conditions": [],
        "content_eligibility": "ELIGIBLE_EDITORIAL_REVIEW",
        "changed_claim_ids": [claim["claim_id"]],
        "materiality_rationale": "The report changes its conditional supply assessment.",
        "private_context_excluded": True,
        "publication_authority": False,
    }
    if parent:
        envelope["parent_report_sha256"] = make_bundle(version=version - 1)[1][
            "report_sha256"
        ]
    return refresh(envelope, report)


def refresh(envelope, report):
    keys = (
        "evidence_id",
        "source_identity",
        "source_url",
        "source_hash",
        "query_sha256",
        "observation_time_utc",
        "retrieval_time_utc",
        "known_at_utc",
        "unit",
        "currency",
        "rights_evidence_sha256",
    )
    for claim in report["claims"]:
        claim["supporting_evidence"] = [
            {key: row.get(key) for key in keys}
            for row in report["evidence"]
            if row["evidence_id"] in claim["evidence_refs"]
        ]
        claim["claim_hash"] = sha256_of(
            {key: item for key, item in claim.items() if key != "claim_hash"}
        )
    envelope["public_safe_claims"] = deepcopy(report["claims"])
    seal(report, "report_sha256")
    envelope["report_sha256"] = report["report_sha256"]
    identity = {
        key: envelope[key]
        for key in (
            "report_id",
            "report_version",
            "report_sha256",
            "change_kind",
            "changed_claim_ids",
        )
    }
    envelope["event_id"] = "report-event:" + sha256_of(identity)
    seal(envelope, "envelope_sha256")
    return envelope, report


def validate(envelope, report, **kwargs):
    return validate_latest_report_bytes(
        canonical_bytes(envelope),
        report_bytes=[canonical_bytes(report)],
        expected_cutoff_utc=CUTOFF,
        now_utc=NOW,
        require_machine_schema=False,
        **kwargs,
    )


@pytest.fixture
def tracker(tmp_path):
    return LatestReportDeliveryTracker(
        ContentOpsDurableStore(
            tmp_path / "disposable.sqlite3",
            now_fn=lambda: datetime(2026, 10, 18, 12, 45, tzinfo=timezone.utc),
        )
    )


def test_control_seals_exact_main_flat_wire_and_claim_formula():
    envelope, report = make_bundle()
    result = validate(envelope, report)
    assert result["status"] == "ADMITTED"
    assert result["machine_schema_verified"] is False
    assert result["claims"][0]["layer"] == "CAPITAL_CHRONICLE_ANALYSIS"
    assert result["claims"][0]["evidence"][0]["source_hash"] == "a" * 64


def test_live_default_rejects_missing_main_machine_schema():
    envelope, report = make_bundle()
    result = validate_latest_report_bytes(
        canonical_bytes(envelope),
        report_bytes=[canonical_bytes(report)],
        expected_cutoff_utc=CUTOFF,
        now_utc=NOW,
    )
    assert result["status"] == "BLOCKED"
    assert "ENVELOPE_MAIN_SCHEMA_EXPORT_UNAVAILABLE" in result["blockers"]


@pytest.mark.parametrize(
    "mutate,expected",
    [
        (
            lambda e, r: e.update(canonicalization="DIFFERENT_HASH_RULE"),
            "CANONICALIZATION_MISMATCH",
        ),
        (lambda e, r: e.update(report_version=True), "REPORT_VERSION_INVALID"),
        (
            lambda e, r: e.update(generated_at_utc="2026-10-18T18:00:00Z"),
            "REPORT_CLOCK_IN_FUTURE",
        ),
        (
            lambda e, r: e.update(known_at_cutoff_utc="2026-10-18T12:44:00Z"),
            "REPORT_CUTOFF_ORDER_INVALID",
        ),
        (
            lambda e, r: e.update(publication_authority=True),
            "PUBLIC_PROJECTION_FLAGS_INVALID",
        ),
        (lambda e, r: e.update(run_id=None), "ASSET_RUN_SNAPSHOT_IDENTITY_REQUIRED"),
    ],
)
def test_wire_clock_authority_controls(mutate, expected):
    envelope, report = make_bundle()
    mutate(envelope, report)
    seal(envelope, "envelope_sha256")
    result = validate(envelope, report)
    assert expected in result["blockers"]


def test_tampered_report_and_missing_body_cannot_use_envelope_claims():
    envelope, report = make_bundle()
    report["evidence"][0]["rights_state"] = "RESTRICTED"
    result = validate(envelope, report)
    assert "REPORT_SEALED_HASH_MISMATCH" in result["blockers"]
    result = validate_latest_report_bytes(
        canonical_bytes(envelope),
        expected_cutoff_utc=CUTOFF,
        now_utc=NOW,
        require_machine_schema=False,
    )
    assert "HASH_BOUND_REPORT_BODY_MISSING" in result["blockers"]


@pytest.mark.parametrize(
    "field,value,expected",
    [
        ("rights_state", "INTERNAL_ANALYSIS_ONLY", "EVIDENCE_PUBLIC_RIGHTS_BLOCKED"),
        ("source_hash", None, "SOURCE_IDENTITY_OR_HASH_MISSING"),
        ("known_at_utc", None, "EVIDENCE_PIT_CLOCK_UNAVAILABLE"),
        ("known_at_utc", "2026-10-18T15:00:00Z", "EVIDENCE_CLOCK_ORDER_INVALID"),
    ],
)
def test_evidence_binding_rights_and_pit_fail_closed(field, value, expected):
    envelope, report = make_bundle()
    report["evidence"][0][field] = value
    refresh(envelope, report)
    result = validate(envelope, report)
    assert result["status"] == "BLOCKED"
    assert any(expected in error for error in result["blockers"])


def test_optional_missing_claim_does_not_block_unrelated_article():
    envelope, report = make_bundle()
    result = validate(envelope, report, optional_claim_ids=["optional-missing"])
    assert result["status"] == "ADMITTED"
    assert result["missing_claims"] == ["optional-missing"]
    result = validate(envelope, report, required_claim_ids=["required-missing"])
    assert result["status"] == "BLOCKED"


def test_private_portfolio_and_credentials_are_not_copied_to_diagnostics():
    envelope, report = make_bundle()
    envelope["private_context"] = {"account_id": "DO_NOT_COPY_THIS"}
    result = validate(envelope, report)
    assert result["blockers"] == ["PRIVATE_CONTEXT_EXCLUDED"]
    assert "DO_NOT_COPY_THIS" not in json.dumps(result)
    with pytest.raises(LatestReportConsumerError):
        build_report_editorial_input(
            validate(*make_bundle()),
            output_dir="test",
            cutoff_utc=CUTOFF,
            rolling_input={"access_token": "hidden"},
        )


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'{"x":NaN}', b"[]", b"not json"])
def test_invalid_json_is_rejected(raw):
    with pytest.raises(LatestReportConsumerError):
        validate_latest_report_bytes(raw, expected_cutoff_utc=CUTOFF)


def test_durable_duplicates_older_equal_version_conflicts_and_counts(tracker):
    first = validate(*make_bundle(version=2))
    assert tracker.consume(first, receipt_id="first")["status"] == "ADMITTED"
    assert tracker.consume(first, receipt_id="duplicate")["status"] == "DUPLICATE_NOOP"
    assert (
        tracker.consume(validate(*make_bundle(version=1)), receipt_id="older")["status"]
        == "OUT_OF_ORDER_NOOP"
    )
    envelope, report = make_bundle(version=2)
    envelope["materiality_rationale"] = "Different bytes at an equal version."
    seal(envelope, "envelope_sha256")
    assert (
        tracker.consume(validate(envelope, report), receipt_id="conflict")["status"]
        == "CONFLICT_EQUAL_VERSION_DIFFERENT_BYTES"
    )
    assert tracker.counts()["no_ops"] == 2
    assert tracker.counts()["blocked_results"] == 1
    assert tracker.consume(first, receipt_id="first")["status"] == "ADMITTED"
    with pytest.raises(LatestReportConsumerError, match="RECEIPT_ID_CONFLICT"):
        tracker.consume(validate(envelope, report), receipt_id="first")


@pytest.mark.parametrize("change", ["CORRECTION", "INVALIDATION"])
def test_correction_invalidation_retains_history_and_supersedes_pending(
    tracker, change
):
    old = tracker.consume(validate(*make_bundle()), receipt_id="old")
    revised = tracker.consume(
        validate(*make_bundle(version=2, change=change, parent="latest-report-v1")),
        receipt_id="revised",
    )
    assert revised["status"] == "ADMITTED"
    assert revised["affected_prior_inputs"] == [old["message_id"]]
    assert (
        next(row for row in tracker.receipts() if row["receipt_id"] == "old")[
            "delivery_status"
        ]
        == "REPORT_SUPERSEDED"
    )
    with pytest.raises(LatestReportConsumerError, match="REPORT_NOT_DELIVERABLE"):
        tracker.prepare_input("old", output_dir="test", cutoff_utc=CUTOFF)
    assert len(tracker.receipts()) == 2


def test_missing_parent_is_durable_gap_and_no_change_never_calls_writer(tracker):
    assert (
        tracker.consume(
            validate(*make_bundle(version=2, change="CORRECTION", parent="unknown")),
            receipt_id="missing-parent",
        )["status"]
        == "LINEAGE_PARENT_NOT_RECEIVED"
    )
    record = tracker.consume(
        validate(*make_bundle(version=3, change="NO_MATERIAL_CHANGE")),
        receipt_id="no-change",
    )
    assert record["status"] == "NO_MATERIAL_CHANGE_NOOP"
    assert tracker.counts()["editorial_inputs"] == 0


def test_missed_delivery_and_crash_resume_uses_existing_outbox_without_writer(
    tracker, tmp_path, monkeypatch
):
    admission = validate(*make_bundle())
    tracker.consume(admission, receipt_id="delivery")
    original = tracker.store.set_outbox_status
    monkeypatch.setattr(
        tracker.store,
        "set_outbox_status",
        lambda *args: (_ for _ in ()).throw(RuntimeError("crash-after-input-commit")),
    )
    with pytest.raises(RuntimeError, match="crash-after-input"):
        tracker.prepare_input("delivery", output_dir=tmp_path, cutoff_utc=CUTOFF)
    monkeypatch.setattr(tracker.store, "set_outbox_status", original)
    reloaded = LatestReportDeliveryTracker(tracker.store)
    monkeypatch.setattr(
        "live_contentops.capital_chronicle_latest_report_consumer_v1.build_report_editorial_input",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must reuse input")),
    )
    result = reloaded.prepare_input("delivery", output_dir=tmp_path, cutoff_utc=CUTOFF)
    assert result["writer_invoked"] is False
    assert reloaded.counts()["editorial_inputs"] == 1
    assert reloaded.counts()["drafts"] == 0
    assert {row["destination"] for row in tracker.store.list_outbox_messages()} == {
        INBOX,
        EDITORIAL_INPUT,
    }


def test_consumer_uses_store_lease_for_concurrent_version_admission(tracker):
    lease = tracker.store.acquire_lease(
        "internal:cc-report-consume", "other-owner", ttl_seconds=60
    )
    with pytest.raises(LeaseConflictError):
        tracker.consume(validate(*make_bundle()), receipt_id="concurrent")
    tracker.store.release_lease(
        lease["lease_id"], "other-owner", lease["fencing_token"]
    )


def test_substantive_input_reaches_existing_simple_context_and_eight_intents(tmp_path):
    admission = validate(*make_bundle(change="THESIS_DELTA"))
    result = build_report_editorial_input(
        admission, output_dir=tmp_path, cutoff_utc=CUTOFF
    )
    args = result["simple_gemini_handoff"]["runner_arguments"]
    context = args["capital_chronicle_context"]
    assert (
        context["latest_analysis_report"]["claims"][0]["text"]
        == admission["claims"][0]["text"]
    )
    assert (
        context["editorial_brief"]["underlying_event_truth"]
        == "NOT_UPGRADED_BY_REPORT_IMPORT"
    )
    assert context["editorial_brief"]["sections"][0]["evidence_ids"] == [
        "public-source-1"
    ]
    assert len(result["derivative_intents"]) == 8
    assert result["compiled_derivative_count"] == result["draft_count"] == 0
    assert (
        result["simple_gemini_handoff"]["operation"] == "run_v1_simple_gemini_newsroom"
    )
    assert result["simple_gemini_handoff"]["invoked"] is False


def test_stale_context_is_dated_and_contradiction_stays_in_limits(tmp_path):
    envelope, report = make_bundle()
    report["evidence"][0]["freshness_state"] = "STALE"
    envelope["limitations"].append(
        "Competing explanation contradicts the supply thesis."
    )
    refresh(envelope, report)
    result = build_report_editorial_input(
        validate(envelope, report), output_dir=tmp_path, cutoff_utc=CUTOFF
    )
    assert result["brief"]["mode"] == "DATA_OR_DOCUMENT_LENS"
    assert "Competing explanation" in result["brief"]["limitations"][-1]


def test_named_gap_is_db_first_and_neo_is_only_used_after_missing_read():
    calls = []
    need = {
        "need_id": "gap-1",
        "data_class": "public_context",
        "required_fields": ["rendered_context"],
        "pit_required": True,
        "browseros_allowed": True,
        "browseros_url": "https://www.eia.gov/naturalgas/weekly/",
        "permitted_routes": ["EXISTING_MARKET_READ_MODEL", "BROWSEROS_READ_ONLY"],
        "exact_or_proxy": "PROXY_ALLOWED",
    }
    row = {
        "need_id": "gap-1",
        "source_identity": "retained",
        "source_hash": "a" * 64,
        "values": {"rendered_context": "Already retained"},
    }

    def recovery(need):
        calls.append("neo")

    result = resolve_report_research_gaps(
        request_id="gap",
        cutoff_utc=CUTOFF,
        needs=[need],
        source_layers={"read_models": [row]},
        browser_recovery=recovery,
    )
    assert (
        result["resolution"]["resolutions"][0]["route"] == "EXISTING_MARKET_READ_MODEL"
    )
    assert calls == []
    assert result["fresh_evidence_requires_new_main_version"] is True


def test_real_neo_adapter_startup_mapping_has_explicit_context_scope():
    class Preflight:
        def run(self, **kwargs):
            assert kwargs == {"auto_open": True, "reconnect_once": True}
            return {"status": "PASS"}

    def capture(url, timeout, limit):
        assert url.startswith("https://www.eia.gov/")
        return {
            "final_url": url,
            "observed_at_utc": NOW,
            "canonical_content_text": "Synthetic captured context",
            "canonical_content_sha256": "a" * 64,
            "tool_policy": {"allowed_tools_used": ["name_session", "tabs", "read"]},
            "browser_runtime": {"server_name": "BrowserOS Neo"},
        }

    recovery = NeoNamedGapRecovery(
        allowed_hosts=["www.eia.gov"], preflight=Preflight(), recovery=capture
    )
    result = recovery(
        {
            "required_fields": ["rendered_context"],
            "browseros_url": "https://www.eia.gov/naturalgas/weekly/",
        }
    )
    assert result["values"]["rendered_context"] == "Synthetic captured context"
    assert result["exact_or_proxy"] == "PROXY"
    with pytest.raises(LatestReportConsumerError, match="BUDGET"):
        recovery(
            {
                "required_fields": ["rendered_context"],
                "browseros_url": "https://www.eia.gov/",
            }
        )


def test_exact_main_export_snapshot_cannot_become_synthetic_success():
    metadata = json.loads((FIXTURES / "source_identity.json").read_text())
    envelope = (FIXTURES / "latest_analysis_report_envelope.json").read_bytes()
    reports = (FIXTURES / "envelope_reports.jsonl").read_bytes().splitlines()
    import hashlib

    assert hashlib.sha256(envelope).hexdigest() == metadata["envelope_raw_sha256"]
    result = validate_latest_report_bytes(
        envelope, report_bytes=reports, expected_cutoff_utc=CUTOFF, now_utc=NOW
    )
    assert result["status"] == "BLOCKED"
    assert "REPORT_CLOCK_IN_FUTURE" in result["blockers"]
    assert "ENVELOPE_MAIN_SCHEMA_EXPORT_UNAVAILABLE" in result["blockers"]
    assert metadata["source_state"] == "MAIN_LOCAL_UNCOMMITTED_EXPORT"


def test_changed_scope_and_evidence_projection_are_not_accepted():
    envelope, report = make_bundle()
    envelope["asset_ids"] = ["DIFFERENT_ASSET"]
    seal(envelope, "envelope_sha256")
    assert "REPORT_ASSET_SCOPE_MISMATCH" in validate(envelope, report)["blockers"]
    envelope, report = make_bundle()
    envelope["public_safe_claims"][0]["supporting_evidence"][0]["source_hash"] = (
        "f" * 64
    )
    envelope["public_safe_claims"][0]["claim_hash"] = sha256_of(
        {
            k: v
            for k, v in envelope["public_safe_claims"][0].items()
            if k != "claim_hash"
        }
    )
    seal(envelope, "envelope_sha256")
    result = validate(envelope, report)
    assert any("CLAIM_NOT_BOUND_TO_REPORT" in x for x in result["blockers"])


def test_corrected_parent_hash_must_match_received_report(tracker):
    tracker.consume(validate(*make_bundle()), receipt_id="parent")
    envelope, report = make_bundle(
        version=2, change="CORRECTION", parent="latest-report-v1"
    )
    envelope["parent_report_sha256"] = "f" * 64
    seal(envelope, "envelope_sha256")
    assert (
        tracker.consume(validate(envelope, report), receipt_id="wrong-parent-hash")[
            "status"
        ]
        == "LINEAGE_HASH_CONFLICT"
    )


def test_input_is_consumable_by_existing_writer_prompt_without_model_calls(tmp_path):
    from live_contentops.v1_simple_gemini_newsroom_v1 import _worker_prompt

    result = build_report_editorial_input(
        validate(*make_bundle()), output_dir=tmp_path, cutoff_utc=CUTOFF
    )
    args = result["simple_gemini_handoff"]["runner_arguments"]
    from live_contentops.v1_simple_gemini_newsroom_v1 import _candidate_packet

    candidates = _candidate_packet(args["rolling_input"], [])
    assert len(candidates) == 1
    assert candidates[0]["headline_text"].startswith("Capital Chronicle report update:")
    assert candidates[0]["public_source_urls"] == [
        "https://www.eia.gov/naturalgas/weekly/"
    ]
    prompt = _worker_prompt(
        {"capital_chronicle_context": args["capital_chronicle_context"]}
    )
    assert "The admitted report describes supply conditions" in prompt
    assert "Regional gas context does not establish Exness CFD direction" in prompt
    assert result["writer_invoked"] is False


def test_internal_report_outbox_cannot_be_dispatched_by_existing_coordinator(
    tracker, tmp_path
):
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator

    tracker.consume(validate(*make_bundle()), receipt_id="internal-only")
    tracker.prepare_input("internal-only", output_dir=tmp_path, cutoff_utc=CUTOFF)

    class ForbiddenTransport:
        def __getattr__(self, name):
            raise AssertionError("public transport must remain unreachable: " + name)

    coordinator = DurablePublicationCoordinator(
        store=tracker.store, transport_runtime=ForbiddenTransport()
    )
    result = coordinator.recover_pending()
    assert result["publish_calls"] == result["backlog_remaining"] == 0
    assert result["legacy_noncanonical_rows_skipped"] == 2


def test_schema_verifier_never_resolves_remote_references():
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
        _schema_errors,
    )

    schema = canonical_bytes(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$ref": "https://unrelated.invalid/private",
        }
    )
    assert _schema_errors({}, schema, "ENVELOPE") == [
        "ENVELOPE_EXTERNAL_SCHEMA_REFERENCE_FORBIDDEN"
    ]
