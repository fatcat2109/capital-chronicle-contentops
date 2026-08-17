# TikTok Sandbox Draft Canary Gate V1 — Final Evidence

Authority date: `2026-08-17`

## Result

`PASS_TIKTOK_SANDBOX_DRAFT_CANARY_GATE_CORRECTED_READY_FOR_FINAL_OWNER_WRITE_AUDIT`

This is the implementation ceiling. No TikTok credential was read, no TikTok API was called, no
media was uploaded, and no draft or public post was created. Independent Jim/ChatGPT audit and a
later exact one-attempt owner grant are mandatory before execution.

## Bounded public-truth semantics correction

Independent audit accepted the canary architecture and identified one truth-semantics defect in
the unexpected `PUBLISH_COMPLETE` branch. The correction started from the reviewed branch head
`f65ef7797061a3202cca16e771b8a6159bc4df0c` and does not change the attempt-ID algorithm, package,
media hash, destination, environment, provider intent, durable ambiguity handling, or authorized
success/stop condition.

Current first-party TikTok status authority was reverified on `2026-08-17`:

- `SEND_TO_USER_INBOX` is inbox draft delivery for creator completion in TikTok's editing flow;
- `PUBLISH_COMPLETE` for Upload Content means the creator completed posting through that flow;
- `publicaly_available_post_id` contains a post ID only for public viewership after moderation.

The receipt now carries nonsecret `creator_finalization_observed`, default `false`. Unexpected
`PUBLISH_COMPLETE` sets it to `true` but remains `UNEXPECTED_PUBLISH_COMPLETE`, outside normal
canary success. `public_post_confirmed` becomes `true` only if the exact status response contains at
least one actual public post ID. No raw public post ID is copied to the receipt or journal, and no
`video.query` or additional mutation is performed.

## Git reconciliation

- freshly fetched starting master: `e29bd8dfd2217f684c2e9d3819cfeebe91b3da14`;
- accepted adapter branch/head:
  `task/v2-publication-adapter-reconciliation-provider-contract-correction-v1@97cd13c914f1a48029cdc8529ab9ffd31637ec1d`;
- merge base: starting master;
- accepted branch divergence: ahead 1, behind 0;
- merge method: exact fast-forward push, no merge commit;
- verified remote master after fast-forward:
  `97cd13c914f1a48029cdc8529ab9ffd31637ec1d`;
- implementation branch:
  `task/v2-tiktok-upload-draft-readiness-exact-owner-live-canary-gate-v1`;
- implementation commit: this task's single implementation commit, reported by the final handoff.

The dirty canonical checkout was preserved. Implementation occurred in the clean dedicated
worktree `A:\Capital Chronicle\ContentOps-worktrees\v2-tiktok-draft-canary-v1`.

## Exact canary contract

- package ID:
  `pkg_2dfe4af587fd8135d04bae456b8c5b30a1560be91232b34f520cf7f05a71c0b2`;
- media SHA-256:
  `1a2bddc40a2db7b019ddd5d7a5f7349182621b6e1ae273bbdd58a7393165c810`;
- destination alias: `TIKTOK_SANDBOX_PRIMARY`;
- environment: `SANDBOX`;
- intent: `DRAFT_DELIVERY`;
- provider intent version: `UPLOAD_TO_TIKTOK_DRAFT.v1`;
- deterministic attempt ID:
  `ttcanary_b9c7a9b18d7ed326d556ba53d75fd0f2f8bb7218558f031dc7e703abf092d27a`;
- execution flag: `--run-exact-tiktok-sandbox-draft-canary`;
- exact authority binding flag:
  `--authorized-attempt-id ttcanary_b9c7a9b18d7ed326d556ba53d75fd0f2f8bb7218558f031dc7e703abf092d27a`;
- readback-only recovery flag: `--readback-only-existing-attempt` with the same exact attempt ID;
- generic `--enable-writes`: absent and unsupported;
- logical draft deliveries: exactly one;
- Direct Post, `video.publish`, `video.query`, creator finalization and public posting: absent.

The attempt ID hashes the exact package ID, manifest media SHA-256, destination alias, Sandbox
environment, draft-delivery intent, and provider intent version. A missing or wrong flag/attempt ID
causes zero Credential Manager reads, zero environment-secret reads, zero network calls, and zero
mutations. The exact attempt suffix is 64 lowercase hexadecimal characters; the externally
truncated value ending in `...f092d` is rejected before any credential or network-capable
dependency is constructed.

## Accepted media preflight

Read-only local validation against the accepted manifest and actual bytes produced:

- bytes: `22,101,311`;
- container: `mov,mp4,m4a,3gp,3g2,mj2` (MP4);
- video codec: `h264`;
- dimensions: `1080x1920`;
- frame rate: `30.0` fps;
- duration: `58.0` seconds;
- chunk size: `22,101,311` bytes;
- total chunk count: `1`;
- Remotion renders/transcodes: `0`.

