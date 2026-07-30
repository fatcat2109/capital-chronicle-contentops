"""Verifier-owned evidence receipts for governed candidate authority.

The objects in this module are intentionally produced from exact bytes and
read-only database records.  A caller-supplied mapping, including one carrying
the legacy ``exact_verified`` boolean, is never a trusted evidence index.
"""
from __future__ import annotations

from hashlib import sha1, sha256
import importlib
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
from types import MappingProxyType
from typing import Any, Iterator, Mapping, Sequence

from live_contentops.governed_upstream_bridge_v1 import (
    GovernedArtifactBlocked,
    GovernedUpstreamBridgeV1,
    read_git_artifact,
)


GIT_RECEIPT_SCHEMA = "contentops.verified_git_evidence_receipt.v1"
NONNUMERIC_STORY_RECEIPT_SCHEMA = (
    "contentops.verified_nonnumeric_story_authority_receipt.v1"
)
DBH2_RECEIPT_SCHEMA = "contentops.verified_dbh2_record_receipt.v1"
AGGREGATION_RECEIPT_SCHEMA = "contentops.verified_aggregation_receipt.v1"
IMPLEMENTATION_RECEIPT_SCHEMA = "contentops.verified_implementation_receipt.v1"
VERIFIED_BINDING_SCHEMA = "contentops.verifier_produced_claim_evidence_binding.v2"
VERIFIED_INDEX_SCHEMA = "contentops.verifier_produced_evidence_index.v1"

_INDEX_TOKEN = object()


