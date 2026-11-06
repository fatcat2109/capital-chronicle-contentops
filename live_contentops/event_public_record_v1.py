"""CC-338: bind Main's frozen public subset to the existing event article path.

Ops Live supplies the file and its SHA-256. This consumer never freezes a forecast,
calculates a probability or score, or rewrites the bytes readers will download.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

from live_contentops.event_article_guard_v1 import (
    CONFLICTS_NOTICE, PUBLIC_NOTICE, check_publication_copy,
)
from live_contentops.public_call_scorecard_v1 import public_time
from live_contentops.published_content_v1 import load_json, utc

SCHEMA = "capital_chronicle.frozen_public_calls.v1"
SHA = re.compile(r"[a-f0-9]{64}")
ROOT_KEYS = {"schema_version", "event_id", "event_time_utc", "frozen_at_utc",
             "reaction_map", "q1_probabilities", "resolution_rule"}
CALL_KEYS = {"condition", "market", "direction", "horizon", "invalidation"}
BINDING_KEYS = {"source_ref", "source_sha256", "known_at_utc"}


def load_record(spec, *, event_id, event_time_utc, cutoff_utc):
    """Accept only a bound public subset; never upload a raw private dossier."""
    path = Path(spec["path"])
    if path.stat().st_size > 2_000_000:
        raise ValueError("FROZEN_PUBLIC_RECORD_TOO_LARGE")
    raw = path.read_bytes()
    digest = sha256(raw).hexdigest()
    if digest != spec.get("sha256"):
        raise ValueError("FROZEN_PUBLIC_RECORD_BYTES_MISMATCH")
    doc = load_json(raw)
    if (not isinstance(doc, dict) or set(doc) != ROOT_KEYS or doc.get("schema_version") != SCHEMA
            or doc.get("event_id") != event_id or utc(doc["event_time_utc"]) != utc(event_time_utc)):
        raise ValueError("FROZEN_PUBLIC_RECORD_EVENT_OR_SCHEMA_INVALID")
    frozen = utc(doc["frozen_at_utc"])
    if frozen >= utc(event_time_utc) or frozen > utc(cutoff_utc):
        raise ValueError("FROZEN_PUBLIC_RECORD_CLOCK_INVALID")
    if not isinstance(doc["reaction_map"], list) or not doc["reaction_map"]:
        raise ValueError("FROZEN_CONDITIONAL_REACTION_MAP_REQUIRED")

    def bound(row, keys):
        if (not isinstance(row, dict) or set(row) != keys | BINDING_KEYS
                or any(not isinstance(v, str) or not v.strip() for v in row.values())
                or not SHA.fullmatch(row["source_sha256"]) or utc(row["known_at_utc"]) > frozen):
            raise ValueError("FROZEN_PUBLIC_FIELD_SOURCE_BINDING_INVALID")

    calls = []
    for row in doc["reaction_map"]:
        bound(row, CALL_KEYS | {"minimum_move", "naive_release_beta"})
        calls.append({k: row[k] for k in CALL_KEYS})
    if not isinstance(doc["q1_probabilities"], list):
        raise ValueError("FROZEN_Q1_PROBABILITIES_ARRAY_REQUIRED")
    for row in doc["q1_probabilities"]:
        bound(row, {"question", "outcome", "probability"})
    if not isinstance(doc["resolution_rule"], str) or not doc["resolution_rule"].strip():
        raise ValueError("FROZEN_RESOLUTION_RULE_REQUIRED")
    # Reject execution details, advice and prediction-market numbers in values.
    # Structured keys/hash strings are not reader-facing numerical claims.
    copy = {"notice": PUBLIC_NOTICE, "conflicts": CONFLICTS_NOTICE,
            "resolution_rule": doc["resolution_rule"],
            "reaction_map": [{k: v for k, v in r.items() if k not in BINDING_KEYS | {"direction"}}
                             for r in doc["reaction_map"]],
            "q1_probabilities": [{k: v for k, v in r.items() if k not in BINDING_KEYS}
                                 for r in doc["q1_probabilities"]]}
    check_publication_copy(copy, conditional_calls=calls, require_call_text=False)
    # Source references are provenance, but still may not contain private text or secrets.
    from tools.product.desk_record_projection_v1 import public_text_problems
    if public_text_problems(json.dumps(doc, ensure_ascii=False)):
        raise ValueError("FROZEN_PUBLIC_RECORD_TEXT_FORBIDDEN")
    return {"path": str(path.resolve()), "sha256": digest, "bytes": len(raw),
            "event_id": event_id, "event_time_utc": doc["event_time_utc"],
            "frozen_at_utc": doc["frozen_at_utc"], "frozen_at_et": public_time(doc["frozen_at_utc"]),
            "preview_deadline_utc": (utc(event_time_utc) - timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
            "record": doc}


def record_document(spec, *, event_id, event_time_utc, cutoff_utc):
    record = load_record(spec, event_id=event_id, event_time_utc=event_time_utc, cutoff_utc=cutoff_utc)
    # The source pack uses exact decoded source text. Upload always uses original bytes.
    text = (f"Frozen: {record['frozen_at_et']}\nSHA-256: {record['sha256']}\n"
            "Capital Chronicle model estimate\n" + Path(record["path"]).read_bytes().decode("utf-8-sig"))
    digest = sha256(text.encode()).hexdigest()
    return {"document_id": "event-public-record-" + record["sha256"],
            "source_url": "urn:cc-public-report:event-freeze:" + record["sha256"],
            "publisher": "Capital Chronicle", "published_at_utc": record["frozen_at_utc"],
            "known_at_utc": record["frozen_at_utc"],
            "canonical_content_text": text, "canonical_content_sha256": digest,
            "raw_sha256": record["sha256"], "content_truncated": False,
            "public_claim_allowed": True,
            "source_authority_class": "governed_capital_chronicle_report_only",
            "frozen_public_record": record,
            "source_reuse_constraints": {"scope": "CAPITAL_CHRONICLE_OWN_FROZEN_PUBLIC_SUBSET",
                "authority_ref": "BACKLOG_CC338_JIM_DECISIONS_40_84_90",
                "MODEL_INPUT_ALLOWED": True, "LLM_INPUT_ALLOWED": True,
                "INTERNAL_ANALYSIS_ALLOWED": True, "public_expression_reuse_allowed": True}}


def attach_research_records(records, spec, *, event_id, event_time_utc, cutoff_utc, article_type):
    """Add exact context to the existing retained-source snapshot, not a new candidate."""
    document = record_document(spec, event_id=event_id, event_time_utc=event_time_utc, cutoff_utc=cutoff_utc)
    _attach_context(records, document, event_id=event_id, article_type=article_type)


def _attach_context(records, document, *, event_id, article_type):
    identity = document["document_id"]
    template = deepcopy(next(iter(records.values())))
    for row in records.values():
        row["supporting_headline_ids"] = [*row.get("supporting_headline_ids", []), identity]
    rights = document["source_reuse_constraints"]
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    template.update(headline_id=identity, headline_text="Main's frozen public conditional reaction map",
        text_sha256=document["canonical_content_sha256"], context_only=True,
        source_identity="Capital Chronicle", source_account="Capital Chronicle",
        source_url=document["source_url"], official_source_urls=[],
        source_timestamp_utc=document["known_at_utc"], headline_timestamp=document["known_at_utc"],
        known_at_utc=document["known_at_utc"], retrieval_time_utc=document["known_at_utc"],
        revision_at_utc=document["known_at_utc"], rights_state="CC_OWN_ANALYSIS",
        source_capture_sha256=document["raw_sha256"], source_permissions=rights,
        source_permission_record_sha256=sha256_of(rights), rights_evidence_sha256=sha256_of(rights),
        permitted_source_text=document["canonical_content_text"], document=document,
        supporting_headline_ids=[], research_metadata={"event_id": event_id, "article_type": article_type,
                                                       "context_only": True})
    records[identity] = template


def attach_scorecard_record(records, store, *, cutoff_utc, feed_path=None):
    from live_contentops.public_call_scorecard_v1 import build_scorecard, render_scorecard
    from live_contentops.published_content_v1 import DEFAULT_FEED
    scorecard = build_scorecard(store, feed_path=feed_path or DEFAULT_FEED, as_of_utc=cutoff_utc)
    text = render_scorecard(scorecard)
    digest = sha256(text.encode()).hexdigest()
    first = next(iter(records.values()))
    document = {"document_id": "public-call-scorecard-" + digest,
        "source_url": "urn:cc-public-report:call-scorecard:" + digest,
        "publisher": "Capital Chronicle", "published_at_utc": cutoff_utc, "known_at_utc": cutoff_utc,
        "canonical_content_text": text, "canonical_content_sha256": digest, "raw_sha256": digest,
        "content_truncated": False, "public_claim_allowed": True,
        "source_authority_class": "governed_capital_chronicle_report_only",
        "public_call_scorecard": scorecard,
        "source_reuse_constraints": {"scope": "CAPITAL_CHRONICLE_OWN_PUBLIC_CALL_SCORECARD",
            "authority_ref": "BACKLOG_CC338_JIM_DECISIONS_40_84_90", "public_expression_reuse_allowed": True,
            "MODEL_INPUT_ALLOWED": True, "LLM_INPUT_ALLOWED": True, "INTERNAL_ANALYSIS_ALLOWED": True}}
    _attach_context(records, document, event_id=first["research_metadata"]["event_id"], article_type="EVENT_REVIEW")


def verified_source_metadata(document):
    """Allow the two exact owned contexts through the existing source-pack normalizer."""
    record = document.get("frozen_public_record")
    card = document.get("public_call_scorecard")
    if not record and not card:
        return {}
    if record:
        expected = record_document(record, event_id=record["event_id"], event_time_utc=record["event_time_utc"],
                                   cutoff_utc=record["frozen_at_utc"])
        if any(document.get(k) != expected[k] for k in ("source_url", "canonical_content_text", "canonical_content_sha256")):
            raise ValueError("FROZEN_PUBLIC_SOURCE_DOCUMENT_CHANGED")
        return {"frozen_public_record": deepcopy(expected["frozen_public_record"])}
    from live_contentops.public_call_scorecard_v1 import render_scorecard
    text = render_scorecard(card)
    digest = sha256(text.encode()).hexdigest()
    if (document.get("source_url") != "urn:cc-public-report:call-scorecard:" + digest
            or document.get("canonical_content_text") != text or document.get("canonical_content_sha256") != digest):
        raise ValueError("PUBLIC_CALL_SCORECARD_SOURCE_CHANGED")
    return {"public_call_scorecard": deepcopy(card)}


def validate_article_record(article, source_pack):
    """Bind copy and an optional review attachment before review/publication."""
    found = [d["frozen_public_record"] for d in source_pack if d.get("frozen_public_record")]
    if not found:
        return None  # immutable historical packets keep their original contract
    if len({r["sha256"] for r in found}) != 1:
        raise ValueError("EVENT_PUBLIC_RECORD_CONFLICT")
    record = found[0]
    record = load_record(record, event_id=record["event_id"], event_time_utc=record["event_time_utc"],
                         cutoff_utc=record["frozen_at_utc"])
    kind = article.get("article_type")
    if kind not in {"EVENT_PREVIEW", "EVENT_REVIEW"}:
        raise ValueError("FROZEN_RECORD_EVENT_ARTICLE_TYPE_REQUIRED")
    text = "\n".join(str(article.get(k) or "") for k in ("title", "subtitle", "substack_body_markdown"))
    if record["sha256"] not in text or record["frozen_at_et"] not in text:
        raise ValueError("EVENT_PUBLIC_HASH_AND_FREEZE_TIME_REQUIRED")
    if kind == "EVENT_PREVIEW":
        title = article.get("title", "").casefold()
        if not any(all(str(row[k]).casefold() in title for k in
                       ("condition", "market", "direction", "minimum_move", "horizon"))
                   for row in record["record"]["reaction_map"]):
            raise ValueError("PREVIEW_HEADLINE_CONDITIONAL_REACTION_MAP_REQUIRED")
    if kind == "EVENT_REVIEW":
        cards = [d["public_call_scorecard"] for d in source_pack if d.get("public_call_scorecard")]
        if cards:
            from live_contentops.public_call_scorecard_v1 import render_scorecard
            # Structured table belongs to code. All calls and the denominator survive prose editing.
            if render_scorecard(cards[0]).strip() not in article.get("substack_body_markdown", ""):
                raise ValueError("REVIEW_FULL_PUBLIC_CALL_SCORECARD_REQUIRED")
    return {k: v for k, v in record.items() if k != "record"}


def attachment_for_article(article, *, media_dir):
    """Materialize original bytes inside this article's own media folder only."""
    spec = article.get("frozen_public_record")
    if not spec or article.get("article_type") != "EVENT_REVIEW":
        return None
    record = load_record(spec, event_id=spec["event_id"], event_time_utc=spec["event_time_utc"],
                         cutoff_utc=spec["frozen_at_utc"])
    folder = Path(media_dir).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (record["sha256"] + ".json")
    raw = Path(record["path"]).read_bytes()
    if target.exists():
        if target.read_bytes() != raw:
            raise ValueError("REVIEW_ATTACHMENT_IMMUTABLE_BYTES_CONFLICT")
    else:
        with target.open("xb") as output:
            output.write(raw)
    return {"path": str(target), "sha256": record["sha256"], "bytes": len(raw),
            "media_type": "application/json", "filename": target.name}


def require_preview_deadline(article, *, now_utc=None):
    spec = article.get("frozen_public_record")
    if spec and article.get("article_type") == "EVENT_PREVIEW":
        now = utc(now_utc) if now_utc else datetime.now(timezone.utc)
        if now > utc(spec["preview_deadline_utc"]):
            raise ValueError("CC338_PREVIEW_TWO_HOUR_DEADLINE_MISSED_USE_NEXT_EVENT")


def attachment_readback_matches(expected, observed, public_object_url):
    """An observed download, not a displayed filename, proves the published hash."""
    return all(any(row.get("sha256") == asset["sha256"] and row.get("bytes") == asset["bytes"]
                   and row.get("download_verified") is True and row.get("public_object_url") == public_object_url
                   and str(row.get("url") or "").startswith("https://") for row in observed)
               for asset in expected)
