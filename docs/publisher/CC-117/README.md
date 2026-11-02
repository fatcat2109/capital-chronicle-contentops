# CC-117 — For Ops

The integration candidate is `origin/backlog/cc-117-newsroom-publication`.
It starts at `contentops-live-20261102-cc042c` (`c2b5aea1`), contains CC-109
`9a24913c` and CC-074 `38b7b7df`, and repairs their newsroom continuation.
Dependency merge `eb2dde73` passed 86 targeted checks before being pushed.
Integration, promotion apply and publication belong to Claude Ops. This run has
performed none of them, and has run no production window or external public write.

## Findings and change

The [retained incident](recorded-hold.json) comes from the 2 November 21:00 GMT+7
window, run `simple-gemini-slot-9fabdc0f3e4ac2048b07c2c667310d4c`. The selection
chose a document-lens analysis from the retained 28 October Fed range. It did not
have the full statement or comparable history. Those facts could support a short,
dated background item; they could not support the proposed analytical argument.
The actual MAX return names `SOFTWARE_PROCESS_DEFECT`, with the observed CLI
error `EXACT_BOUND_LIVE_SELECTION_REQUIRED`; the day summary groups this under
`SOURCE_MISSING`. No external source-access failure was observed. The source
recovery code accepted live manual operations but excluded scheduled bindings,
and rejected recovery after MAX froze. The window therefore spent zero requests.

New scheduled selections put sources within 24 hours first, before the 32-item
cap, retaining source-route ordering within each age group. Original publication
dates determine age; intake and revision clocks do not refresh it. Older items
carry background metadata. Their title and social hook must start with
`Background:`; ordinary claim and source validation still applies. Selection
explicitly prefers today's releases, current moves and source-backed event previews.

Light can name bounded `source_requests` in its selection or media preparation.
The existing CLI then returns `stage: sources` and
`coordinator_action.action: EXECUTE_BOUNDED_SOURCE_REQUESTS` before MAX freezes.
The native conversation executes those exact non-chargeable URLs through existing
BrowserOS Neo/source capture and retained-source admission owners, then calls
`recover-sources` with the same binding, request hash, capture hashes, clocks and
rights records. Registered scheduled bindings now use that existing recovery
route. Requests remain reachable when the initial resolver returns an empty source packet.
Successful recovery and actual captured failures both carry their spending
into the shared ten-request window total, including after interruption. Wrong
bindings, changed requests, paid inputs, future-source clocks and frozen MAX
requests still refuse. Source requests do not claim that acquisition occurred.

CC-109's short NEWS/POLICY path bypasses media planning and render review, while
retaining the actual MAX writer, fact check, exact-copy review, public-output
guard and sole publisher. One integration defect remained: the certainty checker
expected reader copy on channels that CC-109 had explicitly skipped. It now
recognizes those exact named skips. Active channels retain their certainty checks.
Instagram without an image is skipped; the six text destinations can proceed.

Frozen historical requests and returns are unchanged. The incident test makes a
new controlled short background choice from the same exact Fed source packet,
then reaches reconciled publication through disposable transports. It asserts
zero external source calls and zero external public writes. This is a
counterfactual regression, not a new native model return, visual acceptance,
live publication, or proof of daily output. The historical analysis HOLD remains.

## Integrate

Run in Claude Ops' integration turn, after reviewing the pushed candidate and
checking that the operating checkout's uncommitted paths do not overlap it.
Preserve unrelated work. Do not reset, stash or switch the checkout.

```powershell
$operatingRoot = 'A:\Capital Chronicle\ContentOps'
git -C $operatingRoot status --short --branch
git -C $operatingRoot fetch origin backlog/cc-117-newsroom-publication
git -C $operatingRoot diff --name-only HEAD origin/backlog/cc-117-newsroom-publication
git -C $operatingRoot merge --ff-only origin/backlog/cc-117-newsroom-publication
if ($LASTEXITCODE -ne 0) { throw 'Integration failed; preserve the checkout and inspect the exact error.' }
```

## Apply the FOMC promotion and run its publisher

The named invocation is **Claude Ops' CC-117 integration-turn FOMC continuation**,
immediately after the promotion below. Ops owns this command; it is not left to an
unassigned future window. Use the actual active native publisher identity for
`$publisherInvocationId`, taken from its supported invocation context. That future
identity is not observable in this zero-write engineering run. Do not invent it,
reuse the historical writer's identity, or reuse this engineering run's identity.

From the integrated operating checkout:

```powershell
Set-Location -LiteralPath 'A:\Capital Chronicle\ContentOps'
$promotionPlan = python scripts/promote_cc074_fomc_for_ops.py | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Promotion plan failed; inspect its first cause.' }
$promotionPlan
# Review the exact operation, article, paths and fresh plan hash above, then apply.
$promotion = python scripts/promote_cc074_fomc_for_ops.py --apply --expected-plan-sha256 $promotionPlan.plan_sha256 | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Promotion apply failed; inspect its first cause.' }
$fomcBinding = 'A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc074-retro-fomc-20261028-v1\binding.json'
if ($promotion.run_id -ne 'cc074-retro-fomc-20261028-v1' -or $promotion.binding_path -ne $fomcBinding) { throw 'Unexpected promoted operation.' }
python scripts/run_native_desktop_editorial.py publication-status --binding $fomcBinding
if ($LASTEXITCODE -ne 0) { throw 'Publication status failed; inspect its first cause.' }
if ([string]::IsNullOrWhiteSpace($publisherInvocationId)) { throw 'Set the actual active native publisher invocation identity from supported context.' }
python scripts/run_native_desktop_editorial.py publication-resume --binding $fomcBinding --rollout 'A:\Capital Chronicle\ContentOps\config\native_desktop_rollout_v1.json' --native-invocation-id $publisherInvocationId
```

This final command is the exact publication entry point for retained article
`20a1517c263cdec4aca92c0894333f07a775793b8f530f6bc2ace1e74dad04e1`.
Record its actual invocation and result in the existing Ops run result. Continue
its returned Neo/API tool requests through `publication-tool-begin` and
`publication-tool-submit`, then `publication-resume` on this same binding and
active invocation. Confirm the canonical `/p/` URL before derivative publication.
An ambiguous write requires readback/reconciliation before any further send.
Do not run `advance`, intake, selection or writing for this accepted FOMC packet.
Promotion alone proves no publication.

The existing [promotion instructions](../CC-074-live-20261102/README.md) retain
the 207 sealed files, 22 operation rows and original review bindings. No schedule,
new publisher, Main/MT5 path, deployment procedure or new approval round is added.

## Validation

228 distinct targeted tests pass: 216 in the combined run and 12 existing
owner-operation tests in a subsequent process. Only one pytest process ran at
a time, without parallel workers or the whole suite. The 13 E701/E702 lint
findings in the existing source-recovery test helper predate this branch; scoped
lint otherwise passes.

See [validation.json](validation.json), [controlled replay](recorded-replay.json)
and [targeted JUnit](checks/targeted.xml).
The dispatch arguments specify `gpt-6.1-sol/max`, labelled
`CONFIGURED_NOT_OBSERVED`. No editorial model call was made during this repair.
