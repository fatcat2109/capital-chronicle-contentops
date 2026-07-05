"""0174AF premium command-surface / readability / interaction guard tests.

Deterministic static assertions only — no browser, no network. Enforces the
0174AF elevation: command-tile inspection surfaces (read-only/local-only),
local density toggle, lifted type scale, no fake operational controls, no
blue/glow, screenshot-safe wording preserved, and no feature deletion.
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


# ---------- command-tile inspection surfaces ----------
def test_command_tile_defined_and_used():
    css = _css()
    cockpit = _cockpit()
    for cls in [".command-tile-row", ".command-tile", ".command-tile-title", ".command-tile-cue"]:
        assert cls in css, "missing command-tile class in CSS: " + cls
    assert "command-tile-row" in cockpit, "command-tile-row not used in renderer"
    assert "command-tile" in cockpit, "command-tile not used in renderer"


def test_command_tiles_are_read_only_navigation():
    cockpit = _cockpit()
    # Tiles navigate to inspection screens; they are not operational controls.
    assert "renderInspectionCommands" in cockpit
    assert "data-screen-link" in cockpit
    assert "renderScreen(t[2])" in cockpit


# ---------- no fake operational controls ----------
def test_no_fake_operational_buttons():
    text = _runtime_text().lower()
    forbidden = ["publish button", "run button", "send button", "approve button",
                 "schedule button", "connect api", "execute button"]
    for token in forbidden:
        assert token not in text, "fake operational control present: " + token
    # No button label literally inviting an operational action.
    for label in [">publish<", ">post<", ">schedule<", ">approve<", ">execute<", ">connect<"]:
        assert label not in text, "operational button label present: " + label


# ---------- local density toggle ----------
def test_density_toggle_defined_and_used():
    css = _css()
    cockpit = _cockpit()
    assert ".density-toggle" in css
    assert ".density-option" in css
    assert "renderDensityToggle" in cockpit
    assert "density-comfortable" in css and "density-compact" in css
    # toggle must be local-only: no storage/network in the handler region.
    assert "localStorage" not in cockpit
    assert "sessionStorage" not in cockpit


# ---------- lifted type scale (readability) ----------
def test_type_scale_lifted():
    css = _css()
    assert "--type-readable-body: 15px" in css
    assert "--type-primary-answer: 30px" in css
    assert "--type-title: 18px" in css


# ---------- material discipline: no glow / neon / blue ----------
def test_no_glow_or_neon_or_blue():
    css = _css().lower()
    # Genuine structural glow signatures only (avoid colliding with margin
    # shorthands and prose comments like "no neon" / "no glow").
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
    assert "LaneHealthStrip" in cockpit or "lane-health-strip" in cockpit
    assert "publish-checkpoint" in cockpit
    assert "confidence-surface" in cockpit
    assert "workflow-board" in cockpit


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
