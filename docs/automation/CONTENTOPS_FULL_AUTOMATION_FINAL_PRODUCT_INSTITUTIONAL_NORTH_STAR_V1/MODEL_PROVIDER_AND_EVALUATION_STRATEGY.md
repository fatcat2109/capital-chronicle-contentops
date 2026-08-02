# Capital Chronicle ContentOps — Model Provider and Evaluation Strategy V1

## 0. Operator decision

The current economic default is 9router with a Gemini 3.1 Pro-class model because Jim has available credit. This is an operating-cost decision, not a permanent architecture decision and not a quality assumption.

The final product must be able to replace the model without changing:

- evidence packets;
- claim permission;
- DQR/freshness decisions;
- approval envelopes;
- outbox records;
- platform adapter contracts;
- audit evidence;
- public-object identity.

The current repository does not yet meet this standard. The article engine currently contains an implicit 9router default for `vx/gemini-3.5-flash` and separately attempts `vx/gemini-3.1-pro-preview` as a later model option. This conflicts with the operator-intended default and relies on provider-specific strings inside production logic.

The exact 9router model ID must be verified during local implementation through nonsecret configuration/provider capability metadata. Do not assume that `Gemini 3.1 Pro`, a preview alias, or any remembered provider string is still the current exact ID.

## 1. Model authority boundary

A model may:

- propose story framing;
- summarize approved evidence;
- draft article prose;
- explain uncertainty;
- generate platform-native variants;
- propose visual concepts;
- critique readability and structure;
- cluster redacted feedback;
- propose content ideas and experiments.

A model may not:

- create or upgrade source authority;
- invent claim IDs, numeric truth, citations, known-at times or revision state;
- clear DQR or source-health blockers;
- decide public-use permission;
- certify its own output as factually valid;
- approve a package;
- select a destination/account binding;
- authorize or execute a public write;
- override deterministic blockers;
- mutate a previously approved payload;
- learn directly into production policy without review.

Every model output is a candidate artifact. Deterministic validators and independent review determine whether it can progress.

## 2. Provider/model registry

Create one versioned registry, for example:

`docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/model_provider_registry_v1.json`

Each row must include:

```json
{
  "provider_id": "9router",
  "model_id": "EXACT_VERIFIED_PROVIDER_MODEL_ID",
  "display_name": "Gemini 3.1 Pro",
  "model_family": "gemini",
  "model_tier": "pro",
  "lifecycle_state": "current_default",
  "capability_classes": [
    "long_context_editorial",
    "structured_json",
    "critique",
    "platform_adaptation"
  ],
  "allowed_roles": [
    "assignment_judgment",
    "reporter_writer",
    "copy_editor",
    "platform_editor",
    "adversarial_reviewer",
    "feedback_summarizer"
  ],
  "context_limit_tokens": null,
  "max_output_tokens": null,
  "schema_mode": "provider_specific_or_prompt_validated",
  "temperature_policy": "role_specific",
  "timeout_seconds": null,
  "attempt_budget": null,
  "fallback_policy_id": "editorial_default_v1",
  "cost_class": "credit_subsidized_current",
  "evaluation_corpus_version": "contentops_model_eval_v1",
  "evaluation_status": "PENDING_LOCAL_VERIFICATION",
  "last_verified_at_utc": null,
  "provider_alias_verified": false,
  "publication_authority": false
}
```

Unknown provider capabilities remain null or unverified. Do not fill them from memory.

## 3. Role routing

Use role classes rather than one model call for everything.

### 3.1 Deterministic-only roles

No model call:

- evidence transport and byte verification;
- claim permission;
- DQR and source-health gates;
- point-in-time authority;
- freshness calculation;
- numeric transformations where deterministic code exists;
- payload hashing;
- approval validity;
- destination/account binding;
- idempotency;
- outbox state;
- dispatch and readback classification;
- SLO calculations.

### 3.2 High-reasoning semantic roles

Default to Gemini 3.1 Pro-class current model:

- assignment framing among already eligible candidates;
- evidence plan;
- canonical article drafting;
- causal/mechanism explanation;
- deep quantitative prose review;
- independent adversarial final review;
- complex feedback synthesis.

### 3.3 Lower-cost bounded roles

May use a cheaper verified model only after evaluation:

- title variant generation;
- format-preserving platform adaptation;
- alt-text draft;
- metadata cleanup;
- classification of already redacted feedback;
- non-authoritative copy suggestions.

