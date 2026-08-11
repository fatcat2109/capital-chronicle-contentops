"""Read-only current-state canary for ContentOps preselection intelligence."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from live_contentops.capital_chronicle_data_catalog_v1 import (
    DEFAULT_CC_ROOT,
    discover_cc_data_estate,
    query_story_scoped_cc_context,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.newsroom_assignment_scheduler_v1 import (
    load_rolling_x_headline_sidecars,
)
from live_contentops.published_corpus_read_model_v1 import load_published_corpus

SCHEMA_VERSION = "contentops.preselection_read_only_canary.v1"
DEFAULT_SIDECAR_GLOB = "headline_ingestion/data/intake/headline_sidecars/*.jsonl"
_STOPWORDS = {
    "about", "after", "again", "against", "also", "been", "before", "being", "between",
    "could", "from", "have", "into", "just", "more", "most", "over", "says", "than",
    "that", "their", "there", "these", "they", "this", "today", "under", "were", "what",
    "when", "where", "which", "while", "with", "would", "https", "breaking", "report",
    "t.co", "first",
}


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _current_terms(headlines: list[dict[str, Any]]) -> list[str]:
    """Compact deterministic terms from recent untrusted discovery text; no LLM."""
    recent = sorted(
        headlines,
        key=lambda row: (
            str(row.get("source_timestamp_utc") or ""),
            str(row.get("headline_id") or ""),
        ),
        reverse=True,
    )[:80]
    counts: Counter[str] = Counter()
    display: dict[str, str] = {}
    for row in recent:
        external = row.get("external_content") or {}
        text = str(external.get("headline_text") or "")
        for token in re.findall(r"[A-Za-z][A-Za-z0-9.-]{3,}", text):
            normalized = token.casefold().strip(".-")
            if (
                normalized in _STOPWORDS
                or normalized.startswith(("http", "www"))
                or normalized.endswith((".co", ".com", ".org", ".net"))
            ):
                continue
            counts[normalized] += 1
            display.setdefault(normalized, token.strip(".-"))
    return [display[token] for token, _ in sorted(
        counts.items(), key=lambda item: (-item[1], item[0])
    )[:6]]


def build_read_only_preselection_canary(
    *,
    store_path: str | Path,
    cc_root: str | Path = DEFAULT_CC_ROOT,
    sidecar_glob: str = DEFAULT_SIDECAR_GLOB,
    now: datetime | None = None,
) -> dict[str, Any]:
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    store = ContentOpsDurableStore(Path(store_path), auto_migrate=False)
    with store.get_read_only_connection() as conn:
        schema_version = int(
            conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] or 0
        )
        lifecycle = {
            "unknown_write_count": int(conn.execute(
                "SELECT COUNT(*) FROM platform_dispatches WHERE status='UNKNOWN_WRITE'"
            ).fetchone()[0]),
            "attempt_started_count": int(conn.execute(
                "SELECT COUNT(*) FROM platform_dispatches WHERE status='ATTEMPT_STARTED'"
            ).fetchone()[0]),
            "pending_reconciliation_count": int(conn.execute(
                "SELECT COUNT(*) FROM reconciliations WHERE status IN "
                "('PENDING','RECONCILIATION_PENDING','RECONCILIATION_PENDING_READBACK',"
                "'RECONCILIATION_PENDING_OPERATOR_RECOVERY')"
            ).fetchone()[0]),
            "active_editorial_dispatch_count": int(conn.execute(
                "SELECT COUNT(DISTINCT w.work_item_id) FROM work_items w JOIN leases l "
                "ON l.work_item_id=w.work_item_id WHERE w.current_state='EVIDENCE_PENDING' "
                "AND l.status='ACTIVE' AND l.expires_at>?",
                (_iso(moment),),
            ).fetchone()[0]),
        }
    intake = load_rolling_x_headline_sidecars(
        cutoff_utc=_iso(moment), sidecar_glob=sidecar_glob, window_hours=24.0
    )
    headlines = [
        dict(row) for row in (intake.get("headlines") or []) if isinstance(row, dict)
    ]
    terms = _current_terms(headlines)
    catalog = discover_cc_data_estate(cc_root=cc_root)
    cc_context = query_story_scoped_cc_context(catalog, terms)
    corpus = load_published_corpus(store)
    return {
        "schema_version": SCHEMA_VERSION,
        "evaluated_at_utc": _iso(moment),
        "production_store_path": str(Path(store_path).resolve()),
        "production_store_schema_version": schema_version,
        "rolling_24h": {
            "counts": dict(intake.get("counts") or {}),
            "canonical_input_hash": intake.get("canonical_input_hash"),
            "current_term_count": len(terms),
            "current_terms": terms,
            "raw_headline_text_persisted_in_report": False,
            "x_content_grants_factual_or_numeric_authority": False,
        },
        "capital_chronicle": {
            "store_count_total": catalog.get("store_count_total"),
            "store_count_discovered": catalog.get("store_count_discovered"),
            "stores_omitted": catalog.get("stores_omitted"),
            "table_count_discovered": sum(
                int(row.get("table_count") or 0) for row in catalog.get("stores") or []
            ),
            "discovery_complete": catalog.get("discovery_complete"),
            "catalog_fingerprint": catalog.get("catalog_fingerprint"),
            "matched_store_count": cc_context.get("matched_store_count"),
            "matched_store_ids": cc_context.get("matched_store_ids"),
            "matched_table_count": cc_context.get("matched_table_count"),
            "cc_context_richness": cc_context.get("cc_context_richness"),
            "mutated_upstream": False,
            "grants_factual_or_numeric_authority": False,
        },
        "published_corpus": {
            "article_count": corpus.get("article_count"),
            "lifecycle_confirmed_derivative_count": corpus.get(
                "lifecycle_confirmed_derivative_count"
            ),
            "full_text_article_count": corpus.get("full_text_article_count"),
            "content_unavailable_count": corpus.get("content_unavailable_count"),
            "canonical_publication_contract": corpus.get(
                "canonical_publication_contract"
            ),
        },
        "lifecycle_safety": lifecycle,
        "read_only": True,
        "llm_or_provider_calls": 0,
        "public_write_performed": False,
        "upstream_mutation_performed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store-path", required=True)
    parser.add_argument("--cc-root", default=str(DEFAULT_CC_ROOT))
    parser.add_argument("--sidecar-glob", default=DEFAULT_SIDECAR_GLOB)
    args = parser.parse_args(argv)
    print(json.dumps(build_read_only_preselection_canary(
        store_path=args.store_path,
        cc_root=args.cc_root,
        sidecar_glob=args.sidecar_glob,
    ), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
