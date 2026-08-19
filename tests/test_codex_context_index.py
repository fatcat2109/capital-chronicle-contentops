"""Focused validation for the deterministic Codex context generator."""

import json
import subprocess
from pathlib import Path

import pytest

from scripts import generate_codex_context_index as index


def _git(repo: Path, *args: str, input_text: str | None = None, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        input=input_text,
        text=True,
        capture_output=True,
        check=check,
    )
    return result.stdout.strip()


def _init_git_repo(repo: Path) -> None:
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "CodeGraph Test")
    _git(repo, "config", "user.email", "codegraph-test@example.invalid")


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", "--all")
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture(scope="module")
def graph():
    return index.build_graph()


def test_generated_outputs_are_deterministic_without_clock_or_randomness(graph):
    assert index.index_markdown(graph) == index.index_markdown(graph)
    assert index.context_markdown(graph) == index.context_markdown(graph)
    assert json.dumps(graph, sort_keys=True) == json.dumps(graph, sort_keys=True)
    assert graph["schema_version"] == index.SCHEMA_VERSION
    assert graph["generator_version"] == index.GENERATOR_VERSION
    assert graph["generation_timestamp_utc"]


def test_check_normalization_preserves_source_epoch_truth():
    first = "Source HEAD: `" + "a" * 40 + "`\nGenerated from source HEAD `" + "a" * 40 + "`."
    second = "Source HEAD: `" + "b" * 40 + "`\nGenerated from source HEAD `" + "b" * 40 + "`."
    assert index.normalized_for_check("docs/codegraph/V2_CONTEXT.md", first) != index.normalized_for_check(
        "docs/codegraph/V2_CONTEXT.md", second
    )


def test_git_head_resolves_tree_identical_merge_through_matching_parent(monkeypatch, tmp_path):
    repo = tmp_path / "tree-identical-merge"
    _init_git_repo(repo)
    source = repo / "live_contentops" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    base = _commit_all(repo, "base source")

    _git(repo, "checkout", "-b", "left")
    (repo / "README.md").write_text("left-only history\n", encoding="utf-8")
    left = _commit_all(repo, "left non-indexed change")

    _git(repo, "checkout", "-b", "right", base)
    source.write_text("VALUE = 2\n", encoding="utf-8")
    right = _commit_all(repo, "right source change")
    right_tree = _git(repo, "rev-parse", f"{right}^{{tree}}")
    merge = _git(
        repo,
        "commit-tree",
        right_tree,
        "-p",
        left,
        "-p",
        right,
        input_text="tree-identical merge\n",
    )
    _git(repo, "checkout", "--detach", merge)

    monkeypatch.setattr(index, "ROOT", repo)
    assert _git(repo, "rev-parse", f"{merge}^{{tree}}") == _git(
        repo, "rev-parse", f"{right}^{{tree}}"
    )
    assert index.git_head() == right


def test_git_head_keeps_merge_with_real_source_resolution(monkeypatch, tmp_path):
    repo = tmp_path / "source-resolution-merge"
    _init_git_repo(repo)
    source = repo / "live_contentops" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 'base'\n", encoding="utf-8")
    base = _commit_all(repo, "base source")

    _git(repo, "checkout", "-b", "left")
    source.write_text("VALUE = 'left'\n", encoding="utf-8")
    left = _commit_all(repo, "left source change")

    _git(repo, "checkout", "-b", "right", base)
    source.write_text("VALUE = 'right'\n", encoding="utf-8")
    right = _commit_all(repo, "right source change")

    _git(repo, "checkout", "left")
    merge_result = subprocess.run(
        ["git", "merge", "--no-ff", "right", "-m", "source resolution merge"],
        cwd=repo,
        text=True,
        capture_output=True,
    )
    assert merge_result.returncode != 0
    source.write_text("VALUE = 'resolved'\n", encoding="utf-8")
    merge = _commit_all(repo, "resolve source conflict")

    monkeypatch.setattr(index, "ROOT", repo)
    merge_tree = _git(repo, "rev-parse", f"{merge}^{{tree}}")
    assert merge_tree != _git(repo, "rev-parse", f"{left}^{{tree}}")
    assert merge_tree != _git(repo, "rev-parse", f"{right}^{{tree}}")
    assert index.git_head() == merge


def test_git_head_skips_generated_only_commit_to_source_epoch(monkeypatch, tmp_path):
    repo = tmp_path / "generated-only"
    _init_git_repo(repo)
    source = repo / "live_contentops" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    source_epoch = _commit_all(repo, "source epoch")

    generated = repo / "docs" / "codegraph" / "INDEX.md"
    generated.parent.mkdir(parents=True)
    generated.write_text("generated\n", encoding="utf-8")
    _commit_all(repo, "generated only")

    monkeypatch.setattr(index, "ROOT", repo)
    assert index.git_head() == source_epoch


