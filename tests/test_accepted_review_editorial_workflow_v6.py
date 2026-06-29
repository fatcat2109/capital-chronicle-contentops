import json
from dataclasses import asdict
from pathlib import Path

from live_contentops.accepted_review_editorial_workflow_v6 import (
    DEFAULT_EDIT_CHECKLIST,
    DEFAULT_FACTUAL_REVIEW_QUEUE,
    DEFAULT_SOURCE_GROUNDING_REQUIREMENTS,
    make_editorial_workflow_packet,
    load_review_decision_packet,
    main,
)


def _decision():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_CANONICAL_ARTICLE_REVIEW_CANDIDATE_HUMAN_REVIEW_DECISION_CONTRACT_V0",
        "decision_id": "canonical_article_review_decision_abc123",
        "source_candidate_id": "canonical_article_review_candidate_abc123",
        "source_candidate_sha256": "a" * 64,
        "decision": "accept_for_editorial_workflow",
        "reviewer_id": "jim",
        "reviewed_at_manual": "2026-06-29T23:00:00+07:00",
        "review_notes": "safe local note",
        "accepted_for_editorial_workflow": True,
        "rejected": False,
        "deferred": False,
        "approved_canonical_article_available": False,
        "human_review_required": True,
        "publication_ready": False,
        "dispatch_allowed": False,
        "platform_variant_generation_allowed": False,
        "outbox_creation_allowed": False,
        "public_url": None,
        "public_metrics": None,
        "review_only": True,
        "kill_switch_active": True,
        "runtime_truth": False,
        "blockers": [],
        "warnings": [],
    }


def _assert_no_public_state(packet):
    assert packet.approved_canonical_article_available is False
    assert packet.publication_ready is False
    assert packet.dispatch_allowed is False
    assert packet.platform_variant_generation_allowed is False
    assert packet.outbox_creation_allowed is False
    assert packet.public_url is None
    assert packet.public_metrics is None
    assert packet.review_only is True
    assert packet.human_review_required is True
    assert packet.kill_switch_active is True
    assert packet.runtime_truth is False


def test_valid_accepted_review_decision_emits_editorial_workflow_packet():
    packet = make_editorial_workflow_packet(_decision())
    assert packet.editorial_workflow_packet_available is True
    assert not packet.blockers
    assert packet.workflow_status == "EDITORIAL_WORKFLOW_PACKET_READY_FOR_OPERATOR_REVIEW"
    for item in DEFAULT_EDIT_CHECKLIST:
        assert item in packet.edit_checklist
    for item in DEFAULT_FACTUAL_REVIEW_QUEUE:
        assert item in packet.factual_review_queue
    for item in DEFAULT_SOURCE_GROUNDING_REQUIREMENTS:
        assert item in packet.source_grounding_requirements
    assert "provide_or_confirm_source_pack" in packet.required_operator_actions
    _assert_no_public_state(packet)


def test_reject_decision_fails_closed():
    decision = _decision()
    decision["decision"] = "reject"
    decision["accepted_for_editorial_workflow"] = False
    decision["rejected"] = True
    packet = make_editorial_workflow_packet(decision)
    assert packet.editorial_workflow_packet_available is False
    assert "decision_not_accept_for_editorial_workflow" in packet.blockers
    _assert_no_public_state(packet)


def test_defer_decision_fails_closed():
    decision = _decision()
    decision["decision"] = "defer"
    decision["accepted_for_editorial_workflow"] = False
    decision["deferred"] = True
    packet = make_editorial_workflow_packet(decision)
    assert packet.editorial_workflow_packet_available is False
    assert "decision_not_accept_for_editorial_workflow" in packet.blockers
    _assert_no_public_state(packet)


def test_accepted_for_editorial_workflow_false_fails_closed():
    decision = _decision()
    decision["accepted_for_editorial_workflow"] = False
    packet = make_editorial_workflow_packet(decision)
    assert "accepted_for_editorial_workflow_not_true" in packet.blockers


def test_decision_packet_with_blockers_fails_closed():
    decision = _decision()
    decision["blockers"] = ["candidate_has_blockers"]
    packet = make_editorial_workflow_packet(decision)
    assert "decision_has_blockers" in packet.blockers


