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

Decision 39's finished/standing path can defer an older article's derivative
recovery while preparing a distinct article. This requires that older operation's
exact plan, canonical identity, confirmed reconciliation and verified readback.
An uncertain canonical, the same article, missing evidence or unbound obligations
still block. Existing derivative states and readbacks remain intact; UNKNOWN_WRITE
is never converted into a retry. Frozen operations retain the former backlog rule.

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

Substack showed **Check your email / Verification code** after the final publish
action. The actual return was saved as UNKNOWN_WRITE, without another send.
Human verification completed and handed control back. The exact readback then
confirmed the same object `223199520` at
[the canonical article](https://capitalchronicle.substack.com/p/the-fed-held-on-october-28-both-dissenters).
The coordinator records REAL_PUBLISHED and RECONCILED_CONFIRMED. No replacement
draft or repeated canonical publish was used. Original source clocks and the
retrospective label are preserved.

The final media-policy sub-step removes the old chart and photo minimum for all
story kinds. The same MAX editor still chooses the argument, media and placement;
all provided images/charts retain their rights, exact-source and review checks.
Instagram alone can carry `SKIPPED_IMAGE_REQUIRED`; that marker cannot skip another
channel. The final focused process passed 164 tests. An ignored local junction
reused the existing operating UI dependencies after the isolated checkout's
missing dependencies were found; no packages were installed.

Readback request
`505555cb4d538fcd883c077995f28c4cae261ad182297e56686f7b3d1d59011a`
resolved the original canonical uncertainty. Telegram, Discord and Facebook are
also confirmed and reconciled. LinkedIn remains UNKNOWN_WRITE and readback-only;
destination-local access and media outcomes are recorded separately in
`validation.json`. The canonical acceptance is satisfied; full distribution is
not implied.

The X thread is now also confirmed and reconciled:
`https://x.com/Capitalnicle/status/2117318307866968521`, with replies
`2117318312149275058` and `2117318315236299015`. Actual public text, ordered
conversation, chart and alt text were checked. The canonical link was followed
through X's redirect to the exact Substack article. X resized and transcoded the
chart to JPEG; its public hash is recorded separately from the source PNG.
Both images were inspected and match after resizing.

The repaired delivery manifest is PASS on the live retained operation. All three
public Substack originals match their source hashes, and the native vote chart
keeps its editorial role as the selected delivery image.

Four derivatives are reconciled: Telegram, Discord, Facebook and X. Remaining
distribution is explicit:

- LinkedIn is UNKNOWN_WRITE. Read back and reconcile; do not resend.
- Instagram is confirmed absent. Its delivery recovery remains held by the
  existing unknown-write media interlock.
- Threads is AUTH_INVALID. No reauthorization or send was attempted.
- YouTube requires one-time account verification for clickable external links.
  The approved text and chart were prepared and inspected, but Post was never
  clicked. The composer was cancelled, and the actual native return records
  DEFINITE_NO_WRITE with `YOUTUBE_EXTERNAL_LINK_VERIFICATION_REQUIRED`. The
  coordinator records absence; verification remains an owner action.

The existing production-day record counts one distinct canonical article and
four confirmed derivative channels. The first verified canonical readback stays
`2026-11-02T17:50:08.539332+00:00`; the next canonical is eligible at
04:20 GMT+7 on 3 November. Rereading has not reset the 3.5-hour interval. No new
standing article or CC-124 selection was started in this engineering run.