def test_git_head_handles_root_commits_without_manufacturing_an_epoch(monkeypatch, tmp_path):
    source_repo = tmp_path / "source-root"
    _init_git_repo(source_repo)
    source = source_repo / "live_contentops" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    source_root = _commit_all(source_repo, "source root")
    monkeypatch.setattr(index, "ROOT", source_repo)
    assert index.git_head() == source_root

    generated_repo = tmp_path / "generated-root"
    _init_git_repo(generated_repo)
    generated = generated_repo / "docs" / "codegraph" / "INDEX.md"
    generated.parent.mkdir(parents=True)
    generated.write_text("generated\n", encoding="utf-8")
    _commit_all(generated_repo, "generated root")
    monkeypatch.setattr(index, "ROOT", generated_repo)
    assert index.git_head() == "UNKNOWN"


def test_graph_edges_entrypoints_and_inference_resolve_to_nodes(graph):
    assert index.validate_graph(graph) == []
    node_ids = {node["id"] for node in graph["nodes"]}
    assert "live_contentops/cli.py" in node_ids
    assert "live_contentops/daily_app_supervisor_v1.py" in node_ids
    assert "python_symbol:live_contentops/publication_coordinator_v1.py::DurablePublicationCoordinator" in node_ids
    assert "typescript_export:ui/contentops_v5/src/views/DailyAppConsole.tsx::DailyAppConsole" in node_ids
    assert "http:GET /api/daily-app/snapshot" in node_ids
    assert "durable_table:operating_controls" in node_ids
    assert any(node["kind"] == "cli_command" for node in graph["nodes"])
    assert any(node["kind"] == "schema" for node in graph["nodes"])
    assert all(edge.get("inference") for edge in graph["edges"])
    assert graph["counts"]["nodes"] == len(node_ids)
    assert graph["counts"]["edges"] == len(graph["edges"])


def test_canonical_relationships_cover_v1_runtime_publication_and_ui(graph):
    relationships = {
        (edge["from"], edge["to"], edge["kind"])
        for edge in graph["edges"]
    }
    assert (
        "live_contentops/daily_app_supervisor_v1.py",
        "live_contentops/continuous_headline_ingest_v1.py",
        "supervises",
    ) in relationships
    assert (
        "live_contentops/eight_platform_substack_first_pipeline_v1.py",
        "live_contentops/production_orchestrator_v1.py",
        "facade_to_orchestrator",
    ) in relationships
    assert (
        "live_contentops/publication_coordinator_v1.py",
        "live_contentops/destination_transport_registry_v1.py",
        "publication_transport_registry",
    ) in relationships
    assert (
        "ui/contentops_v5/src/views/DailyAppConsole.tsx",
        "http:GET /api/daily-app/snapshot",
        "ui_calls_endpoint",
    ) in relationships


def test_scoped_agents_cover_every_major_implementation_scope():
    expected = {
        "live_contentops/tier2_video_factory_v1.py": "live_contentops/AGENTS.md",
        "headline_ingestion/Data_Ingestion.py": "headline_ingestion/AGENTS.md",
        "video/remotion/src/Root.tsx": "video/AGENTS.md",
        "ui/contentops_v5/src/main.tsx": "ui/contentops_v5/AGENTS.md",
        "tests/test_codex_context_index.py": "tests/AGENTS.md",
        "docs/status/CURRENT_PROJECT_STATUS.md": "docs/AGENTS.md",
        "scripts/generate_codex_context_index.py": "scripts/AGENTS.md",
    }
    for path, agents in expected.items():
        assert index.nearest_agents_file(path) == agents


def test_generated_index_routes_v1_hot_paths_and_separates_v2(graph):
    generated = index.index_markdown(graph)
    for heading in (
        "Fresh session",
        "V1 live runtime",
        "Newsroom / intake",
        "Capital Chronicle integration",
        "Evidence",
        "Article / media",
        "Publication / readback",
        "V5",
        "Router / models",
        "Tests",
        "Current authority routing",
        "Tier2 separation",
        "Generated graph files",
        "Regeneration and check",
    ):
        assert f"## {heading}" in generated
    assert "CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md" in generated
    assert "CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md" in generated
    assert "CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md" in generated
    assert "CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md" in generated
    assert "CONTENTOPS_FINAL_DAILY_APP_V1_CURRENT_EXECUTION_POINTER_V3.md" in generated
    assert "V6_FINAL_PRODUCT_EXECUTION_PLAN" not in generated
    assert "TASK_CONTENTOPS_V1_HIGH_COORDINATOR_XHIGH_EDITORIAL_WORKER_ALIGNMENT_V1" not in generated