def test_malformed_json_fails_closed(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{bad", encoding="utf-8")
    try:
        load_review_decision_packet(bad)
    except ValueError as exc:
        assert str(exc) == "malformed_decision_json"
    else:
        raise AssertionError("expected malformed_decision_json")


def test_non_object_json_fails_closed_without_exception_and_cli_returns_1(tmp_path):
    packet = make_editorial_workflow_packet([])
    assert "malformed_decision_json" in packet.blockers
    _assert_no_public_state(packet)
    decision_path = tmp_path / "decision.json"
    decision_path.write_text("[]", encoding="utf-8")
    output_dir = tmp_path / "out"
    exit_code = main([str(decision_path), "--output-dir", str(output_dir)])
    assert exit_code == 1
    packets = list(output_dir.glob("accepted_review_editorial_workflow_*.json"))
    assert len(packets) == 1
    written = json.loads(packets[0].read_text(encoding="utf-8"))
    assert "malformed_decision_json" in written["blockers"]
    assert written["editorial_workflow_packet_available"] is False


def test_public_live_state_true_or_non_null_fails_closed():
    for field, value in [
        ("approved_canonical_article_available", True),
        ("publication_ready", True),
        ("dispatch_allowed", True),
        ("platform_variant_generation_allowed", True),
        ("outbox_creation_allowed", True),
        ("public_url", "https://example.invalid/nope"),
        ("public_metrics", {"views": 1}),
    ]:
        decision = _decision()
        decision[field] = value
        packet = make_editorial_workflow_packet(decision)
        assert packet.editorial_workflow_packet_available is False
        assert packet.blockers
        _assert_no_public_state(packet)


def test_runtime_truth_true_fails_closed():
    decision = _decision()
    decision["runtime_truth"] = True
    packet = make_editorial_workflow_packet(decision)
    assert "decision_runtime_truth_not_false" in packet.blockers


def test_missing_source_candidate_fields_fail_closed():
    decision = _decision()
    decision["source_candidate_id"] = ""
    assert "source_candidate_id_missing" in make_editorial_workflow_packet(decision).blockers
    decision = _decision()
    decision["source_candidate_sha256"] = ""
    assert "source_candidate_sha256_missing" in make_editorial_workflow_packet(decision).blockers


def test_secret_like_marker_fails_closed_and_raw_value_not_persisted():
    raw = "do-not-print-this-token-value"
    decision = _decision()
    decision["review_notes"] = f"token {raw}"
    packet = make_editorial_workflow_packet(decision)
    dumped = json.dumps(asdict(packet), sort_keys=True)
    assert "decision_secret_marker_detected" in packet.blockers
    assert raw not in dumped


def test_output_packet_never_contains_raw_draft_body():
    decision = _decision()
    decision["body_text"] = "RAW DRAFT BODY SHOULD NOT COPY"
    packet = make_editorial_workflow_packet(decision)
    dumped = json.dumps(asdict(packet), sort_keys=True)
    assert "RAW DRAFT BODY SHOULD NOT COPY" not in dumped


def test_module_contains_no_getenv_environ_network_provider_browser_imports():
    source = Path("live_contentops/accepted_review_editorial_workflow_v6.py").read_text(encoding="utf-8")
    forbidden = ["getenv", "environ", "requests", "urllib", "httpx", "provider_gateway", "browser", "webbrowser"]
    assert not any(marker in source for marker in forbidden)


def test_cli_writes_deterministic_packet(tmp_path):
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(json.dumps(_decision(), sort_keys=True), encoding="utf-8")
    output_dir = tmp_path / "out"
    assert main([str(decision_path), "--output-dir", str(output_dir)]) == 0
    first = list(output_dir.glob("accepted_review_editorial_workflow_*.json"))[0]
    first_packet = json.loads(first.read_text(encoding="utf-8"))
    assert main([str(decision_path), "--output-dir", str(output_dir)]) == 0
    second = list(output_dir.glob("accepted_review_editorial_workflow_*.json"))[0]
    second_packet = json.loads(second.read_text(encoding="utf-8"))
    assert first_packet["editorial_workflow_id"] == second_packet["editorial_workflow_id"]
    assert first_packet["editorial_workflow_packet_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_ACCEPTED_REVIEW_EDITORIAL_WORKFLOW_PACKET_CONTRACT")
    paths = [
        Path("live_contentops/accepted_review_editorial_workflow_v6.py"),
        Path("tests/test_accepted_review_editorial_workflow_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_editorial_workflow_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False