"""Truth + redundancy cleanup guard tests for Operator Cockpit V4 (0174V).

Deterministic static assertions only — no browser, no network. Verifies the
0174V cleanup: no duplicate dominant bands after the scan layer, scan layer
preserves reason/evidence, Command Center has no triple redundancy, stale
0174K/0174L current truth is gone, safety-lock cluster truncates gracefully,
and no feature/safety regression.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "ui" / "institutional_operator_cockpit_v4"
STYLES = V4 / "styles.css"
INDEX = V4 / "index.html"
VIEW_MODEL = V4 / "view_model.js"
COCKPIT = V4 / "cockpit.js"

RUNTIME_FILES = [INDEX, STYLES, VIEW_MODEL, COCKPIT]


def _css() -> str:
    return STYLES.read_text(encoding="utf-8")


def _cockpit() -> str:
    return COCKPIT.read_text(encoding="utf-8")


def _vm() -> str:
    return VIEW_MODEL.read_text(encoding="utf-8")


def _runtime_text() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in RUNTIME_FILES)


# ---------- A. no duplicate dominant bands after the scan layer ----------
def test_scan_layer_still_called_before_switch():
    cockpit = _cockpit()
    assert "renderOperatorScanLayer(screen, body)" in cockpit


def test_no_duplicate_dominant_bands():
    cockpit = _cockpit()
    for call in ["renderBand(s.verdict)", "renderBand(s.studio_state)",
                 "renderBand(s.readiness_verdict)", "renderBand(s.evidence_state)",
                 "renderBand(s.plan_state)", "renderBand(s.export_state)",
                 "renderBand(s.policy_state)"]:
        assert call not in cockpit, "duplicate dominant band still present: " + call


# ---------- B. scan layer preserves reason/evidence ----------
def test_scan_layer_has_reason_class():
    cockpit = _cockpit()
    assert "scan-reason" in cockpit or "primary-reason" in cockpit


def test_scan_layer_reads_verdict_reason():
    cockpit = _cockpit()
    assert "verdict.reason" in cockpit


def test_scan_layer_renders_evidence_and_blockers():
    cockpit = _cockpit()
    assert ".map(evidenceRefId)" in cockpit or "evidenceRefId(ref)" in cockpit
    assert "top-blocker-cards" in cockpit


# ---------- C. Command Center no triple redundancy ----------
def test_command_center_no_mission_grid_render():
    cockpit = _cockpit()
    # the mission-grid summary row must no longer be created in the renderer.
    assert 'el("div", "mission-grid primary-command-board section-gap")' not in cockpit


def test_command_center_keeps_core_panels():
    cockpit = _cockpit()
    for label in ["What Changed Since Last Accepted State", "Active Blocker Stack",
                  "Evidence Dependency Map", "Safety Counters"]:
        assert label in cockpit, "command center panel removed: " + label


# ---------- D. stale current-truth cleanup ----------
def test_no_stale_current_truth_phrases():
    vm = _vm()
    for stale in [
        "0174K browser QA found targeted V4 visual defects; 0174L patch applied",
        "0174L patch awaits targeted browser recheck",
        "Awaiting 0174E audit",
        "0174E evidence packet",
    ]:
        assert stale not in vm, "stale current-truth phrase present: " + stale


def test_current_truth_references_present_state():
    vm = _vm()
    # current operator truth is the composed 0174AC baseline + in-progress 0174AD pass.
    for token in ["4ffe650", "0174AD", "Dashboard"]:
        assert token in vm, "missing present-state token: " + token
    # the older progressive-disclosure lineage survives only as historical provenance.
    lineage = vm.split("Build Lineage (Historical Provenance)", 1)
    assert len(lineage) == 2, "historical build-lineage entry missing"
    block = lineage[1].split("}", 1)[0]
    for token in ["0174Z", "0174V", "progressive disclosure"]:
        assert token in block, "lineage token not in historical block: " + token

# ---------- D1. next-action QA copy repair (0174V1) ----------
def test_next_action_no_antigravity_phrase_removed():
    vm = _vm()
    assert "No Antigravity" not in vm


def test_next_action_instructs_antigravity_browser_qa():
    vm = _vm()
    na = vm.split('role_label: "Next Allowed Action"', 1)[1].split("}", 1)[0]
    # composed 0174AD next action: short, Browser-QA-focused, on the current baseline.
    for token in ["Browser QA", "visual audit"]:
        assert token in na, "missing next-action token: " + token
    # no live/platform/API behavior may be implied as available.
    assert "No live" in na or "no live" in na


def test_next_action_no_stale_cline_patch_task_wording():
    vm = _vm()
    na = vm.split('role_label: "Next Allowed Action"', 1)[1].split("}", 1)[0]
    assert "Cline patch task" not in na
    for stale in ["0174L patch awaits targeted browser recheck",
                  "Awaiting 0174E audit", "0174E evidence packet"]:
        assert stale not in vm, "stale wording present: " + stale




# ---------- E. safety-lock ellipsis ----------
def test_safety_lock_cluster_truncates_gracefully():
    css = _css()
    start = css.index(".safety-locks-cluster {")
    block = css[start:css.index("}", start)]
    assert "overflow: hidden" in block
    assert "text-overflow: ellipsis" in block
    assert "white-space: nowrap" in block
    assert "min-width: 0" in block
    assert "flex: 0 0 auto" not in block


# ---------- F. safety / runtime regressions ----------
def test_no_forbidden_runtime_apis():
    text = _runtime_text()
    for token in ["fetch(", "XMLHttpRequest", "WebSocket", "EventSource",
                  "navigator.sendBeacon", "localStorage", "sessionStorage"]:
        assert token not in text, "forbidden runtime API: " + token


def test_no_remote_urls_runtime():
    text = _runtime_text().lower()
    for token in ["http://", "https://", "fonts.googleapis", "fonts.gstatic", "cdn", "unpkg", "jsdelivr"]:
        assert token not in text, "forbidden remote token: " + token


def test_no_object_object_regression():
    assert "[object Object]" not in _runtime_text()


def test_no_trading_or_signal_wording():
    text = _runtime_text().lower()
    for token in ["buy/sell/hold", "price target", "position sizing", "p&l",
                  "trade recommendation", "bullish", "bearish"]:
        assert token not in text, "forbidden trading wording: " + token


# ---------- G. detail preservation (no feature deletion) ----------
def test_detail_sections_preserved():
    cockpit = _cockpit()
    for label in ['"Gate Matrix"', '"Validation Matrix"', '"Evidence Timeline"',
                  '"Caveat Registry"', '"Forbidden-Scope Registry"',
                  '"Active Blocker Registry"', '"Policy Matrix"',
                  '"Credential Never-Display Registry"']:
        assert label in cockpit, "detail section removed: " + label


def test_content_studio_and_calendar_and_export_detail_preserved():
    cockpit = _cockpit()
    for cls in ["lane-limits", "lane-checklist", "lane-evidence-strip"]:
        assert cls in cockpit, "content studio detail removed: " + cls
    assert "Forbidden Automated States" in cockpit
    assert "Redaction Preview" in cockpit
    assert "Limitation Strip" in cockpit


def test_safety_locks_preserved():
    vm = _vm()
    for lock in ["LOCAL-ONLY", "REVIEW-ONLY", "NOT PUBLIC-POSTABLE",
                 "LIVE DISABLED", "KILL SWITCH ACTIVE", "NO FINANCIAL ADVICE",
                 "NO SIGNAL LANGUAGE", "NO PLATFORM API", "NO PROVIDER API",
                 "NO SCHEDULER", "NO SCRAPING", "NO CREDENTIAL READ", "SECRET REDACTED"]:
        assert lock in vm, "safety lock removed: " + lock
