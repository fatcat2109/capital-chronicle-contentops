# V6 Next Task Pointer

Current task just completed: `TASK_CONTENTOPS_DAILY_DATABASE_SUPPORT_GAP_REPAIR_PLAN_V0`.

Result:
- Classification: `PASS_WITH_GAPS_DAILY_DATABASE_SUPPORT_GAP_REPAIR_PLAN_V0`.
- Output: Daily database support gap repair plan (Step 3b) generated.
- Identified Gaps:
  - Global Central Bank Liquidity Measures (missing)
  - Japan Yield Curve (JGB) (partial)
  - USD/JPY FX Spot & Volatility (partial)
- Recommended Ingestion & Promotion Tasks:
  - `TASK_TREASURY_FED_NYFED_RATES_LIQUIDITY_CONTRACT_FIXTURE_EXTREME_V1`
  - `TASK_APAC_CHINA_JAPAN_OFFICIAL_MACRO_VALUE_CAPTURE_V1`
  - `TASK_USDJPY_MT5_OANDA_CONTRACT_PROMOTION_V1`
- Invariants:
  - `ready_for_article_draft` remains `false`.
  - No live ingestion, article writing, media generation, or public dispatch was performed.

Evidence:
- Gap repair plan: `docs/automation/DAILY_DATABASE_SUPPORT_GAP_REPAIR_PLAN_V0/database_support_gap_repair_plan_v0.json`
- Gap repair summary memo: `docs/automation/DAILY_DATABASE_SUPPORT_GAP_REPAIR_PLAN_V0/database_support_gap_repair_summary_v0.md`
- Run evidence: `docs/automation/DAILY_DATABASE_SUPPORT_GAP_REPAIR_PLAN_V0/run_evidence_v0.json`

Hard blockers that remain:
- secret, credential, token, cookie, localStorage, sessionStorage, webhook, provider-key, or raw env/session value reads/logs
- main repo/database mutation from ContentOps
- candidate/proxy numeric truth promotion to authoritative
- financial advice, trading signal, recommendation, position sizing, or broker behavior
- public dispatch without explicit operator public override and separate live task
- duplicate/spam publish when duplicate guard fails
- hidden caveats/disclaimers
- scheduler/retry storm
- platform API call unless a separate live-dispatch task explicitly authorizes existing safe adapter paths

Architecture boundary:
- CDP Ingestion = fresh catalyst/headline/event discovery.
- Capital Chronicle local database/exporter = numeric/source/context authority.
- The local database remains in `A:\Capital Chronicle\Headline Raw data local json\capital-chronicle-ingestion`.
- ContentOps = content production, platform adaptation, approval, dispatch gating, and readback.
- Capital Chronicle Analysis Alpha = later core value/intelligence layer, not part of this task.
- ContentOps must not become a second macro database, source fetcher/parser, numeric truth authority, or source-brain.

Recommended next task:
```text
TASK_CONTENTOPS_DAILY_DATABASE_SUPPORT_GAP_INGESTION_EXECUTION_V0
```

Purpose: Execute the localized ingestion/promotion tasks defined in the gap repair plan to populate the main database repository with necessary JGB/FX/Liquidity series.

Out of scope unless explicitly approved:
- Live public dispatch from this task.
- Platform API calls.
- Browser/CDP readback.
- Macro source fetching/parsing inside ContentOps.
- Main repo/database writes from ContentOps.
- Analysis Alpha.
- New ContentOps source-family fixtures.
