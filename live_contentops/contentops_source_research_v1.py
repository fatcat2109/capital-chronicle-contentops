"""Retained evidence adapter for the existing acquisition, Simple and media owners.

Neither a hostname nor row-supplied permission flags establish reuse permission.
Only exact retained source/policy bytes and a bounded, authored-text proposition
can produce a permission record here. Unknown publisher rights remain a gap.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Mapping
from urllib.parse import urlsplit

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    _private,
    _time,
    sha256_of,
)
from live_contentops.official_primary_evidence_loader_v1 import (
    _html_canonical_visible_text,
)

SCHEMA = "contentops.retained_source_research.v1"
# These are authorship-specific policies, not an allowlist granting all .gov content rights.
POLICIES = {
    "www.federalreserve.gov": (
        "https://www.federalreserve.gov/disclaimer.htm",
        ("public domain", "copied and distributed without permission", "non-board"),
        ("/newsevents/pressreleases/monetary", "/releases/h10/"),
    ),
    "www.sec.gov": (
        "https://www.sec.gov/about/privacy-information",
        ("information presented on sec.gov", "copied or further distributed", "please do not use the sec seal"),
        ("/answers/reada10k.htm", "/newsroom/press-releases/"),
    ),
    "www.cftc.gov": (
        "https://www.cftc.gov/WebPolicy/index.htm",
        ("public domain", "freely distributed and copied", "written permission of the copyright owners"),
        ("/LearnAndProtect/AdvisoriesAndArticles/",),
    ),
    "www.bls.gov": (
        "https://www.bls.gov/bls/linksite.htm",
        (
            "everything that we publish",
            "public domain",
            "except for previously copyrighted photographs",
        ),
        ("/news.release/",),
    ),
    "www.eia.gov": (
        "https://www.eia.gov/about/copyrights_reuse.php",
        ("public domain", "you may use and/or distribute", "protected materials"),
        (
            "/todayinenergy/detail.php",
            "/naturalgas/weekly/",
            "/petroleum/supply/weekly/",
        ),
    ),
    "ir.eia.gov": (
        "https://www.eia.gov/about/copyrights_reuse.php",
        ("public domain", "you may use and/or distribute", "protected materials"),
        ("/secure/ngs/ngs.html", "/ngs/ngs.html", "/secure/wpsr/summary.txt", "/wpsr/summary.txt"),
    ),
}


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _rendered(raw: bytes, expected_url: str):
    from live_contentops.browser_rendered_source_recovery_v1 import (
        _canonical_rendered_text,
    )

    value = json.loads(raw)
    if (
        value.get("status") != "PASS"
        or value.get("final_url") != expected_url
        or value.get("retrieval_method") != "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE"
        or value.get("content_truncated") is not False
        or _hash(value["rendered_markdown"].encode()) != value["rendered_page_sha256"]
        or _canonical_rendered_text(value["rendered_markdown"])
        != value["canonical_content_text"]
        or _hash(value["canonical_content_text"].encode())
        != value["canonical_content_sha256"]
        or value.get("credential_or_session_material_read") is not False
        or value.get("public_write_performed") is not False
    ):
        raise ValueError("RENDERED_SOURCE_CAPTURE_INVALID")
    return value


class RetainedSourceResearch:
    """Read an explicitly configured evidence root; never follow arbitrary row paths."""

    def __init__(self, root: str | Path, *, editions_root: str | Path | None = None):
        self.root = Path(root).resolve()
        self.records: dict[str, dict[str, Any]] = {}
        self.gaps: list[dict[str, Any]] = []
        index_raw = self._read("index.json")
        index = json.loads(index_raw)
        if (
            index.get("schema_version") != SCHEMA
            or not isinstance(index.get("records"), list)
            or len(index["records"]) > 100
        ):
            raise ValueError("RESEARCH_INDEX_INVALID")
        self.revision = _hash(index_raw)
        for spec in index["records"]:
            try:
                record = self._verify(spec)
                if record["headline_id"] in self.records:
                    raise ValueError("RESEARCH_DUPLICATE_HEADLINE_ID")
                self.records[record["headline_id"]] = record
            except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
                self.gaps.append({"record_sha256": sha256_of(spec), "state": str(exc)})
        if editions_root:
            # A new edition is appended in its own evidence root. Existing captures,
            # propositions and their exact admission clocks are never overwritten.
            for location in editions_root if isinstance(editions_root, (list, tuple)) else [editions_root]:
                edition = RetainedSourceResearch(location)
                if set(edition.records) & set(self.records):
                    raise ValueError("SOURCE_EDITION_MUST_HAVE_NEW_IDENTITY")
                self.records.update(edition.records)
                self.gaps.extend(edition.gaps)
                self.revision = sha256_of([self.revision, edition.revision])

    def frozen_snapshot(self):
        value = {"root": str(self.root), "revision": self.revision,
                 "records": self.records, "gaps": self.gaps}
        return {**value, "snapshot_sha256": sha256_of(value)}

    @classmethod
    def from_frozen_snapshot(cls, value):
        """Restore only a previously verified, internal immutable opportunity input."""
        if value["snapshot_sha256"] != sha256_of({k: v for k, v in value.items() if k != "snapshot_sha256"}):
            raise ValueError("FROZEN_RESEARCH_SNAPSHOT_CHANGED")
        result = cls.__new__(cls)
        result.root = Path(value["root"])
        result.revision, result.records, result.gaps = value["revision"], value["records"], value["gaps"]
        return result

    def _read(self, relative: str) -> bytes:
        p = PurePosixPath(relative)
        if p.is_absolute() or ".." in p.parts or "\\" in relative or ":" in relative:
            raise ValueError("RESEARCH_PATH_OUTSIDE_CONFIGURED_ROOT")
        target = (self.root / relative).resolve()
        if not target.is_relative_to(self.root) or target.stat().st_size > 4_000_000:
            raise ValueError("RESEARCH_PATH_OR_SIZE_INVALID")
        return target.read_bytes()

    def _verify(self, spec: Mapping[str, Any]) -> dict[str, Any]:
        raw = self._read(spec["capture_path"])
        policy = self._read(spec["policy_capture_path"])
        loader = json.loads(self._read(spec["loader_result_path"]))
        doc = loader["official_source_documents"][0]
        if _private(spec) or loader["status"] != "PASS" or doc.get("content_truncated"):
            raise ValueError("RESEARCH_EVIDENCE_NOT_ADMITTED")
        if spec.get("authorship_class") == "ISSUER_FILING_FACTS_ONLY":
            return self._verify_issuer_facts(spec, raw, policy, loader, doc)
        url = urlsplit(doc["source_url"])
        rule = POLICIES.get(url.hostname)
        if (
            not rule
            or url.scheme != "https"
            or url.username
            or url.password
            or url.port not in (None, 443)
            or not any(url.path.startswith(p) for p in rule[2])
        ):
            raise ValueError("SOURCE_REUSE_POLICY_NOT_SUPPORTED")
        if (
            spec["policy_url"] != rule[0]
            or _hash(policy) != spec["policy_capture_sha256"]
        ):
            raise ValueError("SOURCE_PERMISSION_CAPTURE_MISMATCH")
        rendered_source = (
            spec.get("capture_class") == "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE"
        )
        if rendered_source:
            capture = _rendered(raw, doc["source_url"])
        if spec.get("policy_capture_class", spec.get("capture_class")) == "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE":
            policy_capture = _rendered(policy, rule[0])
            policy_text = _normalize(policy_capture["canonical_content_text"]).lower()
        else:
            policy_text = _normalize(
                _html_canonical_visible_text(policy.decode("utf-8", errors="replace"))
            ).lower()
        if not all(marker in policy_text for marker in rule[1]):
            raise ValueError("SOURCE_PERMISSION_TEXT_NOT_VERIFIED")
        observation = (spec.get("research_metadata") or {}).get("observation_date")
        relation = (spec.get("research_metadata") or {}).get("period_relation")
        if relation == "NEW_OBSERVATION_PERIOD" and not observation:
            raise ValueError("NEW_SOURCE_PERIOD_REQUIRES_OBSERVATION_DATE")
        capture_hash = (
            capture["rendered_page_sha256"] if rendered_source else _hash(raw)
        )
        if (
            capture_hash != doc["raw_sha256"]
            or capture_hash != spec["source_capture_sha256"]
        ):
            raise ValueError("SOURCE_CAPTURE_HASH_MISMATCH")
        authored_family = {"www.bls.gov": "official_macro", "www.eia.gov": "official_macro", "ir.eia.gov": "official_macro",
                           "www.federalreserve.gov": "official_policy", "www.sec.gov": "sec_regulatory",
                           "www.cftc.gov": "official_regulatory_fiscal"}
        if (
            doc["source_adapter_family"] != authored_family.get(url.hostname)
            or doc["source_authority_class"] != "official_public_primary_source"
        ):
            raise ValueError("SOURCE_AUTHORSHIP_NOT_SUPPORTED")
        canonical = (
            capture["canonical_content_text"]
            if rendered_source
            else _html_canonical_visible_text(raw.decode("utf-8", errors="replace"))[
                :100_000
            ]
        )
        if canonical != doc["canonical_content_text"]:
            raise ValueError("SOURCE_CANONICAL_TEXT_MISMATCH")
        # A text-only exact span; photographs, logos and third-party exhibits are excluded.
        start, end = spec["proposition_span"]
        if (
            type(start) is not int
            or type(end) is not int
            or not 0 <= start < end <= len(canonical)
            or end - start > 2000
        ):
            raise ValueError("SOURCE_PROPOSITION_SPAN_INVALID")
        proposition = _normalize(canonical[start:end])
        if proposition != _normalize(spec["headline_text"]) or not proposition:
            raise ValueError("SOURCE_PROPOSITION_NOT_EXACT")
        context_texts = []
        for context_start, context_end in spec.get("context_spans", [])[:4]:
            if (
                type(context_start) is not int
                or type(context_end) is not int
                or not 0 <= context_start < context_end <= len(canonical)
                or context_end - context_start > 3000
            ):
                raise ValueError("SOURCE_CONTEXT_SPAN_INVALID")
            context_texts.append(_normalize(canonical[context_start:context_end]))
        known = loader["provenance"]["retrieved_at_utc"]
        revision = spec.get("revision_at_utc") or known
        published = doc.get("published_at_utc")
        if (published is not None and _time(published) > _time(known)) or _time(known) > _time(revision):
            raise ValueError("RESEARCH_CLOCK_ORDER_INVALID")
        if _time(spec["policy_retrieved_at_utc"]) > _time(revision):
            raise ValueError("SOURCE_PERMISSION_NOT_KNOWN_AT_REVISION")
        permission = {
            "source_capture_sha256": capture_hash,
            "canonical_text_sha256": _hash(canonical.encode()),
            "content_sha256": _hash(proposition.encode()),
            "policy_url": rule[0],
            "policy_capture_sha256": _hash(policy),
            "policy_retrieved_at_utc": spec["policy_retrieved_at_utc"],
            "scope": "AGENCY_AUTHORED_TEXT_ONLY_EXCLUDES_LOGOS_PHOTOS_THIRD_PARTY",
            "permitted_context_text_hashes": [_hash(t.encode()) for t in context_texts],
            "INTERNAL_ANALYSIS_ALLOWED": True,
            "MODEL_INPUT_ALLOWED": True,
            "LLM_INPUT_ALLOWED": True,
            "provider_safe": True,
            "permitted_consumers": ["internal_research", "narrative_context"],
        }
        record = {
            "headline_id": spec["headline_id"],
            "headline_text": proposition,
            "text_sha256": permission["content_sha256"],
            "source_identity": doc["publisher"],
            "source_platform": "CONTENTOPS_ORIGINAL_OFFICIAL_ACQUISITION",
            "source_account": doc["publisher"],
            "source_timestamp_utc": doc["published_at_utc"],
            "official_source_urls": [doc["source_url"]],
            "source_url": doc["source_url"],
            "headline_timestamp": doc["published_at_utc"],
            "known_at_utc": known,
            "retrieval_time_utc": known,
            "revision_at_utc": revision,
            "revision_clock_basis": "CAPTURE_ADMISSION_TIME_PUBLISHER_REVISION_NOT_VERIFIED",
            "rights_state": "GOVERNED_GOVERNMENT_AUTHORED_TEXT_PUBLIC_DOMAIN",
            "rights_evidence_sha256": _hash(policy),
            "source_capture_sha256": capture_hash,
            "source_permission_record_sha256": sha256_of(permission),
            "source_permissions": permission,
            "candidate_catalyst_tags": list(spec.get("candidate_catalyst_tags", [])),
            "originality": "INDEPENDENT_CONTENTOPS_ACQUISITION",
            "correction_of": spec.get("correction_of"),
            "document": doc,
            "source_chart": spec.get("source_chart"),
            "permitted_source_text": "\n\n".join([proposition, *context_texts]),
            "supporting_headline_ids": list(spec.get("supporting_headline_ids", []))[
                :2
            ],
            "research_metadata": dict(spec.get("research_metadata") or {}),
        }
        return record

    def _verify_issuer_facts(self, spec, raw, policy, loader, doc):
        """Bounded filing facts, not a public-domain grant over issuer expression.

        SEC hosting does not make a company's filing SEC-authored. Keep the
        original exact excerpts for internal verification; public prose must be
        independently written and attributed to the issuer.
        """
        url = urlsplit(doc["source_url"])
        match = re.fullmatch(r"/Archives/edgar/data/([0-9]+)/([0-9]{18})/([A-Za-z0-9_-]+\.htm)", url.path)
        if (url.scheme != "https" or url.hostname != "www.sec.gov" or url.username
                or url.password or url.port not in (None, 443) or url.query or url.fragment or not match):
            raise ValueError("ISSUER_FILING_LOCATOR_INVALID")
        policy_url = "https://www.copyright.gov/help/faq/faq-protect.html"
        if spec["policy_url"] != policy_url or _hash(policy) != spec["policy_capture_sha256"]:
            raise ValueError("SOURCE_PERMISSION_CAPTURE_MISMATCH")
        rights = _rendered(policy, policy_url)
        policy_text = _normalize(rights["canonical_content_text"]).lower()
        if not all(t in policy_text for t in ("copyright does not protect facts", "may protect the way these things are expressed")):
            raise ValueError("SOURCE_PERMISSION_TEXT_NOT_VERIFIED")
        capture = json.loads(raw)
        excerpts = capture["excerpts"]
        if (capture.get("url") != doc["source_url"] or capture.get("source_identity") != doc["publisher"]
                or not re.fullmatch(r"[a-f0-9]{64}", capture.get("full_page_text_sha256", ""))
                or not 1 <= len(excerpts) <= 4 or sum(len(e["text"]) for e in excerpts) > 4000
                or any(type(e["start"]) is not int or type(e["end"]) is not int
                       or not 0 <= e["start"] < e["end"] <= capture["full_page_characters"]
                       or e["end"] - e["start"] != len(e["text"]) for e in excerpts)
                or doc["source_adapter_family"] != "issuer_filing"
                or doc["source_authority_class"] != "first_party_public_source"
                or doc.get("source_interest_role") != "ISSUER"
                or spec.get("source_chart") or spec.get("public_expression_reuse_allowed") is not False):
            raise ValueError("ISSUER_FILING_SCOPE_INVALID")
        index_url = doc["source_url"].rsplit("/", 1)[0] + "/" + match[2][:10] + "-" + match[2][10:12] + "-" + match[2][12:] + "-index.html"
        index_raw = self._read(spec["filing_index_capture_path"])
        if _hash(index_raw) != spec["filing_index_capture_sha256"]:
            raise ValueError("ISSUER_FILING_INDEX_HASH_MISMATCH")
        index = _rendered(index_raw, index_url)
        index_text = _normalize(index["canonical_content_text"])
        if (capture["form"] not in ("10-Q", "10-K")
                or re.sub(r"\W", "", doc["publisher"]).casefold() not in re.sub(r"\W", "", index_text).casefold()
                or match[1].zfill(10) not in index_text
                or capture["form"] not in index_text or match[3] not in index_text
                or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", spec["filing_date"])
                or spec["filing_date"] not in index_text or capture["period"] not in index_text
                or doc.get("published_at_precision") != "DATE_ONLY"
                or doc.get("published_at_source") != spec["filing_date"]
                or doc.get("published_at_utc") != spec["filing_date"] + "T00:00:00Z"):
            raise ValueError("ISSUER_FILING_IDENTITY_NOT_VERIFIED")
        canonical = "\n\n".join(e["text"] for e in excerpts)
        capture_hash = _hash(raw)
        if (capture_hash != spec["source_capture_sha256"] or capture_hash != doc["raw_sha256"]
                or doc["canonical_content_text"] != canonical):
            raise ValueError("SOURCE_CAPTURE_HASH_MISMATCH")
        start, end = spec["proposition_span"]
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(canonical) or end - start > 1000:
            raise ValueError("SOURCE_PROPOSITION_SPAN_INVALID")
        proposition = _normalize(canonical[start:end])
        if not proposition or proposition != _normalize(spec["headline_text"]):
            raise ValueError("SOURCE_PROPOSITION_NOT_EXACT")
        known, revision = loader["provenance"]["retrieved_at_utc"], spec["revision_at_utc"]
        if (known != capture["observed_at_utc"] or _time(known) > _time(revision)
                or _time(doc["published_at_utc"]) > _time(known)
                or _time(spec["policy_retrieved_at_utc"]) > _time(revision)
                or _time(index["retrieved_at_utc"]) > _time(revision)):
            raise ValueError("RESEARCH_CLOCK_ORDER_INVALID")
        permission = {
            "source_capture_sha256": capture_hash, "canonical_text_sha256": _hash(canonical.encode()),
            "content_sha256": _hash(proposition.encode()), "policy_url": policy_url,
            "policy_capture_sha256": _hash(policy), "policy_retrieved_at_utc": spec["policy_retrieved_at_utc"],
            "scope": "ATTRIBUTED_FILING_FACTS_ONLY_INDEPENDENT_PUBLIC_PARAPHRASE",
            "INTERNAL_ANALYSIS_ALLOWED": True, "MODEL_INPUT_ALLOWED": True, "LLM_INPUT_ALLOWED": True,
            "provider_safe": True, "permitted_consumers": ["internal_research", "narrative_context"],
            "public_expression_reuse_allowed": False, "images_logos_exhibits_reuse_allowed": False,
            "attribution_required": True, "government_authorship": False,
        }
        return {
            "headline_id": spec["headline_id"], "headline_text": proposition, "text_sha256": permission["content_sha256"],
            "source_identity": doc["publisher"], "source_account": doc["publisher"],
            "source_platform": "CONTENTOPS_ORIGINAL_PUBLIC_FILING_ACQUISITION",
            "source_timestamp_utc": doc["published_at_utc"], "headline_timestamp": doc["published_at_utc"],
            "source_url": doc["source_url"], "official_source_urls": [doc["source_url"]],
            "known_at_utc": known, "retrieval_time_utc": known, "revision_at_utc": revision,
            "revision_clock_basis": "CAPTURE_ADMISSION_TIME_PUBLISHER_REVISION_NOT_VERIFIED",
            "rights_state": "GOVERNED_PUBLIC_FILING_FACTS_ONLY_NO_EXPRESSIVE_REUSE",
            "rights_evidence_sha256": _hash(policy), "source_capture_sha256": capture_hash,
            "source_permission_record_sha256": sha256_of(permission), "source_permissions": permission,
            "candidate_catalyst_tags": list(spec.get("candidate_catalyst_tags", [])),
            "originality": "INDEPENDENT_CONTENTOPS_ACQUISITION", "correction_of": None,
            "document": {**doc, "source_reuse_constraints": permission}, "source_chart": None,
            "permitted_source_text": canonical, "supporting_headline_ids": list(spec.get("supporting_headline_ids", []))[:2],
            "research_metadata": dict(spec.get("research_metadata") or {}),
        }

    def permission_for(
        self, row: Mapping[str, Any], cutoff_utc: str
    ) -> dict[str, Any] | None:
        record = self.records.get(row.get("headline_id"))
        if not record:
            return None
        for key in (
            "source_identity",
            "source_url",
            "source_capture_sha256",
            "rights_evidence_sha256",
            "revision_at_utc",
            "rights_state",
            "source_platform",
            "correction_of",
        ):
            if row.get(key) != record.get(key):
                return None
        if _normalize(str(row.get("headline_text") or "")) != record["headline_text"]:
            return None
        return record["source_permissions"]

    def headlines(self, *, cutoff_utc: str) -> list[dict[str, Any]]:
        return [
            {
                k: v
                for k, v in row.items()
                if k not in {"document", "source_chart", "permitted_source_text"}
            }
            for row in self.records.values()
            if _time(row["revision_at_utc"]) <= _time(cutoff_utc)
        ]

    def evidence(
        self, request: Mapping[str, Any], *, cutoff_utc: str | None = None
    ) -> dict[str, Any] | None:
        found = [
            self.records[h]
            for h in request.get("headline_ids", [])
            if h in self.records
        ]
        if not found:
            return None
        support_ids = list(
            dict.fromkeys(h for r in found for h in r["supporting_headline_ids"])
        )
        # A follow-up retains both vintages from its already governed story brief.
        # These IDs still resolve through this adapter's verified exact records.
        for story in (request.get("story_context") or {}).get("evolving_story_context", []):
            support_ids.extend(h for h in story.get("source_item_ids", []) if h not in support_ids)
        support_ids.extend(h for h in request.get("retained_supporting_headline_ids", []) if h not in support_ids)
        supporting = [
            self.records[h]
            for h in support_ids
            if h in self.records and h not in request.get("headline_ids", [])
        ]
        if cutoff_utc:
            supporting = [
                r
                for r in supporting
                if _time(r["revision_at_utc"]) <= _time(cutoff_utc)
            ]
            found = [
                r for r in found if _time(r["revision_at_utc"]) <= _time(cutoff_utc)
            ]
        else:
            supporting = []
        if not found:
            return None
        # Existing official evidence shape, with zero additional network reads.
        docs = [
            {
                **r["document"],
                "document_id": r["document"].get("document_id") or r["headline_id"],
                "source_identity": r["source_identity"],
                "known_at_utc": r["known_at_utc"],
                "canonical_content_text": r["permitted_source_text"],
                "canonical_content_sha256": _hash(r["permitted_source_text"].encode()),
                "source_capture_sha256": r["source_capture_sha256"],
                "retrieval_method": (
                    "RETAINED_PUBLIC_FILING_FACTS_ONLY" if r["document"].get("source_adapter_family") == "issuer_filing"
                    else "RETAINED_OFFICIAL_PERMITTED_TEXT_SPANS"),
                "underlying_reuse_classification": (
                    "attributed_public_filing_facts_only" if r["document"].get("source_adapter_family") == "issuer_filing"
                    else "governed_government_public_domain"),
                "rights_evidence_sha256": r["rights_evidence_sha256"],
                # _verify proved the exact authorship/rights class and bounded
                # evidence. A filing remains attributed issuer facts only.
                "public_claim_allowed": True,
            }
            for r in found
        ]
        result = {
            "status": "PASS",
            "official_source_documents": docs,
            "provided_evidence_capabilities": ["official_document", "official_data"],
            "blockers": [],
            "publication_authority": False,
            "rolling_x_story_binding": {
                "cluster_id": request.get("cluster_id"),
                "headline_ids": request.get("headline_ids"),
                "request_logical_hash": request.get("request_logical_hash"),
            },
            "provenance": {
                "request_count_for_call": 0,
                "retained_research_revision": self.revision,
                "read_only_http_get_only": True,
            },
        }
        from live_contentops.v1_simple_evidence_resolver_v1 import (
            SimpleFirstPartyAwareEvidenceResolver,
        )

        accepted, state, blockers = (
            SimpleFirstPartyAwareEvidenceResolver._accepted_epistemic_route(
                request, result, route="OFFICIAL_PRIMARY"
            )
        )
        if accepted:
            # Explicitly retained editorial context joins the selected event only
            # after its own permission/capture verification. Its role is context;
            # it does not acquire authority over the selected event proposition.
            accepted.extend(
                {
                    **r["document"],
                    "document_id": r["document"].get("document_id") or r["headline_id"],
                    "source_identity": r["source_identity"],
                    "canonical_content_text": r["permitted_source_text"],
                    "canonical_content_sha256": _hash(
                        r["permitted_source_text"].encode()
                    ),
                    "known_at_utc": r["known_at_utc"],
                    "context_only": True,
                    "public_claim_allowed": True,
                    "rights_evidence_sha256": r["rights_evidence_sha256"],
                    "retrieval_method": "RETAINED_OFFICIAL_PERMITTED_CONTEXT_SPANS",
                }
                for r in supporting
            )
        return {
            **result,
            "status": "PASS" if accepted else "BLOCKED",
            "evidence_documents": accepted,
            "epistemic_state": state or {},
            "blockers": blockers,
            "provenance": {
                **result["provenance"],
                "selected_route": "OFFICIAL_PRIMARY",
            },
        }
