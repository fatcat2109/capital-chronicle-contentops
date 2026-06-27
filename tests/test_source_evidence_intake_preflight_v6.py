import json
from pathlib import Path
from live_contentops import source_evidence_intake_preflight_v6 as preflight_lane


def write_temp_inputs(tmp_path, variant_status="VARIANT_SCAFFOLD_READY_WITH_SOURCE_GAP", drop_status="DISCORD_DROP_REVIEW_READY_WITH_SOURCE_GAP", **kwargs):
    # Mimics platform_native_variant_generator_v6 output
    variant_data = {
        "platform_variant_packet_id": "platform_variants_f4e590ab1f3c",
        "source_article_id": "substack_article_053c35205d67",
        "source_intent_id": "discord_operator_intent_d1720f70a937",
        "source_mode": "operator_idea_only",
        "variant_status": variant_status,
        "missing_source_refs": kwargs.get("missing_source_refs", ["operator_idea_source_ref"]),
        "source_needed": kwargs.get("source_needed", True),
        "source_evidence_required": kwargs.get("source_evidence_required", False),
        "blocked_reasons": kwargs.get("blocked_reasons", []),
    }
    
    # Mimics discord_community_drop_lane_v6 output
    drop_data = {
        "discord_drop_packet_id": "discord_drop_ce89baf48671",
        "source_platform_variant_packet_id": "platform_variants_f4e590ab1f3c",
        "source_article_id": "substack_article_053c35205d67",
        "source_intent_id": "discord_operator_intent_d1720f70a937",
        "source_mode": "operator_idea_only",
        "source_variant_status": variant_status,
        "discord_drop_status": drop_status,
        "missing_source_refs": kwargs.get("missing_source_refs", ["operator_idea_source_ref"]),
        "source_needed": kwargs.get("source_needed", True),
        "source_evidence_required": kwargs.get("source_evidence_required", False),
        "blocked_reasons": kwargs.get("blocked_reasons", []),
    }
    
    # Mimics operator_review_packet output
    review_data = {
        "operator_review_packet_id": "review_packet_ce89baf4",
        "source_discord_drop_packet_id": "discord_drop_ce89baf48671",
        "review_status": "AWAITING_OPERATOR_EVIDENCE_AND_APPROVAL"
    }
    
    # Mimics research_grounding_packet output
    grounding_data = {
        "research_packet_id": "substack_research_6a7a2be45f6e"
    }

    var_p = tmp_path / "platform_variant_packet.json"
    var_p.write_text(json.dumps(variant_data, indent=2), encoding="utf-8")
    
    drop_p = tmp_path / "discord_drop_packet.json"
    drop_p.write_text(json.dumps(drop_data, indent=2), encoding="utf-8")
    
    rev_p = tmp_path / "operator_review_packet.json"
    rev_p.write_text(json.dumps(review_data, indent=2), encoding="utf-8")
    
    gnd_p = tmp_path / "research_grounding_packet.json"
    gnd_p.write_text(json.dumps(grounding_data, indent=2), encoding="utf-8")
    
    return drop_p, rev_p, gnd_p, var_p


def test_missing_refs_produce_awaiting_operator_evidence(tmp_path):
    drop_p, rev_p, gnd_p, var_p = write_temp_inputs(tmp_path, missing_source_refs=["operator_idea_source_ref"], source_needed=True)
    intake, registry, preflight, snapshot = preflight_lane.materialize_intake_packets(drop_p, rev_p, gnd_p, var_p)
    assert intake["intake_status"] == "AWAITING_OPERATOR_SOURCE_EVIDENCE"
    assert intake["evidence_complete"] is False
    assert intake["dispatch_allowed_now"] is False


def test_no_missing_refs_produce_ready_for_review(tmp_path):
    drop_p, rev_p, gnd_p, var_p = write_temp_inputs(tmp_path, variant_status="VARIANT_SCAFFOLD_READY", drop_status="DISCORD_DROP_REVIEW_READY", missing_source_refs=[], source_needed=False)
    intake, registry, preflight, snapshot = preflight_lane.materialize_intake_packets(drop_p, rev_p, gnd_p, var_p)
    assert intake["intake_status"] == "SOURCE_EVIDENCE_READY_FOR_HUMAN_REVIEW"
    assert intake["evidence_complete"] is True
    assert intake["dispatch_allowed_now"] is False
    assert intake["public_postable"] is False


