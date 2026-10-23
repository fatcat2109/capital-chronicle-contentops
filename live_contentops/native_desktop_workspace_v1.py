"""Verified path relocation for the existing manual newsroom; no new state owner."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from pathlib import Path


SCHEMA = "contentops.native_manual_workspace_relocation.v1"
DEFAULT_MANIFEST = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "CapitalChronicle/ContentOps/owner-newsroom/relocation.json"


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def resolve_workspace_path(path, *, manifest_path=None):
    """Resolve operational locations without changing historical sealed paths or payloads."""
    source = Path(path).resolve()
    marker = source.with_name(source.name + ".relocated.json")
    pointer = json.loads(marker.read_bytes()) if marker.is_file() else None
    manifest = Path(manifest_path or (pointer or {}).get("manifest_path") or DEFAULT_MANIFEST)
    if not manifest.is_file():
        if pointer:
            raise ValueError("RELOCATED_WORKSPACE_MANIFEST_MISSING")
        return source
    value = json.loads(manifest.read_bytes())
    digest = _hash({k: v for k, v in value.items() if k != "manifest_sha256"})
    if value.get("schema_version") != SCHEMA or digest != value.get("manifest_sha256") or (pointer and digest != pointer["manifest_sha256"]):
        raise ValueError("WORKSPACE_RELOCATION_METADATA_CHANGED")
    for entry in sorted(value["paths"], key=lambda e: len(e["source"]), reverse=True):
        old, new = Path(entry["source"]), Path(entry["target"])
        if source == old or (entry["kind"] == "directory" and old in source.parents):
            target = new if source == old else new / source.relative_to(old)
            if not new.is_absolute() or not target.exists():
                raise ValueError("RELOCATED_WORKSPACE_TARGET_MISSING")
            return target
    return source


def workspace_snapshot(path):
    """Hash every table's exact logical rows, including leases and accepted model returns."""
    with sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True) as conn:
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("WORKSPACE_INTEGRITY_FAILED")
        tables = {}
        for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            rows = conn.execute('SELECT * FROM "' + name.replace('"', '""') + '"').fetchall()
            encoded = [json.dumps(row, ensure_ascii=False, default=lambda v: v.hex(), separators=(",", ":")) for row in rows]
            tables[name] = {"rows": len(rows), "sha256": _hash(sorted(encoded))}
        return tables


def relocate_owner_workspace(profile_path, target_root):
    """One explicit reversible cutover using the canonical WAL-safe backup facility."""
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    profile_path, target_root = Path(profile_path), Path(target_root).resolve()
    profile = json.loads(profile_path.read_bytes())
    if profile.get("scope") != "OWNER_MANUAL_EDITORIAL_ONLY_EXISTING_REVIEWED_WORKSPACE_NOT_PRODUCTION":
        raise ValueError("EXPLICIT_MANUAL_WORKSPACE_REQUIRED")
    source = Path(profile["store_path"]).resolve()
    if source == resolve_workspace_path(source) and target_root.exists():
        raise ValueError("RELOCATION_TARGET_ALREADY_EXISTS")
    if source != resolve_workspace_path(source):
        raise ValueError("WORKSPACE_ALREADY_RELOCATED")
    if target_root == source.parent or target_root in source.parents or source.parent in target_root.parents:
        raise ValueError("DISTINCT_WORKSPACE_LOCATION_REQUIRED")
    store = ContentOpsDurableStore(source, auto_migrate=False)
    with store.get_read_only_connection() as conn:
        if conn.execute("SELECT 1 FROM leases WHERE status='ACTIVE' LIMIT 1").fetchone():
            raise ValueError("WORKSPACE_HAS_ACTIVE_WRITER_LEASE")
        payloads = [r[0] for r in conn.execute("SELECT payload FROM outbox_messages")]
    before = workspace_snapshot(source)
    backup = store.create_wal_safe_backup()
    target_root.mkdir(parents=True, exist_ok=False)
    target = target_root / source.name
    shutil.copyfile(backup, target)
    if workspace_snapshot(target) != before or workspace_snapshot(source) != before:
        raise ValueError("WORKSPACE_BACKUP_LOGICAL_IDENTITY_CHANGED")
    references = set()

    def collect(value):
        if isinstance(value, dict):
            for item in value.values():
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)
        elif isinstance(value, str) and len(value) < 600 and ("/Temp/" in value or "\\Temp\\" in value):
            path = Path(value)
            if path.is_absolute() and path.exists() and path.resolve() != source:
                references.add(path.resolve())

    for raw in payloads:
        collect(json.loads(raw))
    # Copy referenced historical directories once; their original bytes remain recovery evidence.
    roots = [p for p in sorted(references, key=lambda p: len(str(p))) if not any(d.is_dir() and d in p.parents for d in references)]
    paths = [{"source": str(source), "target": str(target), "kind": "store", "recovery_state": "NON_OPERATING_RECOVERY_COPY"}]
    assets = []
    for number, old in enumerate(roots):
        new = target_root / "historical-artifacts" / (str(number) + "-" + old.name)
        new.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(old, new) if old.is_dir() else shutil.copyfile(old, new)
        paths.append({"source": str(old), "target": str(new), "kind": "directory" if old.is_dir() else "file"})
        for original in (old.rglob("*") if old.is_dir() else [old]):
            if original.is_file():
                copied = new / original.relative_to(old) if old.is_dir() else new
                digest = hashlib.sha256(original.read_bytes()).hexdigest()
                if hashlib.sha256(copied.read_bytes()).hexdigest() != digest:
                    raise ValueError("RELOCATED_ARTIFACT_BYTES_CHANGED")
                assets.append({"source": str(original), "target": str(copied), "sha256": digest})
    value = {"schema_version": SCHEMA, "paths": paths, "artifact_bytes": assets,
             "table_identity_at_cutover": before, "backup_path": str(backup),
             "profile_path": str(profile_path.resolve()), "original_profile": profile,
             "one_operating_store": str(target), "production_migration": False}
    value["manifest_sha256"] = _hash(value)
    manifest = target_root / "relocation.json"
    manifest.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    source.with_name(source.name + ".relocated.json").write_text(json.dumps({
        "manifest_path": str(manifest), "manifest_sha256": value["manifest_sha256"],
        "state": "NON_OPERATING_RECOVERY_COPY"}, indent=2), encoding="utf-8")
    updated = {**profile, "store_path": str(target), "workspace_relocation_manifest": str(manifest)}
    profile_path.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
    return value
