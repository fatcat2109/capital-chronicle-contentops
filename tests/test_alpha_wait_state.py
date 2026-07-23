import os

from live_contentops import alpha_wait_state as aws
from live_contentops import final_bundle_manifest as fbm


def test_wait_state_record_has_all_required_fields():
    rec = aws.build_wait_state_record()
    required = [
        "wait_state_id", "repo_path", "accepted_starting_head", "current_phase",
        "wait_state_status", "reason_for_wait_state", "built_capabilities_summary",
        "intentionally_disabled_capabilities", "required_before_real_alpha_intake",
        "required_before_public_content", "required_before_any_live_integration",
        "safe_operator_actions_now", "forbidden_operator_actions_now",
        "known_caveats", "next_recommended_task", "local_only", "advisory_only",
        "fixture_only", "requires_real_alpha_artifacts_now",
        "public_content_allowed_now", "live_integration_allowed_now",
        "human_review_required", "approval_granted", "publish_ready",
        "provider_call_allowed", "search_call_allowed", "platform_action_allowed",
    ]
    for key in required:
        assert key in rec, f"missing field: {key}"


def test_wait_state_status_is_waiting():
    rec = aws.build_wait_state_record()
    assert rec["wait_state_status"] == "WAITING_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS"


def test_no_real_alpha_required_now():
    rec = aws.build_wait_state_record()
    assert rec["requires_real_alpha_artifacts_now"] is False


def test_public_content_and_live_integration_not_allowed_now():
    rec = aws.build_wait_state_record()
    assert rec["public_content_allowed_now"] is False
    assert rec["live_integration_allowed_now"] is False


def test_no_authority_granted():
    rec = aws.build_wait_state_record()
    for flag in ("approval_granted", "publish_ready", "provider_call_allowed",
                 "search_call_allowed", "platform_action_allowed"):
        assert rec[flag] is False
    assert rec["human_review_required"] is True


def test_built_and_disabled_capabilities_present():
    rec = aws.build_wait_state_record()
    assert len(rec["built_capabilities_summary"]) >= 10
    disabled = " ".join(rec["intentionally_disabled_capabilities"]).lower()
    assert "provider" in disabled
    assert "network" in disabled
    assert "platform" in disabled
    assert "core repo" in disabled


def test_readiness_checklists_exist():
    rec = aws.build_wait_state_record()
    assert len(rec["required_before_real_alpha_intake"]) >= 5
    assert len(rec["required_before_public_content"]) >= 5
    assert len(rec["required_before_any_live_integration"]) >= 5


def test_runbook_includes_hard_boundaries():
    docs = os.path.join(os.path.dirname(__file__), "..", "docs")
    path = os.path.join(docs, "ALPHA_WAIT_STATE_OPERATOR_RUNBOOK_AFTER_0073.md")
    if not os.path.isfile(path):
        path = os.path.join(docs, "archive", "stale_prelaunch_reset_0174CG", "ALPHA_WAIT_STATE_OPERATOR_RUNBOOK_AFTER_0073.md")
    assert os.path.isfile(path)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    for banner in ("NO PROVIDER CALL", "NO PLATFORM ACTION", "NOT PUBLIC POSTABLE",
                   "WAITING_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS"):
        assert banner in text


def test_0073_bundle_docs_exist():
    for name in ("NEW_CHAT_CONTINUATION_AFTER_0073.md",
                 "UPLOAD_BUNDLE_MANIFEST_AFTER_0073.md",
                 "PROJECT_SOURCE_EXPORT_AFTER_0073.md",
                 "CURRENT_STATE_SUMMARY_AFTER_0073.md",
                 "ALPHA_WAIT_STATE_OPERATOR_RUNBOOK_AFTER_0073.md",
                 "TASK_CONTENTOPS_0073_EXTREME_LOCAL_ALPHA_WAIT_STATE_OPERATOR_RUNBOOK_FINAL_BUNDLE_AND_PATH_REPAIR_V0.md"):
        assert fbm.resolve_historical_doc(name) is not None, f"missing doc: {name}"


def test_recommended_upload_paths_exist_and_unique():
    manifest = fbm.build_manifest()
    paths = [e["path"] for e in manifest["recommended_uploads"]]
    assert len(paths) == len(set(paths)), "duplicate recommended upload paths"
    for p in paths:
        assert fbm.resolve_historical_doc(p) is not None, f"missing: {p}"


def test_manifest_excludes_gitignore_and_unsafe_categories():
    manifest = fbm.build_manifest()
    cats = " ".join(manifest["excluded_categories"]).lower()
    for needle in ("env", "credential", "secret", "raw_log", "provider_output",
                   "platform_id", "pycache", ".gitignore", "sibling",
                   "public_postable", "stale_0069_0072"):
        assert needle in cats, f"missing exclusion: {needle}"
    paths = " ".join(e["path"] for e in manifest["recommended_uploads"]).lower()
    assert ".gitignore" not in paths


def test_no_upload_entry_grants_authority():
    manifest = fbm.build_manifest()
    for e in manifest["recommended_uploads"]:
        assert e["contains_secrets"] is False
        assert e["contains_live_ids"] is False
        assert e["contains_provider_outputs"] is False
        assert e["contains_public_postable_content"] is False
        assert e["safety_status"] == "SAFE_FOR_PROJECT_SOURCES"
    for flag in ("approval_granted", "publish_ready", "provider_call_allowed",
                 "search_call_allowed", "platform_action_allowed"):
        assert manifest[flag] is False


def test_manifest_validation_passes():
    res = fbm.validate_manifest()
    assert res["status"] == "PASS", res["blockers"]
    assert res["blockers"] == []


def test_bundle_supersedes_0072_and_0069():
    manifest = fbm.build_manifest()
    supersedes = " ".join(manifest["supersedes"]).lower()
    assert "0072" in supersedes
    assert "0069" in supersedes


def test_no_stale_non_underscore_variants_recommended():
    manifest = fbm.build_manifest()
    for e in manifest["recommended_uploads"]:
        assert "after0073" not in e["path"].lower()
        assert "contentops0073" not in e["path"].lower()


def test_summary_fields():
    s = aws.build_summary()
    assert s["alpha_wait_state_enabled"] is True
    assert s["wait_state_status"] == "WAITING_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS"
    assert s["requires_real_alpha_artifacts_now"] is False
    assert s["public_content_allowed_now"] is False
    assert s["live_integration_allowed_now"] is False
    assert s["all_exports_safe_for_project_sources"] is True
    assert s["recommended_upload_count"] == 6
    assert s["next_recommended_task"] == aws.NEXT_RECOMMENDED_TASK

