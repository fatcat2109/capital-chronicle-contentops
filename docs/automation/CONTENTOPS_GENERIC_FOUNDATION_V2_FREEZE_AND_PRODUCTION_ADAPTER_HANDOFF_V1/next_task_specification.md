# Exact next task specification

Task: `TASK_CONTENTOPS_PRODUCTION_ADAPTER_BATCH_TREASURY_YIELD_CFTC_COT_AND_FED_H41_V1`

Starting authority: the committed ContentOps HEAD produced by `TASK_CONTENTOPS_GENERIC_FOUNDATION_V2_FREEZE_AND_PRODUCTION_ADAPTER_HANDOFF_V1` on `master`; read-only upstream `fatcat2109/Headline-Raw-data-json` must be freshly fetched and pinned before work.

Implement exactly three versioned, no-write production adapters over already committed bytes:

1. U.S. Treasury daily yield-curve Atom/XML.
2. CFTC Commitments of Traders legacy CSV.
3. Federal Reserve H.4.1 ZIP/XML.

For each family, append a new immutable extractor record and required artifact schema to versioned registries, extend the verifier allow-list under a new registry version/hash, implement adapter-owned selectors/shape/timestamp/feature derivations, and pass the production adapter conformance harness. Preserve every frozen semantic file from the freeze manifest byte-for-byte. Treat external evidence as at most `OFFICIAL_VERIFIED` plus `CONTEXT_ONLY`; do not upgrade reporting permission. Keep H.4.1 numeric values quarantined unless its committed schema/field evidence independently qualifies them.

No live fetch, credentials, provider/browser access, publication, dispatch, DQR/source/claim authority mutation, scheduler/editorial mutation, production calibration, or upstream write. Finish with focused tests, all V2/V1 compatibility tests, deterministic replay, evidence, status reconciliation, explicit-path commit/push, remote parity, and honest CI truth.
