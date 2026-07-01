from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def load(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def assert_common_false(p):
    for k in ['x_api_used','provider_call_made','network_call_made','credential_read_made','env_value_read_made','browser_session_used']:
        assert p[k] is False
    assert p['sample_scope']=='sample_fixture_only'

from live_contentops.x_publication_audit_review_metrics_summary_v6 import build_x_publication_audit_review_metrics_summary_packet
def test_x_metrics_summary_manual_only():
    audit=load('docs/automation/V6_X_MANUAL_PUBLICATION_URL_AUDIT_IMPORT/sample_x_manual_publication_url_audit_import_packet.json')
    p=load('docs/automation/V6_X_PUBLICATION_AUDIT_REVIEW_METRICS_SUMMARY/sample_x_publication_audit_review_metrics_summary_packet.json')
    assert build_x_publication_audit_review_metrics_summary_packet(audit, operator_supplied_impressions=1840, operator_supplied_likes=41, operator_supplied_replies=6, operator_supplied_reposts=8, operator_supplied_quotes=2, operator_supplied_bookmarks=13, operator_supplied_profile_visits=17, operator_supplied_followers_delta=3, operator_supplied_link_clicks=22, operator_supplied_notes='Fixture-only manual metrics entered by operator; not network/API verified.')==p
    assert p['metrics_source']=='operator_supplied_manual_entry'
    assert p['metrics_network_verified'] is False
    assert p['metrics_provider_api_used'] is False
    assert p['manual_metrics_claim_operator_supplied'] is True
    assert_common_false(p)
