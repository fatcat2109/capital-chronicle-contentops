"""Brand-language + state-grammar guard tests for Operator Cockpit V4 (0174AB).

Deterministic static assertions only — no browser, no network. Verifies the
0174AB targeted patch: current-state copy rebased to the 047ca7a baseline /
0174AA Browser QA caveats / 0174AB next action, red reserved for genuine danger
locks, the scan reason row cannot collide label+value, the composed Publish
Readiness gate-summary strip exists, residual blue/cyber surface literals are
gone, and no safety/runtime regression.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "ui" / "institutional_operator_cockpit_v4"
STYLES = V4 / "styles.css"
VIEW_MODEL = V4 / "view_model.js"
COCKPIT = V4 / "cockpit.js"


def _css() -> str:
    return STYLES.read_text(encoding="utf-8")


def _vm() -> str:
    return VIEW_MODEL.read_text(encoding="utf-8")


def _cockpit() -> str:
    return COCKPIT.read_text(encoding="utf-8")


# ---------- A. current-state copy rebased to 047ca7a / 0174AA / 0174AB ----------
def test_current_state_references_047ca7a_baseline():
    vm = _vm()
    assert "047ca7a" in vm, "current baseline 047ca7a missing from truth model"


def test_current_state_references_0174aa_and_0174ab():
    vm = _vm()
    for token in ["0174AA", "0174AB"]:
        assert token in vm, "missing present-state task token: " + token


def test_no_stale_current_head_placeholder():
    vm = _vm()
    # the stale build-time placeholder must no longer be the Current Product HEAD.
    assert "set-at-build (V4 frontend; visual remediation in progress)" not in vm


# ---------- B. red reserved for genuine danger locks only ----------
def test_safety_rail_reserves_red_for_danger_locks():
    cockpit = _cockpit()
    # the renderer must gate the critical (red) class behind a danger-lock map,
    # not paint every lock red.
    assert "dangerLocks" in cockpit
    assert 'rail.appendChild(el("span", "safety-chip critical", lbl));' not in cockpit


# ---------- C. scan reason label/value cannot collide ----------
def test_scan_reason_row_has_flex_gap():
    css = _css()
    start = css.index(".primary-reason, .scan-reason {")
    block = css[start:css.index("}", start)]
    assert "display: flex" in block
    assert "gap:" in block


# ---------- D. composed Publish Readiness gate-summary strip ----------
def test_gate_summary_strip_rendered():
    cockpit = _cockpit()
    assert "gate-summary-strip" in cockpit
    assert "gate-summary-blocker" in cockpit


def test_gate_summary_strip_styled():
    css = _css()
    assert ".gate-summary-strip {" in css
    assert ".gate-summary-cell {" in css
    # only the blocker cell carries the danger accent.
    start = css.index(".gate-summary-cell.gate-summary-blocker {")
    block = css[start:css.index("}", start)]
    assert "var(--red)" in block


# ---------- E. residual blue/cyber surface literals removed ----------
def test_no_residual_blue_surface_literals():
    css = _css()
    for literal in ["#0e1418", "#0e1216", "#0e1115", "#121417"]:
        assert literal not in css, "residual blue-tinted surface literal: " + literal


# ---------- F. no safety / runtime regression ----------
def test_no_forbidden_runtime_apis():
    text = "\n".join(p.read_text(encoding="utf-8") for p in [STYLES, VIEW_MODEL, COCKPIT])
    for token in ["fetch(", "XMLHttpRequest", "WebSocket", "EventSource",
                  "navigator.sendBeacon", "localStorage", "sessionStorage"]:
        assert token not in text, "forbidden runtime API: " + token


def test_no_remote_urls_runtime():
    text = "\n".join(p.read_text(encoding="utf-8") for p in [STYLES, VIEW_MODEL, COCKPIT]).lower()
    for token in ["http://", "https://", "fonts.googleapis", "fonts.gstatic",
                  "unpkg", "jsdelivr"]:
        assert token not in text, "forbidden remote token: " + token


# ---------- G. composed current state (0174AC) ----------
def _current_head_block(vm):
    return vm.split('role_label: "Current Product HEAD"', 1)[1].split("}", 1)[0]


def _next_action_block(vm):
    return vm.split('role_label: "Next Allowed Action"', 1)[1].split("}", 1)[0]


def test_current_head_is_992a7d0_executive_cockpit():
    vm = _vm()
    head = _current_head_block(vm)
    assert "992a7d0" in head, "current head must be 992a7d0 (0174AJ_AK)"
    assert "0174AJ_AK" in head
    # the active part before "Prior" should not list older heads as active
    active = head.split("Prior")[0]
    for stale in ["152b855", "9570bdc", "4ffe650", "0174AD"]:
        assert stale not in active, f"stale head {stale} is listed as active"


def test_no_active_1f9ed89_as_current_head():
    vm = _vm()
    # the prior committed hash must not present itself as the live current head.
    assert "1f9ed89" not in _current_head_block(vm)
    assert "1f9ed89" not in _next_action_block(vm)
    gate = vm.split('role_label: "Current Gate"', 1)[1].split("}", 1)[0]
    assert "1f9ed89" not in gate


def test_1f9ed89_only_in_historical_provenance():
    vm = _vm()
    # any surviving reference to the prior hash lives in the historical lineage.
    lineage = vm.split("Build Lineage (Historical Provenance)", 1)
    assert len(lineage) == 2, "historical build-lineage entry missing"
    block = lineage[1].split("}", 1)[0]
    assert "1f9ed89" in block
    assert 'kind: "historical"' in block


def test_next_action_references_browser_qa_visual_audit():
    vm = _vm()
    na = _next_action_block(vm)
    assert "Browser QA" in na, "next action must reference Browser QA"
    assert "0174AL" in na


def test_no_0174z_browser_recheck_in_current_blocker():
    vm = _vm()
    stack = vm.split("blocker_stack:", 1)[1].split("],", 1)[0]
    assert "0174Z" not in stack, "current blocker must not cite historical 0174Z recheck"
    assert "browser recheck" not in stack


def test_blue_edge_glow_neutralized():
    css = _css()
    assert "accent-color: var(--accent-authority)" in css
    assert "accent-color: auto" not in css



# ---------- H. de-zebra audit/gate tables ----------
def test_tables_are_de_zebra():
    css = _css()
    # zebra striping (a distinct even-row panel background) must be gone.
    assert "tbody tr:nth-child(even) td { background: var(--bg-panel-2); }" not in css
    # de-zebra mechanism: even rows neutralized to transparent + restrained hover.
    assert "table.matrix tbody tr:nth-child(even) td { background: transparent; }" in css
    assert "table.matrix tbody tr:hover td" in css
