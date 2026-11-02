# Event preview and review articles

CC-107 adds two writer briefs and an offline public-copy guard. The real midterm and
NFP drafts are blocked on their future frozen inputs. No real article, native writer
call, rendered review, live integration or publication is claimed by these templates.

Jim's decision 35, 2 November 2026, permits scenarios and market reactions in these
types. Trading calls, entries, stops, targets, sizes and DEMO positions/results stay
private. Every article needs Jim's explicit yes until he grants a standing yes. This
item's narrower approval requirement governs these new types despite V1's general
routine-publication grant.

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
own exact spans. When this type is wired into the live native path, Ops must connect
the same guard and Jim's exact approval at the existing review/publisher boundary;
this isolated engineering utility is not already that deployment.

## Draft inputs and continuation

The source read on 2 November found these files absent:

- Midterms: `A:/Capital Chronicle/ResearchRuns/claude-main-events-20261029/20261103-midterm-dossier/PREVIEW.md` and `dossier.json`.
- NFP: `A:/Capital Chronicle/ResearchRuns/claude-main-events-20261029/20261106-1100-dossier-nfp/DOSSIER.md` and `dossier.json`.

The retained prompts locate the future runs: midterms at 06:00 GMT+7 on 3 November;
NFP at 18:00 GMT+7 on 6 November. A prompt or calendar is not a frozen dossier.
No placeholder file is counted as a private draft. Claude Ops must supply the actual
frozen inputs and existing source/rights admission, then resume this same branch for
approved native preparation, writing and rendered review. Do not start a test run
in the 18:30–22:30 GMT+7 event freezes on 6, 10 or 13 November.

Focused verification:

```powershell
python -m pytest -q tests/test_event_article_guard_v1.py
```
