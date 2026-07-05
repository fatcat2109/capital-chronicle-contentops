"""0174AI object-centric inspection + contextual command guard tests.

Deterministic static assertions only — no browser, no network. Enforces the
selected-object registry, per-screen default objects, object-detail fields,
selection wiring, safe inspect/review control language, absence of forbidden
operational labels, motion + reduced-motion support, ARIA/focus on local
inspection controls, and the standing safety/material/feature invariants.
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


# ---------- selected-object registry ----------
def test_selected_object_registry_exists():
    cockpit = _cockpit()
    for sym in ["SELECTED_OBJECT", "inspectObject", "makeSelectable",
                "selectObject", "defaultObjectForScreen", "renderSelectedObjectDetail"]:
        assert sym in cockpit, "object registry symbol missing: " + sym


def test_inspect_object_canonical_shape():
    cockpit = _cockpit()
    for field in ["kind:", "id:", "label:", "state:", "severity:", "reason:",
                  "evidence_refs:", "allowed_local_action:", "blocked_action:",
                  "caveat:", "posture:"]:
        assert field in cockpit, "canonical object field missing: " + field


def test_each_screen_has_default_object():
    cockpit = _cockpit()
    for sid in ['"command_center"', '"content_studio"', '"publish_readiness"',
                '"evidence_vault"', '"content_calendar"', '"visual_export"',
                '"settings_safety_policy"']:
        assert sid in cockpit, "default object screen missing: " + sid
    # The default-object kinds prove per-screen object specialization.
    for kind in ['"blocker"', '"content lane"', '"publish gate"', '"QA caveat"',
                 '"workflow item"', '"redaction proof"', '"policy group"']:
        assert kind in cockpit, "inspectable object kind missing: " + kind


def test_selected_object_detail_renders_fields():
    cockpit = _cockpit()
    for label in ['"Why"', '"Allowed (local)"', '"Blocked"', '"Caveat"', '"Posture"']:
        assert label in cockpit, "selected-object detail row missing: " + label


def test_evidence_path_present():
    cockpit = _cockpit()
    assert "evidence-path" in cockpit
    assert _css().find(".evidence-chip") != -1, "evidence-chip style missing"


# ---------- local controls use safe language only ----------
def test_local_controls_use_safe_language():
    cockpit = _cockpit()
    for safe in ['"Inspect Gate"', '"Select Lane"', '"Review Blocker"',
                 '"View Evidence"', '"View Redaction Proof"', '"Open Policy Group"',
                 '"Inspect Workflow Item"']:
        assert safe in cockpit, "expected safe control label missing: " + safe


def test_no_forbidden_operational_labels():
    text = _runtime_text().lower()
    for token in ["publish button", "run button", "send button", "approve button",
                  "schedule button", "connect api", "execute button", "start automation",
                  "validate credential", "promote to live", "read credentials"]:
        assert token not in text, "forbidden operational control: " + token
    for label in [">publish<", ">post<", ">schedule<", ">approve<", ">execute<",
                  ">connect<", ">dispatch<"]:
        assert label not in text, "operational button label present: " + label


# ---------- motion + reduced motion ----------
def test_motion_tokens_and_reduced_motion():
    css = _css()
    assert "--motion-select" in css, "motion token missing"
    assert "prefers-reduced-motion" in css, "reduced-motion support missing"


# ---------- accessibility / focus ----------
def test_focus_and_aria_support():
    cockpit = _cockpit()
    assert "aria-pressed" in cockpit, "aria-pressed missing on selectable objects"
    assert 'setAttribute("tabindex"' in cockpit, "keyboard reachability missing"
    assert 'e.key === "Enter"' in cockpit, "keyboard activation missing"
    assert "focus-visible" in _css(), "visible focus state missing"


# ---------- standing invariants ----------
def test_no_glow_or_neon_or_blue():
    css = _css().lower()
    for token in ["box-shadow: 0 0", "text-shadow",
                  "#00f", "#0ff", "rgba(0, 0, 255", "rgba(0,0,255"]:
        assert token not in css, "forbidden glow/neon/blue token: " + token


def test_screenshot_safe_and_redaction_preserved():
    text = _runtime_text()
    assert "SCREENSHOT_SAFE" in text
    assert "SECRET_REDACTED" in text
    assert "redaction proof" in _cockpit()


def test_no_forbidden_runtime_apis():
    text = _runtime_text()
    for token in ["fetch(", "XMLHttpRequest", "WebSocket", "EventSource",
                  "navigator.sendBeacon", "localStorage", "sessionStorage"]:
        assert token not in text, "forbidden runtime API: " + token


def test_no_remote_urls_runtime():
    text = _runtime_text().lower()
    for token in ["http://", "https://", "fonts.googleapis", "fonts.gstatic", "cdn", "unpkg", "jsdelivr"]:
        assert token not in text, "forbidden remote token: " + token


def test_no_feature_deletion():
    cockpit = _cockpit()
    for label in ['"Gate Matrix"', '"Validation Matrix"', '"Evidence Timeline"',
                  '"Caveat Registry"', '"Active Blocker Registry"',
                  '"Credential Never-Display Registry"', '"Policy Matrix"']:
        assert label in cockpit, "feature removed: " + label
