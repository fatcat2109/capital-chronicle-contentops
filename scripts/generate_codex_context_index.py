#!/usr/bin/env python3
"""Generate the deterministic Codex repository graph and hot-path entry maps.

The output is descriptive repository state, not product authority. The generator uses only the
Python standard library and a small set of syntax/manifest readers; it intentionally excludes
archives, runtime data, vendor trees, and generated media.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs" / "codegraph"
GRAPH_PATH = OUTPUT_DIR / "graph.json"
INDEX_PATH = OUTPUT_DIR / "INDEX.md"
V2_CONTEXT_PATH = OUTPUT_DIR / "V2_CONTEXT.md"
V1_CONTEXT_PATH = OUTPUT_DIR / "V1_CONTEXT.md"
SCHEMA_VERSION = "contentops.codex_context_graph.v2"
GENERATOR_VERSION = "2.2.1"

CODE_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".ps1",
    ".cmd",
    ".bat",
}
MANIFEST_NAMES = {"pyproject.toml", "package.json", "tsconfig.json", "vite.config.ts"}
AUTHORITY_DOCS = {
    "AGENTS.md",
    "docs/AGENTS.md",
    "docs/CURRENT_CONTEXT.md",
    "docs/AI_BUILDER_BOOTSTRAP.md",
    "docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md",
    "docs/status/CURRENT_PROJECT_STATUS.md",
    "docs/status/current_project_status.json",
    "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md",
    "docs/status/CONTENTOPS_V1_FULL_AUTOMATION_NINE_SURFACE_HANDOFF_V1.md",
    "docs/status/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_DIRECTION_OVERLAY_V1.md",
    "docs/status/CONTENTOPS_V2_GPT56_CREATIVE_CODE_AND_ASSET_DENSITY_OWNER_OVERRIDE_V1.md",
    "docs/automation/CONTENTOPS_V2_FREEFORM_CHAPTERIZED_HIGH_XHIGH_OWNER_OVERRIDE_V1.md",
    "docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_NORTH_STAR_V2.md",
    "docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_MASTER_PLAN_V2.md",
    "docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_TASK_GRAPH_V2.md",
    "docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_CURRENT_EXECUTION_POINTER_V2.md",
    "docs/automation/CONTENTOPS_V2_REMOTION_AGENT_SKILL_BASELINE_V1.md",
    "docs/automation/CONTENTOPS_V2_FRESH_CHAT_HANDOFF_V1.md",
    "docs/codegraph/V1_CONTEXT.md",
    "docs/codegraph/V2_CONTEXT.md",
}
GENERATED_PATHS = {
    "docs/codegraph/graph.json",
    "docs/codegraph/INDEX.md",
    "docs/codegraph/V2_CONTEXT.md",
}
EXCLUDED_PARTS = {
    ".git",
    ".task-runtime",
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    "raw_archive",
    "exports",
    "scratch",
    "runtime",
    "venv",
    "virtualenvs",
}
EXCLUDED_PREFIXES = (
    "docs/archive/",
    "docs/automation/VIDEO_FOUNDATION_AND_PAUSE_V1/",
    "headline_ingestion/data/raw_archive/",
    "headline_ingestion/data/intake/headline_sidecars/",
)
INCLUDED_ROOTS = (
    "live_contentops/",
    "headline_ingestion/",
    "tests/",
    "ui/contentops_v5/",
    "scripts/",
    "video/",
    "current authority anchors",
    "AGENTS hierarchy",
)
EXCLUDED_ROOTS = (
    ".git/",
    ".task-runtime/",
    ".venv/ and virtualenvs/",
    "node_modules/",
    "Runtime outputs/",
    "headline_ingestion/data/raw_archive/",
    "headline_ingestion/data/intake/headline_sidecars/",
    "docs/archive/ and non-anchor historical evidence/",
    "screenshots, video, caches, and generated build artifacts",
)

HOT_PATHS: dict[str, tuple[str, ...]] = {
    "V1 live runtime": (
        "Start_ContentOps_Daily_App.cmd",
        "STOP_ALL_CONTENTOPS_BACKGROUND.cmd",
        "RESUME_CONTENTOPS_LLM.cmd",
        "scripts/Stop-ContentOpsBackground.ps1",
        "scripts/Resume-ContentOpsLLM.ps1",
        "live_contentops/daily_app_launcher_v1.py",
        "live_contentops/daily_app_supervisor_v1.py",
        "live_contentops/llm_operator_control_v1.py",
        "live_contentops/llm_cost_governor_v1.py",
        "live_contentops/durable_operational_store_v1.py",
        "tests/test_contentops_emergency_stop_v1.py",
        "tests/test_llm_cost_governor_v1.py",
        "tests/test_contentops_daily_app_launcher_v1.py",
        "tests/test_daily_app_supervisor_v1.py",
    ),
    "Newsroom / intake": (
        "live_contentops/continuous_headline_ingest_v1.py",
        "live_contentops/eight_platform_substack_first_pipeline_v1.py",
        "live_contentops/_eight_platform_substack_first_pipeline_impl_v1.py",
        "live_contentops/newsroom_assignment_scheduler_v1.py",
        "live_contentops/preselection_intelligence_v1.py",
        "live_contentops/editorial_portfolio_v1.py",
        "tests/test_contentops_continuous_intelligence_realign_v1.py",
        "tests/test_preselection_published_memory_breaking_wake_closeout_v1.py",
        "tests/test_rolling_x_newsroom_cycle_v1.py",
    ),
    "Capital Chronicle integration": (
        "live_contentops/capital_chronicle_data_catalog_v1.py",
        "live_contentops/published_corpus_read_model_v1.py",
        "tests/test_contentops_continuous_intelligence_realign_v1.py",
        "tests/test_preselection_published_memory_breaking_wake_closeout_v1.py",
    ),
    "Evidence": (
        "live_contentops/rolling_x_targeted_evidence_adapter_v1.py",
        "live_contentops/official_primary_evidence_loader_v1.py",
        "live_contentops/official_primary_source_locator_v1.py",
        "tests/test_rolling_x_targeted_evidence_adapter_v1.py",
        "tests/test_official_primary_evidence_loader_v1.py",
        "tests/test_rolling_x_evidence_viability_v1.py",
    ),
    "Article / media": (
        "live_contentops/rolling_x_grounded_article_media_builder_v1.py",
        "tests/test_rolling_x_grounded_article_media_builder_v1.py",
    ),
    "Publication / readback": (
        "live_contentops/publication_coordinator_v1.py",
        "live_contentops/destination_transport_registry_v1.py",
        "live_contentops/production_runtime_v1.py",
        "tests/test_publication_coordinator_v1.py",
        "tests/test_destination_identity_pinning_v1.py",
        "tests/test_daily_app_publication_lifecycle_v1.py",
        "tests/test_daily_app_automatic_readback_housekeeping_v1.py",
    ),
    "V5": (
        "live_contentops/server.py",
        "live_contentops/daily_app_ui_read_model_v1.py",
        "ui/contentops_v5/src/main.tsx",
        "ui/contentops_v5/src/views/DailyAppConsole.tsx",
        "ui/contentops_v5/src/test/daily_app_console.test.tsx",
        "tests/test_daily_app_ui_read_model_v1.py",
    ),
    "Router / models": (
        "live_contentops/nine_router_llm_seam_v2.py",
        "live_contentops/nine_router_ordered_model_router_v2.py",
        "live_contentops/nine_router_provider_adapter_v2.py",
        "tests/test_nine_router_ordered_model_router_v2.py",
        "tests/test_nine_router_provider_adapter_and_preflight_v2.py",
    ),
}
SYMBOL_DETAIL_PATHS = {
    path
    for paths in HOT_PATHS.values()
    for path in paths
    if path.endswith(".py") and not path.startswith("tests/")
} | {
    "live_contentops/production_orchestrator_v1.py",
    "live_contentops/newsroom_assignment_scheduler_v1.py",
    "live_contentops/editorial_portfolio_v1.py",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def included(path: Path) -> bool:
    relative = rel(path)
    if relative in GENERATED_PATHS or any(
        relative.startswith(prefix) for prefix in EXCLUDED_PREFIXES
    ):
        return False
    if (
        relative.startswith("docs/")
        and relative not in AUTHORITY_DOCS
        and not path.name == "AGENTS.md"
    ):
        return False
    if any(part.lower() in EXCLUDED_PARTS for part in PurePosixPath(relative).parts):
        return False
    return (
        path.suffix.lower() in CODE_SUFFIXES
        or path.name in MANIFEST_NAMES
        or relative in AUTHORITY_DOCS
        or path.name == "AGENTS.md"
    )


def source_files() -> list[Path]:
    paths: list[Path] = []
    for current, directories, filenames in os.walk(ROOT):
        directories[:] = sorted(
            directory
            for directory in directories
            if directory.lower() not in EXCLUDED_PARTS
        )
        base = Path(current)
        for filename in sorted(filenames):
            path = base / filename
            if included(path):
                paths.append(path)
    return sorted(paths, key=rel)


def git_commit_timestamp() -> str:
    """Return a deterministic generation timestamp derived from the source commit."""
    try:
        source_head = git_head()
        raw = subprocess.check_output(
            ["git", "show", "-s", "--format=%cI", source_head], cwd=ROOT, text=True
        ).strip()
        return datetime.fromisoformat(raw).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except (OSError, subprocess.CalledProcessError, ValueError):
        return "UNKNOWN"


def git_head() -> str:
    """Newest commit that changed an indexed source, not a generated-only commit."""
    try:
        current = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
        for _ in range(100):
            changed = subprocess.check_output(
                [
                    "git", "diff-tree", "--root", "-m", "--no-commit-id", "--name-only",
                    "-r", current,
                ],
                cwd=ROOT,
                text=True,
            ).splitlines()
            if any(name not in GENERATED_PATHS and included(ROOT / name) for name in changed):
                return current
            current = subprocess.check_output(
                ["git", "rev-parse", f"{current}^"], cwd=ROOT, text=True
            ).strip()
        return current
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def source_digest(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(rel(path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        digest.update(b"\n")
    return digest.hexdigest()


def nearest_agents_file(relative_path: str) -> str:
    """Return the nearest scoped AGENTS.md for a file-like repository path."""
    candidate = ROOT / relative_path
    current = candidate if candidate.is_dir() else candidate.parent
    while True:
        scoped = current / "AGENTS.md"
        if scoped.is_file():
            return rel(scoped)
        if current == ROOT or ROOT not in current.parents:
            return "AGENTS.md"
        current = current.parent


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def python_module_name(path: str) -> str | None:
    if not path.endswith(".py"):
        return None
    stem = path[:-3].replace("/", ".")
    if stem.endswith(".__init__"):
        stem = stem[: -len(".__init__")]
    return stem


def python_import_edges(
    path: Path, module_paths: dict[str, str]
) -> list[dict[str, str]]:
    try:
        tree = ast.parse(read_text(path), filename=str(path))
    except SyntaxError:
        return []
    current = python_module_name(rel(path)) or ""
    package = current.rsplit(".", 1)[0] if "." in current else ""
    edges: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            prefix = package
            if node.level:
                parts = package.split(".") if package else []
                prefix = ".".join(parts[: max(0, len(parts) - node.level + 1)])
            base = ".".join(part for part in (prefix, node.module or "") if part)
            names = [base] + [
                f"{base}.{alias.name}" for alias in node.names if alias.name != "*"
            ]
        for name in names:
            target_module = name
            while target_module and target_module not in module_paths:
                target_module = (
                    target_module.rsplit(".", 1)[0] if "." in target_module else ""
                )
            if target_module and module_paths[target_module] != rel(path):
                edges.add((module_paths[target_module], "imports"))
    return [
        {
            "from": rel(path),
            "to": target,
            "kind": kind,
            "inference": "python_ast_import",
        }
        for target, kind in sorted(edges)
    ]


IMPORT_RE = re.compile(r"(?:from|import)\s+['\"](\.?\.?/[^'\"]+)['\"]")


def ts_import_edges(path: Path, code_paths: set[str]) -> list[dict[str, str]]:
    edges: set[str] = set()
    source = rel(path)
    for raw in IMPORT_RE.findall(read_text(path)):
        candidate = (path.parent / raw).resolve()
        options = [
            candidate,
            *[
                candidate.with_suffix(suffix)
                for suffix in (".ts", ".tsx", ".js", ".jsx")
            ],
            candidate / "index.ts",
            candidate / "index.tsx",
        ]
        for option in options:
            try:
                target = rel(option)
            except ValueError:
                continue
            if target in code_paths and target != source:
                edges.add(target)
                break
    return [
        {
            "from": source,
            "to": target,
            "kind": "imports",
            "inference": "typescript_relative_import_regex",
        }
        for target in sorted(edges)
    ]


class _PythonDefinitionVisitor(ast.NodeVisitor):
    def __init__(self, source: str) -> None:
        self.source = source
        self.stack: list[str] = []
        self.definitions: list[dict[str, Any]] = []

    def _visit_definition(self, node: ast.AST, name: str, kind: str) -> None:
        qualified = ".".join((*self.stack, name))
        self.definitions.append(
            {
                "id": f"python_symbol:{self.source}::{qualified}",
                "kind": kind,
                "path": self.source,
                "symbol": qualified,
                "line": int(getattr(node, "lineno", 0) or 0),
            }
        )
        self.stack.append(name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self._visit_definition(node, node.name, "python_class")

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        kind = "python_method" if self.stack else "python_function"
        self._visit_definition(node, node.name, kind)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        kind = "python_method" if self.stack else "python_function"
        self._visit_definition(node, node.name, kind)


def python_tree(path: Path) -> ast.Module | None:
    try:
        return ast.parse(read_text(path), filename=str(path))
    except SyntaxError:
        return None


def python_definitions(path: Path) -> list[dict[str, Any]]:
    tree = python_tree(path)
    if tree is None:
        return []
    visitor = _PythonDefinitionVisitor(rel(path))
    visitor.visit(tree)
    source = rel(path)
    if is_test_path(source):
        return []
    if source in SYMBOL_DETAIL_PATHS:
        # Top-level definitions and direct class methods are the useful call-path surface;
        # nested closure internals add bulk without improving fresh-session routing.
        return [row for row in visitor.definitions if row["symbol"].count(".") <= 1]
    return [
        row
        for row in visitor.definitions
        if "." not in row["symbol"] and not row["symbol"].startswith("_")
    ]


TS_EXPORT_RE = re.compile(
    r"^\s*export\s+(?:default\s+)?(?:async\s+)?"
    r"(?:function|class|const|let|var|interface|type|enum)\s+([A-Za-z_$][\w$]*)",
    re.MULTILINE,
)


def typescript_export_nodes(path: Path) -> list[dict[str, Any]]:
    source = rel(path)
    text = read_text(path)
    return [
        {
            "id": f"typescript_export:{source}::{name}",
            "kind": "typescript_export",
            "path": source,
            "symbol": name,
            "line": text[: match.start()].count("\n") + 1,
        }
        for match in TS_EXPORT_RE.finditer(text)
        for name in [match.group(1)]
    ]


def _constant_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def python_metadata_nodes(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Derive CLI commands, HTTP routes, schema IDs, and durable tables."""
    source = rel(path)
    text_value = read_text(path)
    tree = python_tree(path)
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str], dict[str, str]] = {}
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                value = _constant_string(node.value)
                if value:
                    for target in targets:
                        if isinstance(target, ast.Name) and "SCHEMA" in target.id and "." in value:
                            node_id = f"schema:{value}"
                            nodes[node_id] = {"id": node_id, "kind": "schema", "schema_id": value}
                            edges[(source, node_id, "declares_schema")] = {
                                "from": source,
                                "to": node_id,
                                "kind": "declares_schema",
                                "inference": "python_ast_schema_constant",
                            }
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "add_parser" and node.args:
                    command = _constant_string(node.args[0])
                    if command:
                        node_id = f"cli:{command}"
                        nodes[node_id] = {"id": node_id, "kind": "cli_command", "command": command}
                        edges[(source, node_id, "registers_cli_command")] = {
                            "from": source,
                            "to": node_id,
                            "kind": "registers_cli_command",
                            "inference": "python_ast_add_parser",
                        }
    for match in re.finditer(r"CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+([A-Za-z_][\w]*)", text_value, re.I):
        table = match.group(1)
        node_id = f"durable_table:{table}"
        nodes[node_id] = {"id": node_id, "kind": "durable_table", "table": table}
        edges[(source, node_id, "owns_table_definition")] = {
            "from": source,
            "to": node_id,
            "kind": "owns_table_definition",
            "inference": "sql_create_table_regex",
        }
    return sorted(nodes.values(), key=lambda row: row["id"]), sorted(
        edges.values(), key=lambda row: (row["from"], row["to"], row["kind"])
    )


