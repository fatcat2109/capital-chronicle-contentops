# Institutional Antigravity Browser QA Strategy (After 0168)

Task label: TASK_CONTENTOPS_0168_ANTIGRAVITY_BROWSER_QA_STRATEGY_AND_MANUAL_RUNBOOK_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Baseline HEAD: dc57892 — "test: harden institutional shell before antigravity qa"

Strategy/runbook/evidence-contract only. This task defines what a future browser/
Antigravity QA pass is allowed to inspect and forbidden to do. It does NOT execute
browser QA. No browser was opened, no automation ran, no Antigravity ran, no
screenshots/exports were generated, no env was read, no APIs were called.

## 1. Purpose Of Future Browser QA

- Verify local static rendering only.
- Verify navigation coverage visually across all 12 screens.
- Verify visible labels, watermarks, and redaction surfaces.
- Verify disabled controls are visibly disabled.
- Verify layout and readability.
- Verify no accidental live/post/export affordance.
- Verify screenshot-safe surfaces.
- Verify evidence/limitation/freshness surfaces.

## 2. Non-Goals (Explicitly Out Of Scope)

- No backend functionality testing.
- No live platform testing.
- No Telegram testing.
- No provider/LLM testing.
- No credential testing.
- No network testing.
- No publishing/scheduling/export testing.
- No market-data validation.
- No screenshot capture unless separately authorized.

## 3. Allowed Browser Target

- Local file only: `ui/institutional_shell/index.html`.
- `file://` manual open only, unless a future task explicitly allows a local static server.
- No remote URL, no platform login.
- Avoid any browser profile that carries credentials.
- No devtools network calls required or permitted.

## 4. Explicit Forbidden Actions

open external sites; use network; submit forms; click any live/publish/connect/
export/API controls; run console scripts; paste secrets; read env; capture
screenshots; upload screenshots; save images/PDFs; post to platforms; schedule
posts; call Telegram; use platform credentials; scrape metrics; mutate evidence;
refresh Project Sources.

## 5. Cline vs Antigravity Role Split

- Cline builds and validates architecture/code/tests (0157–0167 already done).
- Antigravity is weaker for architecture/building and is used only for browser QA
  after Cline produces a testable static UI.
- Antigravity must not design architecture, broaden scope, call platform APIs, or
  inspect secrets.
- Antigravity prompt must be narrow, screen-by-screen, expected-state based.

## 6. Future Next Task (Not Self-Authorized)

This strategy does NOT self-authorize browser QA. Next allowed action:
AWAIT OPERATOR/CHATGPT_AUDIT_OF_0168_RUNBOOK_EVIDENCE_BEFORE_ANY_BROWSER_OR_ANTIGRAVITY_TASK

A future possible task may be named only after an explicit operator/ChatGPT GO:
TASK_CONTENTOPS_0169_OPERATOR_APPROVED_ANTIGRAVITY_BROWSER_QA_LOCAL_STATIC_SHELL_V0

## 7. Validation Surface

- Schema: `schemas/institutional_antigravity_browser_qa_strategy_packet.schema.json`.
- Validator + summary: `live_contentops/institutional_antigravity_browser_qa_strategy.py`.
- CLI summary: `python -m live_contentops.cli pre-alpha-institutional-antigravity-browser-qa-strategy-summary`.
- Tests: `tests/test_institutional_antigravity_browser_qa_strategy.py`.

## 8. Relationship To Telegram Live-Gate Sequencing

This strategy does NOT supersede Telegram live-gate sequencing. No live action is
enabled. Browser/Antigravity QA remains deferred and requires a separate explicit
operator/ChatGPT GO.
