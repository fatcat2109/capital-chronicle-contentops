"""Global Truth Rail progressive-disclosure guard tests for Operator Cockpit V4 (0174Z).

Deterministic static assertions only -- no browser, no network, no screenshots.
Enforces the 0174Z patch: the dense Global Truth Rail is wrapped in a native
details/summary disclosure that is COLLAPSED by default, a concise summary is
shown when collapsed, the top safety-lock strip stays permanently visible
OUTSIDE the disclosure, and all expanded current-vs-historical/provenance
metadata, the readable scan layer, the seven screens, and all safety
boundaries are preserved.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "ui" / "institutional_operator_cockpit_v4"
INDEX = V4 / "index.html"
STYLES = V4 / "styles.css"
VIEW_MODEL = V4 / "view_model.js"
COCKPIT = V4 / "cockpit.js"

RUNTIME_FILES = [INDEX, STYLES, VIEW_MODEL, COCKPIT]


def _css() -> str:
    return STYLES.read_text(encoding="utf-8")


def _cockpit() -> str:
    return COCKPIT.read_text(encoding="utf-8")


def _vm() -> str:
    return VIEW_MODEL.read_text(encoding="utf-8")


def _index() -> str:
    return INDEX.read_text(encoding="utf-8")


def _runtime_text() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in RUNTIME_FILES)


def _truth_rail_fn() -> str:
    """The body of renderTruthRail (disclosure builder)."""
    c = _cockpit()
    start = c.index("function renderTruthRail")
    end = c.index("function renderNav", start)
    return c[start:end]


def _safety_rail_fn() -> str:
    c = _cockpit()
    start = c.index("function renderSafetyRail")
    end = c.index("function renderTruthRail", start)
    return c[start:end]


# ---------- 1. disclosure container exists ----------
def test_truth_rail_disclosure_container_exists():
    fn = _truth_rail_fn()
    assert 'el("details", "truth-rail-disclosure")' in fn
    css = _css()
    assert ".truth-rail-disclosure" in css
    assert ".truth-rail-summary" in css


# ---------- 2. dense truth grid lives inside the disclosure body ----------
def test_dense_grid_inside_disclosure_body():
    fn = _truth_rail_fn()
    # the dense labeled grid is now built as .truth-grid and appended to details.
    assert 'el("div", "truth-grid")' in fn
    assert "details.appendChild(grid)" in fn
    # the grid is no longer the dominant first-fold rail itself.
    assert ".truth-grid" in _css()


# ---------- 3. collapsed by default ----------
def test_disclosure_collapsed_by_default():
    fn = _truth_rail_fn()
    # no `open` attribute / property may be set on initial render.
    assert 'setAttribute("open"' not in fn
    assert ".open = true" not in fn
    assert ".open=true" not in fn
    assert 'details.open' not in fn


# ---------- 4. concise summary with current state / gate / next action ----------
def test_summary_present_with_concise_current_state():
    vm = _vm()
    assert "truth_rail_summary" in vm
    for field in ["product_head", "gate", "next_action", "safety_status"]:
        assert field in vm, "missing summary field: " + field
    fn = _truth_rail_fn()
    assert "truth-rail-summary" in fn
    assert "MODEL.truth_rail_summary" in fn
    # the summary surfaces gate + next action semantics, not the full grid.
    assert "Gate" in fn
    assert "Next Action" in fn


def test_summary_is_concise_not_full_provenance_wall():
    vm = _vm()
    # the collapsed summary must not embed the historical provenance hashes.
    start = vm.index("truth_rail_summary")
    block = vm[start:vm.index("truth_rail:", start)]
    for hist in ["15b87ff", "1c03ca0", "444ef2c", "Historical Screen Provenance"]:
        assert hist not in block, "provenance leaked into collapsed summary: " + hist


# ---------- 5. safety lock strip stays OUTSIDE the disclosure ----------
def test_safety_strip_outside_disclosure():
    # safety chips are rendered into the separate #safety-rail element.
    safety_fn = _safety_rail_fn()
    assert 'getElementById("safety-rail")' in safety_fn
    assert "safety-chip" in safety_fn
    # the disclosure builder must not render safety chips inside details.
    truth_fn = _truth_rail_fn()
    assert "safety-chip" not in truth_fn
    assert "safety_locks" not in truth_fn


def test_index_keeps_safety_rail_above_and_separate_from_truth_rail():
    html = _index()
    assert 'id="safety-rail"' in html
    assert 'id="truth-rail"' in html
    # safety rail markup precedes the truth rail in the document.
    assert html.index('id="safety-rail"') < html.index('id="truth-rail"')


# ---------- 6. all safety lock tokens still present ----------
def test_all_safety_lock_tokens_present():
    vm = _vm()
    critical = [
        "LOCAL-ONLY", "REVIEW-ONLY", "NOT PUBLIC-POSTABLE", "LIVE DISABLED",
        "KILL SWITCH ACTIVE", "NO FINANCIAL ADVICE", "NO SIGNAL LANGUAGE",
    ]
    for lock in critical:
        assert lock in vm, "missing critical safety lock: " + lock
    grouped = [
        "NO PLATFORM API", "NO PROVIDER API", "NO SCHEDULER", "NO SCRAPING",
        "NO CREDENTIAL READ", "SECRET REDACTED",
    ]
    for lock in grouped:
        assert lock in vm, "missing grouped safety lock: " + lock


# ---------- 7. expanded truth metadata preserved ----------
def test_expanded_truth_metadata_preserved():
    vm = _vm()
    for label in [
        "Current Product HEAD", "Current Gate", "Next Allowed Action",
        "V4 Build Status",
        "Tested HEAD (Evidence-only Browser QA)",
        "V3 Failed-Candidate Build",
        "V2 Historical Build Candidate",
        "Reference Quarantine",
        "Historical Screen Provenance",
    ]:
        assert label in vm, "expanded truth metadata removed: " + label
    # reference-only / not-runtime-authority labels preserved.
    assert "Not Runtime Authority" in vm
    assert "reference-only" in vm.lower()


# ---------- 8. runtime copy references 0174Y and 0174Z ----------
def test_runtime_copy_references_0174y_and_0174z():
    vm = _vm()
    assert "0174Y" in vm
    assert "0174Z" in vm
    assert "progressive-disclosure" in vm or "progressive disclosure" in vm
    assert "Global Truth Rail" in vm
    assert "cognitive overload" in vm.lower()


# ---------- 9. no stale / contradictory current-truth phrases ----------
def test_no_stale_or_contradictory_phrases():
    runtime = _runtime_text()
    for stale in [
        "No Antigravity",
        "Cline patch task",
        "0174K browser QA found targeted V4 visual defects; 0174L patch applied",
        "0174L patch awaits targeted browser recheck",
    ]:
        assert stale not in runtime, "stale/contradictory phrase present: " + stale
    # final-acceptance language must not be asserted as CURRENT runtime truth.
    vm = _vm()
    current_block = vm[vm.index("truth_rail:"):vm.index("evidence_refs")]
    assert "PASS_FINAL_QA_READY" not in current_block
    assert "final accepted" not in current_block.lower()


# ---------- 10. scan layer + seven-screen routing preserved ----------
def test_scan_layer_classes_preserved():
    cockpit = _cockpit()
    for cls in ["operator-scan-layer", "operator-summary-board",
                "primary-answer", "next-action-card", "top-blocker-cards",
                "confidence-summary"]:
        assert cls in cockpit, "scan-layer class removed: " + cls
    assert "renderOperatorScanLayer(screen, body)" in cockpit


def test_seven_screen_routing_preserved():
    cockpit = _cockpit()
    vm = _vm()
    for sid in ["command_center", "content_studio", "publish_readiness",
                "evidence_vault", "content_calendar", "visual_export",
                "settings_safety_policy"]:
        assert sid in vm, "screen missing in model: " + sid
        assert sid in cockpit, "screen route missing in renderer: " + sid


# ---------- 11. evidence refs render as ids, not [object Object] ----------
def test_evidence_refs_render_as_ids():
    cockpit = _cockpit()
    assert "function evidenceRefId" in cockpit
    assert ".map(evidenceRefId)" in cockpit
    assert "[object Object]" not in _runtime_text()


# ---------- 12. no forbidden controls introduced ----------
def test_no_forbidden_controls_introduced():
    text = _runtime_text().lower()
    for token in ["<form", "<input", "type=\"submit\"", "type='submit'",
                  "publish(", "schedule(", "sendpost", "upload("]:
        assert token not in text, "forbidden control introduced: " + token


# ---------- 13. no external network / api / credential behavior ----------
def test_no_external_network_or_credential_behavior():
    text = _runtime_text()
    for token in ["fetch(", "XMLHttpRequest", "WebSocket", "EventSource",
                  "navigator.sendBeacon", "localStorage", "sessionStorage",
                  "process.env"]:
        assert token not in text, "forbidden runtime API: " + token
    low = text.lower()
    for token in ["http://", "https://", "fonts.googleapis", "cdn", "unpkg", "jsdelivr"]:
        assert token not in low, "forbidden remote token: " + token


# ---------- 14. safety chip ellipsis CSS remains intact ----------
def test_safety_chip_ellipsis_css_intact():
    css = _css()
    start = css.index(".safety-locks-cluster {")
    block = css[start:css.index("}", start)]
    assert "overflow: hidden" in block
    assert "text-overflow: ellipsis" in block
    assert "white-space: nowrap" in block
    assert "min-width: 0" in block


def test_summary_value_clips_gracefully():
    css = _css()
    start = css.index(".truth-summary-value {")
    block = css[start:css.index("}", start)]
    assert "text-overflow: ellipsis" in block
    assert "overflow: hidden" in block
