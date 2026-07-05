from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'docs/automation/V6_JIM_CANONICAL_DRAFT_FINAL_REVIEW_VARIANT_PREVIEW_PROMOTION/jim_canonical_draft_final_review_variant_preview_manifest_v0.json'
HANDOFF = ROOT / 'docs/automation/V6_JIM_CANONICAL_DRAFT_FINAL_REVIEW_VARIANT_PREVIEW_PROMOTION/jim_canonical_draft_final_review_variant_preview_promotion_v0.md'
JIM = ROOT / 'ui/contentops_v5/src/views/JimDailyRun.tsx'
FIXTURES = ROOT / 'ui/contentops_v5/src/fixtures.ts'
TYPES = ROOT / 'ui/contentops_v5/src/types.ts'
STATUS_JSON = ROOT / 'docs/status/current_project_status.json'
STATUS_MD = ROOT / 'docs/status/CURRENT_PROJECT_STATUS.md'


def test_promotion_manifest_and_handoff_are_preview_only():
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    handoff = HANDOFF.read_text(encoding='utf-8')

    assert manifest['task_label'] == 'TASK_0083_JIM_CANONICAL_DRAFT_FINAL_REVIEW_VARIANT_PREVIEW_PROMOTION_V0'
    assert manifest['status'] == 'ready_for_operator_final_review'
    assert manifest['variant_status'] == 'platform_variant_preview_created_for_operator_review'
    assert manifest['safety_flags']['platform_variants_are_preview_only'] is True
    for key in [
        'final_article_approved',
        'platform_payloads_approved',
        'ready_for_auto_publish',
        'ready_for_dispatch',
        'live_action_allowed',
        'llm_provider_call_made',
        'provider_call_made',
        'platform_api_used',
        'network_call_made',
        'browser_session_used',
        'env_value_read_made',
        'credential_read_made',
        'public_url_verification_performed',
    ]:
        assert manifest['safety_flags'][key] is False
        assert f'{key}=false' in handoff


def test_jim_cockpit_promotes_packet_without_live_controls_or_links():
    text = JIM.read_text(encoding='utf-8')
    assert 'Canonical Draft Final Review + Platform Variant Preview' in text
    assert 'canonical_draft_final_review_variant_preview' in text
    assert 'platform_variants_are_preview_only=true' in text
    assert 'ready_for_dispatch=false' in text
    assert 'public_url_verification_performed=false' in text
    assert 'href=' not in text
    for fragment in ['publish now', 'send now', 'dispatch live', 'schedule now', 'approve now']:
        assert fragment not in text.lower()


def test_typed_fixture_wiring_exists():
    assert 'CanonicalDraftFinalReviewVariantPreviewPacket' in TYPES.read_text(encoding='utf-8')
    fixtures = FIXTURES.read_text(encoding='utf-8')
    assert 'canonicalDraftFinalReviewVariantPreviewPacket' in fixtures
    assert 'canonical_draft_final_review_variant_preview' in fixtures


def test_status_promotes_task_0083_and_points_to_0084():
    status = json.loads(STATUS_JSON.read_text(encoding='utf-8'))
    md = STATUS_MD.read_text(encoding='utf-8')
    assert status['latest_accepted_task'] == 'TASK_0083_JIM_CANONICAL_DRAFT_FINAL_REVIEW_VARIANT_PREVIEW_PROMOTION_V0'
    assert status['last_updated_by_task'] == status['latest_accepted_task']
    assert status['current_product_phase'] == 'TASK 0083 Jim canonical draft final review platform variant preview promoted into cockpit baseline'
    assert 'TASK_0084_JIM_PLATFORM_VARIANT_FINAL_REVIEW_TO_APPROVAL_PACKET_PREVIEW_PROMOTION_V0' in status['next_recommended_task']
    assert 'TASK_0083_JIM_CANONICAL_DRAFT_FINAL_REVIEW_VARIANT_PREVIEW_PROMOTION_V0' in md
    assert 'TASK_0084_JIM_PLATFORM_VARIANT_FINAL_REVIEW_TO_APPROVAL_PACKET_PREVIEW_PROMOTION_V0' in md
