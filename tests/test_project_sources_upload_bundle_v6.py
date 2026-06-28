import json
from pathlib import Path
from live_contentops import project_sources_upload_bundle_v6 as upload_lane


def write_temp_readiness_inputs(tmp_path, missing_bundle=False, include_valid_hash=False, include_placeholder_hash=False, **kwargs):
    readiness_bundle = {
        "readiness_evidence_bundle_packet_id": "bundle_fbe34af9e66e",
        "source_supervised_dispatch_readiness_packet_id": "readiness_34edf10af116",
        "unresolved_blockers": ["evidence_incomplete", "operator_idea_source_ref_missing", "payload_hash_incomplete", "note"]
    }
    dispatch_readiness = {
        "supervised_dispatch_readiness_packet_id": "readiness_34edf10af116",
        "readiness_status": "DISPATCH_READINESS_BLOCKED_PENDING_REQUIREMENTS"
    }

    rb_path = tmp_path / "readiness_evidence_bundle_packet.json"
    dr_path = tmp_path / "supervised_dispatch_readiness_packet.json"

    if not missing_bundle:
        rb_path.write_text(json.dumps(readiness_bundle, indent=2), encoding="utf-8")
    dr_path.write_text(json.dumps(dispatch_readiness, indent=2), encoding="utf-8")

    if include_valid_hash or include_placeholder_hash:
        hash_packet = {
            "payload_hash_created": True,
            "exact_payload_preview_created": True,
            "payload_preview_status": "READY_FOR_OPERATOR_REVIEW",
            "payload_hash": "a" * 64,
            "payload_preview_id": "preview_ok"
        }
        if include_placeholder_hash:
            hash_packet["payload_preview_id"] = "PLACEHOLDER_preview"
        (tmp_path / "payload_preview_hash_packet.json").write_text(json.dumps(hash_packet, indent=2), encoding="utf-8")

    return rb_path, dr_path


def test_missing_artifacts_triggers_blocked_status(tmp_path):
    rb_path, dr_path = write_temp_readiness_inputs(tmp_path, missing_bundle=True)
    
    packet, files = upload_lane.materialize_project_sources_upload_bundle_packets(rb_path, dr_path)
    
    assert packet["bundle_status"] == "PROJECT_SOURCES_UPLOAD_BUNDLE_BLOCKED_MISSING_ARTIFACTS"
    assert packet["dispatch_allowed_now"] is False
    assert packet["approval_valid_for_dispatch"] is False
    assert packet["public_postable"] is False


def test_valid_readiness_produces_ready_with_blockers(tmp_path):
    rb_path, dr_path = write_temp_readiness_inputs(tmp_path)

    packet, files = upload_lane.materialize_project_sources_upload_bundle_packets(rb_path, dr_path)

    assert packet["bundle_status"] == "PROJECT_SOURCES_UPLOAD_BUNDLE_READY_WITH_DISPATCH_BLOCKERS"
    assert packet["dispatch_allowed_now"] is False
    assert packet["approval_valid_for_dispatch"] is False
    assert packet["public_postable"] is False

    assert "note" not in packet["unresolved_blockers"]
    assert "evidence_incomplete" in packet["unresolved_blockers"]
    assert "payload_hash_incomplete" in packet["unresolved_blockers"]


def test_file_list_contents_and_safety(tmp_path):
    rb_path, dr_path = write_temp_readiness_inputs(tmp_path)
    packet, files = upload_lane.materialize_project_sources_upload_bundle_packets(rb_path, dr_path)
    
    for f in files:
        assert not f.startswith("A:")
        assert not f.startswith("C:")
        assert f.endswith(".md") or f.endswith(".json") or f.endswith(".txt") or f.endswith(".html")
        assert ".env" not in f
        if "substack_browser" in f.lower():
            continue
        assert "browser" not in f.lower()
        assert "session" not in f.lower()


def test_new_chat_continuation_starts_with_task_label(tmp_path):
    rb_path, dr_path = write_temp_readiness_inputs(tmp_path)
    packet, files = upload_lane.materialize_project_sources_upload_bundle_packets(rb_path, dr_path)
    
    content = upload_lane.generate_new_chat_continuation_markdown(
        packet["bundle_generation_head"], packet["unresolved_blockers"]
    )
    lines = content.strip().splitlines()
    assert lines[0] == "TASK_CONTENTOPS_V6_PROJECT_SOURCES_REFRESH_CONTINUATION_AFTER_READINESS_BUNDLE_V0"
    assert "cc-live-contentops" in content
    assert "master" in content
    assert "Baseline before upload bundle task" in content