Machine-readable evidence: `accepted_media_readiness.json`.

## Durable ambiguity and privacy boundary

Default journal directory:

`.task-runtime/v2-tiktok-sandbox-draft-canary-v1/journal/`

Schema: `contentops.v2.tiktok_sandbox_draft_canary_journal.v1`.

The journal atomically records only attempt/package/media/destination identity, state,
`publish_id` when known, uploaded bytes when known, last bounded provider status, timestamps, and
terminal classification. It never stores an upload URL, upload query/token, credential, access or
refresh token, raw `open_id`, Authorization header, or raw provider/OAuth response.

An ambiguous init enters `UNKNOWN_WRITE` and cannot retry. An ambiguous transfer with known
`publish_id` can perform status readback only and cannot issue a second `PUT`. An unresolved
attempt stays `UNKNOWN_WRITE`. Existing terminal or unresolved journals block a second logical
delivery. The separate live receipt schema is
`contentops.v2.tiktok_sandbox_draft_canary_receipt.v1`; the generic shadow receipt is not reused.

Raw `open_id` persistence outside Windows Credential Manager: `false`.
Raw `open_id` evidence/stdout/logging: `false`.
Upload URL persistence/logging: `false`.
Access-token persistence: `false`.

## Fake proof

Focused fake E2E proves:

`secure fake refresh -> refresh rotation persistence -> exact identity match -> accepted fake package -> init -> transient upload URL -> one media PUT -> PROCESSING_UPLOAD -> SEND_TO_USER_INBOX -> DRAFT_DELIVERY_CONFIRMED`.

The success path has one logical draft delivery, one init mutation, one transfer mutation, two
bounded status reads, zero Direct Post calls, zero `video.publish`, zero `video.query`, zero creator
finalization and zero public writes.

The `SEND_TO_USER_INBOX` regression additionally proves
`creator_finalization_observed=false` and `public_post_confirmed=false`. Focused unexpected-status
proofs establish:

- `PUBLISH_COMPLETE` with no public IDs: creator finalization observed, public post not confirmed;
- `PUBLISH_COMPLETE` with one actual public ID: creator finalization observed and public-post
  boolean confirmed, while the result still remains out-of-scope `UNEXPECTED_PUBLISH_COMPLETE`;
- neither case calls `video.query`, performs an additional mutation, or serializes a raw public ID.

Adversarial coverage includes identity mismatch, missing scope, package/hash failure, wrong exact
authority, ambiguous init, reconciled and unresolved ambiguous transfer, provider failure, polling
timeout, duplicate prevention, readback-only capability restriction, unexpected
`PUBLISH_COMPLETE`, and secret-leak scanning across receipt and journal.

Machine-readable evidence: `fake_e2e_summary.json`.

## Validation

- accepted publication adapters, accepted OAuth/secure persistence, corrected canary, accepted
  package, zero-rerender, and CodeGraph tests: `125 passed`;
- corrected canary focused tests: `19 passed`;
- Ruff on all new Python paths: `All checks passed`;
- Python bytecode compilation: passed;
- accepted real Short manifest/hash/media probe: `ACCEPTED_SHORT_MEDIA_READY`;
- CodeGraph regenerated after the correction; final check: `CODEGRAPH_CURRENT`.

## Safety counters for this implementation phase

- real Credential Manager reads: `0`;
- real environment-secret reads: `0`;
- real OAuth refresh calls: `0`;
- real user-info calls: `0`;
- real Content Posting init calls: `0`;
- real media transfers: `0`;
- real status calls: `0`;
- real draft deliveries: `0`;
- public writes: `0`;
- V1 mutations: `0`;
- scheduler changes: `0`;
- Remotion renders: `0`.

## Exact proposed next owner scope — not executed

After independent audit only, the proposed grant is:

```text
provider = TIKTOK
environment = SANDBOX
destination_alias = TIKTOK_SANDBOX_PRIMARY
attempt_id = ttcanary_b9c7a9b18d7ed326d556ba53d75fd0f2f8bb7218558f031dc7e703abf092d27a
package_id = pkg_2dfe4af587fd8135d04bae456b8c5b30a1560be91232b34f520cf7f05a71c0b2
media_sha256 = 1a2bddc40a2db7b019ddd5d7a5f7349182621b6e1ae273bbdd58a7393165c810
delivery_intent = DRAFT_DELIVERY
logical_deliveries = 1
public_write = false
creator_finalization = OUT_OF_SCOPE
ambiguous_init_retry = false
ambiguous_transfer_action = READBACK_ONLY
stop_condition = SEND_TO_USER_INBOX
```

Do not execute this scope without Jim's later exact grant.
