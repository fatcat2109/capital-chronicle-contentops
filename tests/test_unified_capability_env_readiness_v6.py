import json
from dataclasses import asdict
from pathlib import Path
from live_contentops.unified_capability_env_readiness_v6 import collect_key_presence, make_unified_capability_env_readiness_packet, sample_packet

def _by_id(packet):
    return {c['capability_id']: c for c in asdict(packet)['capabilities']}

def test_synthetic_env_presence_and_statuses():
    env={'DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK':'discord-secret','TELEGRAM_BOT_TOKEN':'telegram-secret','OPENAI_API_KEY':'openai-secret'}
    pkt=make_unified_capability_env_readiness_packet(env=env,dotenv_path='missing.env',scan_mode='process_env_only')
    data=asdict(pkt); caps=_by_id(pkt)
    assert data['env_scan']['scan_mode']=='process_env_only'
    assert data['env_scan']['key_presence']['DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK'] is True
    assert data['env_scan']['key_presence']['TELEGRAM_BOT_TOKEN'] is True
    assert data['env_scan']['key_presence']['TELEGRAM_CHAT_ID'] is False
    assert caps['discord_webhook']['capability_status']=='configured_for_supervised_live_scope_candidate'
    assert caps['telegram_bot']['capability_status']=='unavailable'
    assert caps['ai_provider_research_writer']['capability_status']=='configured_for_dry_run'
    assert caps['browser_operator']['capability_status']=='configured_for_dry_run'
    assert caps['manual_export_fallback']['capability_status']=='configured_for_dry_run'

def test_no_raw_values_or_value_derivatives_serialized():
    raw=['discord-secret','telegram-secret','openai-secret','anthropic-secret']
    env={'DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK':raw[0],'TELEGRAM_BOT_TOKEN':raw[1],'OPENAI_API_KEY':raw[2],'ANTHROPIC_API_KEY':raw[3]}
    text=json.dumps(asdict(make_unified_capability_env_readiness_packet(env=env,dotenv_path='missing.env',scan_mode='process_env_only')))
    for value in raw: assert value not in text
    data=json.loads(text)
    assert data['raw_secret_values_serialized'] is False
    for term in ['value_lengths_serialized','value_prefixes_serialized','value_suffixes_serialized','value_hashes_serialized','value_digests_serialized','env_lines_serialized']:
        assert data[term] is False
        assert data['env_scan'][term] is False

def test_missing_dotenv_not_blocker(tmp_path):
    missing=tmp_path/'absent.env'
    scan=collect_key_presence(env={},dotenv_path=missing,scan_mode='both')
    assert scan.dotenv_path_present is False
    assert scan.dotenv_missing_is_blocker is False

def test_dotenv_key_names_only(tmp_path):
    dot=tmp_path/'.env'
    dot.write_text('DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK=never-serialize-this\n# comment\nTELEGRAM_CHAT_ID=also-secret\n',encoding='utf-8')
    pkt=make_unified_capability_env_readiness_packet(env={},dotenv_path=dot,scan_mode='dotenv_key_name_presence_only')
    data=asdict(pkt); text=json.dumps(data)
    assert data['env_scan']['key_presence']['DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK'] is True
    assert data['env_scan']['key_presence']['TELEGRAM_CHAT_ID'] is True
    assert 'never-serialize-this' not in text
    assert 'also-secret' not in text

def test_live_write_separate_scope_for_provider_capabilities():
    pkt=sample_packet(); data=asdict(pkt)
    assert data['live_provider_write_performed'] is False
    assert data['provider_live_write_requires_separate_scope'] is True
    for c in data['capabilities']:
        if c['capability_id'] in {'discord_webhook','telegram_bot','substack_manual_or_browser_compose'}:
            assert c['live_write_requires_separate_scope'] is True

def test_sample_packet_has_no_secret_like_values():
    text=json.dumps(asdict(sample_packet()),sort_keys=True)
    bad=['http://','https://','Bearer ','sk-','xoxb-','never-serialize','secret-value','.env=']
    for term in bad: assert term.lower() not in text.lower()
    assert 'TASK_CONTENTOPS_V6_DISCORD_DRY_RUN_OUTBOX_AND_OPERATOR_APPROVAL_SPINE_HEAVY_BATCH_V0' in text

def test_static_no_forbidden_runtime_or_secret_derivative_code():
    src=Path('live_contentops/unified_capability_env_readiness_v6.py').read_text(encoding='utf-8-sig').lower()
    for bad in ['requests','httpx','urllib','webbrowser','selenium','playwright','discord.com/api','api/webhooks','post(','authorization','content-type','hexdigest(','digest(','len(','endswith(']:
        assert bad not in src, bad

def test_recent_gate_status_constants_are_current():
    ep=Path('live_contentops/endpoint_allowlist_gate_from_official_provider_docs_scope_v6.py').read_text(encoding='utf-8-sig')
    rt=Path('live_contentops/provider_runtime_authority_gate_from_endpoint_allowlist_v6.py').read_text(encoding='utf-8-sig')
    ch=Path('live_contentops/credential_hydration_gate_from_provider_runtime_authority_v6.py').read_text(encoding='utf-8-sig')
    assert 'dispatch_execution_preparation_ready_for_future_provider_scoped_dispatch_execution_task_only' not in ep
    assert 'dispatch_execution_preparation_ready_for_future_provider_scoped_dispatch_execution_task_only' not in rt
    assert 'dispatch_execution_preparation_ready_for_future_provider_scoped_dispatch_execution_task_only' not in ch
