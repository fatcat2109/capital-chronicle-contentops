# ContentOps LLM Quota / Retry Discipline Addendum (After 0174AY)

**Task:** `TASK_CONTENTOPS_0174AY_LLM_QUOTA_RETRY_DISCIPLINE_AND_PROVIDER_GATEWAY_MASTER_PLAN_ADDENDUM_V0`
**Status:** BINDING ADDENDUM to the current product strategy authority
**Authority parent:** `docs/CAPITAL_CHRONICLE_CONTENTOPS_RECONCILED_FINAL_PRODUCT_MASTER_PLAN_AFTER_0174AO.md`
**Roadmap parent:** `docs/CONTENTOPS_FINAL_PRODUCT_ROADMAP_AFTER_0174AO.md`
**Branch:** master · local-only · supervised · fail-closed
**Scope of this task:** planning/contract hardening + a local schema/validator/test
package. No provider call, no network, no credentials, no UI.

---

## 0. Why this addendum exists

The reconciled master plan (4.3) defines a bounded LLM editorial writer and a
deterministic content safety compiler (4.4). It does **not** yet codify *how many
times* the system may call a provider, or what happens when a draft fails local
validation. Before any real provider adapter is built, that gap must be closed.

This addendum codifies a first-class **LLM quota / retry discipline** so future
implementation cannot accidentally adopt an expensive, quality-degrading rewrite loop.

---

## 1. The forbidden pattern

The system must never use this pattern:

```text
LLM draft -> local validator fails -> LLM full rewrite -> validator fails ->
LLM full rewrite -> validator fails -> ... (loop)
```

Why it is forbidden:

- It burns provider quota with no bounded stop.
- Repeated full rewrites drift toward generic, "AI-ish" prose.
- It increases hallucination risk on each pass.
- It can silently drop citations, limitations, source nuance, and non-signal framing.
- It destroys audit lineage: there is no single canonical draft to review.

This is a direct extension of the Non-Negotiable Boundaries (master plan 8): the
system must never turn "missing quality" into "infinite spend."

---

## 2. The required architecture

1. **Validate brief/input locally** before any provider call.
2. **Compile a strong deterministic prompt pack** from the `ContentIntentPacket`.
3. **Run max 1 canonical generation.**
4. **Validate the canonical draft locally** (deterministic validator is primary).
5. If failure is **minor/localized**, allow **max 1 targeted repair**.
6. **Targeted repair patches only the failing section** and must preserve citations,
   limitations, source refs, claim meaning, and non-signal framing.
7. If still failing, mark **REVIEW_REQUIRED** or **BLOCKED** and route to Jim.
8. **Never generate platform variants** until the canonical draft is PASS.
9. **LLM critique is optional, budgeted, and never the primary safety validator.**
10. **Cache** by brief hash + prompt version + source packet hash + model config.
11. **Track estimated/actual spend** per packet, per stage, and per provider.
12. **No hidden auto-regeneration. No infinite retry loop. No full rewrite** unless
    explicitly approved by the operator.

```text
brief -> [local validate] -> prompt pack -> [1 canonical generation]
      -> [local validate] --PASS--> platform variants -> approval pipeline
                          --minor--> [1 targeted repair] -> [local validate]
                                        --PASS--> platform variants
                                        --fail--> REVIEW_REQUIRED / BLOCKED -> Jim
                          --major--> BLOCKED -> Jim
```

---

## 3. Policy object: `SCDLLMQuotaRetryPolicy`

The discipline is enforced by a deterministic local policy object and validator
(`live_contentops/scd_llm_quota_retry_policy.py`, schema
`schemas/scd_llm_quota_retry_policy.schema.json`). Core fields:

| Field | Required value (this task) |
|---|---|
| `provider_api_allowed` / `network_allowed` / `credentials_required` | false |
| `max_generation_attempts` | 1 |
| `max_targeted_repair_attempts` | <= 1 |
| `max_full_rewrite_attempts` | 0 (unless explicit operator override; never PASS) |
| `allow_infinite_retry` / `allow_full_rewrite_loop` | false |
| `pre_llm_validation_required` / `post_llm_validation_required` | true |
| `deterministic_validator_primary` | true |
| `llm_critique_optional_only` | true |
| `platform_variants_require_canonical_pass` | true |
| `targeted_repair_only_for_minor_failures` | true |
| `preserve_citations` / `_limitations` / `_source_refs` / `_claim_meaning` / `_non_signal_framing` | true |
| `review_required_after_second_failure` | true |
| `block_after_major_safety_failure` | true |
| `cache_key_required` (+ `cache_key_components`) | true |
| `spend_tracking_required` (+ `spend_fields_required`) | true |
| `model_output_never_authority` / `human_review_required_on_failure` | true |
| `no_public_ready_claim` / `no_live_dispatch` | true |

`cache_key_components`: brief_hash, prompt_version, source_packet_hash, model_config.
`spend_fields_required`: estimated_tokens, actual_tokens, estimated_cost, actual_cost,
provider_name, model_name.

---

## 4. Validator behavior (fail-closed)

- Bounded generation/repair violations, retry-loop flags, provider/network/credential
  flags, missing platform-variant gating, missing spend fields, and any
  "generate/retry until pass", "auto-regenerate", "unbounded", or "rewrite entire draft
  repeatedly" prose all resolve to **BLOCKED**.
- Missing/incomplete `cache_key_components` resolves to **UNKNOWN** (lineage unproven).
- `llm_critique_enabled` without a budget resolves to **REVIEW_REQUIRED**.
- `max_full_rewrite_attempts > 0` is only tolerated with an explicit operator override,
  and even then the policy can never be **PASS** (downgraded to REVIEW_REQUIRED).
- Precedence is the standard SCD order: **BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS.**

---

## 5. Relationship to the provider gateway (future)

This policy is a **precondition** for the future provider/LLM live gate, not the gate
itself. A future `provider gateway` task must:

- load and validate this policy to **PASS** before any adapter is constructed;
- enforce the bounded attempt counts at call sites (not as advisory comments);
- record per-call spend against `spend_fields_required`;
- treat the deterministic content safety compiler (master plan 4.4) as the primary
  validator and any LLM critique as optional/budgeted only.

No provider key, network call, or credential read is introduced by this task. Provider
integration remains behind its own dedicated live/provider gate.

---

## 6. Boundaries (unchanged, reaffirmed)

Local-only · deterministic · fail-closed · no provider/LLM API · no network · no
credential/env reads · no platform API · no UI/browser/screenshots · no live dispatch ·
no scheduler · no auto-posting · no public-ready content · no financial advice or signal
framing. The system is powerful because it is controlled, not because it is autonomous.
