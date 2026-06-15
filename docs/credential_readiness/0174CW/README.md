# 0174CW X OAuth User-Context Design and Redirection Policy

Strictly local, official-doc-grounded, DESIGN-ONLY X OAuth user-context + redirect/callback/PKCE/token policy packet. No OAuth flow, no authorize URL opened, no browser/developer-portal login, no token exchange, no Client ID/Secret read, no state/code_verifier/code_challenge generated, no account binding, no posting.

## Inherited posture

- Inherits the conservative posture: live posting is `blocked_until_new_explicit_task_and_operator_go`.
- This task only designs the future OAuth user-context; it does not enable any live path.

## OAuth flow (symbolic)

- Flow family: OAuth 2.0 Authorization Code Flow with PKCE (user context). Not initiated now.
- Public vs confidential client decision is deferred to a dedicated future gate.

## Official docs inspected

- Authorization Code Flow with PKCE (`docs.x.com/fundamentals/authentication/oauth-2-0/authorization-code`) -- accessible.
- Authentication Overview (`docs.x.com/fundamentals/authentication/overview`) -- accessible.
- Create or Edit Post (`docs.x.com/x-api/posts/create-post`) -- accessible (downstream context only).
- Developer Portal access tiers (`developer.x.com/en/portal`) -- gated (login required, not performed) -> blocker.

## Redirect / callback policy

- No real callback URL registered or tested now.
- Future callback URL must be exact-match, deterministic, local-first, and must never be logged with its query string.
- Future callback handler redacts `code`, `state`, token-like strings, and all query params before persistence; logs store booleans/classes only.
- Browser redirect handling is operator-triggered only, never autonomous.

## State / PKCE policy

- Future state and `code_verifier` must be high-entropy, per-attempt, single-use, short-lived, and never logged raw.
- Future `code_challenge` may be stored only as a redacted/hash class if necessary.
- This task generates NO real state, code_verifier, or code_challenge.

## Scope policy

- Least privilege. Candidate future scopes: `tweet.write`, `tweet.read`, `users.read`.
- `offline.access` (refresh token) is blocked until a dedicated justification gate.
- Forbidden until scoped: `dm.read`, `dm.write`, `like.write`, `bookmark.write`, `follows.write`, `mute.write`, `block.write`, `list.write`, `media.write`, `tweet.moderate.write`, and any scope unrelated to text-only posting/account proof.

## Token storage / redaction / revocation policy

- No token exchange, access token, refresh token, or bearer token now; no token persistence now.
- Future token storage is local-only, encrypted or OS-secret-store backed if available, redacted in logs, never committed or placed in evidence.
- Token rotation and revocation plans are required before the first credential-readiness gate.

## What this did NOT do

No X (or any platform) API call. No OAuth flow, authorize URL, browser login, or developer-portal login. No authorization code, token exchange, or token persistence. No Client ID/Secret read. No state/code_verifier/code_challenge generated. No account binding, no credential or env read, no credential-entry schema. No post/edit/delete/repost/quote/bookmark/like/reply/DM, metrics, webhook, or scraping. The module never browses docs at runtime; docs reading was an Antigravity/operator activity before writing symbolic packet data.

## Next

Recommended next task: `TASK_CONTENTOPS_0174CX_X_OAUTH_CALLBACK_AND_PKCE_DRY_RUN_DESIGN_NO_SECRET_NO_TOKEN_NO_LIVE_V0`.
