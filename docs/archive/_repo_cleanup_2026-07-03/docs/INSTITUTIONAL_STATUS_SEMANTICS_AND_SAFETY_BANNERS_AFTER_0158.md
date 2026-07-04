# Institutional Status Semantics and Safety Banners (After 0158)

Task label: TASK_CONTENTOPS_0158_INSTITUTIONAL_DESIGN_SYSTEM_AND_FUTURISTIC_FINTECH_VISUAL_CONTRACT_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by
`docs/INSTITUTIONAL_DESIGN_SYSTEM_AND_FUTURISTIC_FINTECH_VISUAL_CONTRACT_AFTER_0158.md`.

Planning/spec only. No active front-end code created here. This doc is the
canonical status token table and the required safety banner set.

## Canonical Status Token Table

Each token: meaning, when to use, when not to use, required UI copy, color role,
icon role, test requirement. Color is operational only — never market direction.

### PASS
- meaning: validated, contract-clean, review-ready.
- when to use: a validator returned valid with no errors.
- when not to use: any unresolved error, missing data, or pending review.
- required UI copy: "PASS".
- color role: color.status.pass (green, operational).
- icon role: check glyph.
- test requirement: PASS never shown while errors/blocked reasons exist.

### DEGRADED
- meaning: works but inputs are partial / lower quality.
- when to use: partial coverage, reduced confidence, recoverable gaps.
- when not to use: as a substitute for BLOCKED or to hide missing data.
- required UI copy: "DEGRADED".
- color role: color.status.degraded (amber).
- icon role: half-filled glyph.
- test requirement: DEGRADED never collapses to PASS.

### BLOCKED
- meaning: fail-closed; action not permitted.
- when to use: any contract violation or unmet gate.
- when not to use: to imply market loss/bearish (operational only).
- required UI copy: "BLOCKED" + reason.
- color role: color.status.blocked (red, operational).
- icon role: stop glyph.
- test requirement: every BLOCKED has a plain-language reason.

### REVIEW_REQUIRED
- meaning: awaiting mandatory human review.
- when to use: drafts/items pending operator decision.
- when not to use: after an approved decision.
- required UI copy: "REVIEW REQUIRED".
- color role: color.status.review (blue).
- icon role: eye glyph.
- test requirement: present wherever manual review is pending.

### NOT_PUBLIC_POSTABLE
- meaning: never public-postable in current state.
- when to use: all content surfaces by default.
- when not to use: never removed in current sequence (0158–0168).
- required UI copy: "NOT PUBLIC-POSTABLE".
- color role: color.status.locked (slate) + lock icon.
- icon role: lock glyph.
- test requirement: present on every content screen.

### LIVE_DISABLED
- meaning: live capability intentionally off.
- when to use: every platform/publish surface.
- when not to use: never removed in current sequence.
- required UI copy: "LIVE DISABLED".
- color role: color.status.locked (slate) + lock icon.
- icon role: lock glyph.
- test requirement: present on every platform gate.

### UNKNOWN
- meaning: state could not be determined.
- when to use: missing/unevaluated state.
- when not to use: to mask a known BLOCKED/DEGRADED.
- required UI copy: "UNKNOWN".
- color role: color.status.unknown (gray) + "?".
- icon role: question glyph.
- test requirement: unknown never rendered as PASS.

### PROXY_ONLY
- meaning: data is a proxy, not the real source.
- when to use: proxy/substitute data.
- when not to use: to imply a real source exists.
- required UI copy: "PROXY ONLY".
- color role: color.status.proxy (violet).
- icon role: link-dashed glyph.
- test requirement: proxy data always labeled PROXY_ONLY.

### STALE
- meaning: data is past freshness threshold.
- when to use: as_of older than threshold.
- when not to use: to imply fresh data.
- required UI copy: "STALE".
- color role: color.status.degraded (amber) + clock.
- icon role: clock glyph.
- test requirement: stale data never shown as fresh/PASS.

### SECRET_REDACTED
- meaning: a value exists but is intentionally hidden.
- when to use: any secret/credential surface.
- when not to use: never reveal value/snippet/length/hash.
- required UI copy: "SECRET REDACTED".
- color role: color.status.redacted (slate) + shield.
- icon role: shield glyph.

### CREDENTIAL_PRESENT_REDACTED
- meaning: credential is present locally; value hidden.
- when to use: presence confirmed via redacted boolean check.
- when not to use: to reveal any value/snippet/length/hash.
- required UI copy: "CREDENTIAL PRESENT (REDACTED)".
- color role: color.status.redacted (slate) + shield.
- icon role: shield-check glyph.
- test requirement: boolean/token only; no value ever rendered.

### CREDENTIAL_VALIDATED_NO_POST
- meaning: credential validated; posting still not allowed.
- when to use: a bounded credential validation passed, posting still gated.
- when not to use: to imply posting is now allowed.
- required UI copy: "CREDENTIAL VALIDATED — NO POST".
- color role: color.status.review (blue) + lock.
- icon role: shield-check + lock glyph.
- test requirement: never implies posting allowed; live still disabled.

