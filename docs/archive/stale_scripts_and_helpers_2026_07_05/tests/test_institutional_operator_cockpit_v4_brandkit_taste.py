"""Brandkit / taste / typography / block-grammar guard tests for Operator Cockpit V4.

Deterministic static assertions only (no browser, no network). Enforces the
0174F hardening: DESIGN.md typography tokens (Inter / JetBrains Mono local-only),
the compact type scale, instrumentation block-grammar classes, technical-matte
flat depth, and that no remote font / @import / content network was introduced.
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


def _runtime_text() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in RUNTIME_FILES)


# ---------- font strategy ----------
def test_font_tokens_defined():
    css = _css()
    assert "--font-ui:" in css
    assert "--font-mono:" in css


def test_inter_in_font_ui():
    css = _css()
    # find the --font-ui declaration line and assert Inter present.
    line = [l for l in css.splitlines() if "--font-ui:" in l][0]
    assert "Inter" in line


def test_jetbrains_mono_in_font_mono():
    css = _css()
    line = [l for l in css.splitlines() if "--font-mono:" in l][0]
    assert "JetBrains Mono" in line


def test_no_at_import_rule():
    css = _css()
    # An actual @import rule is "@import " followed by url/string; a comment
    # mentioning the word is allowed. Reject any real import statement.
    for line in css.splitlines():
        stripped = line.strip()
        if stripped.startswith("@import"):
            raise AssertionError("real @import rule present: " + line)


def test_no_remote_font_or_network_in_runtime():
    text = _runtime_text().lower()
    for token in ["http://", "https://", "fonts.googleapis", "fonts.gstatic",
                  "@import url", "cdn", "unpkg", "jsdelivr", "tailwind"]:
        assert token not in text, "forbidden remote token: " + token


# ---------- type scale ----------
def test_type_scale_tokens_exist():
    css = _css()
    for token in ["--type-micro", "--type-label", "--type-body", "--type-title", "--type-verdict"]:
        assert token in css, "missing type token: " + token

# ---------- block grammar / instrumentation classes ----------
def test_instrumentation_classes_exist():
    css = _css()
    for cls in [".instrument-panel", ".evidence-cell", ".status-ledger",
                ".proof-strip", ".blocker-rail", ".gate-matrix",
                ".registry-row", ".operator-verdict", ".data-label", ".mono-value"]:
        assert cls in css, "missing instrumentation class: " + cls


def test_instrumentation_classes_used_in_runtime():
    # at least the core instrumentation classes are actually rendered.
    cockpit = COCKPIT.read_text(encoding="utf-8")
    for cls in ["instrument-panel", "blocker-rail", "proof-strip", "gate-matrix"]:
        assert cls in cockpit, "instrumentation class not used: " + cls


# ---------- technical matte depth ----------
def test_zero_or_near_zero_radius():
    css = _css()
    assert "border-radius: 0" in css


def test_one_px_gridline_discipline():
    css = _css()
    assert "1px solid var(--gridline)" in css or "1px solid var(--outline)" in css


def test_no_glow_or_heavy_shadow():
    css = _css().lower()
    # box-shadow may appear only as an explicit reset (box-shadow: none).
    for line in css.splitlines():
        s = line.strip()
        if "box-shadow" in s:
            assert "none" in s, "non-reset box-shadow present: " + line
    assert "text-shadow" not in css
    assert "drop-shadow" not in css


def test_no_market_direction_language_in_css():
    css = _css().lower()
    for token in ["bullish", "bearish", "market direction red", "buy/sell"]:
        assert token not in css, "market-direction language in css: " + token

