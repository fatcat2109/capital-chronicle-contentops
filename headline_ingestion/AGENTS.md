# `headline_ingestion/` — Canonical Headline Sidecar Scope

This scope owns the ingestion implementation and the append-only canonical headline sidecars.
`Data_Ingestion.py` is called by `live_contentops.continuous_headline_ingest_v1`; it is not a
second scheduler or newsroom.

## Canonical seams

- ingestion implementation: `Data_Ingestion.py`
- canonical sidecar root: `data/intake/headline_sidecars/`
- supervisor lane: `../live_contentops/continuous_headline_ingest_v1.py`
- rolling loader: `../live_contentops/newsroom_assignment_scheduler_v1.py`

Preserve stable post/tweet identity deduplication, source-event time, append-only daily naming,
restart safety, untrusted-text handling, and zero-LLM intake. Chrome CDP 9222 is ingestion-only;
never create/clone/reset its profile or inspect session material.

Do not revive `capital_chronicle_ALL_DATA.json` or timestamp-per-capture files as current truth.
Raw archives and sidecar data are runtime/data artifacts and intentionally excluded from the
generated graph. Test routing starts at
`tests/test_contentops_continuous_intelligence_realign_v1.py` and
`tests/test_preselection_published_memory_breaking_wake_closeout_v1.py`. Search the graph for
`continuous_headline_ingest_v1` and `load_rolling_x_headline_sidecars`.
