# Capital Chronicle → ContentOps publication interoperability requirements V1

Authority inspected: read-only `fatcat2109/Headline-Raw-data-json` `main` at
`7819ad53347bab6ae5023233b20c48ebb222bd60`. The upstream checkout remained unchanged and clean;
no Capital Chronicle database was opened and no upstream file, branch, runtime, provider, or
publication surface was mutated.

## Exact observed coverage

The failed-day universe contains 40 attempted stories: 18 `general_public_event`, 11
`market_move`, 7 `regulatory_fiscal_event`, 2 `data_release`, and 2 `geopolitical_event`. It also
contains 453 held identities, but the committed failed-day artifacts do not assign story families
to those held identities. Therefore this audit does not fabricate a family-coverage denominator
for the held set.

The exact upstream commit contains one `capital_chronicle.publication_evidence_packet.v1` packet,
`cc-publication-73ff151c3d3094741b6c`, for the July 13 Treasury curve. At the audit cutoff it was
962.648 hours old, contains no `rolling_x_story_binding`, and matches none of the 40 attempted
stories or 453 held identities. Current realized coverage is consequently **0/40 and 0/453**.

The supported `story_scoped_publication_evidence_v1` family names 20/40 failed stories as
family-compatible—11 market moves, 7 regulatory/fiscal events, and 2 data releases. That is a
future packet-production ceiling in this observed universe, not current packet availability,
claim permission, or authority. Other upstream families remain explicitly context-only or
blocked pending authority mapping:

- `governed_point_in_time_handoff_v1`: 13/40 family-compatible; reporting permission, public URL,
  and unit/metric mappings are missing.
- `official_catalyst_sidecars_hb8`: 11/40 family-compatible; context only, with story-scoped
  reporting authority absent.
- `headline_and_x_sidecars`: 13/40 family-compatible; context only and not source clearance.
- `macro_state_phase_b`: 13/40 family-compatible; context only and not forecast/reporting authority.
- `weather_energy_sanctions_trade_calendar`: 11/40 family-compatible; timestamp, claim permission,
  and citation mappings are missing.

## Reuse boundary

No parallel store, parser, authority system, or ContentOps-specific Capital Chronicle product is
warranted. A future upstream-authorized implementation should reuse:

- Capital Chronicle `publication_evidence_fabric_v1.build_publication_packet` for exact official
  bytes, claims, citations, freshness, and story permission;
- Capital Chronicle `newsroom_candidate_pool_v1.build_candidate_pool` for fail-closed candidate
  projection and relationship identity;
- `NEWSROOM_CANDIDATE_SOURCES_V1` for source-family status and forbidden promotions;
- ContentOps `capital_chronicle_data_catalog_v1` for read-only governed-surface discovery;
- ContentOps `cc_evidence_bridge_v2` for lossless compatible packet projection;
- ContentOps `cc_publication_authority_v1` for exact story/consumer/use resolution; and
- the canonical targeted-evidence adapter for current freshness, capability, claim, and source
  acceptance.

## Minimum producer contract

For a packet to improve sourceability and remain eligible for ContentOps evidence use, every
future packet must provide all of the following without changing the existing authority boundary:

1. Exact story binding: `rolling_x_story_binding.cluster_id`, ordered `headline_ids`, and
   `request_logical_hash`. Topic similarity, family compatibility, a duplicate key, or an old
   packet is insufficient.
2. Point-in-time timestamps: packet generation/as-of time, event time, document publication time,
   claim observation time, claim known-at time, and retrieval time. Current readiness is evaluated
   again by ContentOps at consumption.
3. Exact source provenance: public source/data URLs, publisher/document identity, raw-byte hash,
   rights state, source health, and parse result.
4. Exact claim mapping: stable claim ID, metric, value, unit, source identity/URL, authority scope,
   claim-level public permission, and citation map. ContentOps and models may not repair or infer
   missing numeric or citation authority.
5. Exact consumer/use permission: `contentops_publication`, story-scoped `ALLOW`, reporting allowed,
   `llm_numeric_authority=false`, no packet blockers, and no global DQR override.
6. Capability declaration: an explicit `provided_evidence_capabilities` projection describing
   which unchanged ContentOps evidence requirements the exact packet material can satisfy. The
   canonical adapter remains the final verifier and may reject the declaration.

The current V1 schema requires at least four numeric claims, so it is demonstrably suited to the
existing Treasury-style numeric packet. It must not be treated as a generic nonnumeric authority
surface. Any future compatible successor remains an upstream owner decision and must preserve the
essential authority semantics already enforced by the ContentOps compatibility seam.

## Expected utility and non-claims

Fresh, exact, story-bound packets could move up to the observed 20/40 family-compatible stories
earlier in sourceability ranking and may avoid redundant public retrieval or research calls. Exact
request, token, latency, or cost savings are **unmeasured** until such packets exist and the same
frozen universe is replayed. Absence or rejection of a packet remains non-vetoing: ordinary
latest-web journalism may continue through separately acquired public evidence.

Machine evidence: `cc_publication_interop_audit_v1.json` with audit SHA-256
`9676450c76cbd4b4d22cf2e2aaa51d509225b178dde1b049a6d2f10fac463c6e`.
