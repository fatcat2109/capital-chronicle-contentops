"""Durable draft-only adapter into Simple; no scheduler, store or publication owner."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from uuid import uuid4

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    EDITORIAL_INPUT,
    SIMPLE_RESULT,
    LatestReportConsumerError,
    LatestReportDeliveryTracker,
    canonical_bytes,
    sha256_of,
    _private,
    build_report_editorial_input,
)
from live_contentops.llm_operator_control_v1 import (
    llm_operator_pause_active,
    LLMOperatorPausedError,
)
from live_contentops.contentops_foundation_library_v1 import library_projection

STAGE = "internal:cc-report-editorial-stage"
SCHEMA = "contentops.cc_report_editorial_workspace.v1"
CURRENT = {"ADMITTED", "NO_MATERIAL_CHANGE_NOOP", "INVALIDATION_WITHDRAWAL_NOOP", "LINEAGE_ONLY_NOOP"}


def report_scope_notice(admission: Mapping[str, Any]) -> str:
    sessions = (
        "/".join(
            str(h["trading_sessions"])
            for h in admission.get("horizon_blocks", [])
            if h.get("trading_sessions")
        )
        or "unspecified"
    )
    return (
        "CC report / event unconfirmed. Facts, CC analysis and conditional scenarios; "
        + sessions
        + " sessions. Proxy/CFD costs unresolved; no forecast or order."
    )


def report_document(admission: Mapping[str, Any]) -> dict[str, Any]:
    """Distinct derived report bytes/hash/locator, never a relabelled EIA capture."""
    binding = admission.get("producer_binding") or {}
    public_locator = str(binding.get("public_report_locator") or "")
    revision = str(binding.get("producer_commit") or "")
    repository = str(binding.get("producer_repository") or "").removesuffix("/")
    raw_hashes = admission.get("report_raw_sha256") or []
    path = next(
        (
            m["path"]
            for name, m in (binding.get("files") or {}).items()
            if name.endswith("report.json") and m.get("sha256") in raw_hashes
        ),
        None,
    )
    if not public_locator and (
        not repository.startswith("https://github.com/")
        or len(revision) != 40
        or not path
    ):
        raise LatestReportConsumerError("MAIN_REPORT_IMMUTABLE_LOCATOR_UNBOUND")
    text = "\n\n".join(
        c["producer_layer"] + ": " + c["text"] + "\n" + str(c.get("basis_risk") or "")
        for c in admission["claims"]
    )
    text += "\n\n" + report_scope_notice(admission)
    url = public_locator or repository + "/blob/" + revision + "/" + path
    return {
        "document_id": "main-report-" + admission["source_report_sha256"],
        "publisher": "Capital Chronicle",
        "source_identity": admission["report_id"],
        "source_authority_class": "governed_capital_chronicle_report_only",
        "source_url": url,
        "reader_source_url": url,
        "published_at_utc": admission["known_at_cutoff_utc"],
        "published_at_source": "MAIN_REPORT_CUTOFF_NOT_SOURCE_RELEASE_TIME",
        "canonical_content_text": text,
        "canonical_content_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "public_claim_allowed": True,
        "report_truth_only": True,
        "underlying_event_truth_granted": False,
        "retrieval_method": "DERIVED_SEALED_MAIN_PUBLIC_PROJECTION",
        "report_lineage": {
            "report_id": admission["report_id"],
            "report_version": admission["report_version"],
            "report_sha256": admission["source_report_sha256"],
            "claims": admission["claims"],
            "scope_notice": report_scope_notice(admission),
        },
    }


def report_evidence(admission: Mapping[str, Any]) -> dict[str, Any]:
    doc = report_document(admission)
    state = {
        "schema_version": "contentops.v1_simple_epistemic_state.v1",
        "evidence_basis": "GOVERNED_CAPITAL_CHRONICLE_REPORT",
        "event_confirmation_state": "UNCONFIRMED",
        "origin_character": "ON_RECORD",
        "source_multiplicity": "SINGLE_SOURCE",
        "primary_reporting_publisher": "Capital Chronicle",
        "primary_reporting_source_identity": admission["report_id"],
        "report_proposition": "Capital Chronicle reports dated observations and conditional analysis.",
        "event_proposition": "This report import does not independently verify the underlying events.",
        "report_truth_supported": True,
        "event_truth_supported": False,
        "reader_visible_epistemic_label": "CC REPORT / EVENT UNCONFIRMED",
        "supporting_document_ids": [doc["document_id"]],
        "analysis_must_be_conditional": True,
        "underlying_event_may_be_stated_as_confirmed": False,
        "authority_granted_by_adapter": False,
        "public_write_authority": False,
        "report_scope_notice": report_scope_notice(admission),
    }
    return {
        "status": "PASS",
        "blockers": [],
        "evidence_documents": [doc],
        "epistemic_state": state,
        "provenance": {
            "request_count_for_call": 0,
            "new_external_acquisition": False,
            "retrieval_method": doc["retrieval_method"],
        },
    }


class _Stages:
    """Existing outbox/artifact APIs hold immutable successful steps and attempt fences."""

    def __init__(self, tracker: LatestReportDeliveryTracker, receipt_id: str, opportunity_id: str | None = None):
        self.store = tracker.store
        self.work = "cc-report-" + sha256_of(receipt_id) if not opportunity_id else "cc-opportunity-" + sha256_of(opportunity_id)
        if opportunity_id:
            self.store.create_work_item(story_id=self.work, title="Main-enriched newsroom opportunity",
                                       target_surface="CONTENTOPS_EDITORIAL_ONLY", work_item_id=self.work)

    def get(self, key: str) -> dict[str, Any] | None:
        row = next(
            (r for r in self.store.list_outbox_messages() if r["message_id"] == key),
            None,
        )
        return json.loads(row["payload"]) if row else None

    def put(self, key: str, value: Mapping[str, Any], destination: str = STAGE) -> None:
        if _private(value):
            raise LatestReportConsumerError("PRIVATE_EDITORIAL_STAGE_EXCLUDED")
        raw = canonical_bytes(value)
        self.store.register_artifact(
            artifact_id="cc-stage-" + sha256_of(value),
            artifact_type="CC_EDITORIAL_STAGE",
            storage_class="INTERNAL_READ_PROJECTION",
            schema_version=SCHEMA,
            producer_ref="ContentOps.Simple.report-adapter",
            content_bytes=raw,
        )
        self.store.register_outbox_message(
            message_id=key,
            work_item_id=self.work,
            destination=destination,
            payload=raw.decode(),
            status="EDITORIAL_INTERNAL",
        )

    def call(
        self, stage: str, identity: Mapping[str, Any], caller: Callable[[], Any]
    ) -> Any:
        key = "cc-step-" + sha256_of([self.work, stage])
        request_hash = sha256_of(identity)
        prior = self.get(key)
        if prior:
            if prior["request_sha256"] != request_hash:
                raise LatestReportConsumerError(
                    "EDITORIAL_RESUME_INPUT_CHANGED:" + stage
                )
            return prior["result"]
        fence = self.get(key + "-started")
        if fence:
            raise LatestReportConsumerError(
                "EDITORIAL_STEP_RESULT_NOT_RECORDED:" + stage
            )
        self.put(key + "-started", {"stage": stage, "request_sha256": request_hash})
        result = caller()
        self.put(
            key, {"stage": stage, "request_sha256": request_hash, "result": result}
        )
        return result


def _artifact(root: Path, name: str) -> dict[str, Any]:
    return json.loads((root / name).read_bytes())


def run_report_editorial_cycle(
    tracker: LatestReportDeliveryTracker,
    *,
    receipt_id: str,
    admission: Mapping[str, Any] | None,
    output_dir: str | Path,
    cutoff_utc: str,
    rolling_input: Mapping[str, Any] | None = None,
    published_memory: Sequence[Any] = (),
    llm_invoke: Callable[..., Any] | None = None,
    run_id: str | None = None,
    additional_reports: Sequence[Mapping[str, Any]] = (),
    opportunity_id: str | None = None,
    source_route_health: Mapping[str, Any] | None = None,
    attempted_candidate_ids: Sequence[str] = (),
    retained_research=None,
) -> dict[str, Any]:
    """A single bounded manual opportunity; retries replay durable successful stages."""
    record = next(
        (r for r in tracker.receipts() if r["receipt_id"] == receipt_id), None
    )
    if admission is not None and (record is None or record.get("raw_sha256") != admission.get("raw_sha256")):
        raise LatestReportConsumerError("REPORT_DURABLE_RECEIPT_BINDING_REQUIRED")
    record = record or {}
    root = Path(output_dir).resolve()
    stages = _Stages(tracker, receipt_id, opportunity_id)
    final_id = "cc-editorial-final-" + sha256_of(opportunity_id or receipt_id)
    previous = stages.get(final_id)
    if previous:
        if any(r["destination"] == "internal:cc-report-withdrawal"
               and json.loads(r["payload"]).get("source_report_sha256") == previous.get("source_report_sha256")
               for r in tracker.store.list_outbox_messages()):
            return {**previous, "classification": "DRAFT_WITHDRAWN", "draft_count": 0, "preview_count": 0, "previews": [], "article": None}
        newer = [
            r
            for r in tracker.receipts()
            if r["status"] in CURRENT
            and r["report_id"] == previous.get("report_id", record.get("report_id"))
            and r["report_version"] > (previous.get("report_version") or record.get("report_version", 0))
            and r["status"] != "NO_MATERIAL_CHANGE_NOOP"
        ]
        if newer:
            latest = max(newer, key=lambda r: r["report_version"])
            return {
                **previous,
                "classification": "DRAFT_WITHDRAWN"
                if latest.get("withdrawal_only")
                else "DRAFT_SUPERSEDED",
                "superseded_by_version": latest["report_version"],
            }
        return previous
    if record.get("status") in {
        "INVALIDATION_WITHDRAWAL_NOOP",
        "LINEAGE_ONLY_NOOP",
        "NO_MATERIAL_CHANGE_NOOP",
        "DUPLICATE_NOOP",
        "OUT_OF_ORDER_NOOP",
    }:
        return {
            "schema_version": SCHEMA,
            "classification": record["status"],
            "draft_count": 0,
            "preview_count": 0,
            "compiled_derivative_count": 0,
            "public_write_performed": False,
        }
    prepared = tracker.prepare_input(
        receipt_id,
        output_dir=root,
        cutoff_utc=cutoff_utc,
        rolling_input=rolling_input,
        published_memory=published_memory,
    ) if record else {}
    args = prepared["simple_gemini_handoff"]["runner_arguments"] if record else {
        "rolling_input": dict(rolling_input or {}), "published_memory": list(published_memory),
        "capital_chronicle_context": {}, "cutoff_utc": cutoff_utc}
    pool_key = "cc-editorial-pool-" + sha256_of(opportunity_id or receipt_id)
    frozen = stages.get(pool_key)
    if frozen:
        if frozen.get("research_revision") != (retained_research.revision if retained_research else None):
            raise LatestReportConsumerError("FROZEN_RESEARCH_REVISION_CHANGED")
        args, records = frozen["args"], frozen["reports"]
        prepared_inputs = frozen["prepared_inputs"]
        prepared = prepared_inputs.get(record.get("report_id"), {})
    else:
        # Report evidence may be cached across opportunities. Intake and canonical
        # publication memory belong to THIS new opportunity, not that old receipt.
        primary_headlines = [h for h in args["rolling_input"].get("headlines", [])
            if h.get("headline_id") == "cc-report:" + record.get("envelope_sha256", "")]
        args["rolling_input"] = {**dict(rolling_input or {}),
            "headlines": [*primary_headlines, *dict(rolling_input or {}).get("headlines", [])]}
        args["published_memory"] = [m.to_dict() if hasattr(m, "to_dict") else dict(m) for m in published_memory]
        args["cutoff_utc"] = cutoff_utc
        records = [record, *[dict(r) for r in additional_reports]] if record else []
        prepared_inputs = {record["report_id"]: prepared} if record else {}
        for other in records[1:]:
            if not any(r["receipt_id"] == other["receipt_id"] and r["raw_sha256"] == other["raw_sha256"] for r in tracker.receipts()):
                raise LatestReportConsumerError("REPORT_DURABLE_RECEIPT_BINDING_REQUIRED")
            extra = tracker.prepare_input(other["receipt_id"], output_dir=root, cutoff_utc=cutoff_utc)
            prepared_inputs[other["report_id"]] = extra
            args["rolling_input"]["headlines"].insert(0, extra["simple_gemini_handoff"]["runner_arguments"]["rolling_input"]["headlines"][0])
        args["capital_chronicle_context"]["report_editorial_briefs"] = [
            build_report_editorial_input(r, output_dir=root, cutoff_utc=cutoff_utc)["brief"] for r in records
        ]
        from live_contentops.contentops_editorial_desk_v1 import read_reviews, publication_story_context, selection_story_context
        library = library_projection(tracker.store.list_outbox_messages(), read_reviews(tracker.store))
        if library:
            stories = publication_story_context(library["stories"], args["published_memory"], cutoff_utc=cutoff_utc)
            for headline in args["rolling_input"].get("headlines", []):
                external = dict(headline.get("external_content") or {})
                report_id = (external.get("report_editorial_context") or {}).get("report_id")
                matches = [s for s in stories if headline.get("headline_id") in s["source_item_ids"] or report_id in s["main_report_ids"]]
                if matches:
                    headline["external_content"] = {**external, "evolving_story_context": [selection_story_context(s) for s in matches]}
            args["capital_chronicle_context"]["foundation_library"] = {
                "research_revision": library["research_revision"],
                "briefs": [b for b in library["briefs"] if not any(p["brief_id"] == b["brief_id"] and
                    p["review"]["state"] == "HOLD" for p in library["packages"])][:16],
                "families": library["families"],
                "editorial_desk": library["desk"],
                "stories": stories,
                "research_packages": [{k: p.get(k) for k in ("brief_id", "package_revision", "editorial_kind", "review", "source_revision_current")}
                                      for p in library["packages"]],
                "scope": "PUBLIC_RESEARCH_QUESTIONS_NOT_MAIN_NUMERIC_AUTHORITY",
            }
        args["source_route_health"] = dict(source_route_health or {})
        args["attempted_candidate_ids"] = list(attempted_candidate_ids)
        stages.put(pool_key, {"args": args, "reports": records, "prepared_inputs": prepared_inputs,
                              "research_revision": retained_research.revision if retained_research else None})
    source_route_health = args["source_route_health"]
    attempted_candidate_ids = args["attempted_candidate_ids"]
    # These inputs were frozen by prepare_input; never replace them with fresh intake on resume.
    cutoff_utc = str(args.get("cutoff_utc") or cutoff_utc)
    base = {
        "schema_version": SCHEMA,
        "report_id": record.get("report_id"),
        "report_version": record.get("report_version"),
        "source_report_sha256": record.get("source_report_sha256"),
        "receipt_id": receipt_id,
        "input": prepared,
        "model_execution_state": "INJECTED_REPLAY_ONLY"
        if llm_invoke
        else "EXISTING_SIMPLE_PROVIDER",
        "draft_count": 0,
        "qualified_article_count": 0,
        "preview_count": 0,
        "compiled_derivative_count": 0,
        "logical_model_invocation_count": 0,
        "writer_invoked": False,
        "public_write_performed": False,
        "affected_drafts": record.get("affected_drafts", []),
        "article": None,
        "previews": [],
    }
    if llm_invoke is None and llm_operator_pause_active():
        blocked = {
            **base,
            "classification": "DRAFT_BLOCKED",
            "exact_next_blocker": "LLM_OPERATOR_PAUSED",
            "model_execution_state": "PAUSED_BEFORE_PROVIDER_CALL",
            "llm_operator_pause_active": True,
        }
        stages.put(
            "cc-editorial-pause-" + sha256_of(opportunity_id or receipt_id), blocked, SIMPLE_RESULT
        )
        return blocked

    from live_contentops.production_orchestrator_v1 import (
        ContentOpsProductionOrchestrator,
    )
    from live_contentops.v1_simple_gemini_newsroom_v1 import (
        _default_llm_invoke,
        _default_evidence_loader,
    )

    owner = "cc-editorial-" + uuid4().hex
    lease = tracker.store.acquire_lease(
        "internal:cc-report-consume", owner, ttl_seconds=900
    )
    try:
        if any(
            r["status"] in CURRENT
            and any(
                tracker._related(candidate, r) and r["report_version"] > candidate["report_version"]
                and not (r["status"] == "NO_MATERIAL_CHANGE_NOOP"
                         and r.get("claim_set_hash") == candidate.get("claim_set_hash"))
                for candidate in records
            )
            for r in tracker.receipts()
        ):
            raise LatestReportConsumerError("NEWER_REPORT_ALREADY_RECEIVED")
        caller = llm_invoke or _default_llm_invoke

        def model(**kwargs: Any) -> Any:
            stage = str(kwargs["logical_invocation_id"]).rsplit(":", 1)[-1]
            identity = {
                "prompt": kwargs["prompt"],
                "governed_input": kwargs["governed_input"],
            }

            def invoke() -> Any:
                if llm_invoke is None and llm_operator_pause_active():
                    raise LLMOperatorPausedError()
                value, receipt = caller(**kwargs)
                ok, _, _, reason = kwargs["validator"](json.dumps(value))
                if not ok:
                    raise LatestReportConsumerError(
                        "SIMPLE_OUTPUT_CONTRACT:" + str(reason)
                    )
                return [value, receipt]

            return tuple(stages.call(stage, identity, invoke))

        default_loader = _default_evidence_loader(cutoff_utc, source_route_health=source_route_health)
        spent = sum(
            int(
                json.loads(r["payload"])["result"]
                .get("provenance", {})
                .get("request_count_for_call")
                or 0
            )
            for r in tracker.store.list_outbox_messages()
            if r["destination"] == STAGE
            and r["work_item_id"] == stages.work
            and str(json.loads(r["payload"]).get("stage", "")).startswith("source:")
            and "result" in json.loads(r["payload"])
        )
        default_loader.resume_request_count(spent)
        report_by_headline = {"cc-report:" + r["envelope_sha256"]: r for r in records}

        def evidence(request: Mapping[str, Any]) -> dict[str, Any]:
            stage = "source:" + str(request["cluster_id"])
            report = next((report_by_headline[h] for h in request.get("headline_ids", []) if h in report_by_headline), None)
            return stages.call(
                stage,
                request,
                lambda: (
                    report_evidence(report)
                    if report is not None
                    else (retained_research.evidence(request, cutoff_utc=cutoff_utc) if retained_research else None) or default_loader(request)
                ),
            )

        simple = ContentOpsProductionOrchestrator().execute(
            "run_v1_simple_gemini_newsroom",
            output_dir=root,
            cutoff_utc=cutoff_utc,
            rolling_input=args["rolling_input"],
            published_memory=args.get("published_memory", []),
            capital_chronicle_context=args["capital_chronicle_context"],
            llm_invoke=model,
            evidence_loader=evidence,
            run_id=run_id or "cc-report-" + record.get("envelope_sha256", sha256_of(receipt_id)),
            source_route_health=source_route_health,
            attempted_candidate_ids=attempted_candidate_ids,
        )
        result = {
            **base,
            "simple_result": simple,
            "classification": "DRAFT_BLOCKED",
            "exact_next_blocker": simple.get("exact_next_blocker"),
            "logical_model_invocation_count": simple.get(
                "logical_model_invocation_count", 0
            ),
        }
        if simple.get("qualified_article_count") == 1:
            article = _artifact(root, "article_manifest_v1.json")
            previews = _artifact(root, "native_derivative_previews_v1.json")
            validation = _artifact(root, "simple_gemini_validation_v1.json")
            evidence_walk = _artifact(root, "simple_gemini_evidence_v1.json")
            selected_record = report_by_headline.get(simple["selected_candidate"]["headline_id"])
            selected_report = selected_record is not None
            if not selected_report:
                # Independent news remains valid intake but cannot earn report-to-article credit.
                result.update(
                    classification="INDEPENDENT_NEWS_DRAFT",
                    exact_next_blocker=None,
                    report_id=None, report_version=None, source_report_sha256=None,
                    draft_count=1, qualified_article_count=1, preview_count=8, compiled_derivative_count=8,
                    article=article, article_identity=simple["article_identity"],
                    replay_writer_used=llm_invoke is not None, writer_invoked=llm_invoke is None,
                    evidence=evidence_walk["selected_source_pack"],
                    previews=[{"destination": k, "payload": v, "preview_id": "cc-preview-" + sha256_of([simple["article_identity"], k, v]),
                               "article_identity": simple["article_identity"], "claim_lineage": validation.get("supported_material_claims") or []}
                              for k, v in previews["packages"].items()],
                )
                selected_headline = simple["selected_candidate"]["headline_id"]
                retained = retained_research.records.get(selected_headline) if retained_research else None
                if retained:
                    from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_source_backed_media_assets
                    document = {**retained["document"], "known_at_utc": retained["known_at_utc"],
                                "rights_evidence_sha256": retained["rights_evidence_sha256"],
                                "render_excerpt_text": retained["headline_text"],
                                "underlying_reuse_classification": "governed_government_public_domain"}
                    media = build_source_backed_media_assets(
                        {"evidence_documents": [document], "story_type": "DATA_OR_DOCUMENT_LENS"}, output_dir=root, required_asset_count=1)
                    result["media_assets"] = media
                    if retained.get("source_chart"):
                        from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_source_value_comparison_chart
                        chart = retained["source_chart"]
                        media.append(build_source_value_comparison_chart(document, rows=chart["rows"], title=chart["title"], unit=chart["unit"], output_dir=root))
                    import base64
                    for asset in media:
                        raw_media = Path(asset["path"]).read_bytes()
                        if len(raw_media) <= 1_500_000 and hashlib.sha256(raw_media).hexdigest() == asset["sha256"] and raw_media.startswith(b"\x89PNG\r\n\x1a\n"):
                            asset["preview_data_url"] = "data:image/png;base64," + base64.b64encode(raw_media).decode("ascii")
            else:
                record = selected_record
                lineage = validation.get("supported_material_claims") or []
                result.update(
                    report_id=record["report_id"], report_version=record["report_version"],
                    source_report_sha256=record["source_report_sha256"], receipt_id=record["receipt_id"],
                    input=prepared_inputs[record["report_id"]],
                    affected_drafts=record.get("affected_drafts", []),
                    classification="DRAFT_READY",
                    exact_next_blocker=None,
                    draft_count=1,
                    qualified_article_count=1,
                    preview_count=8,
                    compiled_derivative_count=8,
                    writer_invoked=llm_invoke is None,
                    replay_writer_used=llm_invoke is not None,
                    article=article,
                    previews=[
                        {
                            "destination": k,
                            "payload": v,
                            "preview_id": "cc-preview-"
                            + sha256_of([simple["article_identity"], k, v]),
                            "article_identity": simple["article_identity"],
                            "claim_lineage": lineage,
                        }
                        for k, v in previews["packages"].items()
                    ],
                    article_identity=simple["article_identity"],
                    claim_lineage=lineage,
                    evidence=evidence_walk["selected_source_pack"],
                    uncertainty=record["limitations"],
                    canonical_public_url=None,
                    canonical_url_state="UNBOUND_PREVIEW_ONLY",
                    affected_prior_inputs=record.get("affected_prior_inputs", []),
                )
        stages.put(final_id, result, SIMPLE_RESULT)
        return result
    except (LatestReportConsumerError, LLMOperatorPausedError) as exc:
        blocker = str(exc)
        blocked = {
            **base,
            "classification": "DRAFT_BLOCKED",
            "exact_next_blocker": blocker,
        }
        stages.put(
            "cc-editorial-blocked-" + sha256_of([opportunity_id or receipt_id, blocker]),
            blocked,
            SIMPLE_RESULT,
        )
        return blocked
    finally:
        tracker.store.release_lease(lease["lease_id"], owner, lease["fencing_token"])


def report_workspace_projection(
    rows: Sequence[Mapping[str, Any]], report_id: str | None = None, *, review_records=()
) -> dict[str, Any]:
    """Read only durable payloads; blocked/duplicate events never poison current content."""
    admissions, inputs, results = [], [], []
    withdrawals = [json.loads(r["payload"]) for r in rows if r["destination"] == "internal:cc-report-withdrawal"]
    feeds, opportunities, headline_exports = [], [], []
    for row in rows:
        if row["destination"] in {"internal:cc-report-feed", "internal:cc-report-opportunity", "internal:contentops-main-headline-export"}:
            value = {**json.loads(row["payload"]), "created_at": row.get("created_at")}
            if row["destination"] == "internal:cc-report-feed":
                feeds.append(value)
            elif row["destination"] == "internal:cc-report-opportunity":
                opportunities.append(value)
            else:
                headline_exports.append(value)
            continue
        if row["destination"] not in {
            "internal:cc-report-receipt",
            EDITORIAL_INPUT,
            SIMPLE_RESULT,
        }:
            continue
        payload = json.loads(row["payload"])
        item = {
            **payload,
            "message_id": row["message_id"],
            "delivery_status": row["status"],
            "created_at": row.get("created_at"),
        }
        item_id = payload.get("report_id") or payload.get("brief", {}).get("report_id")
        if report_id and item_id != report_id:
            continue
        if row["destination"] == "internal:cc-report-receipt":
            admissions.append(item)
        elif row["destination"] == EDITORIAL_INPUT:
            inputs.append(item)
        else:
            results.append(item)
    accepted = [r for r in admissions if r.get("status") in CURRENT]
    ids = {r["report_id"] for r in accepted}
    accepted.sort(
        key=lambda r: (str(r.get("created_at") or ""), int(r["report_version"])),
        reverse=True,
    )
    if len(ids) == 1:
        accepted.sort(key=lambda r: int(r["report_version"]), reverse=True)
    latest = accepted[0] if accepted else None
    if latest and any(w["source_report_sha256"] == latest["source_report_sha256"] for w in withdrawals):
        latest = {**latest, "withdrawal_only": True, "claims": []}
    content = next(
        (
            r
            for r in accepted
            if latest
            and r["report_id"] == latest["report_id"]
            and r["status"] != "NO_MATERIAL_CHANGE_NOOP"
        ),
        latest,
    )
    same = [
        r
        for r in results
        if content
        and r.get("report_id") == content["report_id"]
        and r.get("report_version") == content["report_version"]
    ]
    same.sort(
        key=lambda r: (
            r.get("classification") == "DRAFT_READY",
            str(r.get("created_at") or ""),
        ),
        reverse=True,
    )
    result = same[0] if same else None
    latest_attempt = max(same, key=lambda r: (str(r.get("created_at") or ""), r.get("classification") == "DRAFT_READY"), default=None)
    current_input = next(
        (
            r
            for r in inputs
            if content
            and r.get("brief", {}).get(
                "report_id",
                r.get("brief", {}).get("correction_lineage", {}).get("report_id"),
            )
            == content["report_id"]
            and r.get("brief", {}).get(
                "report_version",
                r.get("brief", {}).get("correction_lineage", {}).get("report_version"),
            )
            == content["report_version"]
        ),
        None,
    )
    feed = max(feeds, key=lambda r: str(r.get("created_at") or r.get("observed_at_utc")), default=None)
    export = max(headline_exports, key=lambda r: int(r["sequence"]), default=None)
    parent_gaps = [e for e in (feed or {}).get("events", []) if e.get("state") in {"LINEAGE_PARENT_NOT_RECEIVED", "LINEAGE_HASH_CONFLICT"}]
    lag = None
    if latest and feed:
        from live_contentops.capital_chronicle_latest_report_consumer_v1 import _time
        lag = max(0, int((_time(feed["observed_at_utc"]) - _time(latest["known_at_cutoff_utc"])).total_seconds()))
    return {
        "schema_version": SCHEMA,
        "state": "AVAILABLE" if latest else "UNAVAILABLE",
        "foundation_library": library_projection(rows, review_records) if report_id is None else None,
        "report_events_received": len(admissions),
        "latest_report": latest,
        "report_history": admissions,
        "feed": feed,
        "report_age_at_last_scan_seconds": lag,
        "freshness": {"report_age_at_last_scan_seconds": lag,
                      "claims": sorted({c.get("freshness_state", "UNKNOWN") for c in (latest or {}).get("claims", [])}),
                      "current_market_refresh_verified": False,
                      "scope": "DATED_RETAINED_REPORT_NOT_CURRENT_MARKET_STATE"},
        "opportunities": sorted(opportunities, key=lambda r: str(r.get("created_at") or ""), reverse=True)[:32],
        "headline_export": {k: export[k] for k in (
            "schema_version", "observed_at_utc", "sequence", "source_rows_scanned", "eligible_rows",
            "missing_rows", "coverage", "discovered_file_count", "gaps"
        ) if k in export} | {k: export.get(k, 0) for k in ("independent_items", "main_origin_recirculated_items")} if export else None,
        "source_inventory": {
            "independent_items": len({r["projection_sha256"] for p in headline_exports for r in p["rows"] if r.get("originality") == "INDEPENDENT_CONTENTOPS_ACQUISITION"}),
            "main_origin_recirculated_items": len({r["projection_sha256"] for p in headline_exports for r in p["rows"] if r.get("originality") == "MAIN_ORIGIN_RECIRCULATION"}),
            "scope": "DISTINCT_ACCEPTED_PROJECTIONS_NOT_SOURCE_COMPLETENESS",
        },
        "independent_results": [{k: r.get(k) for k in ("classification", "model_execution_state", "article_identity", "article", "previews", "media_assets", "evidence", "created_at")}
                                for r in results if r.get("classification") == "INDEPENDENT_NEWS_DRAFT"][-16:],
        "conversion": {"independent_drafts": sum(r.get("classification") == "INDEPENDENT_NEWS_DRAFT" for r in results),
                       "main_drafts": sum(r.get("classification") == "DRAFT_READY" for r in results),
                       "fresh_provider_drafts": sum(r.get("qualified_article_count", 0) for r in results if r.get("model_execution_state") == "EXISTING_SIMPLE_PROVIDER"),
                       "controlled_drafts": sum(r.get("qualified_article_count", 0) for r in results if r.get("model_execution_state") == "INJECTED_REPLAY_ONLY")},
        "next_operation": ("Main must supply or restore the exact public parent " + str(parent_gaps[0].get("required_parent_report_sha256") or "identified by the manifest") + "; replay manifest admission without a model call. Independent news remains available.")
                          if parent_gaps else "Resume the existing Simple route only after actual pause release; consume the configured public export manifest at the next existing window.",
        "workspaces": [report_workspace_projection(rows, key) for key in sorted(ids)]
        if report_id is None and len(ids) > 1
        else [],
        "latest_editorial_input": current_input,
        "latest_simple_result": result,
        "latest_attempt": latest_attempt,
        "article": None if latest and latest.get("withdrawal_only") else (result or {}).get("article"),
        "previews": [] if latest and latest.get("withdrawal_only") else (result or {}).get("previews", []),
        "named_blocker": (latest_attempt or {}).get("exact_next_blocker")
        or (parent_gaps[0]["state"] if parent_gaps else None)
        or (
            "CLAIMS_WITHDRAWN"
            if latest and latest.get("withdrawal_only")
            else "NO_PUBLIC_SAFE_CLAIMS"
            if latest and latest.get("lineage_only")
            else "DRAFT_NOT_CREATED"
            if not result
            else None
        ),
        "history": [
            {
                "report_id": r.get("report_id"),
                "report_version": r.get("report_version"),
                "article_identity": r.get("article_identity"),
                "preview_ids": [p["preview_id"] for p in r.get("previews", [])],
                "state": "WITHDRAWN"
                if latest and latest.get("withdrawal_only")
                else "SUPERSEDED",
                "superseded_by_version": latest["report_version"] if latest else None,
            }
            for r in results
            if content
            and r.get("report_id") == content["report_id"]
            and r.get("report_version", 0) < content["report_version"]
            and r.get("article_identity")
        ],
        "public_write_performed": False,
    }
