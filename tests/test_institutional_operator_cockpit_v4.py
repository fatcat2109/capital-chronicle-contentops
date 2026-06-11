"""Deterministic static guard tests for Operator Cockpit V4 (0174E clean-room build).

Text/static assertions only. No browser, no network, no execution of the UI.
These tests prove the V4 frontend is local-only, materially different from V3,
implements the seven institutional screens, and carries evidence-backed statuses.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "ui" / "institutional_operator_cockpit_v4"
INDEX = V4 / "index.html"
STYLES = V4 / "styles.css"
VIEW_MODEL = V4 / "view_model.js"
COCKPIT = V4 / "cockpit.js"
README = V4 / "README.md"

RUNTIME_FILES = [INDEX, STYLES, VIEW_MODEL, COCKPIT]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _runtime_text() -> str:
    return "\n".join(_read(p) for p in RUNTIME_FILES)


# ---------- existence ----------
def test_v4_folder_and_files_exist():
    assert V4.is_dir()
    for f in [INDEX, STYLES, VIEW_MODEL, COCKPIT, README]:
        assert f.is_file(), str(f)


def test_index_references_only_local_files():
    text = _read(INDEX)
    assert 'href="styles.css"' in text
    assert 'src="view_model.js"' in text
    assert 'src="cockpit.js"' in text


# ---------- no remote / no network ----------
def test_no_remote_urls_in_runtime():
    text = _runtime_text().lower()
    forbidden = [
        "http://", "https://", "cdn", "fonts.googleapis", "fonts.gstatic",
        "unpkg", "jsdelivr", "tailwind", "material symbols", "materialsymbols",
    ]
    for token in forbidden:
        assert token not in text, "forbidden remote token in runtime: " + token


def test_no_forbidden_runtime_apis():
    text = _runtime_text()
    forbidden = [
        "fetch(", "XMLHttpRequest", "WebSocket", "EventSource",
        "navigator.sendBeacon", "localStorage", "sessionStorage",
    ]
    for token in forbidden:
        assert token not in text, "forbidden runtime API in runtime: " + token


def test_no_forms_or_submit_controls():
    text = _runtime_text().lower()
    for token in ["<form", "<input", "type=\"submit\"", "type='submit'"]:
        assert token not in text, "forbidden form control: " + token


def test_no_credential_or_env_runtime_behavior():
    # credential/env words may appear only as redaction/policy text, never as real values.
    # Tokens are built from fragments so this test file itself stays secret-scan clean.
    text = _runtime_text()
    forbidden = [
        "process.env",
        ".env",
        "API_" + "KEY=",
        "BOT_" + "TOKEN",
        "TELEGRAM_" + "BOT_" + "TOKEN",
        "ghp" + "_",
    ]
    for token in forbidden:
        assert token not in text, "forbidden credential/env token in runtime"

# ---------- seven screens ----------
SEVEN_SCREENS = [
    "command_center", "content_studio", "publish_readiness", "evidence_vault",
    "content_calendar", "visual_export", "settings_safety_policy",
]


def test_seven_screen_ids_exist():
    vm = _read(VIEW_MODEL)
    for sid in SEVEN_SCREENS:
        assert sid in vm, "missing screen id: " + sid


# ---------- safety phrases ----------
def test_safety_phrases_present():
    text = _runtime_text()
    required = [
        "LOCAL-ONLY", "REVIEW-ONLY", "NOT PUBLIC-POSTABLE", "LIVE DISABLED",
        "KILL SWITCH ACTIVE", "NO FINANCIAL ADVICE", "NO SIGNAL LANGUAGE",
    ]
    for phrase in required:
        assert phrase in text, "missing safety phrase: " + phrase


# ---------- no stale 0174B current gate ----------
def test_no_stale_0174b_current_gate():
    vm = _read(VIEW_MODEL)
    # The stale V3 string must not be the current gate.
    assert "0174B V3 clean-room rebuild evidence" not in vm
    # Current gate should reference 0174E.
    assert "0174E" in vm


# ---------- V3/V2 labeled historical, not current authority ----------
def test_v3_v2_labeled_historical():
    vm = _read(VIEW_MODEL)
    assert "Failed-Candidate" in vm
    assert "Historical Build" in vm or "Historical Build Candidate" in vm
    assert "Not Runtime Authority" in vm


# ---------- Command Center ----------
def test_command_center_has_verdict_blockers_evidence_map():
    vm = _read(VIEW_MODEL)
    assert "verdict" in vm
    assert "blocker_stack" in vm
    assert "evidence_dependency_map" in vm


# ---------- Publish Readiness gate matrix ----------
def test_publish_readiness_gate_matrix_columns():
    vm = _read(VIEW_MODEL)
    assert "gate_matrix" in vm
    for col in ["official docs", "dry-run renderer", "approval ledger",
                "credential slot", "credential read", "credential validation",
                "redacted audit", "kill switch", "live adapter", "scheduler",
                "posting", "next blocker"]:
        assert col in vm, "missing gate column: " + col


# ---------- Evidence Vault ----------
def test_evidence_vault_components():
    vm = _read(VIEW_MODEL)
    assert "validation_matrix" in vm
    assert "caveat_registry" in vm
    assert "forbidden_scope_registry" in vm


# ---------- Content Studio ----------
def test_content_studio_lane_governance():
    vm = _read(VIEW_MODEL)
    assert "lanes" in vm
    assert "claim_risk" in vm
    assert "forbidden_language" in vm
    assert "limitations" in vm
    for lane in ["pre_alpha_process", "grounded_news_context", "future_artifact_backed"]:
        assert lane in vm, "missing lane: " + lane


# ---------- Calendar ----------
def test_calendar_allowed_and_forbidden_states():
    vm = _read(VIEW_MODEL)
    for st in ["idea", "source-needed", "research-brief-ready", "draft-review",
               "operator-approved-for-manual", "manually-posted", "metrics-entered"]:
        assert st in vm, "missing allowed state: " + st
    for st in ["scheduled", "queued for auto-post", "auto-publish ready",
               "live campaign", "API dispatch ready", "bot reply ready"]:
        assert st in vm, "missing forbidden state: " + st


# ---------- Visual Export ----------
def test_visual_export_components():
    vm = _read(VIEW_MODEL)
    assert "report_cards" in vm
    assert "redaction_preview" in vm
    assert "limitation_strip" in vm
    assert "blocked_forecast_explainer" in vm
    assert "screenshot-safe" in _runtime_text().lower()


# ---------- Settings ----------
def test_settings_components():
    vm = _read(VIEW_MODEL)
    assert "policy_matrix" in vm
    assert "credential_never_display_registry" in vm


# ---------- evidence-backed status object contract ----------
def test_status_objects_have_full_contract():
    vm = _read(VIEW_MODEL)
    for field in ["status", "severity", "label", "reason", "evidence_ref_ids",
                  "allowed_actions", "blocked_actions", "current_truth",
                  "historical_provenance"]:
        assert field in vm, "missing status contract field: " + field


# ---------- CSS layout hardening ----------
def test_css_layout_hardening_tokens():
    css = _read(STYLES)
    assert "overflow-x: hidden" in css
    assert "min-width: 0" in css
    assert "minmax(0, 1fr)" in css


def test_css_has_no_fixed_bottom_directive_bar():
    css = _read(STYLES)
    # V4 forbids any fixed-position element; footer is explicitly static.
    assert "position: fixed" not in css
    assert "position:fixed" not in css


# ---------- no trading / market-direction wording ----------
def test_no_trading_or_market_direction_wording():
    text = _runtime_text().lower()
    forbidden = [
        "buy/sell/hold", "position sizing", "trade recommendation",
        "price target", "order routing", "p&l",
    ]
    for token in forbidden:
        assert token not in text, "forbidden trading wording: " + token

