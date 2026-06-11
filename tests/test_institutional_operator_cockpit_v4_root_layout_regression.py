"""Root layout regression guard tests for Operator Cockpit V4 (0174I rescue).

Catches the exact class of bug from 0174H visual QA: unstable auto-fill/auto-fit
zero-min grids (1px column collapse / vertical push-down), body/root centering,
unstable root width, and vertical clipping. Deterministic static CSS assertions
only — no browser, no network.
"""
import re
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


def _block(css: str, selector: str) -> str:
    """Return the declaration body for the first rule matching selector exactly."""
    pattern = re.escape(selector) + r"\s*\{(.*?)\}"
    m = re.search(pattern, css, re.S)
    assert m, "selector not found: " + selector
    return m.group(1)


# ---------- unstable grid pattern ----------
def test_no_unstable_autofill_grid():
    css = _css()
    assert "repeat(auto-fill, minmax(0, 1fr))" not in css
    assert "repeat(auto-fit, minmax(0, 1fr))" not in css


def test_no_autofill_or_autofit_in_grid_template():
    css = _css()
    for line in css.splitlines():
        if "grid-template-columns" in line:
            assert "auto-fill" not in line, "auto-fill in grid-template: " + line
            assert "auto-fit" not in line, "auto-fit in grid-template: " + line


# ---------- body / root anti-centering ----------
def test_html_body_not_centered():
    blk = _block(_css(), "html, body")
    assert "align-items: center" not in blk
    assert "justify-content: center" not in blk
    assert "margin: auto" not in blk


def test_html_body_not_flex_centering():
    blk = _block(_css(), "html, body")
    # body must lay out as block, not a flex centering container.
    assert "display: block" in blk


# ---------- stable root sizing ----------
def test_cockpit_root_stable_width_and_height():
    blk = _block(_css(), "#cockpit-root")
    assert "width: 100%" in blk
    assert "min-height: 100vh" in blk
    assert "margin: auto" not in blk


def test_cockpit_frame_stable_grid():
    blk = _block(_css(), ".cockpit-frame")
    assert "grid-template-columns: var(--nav-w) minmax(0, 1fr)" in blk


def test_cockpit_frame_min_width_zero():
    css = _css()
    # nav and content children must allow shrink so the frame cannot collapse.
    assert "min-width: 0" in _block(css, ".screen-nav")
    assert "min-width: 0" in _block(css, ".screen-body")


# ---------- truth rail explicit columns ----------
def test_truth_rail_explicit_columns():
    blk = _block(_css(), ".truth-rail")
    assert "repeat(2, minmax(0, 1fr))" in blk
    assert "width: 100%" in blk
    assert "min-width: 0" in blk


# ---------- scroll behavior ----------
def test_page_overflow_x_hidden():
    assert "overflow-x: hidden" in _css()


def test_matrices_scroll_internally():
    assert "overflow-x: auto" in _css()


# ---------- no fixed bottom / static footer ----------
def test_no_fixed_position():
    css = _css()
    assert "position: fixed" not in css
    assert "position:fixed" not in css


def test_footer_static():
    assert "position: static" in _css()


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
