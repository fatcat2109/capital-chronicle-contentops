from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def load(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def assert_common_false(p):
    for k in ['linkedin_api_used','provider_call_made','network_call_made','credential_read_made','env_value_read_made','browser_session_used']:
        assert p[k] is False
    assert p['sample_scope']=='sample_fixture_only'

from live_contentops.linkedin_manual_approval_export_evidence_v6 import build_linkedin_manual_approval_export_evidence_packet
def test_linkedin_approval_evidence_binds_export():
    export=load('docs/automation/V6_LINKEDIN_MANUAL_EXPORT/sample_linkedin_manual_export_packet.json')
    p=load('docs/automation/V6_LINKEDIN_MANUAL_APPROVAL_EXPORT_EVIDENCE/sample_linkedin_manual_approval_export_evidence_packet.json')
    assert build_linkedin_manual_approval_export_evidence_packet(export)==p
    assert p['source_export_packet_id']==export['export_packet_id']
    assert p['exact_payload_hash']==export['exact_payload_hash']
    assert p['approval_status']=='pending'
    assert 'schedule' in p['blocked_controls']
    assert p['enabled_publish_send_dispatch_approve_controls'] is False
    assert_common_false(p)
