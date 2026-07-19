"""Validation helpers for the accepted generic V2 foundation freeze."""
from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

from live_contentops.content_intelligence_contracts_v2 import canonical_json, logical_hash


MANIFEST_PATH = Path(__file__).with_name("generic_foundation_freeze_manifest_v1.json")


def load_freeze_manifest(path: str | Path = MANIFEST_PATH) -> Mapping[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def calculated_manifest_hash(manifest: Mapping[str, Any]) -> str:
    return logical_hash({key: value for key, value in manifest.items() if key != "manifest_logical_hash"})


def _record_hash(record: Mapping[str, Any]) -> str:
    return sha256(canonical_json(record).encode("utf-8")).hexdigest()


def validate_append_only_registry(
    baseline: Mapping[str, Any], registry: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate baseline-record immutability without freezing record counts."""
    blockers: list[str] = []
    fields = baseline["record_identity_fields"]
    current = {"@".join(str(row[field]) for field in fields): row for row in registry.get("records", [])}
    for identity, expected_hash in baseline["record_hashes"].items():
        if identity not in current:
            blockers.append(f"baseline_registry_record_missing:{identity}")
        elif _record_hash(current[identity]) != expected_hash:
            blockers.append(f"baseline_registry_record_mutated:{identity}")
    if len(current) > len(baseline["record_hashes"]) and registry.get("registry_version") == baseline["registry_version"]:
        blockers.append("append_only_registry_version_not_advanced")
    if len(current) > len(baseline["record_hashes"]) and registry.get("registry_logical_hash") == baseline["registry_logical_hash"]:
        blockers.append("append_only_registry_hash_not_advanced")
    return tuple(dict.fromkeys(blockers))


def validate_foundation_freeze(
    repo_root: str | Path,
    manifest: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    """Reject silent semantic mutation while permitting versioned append-only records."""
    root = Path(repo_root).resolve()
    manifest = manifest or load_freeze_manifest()
    blockers: list[str] = []
    if manifest.get("schema_version") != "contentops.generic_foundation_freeze_manifest.v1":
        blockers.append("freeze_manifest_schema_mismatch")
    if manifest.get("manifest_logical_hash") != calculated_manifest_hash(manifest):
        blockers.append("freeze_manifest_logical_hash_mismatch")
    for row in manifest.get("exact_semantic_files", []):
        path = root / row["path"]
        if not path.is_file():
            blockers.append(f"frozen_semantic_file_missing:{row['path']}")
        elif sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            blockers.append(f"frozen_semantic_file_mutated:{row['path']}")
    for baseline in manifest.get("registry_baselines", []):
        path = root / baseline["path"]
        if not path.is_file():
            blockers.append(f"registry_missing:{baseline['path']}")
            continue
        registry = json.loads(path.read_text(encoding="utf-8"))
        calculated_registry_hash = logical_hash({
            key: value for key, value in registry.items() if key != "registry_logical_hash"
        })
        if registry.get("registry_logical_hash") != calculated_registry_hash:
            blockers.append(f"registry_logical_hash_mismatch:{baseline['path']}")
        blockers.extend(
            f"{reason}:{baseline['path']}"
            for reason in validate_append_only_registry(baseline, registry)
        )
    config = json.loads((root / manifest["config"]["path"]).read_text(encoding="utf-8"))
    for field in ("schema_version", "config_version", "config_logical_hash", "calibration_state"):
        if config.get(field) != manifest["config"][field]:
            blockers.append(f"frozen_config_{field}_mismatch")
    for kind in ("classes", "functions"):
        for qualified in manifest["public_adapter_api"][kind]:
            module_name, symbol = qualified.split(".", 1)
            module = importlib.import_module(f"live_contentops.{module_name}")
            if not hasattr(module, symbol):
                blockers.append(f"public_adapter_api_missing:{qualified}")
    try:
        tag_object = subprocess.run(
            ["git", "-C", str(root), "rev-parse", manifest["release"]["tag"]],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        tag_commit = subprocess.run(
            ["git", "-C", str(root), "rev-parse", f"{manifest['release']['tag']}^{{commit}}"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        if tag_object != manifest["release"]["tag_object"]:
            blockers.append("accepted_release_tag_object_mismatch")
        if tag_commit != manifest["release"]["release_commit"]:
            blockers.append("accepted_release_commit_mismatch")
    except subprocess.CalledProcessError:
        blockers.append("accepted_release_tag_unavailable")
    return tuple(dict.fromkeys(blockers))