### API_VALIDATED_NO_POST
- meaning: API identity validated; posting still not allowed.
- when to use: bounded API identity check (e.g., identity-only) passed.
- when not to use: to imply send/post capability.
- required UI copy: "API VALIDATED — NO POST".
- color role: color.status.review (blue) + lock.
- icon role: plug-check + lock glyph.
- test requirement: never implies send/post; live still disabled.

### CHANNEL_PERMISSION_UNVALIDATED
- meaning: channel write permission not yet validated.
- when to use: identity validated but channel-write not proven.
- when not to use: to imply channel posting is ready.
- required UI copy: "CHANNEL PERMISSION UNVALIDATED".
- color role: color.status.degraded (amber).
- icon role: warning glyph.
- test requirement: present whenever channel write is unproven.

### DQR_BLOCKING
- meaning: data quality / sufficiency is blocking.
- when to use: data sufficiency gate fails.
- when not to use: to imply readiness.
- required UI copy: "DQR BLOCKING".
- color role: color.status.blocked (red, operational).
- icon role: stop glyph.
- test requirement: DQR_BLOCKING never collapses to PASS.

### FORECAST_NOT_READY
- meaning: forecast-readiness gate not satisfied.
- when to use: gating factors exist for forecast readiness.
- when not to use: to claim a guaranteed prediction.
- required UI copy: "FORECAST NOT READY".
- color role: color.status.degraded (amber).
- icon role: clock-warning glyph.
- test requirement: readiness never claimed while gating factors exist.

### MANUAL_ONLY
- meaning: manual operator action only.
- when to use: any action requiring a human.
- when not to use: to imply automation.
- required UI copy: "MANUAL ONLY".
- color role: color.status.review (blue).
- icon role: hand glyph.
- test requirement: no automated handler attached.

### DRY_RUN_ONLY
- meaning: dry-run only; no live execution.
- when to use: all publish-readiness/gate surfaces.
- when not to use: to imply live execution.
- required UI copy: "DRY RUN ONLY".
- color role: color.status.locked (slate).
- icon role: beaker glyph.
- test requirement: no live execution path exists.

### KILL_SWITCH_ACTIVE
- meaning: global kill switch is active.
- when to use: whenever kill switch is active (default).
- when not to use: to imply live capability is enabled.
- required UI copy: "KILL SWITCH ACTIVE".
- color role: color.status.blocked (red, operational).
- icon role: power-off glyph.
- test requirement: reflects kill_switch_status; defaults active/safe.


---

## Required Safety Banners

These banners are required surfaces. Each has fixed copy, is review/safe-only, and
carries no enabling control. Banners persist in screenshot-safe mode.

| Banner | Required copy | When shown | Test requirement |
| --- | --- | --- | --- |
| LOCAL_ONLY | "LOCAL ONLY" | always (shell) | present on first paint |
| DRY_RUN_ONLY | "DRY RUN ONLY" | publish/gate surfaces | present on readiness/gate screens |
| REVIEW_ONLY | "REVIEW ONLY" | content surfaces | present on content screens |
| MANUAL_REVIEW_REQUIRED | "MANUAL REVIEW REQUIRED" | pending review | present while review pending |
| NOT_PUBLIC_POSTABLE | "NOT PUBLIC-POSTABLE" | content surfaces | present on every content screen |
| LIVE_DISABLED | "LIVE DISABLED" | platform/publish | present on every platform gate |
| API_VALIDATED_NO_POST | "API VALIDATED — NO POST" | after identity validation | never implies posting allowed |
| CHANNEL_PERMISSION_UNVALIDATED | "CHANNEL PERMISSION UNVALIDATED" | channel-write unproven | present when channel write unproven |
| KILL_SWITCH_ACTIVE | "KILL SWITCH ACTIVE" | kill switch active | reflects status; defaults active |
| SECRET_REDACTED | "SECRET REDACTED" | credential surfaces | no value/snippet/length/hash shown |
| NO_FINANCIAL_ADVICE | "NO FINANCIAL ADVICE" | all screens | present; no advice language |
| NO_SIGNAL_LANGUAGE | "NO SIGNAL LANGUAGE" | all screens | present; no buy/sell/hold/signal terms |
| DQR_BLOCKING | "DQR BLOCKING" | sufficiency gate fail | never collapses to PASS |
| FORECAST_NOT_READY | "FORECAST NOT READY" | readiness gate unmet | readiness never falsely claimed |
| PROXY_ONLY | "PROXY ONLY" | proxy data present | proxy never implies real source |
| MISSING_DATA_VISIBLE | "MISSING DATA VISIBLE" | missing data present | missing data never hidden |

## Banner Rules

- Banners are informational and review/safe-only; none carries an enabling handler.
- NO_FINANCIAL_ADVICE and NO_SIGNAL_LANGUAGE are always present to reinforce the
  non-advisory, no-signal posture.
- Banners must not contain secrets, env paths, raw vendor data, or public-ready
  claims.
- All banners persist in screenshot-safe mode (they reinforce safety, not hide it).

- test requirement: no value/snippet/length/hash ever rendered.
