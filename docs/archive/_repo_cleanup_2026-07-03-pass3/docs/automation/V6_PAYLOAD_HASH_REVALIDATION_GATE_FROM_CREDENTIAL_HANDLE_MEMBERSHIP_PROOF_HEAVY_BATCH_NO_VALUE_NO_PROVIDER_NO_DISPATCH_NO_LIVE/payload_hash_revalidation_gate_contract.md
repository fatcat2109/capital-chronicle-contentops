# V6 Payload Hash Revalidation Gate Contract

## Purpose

This gate is a local deterministic hash identifier consistency task. It consumes accepted symbolic credential handle membership proof records and validates approved payload hash identifiers already carried by those records.

## Accepted Input

Input must use schema version 6.0.0 and the exact credential handle membership proof scaffold task label. The upstream status must be all required credential handle membership proofs available for future payload hash revalidation only. Records must use symbolic credential handle membership proof scaffold only. Required key names must be allowlisted. Symbolic destination binding IDs and symbolic credential handle IDs must be present and symbolic-only. Approved payload preview IDs must be present and safe. Approved payload hashes must be exactly 64 hexadecimal characters. Human review must be required.

## Output

Output may include key names, booleans, symbolic destination binding IDs, symbolic credential handle IDs, source record IDs, platform, approved payload preview ID, approved payload hash, revalidation mode and status, blocker codes, warnings, future eligibility booleans, and packet hash.

## Safety

Approved payload hashes are public audit identifiers. This gate does not compute hashes from payload bodies. It never reads payload bodies, credential values, env values, .env files, secret stores, browser state, provider config, endpoint, webhook, channel, account, token, published link, telemetry, provider APIs, network resources, browser resources, dispatch paths, publication paths, or live send paths.