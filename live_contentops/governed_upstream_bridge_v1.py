"""Deterministic, read-only bridge for governed upstream database artifacts."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1, sha256
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence


EXPECTED_REPOSITORY = "fatcat2109/Headline-Raw-data-json"
EXPECTED_BRANCH = "main"
BLOCKED_LOCAL_ARTIFACT = "BLOCKED_LOCAL_GOVERNED_DBH2_ARTIFACT_MISSING_OR_HASH_MISMATCH"
DBH2_STORAGE_MANIFEST = (
    "docs/research/database_foundation/public_free_event_text_entity_history_v1/"
    "DBH2_STORAGE_MANIFEST_V1.json"
)
DBH2_TARGET_CATALOG = "config/data_foundation/PUBLIC_FREE_EVENT_TEXT_ENTITY_HISTORY_TARGET_CATALOG_V1.json"
DBH2_FINAL_REPORT = (
    "docs/research/database_foundation/public_free_event_text_entity_history_v1/"
    "DBH2_FINAL_REPORT_V1.md"
)
DBH2_LEDGER = (
    "docs/research/database_foundation/public_free_event_text_entity_history_v1/"
    "DBH2_DOCUMENT_EVENT_ENTITY_REVISION_LEDGER_V1.json"
)
V1_POOL_PATH = "docs/research/newsroom_candidate_pool_v1/CapitalChronicleNewsroomCandidatePoolV1.json"
V1_SCHEMA_PATH = "schemas/publication/CapitalChronicleNewsroomCandidatePoolV1.schema.json"


class GovernedArtifactBlocked(RuntimeError):
    """Raised when exact governed bytes are absent or do not match authority."""


@dataclass(frozen=True)
class GitArtifactReceipt:
    repository: str
    branch: str
    observed_head: str
    producer_commit: str
    artifact_path: str
    git_blob_sha1: str
    byte_sha256: str
    byte_length: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "branch": self.branch,
            "observed_head": self.observed_head,
            "producer_commit": self.producer_commit,
            "artifact_path": self.artifact_path,
            "git_blob_sha1": self.git_blob_sha1,
            "byte_sha256": self.byte_sha256,
            "byte_length": self.byte_length,
        }


@dataclass(frozen=True)
class LocalArtifactReceipt:
    artifact_kind: str
    relative_path: str
    expected_sha256: str
    observed_sha256: str
    byte_length: int
    status: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "artifact_kind": self.artifact_kind,
            "relative_path": self.relative_path,
            "expected_sha256": self.expected_sha256,
            "observed_sha256": self.observed_sha256,
            "byte_length": self.byte_length,
            "status": self.status,
        }


def _run_git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(root), *args],
        stderr=subprocess.DEVNULL,
    )


def resolve_observed_head(root: Path, branch: str = EXPECTED_BRANCH) -> str:
    return _run_git(root, "rev-parse", f"refs/remotes/origin/{branch}").decode().strip()


def is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, descendant],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def read_git_artifact(
    *,
    root: Path,
    observed_head: str,
    artifact_path: str,
    producer_commit: str | None = None,
) -> tuple[bytes, GitArtifactReceipt]:
    producer_commit = producer_commit or observed_head
    if not is_ancestor(root, producer_commit, observed_head):
        raise GovernedArtifactBlocked("producer_commit_not_reachable_from_observed_head")
    try:
        content = _run_git(root, "show", f"{producer_commit}:{artifact_path}")
        blob = _run_git(root, "rev-parse", f"{producer_commit}:{artifact_path}").decode().strip()
    except subprocess.CalledProcessError as error:
        raise GovernedArtifactBlocked(f"governed_git_artifact_missing:{artifact_path}") from error
    receipt = GitArtifactReceipt(
        repository=EXPECTED_REPOSITORY,
        branch=EXPECTED_BRANCH,
        observed_head=observed_head,
        producer_commit=producer_commit,
        artifact_path=artifact_path,
        git_blob_sha1=blob,
        byte_sha256=sha256(content).hexdigest(),
        byte_length=len(content),
    )
    return content, receipt


def read_git_json(
    *,
    root: Path,
    observed_head: str,
    artifact_path: str,
    producer_commit: str | None = None,
) -> tuple[dict[str, Any], GitArtifactReceipt]:
    content, receipt = read_git_artifact(
        root=root,
        observed_head=observed_head,
        artifact_path=artifact_path,
        producer_commit=producer_commit,
    )
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as error:
        raise GovernedArtifactBlocked(f"governed_git_json_malformed:{artifact_path}") from error
    if not isinstance(parsed, dict):
        raise GovernedArtifactBlocked(f"governed_git_json_root_invalid:{artifact_path}")
    return parsed, receipt


def hash_local_file(path: Path) -> tuple[str, int]:
    digest = sha256()
    size = 0
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
                size += len(chunk)
    except OSError as error:
        raise GovernedArtifactBlocked(BLOCKED_LOCAL_ARTIFACT) from error
    return digest.hexdigest(), size


def verify_local_artifact(
    *,
    root: Path,
    relative_path: str,
    expected_sha256: str,
    artifact_kind: str,
) -> LocalArtifactReceipt:
    path = root / relative_path
    if not path.is_file():
        raise GovernedArtifactBlocked(BLOCKED_LOCAL_ARTIFACT)
    observed, length = hash_local_file(path)
    if observed != expected_sha256:
        raise GovernedArtifactBlocked(BLOCKED_LOCAL_ARTIFACT)
    return LocalArtifactReceipt(
        artifact_kind=artifact_kind,
        relative_path=relative_path,
        expected_sha256=expected_sha256,
        observed_sha256=observed,
        byte_length=length,
        status="PASS_EXACT_SHA256",
    )


class GovernedUpstreamBridgeV1:
    """Verify manifest authority before opening exact local database bytes."""

    def __init__(
        self,
        *,
        root: Path,
        observed_head: str,
        branch: str = EXPECTED_BRANCH,
    ) -> None:
        self.root = root.resolve()
        self.observed_head = observed_head
        self.branch = branch
        actual = resolve_observed_head(self.root, branch)
        if actual != observed_head and not is_ancestor(
            self.root, observed_head, actual
        ):
            raise GovernedArtifactBlocked("observed_branch_head_not_reachable")
        self.current_branch_head = actual
        self._manifest: dict[str, Any] | None = None
        self._manifest_receipt: GitArtifactReceipt | None = None
        self._local_receipts: list[LocalArtifactReceipt] = []

    def load_manifest(self) -> Mapping[str, Any]:
        if self._manifest is None:
            manifest, receipt = read_git_json(
                root=self.root,
                observed_head=self.observed_head,
                artifact_path=DBH2_STORAGE_MANIFEST,
            )
            if manifest.get("binaries_committed") is not False:
                raise GovernedArtifactBlocked("dbh2_binary_commit_boundary_invalid")
            if not manifest.get("duckdb_ref") or not manifest.get("duckdb_sha256"):
                raise GovernedArtifactBlocked("dbh2_manifest_duckdb_binding_missing")
            producer_commit = (
                (manifest.get("repair_provenance") or {}).get(
                    "repaired_live_evidence_head"
                )
            )
            if not producer_commit or not is_ancestor(
                self.root, str(producer_commit), self.observed_head
            ):
                raise GovernedArtifactBlocked(
                    "dbh2_artifact_producer_commit_not_reachable"
                )
            self._manifest = manifest
            self._manifest_receipt = receipt
        return self._manifest

    def verify_all_local_artifacts(self) -> tuple[LocalArtifactReceipt, ...]:
        manifest = self.load_manifest()
        receipts = [
            verify_local_artifact(
                root=self.root,
                relative_path=str(manifest["duckdb_ref"]),
                expected_sha256=str(manifest["duckdb_sha256"]),
                artifact_kind="duckdb",
            )
        ]
        for row in manifest.get("parquet_partitions") or []:
            receipts.append(verify_local_artifact(
                root=self.root,
                relative_path=str(row["ref"]),
                expected_sha256=str(row["sha256"]),
                artifact_kind=f"parquet:{row['target_id']}",
            ))
        self._local_receipts = receipts
        return tuple(receipts)

    def open_duckdb(self):
        import duckdb

        manifest = self.load_manifest()
        if not self._local_receipts:
            self.verify_all_local_artifacts()
        path = self.root / str(manifest["duckdb_ref"])
        return duckdb.connect(str(path), read_only=True)

    def target_catalog(self) -> tuple[dict[str, Any], GitArtifactReceipt]:
        return read_git_json(
            root=self.root,
            observed_head=self.observed_head,
            artifact_path=DBH2_TARGET_CATALOG,
        )

    def select_record(
        self,
        *,
        target_id: str,
        provider_record_type: str,
        cutoff_utc: str,
        order: str = "latest",
        required_status: str | None = None,
    ) -> dict[str, Any]:
        from live_contentops.universal_news_candidate_fabric_v2 import parse_utc

        cutoff = parse_utc(cutoff_utc, field_name="cutoff_utc")
        connection = self.open_duckdb()
        try:
            rows = connection.execute(
                """
                SELECT record_id, stable_record_id, target_id, provider,
                       provider_record_type, provider_record_id, candidate_only,
                       current_canonical_apply, exact_authority, numeric_boundary,
                       version_id, updated_at, published_at, content_sha256,
                       title, status, canonical_url, payload_json
                  FROM dbh2_records
                 WHERE target_id = ? AND provider_record_type = ?
                """,
                [target_id, provider_record_type],
            ).fetchall()
            columns = [row[0] for row in connection.description]
        finally:
            connection.close()
        candidates = []
        for raw in rows:
            row = dict(zip(columns, raw))
            if required_status is not None and row.get("status") != required_status:
                continue
            known_text = row.get("updated_at") or row.get("published_at")
            if not known_text:
                continue
            known = parse_utc(
                str(known_text) if "T" in str(known_text) else f"{known_text}T00:00:00Z",
                field_name="record_known_at_utc",
            )
            if known > cutoff:
                continue
            row["known_at_utc"] = known.isoformat().replace("+00:00", "Z")
            published = row.get("published_at")
            if published and "T" not in str(published):
                row["published_at_utc"] = f"{published}T00:00:00Z"
            else:
                row["published_at_utc"] = published
            row["payload"] = json.loads(row.pop("payload_json") or "{}")
            candidates.append(row)
        if not candidates:
            raise GovernedArtifactBlocked(f"governed_record_unavailable:{target_id}")
        candidates.sort(key=lambda row: (
            str(row.get("known_at_utc") or ""),
            str(row.get("provider_record_id") or ""),
            str(row.get("version_id") or ""),
        ), reverse=order == "latest")
        return candidates[0]

    def select_snapshot_entity(
        self,
        *,
        cutoff_utc: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        snapshot = self.select_record(
            target_id="DBH2_OFAC_SDN_CURRENT_SNAPSHOT",
            provider_record_type="ofac_snapshot",
            cutoff_utc=cutoff_utc,
            required_status="snapshot",
        )
        connection = self.open_duckdb()
        try:
            raw = connection.execute(
                """
                SELECT record_id, stable_record_id, target_id, provider,
                       provider_record_type, provider_record_id, candidate_only,
                       current_canonical_apply, exact_authority, numeric_boundary,
                       version_id, updated_at, published_at, content_sha256,
                       title, status, canonical_url, payload_json
                  FROM dbh2_records
                 WHERE target_id = 'DBH2_OFAC_SDN_CURRENT_SNAPSHOT'
                   AND provider_record_type = 'ofac_sdn_entity'
                   AND status = 'listed'
                 ORDER BY provider_record_id, stable_record_id
                 LIMIT 1
                """
            ).fetchone()
            columns = [row[0] for row in connection.description]
        finally:
            connection.close()
        if raw is None:
            raise GovernedArtifactBlocked("governed_ofac_snapshot_entity_missing")
        entity = dict(zip(columns, raw))
        entity["payload"] = json.loads(entity.pop("payload_json") or "{}")
        entity["known_at_utc"] = snapshot["known_at_utc"]
        entity["published_at_utc"] = snapshot["published_at_utc"]
        return snapshot, entity

    def relationships_for_record(
        self,
        *,
        stable_record_id: str,
        counterpart_stable_record_id: str | None = None,
        maximum_relationships: int = 100,
    ) -> list[dict[str, Any]]:
        connection = self.open_duckdb()
        try:
            query = """
                SELECT relationship_id, target_id, relation_type,
                       from_stable_record_id, to_stable_record_id,
                       from_version_id, to_version_id, evidence
                  FROM dbh2_revision_relationships
                 WHERE (from_stable_record_id = ? OR to_stable_record_id = ?)
            """
            parameters: list[Any] = [stable_record_id, stable_record_id]
            if counterpart_stable_record_id is not None:
                query += """
                   AND (from_stable_record_id = ? OR to_stable_record_id = ?)
                """
                parameters.extend([
                    counterpart_stable_record_id,
                    counterpart_stable_record_id,
                ])
            query += " ORDER BY relationship_id"
            rows = connection.execute(query, parameters).fetchall()
            columns = [row[0] for row in connection.description]
        finally:
            connection.close()
        if len(rows) > maximum_relationships:
            raise GovernedArtifactBlocked("governed_relationship_bound_exceeded")
        return [dict(zip(columns, row)) for row in rows]

    def authority_packet(self) -> dict[str, Any]:
        manifest = self.load_manifest()
        catalog, catalog_receipt = self.target_catalog()
        if not self._local_receipts:
            self.verify_all_local_artifacts()
        return {
            "schema_version": "contentops.governed_upstream_bridge_receipt.v1",
            "repository": EXPECTED_REPOSITORY,
            "branch": self.branch,
            "observed_head": self.observed_head,
            "later_observed_branch_head": self.current_branch_head,
            "observed_head_reachable_from_later_branch_head": True,
            "manifest_receipt": self._manifest_receipt.as_dict() if self._manifest_receipt else None,
            "target_catalog_receipt": catalog_receipt.as_dict(),
            "manifest_logical_hash": manifest.get("logical_hash"),
            "artifact_producer_commit": (
                (manifest.get("repair_provenance") or {}).get(
                    "repaired_live_evidence_head"
                )
            ),
            "artifact_producer_commit_reachable_from_observed_head": True,
            "target_catalog_schema_version": catalog.get("schema_version"),
            "target_catalog_exact_authority": catalog.get("exact_authority"),
            "local_artifacts": [row.as_dict() for row in self._local_receipts],
            "local_artifact_status": "PASS_ALL_EXACT_SHA256",
            "read_only": True,
            "upstream_write_performed": False,
        }


def git_blob_sha1(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode()
    return sha1(header + content).hexdigest()
