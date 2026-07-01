from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def load(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def assert_common_false(p):
    for k in ['linkedin_api_used','provider_call_made','network_call_made','credential_read_made','env_value_read_made','browser_session_used']:
        assert p[k] is False
    assert p['sample_scope']=='sample_fixture_only'

from live_contentops.linkedin_manual_export_v6 import build_linkedin_manual_export_packet
def test_linkedin_manual_export_packet_fixture():
    p=load('docs/automation/V6_LINKEDIN_MANUAL_EXPORT/sample_linkedin_manual_export_packet.json')
    assert p['platform']=='linkedin'
    assert p['manual_copy_payload']['target']=='linkedin_manual_copy'
    assert p['manual_copy_only'] is True
    assert p['live_publish_allowed'] is False and p['live_publish_performed'] is False
    assert 'buy' not in p['post_body_fixture'].lower()
    assert_common_false(p)
def test_builder_is_deterministic():
    src=load('docs/automation/V6_AI_RESEARCH_CANONICAL_ARTICLE_ENGINE/sample_ai_research_canonical_article_packet.json')
    assert build_linkedin_manual_export_packet(src)==load('docs/automation/V6_LINKEDIN_MANUAL_EXPORT/sample_linkedin_manual_export_packet.json')
