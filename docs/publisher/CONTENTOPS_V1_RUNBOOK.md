# ContentOps V1 runbook: a finished piece to every destination

Written by the ContentOps V1 lane on 4 Nov 2026 for Codex Publisher; updated 4 Nov 23:00 GMT+7.
Live tags it describes: `contentops-live-20261104-cc199-v1-lane-c` (V1 fixes),
`contentops-live-20261104-cc245-fact-cards` and `contentops-live-20261104-cc245-data-cards`
(cards), `contentops-live-20261104-cc247-repost` (repost after removal). Rollback restores
the live tag before the change (`git tag --list "contentops-live-*" --sort=creatordate`).
Times for Jim are GMT+7; records stay UTC.

## 1. How a finished piece goes out

1. The piece's operation has a `binding.json` under
   `A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\<run_id>\`.
2. From `A:\Capital Chronicle\ContentOps` run, with your real invocation id:

   ```
   python scripts/run_native_desktop_editorial.py publication-resume --binding "<binding.json>" --rollout config/native_desktop_rollout_v1.json --native-invocation-id "<your turn id>"
   ```

3. The coordinator sends Substack first, then every derivative in one pass:
   Telegram, Discord, Facebook, Instagram and Threads through their APIs; X, YouTube,
   the LinkedIn company page and Substack through Neo. Jim's member profile goes through
   the LinkedIn member API. A Neo step comes back as `native_tool_request`: run
   `publication-tool-begin --request-hash <h>`, do exactly that step in BrowserOS Neo
   (one window, your task's tab group; upload only with Neo's upload tool), then
   `publication-tool-submit` with the observed result, then `publication-resume` again.
4. Check with `publication-status --binding "<binding.json>"` (read-only).

What the code now guarantees (4 Nov fixes):
- Every derivative carries an image. An empty per-platform choice takes the first
  reviewed image; a copy frozen without one gets the run's first reviewed chart or card
  at finalization (the same image as the canonical), or an owned facts card if the run
  has none. An image failure never blocks the post: it goes with its link and
  `post_image_floor_failure` records the cause.
- Instagram is never left unregistered for want of an image.
- Each LinkedIn post also goes to the Capital Chronicle company page (`linkedin_company`).
- Substack requests carry each image's `placement_after`, caption and alt text; place
  the image where `placement_after` says, never above the first paragraph unless it says so.
- One destination's recovery (Threads `AUTH_INVALID`, a LinkedIn `UNKNOWN_WRITE`) no
  longer holds the article's other destinations once its canonical is confirmed.
- Daily digest: day label "November 4, 2026", every live article (the store's confirmed
  canonicals as well as the feed), a one-line standfirst each, a titles card at the top;
  a web-confirmed digest never holds the next day's.

## 1b. Cards (CC-245)

Every typographic card renders through `live_contentops/fact_card_design_v1.py` in the site
design: source facts, post facts, the Instagram delivery card (1080x1350), the digest titles
card and CC-144's source-bound data cards (`post_visuals_v1._render_card`, since
`contentops-live-20261104-cc245-data-cards`). Each card shows the name large, the key date or
figure largest (always text from an admitted fact), the facts verbatim, and a footer with the
source and its own date plus the piece's date. A data card whose facts cannot all show at
28 px or larger stops with `DATA_CARD_CONTENT_EXCEEDS_READABLE_LAYOUT` instead of going out
cut. Sent files are never overwritten.

SEC's new card is in its run at `media/sec-si-roundtable-event-facts-20261109-cc245.png`
(record `media/fact-card-asset-cc245.json`). Send SEC only through the reviewed amendment
path with this card. A reviewed LinkedIn company copy supersedes the unsent routine one,
which still holds the old card.

## 1c. Reposting a post Jim deleted (CC-247: X, Telegram, Discord)

1. Read the destination's page through Neo and confirm the exact post is gone. Record it on
   the original dispatch with `DurablePublicationCoordinator.reconcile_owner_removed_object(
   <original dispatch id>, disposition="EXTERNAL_REMOVAL_REPORTED_NO_RETRY", observation={...})`,
   the observation naming `destination`, `public_object_id`, `authority_ref` (Jim's words and
   time), `observation_ref`, `observed_at_utc`, `observation_basis` and
   `exact_object_absence_verified: true`.
2. The repost copy needs the same review reference `publication-reader-derivative` takes: an
   accepted, owner-approved reviewed revision carrying this destination's copy and the new card.
3. Put `{"destination": "x", "review_reference": {...}}` in a response file and run
   `python scripts/run_native_desktop_editorial.py publication-repost-after-removal --binding "<binding.json>" --rollout config/native_desktop_rollout_v1.json --native-invocation-id "<your turn id>" --response "<file>"`.
   Telegram and Discord go out through their APIs and read back in the same call. X returns
   `NATIVE_NEO_TOOL_PENDING` with a `native_tool_request`: begin, do the step in Neo, submit,
   then run the same repost command again; it continues that dispatch and reads it back.

What the code guarantees: one new dispatch per removed post, under its own id
(`repost_of_dispatch_id` names the deleted one); the deleted post keeps its record as
`EXTERNAL_REMOVAL_REPORTED_NO_RETRY`. Running it again only reads back
(`REPOST_ALREADY_ATTEMPTED_READBACK_ONLY`). Named refusals:
`REPOST_VERIFIED_OWNER_REMOVAL_REQUIRED` (no verified removal record),
`REPOST_EXACT_ORIGINAL_DESTINATION_REQUIRED` (not X, Telegram or Discord),
`DATED_DISTRIBUTION_CANONICAL_IDENTITY_CHANGED` (the article's link changed),
`REPOST_IMMUTABLE_REVIEW_CONFLICT` (a second, different review for the same removed post).

## 2. What proves it

For each destination, `publication-status` shows `DISPATCH_CONFIRMED` with
`RECONCILED_CONFIRMED` and a public URL. Then read the public page through Neo and check
the image is the reviewed one (the run's `media/` file). `published_content_v1.jsonl`
gets the piece once its canonical is confirmed. Record each piece's result in its
BACKLOG Result line: `+1: <title>, <Substack URL>, <destinations confirmed>`.

## 3. Named failures and what to do

| Status or cause | Meaning | Action |
|---|---|---|
| `UNKNOWN_WRITE` | The send may or may not have landed. | Read the destination's page through Neo at least 10 minutes after the attempt. Present: confirmed. Absent: one retry, then a readback. Never resend blind. |
| `AUTH_INVALID` / `THREADS_AUTH_INVALID` | The account token expired. | Jim re-authorizes; never retry a login or read secret files. Other destinations continue. |
| `NATIVE_NEO_TOOL_PENDING` / `PENDING_NATIVE` | A Neo step is waiting. | Do the step (begin, act, submit, resume). A Claude Code session may take it: its `tool_observation` says `surface: CLAUDE_CODE_SESSION` and `tool_name: mcp__browseros-neo__run`, with its own invocation id (CC-283); never a Codex label. In a publishing operation a PUBLISH step's action packet carries `composed_run`: one Neo run checks the expected account, publishes once and reads back; submit adds `composed.identity` (observed between begin and the click) and, after a click, `composed.readback`. A mismatch returns FAILED_BEFORE_WRITE with no click. |
| `VERIFY_IDENTITY linkedin_company` | First company-page send in a session. | Open the company admin page in Neo, confirm "Capital Chronicle" (143198922), submit. |
| `PENDING_JIM_EMAIL_CODE` | Substack asked for the email code. | Leave that tab on the code screen; Jim types it; continue in other tabs (decision 54). |
| `DERIVATIVE_EXPIRED_STALE_NO_WRITE` | The copy aged out unsent. | Do not repost a stale copy; the newest piece goes instead (CC-186). |
| `RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE` on Substack | Exact copy equality was not established. | Read back the exact canonical identity, title and public analysis notice. CC-199 records publication separately from the copy limitation, then releases unchanged derivatives. A missing title/notice or wrong identity still holds this canonical. |
| `FAILED_BEFORE_WRITE` (Instagram, unhosted image) | The selected image has no hosted URL. | Re-run the resume; the delivery step hosts the selected image. Never use an old hosted card. |
| `post_image_floor_failure` on an intent | No image could be built. | The post went with its link; fix the cause named there. |
| `NATIVE_FILE_DIALOG_OPEN` | A native file dialog opened. | Stop that step; Jim closes it. Upload only through Neo's upload tool. |

## 4. CC-199 continuation (5 Nov)

The finished-piece path has no 3.5-hour spacing hold and no single-pending-operation
restriction. The shared newsroom lease still prevents simultaneous writers. Every brief
now compiles and registers every authorized destination, including Facebook, Instagram
and YouTube; historical skip records and issued identities stay intact.

LinkedIn failures before its HTTP post (preparation, DNS, connection refusal and certificate
rejection) are definite no-writes. A timeout after sending remains ambiguous and requires
the existing page readback. Instagram validation, container creation and processing are
also definite no-writes; ambiguity begins at `media_publish`. Failure incidents keep bounded
validation/provider codes, never raw provider messages or token-bearing URLs. A definite
no-write does not exhaust the one retry reserved for an ambiguous public send.

Derivative freshness starts at the canonical's original observed publication time, or its
first exact verified readback when that time is unavailable. Later readbacks and edits
never refresh that clock. Breaking briefs have six hours, follow-ups 24 hours, and analysis,
data-lens, retrospective and evergreen pieces seven days. An explicit expiry (including
an event's T0) still takes precedence. The site-first path uses its existing confirmed site
observation. Recovery cannot substitute an old intent URL for an unresolved canonical.

Every native Neo action packet carries decision 63's one-existing-window and task-tab-group
instructions, including identity and readback steps. Issued native request hashes do not change.

The three-piece public timing and image acceptance remains to be observed after the
Threads credential rotation recorded in CC-143. See [CC-199 evidence](CC-199/README.md).

## 5. Retained limits

- Threads: Jim's refreshed token works (Threads posts confirmed at 22:16 and 22:19 GMT+7).
  When it expires, `THREADS_AUTH_INVALID` returns and Jim re-authorizes. A Neo path for
  Threads would remove the token dependency (the web session is signed in).
- 17 tests that already failed on 24e067d3 (listed in
  `CC-199/contentops-v1-lane-20261104/regression-15-files-summary.txt`).
