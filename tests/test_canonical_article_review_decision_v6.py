import json
from dataclasses import asdict
from pathlib import Path

from live_contentops.canonical_article_intake_v6 import parse_markdown_review_candidate
from live_contentops.canonical_article_review_decision_v6 import (
    INTAKE_TASK_LABEL,
    make_review_decision,
    load_review_candidate_packet,
    main,
)


def _candidate(tmp_path):
    draft = tmp_path / "draft.md"
    draft.write_text("---\nsubtitle: Safe\n---\n# Safe Title\n\nSafe local draft body.\n", encoding="utf-8")
    return asdict(parse_markdown_review_candidate(draft))


def _decision(candidate, decision="accept_for_editorial_workflow", notes=""):
    return make_review_decision(candidate, decision, "jim", "2026-06-29T22:00:00+07:00", notes)


def _assert_review_only(packet):
    assert packet.approved_canonical_article_available is False
    assert packet.publication_ready is False
    assert packet.dispatch_allowed is False
    assert packet.platform_variant_generation_allowed is False
    assert packet.outbox_creation_allowed is False
    assert packet.public_url is None
    assert packet.public_metrics is None
    assert packet.human_review_required is True
    assert packet.review_only is True
    assert packet.kill_switch_active is True
    assert packet.runtime_truth is False


def test_valid_accept_emits_editorial_workflow_only(tmp_path):
    decision = _decision(_candidate(tmp_path))
    assert decision.accepted_for_editorial_workflow is True
    assert decision.rejected is False
    assert decision.deferred is False
    assert not decision.blockers
    _assert_review_only(decision)


def test_reject_keeps_public_live_states_blocked(tmp_path):
    decision = _decision(_candidate(tmp_path), "reject")
    assert decision.rejected is True
    assert decision.accepted_for_editorial_workflow is False
    _assert_review_only(decision)


def test_defer_keeps_public_live_states_blocked(tmp_path):
    decision = _decision(_candidate(tmp_path), "defer")
    assert decision.deferred is True
    assert decision.accepted_for_editorial_workflow is False
    _assert_review_only(decision)


def test_blocked_candidate_cannot_be_accepted(tmp_path):
    candidate = _candidate(tmp_path)
    candidate["blockers"] = ["missing_h1_title"]
    decision = _decision(candidate)
    assert decision.accepted_for_editorial_workflow is False
    assert "candidate_has_blockers" in decision.blockers


def test_redacted_candidate_cannot_be_accepted(tmp_path):
    candidate = _candidate(tmp_path)
    candidate["redaction_applied"] = True
    decision = _decision(candidate)
    assert decision.accepted_for_editorial_workflow is False
    assert "candidate_redaction_applied" in decision.blockers


def test_malformed_candidate_fails_closed(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not-json", encoding="utf-8")
    try:
        load_review_candidate_packet(bad)
    except ValueError as exc:
        assert str(exc) == "malformed_candidate_json"
    else:
        raise AssertionError("expected malformed_candidate_json")


def test_invalid_decision_fails_closed(tmp_path):
    decision = _decision(_candidate(tmp_path), "publish_now")
    assert "decision_invalid" in decision.blockers
    assert decision.accepted_for_editorial_workflow is False


def test_missing_reviewer_or_reviewed_at_fails_closed(tmp_path):
    candidate = _candidate(tmp_path)
    d1 = make_review_decision(candidate, "accept_for_editorial_workflow", "", "time")
    d2 = make_review_decision(candidate, "accept_for_editorial_workflow", "jim", "")
    assert "reviewer_id_missing" in d1.blockers
    assert "reviewed_at_manual_missing" in d2.blockers


def test_public_state_candidate_fails_closed(tmp_path):
    for field, value in [
        ("approved_canonical_article_available", True),
        ("publication_ready", True),
        ("dispatch_allowed", True),
        ("platform_variant_generation_allowed", True),
        ("outbox_creation_allowed", True),
        ("public_url", "https://example.invalid/article"),
        ("public_metrics", {"views": 1}),
    ]:
        candidate = _candidate(tmp_path)
        candidate[field] = value
        decision = _decision(candidate)
        assert decision.accepted_for_editorial_workflow is False
        assert decision.blockers


def test_secret_candidate_fields_fail_closed(tmp_path):
    candidate = _candidate(tmp_path)
    candidate["body_text"] = "contains password do-not-print"
    decision = _decision(candidate)
    assert "candidate_secret_marker_detected" in decision.blockers


def test_review_notes_secret_marker_redacted(tmp_path):
    raw = "password do-not-print-note-value"
    decision = _decision(_candidate(tmp_path), "defer", raw)
    dumped = json.dumps(asdict(decision), sort_keys=True)
    assert "review_notes_secret_marker_detected" in decision.blockers
    assert "review_notes_redacted_secret_marker_detected" in decision.warnings
    assert "do-not-print-note-value" not in dumped
    assert decision.review_notes == "[REDACTED_SECRET_MARKER_DETECTED]"


def test_source_candidate_sha256_is_deterministic(tmp_path):
    candidate = _candidate(tmp_path)
    d1 = _decision(candidate)
    d2 = _decision(candidate)
    assert d1.source_candidate_sha256 == d2.source_candidate_sha256
    assert d1.decision_id == d2.decision_id


def test_module_contains_no_getenv_environ_network_provider_browser_imports():
    source = Path("live_contentops/canonical_article_review_decision_v6.py").read_text(encoding="utf-8")
    forbidden = ["getenv", "environ", "requests", "urllib", "httpx", "provider_gateway", "browser", "webbrowser"]
    assert not any(marker in source for marker in forbidden)


def test_cli_writes_decision_packet_deterministically(tmp_path):
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(json.dumps(_candidate(tmp_path), sort_keys=True), encoding="utf-8")
    output_dir = tmp_path / "out"
    exit_code = main([
        str(candidate_path),
        "--decision", "accept_for_editorial_workflow",
        "--reviewer-id", "jim",
        "--reviewed-at-manual", "2026-06-29T22:00:00+07:00",
        "--output-dir", str(output_dir),
    ])
    assert exit_code == 0
    packets = list(output_dir.glob("canonical_article_review_decision_*.json"))
    assert len(packets) == 1
    packet = json.loads(packets[0].read_text(encoding="utf-8"))
    assert packet["accepted_for_editorial_workflow"] is True
    assert packet["approved_canonical_article_available"] is False
    assert packet["source_candidate_id"] == _candidate(tmp_path)["candidate_id"]


def test_wrong_task_label_or_status_fails_closed(tmp_path):
    candidate = _candidate(tmp_path)
    candidate["task_label"] = "wrong"
    assert "candidate_task_label_invalid" in _decision(candidate).blockers
    candidate = _candidate(tmp_path)
    candidate["candidate_status"] = "BLOCKED"
    assert "candidate_status_not_pending_human_review" in _decision(candidate).blockers
    assert INTAKE_TASK_LABEL.endswith("INTAKE_FROM_MARKDOWN_V0")
