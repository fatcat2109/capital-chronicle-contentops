# 0174DE X OAuth Live Read-Only Identity Proof Gate

First gate in the X OAuth chain permitted to perform a SINGLE, bounded, live, READ-ONLY request -- and only when BOTH live flags are present. Its sole purpose is to prove a user-context access token can read the authenticated account identity in a fully REDACTED, NON-PERSISTENT way.

## Default posture

- Default mode is dry-run / blocked: no network, no token read, no write.
- `live_read_only_identity_proof_status = blocked_no_operator_go` until both live flags are supplied.
- Live posting remains blocked. Account binding is NOT approved here.

## CLI

```
python -m live_contentops.cli x-oauth-live-read-only-identity-proof-gate
python -m live_contentops.cli x-oauth-live-read-only-identity-proof-gate --write-x-oauth-live-read-only-identity-proof
python -m live_contentops.cli x-oauth-live-read-only-identity-proof-gate --operator-go-live-read-only-identity-proof --execute-live-read-only-identity-proof --write-x-oauth-live-read-only-identity-proof
```

A live request occurs ONLY when both `--operator-go-live-read-only-identity-proof` and `--execute-live-read-only-identity-proof` are present. The token is then requested via an interactive hidden prompt; it is never echoed, logged, persisted, hashed, or placed in any artifact.

## Verified endpoint (official docs)

- `GET https://api.x.com/2/users/me` -- "Get my User" (`docs.x.com/x-api/users/get-my-user`), OAuth 2.0 user-context bearer token, returns the authenticated user object.
- Host is restricted to `api.x.com`; method is restricted to `GET`; request budget is `1`; there is no retry; timeout is explicit.

## Redacted output only

The transient response is mapped to boolean/class fields only (reachable, authenticated-context, identity-seen, status class) and the raw body is discarded. No user id, username, handle, display name, profile URL, metrics, headers, or token ever appear in the packet, README, logs, or output.

## What this did NOT do

Did not post/edit/delete/repost/like/reply/DM, upload media, fetch metrics, create a webhook, scrape, search, read timelines, or do bulk reads. Did not exchange or refresh tokens. Did not persist, log, hash, fingerprint, prefix, or suffix the token. Did not bind an X account.

## Next

Recommended next task: `TASK_CONTENTOPS_0174DF_X_OAUTH_SUPERVISED_ACCOUNT_BINDING_PROOF_ACCEPTANCE_GATE_REDACTED_NO_POST_NO_TOKEN_PERSIST_OPERATOR_GO_REQUIRED_V0`.
