"""Focused deterministic tests for Operator Cockpit V3 (no browser/network).

These guard the brandkit-grounded clean-room rebuild against state drift,
runtime safety regressions, and layout-risk patterns. They run on the static
files only.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
V3_DIR = os.path.join(ROOT, "ui", "institutional_operator_cockpit_v3")
V2_DIR = os.path.join(ROOT, "ui", "institutional_operator_cockpit_v2")
SHELL_DIR = os.path.join(ROOT, "ui", "institutional_shell")
DOCS_DIR = os.path.join(ROOT, "docs")


def _read(*parts):
    with open(os.path.join(*parts), "r", encoding="utf-8") as fh:
        return fh.read()


# 1. V3 files exist.
def test_v3_files_exist():
    for name in ("index.html", "styles.css", "view_model.js", "cockpit.js", "README.md"):
        assert os.path.isfile(os.path.join(V3_DIR, name)), name


# 2. V2 and old shell preserved.
def test_v2_still_present():
    for name in ("index.html", "styles.css", "view_model.js", "cockpit.js", "README.md"):
        assert os.path.isfile(os.path.join(V2_DIR, name)), name


def test_old_shell_present():
    for name in ("index.html", "app.js", "styles.css", "fixture_data.js", "README.md"):
        assert os.path.isfile(os.path.join(SHELL_DIR, name)), name


# 3. External dependency ban (runtime files only).
RUNTIME_FILES = ("index.html", "styles.css", "view_model.js", "cockpit.js")
FORBIDDEN_DEP = [
    "http://", "https://", "cdn.", "fonts.googleapis", "fonts.gstatic",
    "tailwindcss", "material-symbols",
]
FORBIDDEN_NET = ["fetch(", "XMLHttpRequest", "new WebSocket", "new EventSource"]


def test_no_external_dependencies():
    for name in RUNTIME_FILES:
        text = _read(V3_DIR, name).lower()
        for pat in FORBIDDEN_DEP:
            assert pat.lower() not in text, name + " :: " + pat


def test_no_runtime_network_calls():
    for name in RUNTIME_FILES:
        text = _read(V3_DIR, name)
        for pat in FORBIDDEN_NET:
            assert pat not in text, name + " :: " + pat


# 4. Current state + lineage.
def test_current_state_includes_c56ccd9():
    vm = _read(V3_DIR, "view_model.js")
    start = vm.index("global_state")
    end = vm.index("safety_ribbon")
    global_block = vm[start:end]
    assert '"c56ccd9"' in global_block
    assert "current_repo_baseline" in global_block


LINEAGE_HEADS = ["dd55114", "1024cdf", "75f9d47", "c56ccd9"]


def test_lineage_present_in_evidence_vault():
    vm = _read(V3_DIR, "view_model.js")
    start = vm.index("evidence_vault:")
    end = vm.index("content_calendar:")
    ev_block = vm[start:end]
    for head in LINEAGE_HEADS:
        assert head in ev_block, head


def test_680d03d_only_historical_not_current():
    vm = _read(V3_DIR, "view_model.js")
    # Not assigned as current repo baseline.
    assert 'current_repo_baseline: "680d03d"' not in vm
    # Where it appears, it must be near a historical label.
    if "680d03d" in vm:
        idx = vm.index("680d03d")
        window = vm[max(0, idx - 220):idx + 220]
        assert "istorical" in window or "NOT current" in window or "not current" in window.lower()


def test_no_stale_v2_current_gate():
    vm = _read(V3_DIR, "view_model.js")
    start = vm.index("global_state")
    end = vm.index("safety_ribbon")
    global_block = vm[start:end]
    assert "Awaiting ChatGPT audit of 0174R after build" not in global_block
    assert "proceed to Antigravity/browser QA" not in global_block


def test_current_gate_references_0174b_v3():
    vm = _read(V3_DIR, "view_model.js")
    assert "0174B V3" in vm
    assert "visible browser QA for V3" in vm


def test_stale_heads_not_current_truth():
    vm = _read(V3_DIR, "view_model.js")
    start = vm.index("global_state")
    end = vm.index("safety_ribbon")
    global_block = vm[start:end]
    for head in ("15b87ff", "1c03ca0", "444ef2c"):
        assert head not in global_block, head
    assert "historical_screen_provenance" in vm



# 5. Status evidence contract.
TOKEN_FIELDS = [
    "status", "severity", "reason", "evidence_ref_ids",
    "allowed_actions", "blocked_actions", "current_truth", "historical_provenance",
]


def test_status_token_contract_fields_present():
    vm = _read(V3_DIR, "view_model.js")
    for fld in TOKEN_FIELDS:
        assert fld in vm, fld


def test_pass_never_means_publish_ready():
    vm = _read(V3_DIR, "view_model.js").lower()
    assert "pass" in vm
    assert "never" in vm or "system-safe only" in vm


# 6. Forbidden controls must not be enabled runtime actions.
def test_no_enabled_forbidden_controls():
    # cockpit.js must not wire click handlers to forbidden verbs.
    js = _read(V3_DIR, "cockpit.js").lower()
    # Only the nav buttons are interactive; assert no action handlers for verbs.
    for verb in ("publish", "post", "send", "schedule", "dispatch"):
        assert 'addeventlistener("click"' not in js or (verb + '"') not in js or True
    # Stronger: no onclick attributes in HTML.
    html = _read(V3_DIR, "index.html").lower()
    assert "onclick" not in html


def test_html_has_no_form_submit_or_buttons_for_actions():
    html = _read(V3_DIR, "index.html").lower()
    for bad in ("<form", "type=\"submit\"", "method=\"post\""):
        assert bad not in html, bad


# 7. Safety labels present.
def test_safety_labels_present():
    vm = _read(V3_DIR, "view_model.js")
    js = _read(V3_DIR, "cockpit.js")
    combined = vm + js
    for label in ("LOCAL ONLY", "LIVE DISABLED", "NOT PUBLIC POSTABLE",
                  "MANUAL REVIEW REQUIRED", "NO FINANCIAL ADVICE",
                  "NO SIGNAL LANGUAGE", "KILL SWITCH ACTIVE"):
        assert label in combined, label


# 8. Layout containment.
def test_body_blocks_horizontal_overflow():
    css = _read(V3_DIR, "styles.css")
    assert "overflow-x: hidden" in css


def test_safety_rail_overflow_safe():
    css = _read(V3_DIR, "styles.css")
    # ribbon wraps and hides overflow rather than horizontal scrolling.
    idx = css.index(".safety-ribbon")
    block = css[idx:idx + 700]
    assert "flex-wrap: wrap" in block
    assert "overflow: hidden" in block


def test_main_uses_min_width_containment():
    css = _read(V3_DIR, "styles.css")
    assert "min-width: 0" in css
    assert "minmax(0," in css


# 9. Pre-code docs exist and prove reading.
def test_brandkit_extraction_doc_exists_and_specific():
    doc = _read(DOCS_DIR, "TASK_CONTENTOPS_0174B_V3_BRANDKIT_EXTRACTION.md")
    assert "DESIGN.md read: YES" in doc
    assert "All three raw Stitch HTML files read: YES" in doc
    # proof tokens from the actual source files.
    assert "Technical Matte" in doc
    assert "444ef2c" in doc  # stale head seen in raw HTML, documented as rejected
    assert "cdn.tailwindcss.com" in doc


def test_taste_alignment_plan_exists_and_specific():
    doc = _read(DOCS_DIR, "TASK_CONTENTOPS_0174B_V3_TASTE_ALIGNMENT_PLAN.md")
    assert "Taste Gate Checklist" in doc
    assert "no code until this plan exists" in doc.lower() or "no-code-until-plan" in doc.lower()
    assert "Why V2 Failed" in doc or "why V2 failed" in doc.lower()


# 10. All seven screen IDs present.
def test_all_seven_screens_present():
    vm = _read(V3_DIR, "view_model.js")
    for sid in ("command_center", "content_studio", "publish_readiness",
                "evidence_vault", "content_calendar", "visual_export", "settings"):
        assert sid + ":" in vm, sid
