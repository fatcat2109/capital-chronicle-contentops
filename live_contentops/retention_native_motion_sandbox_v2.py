"""Static sandbox and authorship-lineage checks for GPT-5.6-authored Remotion source."""
from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from live_contentops.retention_native_concrete_first_v2 import logical_hash

SCHEMA_VERSION = "contentops.retention_native.motion_sandbox.v2"
ALLOWED_BARE_IMPORTS = frozenset({"react", "remotion"})
FORBIDDEN_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bprocess\s*\.\s*env\b", "environment_read_forbidden"),
    (r"\b(?:child_process|node:child_process)\b", "shell_execution_forbidden"),
    (r"\b(?:node:fs|fs/promises|require\s*\(\s*['\"]fs)", "filesystem_access_forbidden"),
    (r"\b(?:fetch|XMLHttpRequest|WebSocket|EventSource)\s*\(", "network_access_forbidden"),
    (r"\b(?:eval|Function)\s*\(", "dynamic_execution_forbidden"),
    (r"\b(?:npm|pnpm|yarn)\b", "dynamic_dependency_forbidden"),
    (r"\b(?:youtube|tiktok|substack)\b.*\b(?:upload|publish|post)\b", "platform_write_forbidden"),
)


def _imports(source: str) -> list[str]:
    return re.findall(r"(?:import[^;]*?from\s*|import\s*)['\"]([^'\"]+)['\"]", source)


def validate_generated_motion_files(
    files: Sequence[Mapping[str, Any]], *, expected_beat_ids: Sequence[str]
) -> dict[str, Any]:
    violations: list[dict[str, str]] = []
    hashes: dict[str, str] = {}
    combined = ""
    for row in files:
        path = str(row.get("path") or "")
        source = str(row.get("source") or "")
        pure = PurePosixPath(path)
        if (
            not path.startswith("src/generated/")
            or pure.is_absolute()
            or ".." in pure.parts
            or pure.suffix not in {".tsx", ".ts"}
        ):
            violations.append({"path": path, "code": "generated_path_outside_sandbox"})
            continue
        for package in _imports(source):
            if package.startswith("."):
                resolved = PurePosixPath(path).parent.joinpath(package)
                if ".." in resolved.parts:
                    violations.append({"path": path, "code": "relative_import_escape"})
            elif package not in ALLOWED_BARE_IMPORTS:
                violations.append({"path": path, "code": f"import_not_allowed:{package}"})
        for pattern, code in FORBIDDEN_PATTERNS:
            if re.search(pattern, source, flags=re.IGNORECASE | re.DOTALL):
                violations.append({"path": path, "code": code})
        hashes[path] = logical_hash(source)
        combined += "\n" + source
    absent = [beat_id for beat_id in expected_beat_ids if beat_id not in combined]
    if absent:
        violations.append({"path": "*", "code": "expected_beat_bindings_missing:" + ",".join(absent)})
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if not violations else "BLOCK",
        "violations": violations,
        "source_hashes": hashes,
        "network_calls_allowed": False,
        "filesystem_mutation_allowed": False,
        "public_write_allowed": False,
    }


def persist_authored_files(
    files: Sequence[Mapping[str, Any]], *, renderer_root: str | Path
) -> dict[str, Any]:
    root = Path(renderer_root).resolve()
    generated = (root / "src" / "generated").resolve()
    generated.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    for row in files:
        relative = PurePosixPath(str(row["path"]))
        target = (root / Path(*relative.parts)).resolve()
        if generated not in target.parents:
            raise ValueError("authored_target_outside_generated_root")
        before = str(row["source"])
        after = before.replace("\r\n", "\n").replace("\r", "\n")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(after, encoding="utf-8", newline="\n")
        rows.append(
            {
                "path": str(target),
                "model_output_sha256": logical_hash(before),
                "persisted_sha256": logical_hash(after),
                "normalization": "line_endings_only",
                "viewer_visible_semantic_mutation": "NONE",
            }
        )
    return {"status": "PASS", "files": rows, "provenance_broken": False}


def validate_revision_accounting(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    creative = [row for row in rows if row.get("kind") in {"SYSTEMIC_STORYBOARD", "RENDERED_LOCALIZED"}]
    kinds = [str(row.get("kind")) for row in creative]
    violations: list[str] = []
    if len(creative) > 2:
        violations.append("creative_revision_budget_exceeded")
    if kinds.count("SYSTEMIC_STORYBOARD") > 1:
        violations.append("systemic_storyboard_revision_budget_exceeded")
    if kinds.count("RENDERED_LOCALIZED") > 1:
        violations.append("rendered_localized_revision_budget_exceeded")
    for row in creative:
        if str(row.get("effective_model") or "") != "new/gpt-5.6-sol-xhigh":
            violations.append("creative_revision_degraded_model")
        if not str(row.get("receipt_sha256") or ""):
            violations.append("creative_revision_receipt_missing")
    return {
        "status": "PASS" if not violations else "BLOCK",
        "creative_revisions_consumed": len(creative),
        "mechanical_corrections": sum(1 for row in rows if row.get("kind") == "MECHANICAL"),
        "violations": violations,
    }
