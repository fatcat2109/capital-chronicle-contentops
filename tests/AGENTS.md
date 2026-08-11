# `tests/` — Focused Regression Routing

Tests protect canonical production behavior; they do not authorize runtime, provider, browser,
database, or public actions. Use isolated temporary stores and fixtures only. Never point tests at
the production SQLite path or Runtime output root.

Match the smallest test to the seam:

- launcher/supervisor/store: `test_contentops_daily_app_launcher_v1.py`,
  `test_daily_app_supervisor_v1.py`, `test_durable_operational_store_v1.py`
- intake/preselection/newsroom: `test_contentops_continuous_intelligence_realign_v1.py`,
  `test_preselection_published_memory_breaking_wake_closeout_v1.py`,
  `test_rolling_x_newsroom_cycle_v1.py`
- evidence/article: `test_rolling_x_targeted_evidence_adapter_v1.py`,
  `test_rolling_x_evidence_viability_v1.py`,
  `test_rolling_x_grounded_article_media_builder_v1.py`
- publication/readback: `test_publication_coordinator_v1.py`,
  `test_daily_app_publication_lifecycle_v1.py`,
  `test_daily_app_automatic_readback_housekeeping_v1.py`
- read model/server: `test_daily_app_ui_read_model_v1.py`,
  `test_canonical_production_entrypoint_and_legacy_quarantine_v1.py`
- context generator: `test_codex_context_index.py`

Do not infer full-suite PASS from a focused selection. Graph edges `tests` and `covered_by` identify
exact imports or conservative filename matches; search the symbol/module before broad collection.
