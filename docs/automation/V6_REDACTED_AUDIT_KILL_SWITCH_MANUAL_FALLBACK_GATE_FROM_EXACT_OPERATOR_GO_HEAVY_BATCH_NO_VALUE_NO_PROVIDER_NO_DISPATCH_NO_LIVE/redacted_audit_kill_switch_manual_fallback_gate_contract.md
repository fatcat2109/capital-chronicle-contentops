# V6 Redacted Audit Kill Switch Manual Fallback Gate Contract

## Purpose

This gate is a local deterministic safety-envelope task. It verifies accepted exact operator GO records and emits redacted audit metadata, symbolic local kill-switch proof, and symbolic manual-fallback proof. It is not dispatch execution.

## Accepted Input

Input must be an exact operator dispatch GO gate bundle using schema version 6.0.0, the exact upstream task label, status exact operator GO declaration matched for future redacted audit, kill switch, and manual fallback only, non-empty records, no blockers, human review required true, and all unsafe flags false.

Each exact GO record must use mode exact operator GO declaration match only, matched status, phrase exact match true, future redacted audit eligibility true, valid approved payload hash identifier, safe preview ID, symbolic destination binding ID, symbolic credential handle ID, allowlisted key name, human review required true, and false value/env/provider/network/browser/dispatch/live flags.

## Redacted Audit Envelope

The redacted audit envelope may include source bundle IDs, source record IDs, upstream task labels, approved payload hash identifiers, approved payload preview IDs, symbolic destination binding IDs, symbolic credential handle IDs, required key names, platform labels, safety booleans, blocker codes, warning codes, and local audit packet hash.

It must not include credential values, env values, destination values, payload bodies, published links, telemetry values, provider config, browser state, secret paths, secret-derived fragments, or executable request artifacts.

## Symbolic Kill Switch

The kill switch proof is symbolic and local only. It records that a kill switch is required, symbolic local mode is required before dispatch execution preparation, state is armed for future preparation only, and dispatch execution is still not allowed.

## Symbolic Manual Fallback

The manual fallback proof is symbolic and local only. It records that manual fallback is required, symbolic manual fallback mode is required before dispatch execution preparation, fallback is available for the operator, and instructions are redacted.

## Eligibility

Future dispatch execution preparation eligibility can be true only when upstream exact GO is valid, audit records are complete, kill switch records are symbolic and armed, manual fallback records are symbolic and available, and no unsafe flags are true.

Future dispatch execution, publication readiness, dispatch allowed, live send allowed, live send now, and runtime truth remain false in every case.
