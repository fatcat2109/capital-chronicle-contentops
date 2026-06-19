from dataclasses import replace
from pathlib import Path
from live_contentops import content_performance_review_editorial_feedback_contract as ud
from live_contentops import manual_publish_record_metrics_ledger_contract as uc
from live_contentops import redacted_immutable_audit_ledger_v2_contract as u9

def _fixture(**metric_overrides):
    pkt=uc.build_contract_packet(); p=pkt.manual_publish_records[0]
    base={"impressions":10,"views":9,"likes":2,"shares":1}
    params={"metrics":base,"metric_observed_at_epoch":1400,"metric_recorded_at_epoch":1500,"operator_identity_ref":"operator:jim:redacted","metric_source_class":uc.METRIC_SOURCE_PLATFORM_UI}
    params.update(metric_overrides)
    m=uc.build_manual_metrics_record(publish_record=p,**params)
    r=ud.build_performance_review(p,m); s=ud.build_feedback_signal(r); l=ud.build_feedback_loop_packet((r,),(s,)); v=ud.validate_content_performance(r,l,p,m)
    return p,m,r,s,l,v

def test_packet_deterministic_review_only_and_next_gate():
    a=ud.build_contract_packet(); b=ud.build_contract_packet()
    assert a==b and a.packet_hash==b.packet_hash
    assert a.all_feedback_review_only is True
    assert a.no_api_verification and a.no_scraping and a.no_auto_generation
    assert a.no_auto_publish and a.no_dispatch and a.no_public_claim_authorized
    assert a.next_required_gate=="TASK_CONTENTOPS_0174UE_LOCAL_CONTENT_GOVERNANCE_SUMMARY_MART_CONTRACT_V0"

def test_valid_manual_metrics_make_feedback_but_no_public_truth_or_dispatch():
    _,_,r,s,l,v=_fixture()
    assert r.performance_interpretation_class=="useful_learning_signal"
    assert r.can_create_editorial_feedback and r.can_create_content_idea
    assert s.recommended_future_action_class=="create_new_content_idea_candidate"
    assert l.feedback_loop_status==ud.REVIEW_STATUS
    assert v.validation_status==ud.VALID
    assert not r.public_claim_authorized and not s.public_postable and not l.can_dispatch

def test_incomplete_metrics_hold_for_more_observations():
    _,_,r,s,l,v=_fixture(metrics={"impressions":1})
    assert r.metric_quality_class=="incomplete_manual_snapshot"
    assert s.feedback_class=="insufficient_data_hold"
    assert l.can_dispatch is False and l.can_approve is False
    assert v.validation_status==ud.VALID

def test_blockers_for_hash_platform_negative_time_api_scraped_future():
    p,m,_,_,_,_=_fixture(source_payload_hash="bad",platform_id="bad")
    r=ud.build_performance_review(p,m)
    assert ud.BLOCKERS["hash"] in r.blocked_reasons and ud.BLOCKERS["platform"] in r.blocked_reasons
    for kwargs,key in [({"metrics":{"impressions":-1}},"negative"),({"metric_observed_at_epoch":1},"time"),({"metric_values_are_api_verified":True},"api"),({"metric_values_are_scraped":True},"scraped"),({"metric_source_class":uc.METRIC_SOURCE_FUTURE_API_BLOCKED},"future")]:
        _,_,r,_,_,v=_fixture(**kwargs)
        assert ud.BLOCKERS[key] in r.blocked_reasons
        assert v.validation_status==ud.BLOCKED

def test_feedback_loop_cannot_approve_generate_publish_dispatch():
    _,_,r,s,l,_=_fixture()
    assert r.can_create_approval is False and r.can_dispatch is False
    assert s.required_human_review is True
    assert s.can_auto_generate_content is False and s.can_auto_publish is False
    assert l.can_approve is False and l.can_dispatch is False and l.public_postable is False
    assert l.can_update_platform_defaults is False

def test_u9_redacted_ledger_entries_and_no_secret_leakage():
    pkt=ud.build_contract_packet(); raw=ud._json(pkt)
    assert pkt.audit_ledger_entries[0].previous_entry_hash==u9.GENESIS_HASH
    assert pkt.audit_ledger_entries[1].previous_entry_hash==pkt.audit_ledger_entries[0].entry_hash
    assert pkt.all_records_redacted is True
    for needle in ["raw-secret","operator@example.com","token=raw-secret","credential_hydrated\":true","network_performed\":true"]:
        assert needle not in raw

def test_artifact_writer_locked_to_docs_automation_0174ud(tmp_path):
    repo=tmp_path/"repo"; repo.mkdir(); result=ud.write_artifacts(repo_root=repo)
    assert Path(result["packet_path"]).relative_to(repo)==ud.DOC_REL_DIR/ud.PACKET_FILENAME
    assert Path(result["runbook_path"]).relative_to(repo)==ud.DOC_REL_DIR/ud.RUNBOOK_FILENAME
    try: ud.write_artifacts(repo_root=repo,output_dir=tmp_path/"other")
    except ValueError as exc: assert "artifact_writer_refuses_paths_outside_docs_automation_0174UD" in str(exc)
    else: raise AssertionError("writer accepted out-of-scope path")

def test_static_forbidden_behavior_scan_and_ingestion_boundary():
    text=Path(ud.__file__).read_text(encoding="utf-8")
    forbidden=["import requests","from requests","import urllib","from urllib","import socket","from socket","os.environ","dotenv","playwright","selenium","telegram.Bot","send_message","BeautifulSoup","subprocess","webbrowser","schedule.every"]
    for needle in forbidden: assert needle not in text
    for needle in ["platform_api_called","env_read","ingestion_repo_mutated"]: assert needle in text
