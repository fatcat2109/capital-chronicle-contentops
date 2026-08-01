# V6 Next Task Pointer

Latest accepted release task: `TASK_CONTENTOPS_V1_0_FINAL_AUCTION_LOGIC_REPAIR_ACCEPTANCE_AND_TAG_V1`.

Completed task: `TASK_CONTENTOPS_FAST_SHIP_EXECUTABLE_SNAPSHOT_REQUIREMENT_SEPARATION_V1`

Classification: `PASS_EXECUTABLE_SNAPSHOT_REQUIREMENT_SEPARATION_V1_AWAITING_CHATGPT_AUDIT`.

Evidence: `live_contentops/freshness_market_state_v2.py`, resolver-to-runtime generic-fabric tests, the committed five-case truth table, focused Python/V5/build validation, and `docs/automation/CONTENTOPS_FAST_SHIP_EXECUTABLE_SNAPSHOT_REQUIREMENT_SEPARATION_V1/final_manifest.json`.

The canonical freshness evaluator now treats market sensitivity and snapshot requirements independently at runtime. Snapshot/ingest blockers use the explicit requirement, absent fields preserve historical sensitivity behavior, and sensitivity remains available for downgrade restrictions. Existing FOMC and Apple SEC true/true plus USGS false/false behavior and all canonical HOLD/no-authority states remain unchanged.

## Required Next Action

`INDEPENDENT_CHATGPT_AUDIT_EXECUTABLE_SNAPSHOT_REQUIREMENT_SEPARATION_V1`

Independently verify the executable five-case freshness truth table, absent-field compatibility, sensitivity-specific downgrade behavior, resolver-to-runtime generic-fabric flow, current FOMC/Apple SEC/USGS backend-UI parity, receipt hashes, status consistency, and no-execution invariants. Do not approve, publish, dispatch, read credentials, access provider platforms, mutate upstream, run scheduler actions, or perform public writes.
