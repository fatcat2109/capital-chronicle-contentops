# Database Support Gap Repair Plan

**Idea Title:** Japan's Debt Crisis: Yield and Currency Gap Widens as Intervention Fails
**Selected Idea ID:** idea_macro_policy_rates_liquidity_20260709

## Gap Diagnostics
- **Missing Required Data:** Global Central Bank Liquidity Measures
- **Partial/Candidate Data Only:** Japan Yield Curve (JGB), USD/JPY FX Spot & Volatility

## Required Database Ingestion & Promotion Roadmap

### Global Central Bank Liquidity Measures (MISSING)
- *Status Detail:* Global Central Bank Liquidity Measures: missing, needs exact family definition/source selection before use.
- *Recommended Next Task:* `TASK_TREASURY_FED_NYFED_RATES_LIQUIDITY_CONTRACT_FIXTURE_EXTREME_V1`

### Japan Yield Curve (JGB) (PARTIAL)
- *Status Detail:* Japan Yield Curve (JGB): partial/candidate, needs official source contract hardening or parser/export task.
- *Recommended Next Task:* `TASK_APAC_CHINA_JAPAN_OFFICIAL_MACRO_VALUE_CAPTURE_V1`

### USD/JPY FX Spot & Volatility (PARTIAL)
- *Status Detail:* USD/JPY FX Spot & Volatility: partial/candidate, needs read-only broker/proxy policy/export task or accepted non-exact proxy wording.
- *Recommended Next Task:* `TASK_USDJPY_MT5_OANDA_CONTRACT_PROMOTION_V1`

## Recommended Action Sequence
The recommended first task is a read-only source support verification task:
`TASK_CAPITAL_CHRONICLE_JAPAN_FX_LIQUIDITY_SOURCE_SUPPORT_VERIFICATION_V0`

This task will verify official source contracts and JGB/FX proxy data mappings before any ingestion or drafting is initiated.

## Downstream Article Draft Guidance
Until database gaps are resolved:
1. Downstream article drafts **MUST NOT** be created.
2. `article_draft_blocked` remains `true` and `article_draft_allowed_as_candidate_only` remains `false`.
3. No dispatch or publishing is authorized.
