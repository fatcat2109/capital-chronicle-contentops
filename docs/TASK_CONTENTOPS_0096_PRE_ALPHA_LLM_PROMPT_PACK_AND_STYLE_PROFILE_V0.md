# TASK_CONTENTOPS_0096_PRE_ALPHA_LLM_PROMPT_PACK_AND_STYLE_PROFILE_V0

## Scope

Local-only, deterministic, design-only. Builds the pre-alpha LLM prompt pack and
style profile layer on top of the 0095 content engine. No LLM/provider/search/
network/credential/platform access. No posting. No `.env` reads.

## Baseline

- Starting accepted HEAD: `4330356` on `master`.
- 0095 accepted: pre-alpha content engine + editorial packet.
- Actual 0095 docs inspected from disk before referencing (underscore
  convention): `docs/PRE_ALPHA_CONTENT_ENGINE_AFTER_0095.md` and
  `docs/TASK_CONTENTOPS_0096...` chain confirmed via git/ls.

## Files created

- `schemas/pre_alpha_prompt_pack.schema.json`
- `schemas/pre_alpha_style_profile.schema.json`
- `schemas/pre_alpha_editorial_rubric.schema.json`
- `live_contentops/pre_alpha_prompt_pack.py`
- `fixtures/pre_alpha_prompt_pack/valid_capital_chronicle_process_prompt_pack.json`
- `fixtures/pre_alpha_prompt_pack/valid_macro_education_prompt_pack.json`
- `fixtures/pre_alpha_prompt_pack/valid_build_in_public_style_profile.json`
- `fixtures/pre_alpha_prompt_pack/valid_pre_alpha_editorial_rubric.json`
- `fixtures/pre_alpha_prompt_pack/invalid_signal_service_framing.json`
- `fixtures/pre_alpha_prompt_pack/invalid_fake_alpha_prompt.json`
- `fixtures/pre_alpha_prompt_pack/invalid_public_postable_default.json`
- `tests/test_pre_alpha_prompt_pack.py`
- `docs/PRE_ALPHA_PROMPT_PACK_AND_STYLE_PROFILE_AFTER_0096.md`
- `docs/TASK_CONTENTOPS_0096_PRE_ALPHA_LLM_PROMPT_PACK_AND_STYLE_PROFILE_V0.md`

## Files changed

- `live_contentops/cli.py`: added `pre-alpha-prompt-pack-summary` handler +
  dispatch entry. No external capability introduced.

## Validator behavior

- Valid process + macro-education prompt packs pass.
- Prompt pack output contract aligns with the 0095 draft/packet shape.
- Signal-service framing blocked (`prompt_forbidden_framing`).
- Fake alpha prompting blocked (`prompt_implies_alpha_output`,
  `prompt_invents_data_or_claims`).
- `public_postable_default = true` blocked.
- Style profile requires `no_signal_service_framing` and `no_financial_advice`
  true; unknown platform families blocked.
- Editorial rubric requires manual review and
  `public_postable_until_manual_approval = false`.

## What remains disabled

LLM/provider/API/network/web/search calls; Telegram/API/live post; platform
posting; platform credentials; env/`.env` reads; fake Capital Chronicle alpha
output; public-postable content; financial advice / buy / sell / hold / signal /
execution language; scheduler / replies / DMs / scraping / metrics.

## Exact next task

`TASK_CONTENTOPS_0097_PRE_ALPHA_DRAFT_RENDERER_AND_REVIEW_QUEUE_INTEGRATION_V0`
