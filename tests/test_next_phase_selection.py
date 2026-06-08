import json
import os

from live_contentops import next_phase_selection as nps


REPO_DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")


def test_refreshed_0069_docs_exist():
    for name in ("NEW_CHAT_CONTINUATION_AFTER_0069.md",
                 "UPLOAD_BUNDLE_MANIFEST_AFTER_0069.md",
                 "PROJECT_SOURCE_EXPORT_AFTER_0069.md",
                 "TASK_CONTENTOPS_0069_LOCAL_BUNDLE_REFRESH_AND_NEXT_PHASE_SELECTION_V0.md"):
        assert os.path.isfile(os.path.join(REPO_DOCS, name)), f"missing doc: {name}"


def test_bundle_supersedes_0068_and_older():
    b = nps.build_refresh_bundle()
    assert b["supersedes_0068_bundle"] is True
    assert b["supersedes_older_source_bundles"] is True


def test_recommended_upload_paths_exist_and_unique():
    b = nps.build_refresh_bundle()
    paths = [f["path"] for f in b["included_files"] if f.get("upload_recommended")]
    assert len(paths) == len(set(paths))
    repo_root = os.path.join(os.path.dirname(__file__), "..")
    for p in paths:
        assert os.path.isfile(os.path.join(repo_root, p)), f"missing doc: {p}"


def test_unsafe_categories_remain_excluded():
    b = nps.build_refresh_bundle()
    excluded = {c["category"] for c in b["excluded_categories"]}
    for required in ("env_files", "credentials_tokens_secrets", "raw_logs",
                     "provider_outputs", "platform_ids", "pycache_compiled",
                     "full_output_history", "gitignore_operator_drift",
                     "sibling_or_core_repo_files"):
        assert required in excluded, f"missing exclusion: {required}"


def test_gitignore_remains_excluded():
    b = nps.build_refresh_bundle()
    excluded = {c["category"] for c in b["excluded_categories"]}
    assert "gitignore_operator_drift" in excluded
    for f in b["included_files"]:
        assert ".gitignore" not in f["path"].lower()


def test_future_chats_not_pointed_to_stale_pre_repair_head():
    b = nps.build_refresh_bundle()
    assert b["starting_head_for_0069"] == "77ecb27"
    assert b["starting_head_for_0069"] != "68b041c"
    assert b["starting_head_for_0069"] != "cd72ee4"


def test_next_task_is_0070_intake_contract():
    b = nps.build_refresh_bundle()
    assert b["selected_next_task"] == \
        "TASK_CONTENTOPS_0070_LOCAL_REAL_ARTIFACT_INTAKE_CONTRACT_AND_READINESS_GATE_V0"


def test_option_d_live_work_blocked():
    record = nps.build_next_phase_record()
    assert record["selected_option"] != "D"
    assert "D" in record["blocked_options"]
    d = next(o for o in record["options"] if o["option"] == "D")
    assert d["status"] == "BLOCKED"


def test_real_artifact_intake_is_fixture_only():
    record = nps.build_next_phase_record()
    boundary = " ".join(record["real_artifact_intake_boundary"])
    assert "No dependency on real alpha artifacts yet" in boundary
    assert "fixture-only" in boundary.lower()


def test_continuation_packet_has_boundaries_and_local_only():
    path = os.path.join(REPO_DOCS, "NEW_CHAT_CONTINUATION_AFTER_0069.md")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    assert "LOCAL ONLY" in text
    assert "Hard boundaries" in text
    assert "No network." in text
    assert "77ecb27" in text
    assert "Do NOT resume from 68b041c" in text or "Do not resume from 68b041c" in text


def test_validation_clean_after_docs_exist():
    b = nps.build_refresh_bundle()
    res = nps.validate_refresh_bundle(b)
    assert res["status"] in ("PASS", "WARNING")
    assert res["blockers"] == []


def test_validation_blocks_stale_head():
    b = nps.build_refresh_bundle()
    b["starting_head_for_0069"] = "68b041c"
    res = nps.validate_refresh_bundle(b)
    assert res["status"] == "BLOCKED"
    assert any("stale pre-repair head" in x for x in res["blockers"])


def test_summary_is_deterministic():
    s1 = nps.build_summary()
    s2 = nps.build_summary()
    assert json.dumps(s1, sort_keys=True) == json.dumps(s2, sort_keys=True)
    assert s1["selected_option"] == "C"
    assert s1["previous_bundle_superseded"] is True
