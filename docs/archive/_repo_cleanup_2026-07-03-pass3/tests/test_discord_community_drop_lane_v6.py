import json
from pathlib import Path
from live_contentops import discord_community_drop_lane_v6 as drop_lane


def write_temp_inputs(tmp_path, variant_status="VARIANT_SCAFFOLD_READY_WITH_SOURCE_GAP", **kwargs):
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
    
    var_p = tmp_path / "platform_variant_packet.json"
    var_p.write_text(json.dumps(variant_data, indent=2), encoding="utf-8")
    
    var_md = tmp_path / "discord_variant.md"
    var_md.write_text("📢 Community Announcement Draft: V6 Staging Scaffold", encoding="utf-8")
    
    return var_p, var_md


def test_source_gap_variant_produces_ready_with_source_gap_status(tmp_path):
    var_p, var_md = write_temp_inputs(tmp_path, missing_source_refs=["operator_idea_source_ref"], source_needed=True)
    drop, review, binding, var_body = drop_lane.materialize_drop_packets(var_p, var_md)
    assert drop["discord_drop_status"] == "DISCORD_DROP_REVIEW_READY_WITH_SOURCE_GAP"
    assert drop["public_postable"] is False
    assert drop["not_public_postable"] is True
    assert drop["dispatch_allowed_now"] is False


def test_blocked_variant_produces_blocked_by_platform_variant(tmp_path):
    var_p, var_md = write_temp_inputs(tmp_path, variant_status="BLOCKED_BY_SOURCE_ARTICLE", blocked_reasons=["trading_signal_blocked"])
    drop, review, binding, var_body = drop_lane.materialize_drop_packets(var_p, var_md)
    assert drop["discord_drop_status"] == "BLOCKED_BY_PLATFORM_VARIANT"
    assert "trading_signal_blocked" in drop["blocked_reasons"]


def test_source_refs_present_produces_ready_drop(tmp_path):
    var_p, var_md = write_temp_inputs(tmp_path, variant_status="VARIANT_SCAFFOLD_READY", missing_source_refs=[], source_needed=False)
    drop, review, binding, var_body = drop_lane.materialize_drop_packets(var_p, var_md)
    assert drop["discord_drop_status"] == "DISCORD_DROP_REVIEW_READY"
    assert drop["public_postable"] is False
    assert drop["dispatch_allowed_now"] is False


def test_operator_review_packet_requirements(tmp_path):
    var_p, var_md = write_temp_inputs(tmp_path)
    drop, review, binding, var_body = drop_lane.materialize_drop_packets(var_p, var_md)
    assert review["exact_payload_hash_required"] is True
    assert review["exact_payload_hash_present"] is False
    assert review["destination_binding_required"] is True
    assert review["destination_binding_present"] is False
    assert review["approval_valid_for_dispatch"] is False
    assert review["dispatch_allowed_now"] is False


def test_channel_binding_contains_no_sensitive_values(tmp_path):
    var_p, var_md = write_temp_inputs(tmp_path)
    drop, review, binding, var_body = drop_lane.materialize_drop_packets(var_p, var_md)
    dump = json.dumps(binding)
    assert binding["webhook_url"] is None
    assert binding["secret_keys_present"] is False
    assert "token" not in dump.lower()
    assert "cookie" not in dump.lower()
    assert "auth_token" not in dump.lower()
    assert "authorization:" not in dump.lower()
    assert "authorization_header" not in dump.lower()


def test_preview_markdown_content_and_warnings(tmp_path):
    var_p, var_md = write_temp_inputs(tmp_path)
    drop, review, binding, var_body = drop_lane.materialize_drop_packets(var_p, var_md)
    preview_md = drop_lane.generate_preview_markdown(drop, var_body)
    
    assert "NO-PUBLICATION WARNING" in preview_md
    assert "Source Mode" in preview_md
    assert "operator_idea_only" in preview_md
    assert "operator_idea_source_ref" in preview_md
    assert "channel_family" in preview_md or "channel binding" in preview_md.lower()
    assert "dispatch_allowed_now` is false" in preview_md
    assert "CPC" not in preview_md
    assert "search_volume" not in preview_md
    assert "traffic" not in preview_md


def test_packet_contains_no_sensitive_values(tmp_path):
    var_p, var_md = write_temp_inputs(tmp_path)
    drop, review, binding, var_body = drop_lane.materialize_drop_packets(var_p, var_md)
    
    for obj in [drop, review]:
        dump = json.dumps(obj)
        assert "discord.com/api/webhooks" not in dump
        assert "token" not in dump.lower()
        assert "cookie" not in dump.lower()
        assert obj.get("raw_secret_output", False) is False
        assert obj.get("webhook_url_printed", False) is False


def test_module_contains_no_forbidden_behavior():
    attrs = dir(drop_lane)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
