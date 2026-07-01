from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def load(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def assert_common_false(p):
    for k in ['linkedin_api_used','provider_call_made','network_call_made','credential_read_made','env_value_read_made','browser_session_used']:
        assert p[k] is False
    assert p['sample_scope']=='sample_fixture_only'

from live_contentops.linkedin_publication_audit_review_metrics_summary_v6 import build_linkedin_publication_audit_review_metrics_summary_packet
def test_linkedin_metrics_summary_manual_only():
    audit=load('docs/automation/V6_LINKEDIN_MANUAL_PUBLICATION_URL_AUDIT_IMPORT/sample_linkedin_manual_publication_url_audit_import_packet.json')
    p=load('docs/automation/V6_LINKEDIN_PUBLICATION_AUDIT_REVIEW_METRICS_SUMMARY/sample_linkedin_publication_audit_review_metrics_summary_packet.json')
    assert build_linkedin_publication_audit_review_metrics_summary_packet(audit, operator_supplied_impressions=2310, operator_supplied_reactions=67, operator_supplied_comments=9, operator_supplied_reposts=4, operator_supplied_clicks=33, operator_supplied_profile_views=21, operator_supplied_followers_delta=6, operator_supplied_notes='Fixture LinkedIn metrics for evaluation purposes only.')==p
    assert p['metrics_source']=='operator_supplied_manual_entry'
    assert p['metrics_network_verified'] is False
    assert p['metrics_provider_api_used'] is False
    assert p['manual_metrics_claim_operator_supplied'] is True
    assert_common_false(p)