def http_endpoint_nodes(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    if rel(path) != "live_contentops/server.py":
        return [], []
    text_value = read_text(path)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    for method, start, end in (("GET", "def do_GET", "def do_POST"), ("POST", "def do_POST", None)):
        start_at = text_value.find(start)
        if start_at < 0:
            continue
        end_at = text_value.find(end, start_at) if end else len(text_value)
        body = text_value[start_at : end_at if end_at >= 0 else len(text_value)]
        handler = f"python_symbol:live_contentops/server.py::PipelineServerHandler.do_{method}"
        for route in sorted(set(re.findall(r'route\s*(?:==|!=)\s*[\'\"](/api/[^\'\"]+)', body))):
            node_id = f"http:{method} {route}"
            nodes.append({"id": node_id, "kind": "http_endpoint", "method": method, "route": route})
            edges.extend(
                [
                    {
                        "from": "live_contentops/server.py",
                        "to": node_id,
                        "kind": "defines_endpoint",
                        "inference": "server_route_guard_regex",
                    },
                    {
                        "from": node_id,
                        "to": handler,
                        "kind": "handled_by",
                        "inference": "server_method_scope",
                    },
                ]
            )
    return nodes, edges


class _ExactCallVisitor(ast.NodeVisitor):
    """Emit only calls with an exact local or explicit-import target."""

    def __init__(
        self,
        *,
        source: str,
        module: str,
        symbol_ids: set[str],
        imported_names: dict[str, tuple[str, str]],
        imported_modules: dict[str, str],
    ) -> None:
        self.source = source
        self.module = module
        self.symbol_ids = symbol_ids
        self.imported_names = imported_names
        self.imported_modules = imported_modules
        self.stack: list[str] = []
        self.calls: set[tuple[str, str]] = set()

    def _caller(self) -> str:
        if not self.stack:
            return self.source
        return f"python_symbol:{self.source}::{'.'.join(self.stack)}"

    def _target(self, node: ast.Call) -> str | None:
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name in self.imported_names:
                target_module, target_name = self.imported_names[name]
                target_path = target_module.replace(".", "/") + ".py"
                candidate = f"python_symbol:{target_path}::{target_name}"
                return candidate if candidate in self.symbol_ids else None
            target_path = self.module.replace(".", "/") + ".py"
            candidate = f"python_symbol:{target_path}::{name}"
            return candidate if candidate in self.symbol_ids else None
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            owner = node.func.value.id
            if owner == "self" and self.stack:
                class_name = self.stack[0]
                candidate = f"python_symbol:{self.source}::{class_name}.{node.func.attr}"
                return candidate if candidate in self.symbol_ids else None
            if owner in self.imported_modules:
                target_path = self.imported_modules[owner].replace(".", "/") + ".py"
                candidate = f"python_symbol:{target_path}::{node.func.attr}"
                return candidate if candidate in self.symbol_ids else None
        return None

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        target = self._target(node)
        if target:
            self.calls.add((self._caller(), target))
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()


def python_call_edges(path: Path, symbol_ids: set[str]) -> list[dict[str, str]]:
    tree = python_tree(path)
    module = python_module_name(rel(path))
    if tree is None or module is None:
        return []
    imported_names: dict[str, tuple[str, str]] = {}
    imported_modules: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for alias in node.names:
                if alias.name != "*":
                    imported_names[alias.asname or alias.name] = (node.module, alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules[alias.asname or alias.name.split(".")[0]] = alias.name
    visitor = _ExactCallVisitor(
        source=rel(path),
        module=module,
        symbol_ids=symbol_ids,
        imported_names=imported_names,
        imported_modules=imported_modules,
    )
    visitor.visit(tree)
    return [
        {
            "from": source,
            "to": target,
            "kind": "calls",
            "inference": "python_ast_exact_name_call",
        }
        for source, target in sorted(visitor.calls)
        if source in symbol_ids or source == rel(path)
    ]


def is_test_path(path: str) -> bool:
    return (
        path.startswith("tests/")
        or "/test/" in path
        or path.endswith(".test.tsx")
        or path.endswith(".test.ts")
    )


def test_relationships(path: Path, node_paths: set[str]) -> list[dict[str, str]]:
    source = rel(path)
    if not is_test_path(source):
        return []
    stem = path.stem
    stem = re.sub(r"\.test$", "", stem)
    if stem.startswith("test_"):
        stem = stem[5:]
    candidates = [
        f"live_contentops/{stem}.py",
        f"live_contentops/{stem}_v1.py",
        f"live_contentops/{stem}_v2.py",
        f"live_contentops/{stem}_v6.py",
        f"ui/contentops_v5/src/{stem}.ts",
        f"ui/contentops_v5/src/{stem}.tsx",
    ]
    matches = [candidate for candidate in candidates if candidate in node_paths]
    rows: list[dict[str, str]] = []
    for candidate in matches:
        rows.extend(
            [
                {
                    "from": source,
                    "to": candidate,
                    "kind": "tests",
                    "inference": "test_filename_convention",
                },
                {
                    "from": candidate,
                    "to": source,
                    "kind": "covered_by",
                    "inference": "test_filename_convention",
                },
            ]
        )
    return rows


def entrypoint_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: set[tuple[str, str, str]] = set()
    curated = {
        "live_contentops/cli.py": ("python -m live_contentops.cli", "canonical_cli"),
        "live_contentops/daily_app_launcher_v1.py": (
            "python -m live_contentops.daily_app_launcher_v1",
            "daily_app_launcher",
        ),
        "live_contentops/daily_app_supervisor_v1.py": (
            "ContentOpsDailyAppSupervisor",
            "daily_app_supervisor",
        ),
        "live_contentops/production_orchestrator_v1.py": (
            "ContentOpsProductionOrchestrator",
            "production_orchestrator",
        ),
        "live_contentops/tier2_video_factory_v1.py": (
            "python -m live_contentops.cli tier2-video-local",
            "tier2_local_factory",
        ),
        "ui/contentops_v5/src/main.tsx": (
            "npm run dev/build/test in ui/contentops_v5",
            "canonical_ui",
        ),
        "Start_ContentOps_Daily_App.cmd": (
            "Start_ContentOps_Daily_App.cmd",
            "one_click_launcher",
        ),
        "STOP_ALL_CONTENTOPS_BACKGROUND.cmd": (
            "STOP_ALL_CONTENTOPS_BACKGROUND.cmd",
            "one_click_emergency_stop",
        ),
        "RESUME_CONTENTOPS_LLM.cmd": (
            "RESUME_CONTENTOPS_LLM.cmd",
            "explicit_llm_resume",
        ),
    }
    for path in paths:
        source = rel(path)
        if source in curated:
            command, kind = curated[source]
            rows.add((source, command, kind))
        if path.suffix.lower() in {".cmd", ".bat", ".ps1"}:
            if source not in curated:
                rows.add((source, source, "operator_script"))
    return [
        {"path": path, "command_or_symbol": command, "kind": kind}
        for path, command, kind in sorted(rows)
    ]


def node_kind(path: str) -> str:
    if path == "AGENTS.md" or path.endswith("/AGENTS.md"):
        return "instructions"
    if path in AUTHORITY_DOCS:
        return "authority_doc"
    if is_test_path(path):
        return "test"
    suffix = Path(path).suffix.lower()
    if suffix == ".py":
        return "python_module"
    if suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
        return "typescript_or_javascript_module"
    return "manifest"


CURATED_RELATIONSHIPS: tuple[tuple[str, str, str], ...] = (
    ("Start_ContentOps_Daily_App.cmd", "scripts/Start-ContentOpsDailyApp.ps1", "entrypoint_to_implementation"),
    ("STOP_ALL_CONTENTOPS_BACKGROUND.cmd", "scripts/Stop-ContentOpsBackground.ps1", "entrypoint_to_implementation"),
    ("RESUME_CONTENTOPS_LLM.cmd", "scripts/Resume-ContentOpsLLM.ps1", "entrypoint_to_implementation"),
    ("scripts/Stop-ContentOpsBackground.ps1", "live_contentops/llm_operator_control_v1.py", "activates_operator_fuse_before_stop"),
    ("live_contentops/nine_router_llm_seam_v2.py", "live_contentops/llm_operator_control_v1.py", "enforces_operator_fuse"),
    ("live_contentops/nine_router_llm_seam_v2.py", "live_contentops/llm_cost_governor_v1.py", "enforces_cycle_and_daily_cost_budget"),
    ("scripts/Start-ContentOpsDailyApp.ps1", "live_contentops/daily_app_launcher_v1.py", "entrypoint_to_implementation"),
    ("live_contentops/daily_app_launcher_v1.py", "live_contentops/cli.py", "entrypoint_to_implementation"),
    ("live_contentops/cli.py", "live_contentops/daily_app_supervisor_v1.py", "entrypoint_to_implementation"),
    ("live_contentops/daily_app_supervisor_v1.py", "live_contentops/continuous_headline_ingest_v1.py", "supervises"),
    ("live_contentops/daily_app_supervisor_v1.py", "live_contentops/eight_platform_substack_first_pipeline_v1.py", "supervises"),
    ("live_contentops/daily_app_supervisor_v1.py", "live_contentops/publication_coordinator_v1.py", "owns_lifecycle_through"),
    ("live_contentops/eight_platform_substack_first_pipeline_v1.py", "live_contentops/production_orchestrator_v1.py", "facade_to_orchestrator"),
    ("live_contentops/production_orchestrator_v1.py", "live_contentops/_eight_platform_substack_first_pipeline_impl_v1.py", "orchestrator_to_implementation"),
    ("live_contentops/_eight_platform_substack_first_pipeline_impl_v1.py", "live_contentops/preselection_intelligence_v1.py", "newsroom_stage"),
    ("live_contentops/_eight_platform_substack_first_pipeline_impl_v1.py", "live_contentops/rolling_x_targeted_evidence_adapter_v1.py", "newsroom_stage"),
    ("live_contentops/_eight_platform_substack_first_pipeline_impl_v1.py", "live_contentops/rolling_x_grounded_article_media_builder_v1.py", "newsroom_stage"),
    ("live_contentops/publication_coordinator_v1.py", "live_contentops/destination_transport_registry_v1.py", "publication_transport_registry"),
    ("live_contentops/publication_coordinator_v1.py", "live_contentops/_eight_platform_substack_first_pipeline_impl_v1.py", "publication_transport_runtime"),
    ("ui/contentops_v5/src/views/DailyAppConsole.tsx", "http:GET /api/daily-app/snapshot", "ui_calls_endpoint"),
    ("ui/contentops_v5/src/views/DailyAppConsole.tsx", "http:POST /api/daily-app/control/run-now", "ui_calls_endpoint"),
    ("ui/contentops_v5/src/views/DailyAppConsole.tsx", "http:POST /api/daily-app/control/mode", "ui_calls_endpoint"),
    ("http:GET /api/daily-app/snapshot", "python_symbol:live_contentops/daily_app_ui_read_model_v1.py::build_daily_app_snapshot", "endpoint_to_read_model"),
    ("http:POST /api/daily-app/control/run-now", "python_symbol:live_contentops/daily_app_ui_read_model_v1.py::request_operator_cycle", "endpoint_to_read_model"),
    ("http:POST /api/daily-app/control/mode", "python_symbol:live_contentops/daily_app_ui_read_model_v1.py::update_daily_app_mode", "endpoint_to_read_model"),
)


def build_graph() -> dict[str, Any]:
    paths = source_files()
    node_paths = {rel(path) for path in paths}
    module_paths = {
        python_module_name(path): path
        for path in node_paths
        if python_module_name(path)
    }
    nodes: list[dict[str, Any]] = []
    for path in paths:
        source = rel(path)
        nodes.append(
            {"id": source, "kind": node_kind(source), "size_bytes": path.stat().st_size}
        )
    symbol_nodes: list[dict[str, Any]] = []
    metadata_edges: list[dict[str, str]] = []
    for path in paths:
        source = rel(path)
        if path.suffix == ".py":
            definitions = python_definitions(path)
            symbol_nodes.extend(definitions)
            metadata_edges.extend(
                {
                    "from": source,
                    "to": row["id"],
                    "kind": "defines",
                    "inference": "python_ast_definition",
                }
                for row in definitions
            )
            derived_nodes, derived_edges = python_metadata_nodes(path)
            symbol_nodes.extend(derived_nodes)
            metadata_edges.extend(derived_edges)
            endpoint_nodes, endpoint_edges = http_endpoint_nodes(path)
            symbol_nodes.extend(endpoint_nodes)
            metadata_edges.extend(endpoint_edges)
        elif path.suffix.lower() in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
            exports = typescript_export_nodes(path)
            symbol_nodes.extend(exports)
            metadata_edges.extend(
                {
                    "from": source,
                    "to": row["id"],
                    "kind": "defines",
                    "inference": "typescript_export_regex",
                }
                for row in exports
            )
    unique_symbol_nodes = {row["id"]: row for row in symbol_nodes}
    nodes.extend(unique_symbol_nodes.values())
    for source in sorted(path for path in node_paths if path == "AGENTS.md" or path.endswith("/AGENTS.md")):
        governed = "." if source == "AGENTS.md" else str(PurePosixPath(source).parent)
        directory_id = f"directory:{governed}"
        nodes.append({"id": directory_id, "kind": "directory_scope", "path": governed})
        metadata_edges.append(
            {
                "from": source,
                "to": directory_id,
                "kind": "governs",
                "inference": "agents_directory_scope",
            }
        )
    nodes = sorted({row["id"]: row for row in nodes}.values(), key=lambda row: row["id"])
    all_node_ids = {row["id"] for row in nodes}
    edges: list[dict[str, str]] = []
    for path in paths:
        if path.suffix == ".py":
            edges.extend(python_import_edges(path, module_paths))
            edges.extend(python_call_edges(path, all_node_ids))
        elif path.suffix.lower() in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
            edges.extend(ts_import_edges(path, node_paths))
        edges.extend(test_relationships(path, node_paths))
    # Exact test imports are stronger coverage evidence than filename similarity alone.
    for edge in list(edges):
        if edge["kind"] == "imports" and is_test_path(edge["from"]):
            edges.extend(
                [
                    {
                        "from": edge["from"],
                        "to": edge["to"],
                        "kind": "tests",
                        "inference": "test_exact_import",
                    },
                    {
                        "from": edge["to"],
                        "to": edge["from"],
                        "kind": "covered_by",
                        "inference": "test_exact_import",
                    },
                ]
            )
    edges.extend(metadata_edges)
    for source, target, kind in CURATED_RELATIONSHIPS:
        if source in all_node_ids and target in all_node_ids:
            edges.append(
                {
                    "from": source,
                    "to": target,
                    "kind": kind,
                    "inference": "curated_canonical_v1_relationship",
                }
            )
    # The canonical store owns every durable table in the embedded migration registry.
    durable_store = "live_contentops/durable_operational_store_v1.py"
    for node_id in sorted(node for node in all_node_ids if node.startswith("durable_table:")):
        edges.append(
            {
                "from": durable_store,
                "to": node_id,
                "kind": "state_owner",
                "inference": "curated_canonical_store_plus_embedded_migrations",
            }
        )
    edges = sorted(
        {
            (edge["from"], edge["to"], edge["kind"], edge.get("inference", "")): edge
            for edge in edges
        }.values(),
        key=lambda edge: (
            edge["from"], edge["to"], edge["kind"], edge.get("inference", "")
        ),
    )
    paths_digest = source_digest(paths)
    kind_counts: dict[str, int] = {}
    for node in nodes:
        kind_counts[node["kind"]] = kind_counts.get(node["kind"], 0) + 1
    inference_types = sorted({edge.get("inference", "unspecified") for edge in edges})
    return {
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "generation_timestamp_utc": git_commit_timestamp(),
        "source_head": git_head(),
        "source_tree_digest": paths_digest,
        "authority_anchor_paths": sorted(AUTHORITY_DOCS),
        "generated_outputs": sorted(GENERATED_PATHS),
        "included_roots": list(INCLUDED_ROOTS),
        "excluded_roots": list(EXCLUDED_ROOTS),
        "excluded_noise": sorted(EXCLUDED_PARTS | set(EXCLUDED_PREFIXES)),
        "inference_types": inference_types,
        "nodes": nodes,
        "edges": edges,
        "entrypoints": entrypoint_rows(paths),
        "protected_boundaries": [
            {"path": "v1.0", "status": "IMMUTABLE_PROTECTED_RELEASE"},
            {
                "path": "live_contentops/durable_operational_store_v1.py",
                "status": "CANONICAL_V1_STATE",
            },
            {
                "path": "live_contentops/production_orchestrator_v1.py",
                "status": "CANONICAL_V1_PRODUCTION_BOUNDARY",
            },
            {"path": "ui/contentops_v5/", "status": "CANONICAL_V1_UI"},
            {
                "path": "live_contentops/tier2_video_factory_v1.py",
                "status": "LOCAL_TIER2_AUTHORITY_NO_PUBLIC_WRITE",
            },
        ],
        "reference_only": {
            "branches": [
                {
                    "ref": "origin/task/tier2-b-remotion-multimodal-bakeoff-v1",
                    "status": "REJECTED_NOT_INDEXED_IN_MASTER",
                    "relationships": [
                        {
                            "from": "video/remotion/src/Root.tsx",
                            "to": "video/remotion/src/scenes/SceneRenderer.tsx",
                            "kind": "component",
                        },
                        {
                            "from": "video/remotion/src/Root.tsx",
                            "to": "video/remotion/src/program/types.ts",
                            "kind": "type_import",
                        },
                        {
                            "from": "video/remotion/src/scenes/SceneRenderer.tsx",
                            "to": "video/remotion/src/scenes/primitives.tsx",
                            "kind": "component_dispatch",
                        },
                        {
                            "from": "video/remotion/src/scenes/SceneRenderer.tsx",
                            "to": "video/remotion/src/scenes/scaffold.tsx",
                            "kind": "component_wrapper",
                        },
                        {
                            "from": "live_contentops/tier2_remotion_factory_v1.py",
                            "to": "video/remotion/scripts/render-job.mjs",
                            "kind": "renderer_target",
                        },
                    ],
                },
                {
                    "ref": "origin/task/tier2-image-generation-9router-contract-correction-v1",
                    "status": "REJECTED_NOT_INDEXED_IN_MASTER",
                    "relationships": [],
                },
            ]
        },
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges),
            "entrypoints": len(entrypoint_rows(paths)),
            "nodes_by_kind": dict(sorted(kind_counts.items())),
        },
    }


