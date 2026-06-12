"""Visual QA defect regression guard tests for Operator Cockpit V4 (0174L).

Catches the exact defects found by 0174K full browser QA:
1. Evidence Vault registries failing to render (missing var cav declaration).
2. Content Studio lanes rendered as uniform plain text (no instrumentation).
3. Stale 0174E current-gate / next-action copy.
4. (matrix readability is CSS-only; covered indirectly.)

Deterministic static assertions only — no browser, no network.
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


# ---------- defect 1: Evidence Vault registries render ----------
def test_evidence_vault_registry_panels_created():
    cockpit = _cockpit()
    assert '"Caveat Registry"' in cockpit
    assert '"Forbidden-Scope Registry"' in cockpit
    assert '"Active Blocker Registry"' in cockpit


def test_cav_declared_before_use():
    cockpit = _cockpit()
    decl = cockpit.find("var cav")
    use = cockpit.find("cav.appendChild")
    assert decl != -1, "var cav declaration missing"
    assert use != -1, "cav usage missing"
    assert decl < use, "cav used before declaration (ReferenceError risk)"


def test_evidence_vault_model_fields_present():
    vm = _vm()
    assert "CAV-0174C" in vm
    assert "forbidden_scope_registry" in vm
    assert "active_blocker_registry" in vm


# ---------- defect 2: Content Studio instrumentation ----------
def test_content_studio_instrumentation_classes_used():
    cockpit = _cockpit()
    for cls in ["lane-instrument-grid", "lane-metric-risk", "lane-metric-forbidden",
                "lane-metric-platform", "lane-limits", "lane-checklist",
                "lane-evidence-strip"]:
        assert cls in cockpit, "lane class not used in renderer: " + cls


def test_content_studio_instrumentation_classes_defined():
    css = _css()
    for cls in [".lane-instrument-grid", ".lane-metric-risk", ".lane-metric-forbidden",
                ".lane-metric-platform", ".lane-limits", ".lane-checklist",
                ".lane-evidence-strip"]:
        assert cls in css, "lane class not defined in CSS: " + cls


# ---------- defect 3: stale current-gate copy removed ----------
def test_no_stale_0174e_current_gate_copy():
    vm = _vm()
    assert "Awaiting ChatGPT audit of 0174E" not in vm


def test_next_action_references_browser_recheck():
    vm = _vm()
    # the next allowed action must reference the current composed audit state.
    assert "1e12953" in vm.lower() or "screenshot audit" in vm.lower()


# ---------- root layout guard still holds ----------
def test_no_unstable_grid_or_fixed_position():
    css = _css()
    assert "repeat(auto-fill, minmax(0, 1fr))" not in css
    assert "repeat(auto-fit, minmax(0, 1fr))" not in css
    assert "position: fixed" not in css
    assert "position:fixed" not in css


# ---------- runtime safety still intact ----------
def test_no_remote_urls_runtime():
    text = _runtime_text().lower()
    for token in ["http://", "https://", "fonts.googleapis", "fonts.gstatic", "cdn", "unpkg", "jsdelivr"]:
        assert token not in text, "forbidden remote token: " + token


def test_no_forbidden_runtime_apis():
    text = _runtime_text()
    for token in ["fetch(", "XMLHttpRequest", "WebSocket", "EventSource",
                  "navigator.sendBeacon", "localStorage", "sessionStorage"]:
        assert token not in text, "forbidden runtime API: " + token


def test_no_trading_or_signal_wording():
    text = _runtime_text().lower()
    for token in ["buy/sell/hold", "price target", "position sizing", "p&l",
                  "trade recommendation", "bullish", "bearish"]:
        assert token not in text, "forbidden trading wording: " + token
