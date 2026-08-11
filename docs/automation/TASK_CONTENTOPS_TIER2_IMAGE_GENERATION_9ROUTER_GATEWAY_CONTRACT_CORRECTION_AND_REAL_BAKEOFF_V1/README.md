# Tier-2 image-generation 9Router contract correction

Task: `TASK_CONTENTOPS_TIER2_IMAGE_GENERATION_9ROUTER_GATEWAY_CONTRACT_CORRECTION_AND_REAL_BAKEOFF_V1`

Result: `COMPLETE_CONTRACT_CORRECTED_REAL_BAKEOFF_BLOCKED_PROVIDER_AUTHORIZATION_MISSING`

Review status: `PROVISIONAL_IMAGE_BAKEOFF_AWAITING_JIM_CHATGPT_VISUAL_REVIEW`

## User problem and capability delivered

The rejected Tier2-B run treated one failed guessed OpenAI-compatible image route as model
incapability. This correction establishes one reusable specialist image boundary on the
canonical 9Router credential/configuration surface, preserves requested aliases and wire model
identity, supports sync base64/temporary-URL responses and bounded async polling, hashes and
validates returned bytes, and implements the owner-authorized fallback order:

1. `new/gpt-5.5` -> `gpt-5.5`
2. `new/wan2.7-image-pro` -> `wan2.7-image-pro`
3. `new/qwen-image-2.0` -> `qwen-image-2.0`

No video, typography, motion, music, narration, entity-photo sourcing, browser, platform, or
publication work is included.

## Root cause

The previous request sent the `new/...` chat alias to the localhost gateway's
`POST /v1/images/generations` route. The gateway resolved it through an
`openai-compatible-chat-*` provider and returned HTTP 400: the selected chat provider does not
support image generation. That proves only `PREVIOUS_9ROUTER_IMAGE_CALL_CONTRACT_FAILED`.

Owner-supplied contract correction on 2026-08-11:

```text
base:    https://ai.api-cheap.site/v1
path:    POST /images/generations
schema:  OpenAI-compatible JSON image generation
model:   bare wire ID, without the new/ gateway prefix
```

The existing `NINE_ROUTER_API_KEY` was then used presence-only for one real smoke per target.
All three reached the corrected host/path and returned the same non-retryable HTTP 403 JSON
error class: `permission_denied` / `rate_limit`, key not permitted for the requested operation.
The exact task classification is therefore `PROVIDER_AUTHORIZATION_MISSING`, not model absence,
route absence, or image incapability.

## Real smoke results

| Requested alias | Wire model | Result | HTTP | Generations |
|---|---|---|---:|---:|
| `new/gpt-5.5` | `gpt-5.5` | `PROVIDER_AUTHORIZATION_MISSING` | 403 | 0 |
| `new/wan2.7-image-pro` | `wan2.7-image-pro` | `PROVIDER_AUTHORIZATION_MISSING` | 403 | 0 |
| `new/qwen-image-2.0` | `qwen-image-2.0` | `PROVIDER_AUTHORIZATION_MISSING` | 403 | 0 |

Because no model passed the mandatory smoke gate, the three-archetype bakeoff was not started,
no generation retries were made, and no contact sheet could be truthfully produced. The runtime
review package is at:

`A:\Capital Chronicle\Runtime\ContentOps\tier2-image-gateway-correction`

## Validation

- focused image-boundary + canonical adapter regressions: `35 passed`;
- exact payload/wire-model mapping tested;
- requested alias preservation tested;
- base64, temporary URL/redaction, bounded async polling, timeout, malformed response,
  capability classification, no-secret serialization, hashing, dimensions, content type, and
  fallback order tested;
- real gateway smoke: three bounded calls, zero successful image bytes;
- no full repository suite or CI claim.

## Safety and product direction

- credentials reported only as `PRESENT`/`MISSING`; no values or auth headers serialized;
- hosts used: `localhost:20128` read-only diagnosis and `ai.api-cheap.site` corrected image call;
- no browser/CDP, upload, platform action, public/private write, or account change;
- generated imagery remains illustrative/conceptual only;
- a rights-aware real-person/entity asset resolver remains a hard fresh-V2 requirement;
- rejected Tier2-B remains `FAIL` visually and was not merged or imported.

## Exact next action

`CHATGPT_JIM_TIER2_IMAGE_GATEWAY_AND_BAKEOFF_AUDIT`

The audit must establish an authorized credential binding for the corrected image endpoint
without emitting its value, then rerun the smoke and only then the bounded bakeoff. Do not
advance automatically to the V2 rebuild.
