"""UI guardrails for operator feedback backlog V5 surfaces."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V5 = ROOT / "ui" / "contentops_v5" / "src"
MANUAL_EXPORT = V5 / "views" / "ManualExportPilotVerification.tsx"
APPROVAL_QUEUE = V5 / "views" / "ApprovalQueue.tsx"
EVIDENCE_VAULT = V5 / "views" / "EvidenceVault.tsx"
ADAPTER = V5 / "data" / "operatorFeedbackBacklogAdapter.ts"

SURFACES = [MANUAL_EXPORT, APPROVAL_QUEUE, EVIDENCE_VAULT]
REQUIRED_PHRASES = [
    "operator-supplied feedback only",
    "no llm/provider call",
    "public url fetch",
    "platform api",
    "browser session",
    "publish",
    "send",
    "dispatch",
    "approve",
    "schedule",
]
FORBIDDEN_CLAIMS = [
    "auto-publish",
    "autopublish",
    "dispatch readiness",
    "public url verification",
    "llm synthesis",
    "api readiness",
    "platform auth readiness",
]
EXTERNAL_URL_RE = re.compile(r"https?://", re.IGNORECASE)
ENABLED_LIVE_CONTROL_RE = re.compile(
    r"<button[^>]*(publish|send|dispatch|approve|schedule)|"
    r"(publish|send|dispatch|approve|schedule)[^\n]{0,80}disabled=\{false\}",
    re.IGNORECASE,
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def test_canonical_v5_feedback_backlog_surfaces_exist() -> None:
    assert ADAPTER.exists()
    for path in SURFACES:
        assert path.exists(), path


def test_feedback_backlog_surfaces_are_present_on_required_v5_views() -> None:
    assert "operatorfeedbackbacklogadapter" in _read(APPROVAL_QUEUE)
    assert "operator feedback backlog" in _read(APPROVAL_QUEUE)
    assert "operatorfeedbackbacklogadapter" in _read(EVIDENCE_VAULT)
    assert "operator feedback intake and backlog evidence" in _read(EVIDENCE_VAULT)
    assert "operatorfeedbackbacklogadapter" in _read(MANUAL_EXPORT)
    assert "operator feedback backlog" in _read(MANUAL_EXPORT)


def test_feedback_backlog_ui_safety_phrases_and_no_live_claims() -> None:
    combined = "\n".join(_read(path) for path in SURFACES)
    for phrase in REQUIRED_PHRASES:
        assert phrase in combined
    for forbidden in FORBIDDEN_CLAIMS:
        assert forbidden not in combined


def test_feedback_backlog_ui_has_no_external_urls_or_enabled_live_controls() -> None:
    for path in SURFACES:
        text = path.read_text(encoding="utf-8")
        assert not EXTERNAL_URL_RE.search(text), path
        assert not ENABLED_LIVE_CONTROL_RE.search(text), path


def test_feedback_backlog_adapter_is_local_manual_only() -> None:
    text = _read(ADAPTER)
    assert "operator_supplied_only" in text
    assert "deterministic_tag_grouping_no_llm" in text
    assert "llm_provider_call_made\": false" in text
    assert "platform_api_used\": false" in text
    assert "public_url_fetch_made\": false" in text
    assert "browser_session_used\": false" in text
