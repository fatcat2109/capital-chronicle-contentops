# Final Closure Operator Runbook

Classification: `BLOCKED_FINAL_AUTOMATION_PIPELINE_CLOSURE`

## Current Gate

Do not publish the oil repair or a fresh generalized canary while Capital Chronicle DQR is degraded or `reporting_allowed=false`. Successful LinkedIn and Facebook repairs and the two exact Threads deletions are frozen.

## Resume

1. Refresh and verify the main ingestion repo with its documented readiness command.
2. Run the canonical runner with `--prepare-generic-fabric`, explicit evidence root/packet, deterministic run ID, and output directory.
3. Continue live only when freshness, DQR, market state, visual, and all editorial roles pass.
4. Resume only failed destinations. Reconcile `UNKNOWN` read-only before retry.
5. Run `--closure-release-verify` against the completed generic result.

## Manual Audit

- Confirm LinkedIn activity `7481311616265895936` again shows the accepted Fed article.
- Confirm Threads root `18087989708109547`, replacement mechanism reply `18366144508233800`, and policy reply `18166762501444151`; decide whether the visible order is acceptable.
- After a future eligible run, inspect the repaired oil article, fresh oil LinkedIn activity, fresh Substack canary, and eight derivative readbacks.

## Release Finalizer

Only after the verifier reports `AWAITING_OPERATOR_FINAL_V1_0_ACCEPTANCE_NO_ENGINEERING_BLOCKERS` and Jim explicitly accepts:

```powershell
python -m live_contentops.eight_platform_substack_first_pipeline_v1 --run-id contentops-v1.0.0 --output-dir docs/automation/FINAL_AUTOMATION_PIPELINE_CLOSURE_V1/contentops_final_closure_20260711_1 --finalize-v1-tag --operator-final-acceptance ACCEPT
```

The command fails closed unless branch `master` is synchronized with `origin/master`, the tag is absent, and the verifier has no blockers.
