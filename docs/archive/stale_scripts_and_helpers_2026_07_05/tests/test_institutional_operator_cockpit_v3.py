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
    js = _read(V3_DIR, "cockpit.js")
    # The only click handlers permitted are the nav screen-switch buttons,
    # added inside renderNav. Assert exactly one click handler is wired.
    assert js.count('addEventListener("click"') == 1, "exactly one click handler (nav) expected"
    # That single handler must live in renderNav.
    nav_start = js.index("function renderNav()")
    nav_end = js.index("function renderDirective()")
    nav_block = js[nav_start:nav_end]
    assert 'addEventListener("click"' in nav_block, "the click handler must be in renderNav"

    # cockpit.js must not define action handlers/functions for forbidden verbs.
    js_lower = js.lower()
    for ident in ("callapi", "readenv", "readcredential", "validatecredential",
                  "function publish", "function post", "function send",
                  "function schedule", "function dispatch"):
        assert ident not in js_lower, "forbidden action identifier: " + ident

    # HTML must not include action-looking controls.
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


# 11. CSS syntax / brace-balance / no-gradient guards (0174B1 repair).
def test_css_braces_balanced():
    css = _read(V3_DIR, "styles.css")
    assert css.count("{") == css.count("}"), "CSS braces must balance"


def test_css_no_negative_brace_depth():
    css = _read(V3_DIR, "styles.css")
    depth = 0
    for ch in css:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            assert depth >= 0, "CSS closing brace without matching opener"
    assert depth == 0


def test_ribbon_sev_block_closes_before_system_header():
    css = _read(V3_DIR, "styles.css")
    start = css.index(".ribbon-chip.sev-block")
    nxt = css.index(".system-header", start)
    block = css[start:nxt]
    # the sev-block rule must close with a brace before .system-header begins.
    assert block.count("{") == block.count("}") == 1, "sev-block must open and close exactly once"
    assert "}" in block, "sev-block must close before .system-header"


GRADIENT_PATTERNS = [
    "gradient(", "linear-gradient", "radial-gradient", "conic-gradient",
    "repeating-linear-gradient", "repeating-radial-gradient",
]


def test_css_has_no_gradient_functions():
    css = _read(V3_DIR, "styles.css").lower()
    for pat in GRADIENT_PATTERNS:
        assert pat not in css, "runtime gradient forbidden: " + pat


def test_safety_ribbon_max_width_contained():
    css = _read(V3_DIR, "styles.css")
    idx = css.index(".safety-ribbon")
    block = css[idx:idx + 700]


# 12. Structural brace tests (0174B2 repair) — catch misplaced balanced braces.
def _slice_between(css, sel_a, sel_b):
    start = css.index(sel_a)
    end = css.index(sel_b, start + len(sel_a))
    return css[start:end]


def _assert_single_block_closes(css, sel_a, sel_b):
    block = _slice_between(css, sel_a, sel_b)
    assert block.count("{") == 1, sel_a + " must open exactly once before " + sel_b
    assert block.count("}") == 1, sel_a + " must close exactly once before " + sel_b
    assert block.rindex("}") > block.index("{"), sel_a + " close must follow its open"


def test_dir_value_closes_before_note_banner():
    css = _read(V3_DIR, "styles.css")
    _assert_single_block_closes(css, ".dir-value {", ".note-banner {")


def test_note_banner_closes_before_screen_title():
    css = _read(V3_DIR, "styles.css")
    _assert_single_block_closes(css, ".note-banner {", ".screen-title")


def test_no_compensating_brace_after_kv_is_block():
    css = _read(V3_DIR, "styles.css")
    # between .kv.is-block rule and the chips section there must be no stray
    # closing brace compensating for an earlier missing one.
    block = _slice_between(css, ".kv.is-block", "/* ---- Status tokens / chips ---- */")
    # the only braces here belong to the single-line .kv.is-block rule itself.
    assert block.count("{") == block.count("}"), "no stray compensating brace after .kv.is-block"
    assert block.count("}") == 1, "exactly one closing brace (the .kv.is-block rule) expected"


def test_critical_selector_order_sane():
    css = _read(V3_DIR, "styles.css")
    order = [".directive-bar", ".dir-value", ".note-banner", ".screen-title",
             ".section", ".panel", ".hero", ".kv", ".chip"]
    positions = [css.index(sel) for sel in order]
    assert positions == sorted(positions), "critical CSS selectors must appear in structural order"
