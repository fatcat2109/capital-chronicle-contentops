# Daily Headline Cluster Rank & Article Idea Packet (Step 2)

This module implements Step 2 of the definitive Daily ContentOps loop: loading the captured Step 1 X/CDP headline packet, clustering headlines by topic family, ranking them based on editorial weight and hotness signals, applying topic balance constraints (to prevent premature Crude/WTI repetition), and selecting one downstream article idea brief.

## Operation

- Load normalized headlines from Step 1.
- Cluster by topic family:
  - `macro_policy_rates_liquidity`
  - `energy_commodities`
  - `china_asia_global_trade`
  - `volatility_risk_sentiment`
  - `geopolitics_sanctions`
  - `earnings_equities_credit`
  - `alternative_data_prediction_markets`
  - `crypto_digital_assets`
  - `other_market_structure`
- Rank clusters based on size, source diversity, tag weights, and hot words.
- Gating prevents repeating a stale topic unless there is a major new breaking catalyst (high hotness).
- Select a target idea, output database support requirements, and write the next brief markdown.
- No live publication, platform variants, article drafts, or database queries occurred.

## Verification Details
- **Classification**: `PASS_DAILY_HEADLINE_CLUSTER_RANK_ARTICLE_IDEA_PACKET_V0` or `PASS_WITH_FALLBACK_TOPIC_BALANCE_DAILY_HEADLINE_CLUSTER_RANK_ARTICLE_IDEA_PACKET_V0`.
- **Outputs**:
  - `headline_clusters_v0.json`
  - `article_idea_selection_v0.json`
  - `topic_balance_state_v0.json`
  - `next_article_idea_brief_v0.md`
  - `run_evidence_v0.json`
