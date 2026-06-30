from __future__ import annotations
import copy, json
from pathlib import Path
import pytest
from live_contentops.substack_manual_approval_export_evidence_v6 import SubstackApprovalExportEvidenceError, build_substack_manual_approval_export_evidence_packet

ROOT=Path(__file__).resolve().parents[1]
EXPORT_SAMPLE=ROOT/'docs/automation/V6_SUBSTACK_MANUAL_EXPORT_ARTICLE_STUDIO/sample_substack_manual_export_article_studio_packet.json'
SAMPLE=ROOT/'docs/automation/V6_SUBSTACK_MANUAL_APPROVAL_EXPORT_EVIDENCE/sample_substack_manual_approval_export_evidence_packet.json'

def _export(): return json.loads(EXPORT_SAMPLE.read_text(encoding='utf-8-sig'))
def _sample(): return json.loads(SAMPLE.read_text(encoding='utf-8-sig'))

def test_committed_sample_matches_builder() -> None:
    built=build_substack_manual_approval_export_evidence_packet(_export())
    assert _sample()==built
    assert built['approval_export_evidence_packet_id'].startswith('substack_manual_approval_export_evidence_')
    assert built['source_export_packet_id']=='substack_manual_export_e556b07116d81110'
    assert built['exact_payload_hash']=='e556b07116d81110da7f8b96f5e5d39b80d65ce16c0c190eb51cdc9fdbd1f335'

def test_stable_hash_and_packet_id() -> None:
    first=build_substack_manual_approval_export_evidence_packet(_export())
    second=build_substack_manual_approval_export_evidence_packet(_export())
    assert first['approval_export_evidence_hash']==second['approval_export_evidence_hash']
    assert first['approval_export_evidence_packet_id']==second['approval_export_evidence_packet_id']

def test_required_safety_flags_are_closed() -> None:
    packet=build_substack_manual_approval_export_evidence_packet(_export())
    assert packet['operator_review_status']=='pending_review'
    assert packet['approval_status']=='pending'
    assert packet['manual_export_status']=='ready_for_manual_copy'
    for key in ['live_publish_allowed','live_publish_performed','substack_api_used','provider_call_made','network_call_made','credential_read_made','env_value_read_made','browser_session_used','enabled_publish_send_dispatch_approve_controls']:
        assert packet[key] is False
    assert packet['sample_scope']=='sample_fixture_only'

def test_evidence_cards_cover_required_lane() -> None:
    packet=build_substack_manual_approval_export_evidence_packet(_export())
    card_types={card['card_type'] for card in packet['evidence_cards']}
    assert card_types=={'article_source_packet','substack_export_packet','approval_checkpoint','manual_copy_checklist','blocked_live_publish_state'}
    checklist={item['check_id']: item for item in packet['manual_copy_checklist']}
    assert checklist['operator_confirms_no_live_publish']['status']=='pending_review'
    assert checklist['operator_confirms_substack_api_absent']['required'] is True

def test_no_secret_env_provider_webhook_or_session_material_serialized() -> None:
    serialized=json.dumps(build_substack_manual_approval_export_evidence_packet(_export()), sort_keys=True).lower()
    for term in ['https://discord.com/api/webhooks/','discord_live_announcements_webhook=https','sk-','xoxb-','ghp_','bearer ','cookie=','localstorage=','sessionstorage=']:
        assert term not in serialized

@pytest.mark.parametrize('field,value',[('live_publish_allowed', True),('live_publish_performed', True),('provider_call_made', True),('network_call_made', True),('browser_session_used', True)])
def test_source_export_must_remain_closed(field: str, value: bool) -> None:
    export=copy.deepcopy(_export())
    export[field]=value
    with pytest.raises(SubstackApprovalExportEvidenceError):
        build_substack_manual_approval_export_evidence_packet(export)

def test_missing_manual_copy_payload_fails_closed() -> None:
    export=_export(); export.pop('manual_copy_payload')
    with pytest.raises(SubstackApprovalExportEvidenceError):
        build_substack_manual_approval_export_evidence_packet(export)
