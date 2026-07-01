"""UI guardrail tests for V6 Dispatch Outbox Dry Run."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V5 = ROOT / "ui" / "contentops_v5" / "src"
PLATFORM_PREVIEW = V5 / "views" / "PlatformPreview.tsx"
MANUAL_EXPORT = V5 / "views" / "ManualExportPilotVerification.tsx"
APPROVAL_QUEUE = V5 / "views" / "ApprovalQueue.tsx"
EVIDENCE_VAULT = V5 / "views" / "EvidenceVault.tsx"
ADAPTER = V5 / "data" / "dispatchOutboxDryRunAdapter.ts"

SURFACES = [PLATFORM_PREVIEW, MANUAL_EXPORT, APPROVAL_QUEUE, EVIDENCE_VAULT]
REQUIRED_PHRASES = [
    "dispatch_outbox_dry_run_status=dispatch_outbox_dry_run_created_for_operator_review",
    "executable_outbox_entry_created=false",
    "real_outbox_entry_created=false",
    "dispatch_outbox_ready=false",
    "dispatch_attempted=false",
    "dispatch_request_count=0",
    "webhook_request_count=0",
    "platform_api_request_count=0",
    "kill_switch_active=true",
    "ready_for_dispatch=false",
    "no llm/provider/api/env/credential/public url/live action",
]
EXTERNAL_URL_RE = re.compile(r"https?://", re.IGNORECASE)
ENABLED_LIVE_CONTROL_RE = re.compile(
    r"<button[^>]*(publish|send|dispatch|approve|schedule|retry)|"
    r"(publish|send|dispatch|approve|schedule|retry)[^\n]{0,80}disabled=\{false\}",
    re.IGNORECASE,
)


def _read(path: Path) -> str:
    return re.sub(r'\s+', '', path.read_text(encoding="utf-8").lower())


def test_surfaces_exist() -> None:
    assert ADAPTER.exists()
    for path in SURFACES:
        assert path.exists(), path


def test_surfaces_import_adapter() -> None:
    for path in SURFACES:
        text = _read(path)
        assert "dispatchoutboxdryrunadapter" in text
        assert "dispatchoutboxdryrunpacket" in text


def test_ui_safety_phrases() -> None:
    combined = "\n".join(_read(path) for path in SURFACES)
    for term in REQUIRED_PHRASES:
        normalized_term = re.sub(r'\s+', '', term.lower())
        assert normalized_term in combined, f"{term} not found in UI views"


def test_ui_has_no_external_urls_or_enabled_live_controls() -> None:
    for path in SURFACES:
        text = path.read_text(encoding="utf-8")
        assert 'href="http' not in text, path
        assert not ENABLED_LIVE_CONTROL_RE.search(text), path


def test_adapter_is_local_manual_only() -> None:
    text = _read(ADAPTER)
    assert "executable_outbox_entry_created\":false" in text
    assert "real_outbox_entry_created\":false" in text
    assert "dispatch_outbox_ready\":false" in text
    assert "dispatch_attempted\":false" in text
    assert "dispatch_request_count\":0" in text
    assert "webhook_request_count\":0" in text
    assert "platform_api_request_count\":0" in text
    assert "kill_switch_active\":true" in text
    assert "ready_for_dispatch\":false" in text
    assert "llm_provider_call_made\":false" in text
    assert "provider_call_made\":false" in text
    assert "platform_api_used\":false" in text
    assert "network_call_made\":false" in text
    assert "public_url_fetch_made\":false" in text
    assert "env_value_read_made\":false" in text
    assert "credential_read_made\":false" in text
    assert "browser_session_used\":false" in text
    assert "public_url_verification_performed\":false" in text