def context_markdown(graph: dict[str, Any]) -> str:
    counts = graph["counts"]
    return f"""# ContentOps Codex Context Map

Generated from source HEAD `{graph["source_head"]}`. Source tree digest: `{graph["source_tree_digest"]}`.
Run `python scripts/generate_codex_context_index.py --check` to determine staleness.

This map is descriptive repository state, not product authority. Jim's current direction and
the committed status/next-task documents remain authoritative.

## Accepted master capabilities

- Canonical V1 Daily App runtime, durable operational store, production orchestrator, router
  seam, bounded publication/readback/reconciliation, and canonical V5 UI.
- Tier2-A local renderer-neutral `VideoProgram` factory in
  `live_contentops/tier2_video_factory_v1.py`, with no provider/platform/public write.
- Current 9Router text/model authority in `live_contentops/nine_router_*_v2.py`.
- `TASK_CONTENTOPS_TIER2_DIRECT_IMAGE_API_REAL_SMOKE_AND_BAKEOFF_V1` accepted
  `PASS_WITH_CAVEAT` at `a859d5ff82707842f59163e4ec5150b22fbe6b0e`: the dedicated direct
  `https://ai.api-cheap.site/v1/images/generations` route using `AI_API_CHEAP_API_KEY` is
  proven end to end for `gpt-5.5`. Evidence:
  `docs/automation/CONTENTOPS_TIER2_DIRECT_IMAGE_API_REAL_SMOKE_AND_BAKEOFF_V1/README.md`.

## Rejected or unmerged experiments

- `task/tier2-b-remotion-multimodal-bakeoff-v1`: rejected visual product; reference only.
- `task/tier2-image-generation-9router-contract-correction-v1` at `8b043a5`: rejected; do not
  import its implementation or add `ai.api-cheap.site` to the generic 9Router adapter.

Reference-only Remotion relationships are recorded descriptively in `graph.json` but its source
files are not imported into master: `Root.tsx` composes `SceneRenderer`, `SceneRenderer`
dispatches to `primitives.tsx` inside `scaffold.tsx`, and the renderer-neutral Python factory
targets `render-job.mjs`.

## Current V2 free-form chapterized authority and route

- `gpt-5.5` is the provisional V2 generated-illustration default pending future product
  evidence; generated illustration is never factual or documentary authority.
- `wan2.7-image-pro` and `qwen-image-2.0` returned confirmed HTTP 400 responses on the tested
  contract and remain unresolved without blocking V2.
- The V2 free-form chapterized owner override, `NORTH_STAR_V2`, `MASTER_PLAN_V2`,
  `TASK_GRAPH_V2`, current V2 execution pointer, Remotion baseline, and fresh-session handoff
  are the canonical V2 product authority. Older V2 and V1 plan sets are historical where they
  conflict with this chain.
- The current task is
  `TASK_CONTENTOPS_V2_UNATTENDED_PRODUCTION_SOAK_WITH_TRANSCRIPT_VOICEOVER_SEO_HARDENING_V1`.
- `V2_CANONICAL_CREATIVE_RUNTIME = CODEX_DESKTOP_APP_FRESH_TASK_SESSION` remains the explicit
  governed creative-session boundary.
- The normal Codex Desktop App parent/task session uses `GPT-5.6 Sol / HIGH`; only consequential
  editorial/narration, timing-bound motion/visual authorship, actual-media review, and bounded
  same-video creative revision use fresh `GPT-5.6 Sol / Extra High (XHIGH)` work. Governed
  artifacts and checkpoints, not hidden chat memory, remain durable authority.
- `CODEX_CLI_NOT_V2_CREATIVE_AUTHORITY`: Codex CLI and `codex exec` are forbidden creative
  substitutes. `CODEX_SDK_API_NOT_V2_CREATIVE_AUTHORITY`: SDK/API/headless processes are also
  forbidden creative substitutes. If Desktop-App handoff is unavailable, report that boundary;
  never switch execution surfaces for convenience.
- `9ROUTER_RESEARCH_ONLY`: 9Router is research/evidence assistance only on
  `vx/gemini-3.1-pro-preview(high)` -> `vx/gemini-3.5-flash(high)`; Terra is excluded from this
  role, and all routes have zero V2 creative authority and zero factual, numeric, publication, or
  public-write authority.
- `CodexJobBrain` is a conceptual per-job boundary only; canonically it means
  `CodexDesktopSessionBrain`, not `CodexCliExecutor`, subprocess, SDK/API, provider adapter, or
  generic model route.
- Commit `622b19e1282d4fbd81fad47f76f399b97c454737`, `CodexCliExecutor`, and its failed
  `codex exec` proof are `NON_CANONICAL_FAILED_EXECUTION_SEAM / HISTORICAL EVIDENCE`. They prove
  only that the mistaken CLI seam failed, not that canonical Codex Desktop App execution failed.
- The accepted core proof implementation is `52c92ec1e097ef2441a2cb916132576c241b5def`, its evidence
  HEAD is `001ca4e7c2a06224d1d3e7c0d098b3d965376fc3`, and owner lineage
  `77d7ac16432415afcbb113596554d551cd4f0fb9` records
  `PASS_WITH_CAVEAT / CORE_PROOF_ACCEPTED_FOR_PRODUCTION_SOAK`. The current bounded soak processes
  up to three distinct qualified Shorts with no filler and hardens canonical transcript, Kokoro
  pronunciation/voice-over, locked-audio captions, transcript-derived SEO, asset-rich visuals,
  and multi-job isolation/cost truth. MAX/ULTRA and mode bakeoffs remain retired.
  Each job orders creative work as transcript/voice-over, visual needs, grounded web discovery,
  candidate board, rights-safe selection, then story-specific Remotion. The post-transcript asset
  selection is immutable and hash-bound to canonical transcript plus waveform timing before motion
  source lock; HIGH retains download, rights, hashing, sandbox, and deterministic QA authority.
  `MULTILINGUAL_CLOSED_INPUT` and `ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY` remain controlling.
- Remotion is deterministic execution, not creative authority. Viewer-facing source remains
  free-form React/Remotion code organized by semantic creative chapters. Chapters are not
  automatically render units, and deterministic aesthetic schemas/gates are forbidden.
- The rejected creative branch `task/tier2-v2-creative-system-rebuild-v1` at `d231b54e` is
  reference only: do not merge or continue its slideshow-heavy creative product.
- The rejected first retention-native attempt at `b6f50029` is also reference only; do not
  continue its repetitive creative grammar.
- Output is 1080-first with real authored audio/music, rights-aware assets, dirty-range review,
  chapter caching, stream-copy assembly, bounded XHIGH actual-media critique, and Jim/ChatGPT
  owner review. 4K is deferred/forbidden in the current contract. Virality is never guaranteed.
- V2 is isolated from V1 and has zero public-write authority.

## Subsystem map

| Subsystem | Entry files | Tests / evidence |
|---|---|---|
| V1 state/runtime | `live_contentops/durable_operational_store_v1.py`, `production_orchestrator_v1.py`, `daily_app_supervisor_v1.py` | `tests/test_durable_operational_store_v1.py`, `tests/test_daily_app_*` |
| 9Router | `live_contentops/nine_router_ordered_model_router_v2.py`, `nine_router_llm_seam_v2.py`, `nine_router_provider_adapter_v2.py` | `tests/test_nine_router_*`, `docs/automation/CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2/` |
| Tier2-A | `live_contentops/tier2_video_factory_v1.py` | `tests/test_tier2_video_factory_v1.py`, `docs/automation/CONTENTOPS_TIER2_A_PROGRAMMABLE_VIDEO_VERTICAL_SLICE_V1/` |
| Direct image | `live_contentops/direct_image_api_v1.py`, `scripts/run_direct_image_bakeoff_v1.py` | `tests/test_direct_image_api_v1.py`, `docs/automation/CONTENTOPS_TIER2_DIRECT_IMAGE_API_REAL_SMOKE_AND_BAKEOFF_V1/` |
| V2 durable control plane / non-canonical CLI experiment | `video/unattended_core_factory_v1/codex_job_brain.py`, `video/unattended_core_factory_v1/supervisor.py`, `video/unattended_core_factory_v1/store.py` | Control-plane substrate plus `NON_CANONICAL_FAILED_EXECUTION_SEAM / HISTORICAL EVIDENCE`; `tests/test_v2_unattended_core_factory_v1.py` |
| V2 free-form chapterized authority | `docs/automation/CONTENTOPS_V2_FREEFORM_CHAPTERIZED_HIGH_XHIGH_OWNER_OVERRIDE_V1.md`, `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_CURRENT_EXECUTION_POINTER_V2.md`, `docs/automation/CONTENTOPS_V2_FRESH_CHAT_HANDOFF_V1.md` | Free-form pipeline, V2 North Star, master plan, task graph, Remotion baseline, owner-polish evidence |
| UI | `ui/contentops_v5/src/main.tsx`, `ui/contentops_v5/src/views/DailyAppConsole.tsx`, `ui/contentops_v5/src/dailyAppTypes.ts` | `ui/contentops_v5/src/test/`, `ui/contentops_v5/AGENTS.md` |
| Tooling | `scripts/generate_codex_context_index.py` | `tests/test_codex_context_index.py` |

## Graph inventory

- Nodes: `{counts["nodes"]}`
- Edges: `{counts["edges"]}`
- Entrypoints: `{counts["entrypoints"]}`
- Python import edges, TypeScript/JavaScript relative import edges, and determinable test-to-
  implementation edges are included.
- Archives, runtime output, generated media, caches, vendor trees, and node_modules are excluded.
"""


