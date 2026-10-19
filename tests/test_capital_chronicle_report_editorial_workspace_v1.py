"""Exact Main input + injected output controls; no fresh model/external-write credit."""

import json
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    LatestReportDeliveryTracker,
    canonical_bytes,
    sha256_of,
    validate_latest_report_bytes,
    run_admitted_report_through_simple,
)
from live_contentops.capital_chronicle_report_editorial_workspace_v1 import (
    report_document,
    report_scope_notice,
    report_workspace_projection,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

ROOT = Path(__file__).parent / "fixtures/main_goal17_report/producer_v2"
BINDING = json.loads((ROOT / "producer_binding.json").read_bytes())
NOW = BINDING["observed_at_utc"]


def admit(prefix="", envelope=None, report=None):
    return validate_latest_report_bytes(
        canonical_bytes(envelope)
        if envelope
        else (ROOT / (prefix + "envelope.json")).read_bytes(),
        report_bytes=[
            canonical_bytes(report)
            if report
            else (ROOT / (prefix + "report.json")).read_bytes()
        ],
        expected_cutoff_utc=NOW,
        now_utc=NOW,
        envelope_schema_bytes=(
            ROOT / "CapitalChronicleLatestAnalysisReportEnvelopeV1.schema.json"
        ).read_bytes(),
        report_schema_bytes=(
            ROOT / "CapitalChronicleAssetAnalysisReportV1.schema.json"
        ).read_bytes(),
        producer_binding=BINDING,
    )


def reseal(envelope, report=None):
    if report is not None:
        report["report_sha256"] = sha256_of(
            {k: v for k, v in report.items() if k != "report_sha256"}
        )
        envelope["report_sha256"] = report["report_sha256"]
    envelope["event_id"] = "report-event:" + sha256_of(
        {
            k: envelope[k]
            for k in (
                "report_id",
                "report_version",
                "report_sha256",
                "change_kind",
                "changed_claim_ids",
            )
        }
    )
    envelope["envelope_sha256"] = sha256_of(
        {k: v for k, v in envelope.items() if k != "envelope_sha256"}
    )


def delta(kind, withdraw=False):
    """Resealed lifecycle test control, never a newly produced Main report."""
    e = json.loads((ROOT / "envelope.json").read_bytes())
    r = json.loads((ROOT / "report.json").read_bytes())
    for obj in (e, r):
        obj["report_version"] = 3
        obj["parent_report_sha256"] = r["report_sha256"]
        obj["supersedes_report_id"] = r["report_id"]
    e["change_kind"] = kind
    e["changed_claim_ids"] = []
    e["content_eligibility"] = (
        "NO_MATERIAL_CHANGE"
        if kind == "NO_MATERIAL_CHANGE"
        else "BLOCKED_NO_PUBLIC_SAFE_CLAIM"
    )
    if withdraw:
        e["public_safe_claims"] = r["claims"] = []
        e["hold_conditions"] = e["invalidation_conditions"] = []
        for h in e["horizon_blocks"]:
            h["outlook"] = "NO_PUBLIC_SAFE_OUTLOOK"
    reseal(e, r)
    return admit(envelope=e, report=r)


@pytest.fixture
def tracker(tmp_path):
    tracker = LatestReportDeliveryTracker(
        ContentOpsDurableStore(tmp_path / "editorial.sqlite3")
    )
    tracker.consume(admit("parent_"), receipt_id="v1")
    return tracker


def controlled_writer(calls):
    """Inject strict synthetic writer output; inspect actual Simple governed inputs."""

    def invoke(**kwargs):
        calls.append(kwargs["logical_invocation_id"])
        g = kwargs["governed_input"]
        receipt = {
            "selected_model": "vx/gemini-3.5-flash(high)",
            "total_attempts": 0,
            "replay_only": True,
            "model_identity_provider_verifiable": False,
        }
        if "candidates" in g:
            return {
                "schema_version": "contentops.v1_simple_gemini_selection.v2",
                "status": "SELECT_CANDIDATE_PLAN",
                "ordered_candidate_plan": [
                    {
                        "candidate_id": g["candidates"][0]["candidate_id"],
                        "article_mode": "DATA_OR_DOCUMENT_LENS",
                        "selection_rationale": "Synthetic output tests the pinned Main input path.",
                        "research_queries": [
                            "Examine the dated report and its limitations"
                        ],
                    }
                ],
                "selection_summary": "Synthetic control only.",
                "public_write_attempted": False,
            }, receipt
        source = g["source_pack"][0]
        claims = source["report_lineage"]["claims"]
        label = g["epistemic_state"]["reader_visible_epistemic_label"]
        notice = g["epistemic_state"]["report_scope_notice"]
        article = {
            "title": "Capital Chronicle report: weekly gas injection",
            "dek": label + ". The weekly injection leaves a seasonal balance question.",
            "search_title": "Capital Chronicle report: gas stocks and the next release",
            "meta_description": "Capital Chronicle analysis: the weekly refill alone cannot establish a market surprise.",
            "social_hook": "Capital Chronicle report: the next weekly release tests the tightening watch.",
            "substack_body_markdown": "\n\n".join(
                [f"{label}. {c['text']} [[SOURCE:SOURCE_1]]" for c in claims]
                + [notice + " [[SOURCE:SOURCE_1]]"]
            ),
        }
        bindings = [
            {
                "claim_id": "metadata-" + k,
                "claim_text": v,
                "claim_kind": "FACT",
                "source_id": "SOURCE_1",
                "support_excerpt": claims[0]["text"],
                "attribution_required": True,
            }
            for k, v in article.items()
            if k != "substack_body_markdown"
        ]
        bindings += [
            {
                "claim_id": c["claim_id"],
                "claim_text": c["text"],
                "claim_kind": "FACT",
                "source_id": "SOURCE_1",
                "support_excerpt": c["text"],
                "attribution_required": True,
            }
            for c in claims
        ]
        return {
            "schema_version": "contentops.v1_simple_gemini_article.v1",
            "article": article,
            "cited_sources": [
                {
                    "source_id": "SOURCE_1",
                    "url": source["url"],
                    "publisher": "Capital Chronicle",
                    "published_at_utc": source["published_at_utc"],
                }
            ],
            "material_claim_bindings": bindings,
            "public_write_attempted": False,
        }, receipt

    return invoke


def run(tracker, tmp_path, receipt="v2", admission=None, calls=None):
    return run_admitted_report_through_simple(
        admission or admit(),
        tracker=tracker,
        receipt_id=receipt,
        output_dir=tmp_path / receipt,
        cutoff_utc=NOW,
        llm_invoke=controlled_writer(calls if calls is not None else []),
    )


def test_resealed_poison_cannot_replace_durable_latest_or_ui(tracker, tmp_path):
    tracker.consume(admit(), receipt_id="v2")
    e = json.loads((ROOT / "envelope.json").read_bytes())
    e["report_version"] = 102
    reseal(e)
    bad = admit(envelope=e)
    assert bad["status"] == "BLOCKED"
    tracker.consume(bad, receipt_id="poison")
    projection = report_workspace_projection(tracker.store.list_outbox_messages())
    assert projection["latest_report"]["report_version"] == 2
    assert tracker.prepare_input("v2", output_dir=tmp_path, cutoff_utc=NOW)


@pytest.mark.parametrize(
    "key,value",
    [
        ("report_id", "wrong-id"),
        ("report_version", 102),
        ("run_id", "wrong-run"),
        ("parent_report_sha256", "f" * 64),
        ("supersedes_report_id", "wrong-parent"),
        ("generated_at_utc", "2026-10-18T13:51:00Z"),
        ("known_at_cutoff_utc", "2026-10-18T13:04:00Z"),
        ("as_of_utc", "2026-10-18T12:00:00Z"),
        ("asset_ids", ["XNGUSD", "BTCUSD"]),
        ("affected_symbols", ["BTCUSD"]),
        (
            "source_snapshot",
            {"catalog_sha256": "f" * 64, "evidence_snapshot_sha256": "f" * 64},
        ),
    ],
)
def test_all_resealed_identity_and_clock_poison_is_blocked(key, value):
    e = json.loads((ROOT / "envelope.json").read_bytes())
    e[key] = value
    reseal(e)
    assert admit(envelope=e)["status"] == "BLOCKED"


def test_derived_report_hash_and_locator_are_distinct_from_underlying_capture():
    import hashlib

    a = admit()
    doc = report_document(a)
    assert (
        doc["canonical_content_sha256"]
        == hashlib.sha256(doc["canonical_content_text"].encode()).hexdigest()
    )
    assert "/blob/" + BINDING["producer_commit"] + "/" in doc["source_url"]
    assert (
        doc["canonical_content_sha256"] != a["claims"][0]["evidence"][0]["source_hash"]
    )
    assert doc["retrieval_method"] == "DERIVED_SEALED_MAIN_PUBLIC_PROJECTION"


def test_integrated_main_to_article_eight_previews_and_idempotent_resume(
    tracker, tmp_path
):
    tracker.consume(admit(), receipt_id="v2")
    calls = []
    result = run(tracker, tmp_path, calls=calls)
    assert result["classification"] == "DRAFT_READY", result.get("simple_result")
    assert len(calls) == 2
    assert result["writer_invoked"] is False
    assert result["model_execution_state"] == "INJECTED_REPLAY_ONLY"
    assert len(result["previews"]) == 8
    assert result["canonical_public_url"] is None
    assert all(p["claim_lineage"] for p in result["previews"])
    for p in result["previews"]:
        payload = p["payload"]
        visible = " ".join(
            [str(payload.get("text", "")), *payload.get("reply_texts", [])]
        )
        assert report_scope_notice(admit()) in " ".join(visible.split())
    again = run(tracker, tmp_path, calls=calls)
    assert again == result
    assert len(calls) == 2
    view = report_workspace_projection(tracker.store.list_outbox_messages())
    assert view["article"]["title"] == result["article"]["title"]
    assert len(view["previews"]) == 8


def test_compiler_crash_resumes_without_repeating_successful_model_or_source(
    tracker, tmp_path, monkeypatch
):
    from live_contentops import eight_platform_substack_first_pipeline_v1 as facade

    original = facade.build_native_derivative_payloads
    tracker.consume(admit(), receipt_id="v2")
    calls = []
    monkeypatch.setattr(
        facade,
        "build_native_derivative_payloads",
        lambda **k: (_ for _ in ()).throw(RuntimeError("controlled-compiler-crash")),
    )
    with pytest.raises(RuntimeError, match="controlled-compiler-crash"):
        run(tracker, tmp_path, calls=calls)
    assert len(calls) == 2
    monkeypatch.setattr(facade, "build_native_derivative_payloads", original)
    result = run(tracker, tmp_path, calls=calls)
    assert result["classification"] == "DRAFT_READY", result.get("simple_result")
    assert len(calls) == 2


def test_correction_after_existing_article_and_withdrawal_link_obsolete_previews(
    tracker, tmp_path
):
    calls = []
    prior = run(
        tracker, tmp_path, receipt="v1", admission=admit("parent_"), calls=calls
    )
    assert prior["classification"] == "DRAFT_READY", prior.get("simple_result")
    tracker.consume(admit(), receipt_id="v2")
    interim = report_workspace_projection(tracker.store.list_outbox_messages())
    assert interim["article"] is None
    assert interim["history"][0]["article_identity"] == prior["article_identity"]
    assert len(interim["history"][0]["preview_ids"]) == 8
    current = run(tracker, tmp_path, calls=calls)
    assert current["classification"] == "DRAFT_READY"
    assert (
        current["affected_drafts"][0]["article_identity"] == prior["article_identity"]
    )
    withdrawn = delta("INVALIDATION", withdraw=True)
    assert withdrawn["status"] == "ADMITTED", withdrawn["blockers"]
    tracker.consume(withdrawn, receipt_id="withdrawn-v3")
    result = run(
        tracker, tmp_path, receipt="withdrawn-v3", admission=withdrawn, calls=calls
    )
    assert result["classification"] == "INVALIDATION_WITHDRAWAL_NOOP"
    view = report_workspace_projection(tracker.store.list_outbox_messages())
    assert view["article"] is None and view["previews"] == []
    assert view["named_blocker"] == "CLAIMS_WITHDRAWN"
    assert {r["state"] for r in view["history"]} == {"WITHDRAWN"}
    assert len(calls) == 4


def test_no_change_keeps_existing_draft_and_pending_input_without_writer(
    tracker, tmp_path
):
    tracker.consume(admit(), receipt_id="v2")
    calls = []
    current = run(tracker, tmp_path, calls=calls)
    unchanged = delta("NO_MATERIAL_CHANGE")
    assert unchanged["status"] == "ADMITTED", unchanged["blockers"]
    tracker.consume(unchanged, receipt_id="no-change-v3")
    result = run(
        tracker, tmp_path, receipt="no-change-v3", admission=unchanged, calls=calls
    )
    assert result["classification"] == "NO_MATERIAL_CHANGE_NOOP"
    view = report_workspace_projection(tracker.store.list_outbox_messages())
    assert view["latest_report"]["report_version"] == 3
    assert view["article"] == current["article"]
    assert len(view["previews"]) == 8 and view["history"] == []
    assert len(calls) == 2


def test_pause_result_can_resume_into_same_receipt_without_overwriting_history(
    tracker, tmp_path, monkeypatch
):
    import live_contentops.capital_chronicle_report_editorial_workspace_v1 as workspace

    tracker.consume(admit(), receipt_id="v2")
    monkeypatch.setattr(workspace, "llm_operator_pause_active", lambda: True)
    paused = run_admitted_report_through_simple(
        admit(),
        tracker=tracker,
        receipt_id="v2",
        output_dir=tmp_path / "v2",
        cutoff_utc=NOW,
    )
    assert paused["exact_next_blocker"] == "LLM_OPERATOR_PAUSED"
    result = run(tracker, tmp_path)
    assert result["classification"] == "DRAFT_READY"
    assert (
        report_workspace_projection(tracker.store.list_outbox_messages())[
            "latest_simple_result"
        ]["classification"]
        == "DRAFT_READY"
    )


def test_unrecorded_writer_result_fails_closed_without_duplicate_model_call(
    tracker, tmp_path, monkeypatch
):
    import live_contentops.capital_chronicle_report_editorial_workspace_v1 as workspace

    tracker.consume(admit(), receipt_id="v2")
    monkeypatch.setattr(workspace, "llm_operator_pause_active", lambda: True)
    paused = run_admitted_report_through_simple(
        admit(), tracker=tracker, receipt_id="v2", output_dir=tmp_path / "v2", cutoff_utc=NOW
    )
    assert paused["exact_next_blocker"] == "LLM_OPERATOR_PAUSED"
    calls = []
    control = controlled_writer(calls)

    def crash(**kwargs):
        output = control(**kwargs)
        if str(kwargs["logical_invocation_id"]).endswith(":write"):
            raise RuntimeError("crash-after-provider-before-local-result")
        return output

    with pytest.raises(RuntimeError, match="crash-after-provider"):
        run_admitted_report_through_simple(
            admit(),
            tracker=tracker,
            receipt_id="v2",
            output_dir=tmp_path / "v2",
            cutoff_utc=NOW,
            llm_invoke=crash,
        )
    blocked = run(tracker, tmp_path, calls=calls)
    assert blocked["exact_next_blocker"] == "EDITORIAL_STEP_RESULT_NOT_RECORDED:write"
    assert len(calls) == 2
    rows = tracker.store.list_outbox_messages()
    for order in (rows, list(reversed(rows))):
        assert report_workspace_projection(order)["named_blocker"] == blocked["exact_next_blocker"]


def test_latest_input_cannot_come_from_another_report_with_the_same_version(tracker, tmp_path):
    tracker.consume(admit(), receipt_id="v2")
    current = tracker.prepare_input("v2", output_dir=tmp_path, cutoff_utc=NOW)
    rows = tracker.store.list_outbox_messages()
    input_row = next(row for row in rows if row["destination"] == "internal:cc-report-editorial-input")
    other = json.loads(input_row["payload"])
    other["brief"]["report_id"] = "asset-report:other"
    foreign = {**input_row, "message_id": "other-input", "payload": json.dumps(other)}
    view = report_workspace_projection([foreign, *rows])
    assert view["latest_editorial_input"]["brief"] == current["brief"]
    legacy = json.loads(input_row["payload"])
    legacy["brief"].pop("report_id")
    legacy_row = {**input_row, "payload": json.dumps(legacy)}
    legacy_view = report_workspace_projection([foreign, legacy_row, *[r for r in rows if r is not input_row]])
    assert legacy_view["latest_editorial_input"]["brief"]["correction_lineage"]["report_id"] == current["brief"]["report_id"]


def test_source_budget_restores_consumed_requests_without_reset():
    from live_contentops.v1_simple_evidence_resolver_v1 import (
        SimpleFirstPartyAwareEvidenceResolver,
    )

    resolver = SimpleFirstPartyAwareEvidenceResolver(evaluation_as_of_utc=NOW)
    resolver.resume_request_count(4)
    assert resolver.request_count == 4
    with pytest.raises(ValueError, match="resume_budget_invalid"):
        resolver.resume_request_count(7)
    with pytest.raises(ValueError, match="resume_budget_invalid"):
        resolver.resume_request_count(0)


def test_independent_intake_stays_in_simple_selection_and_uses_its_own_evidence(
    tracker, tmp_path, monkeypatch
):
    from tests.test_v1_simple_gemini_newsroom_v1 import (
        _headlines,
        _selection,
        _article_output,
        _receipt,
        _evidence_result,
    )
    import live_contentops.v1_simple_gemini_newsroom_v1 as simple

    tracker.consume(admit(), receipt_id="v2")
    evidence_requests = []

    class Resolver:
        def resume_request_count(self, used):
            assert used == 0

        def __call__(self, request):
            evidence_requests.append(request)
            return _evidence_result()

    monkeypatch.setattr(simple, "_default_evidence_loader", lambda *a, **k: Resolver())

    def model(**kwargs):
        g = kwargs["governed_input"]
        if "candidates" in g:
            assert len(g["candidates"]) == 2
            candidate = next(
                c
                for c in g["candidates"]
                if not c["headline_id"].startswith("cc-report:")
            )
            return _selection(candidate["candidate_id"]), _receipt(
                kwargs["role_task_id"]
            )
        assert not g["source_pack"][0].get("report_lineage")
        return _article_output(), _receipt(kwargs["role_task_id"])

    result = run_admitted_report_through_simple(
        admit(),
        tracker=tracker,
        receipt_id="v2",
        output_dir=tmp_path / "v2",
        cutoff_utc=NOW,
        rolling_input=_headlines(1),
        llm_invoke=model,
    )
    assert result["classification"] == "INDEPENDENT_NEWS_DRAFT"
    assert result["exact_next_blocker"] is None
    assert result["draft_count"] == 1 and result["report_id"] is None
    assert len(result["previews"]) == 8  # independent draft, zero Main report credit
    assert len(evidence_requests) == 1
