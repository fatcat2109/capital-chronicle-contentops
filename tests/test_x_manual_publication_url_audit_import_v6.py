from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def load(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def assert_common_false(p):
    for k in ['x_api_used','provider_call_made','network_call_made','credential_read_made','env_value_read_made','browser_session_used']:
        assert p[k] is False
    assert p['sample_scope']=='sample_fixture_only'

import pytest
from live_contentops.x_manual_publication_url_audit_import_v6 import build_x_manual_publication_url_audit_import_packet, XManualPublicationUrlAuditImportError
def test_x_url_audit_import_text_only():
    handoff=load('docs/automation/V6_X_MANUAL_OPERATOR_HANDOFF/sample_x_manual_operator_handoff_packet.json')
    p=load('docs/automation/V6_X_MANUAL_PUBLICATION_URL_AUDIT_IMPORT/sample_x_manual_publication_url_audit_import_packet.json')
    assert build_x_manual_publication_url_audit_import_packet(handoff, operator_supplied_publication_url=p['operator_supplied_publication_url'], operator_supplied_publication_timestamp=p['operator_supplied_publication_timestamp'])==p
    assert p['operator_supplied_publication_platform']=='x'
    assert p['operator_supplied_url_verification_status']=='operator_supplied_not_network_verified'
    assert p['url_network_verified'] is False
    assert p['manual_publication_claim_operator_supplied'] is True
    assert p['live_publish_performed_by_contentops'] is False
    assert_common_false(p)
def test_x_url_requires_https():
    handoff=load('docs/automation/V6_X_MANUAL_OPERATOR_HANDOFF/sample_x_manual_operator_handoff_packet.json')
    with pytest.raises(XManualPublicationUrlAuditImportError):
        build_x_manual_publication_url_audit_import_packet(handoff, operator_supplied_publication_url='http://example.com/post', operator_supplied_publication_timestamp='2026-07-01T06:00:00Z')