def index_markdown(graph: dict[str, Any]) -> str:
    entrypoints = graph["entrypoints"]
    lines = [
        "# ContentOps Codex Entry Index",
        "",
        f"Source HEAD: `{graph['source_head']}`",
        f"Source tree digest: `{graph['source_tree_digest']}`",
        f"Graph schema: `{graph['schema_version']}`; generator: `{graph['generator_version']}`",
        "",
        "This generated map is descriptive, not product authority.",
        "",
        "## Fresh session",
        "",
        "Read only these before the exact task files:",
        "",
        "1. `AGENTS.md`",
        "2. `docs/codegraph/INDEX.md` (this page)",
        "3. nearest scoped `AGENTS.md`",
        "4. `docs/codegraph/V1_CONTEXT.md` when V1 product/state context matters",
        "5. exact implementation and focused tests",
        "",
        "Open current direction/next-task authority only when product direction matters: "
        "`docs/CURRENT_CONTEXT.md`, `docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md`, and "
        "`docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md`.",
        "",
        "## Entrypoints",
        "",
        "| Kind | Path | Command or symbol |",
        "|---|---|---|",
    ]
    lines.extend(
        f"| `{row['kind']}` | `{row['path']}` | `{row['command_or_symbol']}` |"
        for row in entrypoints
    )
    for heading, paths in HOT_PATHS.items():
        lines.extend(["", f"## {heading}", ""])
        lines.extend(f"- `{path}`" for path in paths)
    lines.extend(
        [
            "",
            "## Tests",
            "",
            "Use the focused test beside each hot-path section. Backend tests are under `tests/`; "
            "V5 tests are under `ui/contentops_v5/src/test/`. Generator coverage is "
            "`tests/test_codex_context_index.py`.",
            "",
            "## Current V1 closeout",
            "",
            "Accepted implementation: four-window / full-nine-surface / closed-loop branch "
            "`codex/v1-four-window-closed-loop-current-master-integration-v1`. Exactly four native "
            "Desktop `gpt-5.6-sol / HIGH` coordinator tasks already exist and are all `PAUSED`; do not create, "
            "recreate, enable, or add a fifth task.",
            "",
            "Current task: "
            "`TASK_CONTENTOPS_V1_HIGH_COORDINATOR_XHIGH_EDITORIAL_WORKER_ALIGNMENT_V1`. First "
            "fast-forward the accepted branch, synchronize the canonical checkout, and verify all "
            "nine readiness/identity states plus `UNKNOWN_WRITE=0`. Jim then runs exactly one fresh "
            "Desktop HIGH coordinator manual `GO` canary; it creates one fresh isolated XHIGH "
            "editorial worker only if an article is warranted. Only a Jim/ChatGPT audit PASS of the actual article "
            "and all nine public surfaces enables the existing four tasks. "
            "`V1_FINAL_PRODUCT_ACCEPTED` is forbidden before real evidence.",
            "",
            "## Tier2 separation",
            "",
            "Tier2/video is isolated from the V1 runtime and has no public-write authority. Read "
            "`docs/codegraph/V2_CONTEXT.md` and `video/AGENTS.md` only for an authorized V2 task. "
            "The retention-native authority set and accepted direct-image boundary are routed "
            "there; rejected Tier2-B, `8b043a5`, and creative branch `d231b54e` remain reference "
            "only.",
            "",
            "## Generated graph files",
            "",
            "- `docs/codegraph/graph.json`: machine nodes, edges, inference labels, metadata, and exclusions",
            "- `docs/codegraph/INDEX.md`: generated hot-path router",
            "- `docs/codegraph/V2_CONTEXT.md`: generated compact V2 separation map",
            "- `docs/codegraph/V1_CONTEXT.md`: curated, validated V1 product/decision/state map",
            "",
            "## Regeneration and check",
            "",
            "```text",
            "python scripts/generate_codex_context_index.py",
            "python scripts/generate_codex_context_index.py --check",
            "```",
            "",
            "## Scope",
            "",
            f"`{graph['counts']['nodes']}` nodes and `{graph['counts']['edges']}` edges cover files, "
            "Python symbols, TypeScript exports, tests, CLI commands, HTTP endpoints, durable "
            "tables, schemas, authority anchors, runtime entrypoints, and scoped instructions. "
            "Every inferred edge carries an `inference` label. Included/excluded roots are "
            "recorded in `graph.json`.",
            "",
        ]
    )
    return "\n".join(lines)


