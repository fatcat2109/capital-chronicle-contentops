"""Test V6 Canonical Article Studio Review Queue Validator."""
from __future__ import annotations

from live_contentops import canonical_article_studio_queue_packet_v6 as packet_builder
from live_contentops import canonical_article_studio_review_checklist_v6 as checklist_builder
from live_contentops import canonical_article_studio_review_queue_v6 as coordinator
from live_contentops import canonical_article_studio_review_queue_validator_v6 as validator


def test_validator_passes_on_clean_simulated_state():
    queue_packet = packet_builder.make_canonical_article_studio_queue_packet()
    review_item = coordinator.make_review_item()
    editor_checklist = checklist_builder.make_canonical_article_studio_editor_checklist()
    html_mock = coordinator.make_local_mock_html()
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_review_queue(
        queue_packet, review_item, editor_checklist, html_mock, manifest
    )

    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert len(blockers) == 8
    assert "runtime_operator_approval_missing" in blockers
    assert "real_source_pack_not_approved" in blockers
    assert "article_copy_generation_blocked" in blockers
    assert "editor_review_required" in blockers
    assert "jim_review_required" in blockers
    assert "publication_blocked" in blockers
    assert "dispatch_blocked" in blockers
    assert "human_review_required" in blockers


def test_validator_fails_on_active_article_copy():
    queue_packet = packet_builder.make_canonical_article_studio_queue_packet()
    queue_packet["article_copy_generated"] = True
    review_item = coordinator.make_review_item()
    editor_checklist = checklist_builder.make_canonical_article_studio_editor_checklist()
    html_mock = coordinator.make_local_mock_html()
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_review_queue(
        queue_packet, review_item, editor_checklist, html_mock, manifest
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"


def test_validator_fails_on_active_dispatch_flags():
    queue_packet = packet_builder.make_canonical_article_studio_queue_packet()
    queue_packet["public_postable"] = True
    review_item = coordinator.make_review_item()
    editor_checklist = checklist_builder.make_canonical_article_studio_editor_checklist()
    html_mock = coordinator.make_local_mock_html()
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_review_queue(
        queue_packet, review_item, editor_checklist, html_mock, manifest
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "forbidden_active_dispatch_flags" in blockers


def test_validator_fails_on_source_name_leak():
    queue_packet = packet_builder.make_canonical_article_studio_queue_packet()
    review_item = coordinator.make_review_item()
    review_item["title_placeholder"] = "Federal Reserve Analysis"
    editor_checklist = checklist_builder.make_canonical_article_studio_editor_checklist()
    html_mock = coordinator.make_local_mock_html()
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_review_queue(
        queue_packet, review_item, editor_checklist, html_mock, manifest
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_name_leak_detected" in blockers


def test_validator_fails_on_url_leak():
    queue_packet = packet_builder.make_canonical_article_studio_queue_packet()
    review_item = coordinator.make_review_item()
    editor_checklist = checklist_builder.make_canonical_article_studio_editor_checklist()
    html_mock = coordinator.make_local_mock_html() + "\nhttps://example.com/source"
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_review_queue(
        queue_packet, review_item, editor_checklist, html_mock, manifest
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "url_leak_in_runtime_artifact" in blockers


def test_validator_fails_on_hash_leak():
    queue_packet = packet_builder.make_canonical_article_studio_queue_packet()
    review_item = coordinator.make_review_item()
    editor_checklist = checklist_builder.make_canonical_article_studio_editor_checklist()
    html_mock = coordinator.make_local_mock_html() + "\nsha256:e3b0c442"
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_review_queue(
        queue_packet, review_item, editor_checklist, html_mock, manifest
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "hash_leak_in_runtime_artifact" in blockers


def test_validator_fails_on_citation_leak():
    queue_packet = packet_builder.make_canonical_article_studio_queue_packet()
    review_item = coordinator.make_review_item()
    editor_checklist = checklist_builder.make_canonical_article_studio_editor_checklist()
    html_mock = coordinator.make_local_mock_html() + "\nSee source [1]"
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_review_queue(
        queue_packet, review_item, editor_checklist, html_mock, manifest
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "citation_or_source_reference_leak_detected" in blockers


def test_validator_fails_on_excerpt_leak():
    queue_packet = packet_builder.make_canonical_article_studio_queue_packet()
    review_item = coordinator.make_review_item()
    editor_checklist = checklist_builder.make_canonical_article_studio_editor_checklist()
    html_mock = coordinator.make_local_mock_html() + "\nExcerpt: the yield is up"
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_review_queue(
        queue_packet, review_item, editor_checklist, html_mock, manifest
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_excerpt_leak_in_runtime_artifact" in blockers


def test_validator_fails_on_financial_advice_leak():
    queue_packet = packet_builder.make_canonical_article_studio_queue_packet()
    review_item = coordinator.make_review_item()
    editor_checklist = checklist_builder.make_canonical_article_studio_editor_checklist()
    html_mock = coordinator.make_local_mock_html() + "\nThis is a buy setup."
    manifest = coordinator.make_screenshot_manifest()

    report, blockers = validator.validate_canonical_article_studio_review_queue(
        queue_packet, review_item, editor_checklist, html_mock, manifest
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "financial_advice_or_signal_language_detected" in blockers


def test_no_forbidden_imports_in_validator():
    import live_contentops.canonical_article_studio_review_queue_validator_v6 as target_module
    attrs = dir(target_module)
    forbidden = ["urlopen", "requests", "httpx", "getenv", "environ", "openai", "anthropic", "google"]
    for f in forbidden:
        assert f not in attrs
