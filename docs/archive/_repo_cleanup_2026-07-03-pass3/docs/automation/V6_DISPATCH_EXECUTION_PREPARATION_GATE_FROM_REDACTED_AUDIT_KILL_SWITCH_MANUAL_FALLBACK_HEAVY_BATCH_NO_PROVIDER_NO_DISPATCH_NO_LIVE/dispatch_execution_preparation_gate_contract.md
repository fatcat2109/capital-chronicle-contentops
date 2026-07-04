# V6 Dispatch Execution Preparation Gate Contract

## Purpose

This gate is a local deterministic dispatch-preparation task. It verifies accepted redacted audit, symbolic kill-switch, and symbolic manual-fallback records and emits redacted symbolic non-executable preparation metadata. It is not dispatch execution.

## Accepted Input

Input must be a redacted audit kill switch manual fallback gate bundle using schema version 6.0.0, the exact upstream task label, ready-for-future-dispatch-preparation-only status, preparation eligibility true, generic dispatch and live eligibility false, no unsafe flags, empty blockers, and human review required true.

Redacted audit records must be local audit-safe metadata only, complete, use approved payload hashes, safe approved payload preview IDs, symbolic destination binding IDs, symbolic credential handle IDs, allowlisted key names, and false unsafe flags.

Kill switch records must be required, symbolic local, armed for future dispatch preparation only, able to prevent future dispatch execution, dispatch execution still not allowed, and false unsafe flags.

Manual fallback records must be required, symbolic manual fallback, available redacted for future dispatch preparation only, available for operator, instructions redacted, and false unsafe flags.

## Preparation Output

Preparation records are non-executable redacted symbolic metadata only. They may include source record IDs, platform label, required key name, approved payload hash, approved payload preview ID, symbolic destination binding ID, symbolic credential handle ID, redacted audit envelope ID, redacted audit packet hash, kill switch state, manual fallback state, provider family label only, dispatch method family label only, and future requirements for provider scope, payload rehydration, credential hydration, destination binding, final operator GO, and human review.

They must not include provider endpoints, methods, URL paths, destination binding values, destination channel values, destination account values, credential values, credential handle values, payload bodies, public links, telemetry, browser profiles, executable request artifacts, retry policies, schedulers, background workers, or live-send controls.

## Eligibility

`eligible_for_future_provider_scoped_dispatch_execution_task` can be true only when upstream input is valid, all required preparation records are available, and all unsafe flags are false.

`eligible_for_future_dispatch_execution_task`, `eligible_for_live_send_now`, `dispatch_allowed`, `live_send_allowed`, `publication_ready`, and `runtime_truth` remain false in every case.
