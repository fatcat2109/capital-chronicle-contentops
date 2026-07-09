# Database Support Gap Repair Plan Memo

**Idea Title:** Japan's Debt Crisis: Yield and Currency Gap Widens as Intervention Fails
**Selected Idea ID:** idea_macro_policy_rates_liquidity_20260709

## Gap Diagnostics
- **Missing Required Data:** Global Central Bank Liquidity Measures
- **Partial/Candidate Data Only:** Japan Yield Curve (JGB), USD/JPY FX Spot & Volatility

## Required Database Ingestion & Promotion Roadmap

### Global Central Bank Liquidity Measures (MISSING)
- **Recommended Ingestion Task:** `TASK_TREASURY_FED_NYFED_RATES_LIQUIDITY_CONTRACT_FIXTURE_EXTREME_V1`
- **Action Required:** Implement local rates and liquidity database ingestion sidecars to fetch NY Fed, SOFR, and H.4.1 balance sheet metrics.
- **Target Authority:** Capital Chronicle local database
- **Complexity:** Medium

### Japan Yield Curve (JGB) (PARTIAL)
- **Recommended Ingestion Task:** `TASK_APAC_CHINA_JAPAN_OFFICIAL_MACRO_VALUE_CAPTURE_V1`
- **Action Required:** Promote BOJ official macro contracts and execute localized value capture scripts to verify real JGB yield curve values.
- **Target Authority:** Capital Chronicle local database
- **Complexity:** Medium

### USD/JPY FX Spot & Volatility (PARTIAL)
- **Recommended Ingestion Task:** `TASK_USDJPY_MT5_OANDA_CONTRACT_PROMOTION_V1`
- **Action Required:** Perform source review and promote MT5/OANDA practice FX contracts from candidate-only metadata to cleared numeric truth status.
- **Target Authority:** Capital Chronicle local database
- **Complexity:** Low

## Downstream Article Draft Guidance
Until these database gaps are closed by the ingestion tasks above:
1. Downstream article drafts **MUST NOT** make exact numeric claims about Yen/JGB rates.
2. Market movements must be described as qualitative background or operator-supplied metrics with clear source caveats.
3. Live dispatch/publishing remains locked.
