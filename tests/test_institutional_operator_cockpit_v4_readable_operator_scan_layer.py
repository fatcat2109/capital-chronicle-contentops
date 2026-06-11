"""Readable operator scan layer guard tests for Operator Cockpit V4 (0174S).

Deterministic static assertions only — no browser, no network. Enforces the
0174S readable scan layer: scan-layer classes defined+used, readable type
scale, detail sections preserved (no feature deletion), and no safety/runtime
regression.
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


# ---------- scan layer defined + used ----------
def test_scan_layer_classes_defined():
    css = _css()
    for cls in [".operator-scan-layer", ".operator-summary-board",
                ".primary-answer", ".next-action-card", ".confidence-summary"]:
        assert cls in css, "missing scan-layer class in CSS: " + cls


def test_scan_layer_classes_used():
    cockpit = _cockpit()
    for cls in ["operator-scan-layer", "operator-summary-board",
                "primary-answer", "next-action-card", "confidence-summary"]:
        assert cls in cockpit, "scan-layer class not used: " + cls


def test_scan_layer_rendered_for_every_screen():
    cockpit = _cockpit()
    # the scan layer renderer is called once in the dispatcher before detail.
    assert "renderOperatorScanLayer(screen, body)" in cockpit


# ---------- readable typography ----------
def test_readable_type_scale_defined():
    css = _css()
    for v in ["--type-readable-body", "--type-primary-answer", "--type-summary"]:
        assert v in css, "missing type var: " + v
    assert "readable-body-copy" in css
    assert "reduced-mono-prose" in css


def test_readable_body_not_below_13px():
    css = _css()
    # key readable type tokens must stay at/above 13px.
    assert "--type-readable-body: 13.5px" in css
    assert "--type-summary: 14px" in css
    assert "--type-body: 13px" in css


# ---------- detail preservation (no feature deletion) ----------
def test_detail_sections_preserved():
    cockpit = _cockpit()
    for label in ['"Gate Matrix"', '"Validation Matrix"', '"Evidence Timeline"',
                  '"Caveat Registry"', '"Forbidden-Scope Registry"',
                  '"Active Blocker Registry"', '"Credential Never-Display Registry"']:
        assert label in cockpit, "detail section removed: " + label


def test_content_studio_detail_preserved():
    cockpit = _cockpit()
    for cls in ["lane-limits", "lane-checklist", "lane-evidence-strip"]:
        assert cls in cockpit, "content studio detail removed: " + cls


def test_visual_export_detail_preserved():
    cockpit = _cockpit().lower()
    assert "redaction" in cockpit
    assert "limitation" in cockpit


def test_seven_screens_present():
    vm = _vm()
    for sid in ["command_center", "content_studio", "publish_readiness",
                "evidence_vault", "content_calendar", "visual_export",
                "settings_safety_policy"]:
        assert sid in vm, "screen missing: " + sid


# ---------- evidence ref regression still fixed ----------
def test_evidence_ref_helper_still_used():
    cockpit = _cockpit()
    assert ".map(evidenceRefId)" in cockpit


def test_no_object_object_regression():
    assert "[object Object]" not in _runtime_text()


# ---------- safety locks preserved ----------
def test_safety_locks_preserved():
    vm = _vm()
    for lock in ["LOCAL-ONLY", "REVIEW-ONLY", "NOT PUBLIC-POSTABLE",
                 "LIVE DISABLED", "KILL SWITCH ACTIVE", "NO FINANCIAL ADVICE",
                 "NO SIGNAL LANGUAGE"]:
        assert lock in vm, "safety lock removed: " + lock


# ---------- runtime safety ----------
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
