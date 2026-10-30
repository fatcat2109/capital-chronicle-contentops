# Local subscriber Markdown formats

This is Jim's bounded publisher task from 30 October 2026. It renders structured JSON
into local Markdown; it never starts an editorial pipeline, activates a schedule,
creates a Substack draft, invokes a model or writes to a platform. Existing production
pause controls stay in force. Samples use conspicuously labelled fictional figures.

Run from the ContentOps checkout in PowerShell:

```powershell
python -m live_contentops.local_subscriber_markdown_v1 `
  --input tests/fixtures/local_subscriber_markdown_v1/event_card.json `
  --publication-contract 'A:/Capital Chronicle/Main App/tools/product/subscriber_publication_v1.py' `
  --output-dir docs/publisher/LOCAL_SUBSCRIBER_MARKDOWN_V1/samples
```

Replace the input filename with `auto_delta.json`, `saturday_ledger.json` or
`week_ahead.json` for the other pieces. Each produces Markdown and a local QA sidecar.
The output path is required; live/private Runtime trees, UNC targets, escaping links
and relocated production stores are refused. No default production store is opened.

## Input and omission contract

The four JSON fixtures are complete, runnable examples. `schema`, `format`, `piece_id`,
`title`, `sources`, `fields` and `content` form the small renderer input. This is a local
presentation contract, not a change to Main's producer, source rights or live feed.

Each statement has a `template`, such as `The supplied change is {actual} jobs.`.
Placeholders resolve only exact entries in `fields`. Each entry requires a scalar
`value`, an exact `publication_field` in the existing subscriber `FIELD_ALLOWLIST`,
a `source` identifying a source record and a matching `rights_tag`. The source record
requires provider, dataset family, authority class and a source reference. A tag alone
cannot grant rights: the source must match a code-owned publication rights contract.
Private/unclassified, explicitly refused, FRED-derived and raw broker sources fail closed.

The renderer reads the existing Main owner's allowlist and source-rights constants as
Python AST **data**. It executes no Main code and changes no Main file. The test-only
policy excerpt makes portable fixture tests possible; it is not a new rights owner.
The local check against the actual owner guards drift where that checkout is available.

| Format | Supplied content | Existing allowlisted numeric leaves |
| --- | --- | --- |
| Event Card | Scenario conditions, percentages, pricing, reference levels, invalidation | `internal_model_expectation`, `prior_pricing`, `expected_reaction_path` in `subscriber_relevant_view` |
| Auto-delta | Matched scenario, official figures, change versus prior pricing | `new_evidence_change`, `market_consensus_surprise`, `prior_pricing` in the same view |
| Saturday Ledger | Every supplied call, DEMO trade, loss and no-trade, including its cause | `paper_mark_maintenance.latest_closed.net_result_units` and `numeric_authority` |
| Week Ahead | Every supplied event, release time, prior pricing and watch condition | `event_reference_period` and `prior_pricing` in `subscriber_relevant_view` |

These are exact existing leaves, not wildcard extensions. A probability is explicitly
an upstream estimate, not official data or independent model confirmation. A producer
must supply the actual field meaning; changing its label cannot turn a quote, account
fact or price-unit PnL into an admitted scenario or risk unit. No live Main adapter is
implemented or claimed by this fixture-backed renderer.

A literal digit anywhere in a statement template drops the **whole statement**, even
if another digit in it is tagged. Numeric text, instrument names and dates therefore
also use placeholders. Unicode digits are covered. Missing, nonfinite, untagged,
non-allowlisted or rights-blocked referenced fields drop the whole affected statement.
Omissions appear in the QA sidecar by first cause; absent pricing is not invented.
Values are escaped as plain text, not interpreted as HTML or Markdown links.

Scenario probabilities must be sourced percentages within range. A complete set must
sum to the percentage whole; an incomplete set remains incomplete, without normalizing
the surviving values. This layer never estimates probabilities or what is priced.
Official-release statements require an official-actual source, not derived commentary.
Execution wording is refused: these templates provide no entry, stop-loss or target
instructions. They are not an execution or recommendation surface.

An R result must be explicitly supplied in `R`, together with a separately sourced,
positive denominator marked `role: initial_risk` and carrying its original non-R unit.
The renderer computes neither risk nor PnL. A balance or another positive number cannot
stand in for initial risk. Missing denominators remain unavailable. A no-trade has no
realized R; it is never fabricated as a zero-R trade. Every supplied ledger row remains
visible with its cause, even when its numerical result cannot be shown.

## Existing state owners, local isolation

Local rendering reuses `idempotency_policy.compute_idempotency_key` and the existing
`ContentOpsDurableStore` work-item, outbox, readback and reconciliation tables. The small
SQLite file in the chosen output directory uses the existing schema; it is not another
publisher or production database. Outbox destinations and statuses are explicitly local
and non-dispatchable. No publication coordinator or adapter is instantiated.

An identical input/policy/destination reuses the same outbox identity and immutable
Markdown. A changed admitted input gets a different immutable revision. Complete files
are flushed before atomic exclusive visibility; a disk interruption resumes with the
same outbox. Existing different bytes are refused, never overwritten. Every replay
reads back the actual local bytes. That readback establishes local file integrity only;
it supplies neither a platform object identity nor publication evidence.

The QA sidecar retains the contract hash, fields actually referenced, source/rights
bindings and omissions. Input JSON remains the exact value/source evidence. Required
source-contract disclaimers remain; no discretionary repeated source links are added.

Validation:

```powershell
python -m pytest tests/test_local_subscriber_markdown_v1.py tests/test_idempotency_policy.py -q
```

Future production integration still needs the approved Main input binding, real sourced
probabilities/pricing/ledger coverage, the existing final editorial review and a separate
Jim/Control Tower resumption. These local samples grant none of those actions.
