"""CC-014 public desk records through the existing feed, evidence and story owners."""
from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from live_contentops.capital_chronicle_latest_report_consumer_v1 import _load, _time, sha256_of
from tools.product.desk_record_projection_v1 import (
    RECORD_LISTS, check_clocks, check_public_text, check_references, is_field, project,
)

PRODUCER_COMMIT = "89e59374eda3686271a0df4690e74b2e2d3f996a"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas/publication/CapitalChronicleDeskRecordExportV1.schema.json"
FIXTURE_NOTICE = "Fixture, not current data. Private acceptance preview; never publish."


def display_value(field, *, observations_decimals=None):
    value = field["value"]
    if value is None:
        return "unavailable"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        number = Decimal(str(value))
        decimals = field.get("decimals", 0)
        quantum = Decimal(1).scaleb(-decimals)
        if number != number.quantize(quantum):
            raise ValueError("DESK_NUMBER_PRECISION_MISMATCH")
        return format(number, f".{decimals}f")
    if isinstance(value, str):
        return value
    if isinstance(value, list) and observations_decimals is not None:
        return "[" + ",".join('{"period":' + json.dumps(row["period"]) + ',"value":' +
            ("null" if row["value"] is None else display_value({"value": row["value"], "decimals": observations_decimals})) + "}"
            for row in value) + "]"
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def record_fields(node, path=""):
    """Use producer ids, never array offsets, in the required record citations."""
    if is_field(node):
        yield path, node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield from record_fields(value, path + "/" + key)
    elif isinstance(node, list):
        for value in node:
            if not isinstance(value, dict):
                continue
            identity = next((value[k] for k in ("measure_id", "metric_id", "update_id", "section_id", "scenario_id") if k in value), None)
            if identity is not None:
                yield from record_fields(value, path + "/" + identity)


def read_export(spec, *, cutoff_utc):
    path = Path(spec["path"])
    if path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("DESK_EXPORT_TOO_LARGE")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != spec.get("sha256"):
        raise ValueError("DESK_EXPORT_BYTES_MISMATCH")
    doc = _load(raw)
    schema = json.loads(SCHEMA_PATH.read_bytes())
    if next(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(doc), None):
        raise ValueError("DESK_EXPORT_SCHEMA_INVALID")
    if sha256_of({k: v for k, v in doc.items() if k != "integrity"}) != doc["integrity"]["content_sha256"]:
        raise ValueError("DESK_EXPORT_INTEGRITY_INVALID")
    if check_references(doc) or check_clocks(doc) or check_public_text(doc):
        raise ValueError("DESK_EXPORT_REFERENCE_CLOCK_OR_PUBLIC_TEXT_INVALID")
    if _time(doc["generated_at_utc"]) > _time(cutoff_utc):
        raise ValueError("DESK_EXPORT_AFTER_CUTOFF")
    if doc["fixture"] and spec.get("allow_fixture_private_preview") is not True:
        raise ValueError("DESK_FIXTURE_PRIVATE_PREVIEW_ONLY")
    # This exact producer projection precedes every headline, source span or model input.
    public = project(doc, {"public"})
    sources = {s["source_id"]: s for s in public["sources"]}
    records = []
    for kind in RECORD_LISTS:
        for record in public[kind]:
            fields = []
            for path, field in record_fields(record):
                fields.append({"citation": public["export_id"] + "#" + record["record_id"] + path,
                    "field_path": path, "value": field["value"], "display": display_value(field,
                        observations_decimals=record["decimals"] if kind == "data_series" and path == "/observations" else None),
                    **{k: field[k] for k in ("unit", "decimals", "rights_class", "use_label", "source_ids") if k in field}})
            if not fields:
                continue
            ids = sorted({sid for f in fields for sid in f["source_ids"]})
            assets = record.get("asset_ids") or ([record["asset_id"]] if record.get("asset_id") else [])
            clock = record.get("known_at_utc") or record.get("generated_at_utc") or public["generated_at_utc"]
            events = record.get("event_ids") or ([record["event_id"]] if record.get("event_id") else [])
            # No names/labels are inferred from structure. Fields alone supply readable text.
            title = next((f["display"] for f in fields if f["field_path"] in {"/release/name", "/identity/name", "/title", "/name"}), fields[0]["display"])
            identity = "cc-desk:" + sha256_of([public["export_id"], record["record_id"], fields])
            text = "\n".join(f["citation"] + " = " + f["display"] + (" " + f["unit"] if f.get("unit") else "") for f in fields)
            binding = {"export_id": public["export_id"], "record_id": record["record_id"],
                "record_type": record["record_type"], "export_bytes_sha256": digest,
                "projection_sha256": sha256_of(public), "fixture": public["fixture"],
                "asset_ids": assets, "event_ids": events, "fields": fields,
                "sources": [sources[sid] for sid in ids],
                **({"series": {k: record[k] for k in ("series_id", "series_code", "window", "unit", "decimals", "frequency", "seasonal_adjustment")}}
                   if kind == "data_series" else {})}
            binding["record_content_sha256"] = sha256_of({"record_id": record["record_id"],
                "fields": [{k:v for k,v in f.items() if k != "citation"} for f in fields],
                "sources": binding["sources"], "asset_ids": assets, "event_ids": events,
                **({"series": binding["series"]} if "series" in binding else {})})
            headline = {"headline_id": identity, "headline_text": title,
                "source_identity": "Capital Chronicle", "source_platform": "CAPITAL_CHRONICLE_DESK_RECORD_EXPORT",
                "source_account": "Capital Chronicle", "source_timestamp_utc": clock, "known_at_utc": clock,
                "source_url": spec.get("public_locator") or "urn:cc-public-report:desk:" + sha256_of(binding),
                "provider_safe": True, "MODEL_INPUT_ALLOWED": True, "LLM_INPUT_ALLOWED": True,
                "INTERNAL_ANALYSIS_ALLOWED": True, "permitted_consumers": ["internal_research", "narrative_context"],
                "rights_state": "MAIN_PUBLIC_FIELD_PROJECTION", "originality": "MAIN_ORIGIN_RECIRCULATION",
                "external_content": {"headline_text": title, "source_platform": "CAPITAL_CHRONICLE_DESK_RECORD_EXPORT",
                    "desk_record_binding": binding, "tags": [*assets, *events],
                    "editorial_constraints": [FIXTURE_NOTICE] if public["fixture"] else []}}
            records.append({"headline": headline, "binding": binding, "text": text,
                "known_at_utc": clock, "title": title, "headline_id": identity,
                "record_revision": sha256_of(binding)})
    return records


