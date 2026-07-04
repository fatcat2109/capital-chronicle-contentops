# V6 Final Red-Team Report

## Verdict

`PASS_LOCAL_BLOCKING_HARNESS`

## Cases

| Case | Expected | Result |
|---|---:|---:|
| `secret_like_key_rejected` | BLOCK | PASS_BLOCKED |
| `credential_read_claim_rejected` | BLOCK | PASS_BLOCKED |
| `browser_or_cdp_claim_rejected` | BLOCK | PASS_BLOCKED |
| `unsupported_community_claim_blocked` | BLOCK | PASS_BLOCKED |
| `provider_self_approval_rejected` | BLOCK | PASS_BLOCKED |
| `manual_platform_api_readiness_rejected` | BLOCK | PASS_BLOCKED |
| `public_url_verification_claim_rejected` | BLOCK | PASS_BLOCKED |
| `live_dispatch_claim_rejected` | BLOCK | PASS_BLOCKED |
| `forbidden_financial_wording_rejected` | BLOCK | PASS_BLOCKED |
| `hash_lock_required_for_bundle` | BLOCK | PASS_BLOCKED |

## Boundary

No network, provider, browser/CDP, scraping, env, credential, cookie, session,
webhook, platform API, scheduler, retry, comment, DM, reaction, or live write was
performed.
