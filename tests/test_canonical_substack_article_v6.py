import json
from pathlib import Path
from live_contentops import canonical_substack_article_v6 as generator


def write_temp_intent(tmp_path, prompt, **kwargs):
    # Mimics operator_intent_v6 output
    data = {
        "intent_id": "discord_operator_intent_d1720f70a937",
        "intent_class": "create_canonical_article",
        "source_mode": "operator_idea_only",
        "topic": "Editorial Workflow",
        "source_refs": [],
        "source_needed": False,
        "source_evidence_required": False,
        "future_artifact_claim_detected": False,
        "blocked_reasons": [],
        "dispatch_requested": False,
        "approval_requested": False,
    }
    data.update(kwargs)
    p = tmp_path / "operator_intent_packet.json"
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


def test_safe_operator_intent_produces_ready_outline(tmp_path):
    p = write_temp_intent(tmp_path, "Idea", source_mode="operator_idea_only")
    packet = generator.materialize_article_packet(p)
    assert packet["article_status"] == "OUTLINE_SCAFFOLD_READY"
    assert packet["public_postable"] is False
    assert packet["not_public_postable"] is True
    assert packet["dispatch_allowed_now"] is False


def test_blocked_operator_intent_produces_blocked_article_status(tmp_path):
    p = write_temp_intent(tmp_path, "Idea with signal", blocked_reasons=["trading_signal_language_blocked"])
    packet = generator.materialize_article_packet(p)
    assert packet["article_status"] == "BLOCKED_BY_OPERATOR_INTENT"
    assert "trading_signal_language_blocked" in packet["blocked_reasons"]


def test_operator_idea_only_source_mode_sets_source_needed(tmp_path):
    p = write_temp_intent(tmp_path, "Idea", source_mode="operator_idea_only")
    packet = generator.materialize_article_packet(p)
    assert packet["source_needed"] is True
    assert packet["not_public_postable"] is True
    
    # outline markdown contains limitation note
    md = generator.generate_scaffold_markdown(packet)
    assert "operator_idea_only" in md
    assert "Real-world verification and source evidence are required" in md


def test_numeric_claim_without_source_refs_blocks_article(tmp_path):
    p = write_temp_intent(tmp_path, "metrics", source_evidence_required=True, source_refs=[])
    packet = generator.materialize_article_packet(p)
    assert packet["article_status"] == "BLOCKED_BY_OPERATOR_INTENT"
    assert packet["source_needed"] is True
    assert packet["source_evidence_required"] is True
    assert "missing_source_evidence" in packet["blocked_reasons"]


def test_numeric_claim_with_source_refs_is_not_blocked(tmp_path):
    p = write_temp_intent(tmp_path, "metrics", source_evidence_required=True, source_refs=["docs/evidence.md"])
    packet = generator.materialize_article_packet(p)
    assert packet["article_status"] == "OUTLINE_SCAFFOLD_READY"
    assert "missing_source_evidence" not in packet["blocked_reasons"]


def test_future_artifact_claim_without_source_refs_blocks_article(tmp_path):
    p = write_temp_intent(tmp_path, "alpha", future_artifact_claim_detected=True, source_refs=[])
    packet = generator.materialize_article_packet(p)
    assert packet["article_status"] == "BLOCKED_BY_OPERATOR_INTENT"
    assert "missing_source_evidence" in packet["blocked_reasons"]


def test_approval_dispatch_intent_remains_not_approved_not_dispatchable(tmp_path):
    p = write_temp_intent(tmp_path, "approve", approval_requested=True, dispatch_requested=True)
    packet = generator.materialize_article_packet(p)
    assert packet["not_approved"] is True
    assert packet["not_dispatchable"] is True
    assert packet["dispatch_allowed_now"] is False


def test_generated_markdown_outline_contains_warnings(tmp_path):
    p = write_temp_intent(tmp_path, "blocked", blocked_reasons=["trading_signal_language_blocked"])
    packet = generator.materialize_article_packet(p)
    md = generator.generate_scaffold_markdown(packet)
    assert "PUBLISH BLOCK ACTIVE" in md
    assert "trading_signal_language_blocked" in md
    assert "DRAFT SCAFFOLD ONLY" in md


def test_packet_contains_no_sensitive_values(tmp_path):
    p = write_temp_intent(tmp_path, "safe")
    packet = generator.materialize_article_packet(p)
    dump = json.dumps(packet)
    assert "discord.com/api/webhooks" not in dump
    assert "token" not in dump.lower()
    assert "cookie" not in dump.lower()
    assert packet["raw_secret_output"] is False
    assert packet["webhook_url_printed"] is False


def test_module_contains_no_forbidden_behavior():
    attrs = dir(generator)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
