"""0174AG workspace-shell / inspector-rail guard tests.

Deterministic static assertions only — no browser, no network. Enforces the
0174AG workspace composition: workspace shell + inspector rail primitives
defined and used, inspector is read-only/local-only, no fake operational
controls, no network/storage, evidence/matrices/registries preserved, no
blue/glow, and screenshot-safe wording preserved.
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


def _runtime_text() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in RUNTIME_FILES)


# ---------- workspace shell + inspector primitives ----------
def test_workspace_shell_defined_and_used():
    css = _css()
    cockpit = _cockpit()
    for cls in [".workspace-shell", ".work-surface", ".inspector-rail"]:
        assert cls in css, "missing workspace class in CSS: " + cls
    assert "workspace-shell" in cockpit, "workspace-shell not used in renderer"
    assert "work-surface" in cockpit, "work-surface not used in renderer"
    assert "inspector-rail" in cockpit, "inspector-rail not used in renderer"


def test_inspector_card_primitives_defined():
    css = _css()
    for cls in [".inspector-card", ".inspector-card-label", ".inspector-card-value",
                ".inspector-lock-row"]:
        assert cls in css, "missing inspector primitive: " + cls


def test_inspector_rail_rendered():
    cockpit = _cockpit()
    assert "renderInspectorRail" in cockpit
    # screen renderers now fill the work surface, not the body directly.
    assert "renderCommandCenter(screen, work)" in cockpit


def test_inspector_is_read_only_summary():
    cockpit = _cockpit()
    # The inspector answers state/blocker/evidence/disabled per screen — read-only.
    for label in ['"Active decision"', '"Gate checkpoint"', '"Disabled (cannot run)"']:
        assert label in cockpit, "inspector summary field missing: " + label


# ---------- no fake operational controls ----------
def test_no_fake_operational_controls():
    text = _runtime_text().lower()
    for token in ["publish button", "run button", "send button", "approve button",
                  "schedule button", "connect api", "execute button", "start automation",
                  "read credentials"]:
        assert token not in text, "fake operational control present: " + token
    for label in [">publish<", ">post<", ">schedule<", ">approve<", ">execute<",
                  ">connect<", ">run<", ">send<"]:
        assert label not in text, "operational button label present: " + label


# ---------- responsive shell is stable (no auto-fit/auto-fill) ----------
def test_workspace_grid_is_stable():
    css = _css()
    for line in css.splitlines():
        if "grid-template-columns" in line:
            assert "auto-fill" not in line, "auto-fill in grid-template: " + line
            assert "auto-fit" not in line, "auto-fit in grid-template: " + line


# ---------- material discipline ----------
def test_no_glow_or_neon_or_blue():
    css = _css().lower()
    for token in ["box-shadow: 0 0", "text-shadow",
                  "#00f", "#0ff", "rgba(0, 0, 255", "rgba(0,0,255"]:
        assert token not in css, "forbidden glow/neon/blue token: " + token


# ---------- screenshot-safe wording preserved ----------
def test_screenshot_safe_wording_preserved():
    text = _runtime_text()
    assert "SCREENSHOT_SAFE" in text
    assert "Capture State" in text


# ---------- no feature deletion ----------
def test_no_feature_deletion():
    cockpit = _cockpit()
    for label in ['"Gate Matrix"', '"Validation Matrix"', '"Evidence Timeline"',
                  '"Caveat Registry"', '"Active Blocker Registry"',
                  '"Credential Never-Display Registry"', '"Policy Matrix"']:
        assert label in cockpit, "feature removed: " + label
    for cls in ["lane-health-strip", "publish-checkpoint", "confidence-surface",
                "workflow-board", "command-tile-row", "density-toggle"]:
        assert cls in cockpit, "prior feature removed: " + cls


# ---------- runtime safety ----------
def test_no_forbidden_runtime_apis():
    text = _runtime_text()
    for token in ["fetch(", "XMLHttpRequest", "WebSocket", "EventSource",
                  "navigator.sendBeacon", "localStorage", "sessionStorage"]:
        assert token not in text, "forbidden runtime API: " + token


def test_no_remote_urls_runtime():
    text = _runtime_text().lower()
    for token in ["http://", "https://", "fonts.googleapis", "fonts.gstatic", "cdn", "unpkg", "jsdelivr"]:
        assert token not in text, "forbidden remote token: " + token