class EvidenceReceiptVerificationError(ValueError):
    """Fail-closed exact-byte, database, aggregation, or callable mismatch."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _logical_hash(value: Any) -> str:
    return sha256(_canonical_json(value)).hexdigest()


def _without_hash(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "logical_hash"}


def _git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(root), *args],
        stderr=subprocess.DEVNULL,
    )


def _is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, descendant],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def _parse_utc(value: str) -> datetime:
    text = value.strip()
    if "T" not in text and " " not in text:
        text = f"{text}T00:00:00Z"
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _verify_origin(root: Path, expected_repository: str) -> None:
    try:
        origin = _git(root, "config", "--get", "remote.origin.url").decode().strip()
    except subprocess.CalledProcessError as error:
        raise EvidenceReceiptVerificationError(
            "verified_repository_origin_missing"
        ) from error
    normalized = origin.removesuffix(".git").replace("\\", "/").casefold()
    if not normalized.endswith(expected_repository.casefold()):
        raise EvidenceReceiptVerificationError(
            "verified_repository_origin_mismatch"
        )


class VerifiedEvidenceIndexV1(dict[str, Mapping[str, Any]]):
    """JSON-compatible mapping whose entries can only be inserted by a verifier."""

    schema_version = VERIFIED_INDEX_SCHEMA

    def __init__(self, token: object) -> None:
        if token is not _INDEX_TOKEN:
            raise EvidenceReceiptVerificationError(
                "verified_evidence_index_constructor_forbidden"
            )
        super().__init__()
        self._verifier_owned = True

    def __setitem__(self, key: str, value: Mapping[str, Any]) -> None:
        raise EvidenceReceiptVerificationError(
            "verified_evidence_index_external_mutation_forbidden"
        )

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise EvidenceReceiptVerificationError(
            "verified_evidence_index_external_mutation_forbidden"
        )

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise EvidenceReceiptVerificationError(
            "verified_evidence_index_external_mutation_forbidden"
        )

    def _insert(self, token: object, binding: Mapping[str, Any]) -> None:
        if token is not _INDEX_TOKEN:
            raise EvidenceReceiptVerificationError(
                "verified_evidence_index_insert_forbidden"
            )
        evidence_ref = str(binding.get("evidence_ref") or "")
        if not evidence_ref:
            raise EvidenceReceiptVerificationError("verified_evidence_ref_missing")
        existing = self.get(evidence_ref)
        if existing is not None and existing.get("logical_hash") != binding.get(
            "logical_hash"
        ):
            raise EvidenceReceiptVerificationError(
                f"verified_evidence_ref_collision:{evidence_ref}"
            )
        dict.__setitem__(self, evidence_ref, dict(binding))

    def subset(self, evidence_refs: Sequence[str]) -> "VerifiedEvidenceIndexV1":
        result = VerifiedEvidenceIndexV1(_INDEX_TOKEN)
        for evidence_ref in sorted(set(str(value) for value in evidence_refs)):
            binding = self.get(evidence_ref)
            if binding is None:
                raise EvidenceReceiptVerificationError(
                    f"verified_evidence_ref_missing:{evidence_ref}"
                )
            result._insert(_INDEX_TOKEN, binding)
        return result


def is_verifier_owned_index(value: Any) -> bool:
    return (
        isinstance(value, VerifiedEvidenceIndexV1)
        and getattr(value, "_verifier_owned", False) is True
    )


class EvidenceReceiptVerifierV1:
    """Produce typed receipts and insert only independently verified bindings."""

    def __init__(
        self,
        *,
        authority: Any,
        primary_root: Path,
        upstream_root: Path,
        observed_upstream_head: str,
        bridge: GovernedUpstreamBridgeV1,
    ) -> None:
        self.authority = authority
        self.primary_root = primary_root.resolve()
        self.upstream_root = upstream_root.resolve()
        self.observed_upstream_head = observed_upstream_head
        self.bridge = bridge
        _verify_origin(
            self.primary_root,
            "fatcat2109/capital-chronicle-contentops",
        )
        _verify_origin(
            self.upstream_root,
            "fatcat2109/Headline-Raw-data-json",
        )
        if bridge.branch != "main":
            raise EvidenceReceiptVerificationError(
                "verified_upstream_branch_mismatch"
            )
        self.index = VerifiedEvidenceIndexV1(_INDEX_TOKEN)

    def _binding(
        self,
        *,
        evidence_ref: str,
        source_family_id: str,
        adapter_id: str,
        document_id: str,
        source_native_id: str,
        content_sha256: str,
        source_native_status: str,
        evidence_state: str,
        consumer_permission: str,
        dqr_reporting_allowed: bool,
        receipt: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        adapter = self.authority.adapter_bindings.get(adapter_id)
        family = self.authority.source_families.get(source_family_id)
        if not adapter or not family:
            raise EvidenceReceiptVerificationError(
                "verified_binding_registry_identity_missing"
            )
        if adapter.get("source_family_id") != source_family_id:
            raise EvidenceReceiptVerificationError(
                "verified_binding_adapter_family_mismatch"
            )
        binding_id = "evidence-binding:" + _logical_hash({
            "evidence_ref": evidence_ref,
            "adapter_binding_record_id": adapter["record_id"],
            "receipt_hash": receipt["logical_hash"],
        })[:24]
        value = {
            "schema_version": VERIFIED_BINDING_SCHEMA,
            "binding_id": binding_id,
            "accepted_evidence_binding_id": adapter["accepted_evidence_binding"],
            "evidence_ref": evidence_ref,
            "source_family_id": source_family_id,
            "adapter_id": adapter_id,
            "adapter_binding_record_id": adapter["record_id"],
            "document_id": document_id,
            "source_native_id": source_native_id,
            "content_sha256": content_sha256,
            "source_native_status": source_native_status,
            "evidence_state": evidence_state,
            "consumer_permission": consumer_permission,
            "dqr_reporting_allowed": dqr_reporting_allowed,
            "receipt": dict(receipt),
            "verifier_produced": True,
        }
        value["logical_hash"] = _logical_hash(value)
        self.index._insert(_INDEX_TOKEN, value)
        return self.index[evidence_ref]

    def verify_dbh2_record_binding(
        self,
        *,
        record: Mapping[str, Any],
        source_family_id: str,
        adapter_id: str,
        verification_cutoff_utc: str | None = None,
        requested_consumer_permission: str | None = None,
        requested_dqr_reporting_allowed: bool | None = None,
    ) -> Mapping[str, Any]:
        adapter = self.authority.adapter_bindings.get(adapter_id)
        if not adapter or adapter.get("source_family_id") != source_family_id:
            raise EvidenceReceiptVerificationError(
                "verified_binding_adapter_family_mismatch"
            )
        discovery = adapter.get("discovery_contract") or {}
        connection = self.bridge.open_duckdb()
        try:
            row = connection.execute(
                """
                SELECT record_id, stable_record_id, target_id,
                       provider_record_id, provider_record_type, version_id,
                       content_sha256, status, coalesce(updated_at, published_at),
                       canonical_url, exact_authority
                  FROM dbh2_records
                 WHERE stable_record_id = ? AND version_id = ?
                """,
                [record.get("stable_record_id"), record.get("version_id")],
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            raise EvidenceReceiptVerificationError("dbh2_verified_record_missing")
        observed = {
            "record_id": row[0],
            "stable_record_id": row[1],
            "target_id": row[2],
            "provider_record_id": row[3],
            "provider_record_type": row[4],
            "version_id": row[5],
            "content_sha256": row[6],
            "status": row[7],
            "known_at": str(row[8]),
            "canonical_url": row[9],
            "exact_authority": row[10],
        }
        for field in (
            "record_id",
            "stable_record_id",
            "target_id",
            "provider_record_id",
            "provider_record_type",
            "version_id",
            "content_sha256",
            "status",
        ):
            if str(record.get(field)) != str(observed[field]):
                raise EvidenceReceiptVerificationError(
                    f"dbh2_verified_record_mismatch:{field}"
                )
        expected_target = discovery.get("target_id")
        expected_type = discovery.get("provider_record_type")
        accepted_statuses = {
            str(value) for value in discovery.get("accepted_statuses") or []
        }
        if expected_target and str(observed["target_id"]) != str(expected_target):
            raise EvidenceReceiptVerificationError(
                "dbh2_verified_record_registry_target_mismatch"
            )
        if expected_type and str(observed["provider_record_type"]) != str(expected_type):
            raise EvidenceReceiptVerificationError(
                "dbh2_verified_record_registry_type_mismatch"
            )
        if accepted_statuses and str(observed["status"]) not in accepted_statuses:
            raise EvidenceReceiptVerificationError(
                "dbh2_verified_record_registry_status_blocked"
            )
        known_at = str(record.get("known_at_utc") or observed["known_at"])
        cutoff_utc = str(
            verification_cutoff_utc
            or record.get("verification_cutoff_utc")
            or known_at
        )
        if _parse_utc(str(observed["known_at"])) > _parse_utc(cutoff_utc):
            raise EvidenceReceiptVerificationError(
                "dbh2_verified_record_future_known_at"
            )
        consumer_permission = str(
            discovery.get("consumer_permission")
            or adapter.get("permission_ceiling")
            or "PERMISSION_BLOCKED"
        )
        evidence_state = str(discovery.get("evidence_state") or "context")
        dqr_reporting_allowed = (
            consumer_permission == "PUBLIC_CLAIM_ALLOWED"
            and evidence_state == "exact"
            and bool(observed["exact_authority"])
        )
        if (
            requested_consumer_permission is not None
            and requested_consumer_permission != consumer_permission
        ):
            raise EvidenceReceiptVerificationError(
                "dbh2_requested_consumer_permission_mismatch"
            )
        if (
            requested_dqr_reporting_allowed is not None
            and requested_dqr_reporting_allowed != dqr_reporting_allowed
        ):
            raise EvidenceReceiptVerificationError(
                "dbh2_requested_dqr_reporting_state_mismatch"
            )
        document_id = (
            f"dbh2-document:{observed['stable_record_id']}:"
            f"{observed['version_id']}"
        )
        bridge_packet = self.bridge.authority_packet()
        receipt = {
            "schema_version": DBH2_RECEIPT_SCHEMA,
            "receipt_kind": "dbh2_record_version",
            "exact_verified": True,
            "repository": "fatcat2109/Headline-Raw-data-json",
            "branch": self.bridge.branch,
            "observed_head": self.observed_upstream_head,
            "later_observed_branch_head": self.bridge.current_branch_head,
            "manifest_receipt_hash": _logical_hash(
                bridge_packet["manifest_receipt"]
            ),
            "local_artifact_receipt_hashes": sorted(
                _logical_hash(value)
                for value in bridge_packet["local_artifacts"]
            ),
            "target_id": observed["target_id"],
            "record_id": observed["record_id"],
            "stable_record_id": observed["stable_record_id"],
            "version_id": observed["version_id"],
            "provider_record_type": observed["provider_record_type"],
            "document_id": document_id,
            "source_native_id": observed["provider_record_id"],
            "authorized_urls": (
                [str(observed["canonical_url"])]
                if observed["canonical_url"] else []
            ),
            "content_sha256": observed["content_sha256"],
            "source_native_status": observed["status"],
            "evidence_state": evidence_state,
            "consumer_permission": consumer_permission,
            "dqr_reporting_allowed": dqr_reporting_allowed,
            "record_known_at_utc": known_at,
            "verification_cutoff_utc": cutoff_utc,
            "point_in_time_eligible": True,
            "verified_from_read_only_database": True,
            "authority_derived_from_manifest_row_and_registry": True,
        }
        receipt["logical_hash"] = _logical_hash(receipt)
        evidence_ref = (
            f"dbh2:{observed['target_id']}:{observed['stable_record_id']}:"
            f"{observed['version_id']}"
        )
        return self._binding(
            evidence_ref=evidence_ref,
            source_family_id=source_family_id,
            adapter_id=adapter_id,
            document_id=document_id,
            source_native_id=str(observed["provider_record_id"]),
            content_sha256=str(observed["content_sha256"]),
            source_native_status=str(observed["status"]),
            evidence_state=evidence_state,
            consumer_permission=consumer_permission,
            dqr_reporting_allowed=dqr_reporting_allowed,
            receipt=receipt,
        )

    def verify_git_claim_binding(
        self,
        *,
        artifact_path: str,
        producer_commit: str,
        source_family_id: str,
        adapter_id: str,
        pool_id: str,
        candidate_id: str,
        claim_id: str,
        requested_consumer_permission: str | None = None,
        requested_dqr_reporting_allowed: bool | None = None,
    ) -> Mapping[str, Any]:
        content, git_receipt = read_git_artifact(
            root=self.upstream_root,
            observed_head=self.observed_upstream_head,
            artifact_path=artifact_path,
            producer_commit=producer_commit,
        )
        try:
            artifact = json.loads(content)
        except json.JSONDecodeError as error:
            raise EvidenceReceiptVerificationError(
                "verified_git_artifact_json_malformed"
            ) from error
        if artifact.get("pool_id") != pool_id:
            raise EvidenceReceiptVerificationError(
                "verified_git_pool_identity_mismatch"
            )
        candidate = next(
            (
                value
                for value in artifact.get("eligible_candidates") or []
                if str(value.get("candidate_id")) == candidate_id
            ),
            None,
        )
        if candidate is None:
            raise EvidenceReceiptVerificationError(
                "verified_git_candidate_identity_missing"
            )
        claim = next(
            (
                value
                for value in candidate.get("numeric_claims") or []
                if str(value.get("claim_id")) == claim_id
            ),
            None,
        )
        if claim is None:
            raise EvidenceReceiptVerificationError(
                "verified_git_claim_lineage_missing"
            )
        documents = list(candidate.get("source_documents") or [])
        source_id = str(claim.get("source_id") or "")
        document = next(
            (
                value for value in documents
                if str(value.get("document_id")) == source_id
            ),
            documents[0] if len(documents) == 1 else None,
        )
        if document is None:
            raise EvidenceReceiptVerificationError(
                "verified_git_claim_document_missing"
            )
        claim_permissions = candidate.get("claim_permissions") or {}
        candidate_reporting_allowed = (
            claim_permissions.get("reporting_allowed") is True
        )
        claim_permission = (
            "PUBLIC_CLAIM_ALLOWED"
            if claim.get("public_claim_allowed") is True
            else "REPORTING_NOT_ALLOWED"
        )
        consumer_permission = (
            claim_permission
            if candidate_reporting_allowed
            else "REPORTING_NOT_ALLOWED"
        )
        dqr_reporting_allowed = (
            candidate_reporting_allowed
            and claim_permission == "PUBLIC_CLAIM_ALLOWED"
            and (candidate.get("authority") or {}).get("story_decision") == "ALLOW"
        )
        if (
            requested_consumer_permission is not None
            and requested_consumer_permission != consumer_permission
        ):
            raise EvidenceReceiptVerificationError(
                "verified_git_requested_consumer_permission_mismatch"
            )
        if (
            requested_dqr_reporting_allowed is not None
            and requested_dqr_reporting_allowed != dqr_reporting_allowed
        ):
            raise EvidenceReceiptVerificationError(
                "verified_git_requested_dqr_reporting_state_mismatch"
            )
        authorized_urls = sorted({
            str(value)
            for value in (document.get("source_url"), document.get("data_url"))
            if value
        })
        evidence_state = str(candidate.get("evidence_class") or "unverified")
        source_native_status = (
            "eligible" if candidate.get("eligible") is True else "ineligible"
        )
        candidate_evidence_hash = str(candidate.get("evidence_hash") or "")
        document_id = str(document.get("document_id") or "")
        source_native_id = document_id
        content_sha256 = str(
            document.get("raw_sha256") or document.get("content_sha256") or ""
        )
        if not all((candidate_evidence_hash, document_id, content_sha256)):
            raise EvidenceReceiptVerificationError(
                "verified_git_authority_field_missing"
            )
        receipt = {
            "schema_version": GIT_RECEIPT_SCHEMA,
            "receipt_kind": "git_artifact",
            "exact_verified": True,
            **git_receipt.as_dict(),
            "pool_id": str(artifact["pool_id"]),
            "pool_logical_hash": str(artifact.get("logical_hash") or ""),
            "candidate_id": str(candidate["candidate_id"]),
            "candidate_evidence_hash": candidate_evidence_hash,
            "claim_id": str(claim["claim_id"]),
            "claim_type": "numeric_observation",
            "claim_permission": claim_permission,
            "candidate_reporting_permission": candidate_reporting_allowed,
            "dqr_reporting_allowed": dqr_reporting_allowed,
            "document_id": document_id,
            "source_native_id": source_native_id,
            "authorized_urls": authorized_urls,
            "content_sha256": content_sha256,
            "source_native_status": source_native_status,
            "consumer_permission": consumer_permission,
            "evidence_state": evidence_state,
            "verified_from_exact_git_bytes": True,
            "authority_fields_verifier_derived": True,
        }
        receipt["logical_hash"] = _logical_hash(receipt)
        evidence_ref = f"v1:{candidate_evidence_hash}:{claim_id}"
        return self._binding(
            evidence_ref=evidence_ref,
            source_family_id=source_family_id,
            adapter_id=adapter_id,
            document_id=document_id,
            source_native_id=source_native_id,
            content_sha256=content_sha256,
            source_native_status=source_native_status,
            evidence_state=evidence_state,
            consumer_permission=consumer_permission,
            dqr_reporting_allowed=dqr_reporting_allowed,
            receipt=receipt,
        )

    def verify_nonnumeric_story_authority_bindings(
        self,
        *,
        artifact_path: str,
        producer_commit: str,
        source_family_id: str,
        adapter_id: str,
        requested_claim_ids: Sequence[str] | None = None,
        requested_consumer_permission: str | None = None,
        requested_dqr_reporting_allowed: bool | None = None,
    ) -> tuple[Mapping[str, Any], ...]:
        """Verify and bind the exact first nonnumeric story authority packet."""

        expected_path = (
            "docs/research/publication_evidence/current/"
            "CapitalChronicleNonnumericStoryScopedReportingAuthorityV1.json"
        )
        expected_commit = "ce4d011059b4a78eec47455821f93c418090d944"
        expected_claims = [
            {
                "claim_id": "claim-bfca0e50bb4f64d0",
                "claim_type": "official_regulatory_action",
                "contains_numeric_assertion": False,
                "interpretation_allowed": False,
                "reporting_allowed": True,
                "source_field": "selected_raw_record.abstract",
                "text": (
                    "The OCC, Board, FDIC, NCUA, CFPB, FHFA, CFTC, SEC, and "
                    "Treasury are publishing a final joint rule to establish "
                    "data standards to promote interoperability of financial "
                    "regulatory data across these agencies."
                ),
            },
            {
                "claim_id": "claim-1936ed019eb6602d",
                "claim_type": "official_regulatory_limitation",
                "contains_numeric_assertion": False,
                "interpretation_allowed": False,
                "reporting_allowed": True,
                "source_field": "selected_raw_record.abstract",
                "text": (
                    "At the effective date, the joint rule will not change any "
                    "reporting requirements without further action by the agencies."
                ),
            },
        ]
        expected_claim_ids = tuple(row["claim_id"] for row in expected_claims)
        if artifact_path != expected_path:
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_artifact_path_mismatch"
            )
        if producer_commit != expected_commit:
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_producer_commit_mismatch"
            )
        if requested_claim_ids is not None and tuple(requested_claim_ids) != expected_claim_ids:
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_requested_claim_set_mismatch"
            )
        content, git_receipt = read_git_artifact(
            root=self.upstream_root,
            observed_head=self.observed_upstream_head,
            artifact_path=artifact_path,
            producer_commit=producer_commit,
        )
        git_receipt_fields = git_receipt.as_dict()
        expected_git_receipt_fields = {
            "repository": "fatcat2109/Headline-Raw-data-json",
            "branch": "main",
            "observed_head": self.observed_upstream_head,
            "producer_commit": expected_commit,
            "artifact_path": expected_path,
            "git_blob_sha1": sha1(
                f"blob {len(content)}\0".encode("ascii") + content
            ).hexdigest(),
            "byte_sha256": sha256(content).hexdigest(),
            "byte_length": len(content),
        }
        for field, expected in expected_git_receipt_fields.items():
            if git_receipt_fields.get(field) != expected:
                raise EvidenceReceiptVerificationError(
                    f"nonnumeric_story_git_receipt_{field}_mismatch"
                )
        try:
            packet = json.loads(content)
        except json.JSONDecodeError as error:
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_packet_json_malformed"
            ) from error
        if not isinstance(packet, Mapping):
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_packet_root_invalid"
            )
        packet_without_hash = _without_hash(packet)
        if packet.get("logical_hash") != _logical_hash(packet_without_hash):
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_packet_logical_hash_mismatch"
            )
        exact_top_level = {
            "schema_version": (
                "capital_chronicle.nonnumeric_story_scoped_reporting_authority.v1"
            ),
            "packet_id": "cc-nonnumeric-f93c722c9c8f46741bb8",
            "task_id": "TASK_DATABASE_NONNUMERIC_STORY_SCOPED_REPORTING_AUTHORITY_V1",
            "terminal_status": (
                "PASS_NONNUMERIC_STORY_SCOPED_REPORTING_AUTHORITY_V1_"
                "AWAITING_CHATGPT_AUDIT"
            ),
            "generated_at_utc": "2026-07-12T16:18:42.619968+00:00",
        }
        for field, expected in exact_top_level.items():
            if packet.get(field) != expected:
                raise EvidenceReceiptVerificationError(
                    f"nonnumeric_story_packet_{field}_mismatch"
                )
        if packet.get("claims") != expected_claims:
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_exact_claim_set_mismatch"
            )
        selected_story = packet.get("selected_story") or {}
        expected_story = {
            "authorized_public_use_url": (
                "https://www.govinfo.gov/content/pkg/FR-2026-06-25/pdf/"
                "2026-12787.pdf"
            ),
            "candidate_only": True,
            "canonical_url": (
                "https://www.federalregister.gov/documents/2026/06/25/"
                "2026-12787/financial-data-transparency-act-joint-data-standards"
            ),
            "content_sha256": (
                "63641fe4cec40cad1834708798b51ca38de3739f16756123de1dd8eaafe74f30"
            ),
            "current_canonical_apply": False,
            "document_type": "Rule",
            "exact_numeric_authority": False,
            "numeric_boundary": "numeric_text_not_numeric_truth",
            "official_family": "federal_register",
            "provider": "Federal Register",
            "provider_record_id": "2026-12787",
            "provider_record_type": "federal_register_document",
            "stable_record_id": (
                "cf9b73452130757eb3552a87bf86bf6d8bc5531c263d4d7dabad7a1169345d09"
            ),
            "target_id": "DBH2_FEDERAL_REGISTER_FED_SYSTEM",
            "title": "Financial Data Transparency Act Joint Data Standards",
            "version_id": (
                "a6554c195bb3e7840fb66fbe986cd0f23f0a85a320d8ef4ddf8ce7346b116701"
            ),
        }
        if selected_story != expected_story:
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_identity_or_boundary_mismatch"
            )
        expected_lineage = {
            "is_corrected": False,
            "is_current_version": True,
            "is_superseded": False,
            "is_withdrawn": False,
            "relationship_count": 0,
            "relationships": [],
        }
        if packet.get("lineage") != expected_lineage:
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_current_lineage_mismatch"
            )
        expected_timestamps = {
            "event_at": "2026-06-25",
            "event_precision": "DAY",
            "known_at_precision": "MICROSECOND",
            "known_at_utc": "2026-07-12T16:18:42.619968+00:00",
            "provider_updated_at": "2026-06-25",
            "published_at": "2026-06-25",
            "published_precision": "DAY",
            "revision_precision": "DAY",
        }
        if packet.get("timestamps") != expected_timestamps:
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_timestamp_lineage_mismatch"
            )
        expected_public_scope = {
            "attribution_required": True,
            "basis": "official_federal_register_and_govinfo_public_record",
            "copyright_ownership_adjudicated": False,
            "decision": "PASS_OFFICIAL_PUBLIC_RECORD_FACTUAL_REPORTING",
            "scope": (
                "quote_or_paraphrase_packet_claims_with_official_source_attribution"
            ),
        }
        if packet.get("public_use_scope") != expected_public_scope:
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_public_use_scope_mismatch"
            )
        permissions = packet.get("consumer_permissions") or {}
        expected_permissions = {
            "authorized_claim_ids": list(expected_claim_ids),
            "consumer_class": "contentops_publication",
            "decision": "PASS_STORY_SCOPED_NONNUMERIC_REPORTING",
            "derived_from_verifier": True,
            "dispatch_allowed": False,
            "exact_story_only": True,
            "financial_advice_allowed": False,
            "forecast_allowed": False,
            "global_dqr_override": False,
            "numeric_reporting_allowed": False,
            "reporting_allowed": True,
            "source_family_wide_authority": False,
            "trading_allowed": False,
        }
        if permissions != expected_permissions:
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_consumer_permission_mismatch"
            )
        if packet.get("protected_state") != {
            "analyzer_authority_changed": False,
            "current_canonical_authority_changed": False,
            "global_dqr_override": False,
            "global_dqr_status": "BLOCKED",
            "protected_state_mutation_count": 0,
            "source_family_promoted": False,
        }:
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_protected_state_mismatch"
            )
        if packet.get("ofac_boundary") != {
            "promotion_allowed": False,
            "reporting_authority": False,
            "status": "context_only_current_snapshot_not_history",
        }:
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_ofac_boundary_mismatch"
            )
        source_receipt = packet.get("source_receipt") or {}
        expected_source_binding = {
            "raw_manifest_id": (
                "f59dcfa634f4aab184e60869d5718519071310139e92a8a0afe65355f7083415"
            ),
            "raw_manifest_ref": (
                "docs/research/database_foundation/"
                "public_free_event_text_entity_history_v1/"
                "DBH2_RAW_MANIFEST_INDEX_V1.json"
            ),
            "raw_retrieved_at_utc": "2026-07-12T16:18:42.619968+00:00",
            "raw_sha256": (
                "5bb10637207641d5b562909f0a115e873fc75bb1a250a375586bad837a29cf2a"
            ),
            "parquet_sha256": (
                "e2792c34a09e46426d09ac8708592b4e123267ac7a295c85e90a1b0f739bd62f"
            ),
            "raw_hash_verified": True,
        }
        if any(source_receipt.get(key) != value for key, value in expected_source_binding.items()):
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_source_manifest_binding_mismatch"
            )
        verifier = packet.get("verifier") or {}
        checks = verifier.get("checks") or {}
        if (
            verifier.get("status") != "PASS"
            or verifier.get("blockers") != []
            or not checks
            or not all(value is True for value in checks.values())
        ):
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_upstream_independent_verification_not_pass"
            )
        consumer_permission = "PUBLIC_CLAIM_ALLOWED"
        dqr_reporting_allowed = True
        if (
            requested_consumer_permission is not None
            and requested_consumer_permission != consumer_permission
        ):
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_requested_consumer_permission_mismatch"
            )
        if (
            requested_dqr_reporting_allowed is not None
            and requested_dqr_reporting_allowed != dqr_reporting_allowed
        ):
            raise EvidenceReceiptVerificationError(
                "nonnumeric_story_requested_dqr_reporting_state_mismatch"
            )
        document_id = (
            f"nonnumeric-story-document:{selected_story['stable_record_id']}:"
            f"{selected_story['version_id']}"
        )
        authorized_urls = sorted([
            selected_story["authorized_public_use_url"],
            selected_story["canonical_url"],
        ])
        receipt = {
            "schema_version": NONNUMERIC_STORY_RECEIPT_SCHEMA,
            "receipt_kind": "exact_git_nonnumeric_story_authority",
            "exact_verified": True,
            **git_receipt.as_dict(),
            "packet_logical_hash": packet["logical_hash"],
            "packet_id": packet["packet_id"],
            "packet_schema_version": packet["schema_version"],
            "packet_terminal_status": packet["terminal_status"],
            "upstream_verifier_status": verifier["status"],
            "target_id": selected_story["target_id"],
            "stable_record_id": selected_story["stable_record_id"],
            "version_id": selected_story["version_id"],
            "provider_record_id": selected_story["provider_record_id"],
            "provider_record_type": selected_story["provider_record_type"],
            "document_id": document_id,
            "source_native_id": selected_story["provider_record_id"],
            "authorized_urls": authorized_urls,
            "content_sha256": selected_story["content_sha256"],
            "source_native_status": selected_story["document_type"],
            "evidence_state": "exact",
            "consumer_permission": consumer_permission,
            "dqr_reporting_allowed": dqr_reporting_allowed,
            "authorized_claim_ids": list(expected_claim_ids),
            "authorized_claims": expected_claims,
            "timestamps": expected_timestamps,
            "public_use_scope": expected_public_scope,
            "global_dqr_status": "BLOCKED",
            "global_dqr_override": False,
            "source_family_wide_authority": False,
            "ofac_context_only": True,
            "numeric_reporting_allowed": False,
            "dispatch_allowed": False,
            "verified_from_exact_git_bytes": True,
            "authority_fields_verifier_derived": True,
        }
        receipt["logical_hash"] = _logical_hash(receipt)
        bindings = []
        for claim_id in expected_claim_ids:
            evidence_ref = f"nonnumeric-story:{packet['packet_id']}:{claim_id}"
            bindings.append(self._binding(
                evidence_ref=evidence_ref,
                source_family_id=source_family_id,
                adapter_id=adapter_id,
                document_id=document_id,
                source_native_id=str(selected_story["provider_record_id"]),
                content_sha256=str(selected_story["content_sha256"]),
                source_native_status=str(selected_story["document_type"]),
                evidence_state="exact",
                consumer_permission=consumer_permission,
                dqr_reporting_allowed=dqr_reporting_allowed,
                receipt=receipt,
            ))
        return tuple(bindings)

    def verify_aggregation_binding(
        self,
        *,
        evidence_ref: str,
        source_family_id: str,
        adapter_id: str,
        document_id: str,
        source_native_id: str,
        content_sha256: str,
        source_native_status: str,
        evidence_state: str,
        consumer_permission: str,
        dqr_reporting_allowed: bool,
        consumed_evidence_refs: Sequence[str],
        aggregation_contract: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        refs = tuple(sorted(set(str(value) for value in consumed_evidence_refs)))
        if not refs or len(refs) != len(consumed_evidence_refs):
            raise EvidenceReceiptVerificationError(
                "verified_aggregation_consumed_ref_set_invalid"
            )
        missing = [value for value in refs if value not in self.index]
        if missing:
            raise EvidenceReceiptVerificationError(
                "verified_aggregation_input_not_verified"
            )
        receipt = {
            "schema_version": AGGREGATION_RECEIPT_SCHEMA,
            "receipt_kind": "accepted_aggregation",
            "exact_verified": True,
            "consumed_evidence_refs": list(refs),
            "consumed_binding_hashes": [
                self.index[value]["logical_hash"] for value in refs
            ],
            "aggregation_contract": dict(aggregation_contract),
            "aggregation_contract_hash": _logical_hash(aggregation_contract),
            "verified_exact_input_set": True,
        }
        receipt["logical_hash"] = _logical_hash(receipt)
        return self._binding(
            evidence_ref=evidence_ref,
            source_family_id=source_family_id,
            adapter_id=adapter_id,
            document_id=document_id,
            source_native_id=source_native_id,
            content_sha256=content_sha256,
            source_native_status=source_native_status,
            evidence_state=evidence_state,
            consumer_permission=consumer_permission,
            dqr_reporting_allowed=dqr_reporting_allowed,
            receipt=receipt,
        )


def verify_runtime_implementation(
    *,
    repo_root: Path,
    observed_commit: str,
    implementation_receipt: Mapping[str, Any],
    expected_identity: str,
) -> Any:
    """Verify exact committed implementation bytes and resolve that callable."""

    if (
        implementation_receipt.get("repository")
        != "fatcat2109/capital-chronicle-contentops"
        or implementation_receipt.get("branch") != "master"
    ):
        raise EvidenceReceiptVerificationError(
            "implementation_receipt_repository_or_branch_mismatch"
        )
    _verify_origin(repo_root, "fatcat2109/capital-chronicle-contentops")
    if implementation_receipt.get("schema_version") != IMPLEMENTATION_RECEIPT_SCHEMA:
        raise EvidenceReceiptVerificationError(
            "implementation_receipt_schema_invalid"
        )
    producer = str(implementation_receipt.get("producer_commit") or "")
    if not _is_ancestor(repo_root, producer, observed_commit):
        raise EvidenceReceiptVerificationError(
            "implementation_producer_not_reachable"
        )
    path = str(implementation_receipt.get("path") or "")
    content = _git(repo_root, "show", f"{producer}:{path}")
    observed = {
        "git_blob_sha1": sha1(
            f"blob {len(content)}\0".encode() + content
        ).hexdigest(),
        "byte_sha256": sha256(content).hexdigest(),
        "byte_length": len(content),
    }
    for field, value in observed.items():
        if implementation_receipt.get(field) != value:
            raise EvidenceReceiptVerificationError(
                f"implementation_receipt_{field}_mismatch"
            )
    receipt_identity = str(
        implementation_receipt.get("callable_identity") or ""
    )
    if receipt_identity != expected_identity:
        raise EvidenceReceiptVerificationError(
            "implementation_receipt_callable_mismatch"
        )
    module_name, attribute = receipt_identity.rsplit(".", 1)
    implementation = getattr(importlib.import_module(module_name), attribute, None)
    if not callable(implementation):
        raise EvidenceReceiptVerificationError(
            "implementation_callable_unavailable"
        )
    source_file = inspect.getsourcefile(implementation)
    if not source_file:
        raise EvidenceReceiptVerificationError(
            "implementation_runtime_source_unavailable"
        )
    source_path = Path(source_file).resolve()
    try:
        runtime_relative_path = source_path.relative_to(repo_root.resolve()).as_posix()
    except ValueError as error:
        raise EvidenceReceiptVerificationError(
            "implementation_runtime_source_outside_repository"
        ) from error
    if runtime_relative_path != path:
        raise EvidenceReceiptVerificationError(
            "implementation_runtime_source_path_mismatch"
        )
    runtime_blob_sha1 = _git(
        repo_root,
        "hash-object",
        f"--path={runtime_relative_path}",
        runtime_relative_path,
    ).decode("ascii").strip()
    if runtime_blob_sha1 != implementation_receipt.get("git_blob_sha1"):
        raise EvidenceReceiptVerificationError(
            "implementation_runtime_bytes_mismatch"
        )
    expected_hash = _logical_hash(_without_hash(implementation_receipt))
    if implementation_receipt.get("logical_hash") != expected_hash:
        raise EvidenceReceiptVerificationError(
            "implementation_receipt_logical_hash_mismatch"
        )
    return implementation
