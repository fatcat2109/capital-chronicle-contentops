from dataclasses import replace
from pathlib import Path

import pytest

from live_contentops import primary_platform_payload_preview_contracts as previews
from live_contentops import substack_newsletter_manual_export_contract as substack


SEO = {
    "seo_title": "Why limits come before distribution",
    "seo_description": "A ContentOps newsletter about source trust, citations, and manual export limits.",
    "seo_keywords": ("content operations", "source trust", "manual export"),
    "slug_suggestion": "why-limits-come-before-distribution",
}


def newsletter_preview(**overrides):
    kwargs = {
        "source_content_id": "source_content_test",
        "source_draft_id": "source_draft_test",
        "title": "Source trust before distribution",
        "subtitle": "A process note",
        "body": "Manual export preserves citations and limitations.",
        "markdown_body": "Manual export preserves citations and limitations.",
        "citation_refs": ("source:test",),
        "limitation_notes": ("local manual export only",),
        "content_lane": "grounded_news_context",
        "source_claims_exist": True,
    }
    kwargs.update(overrides)
    return previews.build_substack_newsletter_issue_preview(**kwargs)


def longform_preview(**overrides):
    kwargs = {
        "source_content_id": "source_content_longform_test",
        "source_draft_id": "source_draft_longform_test",
        "title": "Manual export longform",
        "subtitle": "A longer process note",
        "body": "Longform export preserves citations and limitations.",
        "markdown_body": "Longform export preserves citations and limitations.",
        "citation_refs": ("source:test",),
        "limitation_notes": ("local manual export only",),
        "content_lane": "grounded_news_context",
        "source_claims_exist": True,
    }
    kwargs.update(overrides)
    return previews.build_substack_longform_post_preview(**kwargs)


def build_issue(preview=None, **overrides):
    kwargs = {
        "hook": "Manual export stays controlled.",
        "thesis_or_question": "What must remain visible before export?",
        "body_sections": ("Citations and limitations remain visible.",),
        "source_notes": ("source packet local",),
        "seo_metadata": SEO,
        "cross_platform_derivative_refs": ("x_short_post:preview",),
        "source_claims_exist": True,
    }
    kwargs.update(overrides)
    return substack.build_substack_newsletter_issue_from_preview(preview or newsletter_preview(), **kwargs)


def build_package(issue=None, **overrides):
    return substack.build_manual_export_package(issue or build_issue(), **overrides)


def test_newsletter_issue_builds_from_substack_newsletter_preview():
    preview = newsletter_preview()
    issue = build_issue(preview)

    assert issue.platform_id == "substack_newsletter"
    assert issue.payload_class_id == "substack_newsletter_issue"
    assert issue.issue_type == "newsletter_issue"
    assert issue.source_preview_id == preview.preview_id
    assert issue.source_payload_hash == preview.payload_hash
    assert issue.manual_export_status == substack.READY_FOR_MANUAL_REVIEW
    assert issue.dispatch_ready is False
    assert issue.public_postable is False


def test_longform_post_builds_from_substack_longform_preview():
    preview = longform_preview()
    issue = substack.build_substack_longform_post_from_preview(
        preview,
        hook="Longform stays manual.",
        thesis_or_question="How should longform exports stay bounded?",
        body_sections=("Longform export remains local and manual.",),
        seo_metadata=SEO,
        source_claims_exist=True,
    )

    assert issue.payload_class_id == "substack_longform_post"
    assert issue.issue_type == "longform_post"
    assert issue.source_payload_hash == preview.payload_hash


def test_non_substack_preview_fails_closed():
    preview = previews.build_x_short_post_preview(
        source_content_id="source_content_test",
        source_draft_id="source_draft_test",
        body="Process note with citations.",
        markdown_body="Process note with citations.",
        citation_refs=("source:test",),
        limitation_notes=("local preview only",),
    )

    with pytest.raises(substack.NonSubstackPreviewError):
        substack.build_substack_newsletter_issue_from_preview(preview, seo_metadata=SEO)


def test_export_hash_is_deterministic():
    first = build_issue()
    second = build_issue()

    assert first.export_hash == second.export_hash
    assert first.issue_id == second.issue_id


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", "Changed title"),
        ("body_sections", ("Changed body section.",)),
        ("citation_refs", ("source:changed",)),
        ("limitation_notes", ("changed limitation",)),
        ("seo_metadata", {**SEO, "seo_title": "Changed SEO title"}),
    ],
)
def test_content_and_seo_changes_alter_export_hash(field, value):
    baseline = build_issue()
    changed = build_issue(**{field: value})

    assert changed.export_hash != baseline.export_hash


def test_destination_change_alters_export_hash():
    baseline = build_issue(newsletter_preview(destination_binding_id="destination_a"))
    changed = build_issue(newsletter_preview(destination_binding_id="destination_b"))

    assert changed.export_hash != baseline.export_hash


def test_markdown_includes_required_sections():
    issue = build_issue()

    assert "# Source trust before distribution" in issue.markdown_body
    assert "## A process note" in issue.markdown_body
    assert "**Hook:** Manual export stays controlled." in issue.markdown_body
    assert "Citations and limitations remain visible." in issue.markdown_body
    assert "source:test" in issue.markdown_body
    assert "local manual export only" in issue.markdown_body
    assert substack.NO_SIGNAL_DISCLAIMER in issue.markdown_body


