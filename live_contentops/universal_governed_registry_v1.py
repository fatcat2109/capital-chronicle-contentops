"""Receipt-bound authority for the universal candidate fabric.

The registry files are loaded from exact committed Git bytes. Runtime callers
may select registered IDs or request a narrower output, but cannot supply a
new authority-bearing source, adapter, claim capability, evidence profile, or
market-evidence capability.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1, sha256
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence


REPOSITORY = "fatcat2109/capital-chronicle-contentops"
BRANCH = "master"
STARTING_AUTHORITY_COMMIT = "7c5ea920cadb6efb3a8b85282f43eb05c5544374"
REGISTRY_PRODUCER_COMMIT = "455940fe683e46b358c5ffebbcc256360d28aa9a"
AUTHORITY_MANIFEST_COMMIT = "2162ba00effc70fbf30a7f87bda111b673ae5807"
AUTHORITY_MANIFEST_PATH = (
    "live_contentops/governed_universal_registry_authority_manifest_v1.json"
)
EXACT_BINDING_SCHEMA = "contentops.exact_claim_evidence_binding.v1"
MARKET_BINDING_SCHEMA = "contentops.governed_market_evidence_binding.v1"

AUTHORITY_RANK = {
    "UNAVAILABLE": 0,
    "UNVERIFIED": 0,
    "BLOCKED": 0,
    "CONTEXT_ONLY": 1,
    "VERIFIED_GOVERNED": 2,
    "OFFICIAL_VERIFIED": 2,
    "FIRST_PARTY_VERIFIED": 2,
}
PERMISSION_RANK = {
    "UNAVAILABLE": 0,
    "PERMISSION_BLOCKED": 0,
    "REPORTING_NOT_ALLOWED": 0,
    "CONTEXT_ONLY": 1,
    "REPORTING_ALLOWED": 2,
    "PUBLIC_CLAIM_ALLOWED": 3,
}


class GovernedRegistryError(ValueError):
    """Fail-closed registry, evidence-chain, or lineage violation."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def logical_hash(value: Any) -> str:
    return sha256(canonical_json(value)).hexdigest()


def without_hash(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "logical_hash"}


def git_blob_sha1(content: bytes) -> str:
    return sha1(f"blob {len(content)}\0".encode() + content).hexdigest()


def _git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(root), *args],
        stderr=subprocess.DEVNULL,
    )


def _is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "merge-base",
            "--is-ancestor",
            ancestor,
            descendant,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def _git_bytes(root: Path, commit: str, path: str) -> bytes:
    try:
        return _git(root, "show", f"{commit}:{path}")
    except subprocess.CalledProcessError as error:
        raise GovernedRegistryError(f"registry_git_artifact_missing:{path}") from error


def _parse_object(content: bytes, *, path: str) -> dict[str, Any]:
    try:
        value = json.loads(content)
    except json.JSONDecodeError as error:
        raise GovernedRegistryError(f"registry_json_malformed:{path}") from error
    if not isinstance(value, dict):
        raise GovernedRegistryError(f"registry_json_root_invalid:{path}")
    return value


def _record_key(registry_id: str) -> str:
    return {
        "claim_capabilities": "record_id",
        "evidence_profiles": "record_id",
        "source_families": "record_id",
        "adapter_source_bindings": "record_id",
        "market_evidence_capabilities": "record_id",
    }[registry_id]


def _validate_registry(
    registry_id: str,
    value: Mapping[str, Any],
) -> tuple[str, ...]:
    blockers: list[str] = []
    if value.get("logical_hash") != logical_hash(without_hash(value)):
        blockers.append(f"{registry_id}:registry_logical_hash_mismatch")
    records = value.get("records")
    if not isinstance(records, list) or not records:
        blockers.append(f"{registry_id}:registry_records_missing")
        return tuple(blockers)
    identity_field = _record_key(registry_id)
    identities: list[str] = []
    for record in records:
        if not isinstance(record, Mapping):
            blockers.append(f"{registry_id}:registry_record_invalid")
            continue
        identity = str(record.get(identity_field) or "")
        identities.append(identity)
        if not identity:
            blockers.append(f"{registry_id}:record_id_missing")
        if record.get("logical_hash") != logical_hash(without_hash(record)):
            blockers.append(f"{registry_id}:{identity}:record_logical_hash_mismatch")
        for field in (
            "enabled",
            "authority_derivation_rule",
            "permission_derivation_rule",
            "implementation_identity",
            "accepted_evidence_binding",
        ):
            if record.get(field) in (None, ""):
                blockers.append(f"{registry_id}:{identity}:{field}_missing")
    if len(identities) != len(set(identities)):
        blockers.append(f"{registry_id}:record_identity_duplicate")
    if registry_id == "evidence_profiles":
        for contract in value.get("composition_contracts") or []:
            contract_id = str(contract.get("contract_id") or "")
            if contract.get("logical_hash") != logical_hash(without_hash(contract)):
                blockers.append(
                    f"{registry_id}:{contract_id}:composition_logical_hash_mismatch"
                )
    return tuple(sorted(set(blockers)))


