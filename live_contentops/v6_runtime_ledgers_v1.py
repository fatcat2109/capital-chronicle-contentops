"""Canonical Runtime-root path authority and seamless migration for ContentOps V6 ledgers.

Moves default runtime writes for:
  1. public_dispatch_duplicate_ledger_v6.jsonl
  2. live_telemetry_registry_v6.jsonl
off Git-tracked ``docs/automation/...`` paths into ``A:\\Capital Chronicle\\Runtime\\ContentOps\\v6_ledgers\\...``
while preserving 100% backward-compatible read fallback and atomic first-write seeding so zero
historical duplicate-dispatch freeze protection or telemetry history is lost.

Pure standard-library module (zero env lookups, zero network imports).
Operator: T3 Code, Gemini 4 Neon xhigh, antigravity_14
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
from typing import Any, Iterable, Sequence

RUNTIME_ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
CANONICAL_V6_LEDGERS_ROOT = RUNTIME_ROOT / "v6_ledgers"

CANONICAL_PUBLIC_DISPATCH_FREEZE_DIR = CANONICAL_V6_LEDGERS_ROOT / "public_dispatch_freeze"
CANONICAL_PUBLIC_DISPATCH_LEDGER = (
    CANONICAL_PUBLIC_DISPATCH_FREEZE_DIR / "public_dispatch_duplicate_ledger_v6.jsonl"
)

CANONICAL_LIVE_TELEMETRY_DIR = CANONICAL_V6_LEDGERS_ROOT / "live_telemetry"
CANONICAL_LIVE_TELEMETRY_FILE = (
    CANONICAL_LIVE_TELEMETRY_DIR / "live_telemetry_registry_v6.jsonl"
)

REPO_ROOT = Path(__file__).resolve().parents[1]
LEGACY_PUBLIC_DISPATCH_LEDGER_REL = Path(
    "docs/automation/V6_PUBLIC_DISPATCH_FREEZE/public_dispatch_duplicate_ledger_v6.jsonl"
)
LEGACY_LIVE_TELEMETRY_REL = Path(
    "docs/automation/V6_LIVE_TELEMETRY/live_telemetry_registry_v6.jsonl"
)
LEGACY_PUBLIC_DISPATCH_LEDGER = REPO_ROOT / LEGACY_PUBLIC_DISPATCH_LEDGER_REL
LEGACY_LIVE_TELEMETRY_FILE = REPO_ROOT / LEGACY_LIVE_TELEMETRY_REL

_SEED_LOCK = threading.Lock()


def _normalised_key(path: str | Path) -> str:
    try:
        resolved = Path(path).resolve()
    except OSError:
        resolved = Path(os.path.abspath(str(path)))
    return os.path.normcase(str(resolved))


def same_path(a: str | Path | None, b: str | Path | None) -> bool:
    if a is None or b is None:
        return False
    return _normalised_key(a) == _normalised_key(b)


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dedup_paths(paths: Iterable[str | Path]) -> list[Path]:
    seen: set[str] = set()
    ordered: list[Path] = []
    for raw in paths:
        if not raw:
            continue
        p = Path(raw)
        key = _normalised_key(p)
        if key not in seen:
            seen.add(key)
            ordered.append(p)
    return ordered


def default_legacy_paths_for(kind: str, *, repo_root: str | Path | None = None) -> list[Path]:
    """Return deduplicated legacy repo-tracked candidate paths for a V6 ledger kind."""
    if kind == "public_dispatch_duplicate_ledger":
        rel = LEGACY_PUBLIC_DISPATCH_LEDGER_REL
    elif kind == "live_telemetry_registry":
        rel = LEGACY_LIVE_TELEMETRY_REL
    else:
        raise ValueError(f"unsupported_v6_ledger_kind:{kind}")

    candidates: list[Path] = []
    if repo_root is not None:
        candidates.append(Path(repo_root) / rel)
    else:
        candidates.append(REPO_ROOT / rel)
        candidates.append(Path.cwd() / rel)
    return _dedup_paths(candidates)


def _parse_jsonl_dicts(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            rows.append(parsed)
    return rows


def _canonical_row_key(row: dict[str, Any]) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _normalised_lf_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    if not raw:
        return b""
    normalised = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if not normalised.endswith(b"\n"):
        normalised += b"\n"
    return normalised


def _atomic_install_if_absent(target: Path, payload: bytes) -> bool:
    """Atomically create target with payload only if target does not already exist non-empty."""
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=target.name + ".", suffix=".seed.tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if target.exists() and target.stat().st_size > 0:
            return False
        if not target.exists():
            try:
                os.link(tmp_name, target)
                return True
            except FileExistsError:
                return False
            except OSError:
                pass
        # Target is either absent on a link-less FS or exists with 0 bytes.
        if not target.exists() or target.stat().st_size == 0:
            os.replace(tmp_name, target)
            return True
        return False
    finally:
        if os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def seed_runtime_jsonl_if_needed(
    target_path: str | Path,
    legacy_paths: Sequence[str | Path],
) -> bool:
    """Seed a missing/empty runtime JSONL file atomically from the first non-empty legacy file.

    Never mutates or deletes any legacy file. Normalizes CRLF to LF on copy.
    """
    target = Path(target_path)
    with _SEED_LOCK:
        if target.is_file() and target.stat().st_size > 0:
            return False
        source: Path | None = None
        for candidate in _dedup_paths(legacy_paths):
            if same_path(candidate, target):
                continue
            if candidate.is_file() and candidate.stat().st_size > 0:
                source = candidate
                break
        if source is None:
            return False
        payload = _normalised_lf_bytes(source)
        if not payload:
            return False
        return _atomic_install_if_absent(target, payload)


def _should_use_legacy(
    target_path: Path,
    *,
    default_path: Path | None,
    legacy_paths: Sequence[str | Path] | None,
) -> list[Path]:
    if legacy_paths is not None:
        return [p for p in _dedup_paths(legacy_paths) if not same_path(p, target_path)]
    if default_path is not None and same_path(target_path, default_path):
        if same_path(default_path, CANONICAL_PUBLIC_DISPATCH_LEDGER):
            return [p for p in default_legacy_paths_for("public_dispatch_duplicate_ledger") if not same_path(p, target_path)]
        if same_path(default_path, CANONICAL_LIVE_TELEMETRY_FILE):
            return [p for p in default_legacy_paths_for("live_telemetry_registry") if not same_path(p, target_path)]
    return []


def prepare_runtime_jsonl_for_write(
    target_path: str | Path,
    *,
    default_path: str | Path | None = None,
    legacy_paths: Sequence[str | Path] | None = None,
) -> Path:
    """Ensure parent directory exists and seed default runtime ledger from legacy before first write."""
    target = Path(target_path)
    resolved_default = Path(default_path) if default_path is not None else None
    candidates = _should_use_legacy(target, default_path=resolved_default, legacy_paths=legacy_paths)
    if candidates:
        seed_runtime_jsonl_if_needed(target, candidates)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def resolve_jsonl_read_path(
    target_path: str | Path,
    *,
    default_path: str | Path | None = None,
    legacy_paths: Sequence[str | Path] | None = None,
) -> Path:
    """Return target_path if present, else first existing legacy fallback (read-only, zero writes)."""
    target = Path(target_path)
    if target.is_file():
        return target
    resolved_default = Path(default_path) if default_path is not None else None
    for candidate in _should_use_legacy(target, default_path=resolved_default, legacy_paths=legacy_paths):
        if candidate.is_file():
            return candidate
    return target


def read_jsonl_records_with_fallback(
    target_path: str | Path | None,
    *,
    default_path: str | Path | None = None,
    union_legacy: bool = False,
    legacy_paths: Sequence[str | Path] | None = None,
) -> list[dict[str, Any]]:
    """Read JSONL dict records with backward-compatible legacy fallback (strictly read-only).

    - When ``union_legacy=True`` (used for the monotonic duplicate-dispatch freeze ledger),
      reads the deduplicated union of legacy + runtime rows whenever the target resolves to the
      canonical default path (or explicit ``legacy_paths`` are supplied), ensuring zero historical
      duplicate-protection loss even if a runtime file was not pre-seeded.
    - When ``union_legacy=False`` (used for rotatable telemetry), reads ``target_path`` if it
      exists, falling back read-only to legacy only while ``target_path`` does not yet exist.
    - When an explicit custom path (e.g. a test ``tmp_path`` file) is passed without
      ``legacy_paths``, never reads repo legacy files.
    """
    if not target_path:
        return []
    target = Path(target_path)
    resolved_default = Path(default_path) if default_path is not None else None
    candidates = _should_use_legacy(target, default_path=resolved_default, legacy_paths=legacy_paths)

    if not candidates:
        return _parse_jsonl_dicts(target)

    if not union_legacy:
        if target.is_file():
            return _parse_jsonl_dicts(target)
        for candidate in candidates:
            if candidate.is_file():
                return _parse_jsonl_dicts(candidate)
        return []

    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    sources: list[Path] = [c for c in candidates if c.is_file()]
    if target.is_file():
        sources.append(target)
    for src in sources:
        for row in _parse_jsonl_dicts(src):
            key = _canonical_row_key(row)
            if key not in seen:
                seen.add(key)
                merged.append(row)
    return merged


def migrate_v6_ledger(
    *,
    runtime_path: str | Path,
    legacy_path: str | Path,
    union_if_exists: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Idempotently migrate one V6 JSONL ledger from tracked repo path to Runtime root.

    Never modifies or deletes ``legacy_path``.
    """
    src = Path(legacy_path)
    dst = Path(runtime_path)
    src_exists = src.is_file()
    dst_exists_before = dst.is_file()
    src_rows = _parse_jsonl_dicts(src) if src_exists else []
    dst_rows_before = _parse_jsonl_dicts(dst) if dst_exists_before else []

    if not src_exists:
        return {
            "status": "NO_LEGACY_SOURCE",
            "source_path": str(src),
            "target_path": str(dst),
            "source_rows": 0,
            "target_rows_before": len(dst_rows_before),
            "target_rows_after": len(dst_rows_before),
            "rows_added": 0,
            "source_sha256": None,
            "target_sha256": _sha256_file(dst),
            "source_mutated": False,
            "dry_run": dry_run,
        }

    src_sha = _sha256_file(src)
    if not dst_exists_before or dst.stat().st_size == 0:
        if not dry_run:
            seed_runtime_jsonl_if_needed(dst, [src])
        rows_after = len(src_rows) if dry_run else len(_parse_jsonl_dicts(dst))
        return {
            "status": "WOULD_SEED" if dry_run else "SEEDED",
            "source_path": str(src),
            "target_path": str(dst),
            "source_rows": len(src_rows),
            "target_rows_before": len(dst_rows_before),
            "target_rows_after": rows_after,
            "rows_added": len(src_rows),
            "source_sha256": src_sha,
            "target_sha256": _sha256_file(dst),
            "source_mutated": False,
            "dry_run": dry_run,
        }

    if not union_if_exists:
        return {
            "status": "ALREADY_PRESENT_UNTOUCHED",
            "source_path": str(src),
            "target_path": str(dst),
            "source_rows": len(src_rows),
            "target_rows_before": len(dst_rows_before),
            "target_rows_after": len(dst_rows_before),
            "rows_added": 0,
            "source_sha256": src_sha,
            "target_sha256": _sha256_file(dst),
            "source_mutated": False,
            "dry_run": dry_run,
        }

    existing_keys = {_canonical_row_key(row) for row in dst_rows_before}
    missing_rows = [row for row in src_rows if _canonical_row_key(row) not in existing_keys]
    if not missing_rows:
        return {
            "status": "ALREADY_UP_TO_DATE",
            "source_path": str(src),
            "target_path": str(dst),
            "source_rows": len(src_rows),
            "target_rows_before": len(dst_rows_before),
            "target_rows_after": len(dst_rows_before),
            "rows_added": 0,
            "source_sha256": src_sha,
            "target_sha256": _sha256_file(dst),
            "source_mutated": False,
            "dry_run": dry_run,
        }

    if not dry_run:
        with _SEED_LOCK:
            # Ensure target ends with a newline before appending missing legacy rows.
            needs_nl = False
            if dst.stat().st_size > 0:
                with dst.open("rb") as rb:
                    rb.seek(-1, os.SEEK_END)
                    needs_nl = rb.read(1) != b"\n"
            with dst.open("a", encoding="utf-8", newline="\n") as handle:
                if needs_nl:
                    handle.write("\n")
                for row in missing_rows:
                    handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    rows_after = len(dst_rows_before) + len(missing_rows) if dry_run else len(_parse_jsonl_dicts(dst))
    return {
        "status": "WOULD_MERGE_MISSING" if dry_run else "MERGED_MISSING_ROWS",
        "source_path": str(src),
        "target_path": str(dst),
        "source_rows": len(src_rows),
        "target_rows_before": len(dst_rows_before),
        "target_rows_after": rows_after,
        "rows_added": len(missing_rows),
        "source_sha256": src_sha,
        "target_sha256": _sha256_file(dst),
        "source_mutated": False,
        "dry_run": dry_run,
    }


