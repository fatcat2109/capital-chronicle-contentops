# Institutional Design System and Futuristic Fintech Visual Contract (After 0158)

Task label: TASK_CONTENTOPS_0158_INSTITUTIONAL_DESIGN_SYSTEM_AND_FUTURISTIC_FINTECH_VISUAL_CONTRACT_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Baseline HEAD before this task: 260ae89 — "docs: add institutional ui ux rebuild master plan"
Scope: planning / spec / contract only. This task defines the design-language
authority for future UI implementation. It does NOT implement or modify active
front-end code, does NOT run a backend, does NOT run Antigravity or browser
automation, does NOT read credentials/env, and does NOT call any platform/
provider/network API.

## 1. Owner Decision

The owner has decided to convert the 0157 UI rebuild master plan into a concrete
design-language authority. This visual contract is committed repo authority for
the futuristic-institutional-fintech look and feel of Capital Chronicle
ContentOps. It governs design tokens, semantic status colors, typography/density,
component taxonomy, visual hierarchy, safety banners, blocked-state components,
screenshot-safe/redacted rules, and the handoff to the 0159 view-model contract.

This is a planning/spec/contract task only. It is not active front-end
implementation, not browser QA, and not an Antigravity task.

## 2. Accepted 0157 Baseline

This contract builds directly on the accepted 0157 authority:
- `docs/INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_MASTER_PLAN_AFTER_0157.md`
- `docs/INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_BACKLOG_AFTER_0157.md`
- `docs/INSTITUTIONAL_UI_UX_QUALITY_BAR_AND_ACCEPTANCE_MATRIX_AFTER_0157.md`
- `docs/ANTIGRAVITY_BROWSER_QA_STRATEGY_AFTER_0157.md`
- `schemas/institutional_ui_ux_frontend_rebuild_plan_packet.schema.json`
- `live_contentops/institutional_ui_ux_frontend_rebuild_plan.py`
- `tests/test_institutional_ui_ux_frontend_rebuild_plan.py`

The 0157 master plan section 6 status vocabulary is extended here into the full
0158 semantic status token system (section 7 below). The 0158 design system does
not supersede Telegram live-gate sequencing.

## 3. Design North Star

- Institutional local control terminal: an operator-grade terminal for macro
  research governance and content operations, run locally.
- Futuristic fintech: precise, dense, high-information, restrained. Modern, not
  flashy. Confidence through clarity, not decoration.
- Evidence-first: the interface foregrounds sources, lineage, limitations, and
  data-sufficiency before any polished output.
- Safe-by-default: review-only, not-public-postable, live-disabled, redacted, and
  kill-switch-aware as the default visual state.
- No signal-service posture: no buy/sell/hold, no P&L, no market-direction color,
  no "alpha signal" framing anywhere.

## 4. Brand / Product Posture

Capital Chronicle ContentOps is explicitly NOT:
- a Bloomberg replacement;
- an AI trading bot;
- a signal service;
- an execution system;
- a guaranteed prediction engine.

It IS a local-first, evidence-disciplined macro content operations terminal with
supervised, gated, future publishing. The visual language must continuously
reinforce this posture and never imply trading, execution, or guaranteed calls.

## 5. Visual Principles

1. State before action. Every surface shows its safety/validation state before it
   offers any control. Disallowed controls render disabled + explained.
2. Evidence is the interface. Sources, lineage, limitations, and data-sufficiency
   are primary content, not afterthoughts.
3. Missing stays visible. Missing / DEGRADED / PROXY_ONLY / STALE / UNKNOWN data is
   always shown with a reason. No silent gaps, no collapsing to PASS.
4. Review-only by default. Nothing is public-postable by default. Live posting,
   scheduling, and live adapters render as visually gated, disabled, explained
   future states.
5. Redaction by design. Credentials and secrets are never shown. Only redacted
   status tokens (SECRET_REDACTED / CREDENTIAL_PRESENT_REDACTED) appear.