def test_generated_v2_context_routes_through_current_v3_authority(graph):
    context = index.context_markdown(graph)
    normalized = " ".join(context.split())
    assert "CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md" in normalized
    assert "CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md" in normalized
    assert "CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md" in normalized
    assert "CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md" in normalized
    assert "CONTENTOPS_FINAL_DAILY_APP_V1_CURRENT_EXECUTION_POINTER_V3.md" in normalized
    assert "CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_CURRENT_EXECUTION_POINTER_V2.md" in normalized
    assert "zero video public-write authority" in normalized
    assert "V6_FINAL_PRODUCT_EXECUTION_PLAN" not in normalized
    assert "TASK_CONTENTOPS_V2_FREEFORM_CHAPTERIZED_HIGH_COORDINATOR_XHIGH_CREATIVE_OWNER_POLISH_V1" not in normalized


def test_context_contract_paths_exist_and_outputs_have_no_secret_shapes(graph):
    assert index.validate_context_contract(graph) == []
    assert "docs/automation/CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md" in graph["authority_anchor_paths"]
    for paths in index.HOT_PATHS.values():
        assert all((index.ROOT / path).exists() for path in paths)
    for path in (index.V1_CONTEXT_PATH, index.INDEX_PATH, index.GRAPH_PATH, index.V2_CONTEXT_PATH):
        if path.exists():
            assert index.SECRET_SHAPED_RE.search(path.read_text(encoding="utf-8")) is None


def test_relevant_file_and_scoped_agents_changes_change_digest(monkeypatch, tmp_path):
    root = tmp_path / "repo"
    code = root / "live_contentops" / "relevant.py"
    agents = root / "live_contentops" / "AGENTS.md"
    code.parent.mkdir(parents=True)
    code.write_text("VALUE = 1\n", encoding="utf-8")
    agents.write_text("scope v1\n", encoding="utf-8")
    monkeypatch.setattr(index, "ROOT", root)
    before = index.source_digest(index.source_files())
    code.write_text("VALUE = 2\n", encoding="utf-8")
    after_code = index.source_digest(index.source_files())
    agents.write_text("scope v2\n", encoding="utf-8")
    after_agents = index.source_digest(index.source_files())
    assert before != after_code != after_agents


def test_runtime_raw_data_and_cache_changes_do_not_change_digest(monkeypatch, tmp_path):
    root = tmp_path / "repo"
    code = root / "live_contentops" / "relevant.py"
    runtime = root / "Runtime" / "output.json"
    raw = root / "headline_ingestion" / "data" / "raw_archive" / "raw.json"
    cache = root / "ui" / "contentops_v5" / "node_modules" / "cache.js"
    task_runtime = root / ".task-runtime" / "job" / ".venv" / "Lib" / "vendor.py"
    code.parent.mkdir(parents=True)
    runtime.parent.mkdir(parents=True)
    raw.parent.mkdir(parents=True)
    cache.parent.mkdir(parents=True)
    task_runtime.parent.mkdir(parents=True)
    code.write_text("VALUE = 1\n", encoding="utf-8")
    runtime.write_text("one", encoding="utf-8")
    raw.write_text("one", encoding="utf-8")
    cache.write_text("one", encoding="utf-8")
    task_runtime.write_text("one", encoding="utf-8")
    monkeypatch.setattr(index, "ROOT", root)
    before = index.source_digest(index.source_files())
    runtime.write_text("two", encoding="utf-8")
    raw.write_text("two", encoding="utf-8")
    cache.write_text("two", encoding="utf-8")
    task_runtime.write_text("two", encoding="utf-8")
    assert index.source_digest(index.source_files()) == before


def test_source_scope_excludes_history_data_and_generated_outputs():
    paths = {index.rel(path) for path in index.source_files()}
    assert not any(path.startswith("docs/archive/") for path in paths)
    assert not any(path.startswith("headline_ingestion/data/raw_archive/") for path in paths)
    assert not any(path.startswith("headline_ingestion/data/intake/headline_sidecars/") for path in paths)
    assert not any(path in index.GENERATED_PATHS for path in paths)
    assert not any("node_modules" in path for path in paths)
    assert not any(path.startswith(".task-runtime/") for path in paths)
    assert not any("/.venv/" in path or path.startswith(".venv/") for path in paths)
    assert "docs/codegraph/V1_CONTEXT.md" in paths