def desk_evidence(records, request):
    selected = [r for r in records if r["headline_id"] in request.get("headline_ids", [])]
    if not selected:
        return None
    # Join only explicitly linked public dossiers and the same official series.
    # Shared vocabulary alone never establishes story continuity.
    events = {e for r in selected for e in r["binding"]["event_ids"]}
    source_ids = {s["source_id"] for r in selected for s in r["binding"]["sources"]}
    selected_ids = {r["headline_id"] for r in selected}
    related = [r for r in records if r["headline_id"] not in selected_ids and (
        r["binding"]["record_type"] == "asset_dossier" and events.intersection(r["binding"]["event_ids"])
        or r["binding"]["record_type"] == "data_series" and source_ids.intersection(s["source_id"] for s in r["binding"]["sources"]))]
    selected = [*selected, *related][:4]
    docs = [{"document_id": r["headline_id"], "publisher": "Capital Chronicle",
        "source_identity": r["binding"]["record_id"], "source_authority_class": "governed_capital_chronicle_report_only",
        "source_url": r["headline"]["source_url"], "reader_source_url": r["headline"]["source_url"],
        "published_at_utc": r["known_at_utc"], "known_at_utc": r["known_at_utc"],
        "published_at_source": "MAIN_RECORD_KNOWN_AT_NOT_INDEPENDENT_EVENT_CONFIRMATION",
        "canonical_content_text": r["text"], "canonical_content_sha256": hashlib.sha256(r["text"].encode()).hexdigest(),
        "public_claim_allowed": True, "report_truth_only": True, "underlying_event_truth_granted": False,
        "desk_record_binding": r["binding"], "retrieval_method": "MAIN_PUBLIC_DESK_RECORD_PROJECTION"} for r in selected]
    return {"status": "PASS", "blockers": [], "evidence_documents": docs,
        "epistemic_state": {"schema_version": "contentops.v1_simple_epistemic_state.v1",
            "evidence_basis": "GOVERNED_CAPITAL_CHRONICLE_REPORT", "event_confirmation_state": "UNCONFIRMED",
            "origin_character": "ON_RECORD", "source_multiplicity": "SINGLE_SOURCE",
            "primary_reporting_publisher": "Capital Chronicle", "primary_reporting_source_identity": selected[0]["binding"]["export_id"],
            "report_proposition": "Capital Chronicle's public desk fields record dated source facts and analysis.",
            "event_proposition": "This import does not independently confirm the underlying event.",
            "report_truth_supported": True, "event_truth_supported": False,
            "reader_visible_epistemic_label": "DATED CAPITAL CHRONICLE RECORD",
            "supporting_document_ids": [d["document_id"] for d in docs], "analysis_must_be_conditional": True,
            "underlying_event_may_be_stated_as_confirmed": False, "authority_granted_by_adapter": False,
            "public_write_authority": False},
        "provenance": {"request_count_for_call": 0, "new_external_acquisition": False,
            "retrieval_method": "MAIN_PUBLIC_DESK_RECORD_PROJECTION"}}


