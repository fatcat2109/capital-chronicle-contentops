import json
from pathlib import Path
from live_contentops import payload_preview_hash_v6 as preview_hash


def _write_committed_inputs(base_dir: Path, *, placeholder: bool = False, missing_summary: bool = False) -> None:
    delegated_dir = base_dir / "V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING"
    delegated_dir.mkdir(parents=True, exist_ok=True)

    if not missing_summary:
        summary = {
            "schema_version": "6.0.0",
            "fixture_completions": {
                "citation_candidates": True,
                "factual_claims": True,
                "intended_canonical_article_angle": True,
                "intended_content_lane": True,
                "limitation_notes": True,
                "no_signal_disclosure": True,
                "operator_idea_source_ref": True,
                "source_notes": True,
                "supporting_artifacts": True,
                "topic_statement": True,
            },
            "factual_claims_count": 3,
            "citation_candidates_count": 3,
            "verification_state": "PLACEHOLDER_PASS" if placeholder else "PASS",
            "contains_secrets_or_credentials": False,
            "contains_webhooks_or_cookies": False,
        }
        (delegated_dir / "delegated_evidence_fixture_redacted_summary.json").write_text(
            json.dumps(summary), encoding="utf-8"
        )

    source_map = {
        "schema_version": "6.0.0",
        "source_map": {
            "topic_and_claims_grounding": [
                "docs/automation/V6_NETWORK_SCOPE_POLICY/scoped_network_policy_v6.md",
                "docs/automation/V6_OPERATOR_PIPELINE_STATUS_CONSOLIDATION/operator_pipeline_status_packet.json",
            ]
        },
    }
    (delegated_dir / "delegated_evidence_source_map.json").write_text(json.dumps(source_map), encoding="utf-8")

    refresh = {
        "schema_version": "6.0.0",
        "refresh_execution_status": "SUCCESS",
        "refresh_status": "PREFLIGHT_CANDIDATE_READY_FOR_APPROVAL",
        "evidence_complete": True,
        "source_preflight_ready": True,
        "failed_lanes_count": 0,
        "kill_switch_active": True,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
    }
    (delegated_dir / "delegated_evidence_refresh_result.json").write_text(json.dumps(refresh), encoding="utf-8")


def test_committed_preview_hash_packet_properties():
    out_dir = Path("docs/automation/V6_PAYLOAD_PREVIEW_HASH")
    preview_hash.main(["--output-dir", str(out_dir)])

    packet_file = out_dir / "payload_preview_hash_packet.json"
    assert packet_file.exists()

    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["payload_preview_status"] == "READY_FOR_OPERATOR_REVIEW"
    assert data["payload_hash_created"] is True
    assert data["exact_payload_preview_created"] is True
    assert data["evidence_complete"] is True
    assert data["source_preflight_ready"] is True

    assert data["approval_valid_for_dispatch"] is False
    assert data["dispatch_allowed_now"] is False
    assert data["live_write_allowed_now"] is False
    assert data["outbox_entry_created"] is False
    assert data["destination_binding_complete"] is False
    assert data["credentials_hydrated"] is False
    assert data["browser_session_started"] is False
    assert data["public_postable"] is False
    assert data["kill_switch_active"] is True
    assert data["next_recommended_task"] == "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_SIGNATURE_BINDING_LANE_HEAVY_BATCH_V0"


def test_payload_preview_is_review_only_and_grounded():
    out_dir = Path("docs/automation/V6_PAYLOAD_PREVIEW_HASH")
    preview_hash.main(["--output-dir", str(out_dir)])

    preview_file = out_dir / "payload_preview_exact_review.json"
    assert preview_file.exists()

    data = json.loads(preview_file.read_text(encoding="utf-8"))
    assert data["payload_type"] == "review_only_payload_preview"
    assert data["visibility_class"] == "review_only_payload_preview"
    assert data["approval_required"] is True
    assert data["dispatch_ready"] is False
    assert data["public_postable"] is False
    assert data["is_local_only"] is True
    assert data["content_lane"] == "operator_internal_review"
    assert "PLACEHOLDER" not in json.dumps(data)
    assert "factual_claims_count=3" in data["body_text"]


