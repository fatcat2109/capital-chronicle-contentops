# CC-584 integration — 17 November 2026

The existing delivery `4706ef2d13c8a0c3b499102e0fdff05e91f0e6ea` is integrated on
operating base `fa20a339dfbe11298abf6c8fcd6c5a61851cd81c`, on branch
`backlog/cc-584-integrate-current-plan-20261117`.

The merge retains CC-603 corrections and dated endings, CC-583's prohibition on
drawn targets, current Discord link metadata and the current minute transport
ordering. It adds the stored-card and header freshness checks, current page
validation before a send, named pricing attribution and separate cancellation
and post-entry invalidation labels. The existing owner export distinguishes a
waiting entry from a recorded fill; the alert consumer does not infer a fill
from registration or order placement.

The retained image-refused link is recoverable through the existing page CLI:
`python scripts/plan_analysis_pages.py link-repair-image-refusal --link-id <retained-id> --native-invocation-id <run-id> --result <result.json>`.
This validates the confirmed canonical and exact original link bytes, repairs only
the measured pre-transport refusal, and uses the existing coordinator's atomic
claim. Known objects, uncertain attempts and retained native writes cannot use
that repair. A second invocation cannot send a second copy.

## Verification

All test runs used one pytest process, explicit files, and isolated temporary
stores. No test uses the production store or starts a model/browser call.

- `local-evidence/cc584-integration-20261117/acceptance-final.xml`: 46 passed,
  including the stored 12 November card/header, changed public state, pricing
  attribution, phase labels, existing uncertain readback and the real link CLI.
- `local-evidence/cc584-integration-20261117/alert-and-endpoint.xml`: 81 passed,
  including immediate API alert delivery before editorial work and current Neo
  endpoint behavior. The older alert fixtures now use their own public export,
  owner-seal reader and clocks, and isolate the sibling follow-up consumer.
- `local-evidence/cc584-integration-20261117/visual-contracts.xml`: 69 passed,
  including no drawn target, exact overlay pixels and the shared image consumer.
- The first card/thread selection preserved its failures in `card-consumers.xml`;
  the card and thread cases passed. Its five alert fixture failures were corrected
  and rerun in the passing alert/endpoint selection above.

The launch process arguments specify `--model gpt-6.1-sol` and
`model_reasoning_effort="max"`; actual model/effort runtime telemetry remains
`CONFIGURED_NOT_OBSERVED`. No Claude session was started.

## Live completion

Installation, live/rollback tags, the installed consumer check, the retained
EUR/USD link readbacks and the next plan's page/card/chart readback are recorded
here after execution. Tests do not establish those public outcomes.
