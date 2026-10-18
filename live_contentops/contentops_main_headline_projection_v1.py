"""Bounded ContentOps -> Main projection; capture and legal authority stay upstream.

Unknown/restricted rows produce hash-only gaps. Canonical X membership is reporting
provenance, never a grant to export the underlying text to another consumer.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import uuid4
from urllib.parse import urlsplit

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    LatestReportDeliveryTracker,
    PUBLIC_RIGHTS,
    _private,
    _time,
    sha256_of,
)
from live_contentops.capital_chronicle_report_feed_v1 import _persist

SCHEMA = "contentops.main_headline_projection.v1"
DESTINATION = "internal:contentops-main-headline-export"


def project_headline(
    row: Mapping[str, Any], *, cutoff_utc: str, locator: Mapping[str, Any]
) -> tuple[dict[str, Any] | None, str | None]:
    if _private(row):
        return None, "PRIVATE_CONTEXT_EXCLUDED"
    permissions = row.get("source_permissions") or {}
    rights = row.get("rights_state")
    # Explicit official-public-domain rows or record-bound internal grants only.
    source_url = str(row.get("source_url") or row.get("tweet_url") or "")
    source_host = str(urlsplit(source_url).hostname or "").lower()
    official = (
        isinstance(rights, str)
        and rights in PUBLIC_RIGHTS
        and (source_host == "eia.gov" or source_host.endswith(".eia.gov"))
    )
    text = " ".join(str(row.get("headline_text") or "").split())
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    scoped = (
        permissions.get("content_sha256") == text_hash
        and permissions.get("source_identity") == row.get("source_identity")
        and permissions.get("INTERNAL_ANALYSIS_ALLOWED") is True
        and permissions.get("MODEL_INPUT_ALLOWED") is True
        and permissions.get("LLM_INPUT_ALLOWED") is True
        and permissions.get("provider_safe") is True
        and bool(
            {"internal_research", "narrative_context"}.intersection(
                permissions.get("permitted_consumers", [])
            )
        )
    )
    proof = str(
        row.get("rights_evidence_sha256")
        or permissions.get("rights_evidence_sha256")
        or ""
    )
    if isinstance(rights, str) and any(
        marker in rights.upper() for marker in ("FORBIDDEN", "BLOCKED", "NOT_ALLOWED")
    ):
        return None, "SOURCE_RIGHTS_FORBID_INTERNAL_ANALYSIS"
    if (
        not (official or scoped)
        or len(proof) != 64
        or any(c not in "0123456789abcdef" for c in proof)
    ):
        return None, "SOURCE_RIGHTS_MISSING_NO_GOVERNED_INHERITANCE"
    known = row.get("known_at_utc") or row.get("captured_at_utc")
    retrieved = row.get("retrieval_time_utc") or row.get("captured_at_utc")
    published = row.get("headline_timestamp") or row.get("published_at_utc")
    revision = row.get("revision_at_utc") or known
    try:
        if _time(retrieved) > _time(cutoff_utc) or _time(revision) > _time(cutoff_utc):
            return None, "FUTURE_HEADLINE_DEFERRED"
        if not (_time(published) <= _time(known) <= _time(retrieved)) or _time(
            revision
        ) < _time(known):
            return None, "HEADLINE_CLOCK_ORDER_OR_FUTURE"
    except ValueError:
        return None, "HEADLINE_CLOCK_UNAVAILABLE"
    identity = row.get("source_identity")
    url = source_url
    if not text or not identity or not url.startswith("https://"):
        return None, "HEADLINE_SOURCE_IDENTITY_UNAVAILABLE"
    if row.get("text_sha256") not in (None, text_hash):
        return None, "HEADLINE_TEXT_HASH_MISMATCH"
    output = {
        "schema_version": SCHEMA,
        "headline_id": str(row.get("headline_id") or "headline-" + text_hash),
        "headline_text": text,
        "text_sha256": text_hash,
        "source_identity": identity,
        "source_platform": row.get("source_platform") or identity,
        "reporting_identity": row.get("reporting_identity") or identity,
        "source_url": url,
        "claimed_origins": [url],
        "headline_timestamp": published,
        "captured_at_utc": known,
        "known_at_utc": known,
        "retrieval_time_utc": retrieved,
        "revision_at_utc": revision,
        "rights_state": rights
        if official
        else {
            k: permissions[k]
            for k in (
                "INTERNAL_ANALYSIS_ALLOWED",
                "MODEL_INPUT_ALLOWED",
                "LLM_INPUT_ALLOWED",
                "provider_safe",
            )
        },
        "rights_evidence_sha256": proof,
        "allowed_consumers": ["internal_research", "narrative_context"]
        if official
        else sorted(
            {"internal_research", "narrative_context"}.intersection(
                permissions["permitted_consumers"]
            )
        ),
        "permitted_uses": ["INTERNAL_ATTRIBUTED_REPORT_CONTEXT"],
        "public_republication_authority": False,
        "numeric_authority_granted": False,
        "report_truth_only": True,
        "underlying_event_truth_granted": False,
        "candidate_catalyst_tags": list(row.get("candidate_catalyst_tags") or []),
        "context_only": True,
        "source_record_locator": dict(locator),
        "source_capture_sha256": row.get("source_capture_sha256"),
        "upstream_report_lineage": row.get("upstream_report_lineage"),
    }
    return {**output, "projection_sha256": sha256_of(output)}, None


def permitted_report_headlines(
    tracker: LatestReportDeliveryTracker,
) -> list[dict[str, Any]]:
    """Retained public source facts, explicitly identified as Main-origin round trips."""
    rows = []
    for r in tracker.receipts():
        if r["status"] != "ADMITTED" or r["delivery_status"] == "REPORT_SUPERSEDED":
            continue
        for c in r["claims"]:
            if c["producer_layer"] != "OBSERVED_SOURCE_FACT":
                continue
            for e in c["evidence"]:
                rows.append(
                    {
                        "headline_id": "main-public-fact-"
                        + sha256_of(
                            [
                                r["source_report_sha256"],
                                c["claim_hash"],
                                e["evidence_id"],
                            ]
                        ),
                        "headline_text": c["text"],
                        "source_identity": e["source_identity"],
                        "reporting_identity": "Capital Chronicle sealed Main report",
                        "source_url": e["source_url"],
                        "source_platform": "RETAINED_MAIN_PUBLIC_SOURCE_FACT_PROJECTION",
                        "headline_timestamp": e["observation_time_utc"],
                        "known_at_utc": e["known_at_utc"],
                        "retrieval_time_utc": e["retrieval_time_utc"],
                        "revision_at_utc": r["known_at_cutoff_utc"],
                        "rights_state": c["rights_state"],
                        "rights_evidence_sha256": e["rights_evidence_sha256"],
                        "source_capture_sha256": e["source_hash"],
                        "candidate_catalyst_tags": ["energy"],
                        "upstream_report_lineage": {
                            "report_id": r["report_id"],
                            "report_version": r["report_version"],
                            "report_sha256": r["source_report_sha256"],
                            "claim_hash": c["claim_hash"],
                            "novel_contentops_reporting": False,
                        },
                    }
                )
    return rows


class MainHeadlineExporter:
    def __init__(self, store):
        self.store = store

    def export(
        self,
        *,
        batch_id: str,
        paths: Sequence[str | Path],
        cutoff_utc: str,
        max_rows: int = 500,
        max_files: int = 4,
        permitted_rows: Sequence[Mapping[str, Any]] = (),
        authority_revision: str = "retained-record-permissions-v1",
    ) -> dict[str, Any]:
        if not 1 <= max_rows <= 1000 or not 1 <= max_files <= 16:
            raise ValueError("headline_export_bound_invalid")
        identity = "headline-export-" + sha256_of(batch_id)
        previous = self.store.get_outbox_message(identity)
        if previous:
            return json.loads(previous["payload"])
        owner = "headline-export-" + uuid4().hex
        lease = self.store.acquire_lease(DESTINATION, owner, ttl_seconds=120)
        try:
            pages = [
                json.loads(r["payload"])
                for r in self.store.list_outbox_messages()
                if r["destination"] == DESTINATION
            ]
            last = max(pages, key=lambda p: p["sequence"], default={})
            cursors = (
                dict(last.get("cursors", {}))
                if last.get("authority_revision") == authority_revision
                else {}
            )

            def content_identity(r):
                return sha256_of(
                    [
                        r["headline_id"],
                        r["text_sha256"],
                        r["revision_at_utc"],
                        r["rights_evidence_sha256"],
                    ]
                )

            seen = {content_identity(r) for p in pages for r in p["rows"]}
            rows, gaps, scanned, files = [], [], 0, []
            candidates = sorted({Path(p).resolve() for p in paths}, key=str)
            for path in candidates:
                if len(files) >= max_files or scanned >= max_rows:
                    break
                key = sha256_of(str(path))
                cursor = cursors.get(
                    key,
                    {
                        "offset": 0,
                        "prefix_sha256": hashlib.sha256(b"").hexdigest(),
                        "line": 0,
                    },
                )
                try:
                    with path.open("rb") as handle:
                        prefix = handle.read(cursor["offset"])
                        if (
                            hashlib.sha256(prefix).hexdigest()
                            != cursor["prefix_sha256"]
                        ):
                            gaps.append(
                                {
                                    "source_locator_sha256": key,
                                    "state": "HEADLINE_SOURCE_PREFIX_CHANGED",
                                }
                            )
                            continue
                        if handle.tell() == path.stat().st_size:
                            continue
                        digest = hashlib.sha256(prefix)
                        line = cursor["line"]
                        while scanned < max_rows:
                            raw = handle.readline(1_048_577)
                            if not raw:
                                break
                            if not raw.endswith(b"\n"):
                                gaps.append(
                                    {
                                        "source_locator_sha256": key,
                                        "state": "OVERSIZED_OR_PARTIAL_HEADLINE_DEFERRED",
                                    }
                                )
                                break
                            line += 1
                            scanned += 1
                            digest.update(raw)
                            locator = {
                                "source_file_sha256_id": key,
                                "line": line,
                                "record_raw_sha256": hashlib.sha256(raw).hexdigest(),
                            }
                            try:
                                value = json.loads(raw)
                                projected, reason = project_headline(
                                    value, cutoff_utc=cutoff_utc, locator=locator
                                )
                            except (ValueError, TypeError, AttributeError):
                                projected, reason = None, "MALFORMED_HEADLINE_ROW"
                            if reason == "FUTURE_HEADLINE_DEFERRED":
                                # Keep future rows pending rather than committing past their clock.
                                line -= 1
                                handle.seek(-len(raw), 1)
                                digest = hashlib.sha256(prefix)
                                with path.open("rb") as restore:
                                    digest = hashlib.sha256(restore.read(handle.tell()))
                                gaps.append({**locator, "state": reason})
                                break
                            if projected and content_identity(projected) not in seen:
                                rows.append(projected)
                                seen.add(content_identity(projected))
                            elif reason:
                                gaps.append({**locator, "state": reason})
                            cursors[key] = {
                                "offset": handle.tell(),
                                "prefix_sha256": digest.hexdigest(),
                                "line": line,
                            }
                        files.append(
                            {
                                "source_locator_sha256": key,
                                "snapshot_bytes": path.stat().st_size,
                                "committed_offset": cursors.get(key, cursor)["offset"],
                            }
                        )
                except OSError:
                    gaps.append(
                        {
                            "source_locator_sha256": key,
                            "state": "HEADLINE_SOURCE_UNAVAILABLE",
                        }
                    )
            for row in permitted_rows[:100]:
                projected, reason = project_headline(
                    row,
                    cutoff_utc=cutoff_utc,
                    locator={"retained_authority": "SEALED_MAIN_PUBLIC_REPORT"},
                )
                if projected and content_identity(projected) not in seen:
                    rows.append(projected)
                    seen.add(content_identity(projected))
                elif reason:
                    gaps.append({"state": reason, "record_sha256": sha256_of(row)})
            page = {
                "schema_version": SCHEMA,
                "sequence": int(last.get("sequence", 0)) + 1,
                "parent_page_sha256": last.get("page_sha256"),
                "authority_revision": authority_revision,
                "batch_id": batch_id,
                "observed_at_utc": cutoff_utc,
                "rows": rows,
                "gaps": gaps,
                "source_rows_scanned": scanned,
                "eligible_rows": len(rows),
                "missing_rows": len(gaps),
                "cursors": cursors,
                "files": files,
                "discovered_file_count": len(candidates),
                "coverage": "BOUNDED_INCREMENTAL_PREFIXES_NOT_HISTORICAL_COMPLETENESS",
                "bulk_capture_mutated": False,
                "public_write_performed": False,
            }
            page["page_sha256"] = sha256_of(page)
            _persist(self.store, identity, page, DESTINATION)
            return page
        finally:
            self.store.release_lease(lease["lease_id"], owner, lease["fencing_token"])