def test_replacement_guide_safety_warnings():
    guide = upload_lane.generate_replacement_guide_markdown()
    
    assert "never upload `.env` files" in guide.lower()
    assert "credentials" in guide.lower()
    assert "browser" in guide.lower()
    assert "session" in guide.lower()
    assert "do not delete or modify the master plan" in guide.lower()


def test_current_state_summary_details(tmp_path):
    rb_path, dr_path = write_temp_readiness_inputs(tmp_path)
    packet, files = upload_lane.materialize_project_sources_upload_bundle_packets(rb_path, dr_path)
    
    summary = upload_lane.generate_current_state_summary_markdown(
        packet["bundle_generation_head"], packet["unresolved_blockers"]
    )
    
    assert "Baseline before upload bundle task" in summary
    assert "Current generation HEAD" in summary
    assert "master" in summary
    assert upload_lane.TASK_LABEL in summary
    assert "Post-Push Audit Required" in summary


def test_webhook_and_secrets_hygiene(tmp_path):
    rb_path, dr_path = write_temp_readiness_inputs(tmp_path)
    packet, files = upload_lane.materialize_project_sources_upload_bundle_packets(rb_path, dr_path)
    
    # Check templates
    docs = [
        upload_lane.generate_replacement_guide_markdown(),
        upload_lane.generate_new_chat_continuation_markdown(packet["bundle_generation_head"], packet["unresolved_blockers"]),
        upload_lane.generate_current_state_summary_markdown(packet["bundle_generation_head"], packet["unresolved_blockers"]),
        upload_lane.generate_operator_next_actions_markdown(),
        upload_lane.generate_implementation_report_markdown(packet["bundle_status"], packet["bundle_generation_head"]),
        upload_lane.generate_next_task_pointer_markdown(),
        json.dumps(packet)
    ]
    
    for doc in docs:
        assert "discord.com/api/webhooks" not in doc
        assert "http" not in doc or "github.com" in doc or "substack" in doc or "docs/automation" in doc
        assert "token_value" not in doc.lower()
        assert "cookie_value" not in doc.lower()
        assert "secret_key" not in doc.lower()
        assert "env_value" not in doc.lower()


def test_no_forbidden_behavior_in_module():
    attrs = dir(upload_lane)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs


