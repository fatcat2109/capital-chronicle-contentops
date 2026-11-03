# CC-074 FOMC promotion — For Ops

The guarded [promotion script](../../../scripts/promote_cc074_fomc_for_ops.py) is
pushed at `ba892347`. **Live apply and publication have not been performed.** Ops
must apply the promotion and complete actual publication/readback. Jim's decision
37 B1 and CC-074's 2 November 20:46 GMT+7 amendment authorize this step; another
approval or clean-production-day wait is not required.

From the integrated ContentOps checkout, run a fresh read-only plan:

```powershell
python scripts/promote_cc074_fomc_for_ops.py
```

Review its paths and use the returned `plan_sha256`:

```powershell
python scripts/promote_cc074_fomc_for_ops.py --apply --expected-plan-sha256 <plan_sha256>
```

The CLI accepts only the existing Runtime store/output roots. It performs no
migration, control change, model/source call or dispatch. It checks the live
grant, AUTONOMOUS_DEFAULT, operator fuse, schema/integrity, active work and
unresolved publication/reconciliation. The [pinned manifest](promotion-manifest.json)
admits only this FOMC operation, 207 exact sealed files, 22 operation rows and its
original KEEP review. A different existing file or duplicate article/run fails
closed. It is not a general route for promoting private examples.

Apply restores missing sealed bytes without overwriting under
`A:\Capital Chronicle\Worktrees\ContentOps\codex-publisher-backlog\docs\publisher\CC-074-private-20261101`.
It imports only the operation's internal rows and reviews into the existing
store, then uses `prepare_native_publication`. The separate live binding keeps
the same run/article and records the actual promotion time. Its existing outbox
record retains the original private binding and original time. The copied source
store and its `owner_manual_validation: true` binding remain unchanged.
Unrelated state, controls, leases and public dispatches are not imported.

The existing validators recheck media and the same prior writer's exact render
acceptance. No new visual/model acceptance is claimed. Changed renderer, copy,
media or review fails at that boundary. The import transaction rolls back on
failure; exact staged files and a work-item skeleton can remain for a repeat.
After dispatch, a repeat only observes the existing publication. UNKNOWN_WRITE
must first use the existing publisher's readback/reconciliation.

Continue using the returned live `binding_path`:

```powershell
python scripts/run_native_desktop_editorial.py publication-status --binding "<binding_path>"
python scripts/run_native_desktop_editorial.py publication-resume --binding "<binding_path>" --rollout config/native_desktop_rollout_v1.json --native-invocation-id "<actual active native invocation id>"
```

Use the sole coordinator's bound Neo/API requests. Canonical `/p/` readback precedes
derivatives. Do not substitute the old writer's invocation id for the active
publisher, rerun intake/writing or call `advance`. Archive presentation, actual
publication and readback clocks remain distinct; import proves none of them.

Validation: 69 targeted checks across promotion, retrospective and native
publication; final promotion rerun 20 PASS, including the new creation-clock and
duplicate guards (71 distinct checks). See [targeted JUnit](promotion-targeted.xml),
[final JUnit](promotion-final.xml), [retained replay](promotion-replay.json) and
[delivery evidence](promotion-delivery.json). The replay uses disposable stores
and process-local file I/O relocation, preserving historical labels and hashes.
It is not live-store, browser or new visual acceptance.

Further archive pieces and the Web archive remain separate unfinished scope.
No chat, schedule, Main/MT5 path, merge or public write was used for this delivery.

## Earlier release refusal at f20ede92

The retained FOMC article passes the source, chart and clock checks. Publication is
BLOCKED by the installed V1 release gate: `OWNER_MANUAL_PUBLICATION_NOT_AUTHORIZED`.
Decision 37 B1 supplies publication authority; this is a binding/promotion defect,
not a request for another approval or for clean production days.

The accepted base is `bade5d93fec8c72ee002bd0c0efbcee4b6e2cf83`. All 207 sealed
artifact hashes remain exact. The two charts show the 10/2 vote and the announced
policy settings, traced to the two retained Federal Reserve documents within the
28 October cutoff. Both PNGs were opened and compared with those values. The
accepted prose, source clocks, eight previews and prior MAX reviews are unchanged.
This check is not a new same-writer final-render acceptance.

The existing operation `cc074-retro-fomc-20261028-v1` is still bound to the private
copied store with `owner_manual_validation: true`. The exact installed
`scheduled_publication_authority` function rejects that binding before any store
call. Rewriting the flag would not promote the accepted operation into the live
store and would falsify its original private scope. No transport was called.

Validation: 37 targeted retrospective tests pass, including sealed-byte integrity,
chart geometry/source/rights checks and hindsight/writing-date fault injections.
The initial run had 25 passes and 11 failures because absolute fixture paths pointed
at the other worktree, now on CC-042. Tests now relocate only in-memory fixture
references to the same sealed files in this exec checkout. No source or historical
artifact was edited. Ruff and whitespace checks pass.

Evidence: [release-check.json](release-check.json) and
[targeted JUnit](retrospective-guards.xml). The launch arguments specify
`gpt-6.1-sol` and `model_reasoning_effort="max"`; actual model/effort remain
`CONFIGURED_NOT_OBSERVED`.

Next action: Claude Ops integrates a scoped promotion of this exact accepted packet
through the existing live owner/store and sole publisher, preserving its original
binding and review history, then resumes this article. Do not publish from the
copied store or allocate a replacement article. No schedule or chat was changed.
