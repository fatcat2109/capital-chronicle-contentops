"""Read-only current-state canary for ContentOps preselection intelligence."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from live_contentops.capital_chronicle_data_catalog_v1 import (
    DEFAULT_CC_ROOT,
    discover_cc_data_estate,
    query_story_scoped_cc_context,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.editorial_portfolio_v1 import (
    PublishedArticleRef,
    portfolio_state_today,
)
from live_contentops.newsroom_assignment_scheduler_v1 import (
    load_rolling_x_headline_sidecars,
)
from live_contentops.published_corpus_read_model_v1 import load_published_corpus
from live_contentops.preselection_intelligence_v1 import apply_preselection_intelligence

SCHEMA_VERSION = "contentops.preselection_read_only_canary.v2"
from live_contentops.headline_data_root_v1 import canonical_headline_sidecar_glob

DEFAULT_SIDECAR_GLOB = canonical_headline_sidecar_glob()
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


def _bounded_canary_candidates(
    headlines: list[dict[str, Any]], *, limit: int = 4
) -> list[dict[str, Any]]:
    """Build a compact zero-model canary shortlist from newest distinct live rows.

    This is a read-only intelligence projection, not a replacement for the governed
    hierarchical semantic assignment used by an editorial cycle.
    """
    ordered = sorted(
        headlines,
        key=lambda row: (
            str(row.get("source_timestamp_utc") or ""),
            str(row.get("headline_id") or ""),
        ),
        reverse=True,
    )
    result: list[dict[str, Any]] = []
    seen_terms: set[tuple[str, ...]] = set()
    for row in ordered:
        external = row.get("external_content")
        external = external if isinstance(external, Mapping) else {}
        headline_text = str(external.get("headline_text") or "").strip()
        headline_id = str(row.get("headline_id") or "").strip()
        if not headline_id or not headline_text:
            continue
        terms = _current_terms([row])
        term_key = tuple(value.casefold() for value in terms[:3])
        if not term_key or term_key in seen_terms:
            continue
        seen_terms.add(term_key)
        result.append({
            "cluster_id": f"read-only-canary-{headline_id}",
            "rank": len(result) + 1,
            "headline_ids": [headline_id],
            "entities_topics": terms,
            "leaf_summaries": [headline_text],
            "official_source_urls": list(external.get("official_source_urls") or []),
            "source_timestamp_utc": str(row.get("source_timestamp_utc") or ""),
            "canary_candidate_only": True,
        })
        if len(result) >= max(1, int(limit)):
            break
    return result


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
    articles = [
        row for row in (corpus.get("articles") or [])
        if isinstance(row, PublishedArticleRef)
    ]
    candidates = _bounded_canary_candidates(headlines)
    preselection = apply_preselection_intelligence(
        candidates,
        published_corpus=articles,
        cc_catalog=catalog,
        now=moment,
    )
    held = list(preselection.get("held_clusters") or [])
    compact_candidates = []
    for row in [*(preselection.get("ranked_clusters") or []), *held]:
        novelty = row.get("preselection_novelty")
        novelty = novelty if isinstance(novelty, Mapping) else {}
        context = row.get("capital_chronicle_context")
        context = context if isinstance(context, Mapping) else {}
        compact_candidates.append({
            "cluster_id": row.get("cluster_id"),
            "headline_ids": list(row.get("headline_ids") or []),
            "source_timestamp_utc": row.get("source_timestamp_utc"),
            "entities_topics": list(row.get("entities_topics") or []),
            "original_rank": row.get("preselection_original_rank"),
            "resolved_rank": row.get("rank"),
            "editorial_classification": row.get("editorial_classification"),
            "resolved_article_mode": row.get("resolved_article_mode"),
            "preselection_score": row.get("preselection_score"),
            "cc_context_richness": context.get("cc_context_richness"),
            "cc_matched_store_ids": list(context.get("matched_store_ids") or []),
            "cc_matched_table_count": context.get("matched_table_count"),
            "portfolio_concentration_penalty": row.get(
                "portfolio_concentration_penalty"
            ),
            "prior_article_identity": novelty.get("best_prior_article"),
            "prior_article_title": novelty.get("best_prior_title"),
            "held_before_evidence_and_writing": row in held,
        })
    ranked = list(preselection.get("ranked_clusters") or [])
    selected = ranked[0] if ranked else None
    portfolio = portfolio_state_today(articles, now=moment)
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
            "published_today_canonical_article_count": portfolio.get(
                "published_today_count"
            ),
        },
        "preselection_intelligence": {
            "candidate_source": "NEWEST_DISTINCT_REAL_ROLLING_24H_ROWS_READ_ONLY_CANARY",
            "governed_hierarchical_assignment_replaced": False,
            "bounded_candidate_limit": 4,
            "candidate_count": len(candidates),
            "candidates": compact_candidates,
            "original_order": preselection.get("original_order"),
            "reranked_order": preselection.get("reranked_order"),
            "ranking_order_changed": preselection.get("ranking_order_changed"),
            "selected_or_hold": ({
                "decision": "SELECTED",
                "cluster_id": selected.get("cluster_id"),
                "editorial_classification": selected.get("editorial_classification"),
                "resolved_article_mode": selected.get("resolved_article_mode"),
            } if selected else {
                "decision": "HOLD",
                "cluster_id": None,
                "editorial_classification": "NO_PUBLICATION",
                "resolved_article_mode": "HOLD",
            }),
            "no_publication_reason": (
                "READ_ONLY_CANARY_DOES_NOT_START_A_CANONICAL_CYCLE_OR_GRANT_PUBLICATION_AUTHORITY"
            ),
            "occurs_before_targeted_evidence": preselection.get(
                "occurs_before_targeted_evidence"
            ),
            "occurs_before_article_generation": preselection.get(
                "occurs_before_article_generation"
            ),
            "llm_or_provider_calls": preselection.get("llm_or_provider_calls"),
            "raw_headline_text_persisted_in_report": False,
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
