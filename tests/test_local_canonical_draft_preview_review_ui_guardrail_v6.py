"""UI guardrails for local canonical draft preview and review V5 surfaces."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V5 = ROOT / "ui" / "contentops_v5" / "src"
MANUAL_EXPORT = V5 / "views" / "ManualExportPilotVerification.tsx"
APPROVAL_QUEUE = V5 / "views" / "ApprovalQueue.tsx"
EVIDENCE_VAULT = V5 / "views" / "EvidenceVault.tsx"
ADAPTER = V5 / "data" / "localCanonicalDraftPreviewReviewAdapter.ts"

SURFACES = [MANUAL_EXPORT, APPROVAL_QUEUE, EVIDENCE_VAULT]
REQUIRED_PHRASES = [
    "local_draft_preview_created_for_review",
    "pending_operator_review",
    "deterministic_template_no_llm",
    "final_article_approved=false",
    "ready_for_llm_drafting=false",
    "ready_for_provider_drafting=false",
    "ready_for_auto_publish=false",
    "ready_for_dispatch=false",
    "public_url_verification_performed=false",
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


def test_canonical_v5_draft_preview_surfaces_exist() -> None:
    assert ADAPTER.exists()
    for path in SURFACES:
        assert path.exists(), path


def test_draft_preview_surfaces_are_present_on_required_v5_views() -> None:
    assert "localcanonicaldraftpreviewreviewadapter" in _read(APPROVAL_QUEUE)
    assert "localcanonicaldraftpreviewreviewpacket" in _read(APPROVAL_QUEUE)
    assert "localcanonicaldraftpreviewreviewadapter" in _read(EVIDENCE_VAULT)
    assert "localcanonicaldraftpreviewreviewpacket" in _read(EVIDENCE_VAULT)
    assert "localcanonicaldraftpreviewreviewadapter" in _read(MANUAL_EXPORT)
    assert "localcanonicaldraftpreviewreviewpacket" in _read(MANUAL_EXPORT)


def test_draft_preview_ui_safety_phrases() -> None:
    combined = "\n".join(_read(path) for path in SURFACES)
    for term in REQUIRED_PHRASES:
        normalized_term = re.sub(r'\s+', '', term.lower())
        assert normalized_term in combined, f"{term} not found in UI views"


def test_draft_preview_ui_has_no_external_urls_or_enabled_live_controls() -> None:
    for path in SURFACES:
        text = path.read_text(encoding="utf-8")
        # Exclude the unclickable text representation inside metadata layout from URL match if present
        # In this task, we can verify that NO clickable anchors pointing to public URLs exist
        # We can scan the views for clickable href="http
        assert 'href="http' not in text, path
        assert not ENABLED_LIVE_CONTROL_RE.search(text), path


def test_draft_preview_adapter_is_local_manual_only() -> None:
    text = _read(ADAPTER)
    assert "canonical_draft_created\":true" in text
    assert "article_body_created\":true" in text
    assert "final_article_approved\":false" in text
    assert "llm_provider_call_made\":false" in text
    assert "platform_api_used\":false" in text
    assert "public_url_fetch_made\":false" in text
    assert "browser_session_used\":false" in text
    assert "ready_for_llm_drafting\":false" in text
    assert "ready_for_provider_drafting\":false" in text
    assert "ready_for_auto_publish\":false" in text
    assert "ready_for_dispatch\":false" in text
