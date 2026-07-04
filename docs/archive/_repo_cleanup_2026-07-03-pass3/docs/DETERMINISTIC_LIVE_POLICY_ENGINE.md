# Deterministic Live Policy Engine

The deterministic live policy engine (`cc-live-contentops/live_contentops/policy_engine.py`) serves as the strict, local-only safety gate for all payloads before they can proceed to human review or future live operations.

### Purpose
- Evaluates structured payloads (contracts, source exports, prompts) deterministically.
- Returns a `PolicyDecision` enforcing boundaries.
- Pass does **not** mean publish-ready. It only means `PASS_REVIEW_REQUIRED`.

### No Network Guarantees
- No online verification of sources.
- No provider moderation API calls.
- No platform actions.
- No scheduling/publishing.

### Rule Categories
- **Source-state gating:** Blocks content requiring sources if `source_bundle_ids` are absent.
- **Financial/Trading:** Blocks language advising buy/sell/hold, position sizing, or guaranteed predictions.
- **Political/Election:** Blocks partisan persuasion and vote instructions. Neutral policy transmission is allowed to proceed to review.
- **Live-action:** Blocks requests for `auto-publish`, `publish_now`, `schedule_now`, `dm automation`.
- **Secrets:** Blocks payloads embedding keys or credentials.
