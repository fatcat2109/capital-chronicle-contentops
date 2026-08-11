"""Canonical article corpus projected from the existing publication lifecycle.

Only a Substack canonical dispatch in ``DISPATCH_CONFIRMED`` with its exact coordinator
reconciliation in ``RECONCILED_CONFIRMED`` enters this corpus. Platform fan-out remains
derivative metadata on that one article; it never inflates article counts.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Optional
from urllib.parse import urlsplit

from live_contentops.editorial_portfolio_v1 import PublishedArticleRef

CORPUS_SCHEMA_VERSION = "contentops.published_corpus_read_model.v2"
DISPATCH_CONFIRMED = "DISPATCH_CONFIRMED"
RECONCILED_CONFIRMED = "RECONCILED_CONFIRMED"
CONTENT_AVAILABLE = "CONTENT_AVAILABLE"
CONTENT_UNAVAILABLE = "CONTENT_UNAVAILABLE"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    return dict(value) if isinstance(value, Mapping) else {}


def _intent(value: Any) -> dict[str, Any]:
    try:
        parsed = json.loads(str(value or ""))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return dict(parsed) if isinstance(parsed, Mapping) else {}


def _reconciliation_id_for_dispatch(dispatch_id: str) -> str:
    suffix = str(dispatch_id).removeprefix("dispatch_")
    return "reconciliation_" + suffix


def _valid_canonical_substack_url(value: Any) -> bool:
    try:
        parsed = urlsplit(str(value or "").strip())
    except ValueError:
        return False
    path = parsed.path.rstrip("/")
    return bool(
        parsed.scheme == "https"
        and (parsed.hostname or "").casefold() == "capitalchronicle.substack.com"
        and path.startswith("/p/")
        and len(path.removeprefix("/p/")) > 0
        and path != "/p/pending-publication"
        and not parsed.username
        and not parsed.password
    )


def _artifact_article(output_dir: Optional[Path]) -> dict[str, Any]:
    """Recover the canonical body/artifact identity; never manufacture content or a hash."""
    if output_dir is None or not output_dir.is_dir():
        return {
            "content_status": CONTENT_UNAVAILABLE,
            "content_hash": None,
            "full_text": None,
            "body_source": None,
            "article": {},
            "selection": {},
        }
    manifest_path = output_dir / "article_manifest_v1.json"
    context_path = output_dir / "run_context_v1.json"
    selection_path = output_dir / "idea_selection_v1.json"
    article = _read_json(manifest_path)
    context = _read_json(context_path)
    if not article and isinstance(context.get("article"), Mapping):
        article = dict(context["article"])
    selection = _read_json(selection_path)
    if not selection and isinstance(context.get("selection"), Mapping):
        selection = dict(context["selection"])
    body = article.get("substack_body_markdown")
    body_source: Optional[str] = None
    if isinstance(body, str) and body:
        body_source = str(manifest_path if manifest_path.is_file() else context_path)
    else:
        markdown_path = output_dir / "canonical_article.md"
        try:
            body = markdown_path.read_text(encoding="utf-8")
            body_source = str(markdown_path)
        except OSError:
            body = None
    if not isinstance(body, str) or not body:
        return {
            "content_status": CONTENT_UNAVAILABLE,
            "content_hash": None,
            "full_text": None,
            "body_source": None,
            "article": article,
            "selection": selection,
        }
    return {
        "content_status": CONTENT_AVAILABLE,
        "content_hash": _sha256_text(body),
        "full_text": body,
        "body_source": body_source,
        "article": article,
        "selection": selection,
    }


def load_published_corpus(
    store: Any,
    *,
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    """Load one record per lifecycle-confirmed canonical article.

    ``output_root`` is a compatibility fallback only. The preferred artifact location is the
    exact ``output_dir`` persisted in each canonical pre-write intent.
    """
    fallback_root = Path(output_root) if output_root else None
    with store.get_read_only_connection() as conn:
        rows = conn.execute(
            "SELECT d.*,m.work_item_id,m.destination,m.payload,m.created_at AS intent_created_at,"
            " w.story_id AS work_story_id,w.title AS work_title"
            " FROM platform_dispatches d"
            " JOIN outbox_messages m ON m.message_id=d.message_id"
            " JOIN work_items w ON w.work_item_id=m.work_item_id"
            " WHERE d.status=? ORDER BY d.dispatched_at,d.dispatch_id",
            (DISPATCH_CONFIRMED,),
        ).fetchall()
        reconciliations = {
            str(row["reconciliation_id"]): dict(row)
            for row in conn.execute("SELECT * FROM reconciliations").fetchall()
        }

    confirmed: list[dict[str, Any]] = []
    rejected_dispatch_count = 0
    for row in rows:
        reconciliation = reconciliations.get(
            _reconciliation_id_for_dispatch(str(row["dispatch_id"]))
        )
        if not reconciliation or str(reconciliation.get("status") or "") != RECONCILED_CONFIRMED:
            rejected_dispatch_count += 1
            continue
        parsed_intent = _intent(row["payload"])
        confirmed.append({**dict(row), "intent": parsed_intent})

    groups: dict[str, list[dict[str, Any]]] = {}
    for row in confirmed:
        intent = row["intent"]
        article_identity = str(intent.get("article_identity") or "")
        group_key = article_identity or str(row["work_item_id"])
        groups.setdefault(group_key, []).append(row)

    records: list[PublishedArticleRef] = []
    lifecycle_confirmed_derivative_count = 0
    canonical_groups_without_substack = 0
    for group_key, group in sorted(groups.items()):
        substack = next(
            (
                row for row in group
                if str(row.get("destination") or row.get("platform") or "").lower() == "substack"
            ),
            None,
        )
        if (
            substack is None
            or not str(substack.get("public_object_id") or "")
            or not _valid_canonical_substack_url(substack.get("public_object_url"))
        ):
            canonical_groups_without_substack += 1
            continue
        intent = dict(substack["intent"])
        output_value = str(intent.get("output_dir") or "")
        output_dir = Path(output_value) if output_value else None
        if (output_dir is None or not output_dir.is_dir()) and fallback_root is not None:
            candidate = fallback_root / str(substack["work_item_id"])
            output_dir = candidate if candidate.is_dir() else output_dir
        recovered = _artifact_article(output_dir)
        article = recovered["article"]
        selection = recovered["selection"]
        story_identity = str(
            intent.get("story_identity")
            or selection.get("cluster_id")
            or substack.get("work_story_id")
            or substack["work_item_id"]
        )
        # ``cluster_id`` is the existing canonical story/update-chain identity on this route.
        # The read model propagates it; it does not mint a parallel update ID.
        update_chain_identity = str(
            selection.get("update_chain_identity")
            or article.get("update_chain_identity")
            or intent.get("update_chain_identity")
            or selection.get("cluster_id")
            or article.get("cluster_id")
            or story_identity
        ) or None
        entities = tuple(
            str(value) for value in (
                selection.get("entities_topics")
                or article.get("entities_topics")
                or []
            ) if str(value).strip()
        )[:24]
        derivatives = tuple({
            "destination": str(row.get("destination") or row.get("platform") or ""),
            "dispatch_id": str(row.get("dispatch_id") or ""),
            "public_object_id": str(row.get("public_object_id") or "") or None,
            "public_object_url": str(row.get("public_object_url") or "") or None,
            "public_object_url_hash": str(row.get("public_object_url_hash") or "") or None,
            "dispatch_status": DISPATCH_CONFIRMED,
            "reconciliation_status": RECONCILED_CONFIRMED,
        } for row in sorted(group, key=lambda value: str(value.get("destination") or "")))
        lifecycle_confirmed_derivative_count += len(derivatives)
        records.append(PublishedArticleRef(
            story_identity=story_identity,
            title=str(article.get("title") or substack.get("work_title") or story_identity),
            published_at_utc=str(substack.get("dispatched_at") or ""),
            public_object_id=str(substack.get("public_object_id") or "") or None,
            canonical_url_hash=str(substack.get("public_object_url_hash") or "") or None,
            content_hash=recovered["content_hash"],
            entities=entities,
            update_chain_identity=update_chain_identity,
            article_mode=str(
                article.get("resolved_article_mode")
                or selection.get("resolved_article_mode")
                or intent.get("resolved_article_mode")
                or article.get("article_mode")
                or ""
            ) or None,
            article_identity=str(intent.get("article_identity") or group_key) or None,
            canonical_url=str(substack.get("public_object_url") or "") or None,
            full_text=recovered["full_text"],
            content_status=recovered["content_status"],
            body_source=recovered["body_source"],
            source_work_item_id=str(substack["work_item_id"]),
            derivative_public_objects=derivatives,
        ))

    records.sort(key=lambda value: (value.published_at_utc, value.story_identity))
    return {
        "schema_version": CORPUS_SCHEMA_VERSION,
        "articles": records,
        "article_count": len(records),
        "content_hash_coverage": sum(1 for record in records if record.content_hash),
        "full_text_article_count": sum(
            1 for record in records if record.content_status == CONTENT_AVAILABLE
        ),
        "content_unavailable_count": sum(
            1 for record in records if record.content_status == CONTENT_UNAVAILABLE
        ),
        "lifecycle_confirmed_derivative_count": lifecycle_confirmed_derivative_count,
        "rejected_unreconciled_dispatch_count": rejected_dispatch_count,
        "canonical_groups_without_substack_count": canonical_groups_without_substack,
        "dedupe_key": "article_identity_else_work_item_id",
        "canonical_publication_contract": (
            "SUBSTACK_DISPATCH_CONFIRMED_AND_EXACT_RECONCILIATION_CONFIRMED_AND_VALID_CANONICAL_URL"
        ),
        "derived_from_existing_durable_truth": True,
        "second_publication_store_created": False,
    }


def corpus_entity_index(corpus: Mapping[str, Any]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for article in corpus.get("articles") or []:
        for entity in article.entities:
            index.setdefault(str(entity), []).append(article.story_identity)
    return index