def build_outputs() -> dict[str, str]:
    graph = build_graph()
    return {
        rel(GRAPH_PATH): json.dumps(graph, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        rel(INDEX_PATH): index_markdown(graph),
        rel(V2_CONTEXT_PATH): context_markdown(graph),
    }


def normalized_for_check(path: str, value: str) -> str:
    if path.endswith("graph.json"):
        parsed = json.loads(value)
        parsed["source_head"] = "<HEAD>"
        parsed["generation_timestamp_utc"] = "<TIMESTAMP>"
        return json.dumps(parsed, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return re.sub(
        r"((?:source HEAD|Source HEAD)\s*:?\s*)`?[0-9a-f]+`?",
        r"\1`<HEAD>`",
        value,
        flags=re.IGNORECASE,
    )


def check_outputs() -> int:
    expected = build_outputs()
    missing: list[str] = []
    mismatched: list[str] = []
    for path, content in expected.items():
        target = ROOT / path
        if not target.exists():
            missing.append(path)
            continue
        if normalized_for_check(
            path, target.read_text(encoding="utf-8")
        ) != normalized_for_check(path, content):
            mismatched.append(path)
    if missing or mismatched:
        if missing:
            print("MISSING:" + ",".join(missing))
        if mismatched:
            print("STALE:" + ",".join(mismatched))
        return 1
    graph = json.loads(expected[rel(GRAPH_PATH)])
    errors = validate_graph(graph) + validate_context_contract(graph)
    if errors:
        print("INVALID:" + ",".join(errors))
        return 1
    print("CODEGRAPH_CURRENT")
    return 0


def validate_graph(graph: dict[str, Any]) -> list[str]:
    paths = {node["id"] for node in graph.get("nodes", [])}
    errors: list[str] = []
    for edge in graph.get("edges", []):
        if edge.get("from") not in paths:
            errors.append(f"missing_edge_source:{edge.get('from')}")
        if edge.get("to") not in paths:
            errors.append(f"missing_edge_target:{edge.get('to')}")
    for row in graph.get("entrypoints", []):
        if row.get("path") not in paths:
            errors.append(f"missing_entrypoint:{row.get('path')}")
    return errors


SECRET_SHAPED_RE = re.compile(
    r"(?i)(?:sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|"
    r"ghp_[A-Za-z0-9]{20,}|bearer\s+[A-Za-z0-9._-]{20,}|"
    r"discord(?:app)?\.com/api/webhooks/\d+/[A-Za-z0-9_-]+|"
    r"(?:cookie|session|authorization)\s*[:=]\s*[^\s`]{12,})"
)


def validate_context_contract(graph: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for path in sorted(set(AUTHORITY_DOCS) | {item for paths in HOT_PATHS.values() for item in paths}):
        if not (ROOT / path).exists():
            errors.append(f"missing_context_path:{path}")
    for scoped in ("AGENTS.md", "live_contentops/AGENTS.md", "headline_ingestion/AGENTS.md",
                   "ui/contentops_v5/AGENTS.md", "tests/AGENTS.md", "docs/AGENTS.md",
                   "scripts/AGENTS.md", "video/AGENTS.md"):
        if not (ROOT / scoped).is_file():
            errors.append(f"missing_scoped_agents:{scoped}")
    for output_path in (V1_CONTEXT_PATH, INDEX_PATH, GRAPH_PATH, V2_CONTEXT_PATH):
        if output_path.exists() and SECRET_SHAPED_RE.search(read_text(output_path)):
            errors.append(f"secret_shaped_content:{rel(output_path)}")
    if graph.get("schema_version") != SCHEMA_VERSION:
        errors.append("graph_schema_version_mismatch")
    if graph.get("generator_version") != GENERATOR_VERSION:
        errors.append("graph_generator_version_mismatch")
    if sorted(graph.get("authority_anchor_paths") or []) != sorted(AUTHORITY_DOCS):
        errors.append("authority_anchor_list_mismatch")
    return errors


def write_outputs() -> None:
    outputs = build_outputs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
    graph = json.loads(outputs[rel(GRAPH_PATH)])
    errors = validate_graph(graph) + validate_context_contract(graph)
    if errors:
        raise SystemExit("INVALID_GRAPH:" + ",".join(errors))
    print(
        json.dumps(
            {
                "status": "GENERATED",
                **graph["counts"],
                "source_head": graph["source_head"],
            },
            sort_keys=True,
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="check generated files without writing"
    )
    args = parser.parse_args(argv)
    if args.check:
        return check_outputs()
    write_outputs()
    return 0


if __name__ == "__main__":
    sys.exit(main())
