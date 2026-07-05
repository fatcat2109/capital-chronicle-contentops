"""State / layout / content-density guard tests for Operator Cockpit V4 (0174G).

Deterministic static assertions only (no browser, no network). Enforces the
0174G hardening: density/layout classes exist in CSS and are used in the
renderer, screen-specific content depth, responsive overflow discipline, and
no V3 fixed-bottom directive pattern.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "ui" / "institutional_operator_cockpit_v4"
INDEX = V4 / "index.html"
STYLES = V4 / "styles.css"
VIEW_MODEL = V4 / "view_model.js"
COCKPIT = V4 / "cockpit.js"

RUNTIME_FILES = [INDEX, STYLES, VIEW_MODEL, COCKPIT]

DENSITY_CLASSES = [
    "mission-grid", "decision-stack", "change-ledger", "proof-graph",
    "gate-control-surface", "audit-registry", "lane-control-grid",
    "manual-workflow-board", "screenshot-prep-grid", "policy-inspection-grid",
]


def _css() -> str:
    return STYLES.read_text(encoding="utf-8")


def _cockpit() -> str:
    return COCKPIT.read_text(encoding="utf-8")


def _runtime_text() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in RUNTIME_FILES)


# ---------- density / layout classes ----------
def test_density_classes_defined_in_css():
    css = _css()
    for cls in DENSITY_CLASSES:
        assert ("." + cls) in css, "missing CSS class: " + cls


def test_density_classes_used_in_cockpit():
    cockpit = _cockpit()
    # mission-grid / decision-stack remain CSS-defined but the duplicate
    # Command Center summary row was removed in 0174V (scan layer covers it).
    used_classes = [c for c in DENSITY_CLASSES if c not in ("mission-grid", "decision-stack")]
    for cls in used_classes:
        assert cls in cockpit, "density class not used in renderer: " + cls


# ---------- responsive overflow discipline ----------
def test_page_overflow_x_hidden():
    css = _css()
    assert "overflow-x: hidden" in css


def test_matrices_scroll_internally():
    css = _css()
    assert "overflow-x: auto" in css


def test_no_v3_fixed_bottom_directive_pattern():
    css = _css()
    assert "position: fixed" not in css
    assert "position:fixed" not in css
    # in-flow footer must remain static.
    assert "position: static" in css

# ---------- seven screens still present ----------
def test_seven_screens_present():
    vm = VIEW_MODEL.read_text(encoding="utf-8")
    for sid in ["command_center", "content_studio", "publish_readiness",
                "evidence_vault", "content_calendar", "visual_export",
                "settings_safety_policy"]:
        assert sid in vm, "missing screen: " + sid


# ---------- Command Center state clarity ----------
def test_command_center_state_clarity():
    cockpit = _cockpit()
    # 0174V: the duplicate mission-grid summary row was removed. The readable
    # operator scan layer now covers verdict + next action + blockers + evidence.
    assert "renderOperatorScanLayer(screen, body)" in cockpit
    assert "Next Allowed Action" in cockpit
    assert "top-blocker-cards" in cockpit
    assert "change-ledger" in cockpit
    assert "proof-graph" in cockpit


# ---------- Publish Readiness disabled gates ----------
def test_publish_readiness_disabled_gates():
    vm = VIEW_MODEL.read_text(encoding="utf-8")
    assert "credential_read" in vm
    assert "credential_validation" in vm
    assert "live_adapter" in vm
    assert "scheduler" in vm
    assert "posting" in vm
    assert "next_blocker" in vm
    assert "LIVE_DISABLED" in vm


# ---------- Evidence Vault registries ----------
def test_evidence_vault_registries():
    vm = VIEW_MODEL.read_text(encoding="utf-8")
    assert "validation_matrix" in vm
    assert "caveat_registry" in vm
    assert "forbidden_scope_registry" in vm
    assert "active_blocker_registry" in vm
    assert "confidence_legend" in vm


# ---------- Content Studio lane depth ----------
def test_content_studio_lane_depth():
    vm = VIEW_MODEL.read_text(encoding="utf-8")
    for field in ["claim_risk", "forbidden_language", "limitations",
                  "platform_fit", "checklist", "evidence_ref_ids"]:
        assert field in vm, "missing lane field: " + field


# ---------- Calendar manual vs automated ----------
def test_calendar_manual_and_forbidden_states():
    vm = VIEW_MODEL.read_text(encoding="utf-8")
    assert "allowed_states" in vm
    assert "forbidden_states" in vm
    for st in ["scheduled", "queued for auto-post", "auto-publish ready"]:
        assert st in vm, "missing forbidden state: " + st


# ---------- Visual Export safety ----------
def test_visual_export_safety():
    vm = VIEW_MODEL.read_text(encoding="utf-8")
    assert "redaction_preview" in vm
    assert "limitation_strip" in vm
    assert "blocked_forecast_explainer" in vm
    assert "failure_forensics_card" in vm


# ---------- Settings policy inspection ----------
def test_settings_policy_inspection():
    vm = VIEW_MODEL.read_text(encoding="utf-8")
    assert "policy_matrix" in vm
    assert "credential_never_display_registry" in vm
    assert "platform_gate_policy" in vm
    assert "future_gate_requirements" in vm


# ---------- safety: no network / no trading wording ----------
def test_no_network_or_storage_runtime():
    text = _runtime_text()
    for token in ["fetch(", "XMLHttpRequest", "WebSocket", "EventSource",
                  "navigator.sendBeacon", "localStorage", "sessionStorage"]:
        assert token not in text, "forbidden runtime API: " + token


def test_no_remote_urls_runtime():
    text = _runtime_text().lower()
    for token in ["http://", "https://", "fonts.googleapis", "fonts.gstatic", "cdn", "unpkg", "jsdelivr"]:
        assert token not in text, "forbidden remote token: " + token


def test_no_trading_or_signal_wording():
    text = _runtime_text().lower()
    for token in ["buy/sell/hold", "price target", "position sizing", "p&l",
                  "trade recommendation", "bullish", "bearish"]:
        assert token not in text, "forbidden trading wording: " + token

