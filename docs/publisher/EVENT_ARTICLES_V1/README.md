# Event preview and review articles

CC-107 adds two writer briefs, the public-copy guard and a narrow retained-source
adapter for the exact Ops-reviewed midterm PREVIEW.md. The frozen public preview is
available on 3 November; the NFP dossier is still due on 6 November. Templates and
input admission alone prove no native writing, rendered review or publication.

Jim's decision 36 supplies a standing publication yes after Ops review. Decision 40
allows general conditional bullish/bearish calls with condition, market, horizon,
invalidation, the analysis notice and conflicts line. Unconditional calls, execution
instructions, sizes, profit targets, DEMO details and prediction-market numbers remain
refused. Decision 42 requires a factual visual. The later decision 48 and Ops's
3 November 13:04 GMT+7 instruction make Substack drafts only: never press Publish
or Update, read a mailbox or enter a code. Site and social delivery proceeds
independently, using the read-back site link when available and linkless summaries
while the article site is not live.

The [preview brief](templates/event_preview.md) covers scenarios, sourced odds,
conditional reactions across all six required market groups, and view changes. The
[review brief](templates/event_review.md) covers the actual outcome, frozen scenario
match, CC-106 scoring, both baselines, observed reactions and the lesson. These are
subtypes within the current editorial modes, not a replacement for the native writer.

The existing Light preparation, same MAX writer/editor and final-render review,
source/story/media owners, eight-channel compiler and sole publication coordinator
retain their roles. Do not use the older subscriber Event Card or Saturday Ledger
permission as this item's rights or account-data policy. CC-043's public export adapter
is delivered separately and is not in this item's operating-tag base. No duplicate
projection, rights classifier, scorer, state store, scheduler or publisher is added.

`event_preview_source_v1` admits only the hash-bound public PREVIEW.md, verified
against its frozen manifest and separately pinned Ops review. It never reads the
private dossier or promotes its odds, execution fields or account records. The
existing retained-research snapshot and source resolver carry the admitted preview
as conditional Capital Chronicle analysis, never official event confirmation.

## Public-output guard

`live_contentops.event_article_guard_v1.check_public_event_article` checks the entire
authored copy before it can be considered for public output. It refuses private
structured keys at any depth, account/position/result prose, execution instructions,
unknown sections, missing disclaimers, unsupported numbers, modified source displays,
missing reuse admission and time-inconsistent evidence. Diagnostics contain causes
and locations, without quoting private values. The two test article types use
conspicuously synthetic data; they are neither requested drafts nor factual evidence.

Call the API with a separately trusted `evidence` context. The CLI additionally pins
that context's exact bytes:

```powershell
python -m live_contentops.event_article_guard_v1 `
  --article <private-authored-article.json> `
  --evidence <existing-owner-public-evidence.json> `
  --evidence-sha256 <hash-from-the-existing-owner-record>
