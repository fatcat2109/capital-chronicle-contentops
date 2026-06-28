"""Test V6 Canonical Article Studio Placeholder Binding Validator."""
from __future__ import annotations

from live_contentops import canonical_article_studio_placeholder_binding_packet_v6 as packet_builder
from live_contentops import canonical_article_studio_placeholder_binding_review_v6 as review_builder
from live_contentops import canonical_article_studio_placeholder_binding_v6 as coordinator
from live_contentops import canonical_article_studio_placeholder_binding_validator_v6 as validator


def test_validator_passes_on_clean_simulated_state():
    binding_packet = packet_builder.make_canonical_article_studio_placeholder_binding_packet()
    slot_binding_map = coordinator.make_slot_binding_map()
    binding_review = review_builder.make_canonical_article_studio_placeholder_binding_review()
    placeholder_bound_shell_instance = coordinator.make_placeholder_bound_shell_instance(slot_binding_map)

    report, blockers = validator.validate_canonical_article_studio_placeholder_binding(
        binding_packet, slot_binding_map, binding_review, placeholder_bound_shell_instance
    )

    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert len(blockers) == 9
    assert "real_source_pack_not_approved" in blockers
    assert "runtime_operator_approval_missing" in blockers
    assert "placeholder_values_not_materialized" in blockers
    assert "article_copy_generation_blocked" in blockers
    assert "editor_review_required" in blockers
    assert "jim_review_required" in blockers
    assert "publication_blocked" in blockers
    assert "dispatch_blocked" in blockers
    assert "human_review_required" in blockers


def test_validator_fails_on_materialized_slots():
    binding_packet = packet_builder.make_canonical_article_studio_placeholder_binding_packet()
    binding_packet["slot_values_materialized"] = True
    slot_binding_map = coordinator.make_slot_binding_map()
    binding_review = review_builder.make_canonical_article_studio_placeholder_binding_review()
    placeholder_bound_shell_instance = coordinator.make_placeholder_bound_shell_instance(slot_binding_map)

    report, blockers = validator.validate_canonical_article_studio_placeholder_binding(
        binding_packet, slot_binding_map, binding_review, placeholder_bound_shell_instance
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "article_copy_generation_blocked" in blockers


def test_validator_fails_on_non_null_placeholder_value():
    binding_packet = packet_builder.make_canonical_article_studio_placeholder_binding_packet()
    slot_binding_map = coordinator.make_slot_binding_map()
    slot_binding_map[0]["placeholder_value"] = "Some actual title"
    binding_review = review_builder.make_canonical_article_studio_placeholder_binding_review()
    placeholder_bound_shell_instance = coordinator.make_placeholder_bound_shell_instance(slot_binding_map)

    report, blockers = validator.validate_canonical_article_studio_placeholder_binding(
        binding_packet, slot_binding_map, binding_review, placeholder_bound_shell_instance
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "non_null_placeholder_value_detected" in blockers


def test_validator_fails_on_source_name_leak():
    binding_packet = packet_builder.make_canonical_article_studio_placeholder_binding_packet()
    slot_binding_map = coordinator.make_slot_binding_map()
    binding_review = review_builder.make_canonical_article_studio_placeholder_binding_review()
    placeholder_bound_shell_instance = coordinator.make_placeholder_bound_shell_instance(slot_binding_map)
    slot_binding_map[0]["placeholder_label"] = "US Treasury placeholder"

    report, blockers = validator.validate_canonical_article_studio_placeholder_binding(
        binding_packet, slot_binding_map, binding_review, placeholder_bound_shell_instance
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_name_leak_detected" in blockers


def test_no_forbidden_imports_in_validator():
    import live_contentops.canonical_article_studio_placeholder_binding_validator_v6 as target_module
    attrs = dir(target_module)
    forbidden = ["urlopen", "requests", "httpx", "getenv", "environ", "openai", "anthropic", "google"]
    for f in forbidden:
        assert f not in attrs