def test_missing_citations_blocks_when_claims_exist():
    preview = newsletter_preview(citation_refs=())
    issue = build_issue(preview, citation_refs=(), source_claims_exist=True)
    package = build_package(issue)
    validation = substack.validate_substack_export_package(issue, package, source_claims_exist=True)

    assert issue.manual_export_status == substack.BLOCKED
    assert "missing_citation_refs_for_claimed_facts" in validation.blocked_reasons
    assert validation.validation_status == substack.BLOCKED


def test_missing_limitations_blocks_grounded_content():
    preview = newsletter_preview(limitation_notes=())
    issue = build_issue(preview, limitation_notes=())
    package = build_package(issue)
    validation = substack.validate_substack_export_package(issue, package, source_claims_exist=True)

    assert "missing_limitation_notes_for_grounded_or_artifact_content" in issue.blocked_reasons
    assert validation.validation_status == substack.BLOCKED


def test_missing_seo_metadata_blocks_export():
    issue = build_issue(seo_metadata={})
    package = build_package(issue)
    validation = substack.validate_substack_export_package(issue, package, source_claims_exist=True)

    assert "missing_seo_metadata" in validation.blocked_reasons
    assert validation.seo_metadata_present is False
    assert validation.validation_status == substack.BLOCKED


def test_missing_manual_checklist_blocks_export():
    issue = build_issue()
    package = build_package(issue, manual_publish_checklist=("copy markdown manually",))
    validation = substack.validate_substack_export_package(issue, package, source_claims_exist=True)

    assert "missing_manual_publish_checklist" in validation.blocked_reasons
    assert validation.manual_checklist_present is False
    assert validation.validation_status == substack.BLOCKED


def test_forbidden_advice_language_blocks_export():
    issue = build_issue(body_sections=("This is a buy signal.",))
    package = build_package(issue)
    validation = substack.validate_substack_export_package(issue, package, source_claims_exist=True)

    assert "forbidden_signal_or_advice_language" in validation.blocked_reasons
    assert validation.no_signal_pass is False


def test_export_package_preserves_source_payload_hash():
    preview = newsletter_preview()
    issue = build_issue(preview)
    package = build_package(issue)
    validation = substack.validate_substack_export_package(issue, package, source_preview=preview, source_claims_exist=True)

    assert package.source_payload_hash == preview.payload_hash
    assert validation.source_preview_hash_match is True


def test_manual_export_status_never_uses_live_or_system_publish_labels():
    issue = build_issue()

    assert issue.manual_export_status not in substack.FORBIDDEN_STATUS_VALUES
    assert issue.manual_export_status in {substack.READY_FOR_MANUAL_REVIEW, substack.BLOCKED}


def test_no_live_flags_are_forced_false_on_issue_and_package():
    issue = build_issue()
    package = build_package(issue)

    for flag in substack.SAFETY_FALSE_FLAGS:
        assert issue.safety_flags[flag] is False
        assert package.safety_flags[flag] is False


def test_substack_api_session_browser_flags_are_false():
    issue = build_issue()
    package = build_package(issue)

    for flag in ("substack_api_called", "browser_session_used", "session_cookie_used"):
        assert issue.safety_flags[flag] is False
        assert package.safety_flags[flag] is False


def test_validation_passes_for_manual_review_but_stays_no_live():
    issue = build_issue()
    package = build_package(issue)
    validation = substack.validate_substack_export_package(issue, package, source_claims_exist=True)

    assert validation.validation_status == substack.READY_FOR_MANUAL_REVIEW
    assert validation.no_live_defaults_pass is True
    assert issue.dispatch_ready is False
    assert issue.public_postable is False


def test_markdown_hash_changes_when_markdown_changes():
    issue = build_issue()
    package = build_package(issue)
    changed_issue = replace(issue, markdown_body=issue.markdown_body + "\nExtra local note.\n")
    changed_package = build_package(changed_issue)

    assert package.markdown_hash != changed_package.markdown_hash


def test_contract_packet_contains_artifact_scope_and_next_batch():
    packet = substack.build_contract_packet()

    assert packet["artifact_scope"] == "docs/automation/0174U3_only"
    assert packet["next_heavy_batch_recommendation"] == substack.NEXT_HEAVY_BATCH
    assert packet["sample_validation"]["validation_status"] == substack.READY_FOR_MANUAL_REVIEW


def test_artifact_writer_touches_only_0174u3(tmp_path):
    repo_root = tmp_path / "repo"
    packet = substack.write_artifacts(repo_root)
    out = repo_root / "docs" / "automation" / "0174U3"

    assert (out / substack.PACKET_FILENAME).exists()
    assert (out / substack.RUNBOOK_FILENAME).exists()
    assert packet["artifact_scope"] == "docs/automation/0174U3_only"
    with pytest.raises(ValueError):
        substack.write_artifacts(repo_root, repo_root / "docs" / "automation" / "0174U2")
