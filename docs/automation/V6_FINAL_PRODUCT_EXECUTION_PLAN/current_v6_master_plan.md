# Capital Chronicle ContentOps V6 ? Current Master Plan Authority

Task label: `TASK_CONTENTOPS_V6_BOOTSTRAP_ENV_RECON_AND_CAPABILITY_MATRIX_V0`

This file pins V6 as current product authority for this repository.

## Product loop

```text
Jim idea / source / research context / future artifact
? AI research and grounding
? canonical Substack article
? SEO and editorial refinement
? platform-native variants
? Discord community drop
? Telegram/operator checkpoint
? webhook/API/browser/manual dispatch
? public URL and audit record
? community feedback and questions
? LLM summary and content backlog
? next canonical article
```

## Current authority rules

- Substack = canonical long-form authority.
- Discord = community feedback flywheel.
- Telegram = remote operator lane.
- LLM = production engine.
- Webhooks = first Discord live adapter.
- Browser/CDP = supervised adapter, never secret-reading/selfbot.
- Manual = fallback.
- Jim = final authority.
- Discord bot = after final product.

## Safety boundary

- No `.env` or secret file may be staged.
- No raw secret, webhook URL, token length, prefix, suffix, hash, digest, cookie, localStorage, sessionStorage, or browser profile secret may be output.
- Live platform writes require later explicit operator go-gates.
- This bootstrap task performs local redacted readiness classification only.