6. Dashboard is screenshot-safe. Any view can be captured or presented with zero
   secrets, zero env paths, and no false readiness claims.
7. No color-as-market-direction. Red/green are operational PASS/BLOCKED only —
   never bullish/bearish, risk-on/risk-off, buy/sell, P&L, or market direction.


## 6. Design Tokens

Token IDs are stable contract identifiers. Hex values target a dark institutional
terminal and extend the existing `ui/daily_content_studio/styles.css` palette
(`--bg #0f1419`, `--panel #1a2129`, `--text #e6edf3`, `--muted #9aa7b4`,
`--ok #2ea043`, `--warn #d29922`, `--block #f85149`, `--border #30363d`).

### 6.1 Color tokens (base surfaces / text)

| Token | Value | Role |
| --- | --- | --- |
| color.bg.base | #0b0f14 | Terminal background (deepest) |
| color.bg.app | #0f1419 | App canvas |
| color.surface.1 | #141b22 | Card / panel surface |
| color.surface.2 | #1a2129 | Raised panel |
| color.surface.3 | #20272f | Header / sticky bars |
| color.border.subtle | #232b33 | Hairline divider |
| color.border.default | #30363d | Default border |
| color.text.primary | #e6edf3 | Primary text |
| color.text.secondary | #9aa7b4 | Secondary / muted text |
| color.text.disabled | #5b6672 | Disabled text |
| color.focus.ring | #58a6ff | Focus outline (accent, non-semantic) |

### 6.2 Semantic status colors (operational only)

| Token | Value | Role (operational, never market) |
| --- | --- | --- |
| color.status.pass | #2ea043 | PASS (operational success) |
| color.status.degraded | #d29922 | DEGRADED / STALE / caution |
| color.status.blocked | #f85149 | BLOCKED (operational fail-closed) |
| color.status.review | #58a6ff | REVIEW_REQUIRED |
| color.status.locked | #768390 | LIVE_DISABLED / NOT_PUBLIC_POSTABLE / redacted |
| color.status.unknown | #6e7681 | UNKNOWN |
| color.status.proxy | #a371f7 | PROXY_ONLY |
| color.status.redacted | #768390 | SECRET_REDACTED (shield) |

Color is never the only signal: every status renders with a text label and an
icon glyph. Green/red are operational PASS/BLOCKED only.

### 6.3 Typography tokens

| Token | Value |
| --- | --- |
| font.family.sans | -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif |
| font.family.mono | ui-monospace, SFMono-Regular, Menlo, Consolas, monospace |
| font.size.xs | 11px (chips, captions) |
| font.size.sm | 12px (table cells, metadata) |
| font.size.md | 14px (body) |
| font.size.lg | 16px (section titles) |
| font.size.xl | 20px (screen titles) |
| font.weight.regular | 400 |
| font.weight.medium | 600 |
| font.weight.bold | 700 |
| line.height.tight | 1.3 |
| line.height.body | 1.5 |

Monospace is used for IDs, redacted-token references, timestamps, and lineage
references to reinforce the terminal posture.

### 6.4 Spacing scale

space.0 = 0, space.1 = 4px, space.2 = 8px, space.3 = 12px, space.4 = 16px,
space.5 = 24px, space.6 = 32px, space.7 = 48px. Use a strict 4px base grid.

### 6.5 Border / radius rules

radius.sm = 4px (chips, badges), radius.md = 6px (cards), radius.lg = 8px
(panels). Borders are hairline (1px) using color.border.subtle/default. No heavy
shadows used as primary separation; borders define structure.

### 6.6 Elevation / glow rules

elevation.0 = none, elevation.1 = 0 1px 0 rgba(0,0,0,.4), elevation.2 = 0 2px 8px
rgba(0,0,0,.5). Glow is reserved ONLY for the focus ring and never used as a
decorative "live"/hype effect. No pulsing glows on status.

### 6.7 Grid / density rules

12-column fluid grid. Tables are dense and readable: row height 28–32px, 8px cell
padding, sticky headers. Dense but not cramped — minimum 8px between interactive
targets. Default information density is high (institutional), not airy SaaS.

