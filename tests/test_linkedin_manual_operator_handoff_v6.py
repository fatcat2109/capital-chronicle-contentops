from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def load(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def assert_common_false(p):
    for k in ['linkedin_api_used','provider_call_made','network_call_made','credential_read_made','env_value_read_made','browser_session_used']:
        assert p[k] is False
    assert p['sample_scope']=='sample_fixture_only'

from live_contentops.linkedin_manual_operator_handoff_v6 import build_linkedin_manual_operator_handoff_packet
def test_linkedin_handoff_binds_export_and_evidence():
    export=load('docs/automation/V6_LINKEDIN_MANUAL_EXPORT/sample_linkedin_manual_export_packet.json')
    evidence=load('docs/automation/V6_LINKEDIN_MANUAL_APPROVAL_EXPORT_EVIDENCE/sample_linkedin_manual_approval_export_evidence_packet.json')
    p=load('docs/automation/V6_LINKEDIN_MANUAL_OPERATOR_HANDOFF/sample_linkedin_manual_operator_handoff_packet.json')
    assert build_linkedin_manual_operator_handoff_packet(export,evidence)==p
    assert p['source_export_payload_hash']==export['exact_payload_hash']
    assert p['approval_export_evidence_hash']==evidence['approval_export_evidence_hash']
    assert p['manual_copy_only'] is True
    assert p['enabled_publish_send_dispatch_approve_controls'] is False
    assert_common_false(p)
