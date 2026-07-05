"""Deterministic validation of the Operator Cockpit V4 blueprint docs (0174D).

No-code task gate: these tests assert that the four blueprint docs exist and
contain concrete V4 requirements. They are intentionally non-superficial and will
fail if the docs omit required north-star concepts, the V3 rejection, the
target-capture verification, or the no-runtime-code constraint.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, "docs")

GAP_MAP = os.path.join(DOCS, "TASK_CONTENTOPS_0174D_V4_NORTH_STAR_GAP_MAP.md")
BLUEPRINT = os.path.join(DOCS, "TASK_CONTENTOPS_0174D_V4_COMPOSITION_BLUEPRINT.md")
WIREFRAME = os.path.join(DOCS, "TASK_CONTENTOPS_0174D_V4_SCREEN_WIREFRAME_CONTRACT.md")
TESTPLAN = os.path.join(DOCS, "TASK_CONTENTOPS_0174D_V4_TEST_AND_REGRESSION_PLAN.md")

ALL_DOCS = [GAP_MAP, BLUEPRINT, WIREFRAME, TESTPLAN]

SCREENS = [
    "command center", "content studio", "publish readiness", "evidence vault",
    "calendar", "visual export", "settings",
]


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _read_lower(path):
    return _read(path).lower()


# 1. All four docs exist.
def test_all_blueprint_docs_exist():
    for path in ALL_DOCS:
        assert os.path.isfile(path), path


# 2. Every doc mentions all seven screens (per-document, not just combined corpus).
def test_each_doc_mentions_all_seven_screens():
    for path in ALL_DOCS:
        text = _read_lower(path)
        for screen in SCREENS:
            assert screen in text, "doc " + os.path.basename(path) + " missing screen: " + screen


# 3. Required north-star concepts must appear across the doc set.
NORTH_STAR_CONCEPTS = [
    "state before action",
    "evidence is the interface",
    "local",
    "not public",
    "live disabled",
    "no financial advice",
    "no signal language",
    "platform",
    "credential read",
    "bottom overlap",
    "compliance",
    "gate matrix",
    "lane separation",
    "screenshot-safe",
]


def test_required_north_star_concepts_present():
    corpus = " ".join(_read_lower(p) for p in ALL_DOCS)
    for concept in NORTH_STAR_CONCEPTS:
        assert concept in corpus, "missing north-star concept: " + concept


def test_current_vs_historical_provenance_present():
    corpus = " ".join(_read_lower(p) for p in ALL_DOCS)
    assert "current vs historical" in corpus or "current-vs-historical" in corpus
    assert "historical provenance" in corpus or "historical_provenance" in corpus
    assert "not runtime authority" in corpus


def test_settings_policy_not_secrets():
    text = _read_lower(BLUEPRINT) + _read_lower(WIREFRAME)
    assert "policy matrix" in text
    assert "never-display" in text or "never display" in text


def test_no_stale_0174b_gate_required():
    corpus = " ".join(_read_lower(p) for p in ALL_DOCS)
    # the docs must explicitly forbid the stale V3 gate string as V4 current truth.
    assert "awaiting chatgpt audit of 0174b" in corpus
    assert "must not" in corpus or "forbid" in corpus or "fail if" in corpus


def test_no_generic_terminal_table_dashboard():
    corpus = " ".join(_read_lower(p) for p in ALL_DOCS)
    assert "terminal table dump" in corpus or "terminal/table" in corpus or "table dump" in corpus


# 4. V3 rejection + target-capture verification must be explicit.
def test_v3_rejected_as_north_star():
    gap = _read_lower(GAP_MAP)
    assert "not accepted" in gap
    assert "v3" in gap


def test_target_capture_verified_correct():
    gap = _read_lower(GAP_MAP)
    assert "captured the correct v3 target" in gap or "correct v3 target" in gap
    assert "wrong target" in gap  # discussed and rejected


def test_worker_visual_judgment_rejected():
    gap = _read_lower(GAP_MAP)
    assert "rejected" in gap
    assert "0174c" in gap


# 5. Material V4 composition differences from V3.
def test_v4_material_differences_present():
    bp = _read_lower(BLUEPRINT)
    assert "what changes materially from v3" in bp
    assert "what must not be reused from v3" in bp
    assert "verdict band" in bp
    assert "gate matrix" in bp


# 6. No runtime code authorized in 0174D.
def test_docs_forbid_runtime_code_in_0174d():
    for path in ALL_DOCS:
        text = _read_lower(path)
        assert "no" in text and "runtime" in text
    # at least one doc states it explicitly.
    corpus = " ".join(_read_lower(p) for p in ALL_DOCS)
    assert "no runtime frontend code" in corpus or "no frontend runtime code" in corpus


# 7. Requirement matrix + severity present in the gap map.
def test_gap_map_requirement_matrix_present():
    gap = _read(GAP_MAP)
    assert "Requirement Matrix" in gap
    for sev in ("BLOCKER", "MAJOR", "MINOR", "OBSERVATION"):
        assert sev in gap, "missing severity: " + sev


# 8. Wireframes cover first-fold + forbidden controls for each screen.
def test_wireframes_have_first_fold_and_forbidden_controls():
    wf = _read_lower(WIREFRAME)
    assert wf.count("first-fold target") >= 7
    assert wf.count("forbidden controls") >= 7
    assert "1366x768" in _read(WIREFRAME)


# 9. Test/regression plan is concrete.
def test_regression_plan_concrete():
    tp = _read_lower(TESTPLAN)
    for token in ("stale metadata", "forbidden control", "bottom directive",
                  "safety ribbon", "acceptance criteria", "visual acceptance rubric"):
        assert token in tp, "missing regression section: " + token


# 10. Strict north-star contract phrases (not weakened tokens).
STRICT_PHRASES = [
    "state before action",
    "evidence is the interface",
    "local-only",
    "not public-postable",
    "live disabled",
    "no financial advice",
    "no signal language",
    "no platform api",
    "no credential read",
    "no bottom overlap",
    "no generic terminal/table dashboard",
    "compliance room",
    "gate-matrix-first",
    "lane separation",
    "screenshot-safe",
    "never-display registry",
]


def test_strict_north_star_phrases_present():
    corpus = " ".join(_read_lower(p) for p in ALL_DOCS)
    for phrase in STRICT_PHRASES:
        assert phrase in corpus, "missing strict north-star phrase: " + phrase


def test_current_vs_historical_strict_phrase():
    corpus = " ".join(_read_lower(p) for p in ALL_DOCS)
    assert "current-vs-historical provenance" in corpus or \
        "current vs historical provenance" in corpus


def test_no_stale_0174b_current_gate_strict():
    corpus = " ".join(_read_lower(p) for p in ALL_DOCS)
    assert "no stale 0174b current gate" in corpus or \
        "no stale 0174b gate" in corpus


# 11. Gap Map must name the required raw Stitch HTML references.
REQUIRED_RAW_HTML = [
    "command_center_capital_chronicle.html",
    "publish_readiness_tower_capital_chronicle.html",
    "evidence_vault_capital_chronicle.html",
]


def test_gap_map_names_required_raw_stitch_html():
    gap = _read_lower(GAP_MAP)
    for html in REQUIRED_RAW_HTML:
        assert html in gap, "Gap Map missing raw Stitch HTML reference: " + html


def test_gap_map_names_design_md_and_quarantine_status():
    gap = _read_lower(GAP_MAP)
    assert "design.md" in gap
    assert "quarantine" in gap or "quarantined" in gap
    assert "reference only" in gap or "reference-only" in gap
    assert "not runtime authority" in gap or "not copied into runtime" in gap


# 12. Composition Blueprint must not contain the broken section-10 sentence.
def test_blueprint_section10_sentence_repaired():
    bp = _read(BLUEPRINT)
    # the split defect: section 10 ending mid-sentence right before section 11.
    assert "A status with no reason and\n\n## 11" not in bp
    # the stray continuation must not be dangling at EOF.
    assert not bp.rstrip().endswith("no evidence_ref_ids is invalid and must fail tests.") or \
        "A status with no reason and\nno evidence_ref_ids is invalid and must fail tests." in bp
    # the full clean sentence must be present and intact.
    assert "A status with no reason and\nno evidence_ref_ids is invalid and must fail tests." in bp


# 13. Wireframe Contract must have balanced Markdown code fences.
def test_wireframe_fences_balanced():
    lines = _read(WIREFRAME).splitlines()
    fence_lines = [ln for ln in lines if ln.strip() == "```"]
    assert len(fence_lines) % 2 == 0, "unbalanced Markdown code fences"
    # the file must not end with two consecutive fence lines.
    stripped = [ln for ln in lines if ln.strip() != ""]
    assert not (len(stripped) >= 2 and stripped[-1].strip() == "```"
                and stripped[-2].strip() == "```"), "duplicate trailing code fence"

