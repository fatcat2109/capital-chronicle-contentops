"""Focused validation for the deterministic Codex context generator."""

import json

import pytest

from scripts import generate_codex_context_index as index


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


def test_check_normalization_ignores_source_hash_in_index_and_context_forms():
    first = "Source HEAD: `" + "a" * 40 + "`\nGenerated from source HEAD `" + "a" * 40 + "`."
    second = "Source HEAD: `" + "b" * 40 + "`\nGenerated from source HEAD `" + "b" * 40 + "`."
    assert index.normalized_for_check("docs/codegraph/V2_CONTEXT.md", first) == index.normalized_for_check(
        "docs/codegraph/V2_CONTEXT.md", second
    )


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
        "Current V1 closeout",
        "Tier2 separation",
        "Generated graph files",
        "Regeneration and check",
    ):
        assert f"## {heading}" in generated
    assert "Exactly four native" in generated
    assert "all `PAUSED`" in generated
    assert "exactly one fresh Desktop XHIGH manual `GO` canary" in generated
    assert "all nine public surfaces enables the existing four tasks" in generated
    assert "`V1_FINAL_PRODUCT_ACCEPTED` is forbidden" in generated
    assert "TASK_CONTENTOPS_V1_FINAL_AUTHORITY_CLOSEOUT_AND_SINGLE_CANARY_GATE_PREP_V1" in generated


def test_generated_v2_context_routes_direct_image_and_retention_native_authority(graph):
    context = index.context_markdown(graph)
    normalized = " ".join(context.split())
    assert "TASK_CONTENTOPS_TIER2_DIRECT_IMAGE_API_REAL_SMOKE_AND_BAKEOFF_V1" in normalized
    assert "PASS_WITH_CAVEAT" in normalized
    assert "https://ai.api-cheap.site/v1/images/generations" in normalized
    assert "AI_API_CHEAP_API_KEY" in normalized
    assert "gpt-5.5" in normalized
    assert "provisional V2 generated-illustration default" in normalized
    assert "confirmed HTTP 400" in normalized
    assert "TASK_CONTENTOPS_V2_FREEFORM_CHAPTERIZED_HIGH_COORDINATOR_XHIGH_CREATIVE_OWNER_POLISH_V1" in normalized
    assert "GPT-5.6 Sol HIGH" in normalized
    assert "GPT-5.6 Sol XHIGH" in normalized
    assert "MAX/ULTRA and mode bakeoffs are retired" in normalized
    assert "free-form React/Remotion code" in normalized
    assert "NORTH_STAR_V2" in normalized
    assert "d231b54e" in normalized
    assert "b6f50029" in normalized
    assert "zero public-write authority" in normalized
    assert "LOCAL_9ROUTER_IMAGE_REGISTRY_AND_ROUTE_NOT_YET_PROVEN_END_TO_END" not in normalized
    assert "8b043a5" in normalized
    assert "do not import" in normalized


def test_context_contract_paths_exist_and_outputs_have_no_secret_shapes(graph):
    assert index.validate_context_contract(graph) == []
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
