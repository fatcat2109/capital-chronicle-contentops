# Institutional Screenshot-Safe and Redacted Visual Export Rules (After 0158)

Task label: TASK_CONTENTOPS_0158_INSTITUTIONAL_DESIGN_SYSTEM_AND_FUTURISTIC_FINTECH_VISUAL_CONTRACT_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by
`docs/INSTITUTIONAL_DESIGN_SYSTEM_AND_FUTURISTIC_FINTECH_VISUAL_CONTRACT_AFTER_0158.md`.

Planning/spec only. No active front-end code, no screenshots, no browser
automation, no Antigravity in this task. This doc defines the rules a future UI
must follow so any view can be safely captured or presented.

## Screenshot-Safe Mode Activation (Concept)

- A global toggle (`screenshot_safe_toggle`) enables screenshot-safe mode.
- When active, the UI strengthens redaction and adds a watermark; it never weakens
  redaction and never upgrades a non-PASS state to PASS.
- Safe mode is a presentation/capture concept only. It performs no file write and
  no network call. It is purely a client-side rendering state in a future static UI.

## Allowed Screenshot Contexts

- Command Center posture and blocked summary (redacted).
- Publish Readiness Tower with all platforms LIVE_DISABLED.
- Telegram Pilot Gate showing redacted gate steps (no values).
- Evidence Vault with sources/lineage references (no raw vendor payloads).
- Approval Queue and Content Calendar (planning/review only).
- Settings / Safety Policy showing all live flags false.

## Forbidden Screenshot Contexts

- Any view rendering a secret/credential value, snippet, length, or hash.
- Any view rendering a raw env path or file path to an env/secret store.
- Any view rendering raw vendor data, raw platform response, or raw request URL.
- Any view implying public-ready, publish-ready, or scheduled posting.
- Any view implying forecast readiness while gating factors exist.
- Any view containing buy/sell/hold/signal/advice language.

## Redacted Credential Fields

The following must always render as redacted tokens, never as values:
- bot token (CREDENTIAL_PRESENT_REDACTED / SECRET_REDACTED);
- chat/channel id (SECRET_REDACTED);
- any API key, OAuth token, or session token (SECRET_REDACTED).

No value, no partial snippet, no character length, no hash/digest may be shown.

## Redacted Env / Path Fields

- No raw `.env` path, no absolute path to any secret store, no environment
  variable names that could disclose secret locations.
- Credential presence is communicated only as a boolean/token (present/unknown).

## Watermark / Label Requirements

When safe mode is active, a watermark/label band must show:
- "SCREENSHOT-SAFE";
- "LOCAL ONLY";
- "NOT PUBLIC-POSTABLE";
- "LIVE DISABLED".

The watermark must be legible and present in the captured region.

## Export-Safe State Requirements

- All required safety banners remain visible (they reinforce safety).
- All limitations remain visible (no hidden limitations).
- All missing/degraded/proxy/stale states remain visible with reasons.
- No control becomes interactive in safe mode; gated controls stay disabled.

## Visual Examples (Text Only, No Images)

Example A — Telegram Pilot Gate (safe):
```
[ SCREENSHOT-SAFE | LOCAL ONLY | NOT PUBLIC-POSTABLE | LIVE DISABLED ]
Telegram Pilot Gate
  Step 1 Presence Check ......... CREDENTIAL PRESENT (REDACTED)
  Step 2 Official Docs .......... PASS
  Step 3 getMe Validation ....... API VALIDATED — NO POST
  Step 4 Channel Permission ..... CHANNEL PERMISSION UNVALIDATED
  Step 5 Explicit GO (future) ... LIVE DISABLED
  Next gate required before posting.
```
No token, no chat id, no request URL, no raw response appears.

Example B — Evidence Vault row (safe):
```
Evidence: macro_release_2026_06  SOURCE: official_release_ref  RETRIEVED: 2026-06-09T12:00Z
  Sufficiency: DEGRADED  Freshness: STALE  Proxy: PROXY ONLY
```
No raw vendor payload appears; references and states only.

## Hard Prohibitions In Export

- No secrets.
- No raw env/path strings.
- No raw vendor data.
- No public-ready false claims.
- No forecast-readiness false claims.
- No content that could look like advice/signal.
- No raw platform response.
- No raw request URL.