Do not route a role to a weaker model solely because it is cheaper. The role/model pairing requires evaluation evidence.

## 4. Invocation envelope

Every model invocation must persist a redacted envelope:

- invocation ID;
- work item/story/artifact version;
- provider and exact model ID;
- model registry version;
- role;
- prompt template ID and hash;
- policy/evidence input hashes;
- schema version;
- parameters relevant to reproducibility;
- start/end time and latency;
- input/output token counts where available;
- provider request/result status;
- structured validation result;
- quality review result;
- fallback/recovery status;
- output artifact ID/hash;
- no-authority flags.

Never persist raw API keys, authorization headers, hidden chain-of-thought, provider session secrets or unrelated prompt context.

## 5. Prompt architecture

### 5.1 Prompt contract

Prompts must be versioned and composed from:

1. stable role instruction;
2. exact allowed evidence/claim context;
3. article/platform capability policy;
4. explicit forbidden inferences;
5. requested schema;
6. quality rubric;
7. current task context;
8. output-only instruction.

Prompt text must not contain live credential material, raw environment dumps, browser session data or unbounded repository contents.

### 5.2 Evidence minimization

Supply only the claims, documents, limitations and judgment context required for the role. Do not expose every repository packet to the writer. Excess context increases cross-story leakage and makes failure diagnosis harder.

### 5.3 Structured outputs

Each semantic role returns a versioned object. Required controls:

- strict JSON/schema validation;
- unknown-field policy;
- maximum field lengths;
- exact claim-ID allowlist;
- citation reference validation;
- no model-produced authority flags accepted;
- explicit abstention and uncertainty fields;
- deterministic canonicalization before hashing.

Text extraction from prose-wrapped JSON may be used only as a bounded compatibility recovery and must be recorded as a degraded attempt.

## 6. Attempt and fallback policy

### 6.1 Attempt classes

- `PRIMARY_MODEL_ATTEMPT`
- `SAME_MODEL_REPAIR_ATTEMPT`
- `ALTERNATE_MODEL_ATTEMPT`
- `DETERMINISTIC_RECOVERY_CANDIDATE`
- `ABSTAIN_BLOCKED`

### 6.2 Retry eligibility

Retry may occur for:

- transport error before response;
- timeout with no response;
- rate limit according to bounded backoff;
- malformed structured output;
- schema validation failure;
- bounded quality failure where the validator can provide exact repair feedback.

Retry must not occur simply because the model reached a truthful abstention or deterministic evidence gate blocked the story.

### 6.3 Attempt budget

Default per semantic artifact:

- one primary attempt;
- at most one schema/quality repair attempt;
- optional one alternate-model attempt only where registry policy permits it.

The budget is configurable by role and provider. Every attempt remains in the denominator for quality/SLO reporting.

### 6.4 Deterministic recovery

A deterministic recovery template may create a local draft candidate when the provider is unavailable. It must declare:

- recovery provenance;
- no model call or exact model used;
- reduced quality class;
- missing semantic capabilities;
- mandatory operator/editor review;
- no automatic publication eligibility.

A deterministic recovery article must not silently inherit the same quality label as a successfully reviewed model-produced article.

## 7. Provider failure taxonomy

Required classifications:

- `PROVIDER_UNAVAILABLE`
- `AUTHENTICATION_OR_CAPABILITY_BLOCKED`
- `RATE_LIMITED`
- `TIMEOUT_NO_RESPONSE`
- `TRANSPORT_ERROR_PRE_RESPONSE`
- `MALFORMED_RESPONSE`
- `STRUCTURED_SCHEMA_INVALID`
- `CONTEXT_LIMIT_EXCEEDED`
- `OUTPUT_TRUNCATED`
- `MODEL_ALIAS_OR_SUBSTITUTION_UNVERIFIED`
- `SAFETY_REFUSAL`
- `QUALITY_GATE_FAILED`
- `UNSUPPORTED_CLAIM_ADDITION`
- `CROSS_STORY_LEAKAGE`
- `PROMPT_INJECTION_SUSPECTED`
- `UNKNOWN_PROVIDER_OUTCOME`

Each class maps to:

- retry eligibility;
- backoff;
- fallback eligibility;
- incident severity;
- operator visibility;
- artifact disposition.

## 8. Evaluation corpus

