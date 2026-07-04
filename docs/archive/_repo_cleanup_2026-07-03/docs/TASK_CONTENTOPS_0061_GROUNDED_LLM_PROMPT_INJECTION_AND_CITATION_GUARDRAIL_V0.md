# TASK_CONTENTOPS_0061_GROUNDED_LLM_PROMPT_INJECTION_AND_CITATION_GUARDRAIL_V0

## Objective
Build a local-only grounded LLM prompt injection and citation guardrail v0. This defines how future LLM/editorial/planning prompt packets consume `GroundedResearchContext`, SEO metadata, editorial QA, preview, and selection packets while preserving constraints.

## Capabilities Implemented
- **Prompt Injection**: Created `live_contentops/prompt_injection.py` to generate deterministic local prompt packets. Includes all necessary flags to explicitly deny live provider calls, search calls, and platform actions.
- **Citation Guardrails**: Created `live_contentops/citation_guardrail.py` to enforce that current-event claims have sources, synthetic fixtures are not treated as public authority, and that no prompt section improperly asks the LLM to "invent facts", "invent prices", or other blocked phrases.
- **Tests**: Created full coverage proving the prompt packets are deterministic, securely scoped, and that guardrails properly block source-less current-event claims or invalid capabilities.
- **CLI Summary**: Added `prompt-injection-summary` to check deterministic prompt generation engine status.

## Verification
- Local prompt packet generation succeeded.
- Citation guardrails correctly identify missing sources, stale freshness windows, and invalid LLM prompts.
- Suspicious scan was completely clean, mapping only to explicit testing/guardrail boundaries. No live search APIs or network calls were injected.

## Next Phase
`TASK_CONTENTOPS_0062_LOCAL_GROUNDED_EDITORIAL_PACKET_EXPORT_V0`
