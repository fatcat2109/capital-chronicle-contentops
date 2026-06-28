"""Test V6 Canonical Article Studio Editor Shell Validator."""
from __future__ import annotations

from live_contentops import canonical_article_studio_draft_shell_packet_v6 as packet_builder
from live_contentops import canonical_article_studio_draft_slot_schema_v6 as schema_builder
from live_contentops import canonical_article_studio_editor_shell_v6 as coordinator
from live_contentops import canonical_article_studio_editor_shell_validator_v6 as validator


def test_validator_passes_on_clean_simulated_state():
    shell_packet = packet_builder.make_canonical_article_studio_draft_shell_packet()
    slot_schema = schema_builder.make_canonical_article_studio_draft_slot_schema()
    shell_instance = coordinator.make_draft_shell_instance()
    editor_checklist = coordinator.make_editor_shell_checklist()
    html_mock = coordinator.make_local_mock_html()
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_editor_shell(
        shell_packet, slot_schema, shell_instance, editor_checklist, html_mock, manifest
    )

    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert len(blockers) == 11
    assert "real_source_pack_not_approved" in blockers
    assert "runtime_operator_approval_missing" in blockers
    assert "article_copy_generation_blocked" in blockers
    assert "title_generation_blocked" in blockers
    assert "citation_generation_blocked" in blockers
    assert "seo_generation_blocked" in blockers
    assert "editor_review_required" in blockers
    assert "jim_review_required" in blockers
    assert "publication_blocked" in blockers
    assert "dispatch_blocked" in blockers
    assert "human_review_required" in blockers


def test_validator_fails_on_generated_body():
    shell_packet = packet_builder.make_canonical_article_studio_draft_shell_packet()
    shell_packet["article_body_generated"] = True
    slot_schema = schema_builder.make_canonical_article_studio_draft_slot_schema()
    shell_instance = coordinator.make_draft_shell_instance()
    editor_checklist = coordinator.make_editor_shell_checklist()
    html_mock = coordinator.make_local_mock_html()
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_editor_shell(
        shell_packet, slot_schema, shell_instance, editor_checklist, html_mock, manifest
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "article_copy_generation_blocked" in blockers


def test_validator_fails_on_non_empty_slot_value():
    shell_packet = packet_builder.make_canonical_article_studio_draft_shell_packet()
    slot_schema = schema_builder.make_canonical_article_studio_draft_slot_schema()
    slot_schema[0]["current_value"] = "Some actual title"
    shell_instance = coordinator.make_draft_shell_instance()
    editor_checklist = coordinator.make_editor_shell_checklist()
    html_mock = coordinator.make_local_mock_html()
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_editor_shell(
        shell_packet, slot_schema, shell_instance, editor_checklist, html_mock, manifest
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "non_empty_slot_value_detected" in blockers


def test_validator_fails_on_non_zero_word_count():
    shell_packet = packet_builder.make_canonical_article_studio_draft_shell_packet()
    slot_schema = schema_builder.make_canonical_article_studio_draft_slot_schema()
    shell_instance = coordinator.make_draft_shell_instance()
    shell_instance["body_word_count"] = 150
    editor_checklist = coordinator.make_editor_shell_checklist()
    html_mock = coordinator.make_local_mock_html()
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_editor_shell(
        shell_packet, slot_schema, shell_instance, editor_checklist, html_mock, manifest
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "non_zero_word_or_citation_count_detected" in blockers


def test_validator_fails_on_active_dispatch_flags():
    shell_packet = packet_builder.make_canonical_article_studio_draft_shell_packet()
    shell_packet["public_postable"] = True
    slot_schema = schema_builder.make_canonical_article_studio_draft_slot_schema()
    shell_instance = coordinator.make_draft_shell_instance()
    editor_checklist = coordinator.make_editor_shell_checklist()
    html_mock = coordinator.make_local_mock_html()
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_editor_shell(
        shell_packet, slot_schema, shell_instance, editor_checklist, html_mock, manifest
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "forbidden_active_dispatch_flags" in blockers


def test_validator_fails_on_source_name_leak():
    shell_packet = packet_builder.make_canonical_article_studio_draft_shell_packet()
    slot_schema = schema_builder.make_canonical_article_studio_draft_slot_schema()
    shell_instance = coordinator.make_draft_shell_instance()
    editor_checklist = coordinator.make_editor_shell_checklist()
    html_mock = coordinator.make_local_mock_html() + "\nSource: Bloomberg"
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_editor_shell(
        shell_packet, slot_schema, shell_instance, editor_checklist, html_mock, manifest
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_name_leak_detected" in blockers


def test_validator_fails_on_url_leak():
    shell_packet = packet_builder.make_canonical_article_studio_draft_shell_packet()
    slot_schema = schema_builder.make_canonical_article_studio_draft_slot_schema()
    shell_instance = coordinator.make_draft_shell_instance()
    editor_checklist = coordinator.make_editor_shell_checklist()
    html_mock = coordinator.make_local_mock_html() + "\nhttps://example.com/source"
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_editor_shell(
        shell_packet, slot_schema, shell_instance, editor_checklist, html_mock, manifest
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "url_leak_in_runtime_artifact" in blockers


def test_validator_fails_on_hash_leak():
    shell_packet = packet_builder.make_canonical_article_studio_draft_shell_packet()
    slot_schema = schema_builder.make_canonical_article_studio_draft_slot_schema()
    shell_instance = coordinator.make_draft_shell_instance()
    editor_checklist = coordinator.make_editor_shell_checklist()
    html_mock = coordinator.make_local_mock_html() + "\nsha256:e3b0c442"
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_editor_shell(
        shell_packet, slot_schema, shell_instance, editor_checklist, html_mock, manifest
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "hash_leak_in_runtime_artifact" in blockers


def test_no_forbidden_imports_in_validator():
    import live_contentops.canonical_article_studio_editor_shell_validator_v6 as target_module
    attrs = dir(target_module)
    forbidden = ["urlopen", "requests", "httpx", "getenv", "environ", "openai", "anthropic", "google"]
    for f in forbidden:
        assert f not in attrs
