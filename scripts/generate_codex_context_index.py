#!/usr/bin/env python3
"""Generate a small deterministic Codex repository graph and V2 entry map.

The output is descriptive repository state, not product authority. The generator uses only the
Python standard library and a small set of syntax/manifest readers; it intentionally excludes
archives, runtime data, vendor trees, and generated media.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs" / "codegraph"
GRAPH_PATH = OUTPUT_DIR / "graph.json"
INDEX_PATH = OUTPUT_DIR / "INDEX.md"
V2_CONTEXT_PATH = OUTPUT_DIR / "V2_CONTEXT.md"
SCHEMA_VERSION = "contentops.codex_context_graph.v1"

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
    "docs/automation/CONTENTOPS_TIER2_PRO_VIDEO_FACTORY_NORTH_STAR_V1.md",
    "docs/automation/CONTENTOPS_TIER2_PRO_VIDEO_FACTORY_MASTER_PLAN_V1.md",
}
GENERATED_PATHS = {
    "docs/codegraph/graph.json",
    "docs/codegraph/INDEX.md",
    "docs/codegraph/V2_CONTEXT.md",
}
EXCLUDED_PARTS = {
    ".git",
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
}
EXCLUDED_PREFIXES = (
    "docs/archive/",
    "docs/automation/VIDEO_FOUNDATION_AND_PAUSE_V1/",
)


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
    if any(part in EXCLUDED_PARTS for part in PurePosixPath(relative).parts):
        return False
    return (
        path.suffix.lower() in CODE_SUFFIXES
        or path.name in MANIFEST_NAMES
        or relative in AUTHORITY_DOCS
        or path.name == "AGENTS.md"
    )


def source_files() -> list[Path]:
    paths = [path for path in ROOT.rglob("*") if path.is_file() and included(path)]
    return sorted(paths, key=rel)


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
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
        {"from": rel(path), "to": target, "kind": kind}
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
        {"from": source, "to": target, "kind": "imports"} for target in sorted(edges)
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
    return [{"from": source, "to": candidate, "kind": "tests"} for candidate in matches]


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


def build_graph() -> dict[str, Any]:
    paths = source_files()
    node_paths = {rel(path) for path in paths}
    module_paths = {
        python_module_name(path): path
        for path in node_paths
        if python_module_name(path)
    }
    nodes = []
    for path in paths:
        source = rel(path)
        nodes.append(
            {"id": source, "kind": node_kind(source), "size_bytes": path.stat().st_size}
        )
    edges: list[dict[str, str]] = []
    for path in paths:
        if path.suffix == ".py":
            edges.extend(python_import_edges(path, module_paths))
        elif path.suffix.lower() in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
            edges.extend(ts_import_edges(path, node_paths))
        edges.extend(test_relationships(path, node_paths))
    edges = sorted(
        {(edge["from"], edge["to"], edge["kind"]): edge for edge in edges}.values(),
        key=lambda edge: (edge["from"], edge["to"], edge["kind"]),
    )
    paths_digest = source_digest(paths)
    return {
        "schema_version": SCHEMA_VERSION,
        "source_head": git_head(),
        "source_tree_digest": paths_digest,
        "generated_outputs": sorted(GENERATED_PATHS),
        "excluded_noise": sorted(EXCLUDED_PARTS | set(EXCLUDED_PREFIXES)),
        "scope_roots": [
            "live_contentops/",
            "tests/",
            "ui/contentops_v5/",
            "scripts/",
            "docs/authority files",
            "AGENTS hierarchy",
        ],
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

## Rejected or unmerged experiments

- `task/tier2-b-remotion-multimodal-bakeoff-v1`: rejected visual product; reference only.
- `task/tier2-image-generation-9router-contract-correction-v1` at `8b043a5`: rejected direct
  `ai.api-cheap.site` image transport; do not import it.

Reference-only Remotion relationships are recorded descriptively in `graph.json` but its source
files are not imported into master: `Root.tsx` composes `SceneRenderer`, `SceneRenderer`
dispatches to `primitives.tsx` inside `scaffold.tsx`, and the renderer-neutral Python factory
targets `render-job.mjs`.

## Current V2 blocker and route

`LOCAL_9ROUTER_IMAGE_REGISTRY_AND_ROUTE_NOT_YET_PROVEN_END_TO_END`.

Next main action: `TIER2_LOCAL_9ROUTER_IMAGE_ROUTE_CORRECTION_AND_REAL_BAKEOFF`.
Only after that should a fresh V2 creative rebuild address story selection, nonnumeric
narration, premium typography, richer motion, and a later rights-aware real-person/entity
resolver. No video public-write authority exists.

## Subsystem map

| Subsystem | Entry files | Tests / evidence |
|---|---|---|
| V1 state/runtime | `live_contentops/durable_operational_store_v1.py`, `production_orchestrator_v1.py`, `daily_app_supervisor_v1.py` | `tests/test_durable_operational_store_v1.py`, `tests/test_daily_app_*` |
| 9Router | `live_contentops/nine_router_ordered_model_router_v2.py`, `nine_router_llm_seam_v2.py`, `nine_router_provider_adapter_v2.py` | `tests/test_nine_router_*`, `docs/automation/CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2/` |
| Tier2-A | `live_contentops/tier2_video_factory_v1.py` | `tests/test_tier2_video_factory_v1.py`, `docs/automation/CONTENTOPS_TIER2_A_PROGRAMMABLE_VIDEO_VERTICAL_SLICE_V1/` |
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
        "",
        "This is a generated descriptive map. Check freshness with:",
        "",
        "```text",
        "python scripts/generate_codex_context_index.py --check",
        "```",
        "",
        "Start with the nearest scoped instructions, then use the context map and graph:",
        "",
        "- root contract: `AGENTS.md`",
        "- backend: `live_contentops/AGENTS.md`",
        "- renderer/future V2: `video/AGENTS.md`",
        "- canonical UI: `ui/contentops_v5/AGENTS.md`",
        "- authority/generated docs: `docs/AGENTS.md`",
        "- V2 map: `docs/codegraph/V2_CONTEXT.md`",
        "- machine graph: `docs/codegraph/graph.json`",
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
    lines.extend(
        [
            "",
            "## Authority anchors",
            "",
            "- Current direction: `docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md`",
            "- Current context: `docs/CURRENT_CONTEXT.md`",
            "- Next task pointer: `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md`",
            "- Tier-2 authority: `docs/automation/CONTENTOPS_TIER2_PRO_VIDEO_FACTORY_NORTH_STAR_V1.md` and `...MASTER_PLAN_V1.md`",
            "",
            "## Scope",
            "",
            f"`{graph['counts']['nodes']}` nodes and `{graph['counts']['edges']}` edges are generated from Python, TypeScript/JavaScript, manifests, authority files, and the scoped AGENTS hierarchy. Noise exclusions are recorded in `graph.json`.",
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
        return json.dumps(parsed, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return re.sub(
        r"(source HEAD|Source HEAD): `?[0-9a-f]+`?",
        r"\1: `<HEAD>`",
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


def write_outputs() -> None:
    outputs = build_outputs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
    graph = json.loads(outputs[rel(GRAPH_PATH)])
    errors = validate_graph(graph)
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
