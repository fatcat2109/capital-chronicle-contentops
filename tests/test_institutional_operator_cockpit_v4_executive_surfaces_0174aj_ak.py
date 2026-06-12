"""0174AJ/AK executive-surface + hardening guard tests.

Deterministic static assertions only. Lock the DecisionSpine executive header,
the productive motion token system, reduced-motion hardening, and confirm the
object-centric command model + safety invariants across all surfaces did not
regress.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "ui" / "institutional_operator_cockpit_v4"
STYLES = V4 / "styles.css"
INDEX = V4 / "index.html"
VIEW_MODEL = V4 / "view_model.js"
COCKPIT = V4 / "cockpit.js"
RUNTIME_FILES = [INDEX, STYLES, VIEW_MODEL, COCKPIT]


def _css():
    return STYLES.read_text(encoding="utf-8")


def _cockpit():
    return COCKPIT.read_text(encoding="utf-8")


def _runtime():
    return "\n".join(p.read_text(encoding="utf-8") for p in RUNTIME_FILES)


# ---------- A1. DecisionSpine ----------
def test_decision_spine_defined_and_used():
    assert "renderDecisionSpine" in _cockpit()
    assert "renderDecisionSpine(s, body)" in _cockpit()
    assert ".decision-spine" in _css()
    assert ".decision-cell" in _css()


def test_decision_spine_exposes_executive_answers():
    cockpit = _cockpit()
    for label in ['"Top blocker"', '"Evidence"', '"Allowed (local)"',
                  '"Disabled surfaces"', '"Recent delta"']:
        assert label in cockpit, "decision spine missing: " + label


def test_decision_spine_is_selectable():
    # spine decision + top-blocker cells feed the inspector (object-centric).
    cockpit = _cockpit()
    spine = cockpit.split("renderDecisionSpine", 1)[1].split("function renderCommandCenter", 1)[0]
    assert "makeSelectable" in spine, "decision spine not inspectable"
    assert 'kind: "decision"' in spine


# ---------- A2-A7. object-centric command model preserved ----------
def test_all_screens_default_inspectable_objects():
    cockpit = _cockpit()
    for sid in ['"command_center"', '"content_studio"', '"publish_readiness"',
                '"evidence_vault"', '"content_calendar"', '"visual_export"',
                '"settings_safety_policy"']:
        assert sid in cockpit, "screen object wiring missing: " + sid


def test_blocker_board_and_lanes_selectable():
    cockpit = _cockpit()
    # blocker rows + content lanes both route through makeSelectable.
    assert cockpit.count("makeSelectable") >= 5


# ---------- B1. productive motion tokens ----------
def test_motion_tokens_defined():
    css = _css()
    for tok in ["--motion-hover:", "--motion-select:", "--motion-open:",
                "--motion-trace:", "--ease-productive:"]:
        assert tok in css, "motion token missing: " + tok


def test_no_bounce_or_spring_motion():
    import re
    # strip CSS block comments so explanatory prose (e.g. "No bounce/spring")
    # is not mistaken for an actual decorative-motion declaration.
    css = re.sub(r"/\*.*?\*/", "", _css(), flags=re.S).lower()
    for token in ["cubic-bezier(0.175", "elastic", "bounce", "@keyframes spin",
                  "perspective("]:
        assert token not in css, "forbidden decorative motion: " + token


# ---------- B2. reduced-motion hardening ----------
def test_reduced_motion_covers_new_surfaces():
    css = _css()
    rm = css.split("prefers-reduced-motion")[-1]
    assert "decision-spine-head" in rm or "decision-cell" in rm


# ---------- safety invariants (must not regress) ----------
def test_no_forbidden_runtime_apis():
    text = _runtime()
    for token in ["fetch(", "XMLHttpRequest", "WebSocket", "EventSource",
                  "navigator.sendBeacon", "localStorage", "sessionStorage"]:
        assert token not in text, "forbidden runtime API: " + token


def test_no_remote_or_framework():
    text = _runtime().lower()
    for token in ["http://", "https://", "fonts.googleapis", "cdn", "unpkg",
                  "jsdelivr", "react", "tailwind"]:
        assert token not in text, "forbidden remote/framework token: " + token


def test_no_glow_or_neon_regression():
    css = _css().lower()
    for token in ["box-shadow: 0 0", "text-shadow", "#00f", "#0ff",
                  "rgba(0, 0, 255", "rgba(0,0,255"]:
        assert token not in css, "forbidden glow/neon token: " + token


def test_current_truth_not_stale():
    vm = VIEW_MODEL.read_text(encoding="utf-8")
    head = vm.split('role_label: "Current Product HEAD"', 1)[1].split("}", 1)[0]
    assert "0174AI" in head
    assert "4ffe650" not in head