### 6.8 Motion rules

motion.duration.fast = 120ms, motion.duration.base = 200ms. Easing ease-in-out.
Motion is used ONLY for state transitions (expand/collapse, status change) and
focus. No marketing animation, no confetti, no pulsing live glow, no parallax.

### 6.9 Iconography rules

Line icons, 16px/20px, single-weight. Each status token has one assigned glyph
(see status semantics doc). Forbidden icon families: rockets, moons, coins,
flames, bull/bear, casino chips, trade arrows. Icons always pair with a text
label; never icon-only for state.

### 6.10 Chart / visualization rules

Charts are evidence/data-sufficiency oriented (coverage bars, freshness
timelines, completeness matrices). Forbidden: price candlesticks framed as
signals, P&L curves, buy/sell markers, bullish/bearish shading. Charts must show
missing/degraded/proxy/stale segments explicitly and never imply market direction
via red/green.

## 7. Semantic Status Token System

The full 0158 status token system (extends the 0157 section 6 vocabulary). Each
token has one color role, one icon glyph, a text label, and a test requirement.
Full per-token copy/usage is in
`docs/INSTITUTIONAL_STATUS_SEMANTICS_AND_SAFETY_BANNERS_AFTER_0158.md`.

| Token | Meaning (operational) |
| --- | --- |
| PASS | Validated, contract-clean, review-ready |
| DEGRADED | Works but inputs are partial / lower quality |
| BLOCKED | Fail-closed; action not permitted |
| REVIEW_REQUIRED | Awaiting mandatory human review |
| NOT_PUBLIC_POSTABLE | Never public-postable in current state |
| LIVE_DISABLED | Live capability intentionally off |
| UNKNOWN | State could not be determined |
| PROXY_ONLY | Data is a proxy, not the real source |
| STALE | Data is past freshness threshold |
| SECRET_REDACTED | A value exists but is intentionally hidden |
| CREDENTIAL_PRESENT_REDACTED | Credential is present locally; value hidden |
| CREDENTIAL_VALIDATED_NO_POST | Credential validated; posting still not allowed |
| API_VALIDATED_NO_POST | API identity validated; posting still not allowed |
| CHANNEL_PERMISSION_UNVALIDATED | Channel write permission not yet validated |
| DQR_BLOCKING | Data quality / sufficiency is blocking |
| FORECAST_NOT_READY | Forecast-readiness gate not satisfied |
| MANUAL_ONLY | Manual operator action only |
| DRY_RUN_ONLY | Dry-run only; no live execution |
| KILL_SWITCH_ACTIVE | Global kill switch is active |

## 8. Hard Rule: No Market-Direction Color

Red and green (and any color) MUST NOT imply bullish/bearish, risk-on/risk-off,
buy/sell, P&L, or market direction. Red is operational BLOCKED only. Green is
operational PASS only. Amber is operational DEGRADED/STALE only. Any use of color
to communicate market direction is a contract violation and must fail tests.

## 9. Component Taxonomy (Summary)

Full per-component detail is in
`docs/INSTITUTIONAL_UI_COMPONENT_TAXONOMY_AFTER_0158.md`. The contract requires at
least these components:

- Global Safety Ribbon
- Command Center Status Header
- Gate Card
- Blocked Reason Stack
- Evidence Link Card
- Source Lineage Panel
- Data Sufficiency Matrix
- Forecast Readiness Card
- Credential Redaction Badge
- Platform Readiness Card
- Telegram Gate Stepper
- Approval Decision Card
- Audit Timeline
- Draft Inspector Panel
- Claim Risk Panel
- Content Lane Badge
- Publish Disabled Control
- Screenshot-Safe Watermark
- Limitation Strip
- Freshness Chip
- Proxy-Only Warning
- Missing Data Row
- Not Public Postable Banner
- Manual Review Required Banner
- Kill Switch Indicator
- Forbidden Action Tooltip