def test_hash_is_deterministic(tmp_path):
    out_dir1 = tmp_path / "run1"
    out_dir2 = tmp_path / "run2"
    _write_committed_inputs(out_dir1)
    _write_committed_inputs(out_dir2)

    preview_hash.main(["--output-dir", str(out_dir1)])
    preview_hash.main(["--output-dir", str(out_dir2)])

    rec1 = json.loads((out_dir1 / "V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json").read_text(encoding="utf-8"))
    rec2 = json.loads((out_dir2 / "V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json").read_text(encoding="utf-8"))

    assert rec1["payload_hash"] == rec2["payload_hash"]
    assert rec1["payload_hash_algorithm"] == "sha256"


def test_missing_committed_summary_blocks_hash_creation(tmp_path):
    out_dir = tmp_path / "blocked_missing"
    _write_committed_inputs(out_dir, missing_summary=True)

    preview_hash.main(["--output-dir", str(out_dir)])

    packet = json.loads((out_dir / "V6_PAYLOAD_PREVIEW_HASH/payload_preview_hash_packet.json").read_text(encoding="utf-8"))
    record = json.loads((out_dir / "V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json").read_text(encoding="utf-8"))
    blocked_inputs = json.loads((out_dir / "V6_PAYLOAD_PREVIEW_HASH/payload_hash_inputs_redacted.json").read_text(encoding="utf-8"))

    assert packet["payload_preview_status"] == "BLOCKED_EXACT_PAYLOAD_MISSING"
    assert packet["payload_hash_created"] is False
    assert packet["exact_payload_preview_created"] is False
    assert record["payload_hash"] is None
    assert blocked_inputs["hash_blocked"] is True


def test_placeholder_tainted_committed_summary_blocks_hash_creation(tmp_path):
    out_dir = tmp_path / "blocked_placeholder"
    _write_committed_inputs(out_dir, placeholder=True)

    preview_hash.main(["--output-dir", str(out_dir)])

    packet = json.loads((out_dir / "V6_PAYLOAD_PREVIEW_HASH/payload_preview_hash_packet.json").read_text(encoding="utf-8"))
    preview = json.loads((out_dir / "V6_PAYLOAD_PREVIEW_HASH/payload_preview_exact_review.json").read_text(encoding="utf-8"))

    assert packet["payload_preview_status"] == "BLOCKED_EXACT_PAYLOAD_MISSING"
    assert packet["payload_hash_created"] is False
    assert "exact safe payload unavailable" in preview["title"].lower()


def test_no_sensitive_values_in_artifacts():
    out_dir = Path("docs/automation/V6_PAYLOAD_PREVIEW_HASH")
    preview_hash.main(["--output-dir", str(out_dir)])

    files = [
        out_dir / "payload_preview_hash_packet.json",
        out_dir / "payload_preview_exact_review.json",
        out_dir / "payload_hash_record.json",
        out_dir / "payload_hash_inputs_redacted.json",
        out_dir / "payload_preview_blocker_report.md",
        out_dir / "payload_preview_runbook.md",
        out_dir / "implementation_report.md",
        out_dir / "next_task_pointer.md"
    ]

    for f in files:
        assert f.exists()
        content = f.read_text(encoding="utf-8")
        assert "discord.com/api/webhooks" not in content
        assert "token_value" not in content.lower()
        assert "cookie_value" not in content.lower()
        assert "secret_key" not in content.lower()
        assert "env_value" not in content.lower()
        assert "PLACEHOLDER_TOPIC" not in content
        assert "PLACEHOLDER_LANE" not in content
        assert "PLACEHOLDER_ANGLE" not in content


def test_module_contains_no_forbidden_behavior():
    attrs = dir(preview_hash)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
