"""North-star visual polish guard tests for Operator Cockpit V4 (0174N).

Deterministic static assertions only — no browser, no network. Enforces the
0174N polish: compact header classes, Command Center hierarchy classes,
Content Studio lane polish, Evidence Vault audit hierarchy, sparse-screen
governor, low-emphasis footer, and no safety/layout regression.
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


# ---------- compact header / truth rail ----------
def test_compact_header_classes_defined():
    css = _css()
    for cls in [".truth-cell-primary", ".truth-cell-secondary",
                ".provenance-cell", ".safety-strip-compact", ".compact-truth-rail"]:
        assert cls in css, "missing header class: " + cls


# ---------- Command Center hierarchy ----------
def test_command_center_hierarchy_classes_defined():
    css = _css()
    for cls in [".primary-command-board", ".incident-board",
                ".proof-ledger-board", ".counter-strip"]:
        assert cls in css, "missing CC class: " + cls


def test_command_center_hierarchy_classes_used():
    cockpit = _cockpit()
    for cls in ["incident-board", "proof-ledger-board", "counter-strip"]:
        assert cls in cockpit, "CC class not used: " + cls


# ---------- Content Studio polish ----------
def test_content_studio_polish_classes_defined_and_used():
    css = _css()
    cockpit = _cockpit()
    for cls in [".lane-gate-rail", ".lane-readiness-strip"]:
        assert cls in css, "missing lane class in CSS: " + cls
    for cls in ["lane-gate-rail", "lane-readiness-strip"]:
        assert cls in cockpit, "lane class not used: " + cls
    assert "lane-control-board" in cockpit or "lane-verdict-cell" in cockpit


# ---------- Evidence Vault hierarchy ----------
def test_evidence_vault_hierarchy_classes_defined_and_used():
    css = _css()
    cockpit = _cockpit()
    for cls in [".audit-room-grid", ".audit-triad", ".confidence-legend-compact",
                ".evidence-qa-caveat"]:
        assert cls in css, "missing vault class in CSS: " + cls
    for cls in ["audit-room-grid", "audit-triad"]:
        assert cls in cockpit, "vault class not used: " + cls


# ---------- evidence ref render fix (0174P) ----------
def test_evidence_ref_helper_present():
    cockpit = _cockpit()
    assert "function evidenceRefId" in cockpit
    assert "evidence_id" in cockpit


def test_no_direct_object_join_on_evidence_refs():
    cockpit = _cockpit()
    # the prior bug: joining objects directly produced "[object Object]".
    assert 'MODEL.evidence_refs.slice(0, 6).join(" / ")' not in cockpit
    assert ".map(evidenceRefId)" in cockpit


def test_no_object_object_literal_in_runtime():
    text = _runtime_text()
    assert "[object Object]" not in text


# ---------- sparse-screen governor ----------
def test_sparse_screen_governor_defined_and_used():
    css = _css()
    cockpit = _cockpit()
    assert ".secondary-inspection-rail" in css or ".screen-summary-rail" in css
    assert ".empty-space-governor" in css
    assert "secondary-inspection-rail" in cockpit or "screen-summary-rail" in cockpit
    assert "empty-space-governor" in cockpit


# ---------- footer not fixed ----------
def test_footer_not_fixed():
    css = _css()
    assert "position: fixed" not in css
    assert "position:fixed" not in css
    assert ".audit-footer" in css


# ---------- no root layout regression ----------
def test_no_unstable_grid():
    css = _css()
    assert "repeat(auto-fill, minmax(0, 1fr))" not in css
    assert "repeat(auto-fit, minmax(0, 1fr))" not in css


# ---------- prior regressions still hold ----------
def test_evidence_vault_registries_present():
    cockpit = _cockpit()
    assert '"Caveat Registry"' in cockpit
    assert '"Forbidden-Scope Registry"' in cockpit
    assert '"Active Blocker Registry"' in cockpit


def test_no_stale_0174e_gate_copy():
    assert "Awaiting ChatGPT audit of 0174E" not in VIEW_MODEL.read_text(encoding="utf-8")


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
