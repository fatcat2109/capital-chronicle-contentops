from __future__ import annotations

from pathlib import Path

from live_contentops import final_automation_closure_v1 as closure


def test_repair_plan_uses_exact_authorized_ids(tmp_path: Path):
    plan = closure.build_historical_repair_plan(output_dir=tmp_path)
    assert {row["post_id"] for row in plan["threads_delete_allowlist"]} == {
        "17967130901934350", "18368836642225190"
    }
    assert plan["linkedin_restore"]["post_id"] == "7481311616265895936"
    assert plan["linkedin_restore"]["text"] is None
    assert len(plan["linkedin_restore"]["text_sha256"]) == 64


def test_release_verifier_fails_closed_without_canary(tmp_path: Path):
    result = closure.verify_release_readiness(output_dir=tmp_path)
    assert result["classification"] == "BLOCKED_FINAL_AUTOMATION_PIPELINE_CLOSURE"
    assert "dqr_permissions_passed" in result["blockers"]
    assert result["v1_0_tag_allowed"] is False


def test_release_verifier_accepts_complete_machine_evidence(tmp_path: Path):
    closure._write(tmp_path / "historical_repair_result_v1.json", {
        "classification": "PASS_HISTORICAL_RC_TARGETED_REPAIR",
        "oil_substack_edited": True,
        "fresh_oil_linkedin_created": True,
    })
    generic = tmp_path / "generic.json"
    closure._write(generic, {
        "generic_live_path_used": True,
        "freshness_passed": True,
        "dqr_permissions_passed": True,
        "substack_plus_eight_derivatives_passed": True,
        "unresolved_unknown_writes": [],
    })
    result = closure.verify_release_readiness(output_dir=tmp_path, generic_result_path=generic)
    assert result["classification"] == "AWAITING_OPERATOR_FINAL_V1_0_ACCEPTANCE_NO_ENGINEERING_BLOCKERS"


def test_release_verifier_accepts_story_scoped_generic_live_evidence(tmp_path: Path, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(closure.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=""))
    required = ("substack", "telegram", "discord", "x", "linkedin", "facebook_page", "instagram_business", "threads", "youtube")
    generic = tmp_path / "run_evidence_v1.json"
    closure._write(generic, {
        "generic_live_path_used": True,
        "legacy_topic_adapter_used": False,
        "substack_caption_repair": {"status": "SUCCESS"},
        "final_auction_logic_repair": {
            "status": "SUCCESS",
            "numeric_claims_preserved": True,
            "frozen_derivatives_preserved": True,
            "derivative_writes_performed": False,
            "video_adapters_invoked": False,
        },
        "results": {name: {"status": "SUCCESS"} for name in required},
    })
    closure._write(tmp_path / "generic_database_preflight_result_v1.json", {"publication_eligible": True})
    closure._write(tmp_path / "freshness_market_state_decision_v2.json", {"decision": "PASS", "blockers": []})
    closure._write(tmp_path / "release_candidate_lock_v1.json", {
        "generic_live_path_used": True,
        "legacy_topic_adapter_used": False,
        "lock_sha256": "a" * 64,
        "artifacts": {"run_context_v1.json": {"exists": True}},
    })
    closure._write(tmp_path / "operator_manual_audit_packet_v1.json", {"machine_qa": {"status": "PASS"}})

    result = closure.verify_release_readiness(output_dir=tmp_path, generic_result_path=generic)

    assert result["classification"] == "AWAITING_OPERATOR_FINAL_V1_0_ACCEPTANCE_NO_ENGINEERING_BLOCKERS"
    assert result["checks"]["story_scoped_publication_authorized"] is True
    assert result["checks"]["final_auction_logic_repair_verified"] is True
    assert result["checks"]["final_repair_derivatives_frozen"] is True
    assert result["checks"]["v1_tag_absent"] is True
    assert "--run-id v1.0" in result["release_finalizer_command"]


