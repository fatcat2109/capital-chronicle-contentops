"""Published-corpus read model derived from existing durable publication truth.

Owner decision 2026-08-10 (V1 realignment): every editorial decision must know what ContentOps
already published. This read model derives the canonical published corpus from the EXISTING
durable store publication lifecycle (platform_dispatches/outbox/work_items) and cycle output
artifacts - it never creates a second publication truth store.

Long-term token discipline: local decisions may hash/index/summarize the full corpus
deterministically and only send the most relevant prior article(s) to a model; the LOCAL
decision system always considers the complete corpus so coverage is never forgotten.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Optional

from live_contentops.editorial_portfolio_v1 import PublishedArticleRef

CORPUS_SCHEMA_VERSION = "contentops.published_corpus_read_model.v1"
REAL_PUBLICATION = "REAL_PUBLICATION_CONFIRMED"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()


def _entities_from_window_dir(window_dir: Path) -> tuple:
    evidence_path = window_dir / "rolling_x_newsroom_cycle_evidence_v1.json"
    if not evidence_path.is_file():
        return tuple()
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return tuple()
    selected = (evidence.get("ranked_viability") or {}).get("selected_cluster") or {}
    return tuple(str(value) for value in (selected.get("entities_topics") or []))[:12]


def _article_title_from_window_dir(window_dir: Path) -> Optional[str]:
    evidence_path = window_dir / "rolling_x_newsroom_cycle_evidence_v1.json"
    if not evidence_path.is_file():
        return None
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    article = (evidence.get("article") or {})
    if isinstance(article, Mapping):
        return str(article.get("title") or "") or None
    return None


def load_published_corpus(
    store: Any,
    *,
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    """Load every confirmed canonical published article identity from durable truth."""
    output_dir_root = Path(output_root) if output_root else None
    records: list[PublishedArticleRef] = []
    with store.get_connection() as conn:
        dispatch_rows = conn.execute(
            "SELECT d.dispatch_id, d.platform, d.public_object_id, d.public_object_url_hash,"
            " d.dispatched_at, m.work_item_id, m.message_id"
            " FROM platform_dispatches d"
            " LEFT JOIN outbox_messages m ON m.message_id = d.message_id"
            " ORDER BY d.dispatched_at"
        ).fetchall()
        lifecycle_rows = {
            str(row["dispatch_id"]): str(row["status"] or "")
            for row in conn.execute("SELECT dispatch_id, status FROM platform_dispatches").fetchall()
        }
        work_titles = {
            str(row["work_item_id"]): str(row["title"] or "")
            for row in conn.execute("SELECT work_item_id, title FROM work_items").fetchall()
        }
    for row in dispatch_rows:
        status = lifecycle_rows.get(str(row["dispatch_id"]), "")
        if status != REAL_PUBLICATION:
            continue
        work_item_id = str(row["work_item_id"] or "")
        window_dir = (output_dir_root / work_item_id) if (output_dir_root and work_item_id) else None
        entities = _entities_from_window_dir(window_dir) if window_dir else tuple()
        title = (_article_title_from_window_dir(window_dir) if window_dir else None) or work_titles.get(work_item_id) or str(row["dispatch_id"])
        body_source = None
        if window_dir is not None and window_dir.is_dir():
            body_source = _sha256_text(title + json.dumps(sorted(entities)))
        records.append(
            PublishedArticleRef(
                story_identity=work_item_id or str(row["dispatch_id"]),
                title=title,
                published_at_utc=str(row["dispatched_at"] or ""),
                public_object_id=(str(row["public_object_id"]) if row["public_object_id"] else None),
                canonical_url_hash=(str(row["public_object_url_hash"]) if row["public_object_url_hash"] else None),
                content_hash=body_source,
                entities=entities,
                update_chain_identity=None,
                article_mode=None,
            )
        )
    return {
        "schema_version": CORPUS_SCHEMA_VERSION,
        "articles": records,
        "article_count": len(records),
        "content_hash_coverage": sum(1 for record in records if record.content_hash),
        "full_text_held_locally": False,
        "derived_from_existing_durable_truth": True,
        "second_publication_store_created": False,
    }


def corpus_entity_index(corpus: Mapping[str, Any]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for article in corpus.get("articles") or []:
        for entity in article.entities:
            index.setdefault(str(entity), []).append(article.story_identity)
    return index