def _legacy_records(value: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    return value.get("records") or value.get("profiles") or ()


def _verify_append_only(
    *,
    root: Path,
    registries: Mapping[str, Mapping[str, Any]],
    baselines: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    reports: list[dict[str, Any]] = []
    for baseline in baselines:
        registry_id = str(baseline["registry_id"])
        baseline_value = _parse_object(
            _git_bytes(
                root,
                str(baseline["baseline_commit"]),
                str(baseline["baseline_path"]),
            ),
            path=str(baseline["baseline_path"]),
        )
        identity_field = str(baseline["identity_field"])
        preserved_fields = [str(field) for field in baseline["preserved_fields"]]
        baseline_by_id = {
            str(row.get(identity_field)): row
            for row in _legacy_records(baseline_value)
        }
        current_by_id = {
            str(row.get(identity_field)): row
            for row in registries[registry_id]["records"]
        }
        blockers: list[str] = []
        for identity, old in baseline_by_id.items():
            current = current_by_id.get(identity)
            if current is None:
                blockers.append(f"baseline_record_removed:{identity}")
                continue
            for field in preserved_fields:
                old_field = field
                current_field = field
                if field == "authority_class" and "authority_ceiling" in current:
                    current_field = "authority_ceiling"
                if old.get(old_field) != current.get(current_field):
                    blockers.append(f"baseline_field_mutated:{identity}:{field}")
        reports.append({
            "registry_id": registry_id,
            "baseline_commit": baseline["baseline_commit"],
            "baseline_path": baseline["baseline_path"],
            "baseline_mode": baseline.get("baseline_mode", "APPEND_ONLY_SUPERSET"),
            "baseline_record_count": len(baseline_by_id),
            "current_record_count": len(current_by_id),
            "blockers": sorted(blockers),
            "status": "PASS" if not blockers else "FAIL",
        })
    return tuple(reports)


@dataclass(frozen=True)
class GovernedRegistrySnapshotV1:
    observed_commit: str
    manifest: Mapping[str, Any]
    registries: Mapping[str, Mapping[str, Any]]
    receipts: tuple[Mapping[str, Any], ...]
    append_only_reports: tuple[Mapping[str, Any], ...]
    authority_manifest_receipt: Mapping[str, Any]

    def records_by(
        self,
        registry_id: str,
        identity_field: str,
    ) -> Mapping[str, Mapping[str, Any]]:
        return {
            str(row[identity_field]): row
            for row in self.registries[registry_id]["records"]
        }

    @property
    def claim_capabilities(self) -> Mapping[str, Mapping[str, Any]]:
        return self.records_by("claim_capabilities", "claim_type")

    @property
    def evidence_profiles(self) -> Mapping[str, Mapping[str, Any]]:
        return self.records_by("evidence_profiles", "profile_id")

    @property
    def source_families(self) -> Mapping[str, Mapping[str, Any]]:
        return self.records_by("source_families", "source_family_id")

    @property
    def adapter_bindings(self) -> Mapping[str, Mapping[str, Any]]:
        return self.records_by("adapter_source_bindings", "adapter_id")

    @property
    def market_capabilities(self) -> Mapping[str, Mapping[str, Any]]:
        return self.records_by(
            "market_evidence_capabilities",
            "capability_id",
        )

    def authority_packet(self) -> dict[str, Any]:
        value = {
            "schema_version": "contentops.governed_registry_authority_packet.v1",
            "repository": REPOSITORY,
            "branch": BRANCH,
            "observed_commit": self.observed_commit,
            "registry_producer_commit": self.manifest["producer_commit"],
            "authority_manifest_receipt": dict(self.authority_manifest_receipt),
            "registry_receipts": [dict(row) for row in self.receipts],
            "append_only_verification": [
                dict(row) for row in self.append_only_reports
            ],
            "caller_registry_creation_allowed": False,
            "all_registries_verified": True,
        }
        value["logical_hash"] = logical_hash(value)
        return value


def load_governed_registry_authority(
    *,
    repo_root: Path,
    observed_commit: str = "HEAD",
) -> GovernedRegistrySnapshotV1:
    root = repo_root.resolve()
    observed = _git(root, "rev-parse", observed_commit).decode().strip()
    if not _is_ancestor(root, REGISTRY_PRODUCER_COMMIT, observed):
        raise GovernedRegistryError("registry_producer_not_reachable")
    if not _is_ancestor(root, AUTHORITY_MANIFEST_COMMIT, observed):
        raise GovernedRegistryError("registry_authority_manifest_not_reachable")
    manifest_bytes = _git_bytes(
        root,
        AUTHORITY_MANIFEST_COMMIT,
        AUTHORITY_MANIFEST_PATH,
    )
    manifest = _parse_object(manifest_bytes, path=AUTHORITY_MANIFEST_PATH)
    if manifest.get("logical_hash") != logical_hash(without_hash(manifest)):
        raise GovernedRegistryError("registry_authority_manifest_hash_mismatch")
    if manifest.get("repository") != REPOSITORY or manifest.get("branch") != BRANCH:
        raise GovernedRegistryError("registry_authority_repository_mismatch")
    if manifest.get("producer_commit") != REGISTRY_PRODUCER_COMMIT:
        raise GovernedRegistryError("registry_authority_producer_mismatch")

    registries: dict[str, Mapping[str, Any]] = {}
    receipts: list[Mapping[str, Any]] = []
    for receipt in manifest.get("receipts") or []:
        registry_id = str(receipt["registry_id"])
        path = str(receipt["path"])
        content = _git_bytes(root, REGISTRY_PRODUCER_COMMIT, path)
        observed_receipt = {
            **dict(receipt),
            "repository": REPOSITORY,
            "branch": BRANCH,
            "producer_commit": REGISTRY_PRODUCER_COMMIT,
            "observed_commit": observed,
            "observed_git_blob_sha1": git_blob_sha1(content),
            "observed_byte_sha256": sha256(content).hexdigest(),
            "observed_byte_length": len(content),
        }
        if (
            observed_receipt["observed_git_blob_sha1"] != receipt["git_blob_sha1"]
            or observed_receipt["observed_byte_sha256"] != receipt["byte_sha256"]
            or observed_receipt["observed_byte_length"] != receipt["byte_length"]
        ):
            raise GovernedRegistryError(f"registry_receipt_mismatch:{registry_id}")
        value = _parse_object(content, path=path)
        if (
            value.get("schema_version") != receipt["schema_version"]
            or value.get("registry_version") != receipt["registry_version"]
        ):
            raise GovernedRegistryError(f"registry_version_mismatch:{registry_id}")
        blockers = _validate_registry(registry_id, value)
        if blockers:
            raise GovernedRegistryError(",".join(blockers))
        observed_receipt["status"] = "PASS_EXACT_COMMITTED_BYTES"
        registries[registry_id] = value
        receipts.append(observed_receipt)
    required = {
        "claim_capabilities",
        "evidence_profiles",
        "source_families",
        "adapter_source_bindings",
        "market_evidence_capabilities",
    }
    if set(registries) != required:
        raise GovernedRegistryError("registry_authority_set_incomplete")
    append_only = _verify_append_only(
        root=root,
        registries=registries,
        baselines=manifest.get("append_only_baselines") or (),
    )
    if any(row["status"] != "PASS" for row in append_only):
        raise GovernedRegistryError("registry_append_only_verification_failed")
    manifest_receipt = {
        "repository": REPOSITORY,
        "branch": BRANCH,
        "producer_commit": AUTHORITY_MANIFEST_COMMIT,
        "observed_commit": observed,
        "path": AUTHORITY_MANIFEST_PATH,
        "git_blob_sha1": git_blob_sha1(manifest_bytes),
        "byte_sha256": sha256(manifest_bytes).hexdigest(),
        "byte_length": len(manifest_bytes),
        "status": "PASS_EXACT_COMMITTED_BYTES",
    }
    return GovernedRegistrySnapshotV1(
        observed_commit=observed,
        manifest=manifest,
        registries=registries,
        receipts=tuple(receipts),
        append_only_reports=append_only,
        authority_manifest_receipt=manifest_receipt,
    )


def _minimum_label(
    labels: Sequence[str],
    ranks: Mapping[str, int],
    *,
    fallback: str,
) -> str:
    valid = [label for label in labels if label in ranks]
    if len(valid) != len(labels) or not valid:
        return fallback
    return min(valid, key=lambda label: (ranks[label], label))


def validate_evidence_binding(
    binding: Mapping[str, Any],
    *,
    authority: GovernedRegistrySnapshotV1,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if binding.get("schema_version") != EXACT_BINDING_SCHEMA:
        blockers.append("evidence_binding_schema_invalid")
    family_id = str(binding.get("source_family_id") or "")
    adapter_id = str(binding.get("adapter_id") or "")
    family = authority.source_families.get(family_id)
    adapter = authority.adapter_bindings.get(adapter_id)
    if not family or family.get("enabled") is not True:
        blockers.append("evidence_source_family_not_registered")
    if not adapter or adapter.get("enabled") is not True:
        blockers.append("evidence_adapter_not_registered")
    if adapter and adapter.get("source_family_id") != family_id:
        blockers.append("evidence_adapter_source_family_mismatch")
    if adapter and binding.get("adapter_binding_record_id") != adapter.get("record_id"):
        blockers.append("evidence_adapter_binding_record_mismatch")
    accepted_binding_id = str(binding.get("accepted_evidence_binding_id") or "")
    if family and accepted_binding_id != family.get("accepted_evidence_binding"):
        blockers.append("evidence_family_binding_id_mismatch")
    if adapter and accepted_binding_id not in (
        adapter.get("accepted_evidence_binding_ids") or []
    ):
        blockers.append("evidence_adapter_binding_id_mismatch")
    if adapter and binding.get("source_native_status") not in (
        adapter.get("accepted_source_native_statuses") or []
    ):
        blockers.append("evidence_source_native_status_not_accepted")
    if family and binding.get("evidence_state") not in (
        family.get("accepted_evidence_states") or []
    ):
        blockers.append("evidence_state_not_accepted")
    for field in (
        "binding_id",
        "evidence_ref",
        "document_id",
        "source_native_id",
        "content_sha256",
        "consumer_permission",
    ):
        if binding.get(field) in (None, ""):
            blockers.append(f"evidence_binding_{field}_missing")
    content_hash = str(binding.get("content_sha256") or "")
    if len(content_hash) != 64 or any(char not in "0123456789abcdef" for char in content_hash):
        blockers.append("evidence_binding_content_sha256_invalid")
    receipt = binding.get("receipt")
    if not isinstance(receipt, Mapping) or receipt.get("exact_verified") is not True:
        blockers.append("evidence_binding_exact_receipt_missing")
    elif receipt.get("receipt_kind") not in {
        "git_artifact",
        "dbh2_record_version",
        "accepted_aggregation",
    }:
        blockers.append("evidence_binding_receipt_kind_invalid")
    if binding.get("logical_hash") != logical_hash(without_hash(binding)):
        blockers.append("evidence_binding_logical_hash_mismatch")
    return tuple(sorted(set(blockers)))


def derive_claim_authority_permission(
    *,
    authority: GovernedRegistrySnapshotV1,
    claim_type: str,
    evidence_bindings: Sequence[Mapping[str, Any]],
    trusted_evidence_index: Mapping[str, Mapping[str, Any]],
    requested_authority: str | None = None,
    requested_permission: str | None = None,
) -> dict[str, Any]:
    capability = authority.claim_capabilities.get(claim_type)
    blockers: list[str] = []
    if not capability or capability.get("enabled") is not True:
        blockers.append("claim_capability_not_registered")
    if not evidence_bindings:
        blockers.append("claim_evidence_bindings_missing")
    for binding in evidence_bindings:
        blockers.extend(validate_evidence_binding(binding, authority=authority))
        evidence_ref = str(binding.get("evidence_ref") or "")
        trusted = trusted_evidence_index.get(evidence_ref)
        if trusted is None:
            blockers.append("evidence_binding_not_in_trusted_index")
        elif trusted.get("logical_hash") != binding.get("logical_hash"):
            blockers.append("evidence_binding_trusted_index_mismatch")
    if blockers:
        derived_authority = "UNVERIFIED"
        derived_permission = "PERMISSION_BLOCKED"
    else:
        families = [
            authority.source_families[str(binding["source_family_id"])]
            for binding in evidence_bindings
        ]
        adapters = [
            authority.adapter_bindings[str(binding["adapter_id"])]
            for binding in evidence_bindings
        ]
        derived_authority = _minimum_label(
            [
                *[str(row["authority_ceiling"]) for row in families],
                *[str(row["authority_ceiling"]) for row in adapters],
            ],
            AUTHORITY_RANK,
            fallback="UNVERIFIED",
        )
        permissions = [
            *[str(row["permission_ceiling"]) for row in families],
            *[str(row["permission_ceiling"]) for row in adapters],
            *[
                str(binding["consumer_permission"])
                for binding in evidence_bindings
            ],
        ]
        if not all(binding.get("dqr_reporting_allowed") is True for binding in evidence_bindings):
            permissions.append("CONTEXT_ONLY")
        derived_permission = _minimum_label(
            permissions,
            PERMISSION_RANK,
            fallback="PERMISSION_BLOCKED",
        )
    if requested_authority is not None:
        if AUTHORITY_RANK.get(requested_authority, -1) > AUTHORITY_RANK.get(
            derived_authority, -1
        ):
            blockers.append("caller_authority_upgrade_rejected")
        else:
            derived_authority = requested_authority
    if requested_permission is not None:
        if PERMISSION_RANK.get(requested_permission, -1) > PERMISSION_RANK.get(
            derived_permission, -1
        ):
            blockers.append("caller_permission_upgrade_rejected")
        else:
            derived_permission = requested_permission
    decision = {
        "schema_version": "contentops.claim_authority_permission_derivation.v1",
        "claim_type": claim_type,
        "claim_capability_record_id": (
            capability.get("record_id") if capability else None
        ),
        "evidence_binding_ids": sorted(
            str(binding.get("binding_id") or "") for binding in evidence_bindings
        ),
        "derived_authority_class": derived_authority,
        "derived_permission_state": derived_permission,
        "blockers": sorted(set(blockers)),
        "authority_granted": not blockers,
    }
    decision["logical_hash"] = logical_hash(decision)
    return decision


def validate_market_evidence_record(
    record: Mapping[str, Any],
    *,
    authority: GovernedRegistrySnapshotV1,
    claim_evidence_refs: Sequence[str],
    event_evidence_refs: Sequence[str],
) -> tuple[str, ...]:
    blockers: list[str] = []
    capability = authority.market_capabilities.get("separate_market_observation")
    if not capability or capability.get("enabled") is not True:
        blockers.append("market_evidence_capability_not_registered")
        return tuple(blockers)
    if record.get("schema_version") != MARKET_BINDING_SCHEMA:
        blockers.append("market_evidence_schema_invalid")
    for field in capability.get("required_fields") or []:
        if record.get(field) in (None, "", []):
            blockers.append(f"market_evidence_{field}_missing")
    if record.get("evidence_classification") not in (
        capability.get("accepted_classifications") or []
    ):
        blockers.append("market_evidence_classification_invalid")
    refs = set(record.get("evidence_refs") or [])
    if not refs.issubset(set(claim_evidence_refs)):
        blockers.append("market_evidence_not_in_claim_lineage")
    if refs.intersection(event_evidence_refs):
        blockers.append("market_evidence_reuses_event_evidence")
    adapter = authority.adapter_bindings.get(str(record.get("adapter_id") or ""))
    family = authority.source_families.get(
        str(record.get("source_family_id") or "")
    )
    if not family or family.get("enabled") is not True:
        blockers.append("market_evidence_source_family_not_registered")
    if not adapter:
        blockers.append("market_evidence_adapter_not_registered")
    elif record.get("adapter_binding_record_id") != adapter.get("record_id"):
        blockers.append("market_evidence_adapter_binding_mismatch")
    elif adapter.get("source_family_id") != record.get("source_family_id"):
        blockers.append("market_evidence_adapter_source_family_mismatch")
    if record.get("logical_hash") != logical_hash(without_hash(record)):
        blockers.append("market_evidence_logical_hash_mismatch")
    return tuple(sorted(set(blockers)))


def validate_claim_document_lineage(
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    documents = candidate.get("source_documents") or []
    document_ids = [str(row.get("document_id") or "") for row in documents]
    if len(document_ids) != len(set(document_ids)):
        blockers.append("candidate_source_document_duplicate")
    document_by_id = {
        str(row.get("document_id")): row
        for row in documents
        if row.get("document_id")
    }
    bindings = candidate.get("evidence_bindings") or []
    binding_refs = [str(row.get("evidence_ref") or "") for row in bindings]
    if len(binding_refs) != len(set(binding_refs)):
        blockers.append("candidate_evidence_binding_ref_duplicate")
    binding_by_ref = {
        str(row.get("evidence_ref")): row
        for row in bindings
        if row.get("evidence_ref")
    }
    consumed_documents: set[str] = set()
    consumed_refs: set[str] = set()
    claim_reports: list[dict[str, Any]] = []
    for claim in candidate.get("claims") or []:
        claim_id = str(claim.get("claim_id") or "unknown")
        claim_document_ids = set(claim.get("source_document_ids") or [])
        claim_refs = set(claim.get("evidence_refs") or [])
        claim_blockers: list[str] = []
        for document_id in claim_document_ids:
            if document_id not in document_by_id:
                claim_blockers.append("claim_source_document_missing")
            else:
                consumed_documents.add(document_id)
        for citation in claim.get("citations") or []:
            document_id = str(citation.get("source_document_id") or "")
            if document_id not in claim_document_ids:
                claim_blockers.append("citation_document_not_bound_to_claim")
                continue
            document = document_by_id.get(document_id)
            if document is None:
                claim_blockers.append("citation_document_missing")
                continue
            authorized_urls = set(document.get("authorized_urls") or [])
            if citation.get("url") not in authorized_urls:
                claim_blockers.append("citation_url_not_authorized_for_document")
        for evidence_ref in claim_refs:
            binding = binding_by_ref.get(evidence_ref)
            if binding is None:
                claim_blockers.append("claim_evidence_ref_unresolved")
                continue
            consumed_refs.add(evidence_ref)
            document_id = str(binding.get("document_id") or "")
            if document_id not in claim_document_ids:
                claim_blockers.append("claim_evidence_document_mismatch")
                continue
            document = document_by_id.get(document_id) or {}
            if binding.get("content_sha256") != document.get("content_sha256"):
                claim_blockers.append("claim_evidence_content_sha_mismatch")
            if binding.get("source_native_id") != document.get("source_native_id"):
                claim_blockers.append("claim_evidence_source_native_id_mismatch")
        blockers.extend(f"{claim_id}:{value}" for value in claim_blockers)
        claim_reports.append({
            "claim_id": claim_id,
            "document_ids": sorted(claim_document_ids),
            "evidence_refs": sorted(claim_refs),
            "blockers": sorted(set(claim_blockers)),
        })
    candidate_refs = set(candidate.get("evidence_refs") or [])
    claim_union = {
        str(ref)
        for claim in candidate.get("claims") or []
        for ref in claim.get("evidence_refs") or []
    }
    if candidate_refs != claim_union:
        blockers.append("candidate_evidence_refs_not_exact_claim_union")
    unused_documents = sorted(set(document_by_id) - consumed_documents)
    unconsumed_bindings = sorted(set(binding_by_ref) - consumed_refs)
    if unconsumed_bindings:
        blockers.append("unconsumed_authority_evidence_binding")
    report = {
        "schema_version": "contentops.claim_document_citation_lineage_report.v1",
        "candidate_id": candidate.get("candidate_id"),
        "claim_reports": claim_reports,
        "unused_document_ids": unused_documents,
        "unconsumed_authority_evidence_refs": unconsumed_bindings,
        "blockers": sorted(set(blockers)),
        "status": "PASS" if not blockers else "FAIL",
    }
    report["logical_hash"] = logical_hash(report)
    return report


def validate_profile_execution(
    candidate: Mapping[str, Any],
    *,
    authority: GovernedRegistrySnapshotV1,
) -> dict[str, Any]:
    blockers: list[str] = []
    profile_id = str(candidate.get("evidence_requirement_profile_id") or "")
    profile = authority.evidence_profiles.get(profile_id)
    if not profile or profile.get("enabled") is not True:
        blockers.append("evidence_profile_not_registered")
        accepted_types: set[str] = set()
    else:
        accepted_types = set(profile.get("accepted_claim_types") or [])
    present_types = {
        str(claim.get("claim_type") or "")
        for claim in candidate.get("claims") or []
    }
    declared_capabilities = set(
        (candidate.get("capabilities") or {}).get("claim_capabilities") or []
    )
    if present_types != declared_capabilities:
        blockers.append("candidate_capability_claim_type_mismatch")
    if profile:
        required_capabilities = set(profile.get("required_capabilities") or [])
        if not present_types.intersection(accepted_types):
            blockers.append("profile_accepted_capability_missing")
        extra_types = present_types - accepted_types
        composition_id = None
        if extra_types:
            for contract in (
                authority.registries["evidence_profiles"].get(
                    "composition_contracts"
                )
                or []
            ):
                if (
                    contract.get("enabled") is True
                    and profile_id in (contract.get("base_profile_ids") or [])
                    and extra_types.issubset(
                        set(contract.get("additional_claim_types") or [])
                    )
                ):
                    composition_id = contract["contract_id"]
                    break
            if composition_id is None:
                blockers.append("profile_unsupported_extra_claim_type")
        for field in profile.get("required_candidate_fields") or []:
            if candidate.get(field) in (None, "", []):
                blockers.append(f"profile_candidate_field_missing:{field}")
        for claim in candidate.get("claims") or []:
            for field in profile.get("required_claim_fields") or []:
                if claim.get(field) in (None, "", []):
                    blockers.append(
                        f"profile_claim_field_missing:{claim.get('claim_id')}:{field}"
                    )
        if profile.get("numeric_claim_required") is True and (
            "numeric_observation" not in present_types
        ):
            blockers.append("profile_numeric_claim_required")
    else:
        composition_id = None
    unknown_claim_types = present_types - set(authority.claim_capabilities)
    if unknown_claim_types:
        blockers.append("profile_unknown_claim_capability")
    report = {
        "schema_version": "contentops.evidence_profile_execution.v1",
        "candidate_id": candidate.get("candidate_id"),
        "profile_id": profile_id,
        "present_claim_types": sorted(present_types),
        "declared_capabilities": sorted(declared_capabilities),
        "composition_contract_id": composition_id,
        "blockers": sorted(set(blockers)),
        "status": "PASS" if not blockers else "FAIL",
    }
    report["logical_hash"] = logical_hash(report)
    return report


def validate_pool_cross_candidate_lineage(
    candidates: Sequence[Mapping[str, Any]],
) -> tuple[str, ...]:
    owner_by_ref: dict[str, str] = {}
    blockers: list[str] = []
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id") or "unknown")
        for ref in candidate.get("evidence_refs") or []:
            previous = owner_by_ref.get(str(ref))
            if previous is not None and previous != candidate_id:
                blockers.append(
                    f"cross_candidate_evidence_ref_reuse:{ref}:{previous}:{candidate_id}"
                )
            owner_by_ref[str(ref)] = candidate_id
    return tuple(sorted(set(blockers)))


def build_exact_evidence_binding(
    *,
    binding_id: str,
    accepted_evidence_binding_id: str,
    evidence_ref: str,
    source_family_id: str,
    adapter_id: str,
    adapter_binding_record_id: str,
    document_id: str,
    source_native_id: str,
    content_sha256: str,
    source_native_status: str,
    evidence_state: str,
    consumer_permission: str,
    dqr_reporting_allowed: bool,
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    value = {
        "schema_version": EXACT_BINDING_SCHEMA,
        "binding_id": binding_id,
        "accepted_evidence_binding_id": accepted_evidence_binding_id,
        "evidence_ref": evidence_ref,
        "source_family_id": source_family_id,
        "adapter_id": adapter_id,
        "adapter_binding_record_id": adapter_binding_record_id,
        "document_id": document_id,
        "source_native_id": source_native_id,
        "content_sha256": content_sha256,
        "source_native_status": source_native_status,
        "evidence_state": evidence_state,
        "consumer_permission": consumer_permission,
        "dqr_reporting_allowed": dqr_reporting_allowed,
        "receipt": dict(receipt),
    }
    value["logical_hash"] = logical_hash(value)
    return value


def build_governed_claim(
    *,
    authority: GovernedRegistrySnapshotV1,
    trusted_evidence_index: Mapping[str, Mapping[str, Any]],
    claim_id: str,
    claim_type: str,
    evidence_refs: Sequence[str],
    requested_authority: str | None = None,
    requested_permission: str | None = None,
    **claim_values: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    bindings: list[Mapping[str, Any]] = []
    for evidence_ref in evidence_refs:
        binding = trusted_evidence_index.get(str(evidence_ref))
        if binding is None:
            raise GovernedRegistryError(
                f"claim_evidence_not_trusted:{evidence_ref}"
            )
        bindings.append(binding)
    decision = derive_claim_authority_permission(
        authority=authority,
        claim_type=claim_type,
        evidence_bindings=bindings,
        trusted_evidence_index=trusted_evidence_index,
        requested_authority=requested_authority,
        requested_permission=requested_permission,
    )
    decision = {
        **without_hash(decision),
        "claim_id": claim_id,
    }
    decision["logical_hash"] = logical_hash(decision)
    if decision["blockers"]:
        raise GovernedRegistryError(
            "claim_authority_derivation_blocked:" + ",".join(decision["blockers"])
        )
    from live_contentops.universal_news_candidate_fabric_v2 import (
        _build_claim_unchecked,
    )

    claim = _build_claim_unchecked(
        claim_id=claim_id,
        claim_type=claim_type,
        evidence_refs=evidence_refs,
        authority_class=decision["derived_authority_class"],
        permission_state=decision["derived_permission_state"],
        **claim_values,
    )
    return claim, decision


def _authority_label_from_claims(
    claims: Sequence[Mapping[str, Any]],
) -> str:
    labels = [str(claim.get("authority_class") or "") for claim in claims]
    return _minimum_label(labels, AUTHORITY_RANK, fallback="UNVERIFIED")


def _reporting_from_claims(
    claims: Sequence[Mapping[str, Any]],
) -> bool:
    return bool(claims) and all(
        claim.get("permission_state") in {
            "REPORTING_ALLOWED",
            "PUBLIC_CLAIM_ALLOWED",
        }
        for claim in claims
    )


def validate_governed_candidate(
    candidate: Mapping[str, Any],
    *,
    authority: GovernedRegistrySnapshotV1,
    trusted_evidence_index: Mapping[str, Mapping[str, Any]],
    cutoff_utc: str,
) -> dict[str, Any]:
    from live_contentops.universal_news_candidate_fabric_v2 import (
        validate_candidate,
    )

    source_family_lookup = {
        source_family_id: {
            **dict(record),
            "authority_class": record["authority_ceiling"],
        }
        for source_family_id, record in authority.source_families.items()
    }
    blockers = list(validate_candidate(
        candidate,
        cutoff_utc=cutoff_utc,
        source_family_registry=source_family_lookup,
    ))
    profile_report = validate_profile_execution(candidate, authority=authority)
    blockers.extend(profile_report["blockers"])
    lineage_report = validate_claim_document_lineage(candidate)
    blockers.extend(lineage_report["blockers"])

    candidate_bindings = {
        str(row.get("evidence_ref")): row
        for row in candidate.get("evidence_bindings") or []
        if row.get("evidence_ref")
    }
    for evidence_ref, binding in candidate_bindings.items():
        trusted = trusted_evidence_index.get(evidence_ref)
        if trusted is None:
            blockers.append(f"candidate_evidence_not_trusted:{evidence_ref}")
        elif trusted.get("logical_hash") != binding.get("logical_hash"):
            blockers.append(
                f"candidate_evidence_trusted_index_mismatch:{evidence_ref}"
            )
        blockers.extend(validate_evidence_binding(binding, authority=authority))

    decisions_by_claim = {
        str(row.get("claim_id")): row
        for row in candidate.get("claim_authority_decisions") or []
        if row.get("claim_id")
    }
    if len(decisions_by_claim) != len(candidate.get("claims") or []):
        blockers.append("claim_authority_decision_set_incomplete")
    for claim in candidate.get("claims") or []:
        claim_id = str(claim.get("claim_id") or "")
        decision = decisions_by_claim.get(claim_id)
        if not decision:
            blockers.append(f"claim_authority_decision_missing:{claim_id}")
            continue
        if decision.get("logical_hash") != logical_hash(without_hash(decision)):
            blockers.append(f"claim_authority_decision_hash_invalid:{claim_id}")
            continue
        bindings = [
            candidate_bindings[ref]
            for ref in claim.get("evidence_refs") or []
            if ref in candidate_bindings
        ]
        expected = derive_claim_authority_permission(
            authority=authority,
            claim_type=str(claim.get("claim_type") or ""),
            evidence_bindings=bindings,
            trusted_evidence_index=trusted_evidence_index,
            requested_authority=str(claim.get("authority_class") or ""),
            requested_permission=str(claim.get("permission_state") or ""),
        )
        if expected["blockers"]:
            blockers.extend(
                f"{claim_id}:{value}" for value in expected["blockers"]
            )
        if (
            decision.get("derived_authority_class")
            != claim.get("authority_class")
            or decision.get("derived_permission_state")
            != claim.get("permission_state")
            or set(decision.get("evidence_binding_ids") or [])
            != {str(row.get("binding_id") or "") for row in bindings}
        ):
            blockers.append(f"claim_authority_decision_output_mismatch:{claim_id}")

    expected_authority = _authority_label_from_claims(
        candidate.get("claims") or []
    )
    expected_reporting = _reporting_from_claims(candidate.get("claims") or [])
    if candidate.get("authority_state") != expected_authority:
        blockers.append("candidate_authority_not_derived_from_claims")
    if candidate.get("reporting_allowed") is not expected_reporting:
        blockers.append("candidate_reporting_not_derived_from_claims")

    market_records = {
        str(row.get("market_evidence_id")): row
        for row in candidate.get("market_evidence_records") or []
        if row.get("market_evidence_id")
    }
    for claim in candidate.get("claims") or []:
        if claim.get("claim_type") != "market_reaction":
            continue
        market_refs = claim.get("market_evidence_refs") or []
        for market_id in market_refs:
            market_record = market_records.get(str(market_id))
            if market_record is None:
                blockers.append(
                    f"{claim.get('claim_id')}:market_evidence_record_missing"
                )
                continue
            blockers.extend(
                f"{claim.get('claim_id')}:{value}"
                for value in validate_market_evidence_record(
                    market_record,
                    authority=authority,
                    claim_evidence_refs=claim.get("evidence_refs") or [],
                    event_evidence_refs=candidate.get("event_evidence_refs") or [],
                )
            )
    report = {
        "schema_version": "contentops.governed_candidate_validation.v1",
        "candidate_id": candidate.get("candidate_id"),
        "profile_execution": profile_report,
        "lineage": lineage_report,
        "derived_candidate_authority": expected_authority,
        "derived_reporting_allowed": expected_reporting,
        "blockers": sorted(set(blockers)),
        "status": "PASS" if not blockers else "FAIL",
    }
    report["logical_hash"] = logical_hash(report)
    return report


def build_governed_pool(
    *,
    authority: GovernedRegistrySnapshotV1,
    trusted_evidence_index: Mapping[str, Mapping[str, Any]],
    candidates: Sequence[Mapping[str, Any]],
    source_family_ids: Sequence[str],
    generated_at_utc: str,
    cutoff_time_utc: str,
    upstream_binding: Mapping[str, Any],
    category_blockers: Mapping[str, str],
) -> dict[str, Any]:
    from live_contentops.universal_news_candidate_fabric_v2 import (
        _build_pool_unchecked,
    )

    family_records: list[Mapping[str, Any]] = []
    for source_family_id in sorted(set(source_family_ids)):
        record = authority.source_families.get(source_family_id)
        if not record or record.get("enabled") is not True:
            raise GovernedRegistryError(
                f"governed_source_family_not_registered:{source_family_id}"
            )
        family_records.append({
            **dict(record),
            "authority_class": record["authority_ceiling"],
        })
    validation_reports = [
        validate_governed_candidate(
            candidate,
            authority=authority,
            trusted_evidence_index=trusted_evidence_index,
            cutoff_utc=cutoff_time_utc,
        )
        for candidate in candidates
    ]
    if any(report["status"] != "PASS" for report in validation_reports):
        blockers = [
            blocker
            for report in validation_reports
            for blocker in report["blockers"]
        ]
        raise GovernedRegistryError(
            "governed_candidate_pool_invalid:" + ",".join(sorted(set(blockers)))
        )
    cross_candidate = validate_pool_cross_candidate_lineage(candidates)
    if cross_candidate:
        raise GovernedRegistryError(",".join(cross_candidate))
    pool = _build_pool_unchecked(
        candidates=candidates,
        source_family_records=family_records,
        generated_at_utc=generated_at_utc,
        cutoff_time_utc=cutoff_time_utc,
        upstream_binding={
            **dict(upstream_binding),
            "governed_registry_authority": authority.authority_packet(),
        },
        category_blockers=category_blockers,
    )
    pool["governed_candidate_validation"] = validation_reports
    consumed_refs = sorted({
        str(ref)
        for candidate in candidates
        for ref in candidate.get("evidence_refs") or []
    })
    pool["trusted_evidence_index_hash"] = logical_hash({
        ref: trusted_evidence_index[ref].get("logical_hash")
        for ref in consumed_refs
    })
    pool["logical_hash"] = logical_hash(without_hash(pool))
    return pool


def validate_governed_pool(
    pool: Mapping[str, Any],
    *,
    authority: GovernedRegistrySnapshotV1,
    trusted_evidence_index: Mapping[str, Mapping[str, Any]],
) -> tuple[str, ...]:
    from live_contentops.universal_news_candidate_fabric_v2 import validate_pool

    blockers = list(validate_pool(pool))
    packet = (pool.get("upstream_binding") or {}).get(
        "governed_registry_authority"
    )
    if not isinstance(packet, Mapping):
        blockers.append("pool_governed_registry_authority_missing")
    elif packet.get("logical_hash") != authority.authority_packet()["logical_hash"]:
        blockers.append("pool_governed_registry_authority_mismatch")
    consumed_refs = sorted({
        str(ref)
        for candidate in pool.get("candidates") or []
        for ref in candidate.get("evidence_refs") or []
    })
    missing_refs = [
        ref for ref in consumed_refs if ref not in trusted_evidence_index
    ]
    if missing_refs:
        blockers.extend(
            f"pool_trusted_evidence_ref_missing:{ref}" for ref in missing_refs
        )
    expected_index_hash = logical_hash({
        ref: trusted_evidence_index[ref].get("logical_hash")
        for ref in consumed_refs
        if ref in trusted_evidence_index
    })
    if pool.get("trusted_evidence_index_hash") != expected_index_hash:
        blockers.append("pool_trusted_evidence_index_hash_mismatch")
    for candidate in pool.get("candidates") or []:
        report = validate_governed_candidate(
            candidate,
            authority=authority,
            trusted_evidence_index=trusted_evidence_index,
            cutoff_utc=str(pool.get("cutoff_time_utc") or ""),
        )
        blockers.extend(report["blockers"])
    blockers.extend(validate_pool_cross_candidate_lineage(
        pool.get("candidates") or []
    ))
    return tuple(sorted(set(blockers)))