Create a committed, redacted, authority-safe corpus from exact historical inputs and expected defects.

### 8.1 Required cases

1. Accepted Treasury v1.0 canonical article and variants.
2. July 11 oil RC with known headline, process-language, metric-label, partial-period and visual-diversity defects.
3. FOMC/policy decision.
4. Scheduled macro data release.
5. Corporate filing.
6. Regulatory or sanctions document.
7. Physical-event report.
8. Geopolitical/supply-chain event.
9. Nonnumeric source-trust explainer.
10. Build-in-public/product update.
11. Community Q&A.
12. Stale story that must not use breaking framing.
13. Insufficient-evidence case requiring abstention.
14. Conflicting/corrected source case.
15. Prompt-injection or malicious source text case.

### 8.2 Corpus separation

Use:

- development set;
- regression set;
- holdout promotion set.

Do not repeatedly tune against the holdout set. New production incidents become regression cases after operator review.

## 9. Evaluation dimensions

### 9.1 Hard-fail dimensions

Any failure blocks model promotion:

- unauthorized claim addition;
- numeric hallucination;
- citation fabrication;
- evidence-time leakage;
- advice/signal language;
- process/internal language in public copy;
- wrong article mode;
- material headline overstatement;
- deterministic blocker override;
- schema invalidity after budget;
- public authority claim by the model.

### 9.2 Scored dimensions

- news peg clarity;
- why-now explanation;
- source-calibrated language;
- mechanism quality;
- causal restraint;
- quantitative wording;
- uncertainty and limitation handling;
- information density;
- prose coherence;
- originality without unsupported inference;
- visual plan quality;
- platform-native adaptation;
- headline/SEO packaging;
- adversarial-review usefulness;
- operator revision burden.

### 9.3 Operational dimensions

- structured-output validity;
- latency;
- token usage;
- cost;
- retry rate;
- fallback rate;
- context-limit behavior;
- provider stability.

## 10. Promotion policy

A new model or model alias can become default only when:

1. exact provider/model ID is verified;
2. registry metadata is updated;
3. hard-fail count is zero on the promotion holdout;
4. scored quality is noninferior to current default on critical roles;
5. no material increase in operator revision burden;
6. latency/cost tradeoff is documented;
7. deterministic replay and all nonmodel contracts remain unchanged;
8. operator approves the routing-policy commit;
9. shadow canary passes before live use.

A provider-side alias change without a committed routing update must produce `MODEL_ALIAS_OR_SUBSTITUTION_UNVERIFIED`, not silent acceptance.

## 11. Current 9router/Gemini 3.1 Pro implementation decision

The implementation wave must:

- remove the implicit `vx/gemini-3.5-flash` production default from article logic;
- resolve the exact current Gemini 3.1 Pro model ID from operator-approved nonsecret configuration or provider model metadata;
- place it in the model registry;
- use one provider gateway for all semantic roles;
- keep model ID configurable without environment-value disclosure;
- record every provider attempt and effective model ID when returned;
- prohibit silent downgrade to Flash-class models for high-reasoning roles;
- allow an explicitly evaluated cheaper model only for approved bounded roles;
- keep provider calls separate from platform/public writes.

Until exact ID and evaluation are verified, status is:

`PENDING_LOCAL_MODEL_ID_AND_EVALUATION_VERIFICATION`

## 12. Future model upgrade

When credits end or a materially stronger model becomes economically justified:

```text
candidate model registration
→ offline corpus evaluation
→ operator review of hard failures and representative outputs
→ shadow role routing
→ bounded nonpublic production canary
→ optional limited live cohort under unchanged approval/publication gates
→ routing-policy promotion
```

Do not rewrite the editorial architecture around the new model. A stronger model should reduce revision burden and improve analysis, not become a new authority layer.

## 13. Builder anti-drift rules

- Do not scatter provider calls across modules.
- Do not hardcode exact model IDs inside article/story branches.
- Do not use a model fallback that is not registry-declared.
- Do not hide failed attempts after a later success.
- Do not let a deterministic recovery artifact claim normal quality.
- Do not ask the model to judge source authority or approval validity.
- Do not use provider search output as citation/reuse authority without existing evidence contracts.
- Do not optimize prompts against only one accepted Treasury story.
- Do not claim model superiority from anecdotal output.
- Do not promote a model without holdout evidence and operator approval.