def validate_article_citations(article, records):
    facts = {f["citation"]: f for r in records for f in r["binding"]["fields"]}
    citations = article.get("desk_record_citations") or []
    if not isinstance(citations, list) or not 1 <= len(citations) <= 256 or any(not isinstance(c, dict) for c in citations):
        raise ValueError("EXACT_DESK_ARTICLE_CITATIONS_REQUIRED")
    for cite in citations:
        field = facts.get(cite.get("citation"))
        if (not field or type(cite.get("value")) is not type(field["value"])
                or sha256_of(cite.get("value")) != sha256_of(field["value"])
                or any(cite.get(k) != field.get(k) for k in ("value", "display", "decimals", "unit"))):
            raise ValueError("DESK_ARTICLE_VALUE_OR_PRECISION_CHANGED")
    source_ids = {sid for cite in citations for sid in facts[cite["citation"]]["source_ids"]}
    required_sources = {source["source_id"]: source for r in records for source in r["binding"]["sources"]
        if source["source_id"] in source_ids}
    body = article.get("substack_body_markdown", "")
    for source in required_sources.values():
        for key in ("attribution", "disclaimer"):
            if source.get(key) and source[key].casefold() not in body.casefold():
                raise ValueError("DESK_ARTICLE_SOURCE_" + key.upper() + "_REQUIRED")
    if any(r["binding"]["fixture"] for r in records) and "fixture, not current data" not in body.casefold():
        raise ValueError("DESK_FIXTURE_NOTICE_REQUIRED")
    # The producer's text checks run before projection. These checks also cover new prose.
    from tools.product.desk_record_projection_v1 import PRIVATE_TERMS
    prose = " ".join(str(article.get(k) or "") for k in (
        "title", "dek", "search_title", "meta_description", "substack_body_markdown", "social_hook", "social_mechanism_summary", "social_policy_summary", "social_cross_asset_summary"))
    if PRIVATE_TERMS.search(prose):
        raise ValueError("DESK_ARTICLE_PRIVATE_DERIVATION_TERMS")
    if "analysis, not financial advice" not in body.casefold():
        raise ValueError("DESK_ARTICLE_ANALYSIS_NOTICE_REQUIRED")
    numbers = re.compile(r"(?<![A-Za-z0-9])[-+]?\d+(?:[.,]\d+)*")
    allowed = {n for cite in citations for n in numbers.findall(cite["display"])}
    prose = re.sub(r"https?://\S+|\[\[SOURCE:[^\]]+\]\]", "", prose)
    if set(numbers.findall(prose)) - allowed:
        raise ValueError("DESK_ARTICLE_UNBOUND_OR_CHANGED_NUMBER")
    return {"citation_count": len(citations), "citations_sha256": sha256_of(citations),
        "numeric_authority": "EXACT_PROJECTED_PRODUCER_FIELDS", "required_source_ids": sorted(source_ids), "fixture": any(r["binding"]["fixture"] for r in records)}


