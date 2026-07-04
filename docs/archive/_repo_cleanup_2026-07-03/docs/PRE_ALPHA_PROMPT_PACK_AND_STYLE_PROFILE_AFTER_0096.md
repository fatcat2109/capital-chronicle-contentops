# Pre-Alpha LLM Prompt Pack and Style Profile (After 0096)

Local-only, deterministic, design-only. This layer defines prompt packs, style
profiles, and an editorial rubric that may LATER guide LLM-assisted drafting for
the pre-alpha content engine (0095). It performs no LLM/provider/search/network/
credential/platform access. It posts nothing. It reads no `.env`.

## What this adds

- `schemas/pre_alpha_prompt_pack.schema.json`
- `schemas/pre_alpha_style_profile.schema.json`
- `schemas/pre_alpha_editorial_rubric.schema.json`
- `live_contentops/pre_alpha_prompt_pack.py` (deterministic validators + summary)
- Safe/unsafe fixtures under `fixtures/pre_alpha_prompt_pack/`
- `tests/test_pre_alpha_prompt_pack.py`
- CLI: `python -m live_contentops.cli pre-alpha-prompt-pack-summary`

## Prompt pack contract

A prompt pack defines the static instructions that would later be handed to an
LLM. It declares `intended_content_types`, `allowed_source_types`,
`system_instructions`, `user_prompt_template`, `required_context_fields`,
`forbidden_claims`, `required_disclaimers`, a `style_profile_id`, an
`editorial_rubric_id`, and an `output_contract`.

Safety flags are pinned:

- `requires_manual_review` must be `true`
- `provider_call_allowed_now` must be `false`
- `public_postable_default` must be `false`
- `live_execution_allowed_now` must be `false`

### Output contract alignment with 0095

The `output_contract.produces` value must be `draft_candidate` or
`editorial_packet_input`, `platform_families` must be a subset of
`x / linkedin / threads / newsletter / generic`, `public_postable` must be
`false`, and `requires_manual_review` must be `true`. This keeps prompt-pack
output compatible with the 0095 draft candidate / editorial packet shape without
ever producing public-postable copy.

## Prompt template guardrails

The validator scans `system_instructions` and `user_prompt_template` and blocks:

- forbidden trade/advice language (`prompt_forbidden_language`)
- text implying Capital Chronicle alpha output exists (`prompt_implies_alpha_output`)
- positioning framing such as Bloomberg replacement / trading bot / signal
  service / execution engine / guaranteed forecast (`prompt_forbidden_framing`)
- instructions that tell the model to invent / fabricate / make up data, prices,
  forecasts, source IDs, or market claims (`prompt_invents_data_or_claims`)

The `forbidden_claims` list is intentionally excluded from the language scan,
because it is a guardrail enumeration describing what NOT to do. Authors should
keep "do not X" phrasing in `forbidden_claims`, not in the instruction fields, to
avoid tripping the deterministic scanner on negated trigger words.

## Style profile contract

A style profile defines audience, tone, allowed/forbidden voice, hook/body/CTA
patterns, and per-platform-family adaptations. `no_signal_service_framing` and
`no_financial_advice` must both be `true`. Unknown platform families are
rejected. Author-facing voice text is scanned for forbidden language and alpha
implication; the `forbidden_voice` guardrail list is excluded from the scan.

## Editorial rubric contract

The rubric encodes the deterministic review checks a draft must satisfy before
manual approval: content-type classification, source artifact IDs or a
general/process marker, limitations + freshness + educational-only for market
notes, rejection of fake alpha and unverified numeric claims, rejection of
financial-advice/signal language, mandatory manual review, and
`public_postable_until_manual_approval = false`.

## Posture

This task does not call any model, fetch anything, or post anything. It validates
static local design artifacts only. All output remains manual-review-required and
not public postable. Live execution and provider calls remain disabled.
