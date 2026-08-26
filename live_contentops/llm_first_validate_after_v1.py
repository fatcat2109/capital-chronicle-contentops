"""LLM-first, validate-after editorial adapter for the canonical V1 newsroom.

The adapter performs no publication. A HIGH coordinator selects one current governed
candidate, one fresh isolated HIGH worker researches and drafts it, and deterministic public
retrieval verifies cited bytes, publication-time provenance, and exact material-claim excerpts.
The verified evidence packet and article then re-enter the existing canonical qualification and
packaging path.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

from live_contentops.official_codex_provider_v1 import (
    EFFORT,
    MODEL,
    OfficialCodexEditorialSession,
)
from live_contentops.official_primary_evidence_loader_v1 import (
    OFFICIAL_HOSTS_BY_FAMILY,
    _html_timestamp,
    _parse_timestamp,
)
from live_contentops.public_secondary_evidence_loader_v1 import (
    REPUTABLE_SECONDARY_HOSTS,
    _default_public_http_get,
    _public_text,
    _title,
)
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    ARTICLE_TRANSPORT_SCHEMA,
    build_rolling_x_grounded_article_and_media,
)

SCHEMA_VERSION = "contentops.llm_first_validate_after.v1"
COORDINATOR_CHECKPOINT_SCHEMA_VERSION = "contentops.llm_first_coordinator_selection.v1"
MAX_CANDIDATE_ATTEMPTS = 3
MAX_SOURCES = 3
MAX_RESPONSE_BYTES = 800_000
ALLOWED_SOURCE_HOSTS = frozenset(REPUTABLE_SECONDARY_HOSTS).union(
    host for hosts in OFFICIAL_HOSTS_BY_FAMILY.values() for host in hosts
)
ARTICLE_MODES = (
    "BREAKING_BRIEF",
    "FOLLOW_UP_UPDATE",
    "STANDARD_NEWS_ANALYSIS",
    "CAPITAL_CHRONICLE_VIEW",
    "WHAT_THE_MARKET_IS_MISSING",
    "EVERGREEN_EXPLAINER",
    "DATA_OR_DOCUMENT_LENS",
    "WEEK_AHEAD_OR_WATCH",
)


def _hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
        ).encode("utf-8")
    ).hexdigest()


def _closed(properties: Mapping[str, Any], required: Sequence[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": dict(properties),
        "required": list(required),
        "additionalProperties": False,
    }


SELECTION_SCHEMA = _closed(
    {
        "selected_cluster_id": {"type": "string"},
        "article_mode": {"type": "string", "enum": list(ARTICLE_MODES)},
        "selection_rationale": {"type": "string"},
    },
    ("selected_cluster_id", "article_mode", "selection_rationale"),
)
SOURCE_SCHEMA = _closed(
    {
        "source_id": {"type": "string"},
        "url": {"type": "string"},
        "publisher": {"type": "string"},
        # Worker-declared publication time is only a diagnostic hint. Deterministic
        # source bytes/headers or exact URL-bound intake metadata own publication time.
        "published_at_utc": {"type": "string"},
    },
    ("source_id", "url", "publisher", "published_at_utc"),
)
CLAIM_SCHEMA = _closed(
    {
        "claim_id": {"type": "string"},
        "claim_text": {"type": "string"},
        "claim_kind": {
            "type": "string",
            "enum": ["FACT", "NUMBER", "QUOTE", "CAUSALITY"],
        },
        "source_id": {"type": "string"},
        "support_excerpt": {"type": "string"},
        "attribution_required": {"type": "boolean"},
    },
    (
        "claim_id",
        "claim_text",
        "claim_kind",
        "source_id",
        "support_excerpt",
        "attribution_required",
    ),
)
WORKER_SCHEMA = _closed(
    {
        "article": ARTICLE_TRANSPORT_SCHEMA,
        "cited_sources": {"type": "array", "items": SOURCE_SCHEMA},
        "material_claim_bindings": {"type": "array", "items": CLAIM_SCHEMA},
    },
    ("article", "cited_sources", "material_claim_bindings"),
)


def _normalized(value: Any) -> str:
    return " ".join(str(value or "").split()).casefold()


def _public_copy(article: Mapping[str, Any]) -> str:
    return "\n".join(
        str(article.get(key) or "")
        for key in (
            "title",
            "canonical_editorial_headline",
            "dek",
            "subtitle",
            "search_title",
            "seo_title",
            "meta_description",
            "social_hook",
            "social_lede",
            "substack_body_markdown",
        )
    )


def _host_allowed(url: str) -> bool:
    parsed = urlsplit(str(url or ""))
    host = str(parsed.hostname or "").casefold()
    return bool(
        parsed.scheme == "https"
        and host in ALLOWED_SOURCE_HOSTS
        and parsed.username is None
        and parsed.password is None
        and parsed.port in {None, 443}
    )


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class LlmFirstValidationError(ValueError):
    def __init__(self, blockers: Sequence[str]) -> None:
        self.blockers = sorted({str(value) for value in blockers if str(value)})
        super().__init__(";".join(self.blockers))


class LlmFirstValidateAfterProvider:
    """One bounded coordinator/worker adapter consumed by the canonical newsroom cycle."""

    def __init__(
        self, *, output_dir: Path, published_memory: Sequence[Any] | None = None
    ) -> None:
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._prepared: dict[str, Any] | None = None
        self._selected_cluster_id: str | None = None
        self._published_memory = list(published_memory or [])
        self._coordinator_checkpoint_reused = False

    @staticmethod
    def _candidate_packet(
        clusters: Sequence[Mapping[str, Any]], intake: Mapping[str, Any]
    ) -> list[dict[str, Any]]:
        headlines = {
            str(row.get("headline_id") or ""): dict(row)
            for row in intake.get("headlines") or []
            if isinstance(row, Mapping) and str(row.get("headline_id") or "")
        }
        packet: list[dict[str, Any]] = []
        for row in clusters[:8]:
            ids = [str(value) for value in row.get("headline_ids") or [] if str(value)]

            def headline_value(headline_id: str, key: str) -> Any:
                headline = headlines.get(headline_id, {})
                external = (
                    headline.get("external_content")
                    if isinstance(headline.get("external_content"), Mapping)
                    else {}
                )
                aliases = {
                    "headline_text": "headline_text",
                    "source_account": "author_handle",
                    "source_url": "url_or_source_ref",
                }
                return headline.get(key) or external.get(aliases.get(key, key))

            packet.append(
                {
                    "cluster_id": str(row.get("cluster_id") or ""),
                    "rank": int(row.get("rank") or 0),
                    "headline_ids": ids,
                    "headlines": [
                        {
                            "headline_id": value,
                            "headline_text": headline_value(value, "headline_text"),
                            "source_timestamp_utc": headlines.get(value, {}).get(
                                "source_timestamp_utc"
                            ),
                            "source_account": headline_value(value, "source_account"),
                            "source_url": headline_value(value, "source_url"),
                        }
                        for value in ids
                    ],
                    "why_now": row.get("why_now"),
                    "selection_case": row.get("selection_case"),
                    "entities_topics": list(row.get("entities_topics") or []),
                    "resolved_article_mode": row.get("resolved_article_mode"),
                }
            )
        return packet

    @staticmethod
    def _selection_governed_input(
        *,
        candidates: Sequence[Mapping[str, Any]],
        cutoff_utc: str,
        published_corpus: Sequence[Any],
        excluded_cluster_ids: Sequence[str],
    ) -> dict[str, Any]:
        return {
            "cutoff_utc": cutoff_utc,
            "candidates": list(candidates),
            "excluded_cluster_ids": list(excluded_cluster_ids),
            "published_memory": [
                {
                    "title": row.get("title"),
                    "story_identity": row.get("story_identity"),
                    "update_chain_identity": row.get("update_chain_identity"),
                }
                for row in published_corpus
                if isinstance(row, Mapping)
            ][-100:],
        }

    def _load_coordinator_checkpoint(
        self,
        *,
        governed_input_hash: str,
        candidates: Sequence[Mapping[str, Any]],
        excluded_cluster_ids: Sequence[str],
    ) -> tuple[dict[str, Any], dict[str, Any]] | None:
        path = self.output_dir / "llm_first_coordinator_selection_v1.json"
        if not path.exists():
            return None
        try:
            checkpoint = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError):
            return None
        if not isinstance(checkpoint, Mapping):
            return None
        receipt = checkpoint.get("coordinator_receipt")
        selection = checkpoint.get("selection")
        if not isinstance(receipt, Mapping) or not isinstance(selection, Mapping):
            return None
        receipt_identity = receipt.get("provider_input_identity")
        receipt_identity = receipt_identity if isinstance(receipt_identity, Mapping) else {}
        bound_hash = str(
            checkpoint.get("governed_input_hash")
            or receipt_identity.get("governed_input_hash")
            or ""
        )
        selected_id = str(selection.get("selected_cluster_id") or "")
        candidate_ids = {
            str(row.get("cluster_id") or "")
            for row in candidates
            if isinstance(row, Mapping)
        }
        if (
            checkpoint.get("schema_version") != COORDINATOR_CHECKPOINT_SCHEMA_VERSION
            or checkpoint.get("public_write_performed") is not False
            or str(checkpoint.get("maximum_reasoning_effort") or "").upper() != "HIGH"
            or bound_hash != governed_input_hash
            or str(receipt.get("model") or "") != MODEL
            or str(receipt.get("reasoning_effort") or "").upper() != "HIGH"
            or str(receipt_identity.get("role") or "") != "V1_LLM_FIRST_COORDINATOR_SELECTION"
            or selected_id not in candidate_ids
            or selected_id in set(str(value) for value in excluded_cluster_ids)
            or str(selection.get("article_mode") or "") not in ARTICLE_MODES
        ):
            return None
        self._coordinator_checkpoint_reused = True
        return dict(selection), dict(receipt)

    def _select(
        self,
        *,
        candidates: Sequence[Mapping[str, Any]],
        cutoff_utc: str,
        published_corpus: Sequence[Any],
        excluded_cluster_ids: Sequence[str],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        governed = self._selection_governed_input(
            candidates=candidates,
            cutoff_utc=cutoff_utc,
            published_corpus=published_corpus,
            excluded_cluster_ids=excluded_cluster_ids,
        )
        governed_hash = _hash(governed)
        reusable = self._load_coordinator_checkpoint(
            governed_input_hash=governed_hash,
            candidates=candidates,
            excluded_cluster_ids=excluded_cluster_ids,
        )
        if reusable is not None:
            return reusable
        self._coordinator_checkpoint_reused = False
        prompt = (
            "Select exactly one useful current Capital Chronicle story/angle from GOVERNED_INPUT. "
            "Avoid published duplicates and excluded clusters. Quiet news may use a lower-rung mode, "
            "but do not select filler. The selection grants no factual, numeric, publication, or public-write authority.\n"
            "GOVERNED_INPUT:\n" + json.dumps(governed, sort_keys=True, ensure_ascii=False)
        )
        with OfficialCodexEditorialSession(
            proof_cwd=self.output_dir / f"coordinator_{len(excluded_cluster_ids) + 1}_cwd",
            output_schema=SELECTION_SCHEMA,
        ) as session:
            execution = session.run(
                prompt=prompt,
                developer_instructions=(
                    "You are the Capital Chronicle V1 editorial coordinator on gpt-5.6-sol / HIGH. "
                    "Select one useful current story. Use no tools and return only the requested object."
                ),
                governed_input_hash=governed_hash,
                evidence_hash=_hash(governed.get("published_memory") or []),
                role="V1_LLM_FIRST_COORDINATOR_SELECTION",
            )
        selection = dict(execution.output)
        receipt = dict(execution.receipt)
        checkpoint = {
            "schema_version": COORDINATOR_CHECKPOINT_SCHEMA_VERSION,
            "governed_input_hash": governed_hash,
            "selection": selection,
            "coordinator_receipt": receipt,
            "maximum_reasoning_effort": "HIGH",
            "public_write_performed": False,
        }
        (self.output_dir / "llm_first_coordinator_selection_v1.json").write_text(
            json.dumps(checkpoint, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return selection, receipt

    @staticmethod
    def _exact_bound_candidate_timestamp(
        candidate: Mapping[str, Any], requested_url: str
    ) -> str | None:
        for headline in candidate.get("headlines") or []:
            if not isinstance(headline, Mapping):
                continue
            if str(headline.get("source_url") or "").strip() != requested_url:
                continue
            parsed = _parse_timestamp(headline.get("source_timestamp_utc"))
            if parsed:
                return parsed
        return None

    def _worker(
        self,
        *,
        candidate: Mapping[str, Any],
        selection: Mapping[str, Any],
        cutoff_utc: str,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        governed = {
            "cutoff_utc": cutoff_utc,
            "selected_candidate": dict(candidate),
            "selected_article_mode": selection.get("article_mode"),
            "selection_rationale": selection.get("selection_rationale"),
            "allowed_source_hosts": sorted(ALLOWED_SOURCE_HOSTS),
            "source_marker_contract": (
                "cited_sources order is SOURCE_1..SOURCE_N; use exact [[SOURCE:SOURCE_N]] markers"
            ),
        }
        governed_hash = _hash(governed)
        prompt = (
            "Research and write one useful current Capital Chronicle article from GOVERNED_INPUT. Use read-only web research. "
            "Cite one to three exact HTTPS pages only from allowed_source_hosts. Return every source in cited_sources in marker order. "
            "For every material fact, number, quotation, or causal assertion in public copy, return one material_claim_binding whose "
            "claim_text appears verbatim in the public copy and whose support_excerpt is a short exact excerpt from the cited page. "
            "The source published_at_utc field is only a locator hint and never authority; deterministic validation owns publication time. "
            "Use [[SOURCE:SOURCE_N]] in the body. No unsupported facts, numbers, quotes, market reaction, forecasts, probabilities, "
            "scenarios, regimes, valuations, misconduct, or Core Analyzer claims. Zero media is valid.\nGOVERNED_INPUT:\n"
            + json.dumps(governed, sort_keys=True, ensure_ascii=False)
        )
        receipts: list[dict[str, Any]] = []
        with OfficialCodexEditorialSession(
            proof_cwd=self.output_dir / f"worker_{candidate.get('cluster_id')}_cwd",
            output_schema=WORKER_SCHEMA,
            allow_web_items=True,
        ) as session:
            execution = session.run(
                prompt=prompt,
                developer_instructions=(
                    "You are one fresh isolated Capital Chronicle editorial worker on gpt-5.6-sol / HIGH. "
                    "Research with read-only web access and return only the strict object. You have no factual, numeric, "
                    "Capital Chronicle analytical, permission, publication, or public-write authority."
                ),
                governed_input_hash=governed_hash,
                evidence_hash=_hash(candidate),
                role="V1_LLM_FIRST_EDITORIAL_WRITER",
            )
            receipts.append(dict(execution.receipt))
            output = dict(execution.output)
            try:
                verified = self._verify(output, candidate=candidate, cutoff_utc=cutoff_utc)
            except LlmFirstValidationError as exc:
                revision_prompt = (
                    "Revise the prior article in this same thread using only these deterministic validation deltas: "
                    + json.dumps(exc.blockers)
                    + ". Remove or narrow unsupported material, replace unverifiable citations with exact allowed public pages, "
                    "and return the complete strict object. Do not expand factual scope."
                )
                revised = session.run(
                    prompt=revision_prompt,
                    developer_instructions=(
                        "You are the same isolated Capital Chronicle HIGH worker performing the sole bounded validate-after revision. "
                        "Return only the strict object and never attempt a public write."
                    ),
                    governed_input_hash=governed_hash,
                    evidence_hash=_hash(candidate),
                    role="V1_LLM_FIRST_EDITORIAL_REVISION",
                    revision=True,
                )
                receipts.append(dict(revised.receipt))
                output = dict(revised.output)
                verified = self._verify(output, candidate=candidate, cutoff_utc=cutoff_utc)
        verified["governed_input_hash"] = governed_hash
        return verified, receipts

    def _verify(
        self,
        output: Mapping[str, Any],
        *,
        candidate: Mapping[str, Any],
        cutoff_utc: str,
    ) -> dict[str, Any]:
        article = dict(output.get("article") or {})
        sources = [
            dict(row)
            for row in output.get("cited_sources") or []
            if isinstance(row, Mapping)
        ]
        claims = [
            dict(row)
            for row in output.get("material_claim_bindings") or []
            if isinstance(row, Mapping)
        ]
        blockers: list[str] = []
        if not 1 <= len(sources) <= MAX_SOURCES:
            blockers.append("cited_source_count_invalid")
        if not claims:
            blockers.append("material_claim_bindings_missing")
        public_copy = _normalized(_public_copy(article))
        documents: list[dict[str, Any]] = []
        source_by_id: dict[str, dict[str, Any]] = {}
        cutoff = datetime.fromisoformat(str(cutoff_utc).replace("Z", "+00:00"))
        if cutoff.tzinfo is None:
            raise LlmFirstValidationError(["cutoff_timezone_required"])

        for index, source in enumerate(sources, start=1):
            source_id = str(source.get("source_id") or "")
            url = str(source.get("url") or "")
            if source_id != f"SOURCE_{index}":
                blockers.append(f"source_marker_order_invalid:{source_id}")
                continue
            if not _host_allowed(url):
                blockers.append(f"source_host_not_allowed:{source_id}")
                continue
            try:
                response = _default_public_http_get(url, 15.0, MAX_RESPONSE_BYTES)
                body = response.get("body")
                final_url = str(response.get("final_url") or url)
                if (
                    int(response.get("status") or 0) != 200
                    or not isinstance(body, bytes)
                    or not body
                    or not _host_allowed(final_url)
                ):
                    raise ValueError("source_retrieval_invalid")
                headers = {
                    str(key).casefold(): str(value)
                    for key, value in dict(response.get("headers") or {}).items()
                }
                content_type = headers.get("content-type", "").split(";", 1)[0].casefold()
                raw = body.decode("utf-8", errors="replace")
                text = _public_text(body, content_type)
                if len(text) < 80:
                    raise ValueError("source_text_insufficient")

                publisher_timestamp = _html_timestamp(raw) or _parse_timestamp(
                    headers.get("last-modified")
                )
                bound_intake_timestamp = self._exact_bound_candidate_timestamp(candidate, url)
                published_at_utc = publisher_timestamp or bound_intake_timestamp
                if not published_at_utc:
                    blockers.append(
                        f"deterministic_published_timestamp_unavailable:{source_id}"
                    )
                    continue
                published = datetime.fromisoformat(
                    str(published_at_utc).replace("Z", "+00:00")
                )
                if published.tzinfo is None or published > cutoff:
                    blockers.append(
                        f"deterministic_published_timestamp_invalid:{source_id}"
                    )
                    continue
                timestamp_source = (
                    "PUBLISHER_BYTES_OR_HEADERS"
                    if publisher_timestamp
                    else "EXACT_BOUND_HEADLINE_TIMESTAMP"
                )
            except (OSError, RuntimeError, TypeError, ValueError):
                blockers.append(f"deterministic_source_retrieval_failed:{source_id}")
                continue

            document = {
                "document_id": "llm-first-" + hashlib.sha256(body).hexdigest()[:20],
                "title": _title(raw) or source.get("publisher"),
                "publisher": str(source.get("publisher") or urlsplit(final_url).hostname or ""),
                "source_identity": str(urlsplit(final_url).hostname or "").casefold(),
                "source_authority_class": (
                    "official_primary_source"
                    if str(urlsplit(final_url).hostname or "").casefold()
                    not in REPUTABLE_SECONDARY_HOSTS
                    else "reputable_secondary_source"
                ),
                "source_url": final_url,
                "reader_source_url": final_url,
                "requested_source_url": url,
                "published_at_utc": _iso_utc(published),
                "published_at_source": timestamp_source,
                "freshness_timestamp_source": timestamp_source,
                "model_declared_published_at_utc": str(
                    source.get("published_at_utc") or ""
                ),
                "event_time_utc": _iso_utc(published),
                "known_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "raw_sha256": hashlib.sha256(body).hexdigest(),
                "canonical_content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "canonical_content_text": text,
                "content_type": content_type,
                "byte_length": len(body),
                "content_truncated": bool(response.get("content_truncated")),
                "public_claim_allowed": True,
                "permission_state": "PUBLIC_CLAIM_ALLOWED",
                "retrieval_method": "READ_ONLY_PUBLIC_HTTP_GET_AFTER_GENERATION",
                "source_handle": source_id,
                "cluster_id": str(candidate.get("cluster_id") or ""),
                "headline_ids": list(candidate.get("headline_ids") or []),
            }
            documents.append(document)
            source_by_id[source_id] = document

        supported_claims: list[dict[str, Any]] = []
        for claim in claims:
            claim_id = str(claim.get("claim_id") or "")
            claim_text = _normalized(claim.get("claim_text"))
            source_id = str(claim.get("source_id") or "")
            excerpt = _normalized(claim.get("support_excerpt"))
            document = source_by_id.get(source_id)
            if not claim_id or len(claim_text) < 8 or claim_text not in public_copy:
                blockers.append(f"material_claim_not_in_public_copy:{claim_id or 'UNKNOWN'}")
                continue
            if document is None or len(excerpt) < 8 or excerpt not in _normalized(
                document.get("canonical_content_text")
            ):
                blockers.append(
                    f"material_claim_excerpt_not_verified:{claim_id or 'UNKNOWN'}"
                )
                continue
            supported_claims.append(
                {
                    "claim_id": claim_id,
                    "claim_text": str(claim.get("claim_text") or ""),
                    "support_status": "SUPPORTED_EXACT_POST_GENERATION_SOURCE_BYTES",
                    "evidence_document_ids": [document["document_id"]],
                    "source_refs": [source_id],
                    "attribution_required": bool(claim.get("attribution_required")),
                    "direct_or_inferred": "DIRECT",
                    "claim_kind": str(claim.get("claim_kind") or "FACT"),
                    "support_excerpt_sha256": hashlib.sha256(
                        str(claim.get("support_excerpt") or "").encode("utf-8")
                    ).hexdigest(),
                }
            )
        if blockers:
            raise LlmFirstValidationError(blockers)
        if not documents or len(supported_claims) != len(claims):
            raise LlmFirstValidationError(["post_generation_claim_binding_incomplete"])
        return {
            "article": article,
            "documents": documents,
            "supported_claims": supported_claims,
            "cited_sources": sources,
            "material_claim_bindings": claims,
            "verification": {
                "status": "PASS",
                "ordering": "LLM_FIRST_VALIDATE_AFTER",
                "deterministic_source_request_count": len(documents),
                "source_timestamp_authority": (
                    "PUBLISHER_BYTES_OR_HEADERS_OR_EXACT_BOUND_HEADLINE_TIMESTAMP"
                ),
                "model_declared_source_timestamp_grants_authority": False,
                "unsupported_claims_removed_or_narrowed": [],
            },
        }

    def prepare(
        self,
        *,
        ranked_clusters: Sequence[Mapping[str, Any]],
        intake: Mapping[str, Any],
        cutoff_utc: str,
        published_corpus: Sequence[Any],
    ) -> dict[str, Any]:
        candidates = self._candidate_packet(ranked_clusters, intake)
        excluded: list[str] = []
        attempts: list[dict[str, Any]] = []
        for _attempt in range(min(MAX_CANDIDATE_ATTEMPTS, len(candidates))):
            selection, coordinator_receipt = self._select(
                candidates=candidates,
                cutoff_utc=cutoff_utc,
                published_corpus=[*self._published_memory, *published_corpus],
                excluded_cluster_ids=excluded,
            )
            coordinator_reused = self._coordinator_checkpoint_reused
            selected_id = str(selection.get("selected_cluster_id") or "")
            candidate = next(
                (row for row in candidates if row.get("cluster_id") == selected_id), None
            )
            if candidate is None or selected_id in excluded:
                raise LlmFirstValidationError(["coordinator_selected_invalid_candidate"])
            try:
                verified, worker_receipts = self._worker(
                    candidate=candidate,
                    selection=selection,
                    cutoff_utc=cutoff_utc,
                )
            except LlmFirstValidationError as exc:
                attempts.append(
                    {
                        "cluster_id": selected_id,
                        "status": "POST_GENERATION_VALIDATION_BLOCKED",
                        "blockers": exc.blockers,
                        "coordinator_checkpoint_reused": coordinator_reused,
                        "coordinator_receipt": coordinator_receipt,
                    }
                )
                excluded.append(selected_id)
                continue
            attempts.append(
                {
                    "cluster_id": selected_id,
                    "status": "PASS",
                    "coordinator_checkpoint_reused": coordinator_reused,
                    "coordinator_receipt": coordinator_receipt,
                    "worker_receipts": worker_receipts,
                }
            )
            self._selected_cluster_id = selected_id
            self._prepared = {
                **verified,
                "selection": selection,
                "coordinator_receipt": coordinator_receipt,
                "coordinator_checkpoint_reused": coordinator_reused,
                "worker_receipts": worker_receipts,
                "candidate_attempts": attempts,
            }
            self._persist_receipt()
            return self.summary()
        raise LlmFirstValidationError(["bounded_llm_first_candidate_attempts_exhausted"])

    def _persist_receipt(self) -> None:
        assert self._prepared is not None
        path = self.output_dir / "llm_first_validate_after_receipt_v1.json"
        path.write_text(
            json.dumps(self._prepared, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _compact_model_call(row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "role": (row.get("provider_input_identity") or {}).get("role"),
            "model": row.get("model"),
            "reasoning_effort": row.get("reasoning_effort"),
            "usage": dict(row.get("turn_result_usage") or {}),
            "duration_ms": row.get("turn_result_duration_ms"),
        }

    def summary(self) -> dict[str, Any]:
        if self._prepared is None:
            raise ValueError("llm_first_provider_not_prepared")
        coordinator_receipt = self._prepared["coordinator_receipt"]
        worker_receipts = list(self._prepared["worker_receipts"])
        all_receipts = [coordinator_receipt, *worker_receipts]
        executed_receipts = list(worker_receipts)
        if not self._prepared.get("coordinator_checkpoint_reused"):
            executed_receipts.insert(0, coordinator_receipt)
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "PASS",
            "ordering": "LLM_FIRST_VALIDATE_AFTER",
            "selected_cluster_id": self._selected_cluster_id,
            "selection": dict(self._prepared["selection"]),
            "coordinator_checkpoint_reused": bool(
                self._prepared.get("coordinator_checkpoint_reused")
            ),
            "candidate_attempts": list(self._prepared["candidate_attempts"]),
            "model_calls": [self._compact_model_call(row) for row in all_receipts],
            "model_calls_executed_this_prepare": [
                self._compact_model_call(row) for row in executed_receipts
            ],
            "maximum_reasoning_effort": "HIGH",
            "above_high_call_count": sum(
                str(row.get("reasoning_effort") or "").upper() not in {"", "HIGH"}
                for row in all_receipts
            ),
            "network_requests": int(
                self._prepared["verification"]["deterministic_source_request_count"]
            ),
            "post_generation_verification": dict(self._prepared["verification"]),
            "public_write_performed": False,
            "provider_publication_writes": 0,
            "unknown_write_detected": False,
        }

    def evidence_acquirer(self, request: Mapping[str, Any]) -> dict[str, Any]:
        if self._prepared is None or str(request.get("cluster_id") or "") != str(
            self._selected_cluster_id or ""
        ):
            return {
                "status": "BLOCKED",
                "blockers": ["LLM_FIRST_CANDIDATE_NOT_SELECTED"],
                "publication_authority": False,
            }
        documents = [
            {
                **dict(row),
                "request_logical_hash": request.get("request_logical_hash"),
            }
            for row in self._prepared["documents"]
        ]
        supported = [dict(row) for row in self._prepared["supported_claims"]]
        claim_contract = {
            "schema_version": "contentops.claim_evidence_contract.v1",
            "supported_claims": supported,
            "omitted_unsupported_claims": [],
            "omitted_claim_count": 0,
        }
        claim_contract["claim_contract_sha256"] = _hash(claim_contract)
        primary = supported[0]
        return {
            "schema_version": "contentops.rolling_x_targeted_evidence_receipt.v1",
            "status": "PASS",
            "blockers": [],
            "rolling_x_story_binding": {
                "cluster_id": request.get("cluster_id"),
                "headline_ids": list(request.get("headline_ids") or []),
                "request_logical_hash": request.get("request_logical_hash"),
            },
            "evidence_documents": documents,
            "provided_evidence_capabilities": [
                "credible_event_confirmation",
                "basic_attributed_facts",
            ],
            "minimum_trustworthy_evidence_packet": {
                "status": "PASS",
                "risk_tier": "ORDINARY",
                "core_factual_proposition": primary["claim_text"],
                "evidence_document_id": primary["evidence_document_ids"][0],
                "attribution_required": bool(primary["attribution_required"]),
            },
            "grounded_research_packet": {
                "schema_version": "contentops.llm_first_grounded_research.v1",
                "research_as_of_utc": datetime.now(timezone.utc).isoformat().replace(
                    "+00:00", "Z"
                ),
                "research_model_identity": MODEL,
                "grounding_mode": "LLM_FIRST_VALIDATE_AFTER_EXACT_SOURCE_BYTES",
                "core_factual_proposition": primary["claim_text"],
                "confirmed_facts": [
                    {
                        "fact_id": row["claim_id"],
                        "factual_statement": row["claim_text"],
                        "source_refs": list(row["source_refs"]),
                        "attribution_required": row["attribution_required"],
                        "direct_or_inferred": "DIRECT",
                    }
                    for row in supported
                ],
                "sources": [
                    {
                        "source_ref": str(row.get("source_handle") or ""),
                        "evidence_document_id": row["document_id"],
                    }
                    for row in documents
                ],
                "research_status": "PASS",
            },
            "claim_evidence_contract": claim_contract,
            "evidence_substance": {
                "enough_for_useful_article": True,
                "usable_content_words": sum(
                    len(str(row.get("canonical_content_text") or "").split())
                    for row in documents
                ),
            },
            "evidence_review_tier": "POST_GENERATION_DETERMINISTIC_SOURCE_BYTES",
            "capital_chronicle_authority_verified": False,
            "publication_authority": False,
            "llm_first_validate_after": self.summary(),
        }

    def article_builder(self, viability: Mapping[str, Any]) -> dict[str, Any]:
        if self._prepared is None:
            raise ValueError("llm_first_provider_not_prepared")
        built = build_rolling_x_grounded_article_and_media(
            viability,
            output_dir=self.output_dir,
            article_generator=lambda _prompt: dict(self._prepared["article"]),
        )
        built["critical_path_telemetry"] = {
            **dict(built.get("critical_path_telemetry") or {}),
            "article_writer_semantic_calls": len(self._prepared["worker_receipts"]),
            "article_writer_owner": "FRESH_ISOLATED_CODEX_HIGH_LLM_FIRST",
            "llm_first_validate_after": True,
        }
        request = dict(viability.get("editorial_worker_request") or {})
        governed_hash = str(request.get("governed_input_hash") or "")
        article = dict(built.get("article") or {})
        built["editorial_worker_receipt"] = {
            "schema_version": "contentops.llm_first_editorial_worker_return.v1",
            "governed_input_hash": governed_hash,
            "model": MODEL,
            "reasoning_effort": EFFORT.upper(),
            "fresh": True,
            "isolated": True,
            "resume_existing": False,
            "bounded_revision_count": max(0, len(self._prepared["worker_receipts"]) - 1),
            "article": article,
            "llm_first_validate_after": self.summary(),
            "public_write_attempted": False,
            "publication_authority": False,
        }
        built["editorial_worker_validation"] = {
            "schema_version": "contentops.desktop_editorial_worker_return_validation.v1",
            "classification": "PASS_BOUND_HIGH_EDITORIAL_RETURN",
            "governed_input_hash": governed_hash,
            "worker_model": MODEL,
            "worker_reasoning_effort": EFFORT.upper(),
            "worker_fresh_and_isolated": True,
            "bounded_revision_count": max(0, len(self._prepared["worker_receipts"]) - 1),
            "coordinator_resumes": True,
            "deterministic_validation_required": True,
            "llm_first_validate_after": True,
            "publication_coordinator_remains_sole_public_writer": True,
            "public_write_performed": False,
        }
        return built