def test_blocked_upstream_packet(tmp_path):
    drop_p, rev_p, gnd_p, var_p = write_temp_inputs(tmp_path, variant_status="BLOCKED_BY_SOURCE_ARTICLE", blocked_reasons=["trading_signal_blocked"])
    intake, registry, preflight, snapshot = preflight_lane.materialize_intake_packets(drop_p, rev_p, gnd_p, var_p)
    assert intake["intake_status"] == "BLOCKED_BY_UPSTREAM_PACKET"
    assert "trading_signal_blocked" in intake["blocked_reasons"]


def test_source_reference_registry_placeholders(tmp_path):
    drop_p, rev_p, gnd_p, var_p = write_temp_inputs(tmp_path, missing_source_refs=["operator_idea_source_ref"])
    intake, registry, preflight, snapshot = preflight_lane.materialize_intake_packets(drop_p, rev_p, gnd_p, var_p)
    assert len(registry) == 1
    assert registry[0]["source_ref_id"] == "operator_idea_source_ref"
    assert registry[0]["supplied_value"] is None
    assert registry[0]["verified"] is False
    assert registry[0]["status"] == "MISSING_OPERATOR_SUPPLIED_EVIDENCE"


def test_approval_preflight_and_dispatch_readiness_blocked(tmp_path):
    drop_p, rev_p, gnd_p, var_p = write_temp_inputs(tmp_path)
    intake, registry, preflight, snapshot = preflight_lane.materialize_intake_packets(drop_p, rev_p, gnd_p, var_p)
    
    assert preflight["approval_valid_for_dispatch"] is False
    assert preflight["dispatch_allowed_now"] is False
    assert preflight["not_approved"] is True
    assert preflight["not_dispatchable"] is True
    assert "missing_source_references" in preflight["blockers"]
    
    assert snapshot["dispatch_allowed_now"] is False
    assert snapshot["public_postable"] is False
    assert snapshot["dispatch_readiness_status"] == "BLOCKED_SOURCE_EVIDENCE_MISSING"


def test_generated_markdown_checklists(tmp_path):
    drop_p, rev_p, gnd_p, var_p = write_temp_inputs(tmp_path)
    intake, registry, preflight, snapshot = preflight_lane.materialize_intake_packets(drop_p, rev_p, gnd_p, var_p)
    
    source_checklist = preflight_lane.generate_source_checklist_markdown(intake)
    assert "NO-PUBLICATION WARNING" in source_checklist
    assert "No-Live / No-Dispatch Warning" in source_checklist
    assert "No Fake-Citation Warning" in source_checklist
    assert "operator_idea_source_ref" in source_checklist
    
    preflight_checklist = preflight_lane.generate_approval_checklist_markdown(intake, preflight)
    assert "Approval Preflight Checklist" in preflight_checklist
    assert "exact payload hash checklist" in preflight_checklist.lower()
    assert "destination binding checklist" in preflight_checklist.lower()
    assert "dispatch remains strictly blocked" in preflight_checklist.lower()


def test_packet_contains_no_sensitive_values(tmp_path):
    drop_p, rev_p, gnd_p, var_p = write_temp_inputs(tmp_path)
    intake, registry, preflight, snapshot = preflight_lane.materialize_intake_packets(drop_p, rev_p, gnd_p, var_p)
    
    for obj in [intake, preflight, snapshot]:
        dump = json.dumps(obj)
        assert "discord.com/api/webhooks" not in dump
        assert "token" not in dump.lower()
        assert "cookie" not in dump.lower()
        assert obj.get("raw_secret_output", False) is False
        assert obj.get("webhook_url_printed", False) is False


def test_module_contains_no_forbidden_behavior():
    attrs = dir(preflight_lane)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
