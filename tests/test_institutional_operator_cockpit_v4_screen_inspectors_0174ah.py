"""0174AH screen-specific inspector + executive workflow guard tests.

Deterministic static assertions only — no browser, no network. Enforces that
the inspector rail is screen-specific (not the generic 0174AG template), that
each screen's purpose-built labels are present, that stale-reading recency
wording is framed as historical, and that safety/material discipline holds.
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


# ---------- inspector is screen-specific (keyed on screen_id) ----------
def test_inspector_dispatches_per_screen():
    cockpit = _cockpit()
    for sid in ['sid === "command_center"', 'sid === "publish_readiness"',
                'sid === "evidence_vault"', 'sid === "content_studio"',
                'sid === "content_calendar"', 'sid === "visual_export"',
                'sid === "settings_safety_policy"']:
        assert sid in cockpit, "inspector not specialized for: " + sid


def test_screen_specific_inspector_labels_present():
    cockpit = _cockpit()
    # A representative, distinct label per screen — proves no generic-only rail.
    for label in ['"Active decision"', '"Priority blocker"',          # command center
                  '"Gate checkpoint"', '"Next blocker"',              # publish readiness
                  '"Validation state"', '"Lineage health"',          # evidence vault
                  '"Manual review queue"', '"Forbidden-language watch"',  # content studio
                  '"Plan state"', '"Workflow items"',                 # calendar
                  '"Capture state"', '"Redaction proof"',             # visual export
                  '"Runtime boundaries"', '"Credential never-display"']:  # settings
        assert label in cockpit, "screen-specific inspector label missing: " + label


def test_no_generic_inspector_regression():
    cockpit = _cockpit()
    # The old generic template used these exact labels; they must not return as
    # the inspector body (specialized labels replace them).
    assert '"Why"' not in cockpit, "generic inspector 'Why' label regressed"
    assert cockpit.count('"Current state"') <= 1, "generic 'Current state' overused"


# ---------- stale recency wording reframed as historical ----------
def test_qa_caveat_framed_historical():
    cockpit = _cockpit()
    # Evidence Vault inspector must frame the 0174C capture as a historical
    # caveat, not as current recency.
    assert '"QA caveat (historical)"' in cockpit


# ---------- no fake operational controls ----------
def test_no_fake_operational_controls():
    text = _runtime_text().lower()
    for token in ["publish button", "run button", "send button", "approve button",
                  "schedule button", "connect api", "execute button", "start automation"]:
        assert token not in text, "fake operational control present: " + token
    for label in [">publish<", ">post<", ">schedule<", ">approve<", ">execute<",
                  ">connect<", ">run<", ">send<"]:
        assert label not in text, "operational button label present: " + label


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
    for cls in ["workspace-shell", "inspector-rail", "command-tile-row",
                "density-toggle", "lane-health-strip", "workflow-board"]:
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
