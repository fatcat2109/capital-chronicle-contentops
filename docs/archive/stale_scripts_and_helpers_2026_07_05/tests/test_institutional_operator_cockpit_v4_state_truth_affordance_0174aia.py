"""0174AIa state-truth + inspect-affordance guard tests.

Deterministic static assertions only. Enforce that current truth points at the
implemented 0174AI head (152b855), that 4ffe650 / 0174AD survive only as
historical provenance, that the command-tile inspect affordance is a matte
secondary control (not a native white button or a CTA), that the selected-object
visual state and inspector readability rules exist, and the standing safety
invariants hold.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "ui" / "institutional_operator_cockpit_v4"
STYLES = V4 / "styles.css"
VIEW_MODEL = V4 / "view_model.js"
COCKPIT = V4 / "cockpit.js"
INDEX = V4 / "index.html"
RUNTIME_FILES = [INDEX, STYLES, VIEW_MODEL, COCKPIT]


def _vm() -> str:
    return VIEW_MODEL.read_text(encoding="utf-8")


def _css() -> str:
    return STYLES.read_text(encoding="utf-8")


def _cockpit() -> str:
    return COCKPIT.read_text(encoding="utf-8")


def _runtime_text() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in RUNTIME_FILES)


def _summary_block() -> str:
    vm = _vm()
    return vm.split("truth_rail_summary", 1)[1].split("}", 1)[0]


def _current_head_block() -> str:
    vm = _vm()
    return vm.split('role_label: "Current Product HEAD"', 1)[1].split("}", 1)[0]


def _gate_block() -> str:
    vm = _vm()
    return vm.split('role_label: "Current Gate"', 1)[1].split("}", 1)[0]


def _next_action_block() -> str:
    vm = _vm()
    return vm.split('role_label: "Next Allowed Action"', 1)[1].split("}", 1)[0]


def _lineage_block() -> str:
    vm = _vm()
    return vm.split("Build Lineage (Historical Provenance)", 1)[1].split("}", 1)[0]


# ---------- A. current-truth repair ----------
def test_current_head_is_executive_992a7d0():
    head = _current_head_block()
    assert "992a7d0" in head
    assert "0174AJ_AK" in head
    # Active part before prior list
    active = head.split("Prior")[0]
    for stale in ["152b855", "9570bdc", "4ffe650", "0174AD"]:
        assert stale not in active, f"stale head {stale} is listed as active"


def test_current_head_not_stale():
    head = _current_head_block()
    active = head.split("Prior")[0]
    assert "4ffe650" not in active
    assert "0174AD" not in active


def test_summary_head_is_current():
    summary = _summary_block()
    assert "992a7d0" in summary
    assert "152b855" not in summary.split("Prior")[0]
    assert "4ffe650" not in summary


def test_next_action_is_0174al_qa():
    nxt = _next_action_block()
    assert "0174AL" in nxt
    assert "0174AIa" not in nxt
    assert "0174AD" not in nxt
    assert "0174AF" not in nxt


def test_current_blocks_do_not_contain_stale_phrases():
    vm = _vm()
    for stale in [
        "0174AIa state-truth + inspect-affordance patch in progress",
        "Targeted 0174AJ build only after",
        "Browser QA screenshot capture of 0174AIa"
    ]:
        assert stale not in vm, f"stale phrase found: {stale}"


def test_stale_heads_historical_only():
    lineage = _lineage_block()
    assert "152b855" in lineage
    assert "9570bdc" in lineage
    assert "4ffe650" in lineage
    assert "0174AD" in lineage


# ---------- B. command tile inspect affordance ----------
def test_inspect_affordance_class_styled():
    cockpit = _cockpit()
    assert "inspect-affordance" in cockpit, "inspect affordance class missing in renderer"
    assert 'textContent = "Inspect' in cockpit or "Inspect \u203a" in cockpit
    css = _css()
    assert ".command-tile-cue.inspect-affordance" in css, "inspect affordance not styled"
    # must neutralize native button look
    block = css.split(".command-tile-cue.inspect-affordance", 1)[1].split("}", 1)[0]
    assert "appearance: none" in block, "native button appearance not reset"


def test_no_open_label_cta():
    cockpit = _cockpit()
    assert 'textContent = "Open' not in cockpit, "stale white 'Open' button label remains"


# ---------- C/D. selected-object visual + readability ----------
def test_selected_state_rules_present():
    css = _css()
    for rule in [".selectable-object.selected", ".selectable-object:hover",
                 "focus-visible", ".selected-object-detail",
                 ".selected-object-label", ".evidence-path", ".evidence-chip"]:
        assert rule in css, "selected/readability rule missing: " + rule


def test_reduced_motion_supported():
    assert "prefers-reduced-motion" in _css()


# ---------- E. standing safety invariants ----------
def test_safe_labels_only():
    cockpit = _cockpit()
    for safe in ['"Inspect Gate"', '"Select Lane"', '"Review Blocker"',
                 '"View Evidence"', '"Open Policy Group"']:
        assert safe in cockpit, "safe control label missing: " + safe


def test_no_forbidden_runtime_apis():
    text = _runtime_text()
    for token in ["fetch(", "XMLHttpRequest", "WebSocket", "EventSource",
                  "navigator.sendBeacon", "localStorage", "sessionStorage"]:
        assert token not in text, "forbidden runtime API: " + token


def test_no_remote_or_framework_deps():
    text = _runtime_text().lower()
    for token in ["http://", "https://", "fonts.googleapis", "fonts.gstatic",
                  "unpkg", "jsdelivr", "cdn", "react", "tailwind"]:
        assert token not in text, "forbidden remote/framework token: " + token


def test_no_glow_or_neon():
    css = _css().lower()
    for token in ["box-shadow: 0 0", "text-shadow", "#00f", "#0ff",
                  "rgba(0, 0, 255", "rgba(0,0,255"]:
        assert token not in css, "forbidden glow/neon token: " + token


def test_no_feature_deletion():
    cockpit = _cockpit()
    for label in ['"Gate Matrix"', '"Validation Matrix"', '"Evidence Timeline"',
                  '"Caveat Registry"', '"Active Blocker Registry"',
                  '"Credential Never-Display Registry"', '"Policy Matrix"']:
        assert label in cockpit, "feature removed: " + label
