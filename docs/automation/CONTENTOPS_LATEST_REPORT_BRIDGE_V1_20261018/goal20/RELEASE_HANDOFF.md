# Goal 20 — original evidence and evolving public report feed

Status: `REAL_MAIN_HANDOFF_VERIFIED_SCOPED_DELIVERY`.
Owning checkpoint: [existing bridge handoff](../../CONTENTOPS_CAPITAL_CHRONICLE_LATEST_REPORT_BRIDGE_V1_20261018.md).
Base: merged PR87, master `45f9b0ebf209930e904085cf56bd4470a99c6501`.
Scoped draft PR: [#88](https://github.com/fatcat2109/capital-chronicle-contentops/pull/88).

## Current result and proof boundaries

| Required result | Direct evidence and limit |
| --- | --- |
| Immutable Main handoff | Main PR232 repair commit `c27b88db396adce2f78d96b33331fccc2925cd0c` matches fresh remote branch and PR head. [Source identity](real_main_handoff/source_identity.json). All **9** declared public example files match their exact Git blobs and the configured public root. Manifest/schema/handoff bytes are retained in [real_main_handoff](real_main_handoff/producer-handoff.json). No private Main report/account path was read. |
| Real cold start and restart | [Actual receipt](real_main_handoff/receipt.json), observed `2026-10-19T08:38:34.420849Z`: **2 newly received manifest records = 1 ancestor-only + 1 editorial-ready child**. USOIL v1 is `LINEAGE_ONLY_NOOP`; USOIL v2 is `ADMITTED` and is the only pending editorial report. Reopening the same isolated store yields **0 new records**, two `DUPLICATE_NOOP` events, unchanged receipt count 2 and zero gaps. No fresh draft/provider proof is claimed. |
| Explicit compatibility | Main manifest schemas **1.0.0 and 1.1.0** have distinct pinned exact byte hashes. Unknown versions fail closed. `REPORT_ANCESTOR` binds `report-ancestor:<original hash>` to the original `envelope_event_id`; both manifest and public projection forbid editorial/publication intent. Ancestors never enter the writer queue, even if they contain public claims. Original report/envelope bytes, hashes and cutoffs remain unchanged. |
| Changed-seam recovery | Fixed the reproduced interruption after an accepted receipt but before supersession status projection. Duplicate scanning finishes that projection without another receipt/draft/provider call. Controls cover descendant-before-parent arrival, append-only 1.0→1.1 history upgrade, missing/contradictory parent, withdrawal, interrupted withdrawal and interrupted admission. **68 focused tests passed**; the revised nine-test manifest subset and [retained exact Main regression](real_main_handoff/exact_main_regression.txt) passed. Exact-head CI covers the final source. |
| Independent useful evidence | Three retained propositions: EIA small-scale solar, EIA grid peaks and BLS CPI. Exact source/policy bytes or separately identified BrowserOS rendered bytes, text spans, identity, clocks and permission hashes are verified by `RetainedSourceResearch`. [Existing retained research](retained_research/index.json). |
| Verified source permissions | Caller-supplied hostnames/rights/flags cannot authorize Main export. Two supported agency-authored text policies are verified from retained captures; photographs, trademarks and third-party works are excluded. Main claims inherit only their exact durable public contract. Unknown X rights remain blocked. |
| Main context return | [Existing Main adapter readback](main_consumer_readback.json): **5 context-only projections = 3 independent + 2 Main-origin recirculations**. Zero model/DB calls or Main edits by this consumer work. Recirculation earns zero independent credit. |
| Existing single newsroom | [Existing connected receipt](acceptance/receipt.json): **5 controlled drafts, 40 native previews, 4 source-backed media artifacts, 10 injected callbacks, 0 fresh provider calls, 0 public writes**. Independent and Main asset inputs share the established Simple selection/writer/validator/compiler. The grid article uses two independently captured documents. Repeat opportunities add no callbacks. This earlier controlled proof is reused, not relabelled as a fresh Main draft. |
| Substantive media and workspace | Three source cards and one source-bound chart of six reported grid observations. [Workspace](acceptance/workspace.json), [desktop](visual/desktop.jpg), [mobile](visual/mobile.jpg), [native previews](visual/native-previews.jpg). All four rendered media were inspected. Mobile width and scroll width were both 430. Originality, conversion, dated freshness, controlled/provider state, permissions, pause and withdrawal remain visible. Existing UI tests/build and render proof are reused because this continuation changes no UI/media source. |
| Existing scheduler and release | The existing Simple scheduler invokes `MainReportFeed.opportunity` through the four existing windows. No new scheduler/store/writer/publication owner. Runtime configuration, schedule and pause were not changed. The exact continuation command and stable root binding are below. |

## Exact real public lineage

Main owns the wire and public export. Current manifest:
`af7b7eb84e2ff17a66236a2e2311f19b62878309f2a46cbc2722e2869c3af911`.
New manifest schema byte hash:
`bcc960b58953980de704e52b58f43611e52d6a6a83d73d0b65663ec60ac0f954`.
The old 1.0 schema remains unchanged and separately supported.

- Ancestor USOIL v1: `61f08ae0b2bb680ee6c04751fc480106eac0e72b624628ad5814ce928951e02d`, original cutoff `2026-10-18T17:05:18.499399Z`, no public claims and no editorial intent.
- Child USOIL v2: `709b20e83caa5c01f94f21f05ef83adcff219b5a94373e8c9782cba9b01cd43d`, original cutoff `2026-10-19T05:56:21.511006Z`, exact parent hash above, editorial-ready.
- The historical Goal19 parent `797f3132e40f486036fc318cab8acf7b9288715035d90c4b3e82705fb17a3f1a` was not substituted.

`goal20_new_main_manifest_records=2`; `goal20_ancestor_only_records=1`;
`goal20_new_main_editorial_events=1`; `restart_new_records=0`.
These are manifest admission counts, not fresh articles, model calls or publication counts.
The actual isolated SQLite store remains at
`C:/Users/bullw/AppData/Local/Temp/goal20-real-main-c27b88db/isolated-proof.sqlite3`;
its public inputs and receipt are retained here for replay. SQLite itself is not committed.

Earlier [schema mismatch](main_owner_example_readback.json) and
[missing-parent readback](immutable_main_handoff_readback.json) remain historical evidence of the
pre-repair failure. They are superseded for current admission by the actual receipt above.
The original local compatibility control fixture remains labelled as a control, not a real handoff.

## Acquisition and authority limits

EIA documents used the existing bounded official evidence loader. BLS returned HTTP 403; the
existing BrowserOS recovery captured only its registered release `pre` subtree, with policy
captured separately. Rendered Markdown and canonical text have distinct hashes and never stand
in for raw HTTP bytes. No login/session/cookie/model/public action was used.

Retained research revision time is the capture/admission clock; the publisher revision clock is
not independently verified. Historical observations do not establish current market state. The
chart compares peaks from different dates and proves no causal attribution, forecast or price view.
The existing attributed-report and canonical-X epistemic routes and bulk CDP owner remain in place.

The bounded [canonical sidecar scan](manual/receipt.json) inspected 500 rows with 500 retained
missing-permission gaps. Independent verified acquisition and exact Main facts still supplied
5 permitted projections. Seven-article published memory was query-only and unchanged.

## Four existing windows and exact continuation

The four existing windows remain 17:00, 21:00, 23:00 and following 01:00 Bangkok under the existing
production day. One reviewed configuration selected by `CONTENTOPS_MAIN_REPORT_FEED_POINTER`
can use the stable root below; future report events require no manual per-article Git pointer edit.
This continuation did not install or activate that binding.

```json
{
  "schema_version": "contentops.main_public_export_binding.v1",
  "producer_repository": "https://github.com/fatcat2109/Headline-Raw-data-json",
  "export_root_id": "capital-chronicle-public-analysis-reports-v1",
  "public_export_root": "A:\\Capital Chronicle\\Runtime\\MainPublicReports-v1",
  "research_root": "<reviewed retained research directory>"
}
```

The exact command used for the real acceptance was:

```powershell
python scripts/verify_capital_chronicle_public_handoff_v1.py --producer-checkout 'A:\Capital Chronicle\capital-chronicle-goal17-asset-reports-20261018' --producer-commit c27b88db396adce2f78d96b33331fccc2925cd0c --output-dir 'C:\Users\bullw\AppData\Local\Temp\goal20-real-main-c27b88db'
```

A replay requires a **new** output directory; earlier evidence is preserved. The verifier reads
only fixed public Git paths and their exact matching configured export files, checks the known
schema, cold-starts one isolated store and reconstructs its consumer for restart replay. It also
checks the existing pause marker remains active with unchanged bytes.

Persistent LLM pause was active and unchanged. Fresh provider calls, broker/public writes and
runtime/schedule starts are all zero. No self-merge/deployment or private Main/DB-owner change.
Prior task-local preview server cleanup/render proof is reused; user applications were untouched.
Fresh provider, natural-calendar runtime and deployment remain unproven and outside this continuation.

## Delivery and synchronization

Source/evidence commit `a8894effa44d72950e4e91868c33bdfdd4fad7c9` was pushed to PR88.
The staged/committed consumer Git blobs and all nine public evidence hashes match the actual
acceptance. The existing CI owner refreshed CodeGraph in commit
`bfae9d308edd717363cd46a599429549ec9db9f7`; its source epoch is `a8894effa44d72950e4e91868c33bdfdd4fad7c9`
and source digest is `585bc7d4ad18c0b5705004ddb7c1fd2b49e14d25e099935040d582867ebd706c`.
Final exact remote/PR head and its CI run are recorded in PR88's final verification section;
that check must be green before the goal is closed. This handoff's final update changes docs only.
The real producer-to-consumer receipt above establishes admission independently of CI.
Control Tower synchronization remains pending its separate serial owner; this checkpoint/PR supplies a
durable, discoverable handoff and claims no shared database/status-owner mutation or credit.
