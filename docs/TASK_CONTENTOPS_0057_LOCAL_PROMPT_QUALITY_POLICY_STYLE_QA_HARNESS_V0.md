# TASK_CONTENTOPS_0057_LOCAL_PROMPT_QUALITY_POLICY_STYLE_QA_HARNESS_V0

## Objective
Built a local-only prompt quality, policy scoring, and platform style QA harness v0 for cc-live-contentops provider-output simulation. 

## Capabilities Implemented
- **Deterministic QA Evaluator Module**: `live_contentops/editorial_quality.py`.
- **Scoring Dimensions**: hook_strength, clarity, audience_fit, platform_fit, specificity, repetition_risk, wedge_alignment, limitation_visibility, source_discipline, safety_risk, cta_quality.
- **Platform Rubrics Defined**: linkedin, x, threads, substack.
- **Audience Modes Defined**: macro_professional, quant_systematic_trader, builder_ai_tooling, general_finance_reader, product_evaluator.
- **No-Public-Postable Flagging**: Flags synthetic demo inputs, unsafe claims, and source discipline failures as strictly unpublishable.
- **Local Fixtures**: Created `unsafe_financial_advice.json`, `safe_good_linkedin.json`, and `synthetic_demo_threads.json`.

## Testing & Validation
- Added `test_editorial_quality.py` which passes correctly.
- Tests prove that missing limitations lower the score, synthetic/demo fixtures are flagged, and safety boundaries trigger `not_public_postable_reason`.

## Hard Boundaries Respected
- **NO Network / NO API**.
- Evaluator processes static JSON payloads completely offline.
- Output is entirely diagnostic/advisory and strictly labeled against publishing where necessary.
- NO credential structures altered. No core repositories mutated.

## Next Phase
The environment successfully completed Option A and generated its scoring harness. The next task pointer is set exactly to:
`TASK_CONTENTOPS_0058_LOCAL_EDITORIAL_VARIANT_PREVIEW_AND_NO_PUBLIC_POST_REPORT_V0`
