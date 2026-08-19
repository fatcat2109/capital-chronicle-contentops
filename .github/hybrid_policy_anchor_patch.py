from pathlib import Path

POLICY = "docs/automation/CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md"
GENERATOR_PATH = Path("scripts/generate_codex_context_index.py")
TESTS_PATH = Path("tests/test_codex_context_index.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one target, found {count}")
    return text.replace(old, new, 1)


generator = GENERATOR_PATH.read_text(encoding="utf-8")
tests = TESTS_PATH.read_text(encoding="utf-8")

generator = replace_once(
    generator,
    'GENERATOR_VERSION = "2.3.0"',
    'GENERATOR_VERSION = "2.4.0"',
    "generator_version",
)
generator = replace_once(
    generator,
    '    "docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md",\n'
    '    "docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md",',
    '    "docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md",\n'
    f'    "{POLICY}",\n'
    '    "docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md",',
    "authority_docs",
)
generator = replace_once(
    generator,
    """3. `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`
4. `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
5. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`
6. this V2 map or curated `docs/codegraph/V1_CONTEXT.md`
7. the appropriate current lane pointer
8. the nearest scoped `AGENTS.md`
9. exact implementation, tests, and evidence""",
    """3. `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`
4. `docs/automation/CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md`
5. `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
6. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`
7. this V2 map or curated `docs/codegraph/V1_CONTEXT.md`
8. the appropriate current lane pointer
9. the nearest scoped `AGENTS.md`
10. exact implementation, tests, and evidence""",
    "v2_context_read_path",
)
generator = replace_once(
    generator,
    """        "3. `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`",
        "4. `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`",
        "5. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`",
        "6. `docs/codegraph/V1_CONTEXT.md` or `docs/codegraph/V2_CONTEXT.md`",
        "7. the appropriate current V1/V2 lane pointer",
        "8. nearest scoped `AGENTS.md`",
        "9. exact implementation, focused tests, and task evidence",""",
    """        "3. `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`",
        "4. `docs/automation/CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md`",
        "5. `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`",
        "6. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`",
        "7. `docs/codegraph/V1_CONTEXT.md` or `docs/codegraph/V2_CONTEXT.md`",
        "8. the appropriate current V1/V2 lane pointer",
        "9. nearest scoped `AGENTS.md`",
        "10. exact implementation, focused tests, and task evidence",""",
    "index_read_path",
)
generator = replace_once(
    generator,
    '        "docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md",\n'
    '        "docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md",',
    '        "docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md",\n'
    f'        "{POLICY}",\n'
    '        "docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md",',
    "required_authority_anchors",
)

tests = replace_once(
    tests,
    '    assert "CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md" in generated\n'
    '    assert "CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md" in generated',
    '    assert "CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md" in generated\n'
    '    assert "CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md" in generated\n'
    '    assert "CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md" in generated',
    "index_policy_assertion",
)
tests = replace_once(
    tests,
    '    assert "CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md" in normalized\n'
    '    assert "CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md" in normalized',
    '    assert "CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md" in normalized\n'
    '    assert "CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md" in normalized\n'
    '    assert "CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md" in normalized',
    "context_policy_assertion",
)
tests = replace_once(
    tests,
    'def test_context_contract_paths_exist_and_outputs_have_no_secret_shapes(graph):\n'
    '    assert index.validate_context_contract(graph) == []',
    'def test_context_contract_paths_exist_and_outputs_have_no_secret_shapes(graph):\n'
    '    assert index.validate_context_contract(graph) == []\n'
    f'    assert "{POLICY}" in graph["authority_anchor_paths"]',
    "graph_policy_anchor_assertion",
)

GENERATOR_PATH.write_text(generator, encoding="utf-8", newline="\n")
TESTS_PATH.write_text(tests, encoding="utf-8", newline="\n")
