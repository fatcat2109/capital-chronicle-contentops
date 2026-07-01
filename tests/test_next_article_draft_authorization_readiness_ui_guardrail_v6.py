"""UI guardrails for next article draft authorization and readiness V5 surfaces."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V5 = ROOT / "ui" / "contentops_v5" / "src"
MANUAL_EXPORT = V5 / "views" / "ManualExportPilotVerification.tsx"
APPROVAL_QUEUE = V5 / "views" / "ApprovalQueue.tsx"
EVIDENCE_VAULT = V5 / "views" / "EvidenceVault.tsx"
ADAPTER = V5 / "data" / "nextArticleDraftAuthorizationReadinessAdapter.ts"

SURFACES = [MANUAL_EXPORT, APPROVAL_QUEUE, EVIDENCE_VAULT]
REQUIRED_PHRASES = [
    "operator_drafting_authorization_recorded",
    "local_canonical_draft_preparation_only",
    "ready_for_local_canonical_draft_workflow=true",
    "ready_for_llm_drafting=false",
    "ready_for_provider_drafting=false",
    "canonical_draft_created=false",
    "article_body_created=false",
    "ready_for_auto_publish=false",
    "ready_for_dispatch=false",
    "no llm/provider call",
]
EXTERNAL_URL_RE = re.compile(r"https?://", re.IGNORECASE)
ENABLED_LIVE_CONTROL_RE = re.compile(
    r"<button[^>]*(publish|send|dispatch|approve|schedule)|"
    r"(publish|send|dispatch|approve|schedule)[^\n]{0,80}disabled=\{false\}",
    re.IGNORECASE,
)


def _read(path: Path) -> str:
    return re.sub(r'\s+', '', path.read_text(encoding="utf-8").lower())


def test_canonical_v5_draft_auth_surfaces_exist() -> None:
    assert ADAPTER.exists()
    for path in SURFACES:
        assert path.exists(), path


def test_draft_auth_surfaces_are_present_on_required_v5_views() -> None:
    assert "nextarticledraftauthorizationreadinessadapter" in _read(APPROVAL_QUEUE)
    assert "nextarticledraftauthorizationreadinesspacket" in _read(APPROVAL_QUEUE)
    assert "nextarticledraftauthorizationreadinessadapter" in _read(EVIDENCE_VAULT)
    assert "nextarticledraftauthorizationreadinesspacket" in _read(EVIDENCE_VAULT)
    assert "nextarticledraftauthorizationreadinessadapter" in _read(MANUAL_EXPORT)
    assert "nextarticledraftauthorizationreadinesspacket" in _read(MANUAL_EXPORT)


def test_draft_auth_ui_safety_phrases() -> None:
    combined = "\n".join(_read(path) for path in SURFACES)
    for phrase in REQUIRED_PHRASES:
        normalized_phrase = re.sub(r'\s+', '', phrase.lower())
        assert normalized_phrase in combined, f"{phrase} not found in UI views"


def test_draft_auth_ui_has_no_external_urls_or_enabled_live_controls() -> None:
    for path in SURFACES:
        text = path.read_text(encoding="utf-8")
        assert not EXTERNAL_URL_RE.search(text), path
        assert not ENABLED_LIVE_CONTROL_RE.search(text), path


def test_draft_auth_adapter_is_local_manual_only() -> None:
    text = _read(ADAPTER)
    assert "ready_for_local_canonical_draft_workflow\":true" in text
    assert "llm_provider_call_made\":false" in text
    assert "platform_api_used\":false" in text
    assert "public_url_fetch_made\":false" in text
    assert "browser_session_used\":false" in text
    assert "ready_for_llm_drafting\":false" in text
    assert "ready_for_provider_drafting\":false" in text
    assert "canonical_draft_created\":false" in text
    assert "article_body_created\":false" in text
    assert "ready_for_auto_publish\":false" in text
    assert "ready_for_dispatch\":false" in text
