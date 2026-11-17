CC-563 is integrated into the ContentOps operating source. Image-check exceptions now
produce the existing durable `DEFINITE_NO_WRITE` dispatch, outbox and reconciliation
records, preserving their exception type and first cause. A market or release post
without a run folder cannot read capture state relative to the process's current
folder. The actual coordinator and validator consume both repairs.

The Publisher-B delivery is `ac50ac1d00d3d2529c5b1951087d84f5f30775e1`.
It was merged onto operating HEAD
`02318c3d220a37024a7c1798ecdaa10ba092cbe4`, as the backlog item requires,
with integration commit `096d7833ba095a2dcabe243280dbd23a532a5748`. The merge is clean and
changes only the two validation boundaries and the advisor regression file.
The remote default branch lacks this operating baseline, so the integration
uses the existing operating source rather than replacing it.

The [targeted integration result](targeted-tests.xml) records **101 passed in
47.54 seconds**: the 84 CC-548 checks named in the backlog, plus 17 advisor
and boundary cases. The six targeted files ran in one pytest process, with no
workers or full suite. They exercise the existing digest consumer's accepted
folderless intent, wrong-market chart refusals, deleted run folders, unexpected
exception types, restart durability and unrelated current-folder capture state.

The operating root `A:\Capital Chronicle\ContentOps` was then advanced with
`git merge --ff-only backlog/cc-563-live-integration`. The
[live-source consumer result](live-consumer-tests.xml) records **17 passed in
6.61 seconds**, executed from that operating root against its installed modules.
The coordinator tests use isolated temporary stores and fixture transports:
the checks demonstrate installed consumer behavior, with no public send or
production-store mutation. No running app, schedule or control was changed.

The native publication CLI prepends its own repository root to `sys.path`;
its normal coordinator binding imports this installed
`live_contentops.publication_coordinator_v1.DurablePublicationCoordinator`.
Fresh CLI invocations therefore use the repaired shared image boundary. An import inspection from the operating
root confirms `_dispatch_message_once` calls this validator.
The retained native requests and uncertain writes keep their existing recovery.

Rollback tag: `contentops-rollback-20261117-cc563`, at the pre-integration
operating HEAD. Live tag: `contentops-live-20261117-cc563`, at this delivery's
final evidence commit. Both are pushed with the integration branch.

Both pre-existing tracked edits in the execution worktree and all six in
the operating root retain their original byte hashes. They are outside this
item's commits; unrelated untracked artifacts also remain in place.

The active launch's arguments were read from codex.exe PID 40144:
`--model gpt-6.1-sol` and `model_reasoning_effort="max"`,
`CONFIGURED_NOT_OBSERVED`. These are launch configuration observations;
no model-runtime telemetry or editorial model call is claimed.

No-red-tape review: the refusal protects the existing chart requirement against
an unrelated run's state and preserves the measured first failure in the
existing store. No new approval, label gate, ledger or publication owner was
introduced. The backlog's explicit integration route has no Ops review step.

Validation recorded at 2026-11-17T12:56:25.037639+00:00.
