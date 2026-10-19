"""Read Main's public file outbox through one explicitly configured export root.

Main owns the manifest wire. This adapter validates immutable bytes and history;
it does not enumerate arbitrary paths, read private reports, or mutate Main.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Mapping

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    LatestReportConsumerError,
    _load,
    _private,
    _time,
    sha256_of,
)

CONFIG_SCHEMA = "contentops.main_public_export_binding.v1"
MANIFEST_SCHEMA = "CapitalChroniclePublicReportExportManifestV1"
REPOSITORY = "https://github.com/fatcat2109/Headline-Raw-data-json"
PATH = re.compile(
    r"(?:manifests/[a-f0-9]{64}\.json|outbox/[a-f0-9]{64}/(?:latest-report-envelope|public-report|withdrawal)\.json|schemas/1\.[01]\.0/envelope\.json)"
)
MANIFEST_SCHEMAS = {
    "1.0.0": ("CapitalChroniclePublicReportExportManifestV1.schema.json",
              "a37ae594346a2b3a436bef0b1e89629767a01626ec9223a6958e2d000b4ccbc1"),
    "1.1.0": ("main_public_manifest/v1.1/CapitalChroniclePublicReportExportManifestV1.schema.json",
              "bcc960b58953980de704e52b58f43611e52d6a6a83d73d0b65663ec60ac0f954"),
}


class ManifestHistoryPending(LatestReportConsumerError):
    def __init__(self, checkpoint):
        super().__init__("MAIN_PUBLIC_MANIFEST_HISTORY_CONTINUATION_REQUIRED")
        self.checkpoint = checkpoint


def _schema(version):
    if version not in MANIFEST_SCHEMAS:
        raise LatestReportConsumerError("MAIN_PUBLIC_MANIFEST_VERSION_UNSUPPORTED")
    path, digest = MANIFEST_SCHEMAS[version]
    raw = (Path(__file__).resolve().parents[1] / "schemas" / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise LatestReportConsumerError("MAIN_PUBLIC_MANIFEST_SCHEMA_BYTES_CHANGED")
    return _load(raw)


class PublicMainFileSource:
    def __init__(self, pointer: Mapping[str, Any]):
        root = Path(pointer["public_export_root"])
        if (
            pointer.get("schema_version") != CONFIG_SCHEMA
            or not root.is_absolute()
            or pointer.get("producer_repository") != REPOSITORY
            or not re.fullmatch(
                r"[a-zA-Z0-9_-]{1,100}", str(pointer.get("export_root_id") or "")
            )
        ):
            raise LatestReportConsumerError("MAIN_PUBLIC_EXPORT_BINDING_INVALID")
        self.pointer = dict(pointer)
        self.root = root.resolve()
        self.manifest: dict[str, Any] = {}
        from jsonschema import Draft202012Validator

        self._schemas = {version: _schema(version) for version in MANIFEST_SCHEMAS}
        self._row_validators = {
            version: Draft202012Validator({"$defs": schema["$defs"],
                                           **schema["properties"]["entries"]["items"]})
            for version, schema in self._schemas.items()
        }

    def _read(self, path: str, digest: str | None = None) -> bytes:
        if path != "latest-manifest.json" and not PATH.fullmatch(path):
            raise LatestReportConsumerError("MAIN_PUBLIC_EXPORT_PATH_OUTSIDE_CONTRACT")
        target = (self.root / path).resolve()
        if (
            not target.is_relative_to(self.root)
            or target.stat().st_size > 8 * 1024 * 1024
        ):
            raise LatestReportConsumerError("MAIN_PUBLIC_EXPORT_PATH_OR_SIZE_INVALID")
        raw = target.read_bytes()
        if digest and hashlib.sha256(raw).hexdigest() != digest:
            raise LatestReportConsumerError("MAIN_PUBLIC_EXPORT_BYTES_CHANGED")
        return raw

    def _manifest(self, value):
        from jsonschema import Draft202012Validator

        if value.get("version") not in self._schemas:
            raise LatestReportConsumerError("MAIN_PUBLIC_MANIFEST_VERSION_UNSUPPORTED")
        schema = self._schemas[value["version"]]
        header = {
            **schema,
            "properties": {
                **schema["properties"],
                "entries": {"type": "array"},
                "latest_by_asset": {"type": "object"},
            },
        }
        if (
            value.get("schema") != MANIFEST_SCHEMA
            or value.get("producer_owner") != "Main App"
            or value.get("export_root_id") != self.pointer["export_root_id"]
            or value.get("public_account_export_allowed") is not False
            or value.get("publication_authority") is not False
            or value.get("manifest_sha256")
            != sha256_of({k: v for k, v in value.items() if k != "manifest_sha256"})
            or _private(value)
            or not isinstance(value.get("entries"), list)
            or len(value["entries"]) > 4096
            or not Draft202012Validator(header).is_valid(value)
        ):
            raise LatestReportConsumerError("MAIN_PUBLIC_MANIFEST_INVALID")
        return value

    def refresh(self, *, cutoff_utc: str, previous: Mapping[str, Any] | None = None):
        latest = _load(self._read("latest-manifest.json"))
        raw = self._read(latest["path"], latest["bytes_sha256"])
        manifest = self._manifest(_load(raw, max_bytes=8 * 1024 * 1024))
        if latest.get("manifest_sha256") != manifest["manifest_sha256"]:
            raise LatestReportConsumerError("MAIN_PUBLIC_MANIFEST_POINTER_MISMATCH")
        if _time(manifest["emitted_at_utc"]) > _time(cutoff_utc):
            raise LatestReportConsumerError("MAIN_PUBLIC_MANIFEST_FUTURE_DEFERRED")
        # Follow only the bounded hash-addressed parent chain. Missed intervals need
        # no Git pointer edits and previously accepted events cannot disappear.
        current, count = manifest, 0
        wanted = (previous or {}).get("manifest_sha256")
        checkpoint = (previous or {}).get("history_checkpoint") or {}
        if checkpoint and checkpoint.get("target_manifest_sha256") != manifest["manifest_sha256"]:
            # Finish the already observed immutable target before chasing a newer pointer.
            manifest = self._manifest(_load(self._read("manifests/" + checkpoint["target_manifest_sha256"] + ".json"), max_bytes=8 * 1024 * 1024))
            if manifest["manifest_sha256"] != checkpoint["target_manifest_sha256"]:
                raise LatestReportConsumerError("MAIN_PUBLIC_MANIFEST_HISTORY_CHANGED")
        if checkpoint.get("target_manifest_sha256") == manifest["manifest_sha256"]:
            wanted = checkpoint.get("accepted_anchor_sha256")
            current = self._manifest(_load(self._read("manifests/" + checkpoint["resume_manifest_sha256"] + ".json"), max_bytes=8 * 1024 * 1024))
            if current["manifest_sha256"] != checkpoint["resume_manifest_sha256"]:
                raise LatestReportConsumerError("MAIN_PUBLIC_MANIFEST_HISTORY_CHANGED")
        while current["manifest_sha256"] != wanted:
            count += 1
            parent = current.get("parent_manifest_sha256")
            if not parent:
                if wanted:
                    raise LatestReportConsumerError("MAIN_PUBLIC_MANIFEST_HISTORY_FORK")
                break
            if not re.fullmatch(r"[0-9a-f]{64}", str(parent)):
                raise LatestReportConsumerError("MAIN_PUBLIC_MANIFEST_HISTORY_BOUND")
            if count > 128:
                raise ManifestHistoryPending({
                    "target_manifest_sha256": manifest["manifest_sha256"],
                    "accepted_anchor_sha256": wanted,
                    "resume_manifest_sha256": current["manifest_sha256"],
                    "verified_links": checkpoint.get("verified_links", 0) + count - 1,
                })
            parent_value = self._manifest(
                _load(
                    self._read("manifests/" + parent + ".json"),
                    max_bytes=8 * 1024 * 1024,
                )
            )
            if (
                parent_value["manifest_sha256"] != parent
                or current["entries"][: len(parent_value["entries"])]
                != parent_value["entries"]
                or _time(parent_value["emitted_at_utc"])
                > _time(current["emitted_at_utc"])
            ):
                raise LatestReportConsumerError("MAIN_PUBLIC_MANIFEST_HISTORY_CHANGED")
            current = parent_value
        if wanted and current["manifest_sha256"] != wanted:
            raise LatestReportConsumerError("MAIN_PUBLIC_MANIFEST_HISTORY_FORK")
        self.manifest = manifest
        return manifest

    def artifact_fingerprint(self, spec):
        """Local change detector for already hash-verified immutable artifacts, never admission authority."""
        if not self._row_validators[self.manifest["version"]].is_valid(spec):
            raise LatestReportConsumerError("MAIN_PUBLIC_EVENT_SCHEMA_INVALID")
        stamps = []
        for key in ("envelope", "public_report", "schema_ref"):
            relative = spec[key]["path"]
            if not PATH.fullmatch(relative):
                raise LatestReportConsumerError("MAIN_PUBLIC_EXPORT_PATH_OUTSIDE_CONTRACT")
            target = (self.root / relative).resolve()
            if not target.is_relative_to(self.root):
                raise LatestReportConsumerError("MAIN_PUBLIC_EXPORT_PATH_OUTSIDE_CONTRACT")
            stat = target.stat()
            stamps.append([relative, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns])
        return sha256_of([str(self.root), spec, stamps])

    def bundle(self, spec: Mapping[str, Any]) -> dict[str, Any]:
        if not self._row_validators[self.manifest["version"]].is_valid(spec):
            raise LatestReportConsumerError("MAIN_PUBLIC_EVENT_SCHEMA_INVALID")
        if (
            spec.get("event_type") not in {"REPORT_VERSION", "REPORT_ANCESTOR"}
            or spec.get("public_account_export_allowed") is not False
        ):
            raise LatestReportConsumerError("MAIN_PUBLIC_REPORT_EVENT_INVALID")
        envelope = self._read(
            spec["envelope"]["path"], spec["envelope"]["bytes_sha256"]
        )
        public = self._read(
            spec["public_report"]["path"], spec["public_report"]["bytes_sha256"]
        )
        schema = self._read(
            spec["schema_ref"]["path"], spec["schema_ref"]["bytes_sha256"]
        )
        e = _load(envelope)
        ancestor = spec["event_type"] == "REPORT_ANCESTOR"
        if ancestor and (
            spec["event_id"] != "report-ancestor:" + str(e.get("report_sha256"))
            or spec.get("envelope_event_id") != e.get("event_id")
            or spec.get("editorial_intent") is not False
            or spec.get("publication_intent") is not False
        ):
            raise LatestReportConsumerError("MAIN_PUBLIC_ANCESTOR_IDENTITY_OR_INTENT_INVALID")
        for key in (
            "event_id",
            "report_id",
            "report_version",
            "report_sha256",
            "parent_report_sha256",
            "known_at_cutoff_utc",
            "generated_at_utc",
            "contract_revision",
            "envelope_sha256",
            "content_eligibility",
            "change_kind",
        ):
            if key == "event_id" and ancestor:
                continue
            if spec.get(key) != e.get(key):
                raise LatestReportConsumerError("MAIN_PUBLIC_EVENT_ENVELOPE_MISMATCH")
        if e.get("asset_ids") != [spec["asset_id"]]:
            raise LatestReportConsumerError("MAIN_PUBLIC_EVENT_ASSET_MISMATCH")
        binding = {
            "producer_repository": REPOSITORY,
            "producer_commit": self.pointer.get("producer_commit"),
            "producer_revision": self.manifest["manifest_sha256"],
            "contract_revision": e["contract_revision"],
            "manifest_sha256": self.manifest["manifest_sha256"],
            "public_export_manifest_verified": True,
            "public_lineage_only": ancestor,
            "public_report_raw_sha256": hashlib.sha256(public).hexdigest(),
            "public_report_locator": "urn:cc-public-report:"
            + self.pointer["export_root_id"]
            + ":"
            + hashlib.sha256(public).hexdigest(),
            "envelope_schema_sha256": hashlib.sha256(schema).hexdigest(),
            "files": {
                "report.json": {
                    "path": spec["public_report"]["path"],
                    "sha256": hashlib.sha256(public).hexdigest(),
                }
            },
        }
        return {
            "envelope": envelope,
            "report": b"",
            "envelope_schema": schema,
            "report_schema": None,
            "public_export": public,
            "binding": binding,
        }