def test_release_verifier_blocks_missing_final_auction_repair(tmp_path: Path):
    required = ("substack", "telegram", "discord", "x", "linkedin", "facebook_page", "instagram_business", "threads", "youtube")
    generic = tmp_path / "run_evidence_v1.json"
    closure._write(generic, {
        "generic_live_path_used": True,
        "legacy_topic_adapter_used": False,
        "substack_caption_repair": {"status": "SUCCESS"},
        "results": {name: {"status": "SUCCESS"} for name in required},
    })
    closure._write(tmp_path / "generic_database_preflight_result_v1.json", {"publication_eligible": True})
    closure._write(tmp_path / "freshness_market_state_decision_v2.json", {"decision": "PASS", "blockers": []})
    closure._write(tmp_path / "release_candidate_lock_v1.json", {
        "generic_live_path_used": True,
        "legacy_topic_adapter_used": False,
        "lock_sha256": "a" * 64,
        "artifacts": {"run_context_v1.json": {"exists": True}},
    })
    closure._write(tmp_path / "operator_manual_audit_packet_v1.json", {"machine_qa": {"status": "PASS"}})

    result = closure.verify_release_readiness(output_dir=tmp_path, generic_result_path=generic)

    assert result["classification"] == "BLOCKED_FINAL_AUTOMATION_PIPELINE_CLOSURE"
    assert "final_auction_logic_repair_verified" in result["blockers"]
    assert "final_repair_numeric_claims_preserved" in result["blockers"]
    assert "final_repair_derivatives_frozen" in result["blockers"]


def test_release_finalizer_fails_closed_without_acceptance(tmp_path: Path):
    verifier = tmp_path / "verifier.json"
    closure._write(verifier, {
        "classification": "AWAITING_OPERATOR_FINAL_V1_0_ACCEPTANCE_NO_ENGINEERING_BLOCKERS",
        "blockers": [],
    })
    result = closure.finalize_v1_tag(verifier_path=verifier, operator_acceptance="REJECT")
    assert result["status"] == "BLOCKED_RELEASE_FINALIZER_PRECONDITIONS"
    assert result["checks"]["operator_acceptance"] is False
    assert result["tag_created"] is False


def test_release_finalizer_creates_and_verifies_exact_v1_tag(tmp_path: Path, monkeypatch):
    verifier = tmp_path / "verifier.json"
    closure._write(verifier, {
        "classification": "AWAITING_OPERATOR_FINAL_V1_0_ACCEPTANCE_NO_ENGINEERING_BLOCKERS",
        "blockers": [],
    })
    head = "f" * 40
    calls: list[tuple[str, ...]] = []

    class Result:
        def __init__(self, stdout: str = "") -> None:
            self.stdout = stdout

    def run(command, **kwargs):
        args = tuple(command[1:])
        calls.append(args)
        outputs = {
            ("branch", "--show-current"): "master\n",
            ("rev-parse", "HEAD"): f"{head}\n",
            ("rev-parse", "origin/master"): f"{head}\n",
            ("tag", "--list", "v1.0"): "",
            ("ls-remote", "origin", "refs/tags/v1.0^{}"): f"{head}\trefs/tags/v1.0^{{}}\n",
        }
        return Result(outputs.get(args, ""))

    monkeypatch.setattr(closure.subprocess, "run", run)

    result = closure.finalize_v1_tag(verifier_path=verifier, operator_acceptance="ACCEPT")

    assert result["status"] == "SUCCESS_RELEASE_TAG_CREATED_AND_PUSHED"
    assert result["tag"] == "v1.0"
    assert result["tag_message"] == "Capital Chronicle ContentOps v1.0 — database-authorized supervised nine-surface release"
    assert result["remote_tag_commit_sha"] == head
    assert (
        "tag", "-a", "v1.0", "-m",
        "Capital Chronicle ContentOps v1.0 — database-authorized supervised nine-surface release",
    ) in calls
    assert ("push", "origin", "v1.0") in calls
    assert ("ls-remote", "origin", "refs/tags/v1.0^{}") in calls
