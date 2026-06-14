"""Static, deterministic tests for the 0174BU operator evidence surface
integration into the V4 cockpit.

Consistent with the existing V4 test suites, these read the JS / HTML / CSS as
text rather than executing a browser. They assert:

* load order: index.html loads operator_evidence_surface.js BEFORE cockpit.js;
* the renderer references the frozen global and defines the fail-closed gate;
* the four screen render functions + the inspector branch exist;
* no-grant invariants are present (required-false flags, no-grant label,
  explicit fail-closed/unavailable path);
* a forbidden-token scan over the new additions (no network / storage / env);
* the generated bridge artifact stays byte-identical to a fresh --check;
* the protected truth-rail head 992a7d0 and existing model truth are unchanged.
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
UI = os.path.join(REPO, "ui", "institutional_operator_cockpit_v4")

INDEX_HTML = os.path.join(UI, "index.html")
COCKPIT_JS = os.path.join(UI, "cockpit.js")
STYLES_CSS = os.path.join(UI, "styles.css")
SURFACE_JS = os.path.join(UI, "operator_evidence_surface.js")
VIEW_MODEL_JS = os.path.join(UI, "view_model.js")


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


# --------------------------------------------------------------------------- #
# Load order
# --------------------------------------------------------------------------- #
def test_index_loads_surface_before_cockpit():
    html = _read(INDEX_HTML)
    pos_surface = html.find("operator_evidence_surface.js")
    pos_view = html.find("view_model.js")
    pos_cockpit = html.find("cockpit.js")
    assert pos_surface != -1, "index.html must load operator_evidence_surface.js"
    assert pos_view != -1 and pos_cockpit != -1
    # frozen global must exist before any consumer runs
    assert pos_surface < pos_view < pos_cockpit


def test_surface_artifact_defines_frozen_global():
    js = _read(SURFACE_JS)
    assert "window.CC_OPERATOR_EVIDENCE_SURFACE" in js
    assert "Object.freeze(window.CC_OPERATOR_EVIDENCE_SURFACE)" in js


# --------------------------------------------------------------------------- #
# Renderer wiring
# --------------------------------------------------------------------------- #
def test_cockpit_references_bridge_and_defines_gate():
    js = _read(COCKPIT_JS)
    assert "window.CC_OPERATOR_EVIDENCE_SURFACE" in js
    assert "function surfaceIntegrity(" in js
    assert "function surfaceField(" in js
    assert "function surfaceInspectObject(" in js


def test_cockpit_defines_four_screen_render_functions():
    js = _read(COCKPIT_JS)
    for fn in (
        "function renderEvidenceSurfaceSummary(",
        "function renderEvidenceSurfaceHost(",
        "function renderEvidenceSurfaceNoGrant(",
        "function renderEvidenceSurfaceBoundary(",
    ):
        assert fn in js, "missing render function: " + fn


def test_render_functions_are_wired_into_screens():
    js = _read(COCKPIT_JS)
    # Command Center summary after the decision spine.
    assert "renderEvidenceSurfaceSummary(body)" in js
    # Evidence Vault primary host.
    assert "renderEvidenceSurfaceHost(body)" in js
    # Publish Readiness Tower no-grant matrix.
    assert "renderEvidenceSurfaceNoGrant(body)" in js
    # Settings / Safety boundary group.
    assert "renderEvidenceSurfaceBoundary(body)" in js


def test_inspector_has_surface_branch():
    js = _read(COCKPIT_JS)
    assert 'SELECTED_OBJECT.kind === "evidence surface"' in js


# --------------------------------------------------------------------------- #
# No-grant invariants + fail-closed
# --------------------------------------------------------------------------- #
def test_no_grant_label_surfaced():
    js = _read(COCKPIT_JS)
    assert "EVIDENCE ONLY / NO GRANT" in js


def test_required_false_flags_are_checked():
    js = _read(COCKPIT_JS)
    for flag in (
        "public_ready",
        "live_ready",
        "dispatch_ready",
        "executable_dispatch",
        "platform_api_allowed_now",
        "credential_read_allowed_now",
        "scheduler_enabled_now",
        "posting_enabled_now",
        "readiness_granted",
    ):
        assert flag in js, "required-false flag not referenced: " + flag


def test_fail_closed_path_exists():
    js = _read(COCKPIT_JS)
    assert "function renderSurfaceUnavailable(" in js
    assert "EVIDENCE SURFACE UNAVAILABLE / NO GRANT" in js
    assert "SURFACE INTEGRITY BLOCKED" in js
    # fail-closed precedence: BLOCKED and UNKNOWN states both modeled
    assert '"BLOCKED"' in js and '"UNKNOWN"' in js


# --------------------------------------------------------------------------- #
# Forbidden-token scan over the new additions
# --------------------------------------------------------------------------- #
FORBIDDEN = [
    "http://",
    "https://",
    "fetch(",
    "XMLHttpRequest",
    "WebSocket",
    "EventSource",
    "sendBeacon",
    "localStorage",
    "sessionStorage",
    "process.env",
    ".env",
]


def _new_css_section(css):
    marker = "Operator Evidence Surface primitives (0174BU)"
    idx = css.find(marker)
    assert idx != -1, "evidence-surface CSS section missing"
    return css[idx:]


def test_no_forbidden_tokens_in_new_css():
    section = _new_css_section(_read(STYLES_CSS))
    for tok in FORBIDDEN:
        assert tok not in section, "forbidden token in new CSS: " + tok


def test_no_forbidden_tokens_in_surface_block():
    js = _read(COCKPIT_JS)
    marker = "Operator Evidence Surface integration (0174BU)"
    idx = js.find(marker)
    assert idx != -1, "evidence-surface JS block missing"
    block = js[idx:]
    for tok in FORBIDDEN:
        assert tok not in block, "forbidden token in surface JS block: " + tok


def test_no_credential_or_secret_literals_in_new_js():
    js = _read(COCKPIT_JS)
    marker = "Operator Evidence Surface integration (0174BU)"
    block = js[js.find(marker):]
    # never read credentials/env; awareness is names-only prose
    assert "readFileSync" not in block
    assert "credentials" not in block.lower() or "credential read" in block.lower()


# --------------------------------------------------------------------------- #
# Determinism of the generated bridge artifact
# --------------------------------------------------------------------------- #
def test_generated_bridge_is_byte_identical_check():
    script = os.path.join(REPO, "tools", "build_operator_evidence_surface_js.py")
    if not os.path.exists(script):
        return  # generator not present in this checkout; skip silently
    result = subprocess.run(
        [sys.executable, script, "--check"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "generator --check failed (artifact drifted):\n"
        + result.stdout
        + result.stderr
    )


# --------------------------------------------------------------------------- #
# Protected truth-rail head + model truth unchanged
# --------------------------------------------------------------------------- #
def test_truth_rail_head_pinned_992a7d0():
    vm = _read(VIEW_MODEL_JS)
    assert "992a7d0" in vm, "protected current product HEAD must remain pinned"


def test_view_model_not_grant_polluted_by_surface():
    # The integration is additive in the renderer only; the canonical model must
    # not import or reference the evidence-surface global.
    vm = _read(VIEW_MODEL_JS)
    assert "CC_OPERATOR_EVIDENCE_SURFACE" not in vm
