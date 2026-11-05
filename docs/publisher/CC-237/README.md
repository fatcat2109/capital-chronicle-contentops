# CC-237: publication records tell the truth

From the ContentOps lane of Ops Product (Claude Opus 5.5), 5 Nov 2026. Live at bd8ac3a5 (tag `contentops-live-20261105-cc237-publication-truth`, rollback `contentops-rollback-20261105-cc237-publication-truth` -> 0c2b3e2e).

## 1. No failure reads as confirmed

`publication_coordinator_v1.normalize_dispatch_result` used to read any status *containing* PASS, PUBLISHED, CONFIRMED or SUCCESS as a success. NOT_PUBLISHED, NOT_CONFIRMED and DRY_RUN_PASS all counted. An explicit `ok: false` did not override it, and a draft id counted as a public object.

Now:

- Each adapter's own success words are matched exactly.
  - Neo returns: SUCCESS, PUBLISHED, DISPATCH_CONFIRMED.
  - API, webhook and Edge adapters: SUCCESS, ALREADY_SUCCESSFUL_IDEMPOTENT.
- An explicit `ok`, `success` or `published` false always wins.
- A draft id confirms only beside a public post URL, never at the editor (`/publish/...`). It stays the identity an UNKNOWN_WRITE is read back by.

A read-only census of the production store found that every real confirmation used SUCCESS, so no live path loses its success word.

## 2. The midterm is in the feed

The live midterm preview (Substack 223293057, run `cc107-midterm-preview-20261103-v1`) was missing from the feed. Its Substack reconciliation read RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE: the readbacks of 3 Nov came back BLOCKED.

The fix used the existing owners only, read-only:

- `bind_native_neo_coordinator(..., allow_publish=False)`, so the executor refuses any PUBLISH or EDIT;
- `readback_existing_dispatch` on the Substack dispatch only, so no social copy was registered.

The readback ran in BrowserOS Neo, recorded under the CLAUDE_CODE_SESSION surface:

- request `1775c86d...`, claimed, observed at 05:25:47Z;
- `post_date` 2026-11-03T10:20:18.502Z;
- both article images matched the reviewed SHA-256s (19a3be6a..., f230c117...);
- the copy had been edited after publication (the subtitle's "change" became "alter"), so the return honestly reports `content_verified: false`. CC-199's canonical-publication check (title, notice, identity) confirmed it.

Results:

- reconciliation RECONCILED_CONFIRMED;
- `sync_published_content` APPENDED `substack:223293057`;
- the preview hook STARTED its worker (pid 12208, 05:26:20Z).

The owner-manual path already calls the sync (coordinator, after `execute_plan`). The block was the reconciliation, not a missing call.

The midterm package lacked `delivery_media_manifest_v1.json`. The coordinator writes that file at canonical readback only when the copy matches exactly. It was built with the coordinator's own code (`build_delivery_media_manifest` over the observed public originals): status PASS, both reviewed assets hash-continuous. This was a local write only.

## 3. Current outlets, causes and blockers

- **Outlets.** The feed keeps each first recording, sealed and untouched. Later confirmed outlets are appended to `Runtime\ContentOps\published_content_outlets_v1.jsonl`, beside the feed:
  - one sealed line per change, naming the piece by its record seal;
  - `sync_confirmed_piece` appends one when a recorded piece's confirmed outlets change;
  - `current_outlets()` and `read_current_records()` give readers the current list.
- **The first run on live (05:28Z), first recording -> now; no outlet dropped:**

  | Piece | Outlets |
  |---|---|
  | CPI | 1 -> 9 |
  | FOMC | 5 -> 7 |
  | SEC | 6 -> 8 |
  | Jobs | 7 -> 10 |
  | PPI | 7 -> 9 |
  | Southwest | 3 -> 8 |

- **The preview reader** (Main `backlog/cc-237-preview-current-outlets`, 09bd09e840) reads the outlets file.
- **The publication projection's `blocker`** names the reconciliation, dispatch or queued-message state, or NOT_REGISTERED. It no longer gives the fixed CURRENT_EXTERNAL_IDENTITY_AND_READBACK_NOT_VERIFIED.
- **The production-day record** counts a bound window that ended with no editorial result as WINDOW_ENDED_WITHOUT_EDITORIAL_RESULT, instead of `{}`. On 3 Nov five windows read `{}`.

## Tests

- `tests/test_publication_truth_cc237.py`: 27 tests.
- 353 pass across the 10 related files: coordinator, published content, finished-piece dispatch, volume window, native publication, projection, Neo executor, LinkedIn API, digest and latency.
