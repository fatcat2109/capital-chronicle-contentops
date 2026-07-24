"""Verifier-owned evidence receipts for governed candidate authority.

The objects in this module are intentionally produced from exact bytes and
read-only database records.  A caller-supplied mapping, including one carrying
the legacy ``exact_verified`` boolean, is never a trusted evidence index.
"""
from __future__ import annotations

from hashlib import sha1, sha256
import importlib
import json
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
        document_id: str,
        evidence_state: str = "context",
        consumer_permission: str = "CONTEXT_ONLY",
        dqr_reporting_allowed: bool = False,
    ) -> Mapping[str, Any]:
        connection = self.bridge.open_duckdb()
        try:
            row = connection.execute(
                """
                SELECT record_id, stable_record_id, target_id,
                       provider_record_id, provider_record_type, version_id,
                       content_sha256, status, coalesce(updated_at, published_at)
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
            "content_sha256": observed["content_sha256"],
            "source_native_status": observed["status"],
            "verified_from_read_only_database": True,
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
        document_id: str,
        source_native_id: str,
        content_sha256: str,
        source_native_status: str,
        evidence_state: str,
        consumer_permission: str,
        dqr_reporting_allowed: bool,
        pool_id: str,
        pool_logical_hash: str,
        candidate_evidence_hash: str,
        claim_id: str,
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
        if (
            artifact.get("pool_id") != pool_id
            or artifact.get("logical_hash") != pool_logical_hash
        ):
            raise EvidenceReceiptVerificationError(
                "verified_git_pool_identity_mismatch"
            )
        candidates = list(artifact.get("eligible_candidates") or [])
        candidate = next(
            (
                value
                for value in candidates
                if value.get("evidence_hash") == candidate_evidence_hash
            ),
            None,
        )
        if candidate is None or claim_id not in {
            str(value.get("claim_id"))
            for value in candidate.get("numeric_claims") or []
        }:
            raise EvidenceReceiptVerificationError(
                "verified_git_claim_lineage_missing"
            )
        receipt = {
            "schema_version": GIT_RECEIPT_SCHEMA,
            "receipt_kind": "git_artifact",
            "exact_verified": True,
            **git_receipt.as_dict(),
            "pool_id": pool_id,
            "pool_logical_hash": pool_logical_hash,
            "candidate_evidence_hash": candidate_evidence_hash,
            "claim_id": claim_id,
            "verified_from_exact_git_bytes": True,
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
    expected_hash = _logical_hash(_without_hash(implementation_receipt))
    if implementation_receipt.get("logical_hash") != expected_hash:
        raise EvidenceReceiptVerificationError(
            "implementation_receipt_logical_hash_mismatch"
        )
    return implementation
