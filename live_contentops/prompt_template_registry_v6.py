"""V6 Prompt Template Registry.

Registers template families and validation structures for LLM guidance.
"""
from __future__ import annotations

PROMPT_FAMILIES = [
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

TEMPLATES = {
    "idea_classifier": "Classify the following content idea: {idea_text}",
    "research_question_generator": "Generate research questions for topic: {topic}",
    "research_brief_writer": "Write a research brief for: {topic} given source refs: {source_refs}",
    "canonical_substack_writer": "Draft a canonical Substack article for: {title} with grounding: {grounding}",
    "seo_optimizer": "Optimize SEO for canonical article: {article_body}",
    "discord_drop_writer": "Create a Discord community drop from canonical draft: {article_body}",
    "telegram_post_writer": "Create a Telegram post variant: {article_body}",
    "platform_variant_writer": "Generate native variants for {platform} from canonical draft: {article_body}",
    "media_concept_writer": "Generate media asset concept guidelines for: {topic}",
    "draft_inspector_explainer": "Inspect and explain draft quality: {draft_text}",
    "community_signal_summarizer": "Summarize community signals and comments: {comments}",
    "manual_fallback_writer": "Generate manual fallback steps for: {context}"
}


def get_prompt_template(family: str) -> str:
    """Retrieves prompt template string for the given family."""
    if family not in PROMPT_FAMILIES:
        raise KeyError(f"Prompt family {family} is not registered in V6 registry.")
    return TEMPLATES.get(family, "General prompt for {family}")
