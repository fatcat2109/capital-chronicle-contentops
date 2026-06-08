import os

from live_contentops import ide_cli_document_bundle as b


DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")

_DOC_NAMES = [
    "IDE_CLI_DOCUMENT_BUNDLE_AFTER_0074.md",
    "IDE_CLI_QUICKSTART_AFTER_0074.md",
    "IDE_CLI_EVIDENCE_PACKET_TEMPLATE_AFTER_0074.md",
    "IDE_CLI_ALLOWED_MAINTENANCE_TASKS_AFTER_0074.md",
    "TASK_CONTENTOPS_0074_LOCAL_IDE_CLI_DOCUMENT_BUNDLE_FOR_ALPHA_WAIT_STATE_V0.md",
]


def _read(name):
    with open(os.path.join(DOCS, name), "r", encoding="utf-8") as f:
        return f.read()


def test_all_0074_docs_exist():
    for name in _DOC_NAMES:
        assert os.path.isfile(os.path.join(DOCS, name)), f"missing doc: {name}"


def test_master_bundle_required_sections():
    text = _read("IDE_CLI_DOCUMENT_BUNDLE_AFTER_0074.md")
    for needle in ("A:\\Capital Chronicle\\tools\\cc-live-contentops",
                   "f9c4d69",
                   "WAIT_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS_OR_OPERATOR_SELECTED_LOCAL_MAINTENANCE",
                   "Hard boundaries", ".gitignore", "Evidence packet"):
        assert needle in text, f"missing section: {needle}"


def test_quickstart_has_safe_rules():
    text = _read("IDE_CLI_QUICKSTART_AFTER_0074.md")
    assert "git add ." in text  # mentioned as forbidden
    assert ".gitignore" in text
    assert "python -m live_contentops.cli status" in text


def test_evidence_template_required_fields():
    text = _read("IDE_CLI_EVIDENCE_PACKET_TEMPLATE_AFTER_0074.md")
    for field in ("task label", "PASS / BLOCKED / FAIL", "starting HEAD",
                  "final HEAD", "suspicious scan result", "active blockers",
                  "exact next task"):
        assert field in text, f"missing field: {field}"


def test_allowed_maintenance_lists_present():
    text = _read("IDE_CLI_ALLOWED_MAINTENANCE_TASKS_AFTER_0074.md")
    assert "Allowed maintenance categories" in text
    assert "Forbidden maintenance categories" in text


def test_recommended_doc_paths_exact_and_unique():
    paths = b.RECOMMENDED_DOCS
    assert len(paths) == len(set(paths))
    for p in paths:
        assert os.path.isfile(os.path.join(DOCS, os.path.basename(p))), f"missing: {p}"
    # No .gitignore recommended.
    joined = " ".join(paths).lower()
    assert ".gitignore" not in joined


def test_summary_preserves_wait_state_and_adds_no_runtime():
    s = b.build_summary()
    assert s["document_bundle_enabled"] is True
    assert s["runtime_capability_added"] is False
    assert s["wait_state_preserved"] is True
    assert s["recommended_doc_count"] == 5
    for flag in ("contains_secrets", "contains_live_ids",
                 "contains_public_postable_content", "provider_call_allowed",
                 "search_call_allowed", "platform_action_allowed",
                 "approval_granted", "publish_ready"):
        assert s[flag] is False


def test_terminal_wait_state_pointer_unchanged():
    from live_contentops import status
    assert (status.get_status()["next_task"]
            == "WAIT_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS_OR_OPERATOR_SELECTED_LOCAL_MAINTENANCE")


def test_bundle_validation_passes():
    res = b.validate_bundle()
    assert res["status"] == "PASS", res["blockers"]
    assert res["blockers"] == []
