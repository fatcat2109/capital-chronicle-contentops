import json
import os

from live_contentops import review_bundle_manifest as m


REPO_DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")


def test_manifest_has_required_safe_categories():
    man = m.build_manifest()
    artifact_types = {f["artifact_type"] for f in man["included_files"]}
    # Safe inclusion categories present.
    for expected in ("continuation_packet", "upload_manifest",
                     "project_source_export", "completed_task_summary",
                     "dashboard_handoff_report"):
        assert expected in artifact_types, f"missing artifact_type: {expected}"


def test_included_files_have_required_fields():
    man = m.build_manifest()
    required = [
        "path", "artifact_type", "reason_for_inclusion", "authority_role",
        "safety_status", "contains_secrets", "contains_live_ids",
        "contains_raw_logs", "contains_provider_outputs",
        "contains_public_postable_content", "upload_recommended",
    ]
    for f in man["included_files"]:
        for key in required:
            assert key in f, f"missing field {key} in {f.get('path')}"
        assert f["contains_secrets"] is False
        assert f["contains_live_ids"] is False
        assert f["contains_public_postable_content"] is False


def test_manifest_excludes_unsafe_categories():
    man = m.build_manifest()
    excluded = {c["category"] for c in man["excluded_categories"]}
    for required in ("env_files", "credentials_tokens_secrets", "raw_logs",
                     "provider_outputs", "platform_ids", "pycache_compiled",
                     "full_output_history", "large_fixture_dumps",
                     "raw_vendor_data", "public_postable_fake_content"):
        assert required in excluded, f"missing exclusion: {required}"


def test_gitignore_is_excluded():
    man = m.build_manifest()
    excluded = {c["category"] for c in man["excluded_categories"]}
    assert "gitignore_operator_drift" in excluded
    # No included file references .gitignore.
    for f in man["included_files"]:
        assert ".gitignore" not in f["path"].lower()


def test_sibling_core_repo_files_excluded():
    man = m.build_manifest()
    excluded = {c["category"] for c in man["excluded_categories"]}
    assert "sibling_or_core_repo_files" in excluded
    for f in man["included_files"]:
        assert "cc-contentops" not in f["path"].lower()


def test_accepted_head_and_next_task_present():
    man = m.build_manifest()
    assert man["accepted_head"]
    assert man["next_task"]
    assert man["next_task"].startswith("TASK_CONTENTOPS_")

def test_task_0068_completed_head_is_cd72ee4():
    man = m.build_manifest()
    assert man["task_0068_completed_head"] == "cd72ee4"
    assert m.build_summary()["task_0068_completed_head"] == "cd72ee4"


def test_bundle_base_head_is_not_current_accepted():
    man = m.build_manifest()
    assert man["bundle_base_head"] == "68b041c"
    # The base head must never be presented as the current accepted head.
    assert man["accepted_head"] != "68b041c"
    assert man["accepted_head"] == "cd72ee4"


def test_current_next_task_is_0069():
    man = m.build_manifest()
    assert man["current_next_task"] == \
        "TASK_CONTENTOPS_0069_LOCAL_BUNDLE_REFRESH_AND_NEXT_PHASE_SELECTION_V0"


def test_continuation_doc_states_0068_completed_at_cd72ee4():
    path = os.path.join(REPO_DOCS, "NEW_CHAT_CONTINUATION_AFTER_0068.md")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    assert "cd72ee4" in text
    assert "COMPLETED at cd72ee4" in text
    assert "must NOT resume from 68b041c" in text


def test_recommended_upload_paths_exist_and_unique():
    man = m.build_manifest()
    paths = [f["path"] for f in man["included_files"] if f.get("upload_recommended")]
    # No stale duplicate paths.
    assert len(paths) == len(set(paths))
    # Each recommended doc exists on disk.
    repo_root = os.path.join(os.path.dirname(__file__), "..")
    for p in paths:
        assert os.path.isfile(os.path.join(repo_root, p)), f"missing doc: {p}"




def test_manifest_supersedes_older_bundles():
    man = m.build_manifest()
    assert man["supersedes_older_source_bundles"] is True


def test_manifest_safety_flags():
    man = m.build_manifest()
    assert man["advisory_only"] is True
    assert man["local_only"] is True
    assert man["human_review_required"] is True
    assert man["approval_granted"] is False
    assert man["publish_ready"] is False
    assert man["provider_call_allowed"] is False
    assert man["search_call_allowed"] is False
    assert man["platform_action_allowed"] is False
    assert man["all_exports_safe_for_project_sources"] is True


def test_manifest_is_deterministic():
    m1 = m.build_manifest()
    m2 = m.build_manifest()
    assert json.dumps(m1, sort_keys=True) == json.dumps(m2, sort_keys=True)


def test_validation_clean():
    man = m.build_manifest()
    res = m.validate_manifest(man)
    assert res["status"] in ("PASS", "WARNING")
    assert res["blockers"] == []


def test_validation_blocks_unsafe_upload_path():
    man = m.build_manifest()
    man["included_files"].append({
        "path": "config/.env", "artifact_type": "env_file",
        "authority_role": "NONE", "upload_recommended": True,
        "contains_secrets": True, "contains_live_ids": False,
        "contains_raw_logs": False, "contains_provider_outputs": False,
        "contains_public_postable_content": False,
    })
    res = m.validate_manifest(man)
    assert res["status"] == "BLOCKED"
    assert any(".env" in b for b in res["blockers"])


def test_validation_blocks_gitignore_upload():
    man = m.build_manifest()
    man["included_files"].append({
        "path": ".gitignore", "artifact_type": "config",
        "authority_role": "NONE", "upload_recommended": True,
        "contains_secrets": False, "contains_live_ids": False,
        "contains_raw_logs": False, "contains_provider_outputs": False,
        "contains_public_postable_content": False,
    })
    res = m.validate_manifest(man)
    assert res["status"] == "BLOCKED"
    assert any(".gitignore" in b for b in res["blockers"])


def test_validation_blocks_publish_authority_artifact():
    man = m.build_manifest()
    man["included_files"].append({
        "path": "docs/SOME_REPORT.md", "artifact_type": "report",
        "authority_role": "PUBLISH_APPROVAL", "upload_recommended": True,
        "contains_secrets": False, "contains_live_ids": False,
        "contains_raw_logs": False, "contains_provider_outputs": False,
        "contains_public_postable_content": False,
    })
    res = m.validate_manifest(man)
    assert res["status"] == "BLOCKED"
    assert any("publish/approval/platform authority" in b for b in res["blockers"])


def test_validation_blocks_public_postable_artifact():
    man = m.build_manifest()
    man["included_files"].append({
        "path": "docs/FAKE_POST.md", "artifact_type": "report",
        "authority_role": "NONE", "upload_recommended": True,
        "contains_secrets": False, "contains_live_ids": False,
        "contains_raw_logs": False, "contains_provider_outputs": False,
        "contains_public_postable_content": True,
    })
    res = m.validate_manifest(man)
    assert res["status"] == "BLOCKED"
    assert any("public-postable content" in b for b in res["blockers"])