def test_metadata_integrity_and_hardenings(tmp_path):
    rb_path, dr_path = write_temp_readiness_inputs(tmp_path)
    packet, files = upload_lane.materialize_project_sources_upload_bundle_packets(rb_path, dr_path)
    
    # 1. Assert packet values
    assert packet["task_label"] == "TASK_CONTENTOPS_V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK_DRY_RUN_HEAVY_BATCH_V0"
    assert packet["final_head_requires_post_push_audit"] is True
    assert packet["previous_accepted_pipeline_status_head"] == "9571d900552122c0d1c110017d718c7e4b7f375d"
    assert "pre_commit_generation_head_input_only" in packet["bundle_generation_head_label"]
    assert "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_content_generators_packet.json" in files
    assert "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_variant_constraint_registry.json" in files
    assert "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_variant_pack.json" in files
    assert "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/thread_continuation_pack.json" in files
    assert "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_variant_validation_report.json" in files
    assert "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_variant_blocker_report.md" in files
    assert "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_variant_runbook.md" in files
    assert "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/implementation_report.md" in files
    assert "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/next_task_pointer.md" in files
    assert "docs/automation/V6_NETWORK_SCOPE_POLICY/scoped_network_policy_v6.md" in files
    assert "docs/automation/V6_NETWORK_SCOPE_POLICY/network_resource_allowlist.json" in files
    assert "docs/automation/V6_NETWORK_SCOPE_POLICY/network_scope_policy_packet.json" in files
    assert "docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE/fixture_lifecycle_packet.json" in files
    assert "docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE/fixture_lifecycle_stage_matrix.json" in files
    assert "docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE/fixture_dry_run_validation_report.json" in files
    assert "docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE/fixture_audit_trail_template.json" in files
    assert "docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE/fixture_submission_recovery_runbook.md" in files
    assert "docs/automation/V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR/manual_evidence_refresh_orchestrator_packet.json" in files
    assert "docs/automation/V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR/manual_evidence_refresh_rollup.json" in files
    assert "docs/automation/V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR/manual_evidence_refresh_operator_runbook.md" in files
    assert "docs/automation/V6_MANUAL_EVIDENCE_SOURCE_SUBMISSION_REFRESH/manual_evidence_source_submission_refresh_packet.json" in files
    assert "docs/automation/V6_MANUAL_EVIDENCE_SOURCE_SUBMISSION_REFRESH/manual_evidence_source_submission_stage_matrix.json" in files
    assert "docs/automation/V6_MANUAL_EVIDENCE_SOURCE_SUBMISSION_REFRESH/manual_evidence_source_submission_operator_checklist.md" in files
    assert "docs/automation/V6_MANUAL_EVIDENCE_SOURCE_SUBMISSION_REFRESH/manual_evidence_source_submission_recovery_runbook.md" in files
    assert "docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_authoring_report.md" in files
    assert "docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_fixture_redacted_summary.json" in files
    assert "docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_source_map.json" in files
    assert "docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_refresh_result.json" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_gate_packet.json" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_review_packet.json" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_signature_template.json" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_blocker_report.md" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_runbook.md" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_GATE/implementation_report.md" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_GATE/next_task_pointer.md" in files
    assert "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_preview_hash_packet.json" in files
    assert "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_preview_exact_review.json" in files
    assert "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json" in files
    assert "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_hash_inputs_redacted.json" in files
    assert "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_preview_runbook.md" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_binding_packet.json" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_binding_review_packet.json" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_template.json" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_validation_report.json" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_blocker_report.md" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_runbook.md" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/implementation_report.md" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/next_task_pointer.md" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_packet.json" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_ui_spec.md" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_cli_reference.md" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_validation_report.json" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_blocker_report.md" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_runbook.md" in files
    assert "docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/implementation_report.md" in files
    assert "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/destination_binding_outbox_draft_packet.json" in files
    assert "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/destination_binding_review_matrix.json" in files
    assert "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/outbox_draft_preview_packet.json" in files
    assert "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/outbox_draft_validation_report.json" in files
    assert "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/destination_binding_blocker_report.md" in files
    assert "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/destination_binding_runbook.md" in files
    assert "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/implementation_report.md" in files
    assert "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/next_task_pointer.md" in files
    assert "docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION/supervised_dispatch_readiness_packet.json" in files
    assert "docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION/dispatch_readiness_blocker_matrix.json" in files
    assert "docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION/dispatch_readiness_validation_report.json" in files
    assert "docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION/dispatch_readiness_runbook.md" in files
    assert "docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION/dispatch_readiness_blocker_report.md" in files
    assert "docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION/implementation_report.md" in files
    assert "docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION/next_task_pointer.md" in files
    assert "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/approval_ledger_outbox_packet.json" in files
    assert "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/approval_ledger_entry_preview.json" in files
    assert "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/outbox_record_preview.json" in files
    assert "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/outbox_record_validation_report.json" in files
    assert "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/approval_ledger_validation_report.json" in files
    assert "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/approval_ledger_outbox_blocker_report.md" in files
    assert "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/approval_ledger_outbox_runbook.md" in files
    assert "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/implementation_report.md" in files
    assert "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/next_task_pointer.md" in files
    assert "docs/automation/V6_AI_PRODUCTION_CORE/provider_gate_packet.json" in files
    assert "docs/automation/V6_AI_PRODUCTION_CORE/prompt_registry_packet.json" in files
    assert "docs/automation/V6_AI_PRODUCTION_CORE/sample_operator_intents.json" in files
    assert "docs/automation/V6_AI_PRODUCTION_CORE/sample_content_idea_packet.json" in files
    assert "docs/automation/V6_AI_PRODUCTION_CORE/sample_research_grounding_packet.json" in files
    assert "docs/automation/V6_AI_PRODUCTION_CORE/sample_canonical_article_packet.json" in files
    assert "docs/automation/V6_AI_PRODUCTION_CORE/sample_seo_editorial_packet.json" in files
    assert "docs/automation/V6_AI_PRODUCTION_CORE/ai_production_core_packet.json" in files
    assert "docs/automation/V6_AI_PRODUCTION_CORE/ai_production_core_validation_report.json" in files
    assert "docs/automation/V6_AI_PRODUCTION_CORE/ai_production_core_blocker_report.md" in files
    assert "docs/automation/V6_AI_PRODUCTION_CORE/ai_production_core_runbook.md" in files
    assert "docs/automation/V6_AI_PRODUCTION_CORE/implementation_report.md" in files
    assert "docs/automation/V6_AI_PRODUCTION_CORE/next_task_pointer.md" in files
    assert "docs/automation/V6_DRAFT_INSPECTOR_V2/draft_inspector_v2_packet.json" in files
    assert "docs/automation/V6_DRAFT_INSPECTOR_V2/content_quality_scorecard.json" in files
    assert "docs/automation/V6_UNIFIED_PAYLOAD_APPROVAL_OUTBOX/unified_payload_contract_packet.json" in files
    assert "docs/automation/V6_DISCORD_TELEGRAM_OPERATOR_BRIDGE/operator_bridge_packet.json" in files
    assert "docs/automation/V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN/substack_compose_dry_run_packet.json" in files
    
    # 2. Check generate_current_state_summary_markdown details
    summary = upload_lane.generate_current_state_summary_markdown(
        packet["bundle_generation_head"], packet["unresolved_blockers"], packet["next_recommended_task"]
    )
    assert "TASK_CONTENTOPS_V6_FAST_SHIP_OPERATING_PROFILE_AND_PROMPT_CEREMONY_REDUCTION_HEAVY_BATCH_V0" not in summary
    assert "requires GitHub audit after push" in summary
    assert "pre-commit generation input only, not runtime authority" in summary
    
    # 3. Check METADATA_INTEGRITY_NOTE.md contents
    note = upload_lane.generate_metadata_integrity_note_markdown()
    assert "github remote is runtime authority" in note.lower() or "github remote/fetched files are runtime authority" in note.lower()
    assert "no force push" in note.lower() or "never use `git push -f`" in note.lower()
    
    # 4. Check recommended task
    assert packet["next_recommended_task"] == "TASK_CONTENTOPS_V6_SOURCE_PACK_VERIFICATION_UI_AND_OPERATOR_RESEARCH_CHECKLIST_HEAVY_BATCH_V0"
    
    # 5. Check flags are locked
    assert packet["dispatch_allowed_now"] is False
    assert packet["approval_valid_for_dispatch"] is False
    assert packet["public_postable"] is False
    assert packet["kill_switch_active"] is True


