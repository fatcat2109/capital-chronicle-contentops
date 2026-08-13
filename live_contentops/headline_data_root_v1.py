"""Stable operational root and additive reconciliation for V1 headline ingestion.

Source code may run from a Git worktree, but captured headline truth must not follow that
checkout.  This module is the single path authority for capture, rolling-window reads, the
Daily App read model, shadow/zero-write execution, and the independent hourly audit.

Reconciliation copies into a new stable runtime root.  It never deletes or edits a source
artifact.  Sidecar rows and ALL_DATA objects are unioned by governed identity, raw archives
are copied byte-for-byte, and an audit record contains only paths, counts, and hashes (never
headline text or raw payload contents).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


HEADLINE_ROOT_SCHEMA_VERSION = "contentops.headline_operational_root.v1"
RECONCILIATION_SCHEMA_VERSION = "contentops.headline_root_reconciliation.v1"
CANONICAL_HEADLINE_DATA_ROOT = Path(
    r"A:\Capital Chronicle\Runtime\ContentOps\headline_ingestion\data"
)
SIDECAR_RELATIVE_DIR = Path("intake") / "headline_sidecars"
RAW_ARCHIVE_RELATIVE_DIR = Path("raw_archive") / "headline_cdp"
STATE_RELATIVE_DIR = Path("state") / "current"
ALL_DATA_FILENAME = "capital_chronicle_ALL_DATA.json"
SIDECAR_PATTERN = "step1_headline_sidecar_*.jsonl"
_SIDECAR_DATE = re.compile(r"step1_headline_sidecar_(\d{4}_\d{2}_\d{2})\.jsonl$")


def canonical_headline_data_root() -> Path:
    return CANONICAL_HEADLINE_DATA_ROOT


def canonical_headline_sidecar_dir() -> Path:
    return canonical_headline_data_root() / SIDECAR_RELATIVE_DIR


def canonical_headline_sidecar_glob() -> str:
    return str(canonical_headline_sidecar_dir() / "*.jsonl")


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _row_identity(row: Mapping[str, Any]) -> str:
    for field in ("dedup_key", "headline_id", "tweet_id", "text_sha256"):
        value = str(row.get(field) or "").strip()
        if value:
            return f"{field}:{value}"
    return "logical_sha256:" + _sha256_bytes(_canonical_json_bytes(dict(row)))


def _all_data_identity(row: Any) -> str:
    if isinstance(row, Mapping):
        for field in ("dedup_key", "tweet_id", "id_str", "rest_id", "headline_id"):
            value = str(row.get(field) or "").strip()
            if value:
                return f"{field}:{value}"
    return "logical_sha256:" + _sha256_bytes(_canonical_json_bytes(row))


def _preferred_candidate(candidates: Iterable[tuple[str, Mapping[str, Any]]]) -> tuple[str, dict[str, Any]]:
    # Newest capture metadata wins when one governed identity has multiple representations;
    # the canonical serialization is the deterministic tie-breaker.
    source_name, row = max(
        candidates,
        key=lambda item: (
            str(item[1].get("captured_at_utc") or ""),
            _canonical_json_bytes(dict(item[1])),
            item[0],
        ),
    )
    return source_name, dict(row)


def _source_inventory(data_root: Path) -> dict[str, Any]:
    sidecars = sorted((data_root / SIDECAR_RELATIVE_DIR).glob(SIDECAR_PATTERN))
    raw_files = sorted(
        path for path in (data_root / RAW_ARCHIVE_RELATIVE_DIR).rglob("*") if path.is_file()
    ) if (data_root / RAW_ARCHIVE_RELATIVE_DIR).is_dir() else []
    file_hashes = [
        (str(path.relative_to(data_root)).replace("\\", "/"), _sha256_file(path))
        for path in [*sidecars, *raw_files]
    ]
    inventory_digest = _sha256_bytes(_canonical_json_bytes(file_hashes))
    return {
        "data_root": str(data_root),
        "sidecar_file_count": len(sidecars),
        "raw_archive_file_count": len(raw_files),
        "inventory_sha256": inventory_digest,
    }


def reconcile_headline_data_roots(
    source_data_roots: Sequence[str | Path],
    *,
    canonical_root: str | Path = CANONICAL_HEADLINE_DATA_ROOT,
    state_authority_root: str | Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Union split worktree-local headline data into the stable runtime root.

    Source order has no effect on headline selection. ``state_authority_root`` is explicit
    because DQR/input-state documents are point-in-time authority, not an additive corpus.
    Conflicting raw filenames fail closed instead of overwriting either byte sequence.
    """
    target = Path(canonical_root).resolve()
    sources = sorted({Path(value).resolve() for value in source_data_roots if Path(value).is_dir()}, key=str)
    if target.is_dir() and target not in sources:
        sources.append(target)
        sources.sort(key=str)
    if not sources:
        raise ValueError("headline_reconciliation_source_roots_missing")

    candidates: dict[str, list[tuple[str, Mapping[str, Any]]]] = {}
    candidate_day: dict[tuple[str, str], str] = {}
    malformed_sidecar_lines = 0
    source_row_count = 0
    for source in sources:
        for sidecar in sorted((source / SIDECAR_RELATIVE_DIR).glob(SIDECAR_PATTERN)):
            match = _SIDECAR_DATE.fullmatch(sidecar.name)
            day = match.group(1) if match else "undated"
            with sidecar.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    source_row_count += 1
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        malformed_sidecar_lines += 1
                        continue
                    if not isinstance(row, Mapping):
                        malformed_sidecar_lines += 1
                        continue
                    identity = _row_identity(row)
                    source_key = str(source)
                    candidates.setdefault(identity, []).append((source_key, row))
                    candidate_day[(identity, source_key)] = day

    selected_by_day: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for identity, rows in candidates.items():
        source_name, row = _preferred_candidate(rows)
        day = candidate_day[(identity, source_name)]
        selected_by_day.setdefault(day, []).append((identity, row))
    for day, rows in sorted(selected_by_day.items()):
        filename = f"step1_headline_sidecar_{day}.jsonl"
        payload = b"".join(
            _canonical_json_bytes(row) + b"\n" for _identity, row in sorted(rows, key=lambda item: item[0])
        )
        _atomic_write(target / SIDECAR_RELATIVE_DIR / filename, payload)

    all_data: dict[str, Any] = {}
    all_data_source_count = 0
    for source in sources:
        path = source / ALL_DATA_FILENAME
        if not path.is_file():
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(value, list):
            continue
        for row in value:
            all_data_source_count += 1
            identity = _all_data_identity(row)
            current = all_data.get(identity)
            if current is None or _canonical_json_bytes(row) > _canonical_json_bytes(current):
                all_data[identity] = row
    _atomic_write(
        target / ALL_DATA_FILENAME,
        json.dumps(
            [all_data[key] for key in sorted(all_data)],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8") + b"\n",
    )

    copied_raw = 0
    reused_raw = 0
    for source in sources:
        raw_root = source / RAW_ARCHIVE_RELATIVE_DIR
        if not raw_root.is_dir():
            continue
        for raw_path in sorted(path for path in raw_root.rglob("*") if path.is_file()):
            relative = raw_path.relative_to(raw_root)
            destination = target / RAW_ARCHIVE_RELATIVE_DIR / relative
            source_hash = _sha256_file(raw_path)
            if destination.is_file():
                if _sha256_file(destination) != source_hash:
                    raise RuntimeError(f"headline_raw_archive_collision:{relative}")
                reused_raw += 1
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(raw_path, destination)
            copied_raw += 1

    state_source = Path(state_authority_root).resolve() if state_authority_root else sources[0]
    copied_state_files = 0
    state_root = state_source / STATE_RELATIVE_DIR
    if state_root.is_dir():
        for state_path in sorted(path for path in state_root.rglob("*") if path.is_file()):
            destination = target / STATE_RELATIVE_DIR / state_path.relative_to(state_root)
            if destination.is_file() and _sha256_file(destination) != _sha256_file(state_path):
                raise RuntimeError(f"headline_state_authority_conflict:{state_path.name}")
            if not destination.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(state_path, destination)
                copied_state_files += 1

    inventories = [_source_inventory(source) for source in sources]
    generated = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    audit = {
        "schema_version": RECONCILIATION_SCHEMA_VERSION,
        "generated_at_utc": generated.isoformat().replace("+00:00", "Z"),
        "canonical_data_root": str(target),
        "source_roots": inventories,
        "state_authority_root": str(state_source),
        "source_sidecar_row_count": source_row_count,
        "canonical_unique_sidecar_row_count": len(candidates),
        "deduplicated_row_count": max(0, source_row_count - len(candidates)),
        "malformed_sidecar_line_count": malformed_sidecar_lines,
        "source_all_data_count": all_data_source_count,
        "canonical_all_data_count": len(all_data),
        "raw_archive_files_copied": copied_raw,
        "raw_archive_files_reused": reused_raw,
        "state_files_copied": copied_state_files,
        "source_artifacts_mutated": False,
        "public_write_performed": False,
        "llm_or_provider_call_performed": False,
    }
    audit_dir = target.parent / "reconciliation"
    _atomic_write(audit_dir / "latest.json", _canonical_json_bytes(audit) + b"\n")
    return audit
