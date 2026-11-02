# CC-123 — Finished articles and standing production

Decision 39 authorizes Publisher's ContentOps integration and publication. The
existing durable store, native roles, source owners, leases, KILL_SWITCH and
DurablePublicationCoordinator remain in use. No schedule or chat is changed.

The tested CC-117 continuation and CC-107 event templates/guard were integrated
by fast-forward under `contentops-live-20261102-cc123a`. The operating checkout's
42 uncommitted entries had identical status hashes before and after. The previous
rollback tag is `contentops-live-20261102-d39`.

## Release a finished piece

From the integrated operating checkout:

```powershell
python scripts/run_native_desktop_editorial.py release-finished --binding "<original binding.json>" --rollout config/native_desktop_rollout_v1.json
```

The command replays the exact native writer's fact check, checks source clocks,
chart lineage, current KEEP/final acceptance and the public-output guard. It
reuses a live binding or imports only the finished operation through CC-074's
existing promotion engine. It needs no per-store manifest or separate apply
invocation. Source rows, original binding, original clocks and prior reviews stay
unchanged; the existing outbox retains import provenance. Publication eligibility
has its own present clock, so an old event cutoff is never relabelled as current.
A supplied typed event packet uses CC-107's guard and the frozen source-owner
admission. A writer cannot author that admission. Existing attempts are observed,
never recreated or prepared again. An uncertain write uses the same readback path.

The returned live binding continues through the same publication commands:

```powershell
python scripts/run_native_desktop_editorial.py publication-resume --binding "<returned binding_path>" --rollout config/native_desktop_rollout_v1.json --native-invocation-id "<actual supported invocation>"
```

Begin each returned exact native request, perform its actual Neo action, submit
its actual bound observation and resume the same coordinator. Canonical Substack
identity/readback precedes derivatives. Publication authority does not establish
account access. A missing destination is reported by name. No blind retry is safe.

## One standing article

```powershell
python scripts/run_native_desktop_editorial.py standing --operation-id "<stable article operation id>" --request-file "<UTF-8 article request>" --rollout config/native_desktop_rollout_v1.json
```

This extends the existing live owner-manual operation. Resume its stable ID after
interruption; accepted native returns and frozen inputs are retained. It refuses
a held newsroom lease, another unfinished standing operation, eight distinct
read-back canonical articles in the current production day, or the publication
interval. It performs no waiting and creates no scheduler. New canonical sends
are spaced by 3.5 hours, measured from the first verified canonical readback;
identity checks, recovery and derivative continuation do not restart that clock.
The existing day record includes standing and promoted articles on their actual
publication day, retaining their original evidence cutoff.

CC-124 chooses one due article in its backlog priority order, runs the approved
native preparation/writing/review roles, publishes/readbacks it, records the exact
URL and stops. New source facts, copy or media require their existing fresh review.
This engineering item does not perform CC-124's later article selection.

## Evidence

See [validation.json](validation.json) and the focused JUnit files in `checks/`.
Simulated tests establish mechanics only. Actual publication URLs and readbacks
are recorded separately after the real coordinator continuation. Dispatch model
arguments are `gpt-6.1-sol/max`, CONFIGURED_NOT_OBSERVED. Existing accepted editorial
invocation observations retain their original status; none is reconstructed.

## Actual publication continuation

`release-finished` accepted the exact promoted FOMC piece. Neo verified the
signed-in Capital Chronicle publisher, created draft `223199520` under the exact
claimed coordinator request, and placed the approved prose and all three original
media with captions, rights credit and alt text. A saved transport comparison
matches the approved prose after Substack smart punctuation normalization. Actual
mobile vote-chart and desktop rate-chart previews were inspected; this is a
transport check, not a newly invented same-writer acceptance.

Substack then showed **Check your email / Verification code** after the final
Publish without buttons action. No canonical URL or published readback has been
confirmed, and no derivative was sent. Jim must enter the code directly in the
existing BrowserOS Neo dialog. The retained draft is
`https://capitalchronicle.substack.com/publish/post/223199520`. Preserve that object
and the claimed request; read back before any further send. Do not create another
draft, resend a code or treat the draft's numeric id as a published article.

The final media-policy sub-step removes the old chart and photo minimum for all
story kinds. The same MAX editor still chooses the argument, media and placement;
all provided images/charts retain their rights, exact-source and review checks.
Instagram alone can carry `SKIPPED_IMAGE_REQUIRED`; that marker cannot skip another
channel. The final focused process passed 164 tests. An ignored local junction
reused the existing operating UI dependencies after the isolated checkout's
missing dependencies were found; no packages were installed.

The actual publish return is durably recorded as UNKNOWN_WRITE. Coordinator
continuation saved readback request
`505555cb4d538fcd883c077995f28c4cae261ad182297e56686f7b3d1d59011a`.
Resume that read-only request before any new publication action. All eight
derivatives remain NOT_DISPATCHED. Until a real canonical readback is confirmed,
CC-123's publication acceptance is BLOCKED and CC-124 remains blocked.