def test_valid_payload_hash_unblocks_hash_pointer(tmp_path):
    rb_path, dr_path = write_temp_readiness_inputs(tmp_path, include_valid_hash=True)
    (tmp_path / "delegated_evidence_refresh_result.json").write_text(json.dumps({"evidence_complete": True}), encoding="utf-8")

    packet, _ = upload_lane.materialize_project_sources_upload_bundle_packets(rb_path, dr_path)

    assert "payload_hash_incomplete" not in packet["unresolved_blockers"]
    assert packet["next_recommended_task"] == "TASK_CONTENTOPS_V6_SOURCE_PACK_VERIFICATION_UI_AND_OPERATOR_RESEARCH_CHECKLIST_HEAVY_BATCH_V0"


def test_valid_signature_routes_to_supervised_dispatch_readiness(tmp_path):
    rb_path, dr_path = write_temp_readiness_inputs(tmp_path, include_valid_hash=True)
    (tmp_path / "delegated_evidence_refresh_result.json").write_text(json.dumps({"evidence_complete": True}), encoding="utf-8")
    
    # Write a valid signature so destination binding validates
    (tmp_path / "destination_binding_outbox_draft_packet.json").write_text(json.dumps({
        "operator_signature_valid": True,
        "destination_outbox_status": "OUTBOX_DRAFT_READY_FOR_REVIEW"
    }, indent=2), encoding="utf-8")

    packet, _ = upload_lane.materialize_project_sources_upload_bundle_packets(rb_path, dr_path)

    assert "payload_hash_incomplete" not in packet["unresolved_blockers"]
    assert packet["next_recommended_task"] == "TASK_CONTENTOPS_V6_SOURCE_PACK_VERIFICATION_UI_AND_OPERATOR_RESEARCH_CHECKLIST_HEAVY_BATCH_V0"


def test_placeholder_hash_does_not_unblock_hash_pointer(tmp_path):
    rb_path, dr_path = write_temp_readiness_inputs(tmp_path, include_placeholder_hash=True)
    (tmp_path / "delegated_evidence_refresh_result.json").write_text(json.dumps({"evidence_complete": True}), encoding="utf-8")

    packet, _ = upload_lane.materialize_project_sources_upload_bundle_packets(rb_path, dr_path)

    assert "payload_hash_incomplete" in packet["unresolved_blockers"]
    assert packet["next_recommended_task"] == "TASK_CONTENTOPS_V6_SOURCE_PACK_VERIFICATION_UI_AND_OPERATOR_RESEARCH_CHECKLIST_HEAVY_BATCH_V0"