def migrate_all_v6_ledgers(
    *,
    runtime_root: str | Path = RUNTIME_ROOT,
    repo_root: str | Path = REPO_ROOT,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Migrate both V6 ledgers from repo docs/automation into Runtime/ContentOps/v6_ledgers."""
    rt_root = Path(runtime_root) / "v6_ledgers"
    rp_root = Path(repo_root)
    dispatch_result = migrate_v6_ledger(
        runtime_path=rt_root / "public_dispatch_freeze" / "public_dispatch_duplicate_ledger_v6.jsonl",
        legacy_path=rp_root / LEGACY_PUBLIC_DISPATCH_LEDGER_REL,
        union_if_exists=True,
        dry_run=dry_run,
    )
    telemetry_result = migrate_v6_ledger(
        runtime_path=rt_root / "live_telemetry" / "live_telemetry_registry_v6.jsonl",
        legacy_path=rp_root / LEGACY_LIVE_TELEMETRY_REL,
        union_if_exists=False,
        dry_run=dry_run,
    )
    return {
        "runtime_root": str(Path(runtime_root)),
        "repo_root": str(rp_root),
        "dry_run": dry_run,
        "public_dispatch_duplicate_ledger": dispatch_result,
        "live_telemetry_registry": telemetry_result,
    }
