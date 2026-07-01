"""UI guardrail tests for V6 Platform Variant Approval Packet Preview."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V5 = ROOT / "ui" / "contentops_v5" / "src"
PLATFORM_PREVIEW = V5 / "views" / "PlatformPreview.tsx"
MANUAL_EXPORT = V5 / "views" / "ManualExportPilotVerification.tsx"
APPROVAL_QUEUE = V5 / "views" / "ApprovalQueue.tsx"
EVIDENCE_VAULT = V5 / "views" / "EvidenceVault.tsx"
ADAPTER = V5 / "data" / "platformVariantApprovalPacketPreviewAdapter.ts"

SURFACES = [PLATFORM_PREVIEW, MANUAL_EXPORT, APPROVAL_QUEUE, EVIDENCE_VAULT]
REQUIRED_PHRASES = [
    "ready_for_operator_approval_packet_review",
    "approval_packet_preview_status=approval_packet_preview_created_for_operator_review",
    "actual_operator_approval_recorded=false",
    "approval_ledger_entry_created=false",
    "platform_payloads_approved=false",
    "dispatch_outbox_ready=false",
    "ready_for_dispatch=false",
    "no llm/provider/api/env/credential/public url/live action",
]
EXTERNAL_URL_RE = re.compile(r"https?://", re.IGNORECASE)
ENABLED_LIVE_CONTROL_RE = re.compile(
    r"<button[^>]*(publish|send|dispatch|approve|schedule)|"
    r"(publish|send|dispatch|approve|schedule)[^\n]{0,80}disabled=\{false\}",
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
        assert "platformvariantapprovalpacketpreviewadapter" in text
        assert "platformvariantapprovalpacketpreviewpacket" in text


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
    assert "platform_payloads_approved\":false" in text
    assert "actual_operator_approval_recorded\":false" in text
    assert "approval_ledger_entry_created\":false" in text
    assert "approval_record_created\":false" in text
    assert "outbox_entry_created\":false" in text
    assert "dispatch_outbox_ready\":false" in text
    assert "ready_for_auto_publish\":false" in text
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