```

This command only reads the two named files and prints a small report. It does not
open a store or contact a model, browser, account or platform. Exit zero means the
bounded copy guard passed. Exit two means refusal. PASS always has
`publication_authority: false`, `jim_approval_required: true` and
`final_native_render_review_required: true`. No input can waive those boundaries.
The legacy `jim_approval_required` field means the checker cannot grant authority;
decision 36 already supplies the standing yes after Ops review. It does not require
another per-article question to Jim.

The article has `schema_version: contentops.event_article.v1`, `article_type`,
`event_id`, `event_time_utc`, `cutoff_utc`, `written_at_utc`, `copy` and
`numeric_bindings`, with no other keys. `copy` has exactly the keys listed in the
chosen brief. Each is nonempty authored text, except `market_reactions`, which has
six authored strings: `rates`, `dollar`, `gold`, `oil`, `indices`, `sectors`.
The exact disclaimer is `This is general market analysis, not financial advice.`
All record clocks are UTC. Preview writing must precede the event. Review cutoff
must follow it. The preview's original cutoff is never advanced to fill a source gap.

Each number, including numeric text in a headline, has an independent private binding:
`{copy_path, start, end, evidence_ref}`. Offsets cover the exact source display in that
authored string; all numeric characters must be covered, without overlapping spans.
The displayed source owns sign, precision, unit and wording. The checker permits
Unicode presentation and digit-grouping changes only, with no arithmetic, rounding,
imputation, probability normalisation or scoring. A tag on a different number cannot
cover an unrelated private figure. Numeric text with offset-changing Unicode must
be repaired to plain Unicode and rebound, not guessed.

## Existing source and rights authority

The context has `schema_version: contentops.event_article_evidence.v1`, the same
`event_id`, a `facts` map and a `private_text` list for the existing private-text
backstop. Each cited fact needs `display`, `source_ref`, original `source_sha256`,
`known_at_utc`, `rights_class`, `public_use_allowed: true`, `rights_evidence_ref`,
and the original `use_label`. `kind: PRE_EVENT_FORECAST` additionally requires a
known-at time before the event, including when used in a later review. Scores remain
actual Main/CC-106 outputs, not newly computed prose.

**The writer must not author the evidence context.** Its public facts must come from
the existing validated `project(public)` export or the existing source/rights owner's
admission of exact frozen dossier facts. The context hash comes from that owner's
record. The guard verifies the supplied admission and spans; it does not create a
licence or establish that an untrusted declaration is true. No real context is
manufactured in this delivery. CC-014's live event export is still upstream work.

A private capture label is preserved if the existing owner explicitly admits lawful
public reuse of that exact fact. Missing, conditional, unknown, licence-required,
NOT_GRANTED and private-only classes fail. Private consensus, consensus-derived scores,
GEX and account data receive no exception. CC-104's actual public terms check must
precede any prediction-market odds admission. Attribution obligations remain in the
source binding and final copy/review; a private research permission is insufficient.

The caller and final native review still own factual meaning, source selection,
uncertainty, complete scenario coverage and correct attribution. A deterministic
privacy/span guard does not certify arbitrary prose semantics, chart quality, or an
actual source's legal terms. Re-run it on changed copy and derivatives with their
own exact spans. The exact midterm native write/repair submit gate now validates
`article.event_article` against the request's code-owned evidence, binds its sections
to the canonical text, and refuses unsupported extra canonical numbers or private
copy before storing an accepted return. The checker itself never supplies authority.

## Draft inputs and continuation

The 3 November midterm PREVIEW.md and frozen manifest are now available. The exact
Ops-reviewed public preview entered the existing native operation
`cc107-midterm-preview-20261103-v1`; its accepted Light and same MAX returns are
retained. The [private midterm draft](midterm-20261103/midterm-preview.md) uses only
that preview. Source admission, role provenance, focused checks and current limits
are in [execution.json](midterm-20261103/execution.json).

The same MAX editor required repairs to the first assembled renders. The portrait
fact card, caption and linkless derivative corrections are applied through the
existing media owner. The corrected eight reader copies pass the public guard;
final desktop/mobile pixel acceptance remains pending. The existing sole
coordinator's fenced Substack save-draft path is implemented and tested, but has
not been called. It forbids Publish, Update, mailbox access and verification codes;
a saved draft will not count as a public canonical article.

The NFP input remains absent at the recorded 3 November readback:
`A:/Capital Chronicle/ResearchRuns/claude-main-events-20261029/20261106-1100-dossier-nfp/`.
Its existing producer is due at 18:00 GMT+7 on 6 November. A prompt or calendar is
not a frozen dossier, and no placeholder is counted as a private draft. Ops resumes
this same branch after the actual frozen input and source/rights admission arrive.
Do not start a test run in the 18:30–22:30 GMT+7 event freezes on 6, 10 or 13 November.

Focused verification:

```powershell
python -m pytest -q tests/test_event_article_guard_v1.py
```
