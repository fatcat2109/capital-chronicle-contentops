
# LLM Assisted Draft Review Packet Contract (After 0129)

## Purpose
The LLM Assisted Draft Review Packet validates draft text created **outside the repo** (e.g. by an operator using ChatGPT or Deep Research) based on a prior Grounded Research Brief (0128).

## What This Is NOT
- This does **NOT** call an LLM from within the repo.
- This does **NOT** fetch or scrape news.
- This does **NOT** generate final public-ready copy (publish_ready must be false).
- This does **NOT** generate a platform payload.
- This does **NOT** serve as the canonical social post object (that belongs to 0130).

## Checks Performed
1. **Safety Flags**: Enforces strict `manual_review_required`, blocks any `publish_ready`, `auto_publish`, `public_postable`.
2. **Signal Language**: Fails if the draft text or claims contain forbidden market-action signals (buy, sell, hold, entry, exit).
3. **Alpha Impersonation**: Fails if the draft masquerades as an approved Capital Chronicle artifact (e.g., claiming a `dqr_status` or "our model predicts" without an artifact backing).
4. **Source Linkage**: Requires that any factual/current claim be cited with a `source_id` that was officially declared in `source_references_used` from the upstream Grounded Research Brief.

## Future Hooks
This validated local draft packet can later be mapped into a Canonical Social Post and Platform Dry-Run (0130) after the operator confirms the draft meets editorial standards.
