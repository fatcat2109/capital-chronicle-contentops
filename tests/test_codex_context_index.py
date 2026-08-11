"""Focused validation for the deterministic Codex context generator."""

from pathlib import Path

from scripts import generate_codex_context_index as index


def test_generated_outputs_are_deterministic_without_clock_or_randomness():
    first = index.build_outputs()
    second = index.build_outputs()
    assert first == second
    assert first[index.rel(index.GRAPH_PATH)].count('"source_head"') == 1


def test_graph_edges_and_entrypoints_resolve_to_indexed_nodes():
    graph = index.build_graph()
    assert index.validate_graph(graph) == []
    paths = {node["id"] for node in graph["nodes"]}
    assert "live_contentops/cli.py" in paths
    assert "live_contentops/tier2_video_factory_v1.py" in paths
    assert graph["counts"]["nodes"] == len(paths)
    assert graph["counts"]["edges"] == len(graph["edges"])


def test_scoped_agents_cover_backend_video_ui_and_docs():
    assert (
        index.nearest_agents_file("live_contentops/tier2_video_factory_v1.py")
        == "live_contentops/AGENTS.md"
    )
    # The future renderer path is intentionally covered even though master has no renderer code.
    assert index.nearest_agents_file("video/remotion/src/Root.tsx") == "video/AGENTS.md"
    assert (
        index.nearest_agents_file("ui/contentops_v5/src/main.tsx")
        == "ui/contentops_v5/AGENTS.md"
    )
    assert (
        index.nearest_agents_file("docs/status/CURRENT_PROJECT_STATUS.md")
        == "docs/AGENTS.md"
    )


def test_generated_index_has_accepted_direct_image_authority_and_fresh_v2_route():
    context = Path(index.V2_CONTEXT_PATH).read_text(encoding="utf-8")
    normalized = " ".join(context.split())
    assert "TASK_CONTENTOPS_TIER2_DIRECT_IMAGE_API_REAL_SMOKE_AND_BAKEOFF_V1" in normalized
    assert "PASS_WITH_CAVEAT" in normalized
    assert "https://ai.api-cheap.site/v1/images/generations" in normalized
    assert "AI_API_CHEAP_API_KEY" in normalized
    assert "gpt-5.5" in normalized
    assert "provisional V2 generated-illustration default" in normalized
    assert "confirmed HTTP 400" in normalized
    assert "fresh V2 creative-system rebuild" in normalized
    assert "zero public-write authority" in normalized
    assert "LOCAL_9ROUTER_IMAGE_REGISTRY_AND_ROUTE_NOT_YET_PROVEN_END_TO_END" not in normalized
    assert "8b043a5" in normalized
    assert "do not import" in normalized


def test_source_scope_excludes_history_and_generated_outputs():
    paths = {index.rel(path) for path in index.source_files()}
    assert not any(path.startswith("docs/archive/") for path in paths)
    assert not any(path.startswith("docs/codegraph/") for path in paths)
    assert not any("node_modules" in path for path in paths)