## 10. Per-Component Fields (Contract)

Every component in the taxonomy doc defines these fields:
- purpose;
- primary data inputs;
- visible states;
- forbidden states;
- required safety copy;
- redaction requirements;
- empty / missing state;
- screenshot-safe behavior;
- test expectation.

## 11. Screen-Level Visual Hierarchy

Each screen leads with its global safety state, then evidence, then any gated
controls. Screens covered:

- Command Center — global posture, kill switch, blocked summary, ready-for-review.
- Content Lane Control — lane separation + lane policy + NOT_PUBLIC_POSTABLE.
- Daily Content Studio — daily run, REVIEW_REQUIRED, source lineage, limitations.
- Draft Inspector — one draft deep: sources, limitations, forbidden-action gating.
- Grounded News Angle Lab — grounded angles, PROXY_ONLY, no signal framing.
- Publish Readiness Tower — dry-run readiness matrix, LIVE_DISABLED everywhere.
- Telegram Pilot Gate — redacted gate status, SECRET_REDACTED, next-gate-required.
- Approval Queue — REVIEW_REQUIRED items, decision history.
- Content Calendar — planning only; never marks public-ready.
- Evidence Vault — sources, lineage, STALE/PROXY_ONLY/UNKNOWN, data sufficiency.
- Visual Export Studio — screenshot/briefing-safe export of redacted views.
- Settings / Safety Policy — read-only posture; all live flags false.

Hierarchy rule per screen: (1) Global Safety Ribbon at top; (2) screen title +
status header; (3) primary evidence/state region; (4) gated controls last, all
disabled + explained.


## 12. Screenshot-Safe Mode

Full rules are in
`docs/INSTITUTIONAL_SCREENSHOT_SAFE_AND_REDACTED_VISUAL_EXPORT_RULES_AFTER_0158.md`.
Summary requirements:
- Redacted fields: all credential/secret values render as redacted tokens only.
- Watermark/label: a "SCREENSHOT-SAFE / LOCAL ONLY / NOT PUBLIC-POSTABLE" label.
- No secrets, no raw env paths, no raw vendor data, no raw platform response, no
  raw request URL.
- No public-ready false claims, no forecast-readiness false claims.
- No hidden limitations — limitations remain visible in safe mode.
- Non-advisory / no-signal labels remain visible.

## 13. Accessibility and Density

- High contrast: text-on-surface meets a strong contrast target; status colors
  always paired with label + icon (no color-only state).
- Readable small text: 11–12px minimums for dense tables, with adequate weight.
- Keyboard navigability target (for later implementation): logical tab order.
- Focus state requirement: visible focus ring (color.focus.ring) on all
  interactive elements.
- No color-only state communication anywhere.
- Compact but not cramped: minimum 8px between interactive targets.

## 14. Forbidden Visual Metaphors

The following are banned everywhere in the UI:
- trade buttons;
- P&L widgets;
- buy/sell chips;
- bullish/bearish arrows;
- "alpha signal" badges;
- rocket/moon visuals;
- casino/crypto aesthetics;
- execution console framing;
- broker/order-routing icons.

These appear in the contract only as a ban list. Any actual implementation of them
is a contract violation and must fail tests.

## 15. Future Handoff

- 0159 view-model contract must bind data to these design tokens, status tokens,
  component IDs, and screen IDs. See
  `docs/INSTITUTIONAL_DESIGN_SYSTEM_HANDOFF_TO_VIEW_MODEL_AFTER_0158.md`.
- 0160 shell prototype may use this design system to build the static shell.
- Antigravity remains future-only until 0167 browser QA.

## 16. Relationship To Telegram Live-Gate Sequencing

This design system does NOT supersede Telegram live-gate sequencing. The Telegram
lane (0152–0156 and any future explicit GO gate) remains the authoritative path
for supervised live posting readiness. The Telegram Gate Stepper and Telegram
Pilot Gate screen are read-only, redacted *displays* of existing gate state; they
never call getMe or sendMessage and never reveal credentials.


