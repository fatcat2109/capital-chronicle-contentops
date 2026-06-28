import pytest
from live_contentops import prompt_template_registry_v6 as prompt_registry

def test_registry_contains_all_required_families():
    required = [
        "idea_classifier",
        "research_question_generator",
        "research_brief_writer",
        "canonical_substack_writer",
        "seo_optimizer",
        "discord_drop_writer",
        "telegram_post_writer",
        "platform_variant_writer",
        "media_concept_writer",
        "draft_inspector_explainer",
        "community_signal_summarizer",
        "manual_fallback_writer"
    ]
    for family in required:
        assert family in prompt_registry.PROMPT_FAMILIES
        assert family in prompt_registry.TEMPLATES
        template = prompt_registry.get_prompt_template(family)
        assert len(template) > 0

def test_unregistered_family_raises_key_error():
    with pytest.raises(KeyError):
        prompt_registry.get_prompt_template("invalid_family")