def story_context(rows, review_records=()):
    """Read asset/event continuity and reviewed drafts from the existing outbox/table."""
    latest, finals = {}, []
    for row in rows:
        value = json.loads(row["payload"])
        if row["destination"] == "internal:cc-report-feed":
            if "desk_record_sources" in value:
                latest = {record["binding"]["record_id"]: record for record in value["desk_record_sources"]}
        elif row["destination"] == "internal:cc-report-simple-result" and value.get("qualified_article_count"):
            finals.append(value)
    reviews = {}
    for review in review_records:
        try:
            note = json.loads(review["notes"])
        except (ValueError, TypeError, KeyError):
            continue
        if review.get("reviewer_ref") == "NATIVE_DESKTOP_ARTICLE_REVIEW":
            reviews[note.get("article_identity")] = {**note, "decision": review["decision"], "review_id": review["review_id"]}
    stories = []
    for record_id, source in latest.items():
        binding = source["binding"]
        history = []
        for final in finals:
            used = [b for b in final.get("desk_record_source_bindings", []) if b["record_id"] == record_id]
            review = reviews.get(final.get("article_identity"))
            if used and review and review["decision"] == "KEEP":
                history.append({"article_identity": final["article_identity"], "title": final["article"]["title"],
                    "stage": "REVIEWED_UNPUBLISHED_ARTICLE", "review_id": review["review_id"],
                    "source_revision_current": any(b["record_content_sha256"] == binding["record_content_sha256"] for b in used),
                    "state": "KEEP", "rationale": review.get("rationale")})
        stories.append({"story_identity": "main-desk:" + record_id, "update_chain_identity": "main-desk:" + record_id,
            "brief_id": "main-desk:" + record_id, "title": source["title"], "source_item_ids": [source["headline_id"]],
            "main_report_ids": [], "entities_topics": [*binding["asset_ids"], *binding["event_ids"]],
            "asset_ids": binding["asset_ids"], "event_ids": binding["event_ids"], "desk_record_binding": binding,
            "disposition": "NO_MATERIAL_CHANGE" if history and history[-1]["source_revision_current"] else "FOLLOW_UP" if history else "NEW",
            "reason": "Exact Main record revision and reviewed article history; no independent confirmation.",
            "reader_question": "What changed in the dated public record?", "follow_up_value": source["title"],
            "evidence_delta": [], "changed_source_count": int(bool(history and not history[-1]["source_revision_current"])),
            "work_required": not history or not history[-1]["source_revision_current"], "missing_inputs": [],
            "confirmation_state": "MAIN_PUBLIC_RECORD_NOT_INDEPENDENT_CONFIRMATION",
            "publication_state": "UNPUBLISHED_RESEARCH", "current_review": history[-1] if history else None,
            "prior_package": None, "package_history": history, "main_history": [],
            "independent_confirmation_from_main": False})
    return stories



def validate_chart_inputs(packet, documents):
    """Desk charts retain the producer's exact series, window and capture bindings."""
    docs = {d.get("document_id"): d for d in documents}
    metadata = {row.get("document_id"): row for row in packet.get("desk_series", [])}
    for series in packet.get("series", []):
        for point in series.get("points", []):
            for operand in point.get("inputs", []):
                doc = docs.get(operand.get("document_id"), {})
                binding = doc.get("desk_record_binding")
                if not binding:
                    continue
                info = binding.get("series")
                if binding.get("record_type") != "data_series" or not info:
                    raise ValueError("DESK_CHART_DATA_SERIES_REQUIRED")
                expected = {"document_id": doc["document_id"], "export_id": binding["export_id"],
                    "record_id": binding["record_id"], **info,
                    "captures": [{k: source[k] for k in ("source_id", "raw_sha256", "known_at_utc")}
                        for source in binding["sources"]]}
                if metadata.get(doc["document_id"]) != expected:
                    raise ValueError("DESK_CHART_SERIES_WINDOW_OR_CAPTURE_CHANGED")
                field = next((f for f in binding["fields"] if f["field_path"] == "/observations"), None)
                if not field:
                    raise ValueError("DESK_CHART_PUBLIC_OBSERVATIONS_REQUIRED")
                row = next((r for r in field["value"] if r["period"] == operand.get("source_period_text")), None)
                if (not row or operand.get("prepared_period") != row["period"] or point.get("period") != row["period"]
                        or operand.get("value_text") != display_value({"value": row["value"], "decimals": info["decimals"]})
                        or operand.get("unit") != info["unit"] or packet.get("unit") != info["unit"]
                        or point.get("transform") != "IDENTITY" or point.get("scale", 1) != 1
                        or len(point["inputs"]) != 1 or type(point.get("value")) not in (int, float)
                        or point["value"] != row["value"]):
                    raise ValueError("DESK_CHART_EXACT_OBSERVATION_REQUIRED")
                caption = packet.get("source_caption", "")
                if any(info["window"][key] not in caption for key in ("start", "end")):
                    raise ValueError("DESK_CHART_VISIBLE_WINDOW_REQUIRED")
                if any(source.get("attribution") and source["attribution"] not in caption for source in binding["sources"]):
                    raise ValueError("DESK_CHART_ATTRIBUTION_REQUIRED")
