# ContentOps → Main governed headline projection V1

Owner: ContentOps, using canonical ingestion plus existing durable store/outbox/leases.
Schema identifiers: `contentops.main_headline_projection.v1` (page and row),
`contentops.main_report_feed_pointer.v1` (Main producer pointer).
This is an internal exchange contract, not a publication or numeric-authority grant.

## Main consumer and example

The existing Main function `tools.product.continuous_catalyst_trigger_fabric_v1.py::observe_headline_sidecar`
accepts each JSONL row in [manual_main_headline_rows.jsonl](manual_main_headline_rows.jsonl).
[main_consumer_readback.json](main_consumer_readback.json) records an actual bounded call of that
function at pinned Main commit `c8477a035bcb04b3d13bc4f8e26bd651dd9d957d`: two admitted rows,
both `CONTEXT_UPDATE_ONLY`, zero model calls/database writes. Source comparison accounts only
for Git checkout newline conversion. No Main files were changed.

The two rows are retained EIA public source-fact projections from Main's USOIL and XNGUSD
reports. Their `upstream_report_lineage.novel_contentops_reporting=false` is deliberate: they
are not fresh ContentOps headlines, independent confirmation or new intelligence. The 500
sampled canonical X rows remain rejected for missing governed permissions; their bodies are
absent from this export. The earlier 318-row Main inspection was a different bounded sample.

## Row fields and invariants

| Fields | Meaning and validation |
| --- | --- |
| `headline_id`, `headline_text`, `text_sha256` | Stable source identity and exact normalized text hash. Existing hashes must match. No restricted source body is copied. |
| `source_identity`, `reporting_identity`, `source_platform`, `source_url`, `claimed_origins` | Exact retained source/reporting identities and HTTPS locator; reporting identity does not become underlying-event authority. |
| `headline_timestamp`, `known_at_utc`, `retrieval_time_utc`, `revision_at_utc` | Source publication/observation, first known, retrieval and revision clocks. Publication ≤ known ≤ retrieval ≤ cutoff; known ≤ revision ≤ cutoff. `captured_at_utc` is the admitted known clock expected by the existing Main adapter. |
| `rights_state`, `rights_evidence_sha256`, `allowed_consumers`, `permitted_uses` | Retained EIA-original public-domain authority with attribution on an EIA hostname, or an explicit source/text-hash-bound internal permission record. Internal grants must permit provider/model input and an accepted Main consumer. No grant is inferred from canonical X membership or a publisher name. |
| `source_record_locator`, `source_capture_sha256`, `projection_sha256` | Record locator/raw-line hash, retained source capture hash when available, and canonical output seal excluding `projection_sha256`. Locators for rejected input expose hashes and line numbers only. |
| `context_only`, `report_truth_only` | Always true. No event confirmation, Core numeric/forecast truth, performance/alpha claim, trade or broker authority. |
| `public_republication_authority`, `numeric_authority_granted`, `underlying_event_truth_granted` | Always false. Main must preserve these limits downstream. |
| `upstream_report_lineage` | Present for a Main-origin round trip; exact report/version/hash/claim hash and `novel_contentops_reporting=false` prevent miscounting it as independent evidence. |

Official rows are narrowed to `internal_research` and `narrative_context` consumers. For a
non-public record-scoped grant, the output is the intersection of those consumers with the
retained explicit grant. Unknown, missing, blocked, malformed, stale-identity or private records
emit named gaps, not invented permissions. No source-policy or legal authority is created here.

## Page, cursor and recovery

`MainHeadlineExporter.export` writes one immutable page per `batch_id` to
`internal:contentops-main-headline-export`. It uses the existing V1 store and a serial lease.
Each page has `sequence`, `parent_page_sha256`, `page_sha256`, `authority_revision`, exact
counts, bounded gap diagnostics and per-file byte-offset/line/prefix-hash cursors.

- Default bounds: four supplied source files, 500 rows; hard ceilings 16 files / 1,000 rows.
  Each line is bounded to 1 MiB. Partial/oversized lines are deferred without advancing past them.
- Exact repeated batch IDs return the committed page without rescanning. New batches resume
  committed prefixes; changed/truncated prefixes fail visibly. Future records remain pending.
- Content/revision/rights identity prevents duplicate output even when the same row is found in
  a different source location. A crash before the page commit can safely repeat the read; after
  commit the page/cursor is reused. Bulk sidecars and CDP capture are never edited.
- A newly retained rights decision requires a new `authority_revision` to rescan from zero.
  This does not create permission; it merely applies a separately established decision.
- Coverage is `BOUNDED_INCREMENTAL_PREFIXES_NOT_HISTORICAL_COMPLETENESS`; the configured
  latest-four-file window is explicit and is not the full historical corpus.

The JSONL beside `main_headline_projection.json` is the consumer payload. Both artifacts are
produced inside each existing report-enriched newsroom slot. No second scheduler or service
is needed. Main's existing ingestion/dossier/cursor owner decides when to consume these files.

## Main → ContentOps pointer and routine hook

[main_producer_pointer.json](main_producer_pointer.json) pins the Main repository, immutable
commit and four export/schema pairs (USOIL v1/v2 and XNGUSD v1/v2). Main owns those bytes.
The pointer reads Git blobs at the exact commit, not dirty working files. Configure the existing
Simple scheduler process with `CONTENTOPS_MAIN_REPORT_FEED_POINTER=<absolute pointer path>`
when its normal owner later activates it; this work did not set that process environment,
start the process or change schedules.
The existing process re-reads that configured pointer each opportunity. A changed immutable
revision takes effect through the same reader; an unavailable/invalid update is a named gap,
not permission to consume an arbitrary checkout or mutate Main.

One routine slot enriches the normal news pool with pending latest report candidates and
invokes the same Simple owner once. One selector, ≤3 candidates, shared ≤6 source requests,
one writer and ≤1 revision remain unchanged. Deferred reports remain pending for later slots.
Successful controlled output is distinguishable from provider output and does not suppress
fresh-provider eligibility in a later opportunity. Restart reuses the frozen pool and successful
stage results. Correction/withdrawal updates both report history and existing output identities.

An absent pointer keeps the independent Simple path available. An unavailable configured
export is a named feed gap; it does not grant authority or erase independent intake.

## Exact next manual command

This command uses the same bounded draft-only path, with a new isolated store and the existing
pause marker. It will stop at `LLM_OPERATOR_PAUSED` while that marker remains active.

```powershell
python scripts/run_capital_chronicle_intelligence_loop_v1.py --pointer docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal19/main_producer_pointer.json --store C:/Users/bullw/AppData/Local/Temp/goal19-next-manual/store.sqlite3 --output-dir C:/Users/bullw/AppData/Local/Temp/goal19-next-manual/output --opportunity-id goal19-next-manual
```

No fresh provider execution, natural calendar runtime, deployment, public publication or
historical corpus completeness is claimed by the controlled artifacts.
