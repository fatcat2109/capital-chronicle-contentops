# CC-378 — Antigravity light text and claim check

## Live integration — 12 November 2026

Decision 120 removes the earlier Ops-review wait. Publisher squashed the two
record-validation commits onto operating HEAD `e16ddb8c`, pushed
`backlog/cc-378-record-validation-squashed`, and fast-forwarded the operating
root to `cbd97553`. The article submit, preparation and derivative compiler use
the installed module. Rollback is `contentops-rollback-20261112-cc378-r114`.

All 40 targeted tests passed in the delivery worktree and again in the operating
root. Recorded Antigravity output reaches the actual compiler; forced failures
keep publication moving with the existing copy. Existing uncommitted files were
preserved. The live source and runtime evidence are recorded in
[integration-20261112.json](integration-20261112.json).

The fresh operating-root agy 1.5.6 call returned `AGY_TIMEOUT_120S` after its
120-second limit. The installed consumer read that real `AGY_UNAVAILABLE` record
and compiled fallback payloads for all eight current destinations, preserving the
original article and alt text. No retry or public write was made.

Full publication acceptance remains blocked on that missing completed return and
the next two CC-124 pieces: their
claim lists, Publisher flag decisions, alt text, social variants and exact public
readbacks. Integration and a controlled runtime call do not establish those
publications. No historical request or public article is rewritten to supply them.


## Decision 114 delivery — 11 November 2026

The reopened delivery checks claims and light copy against the retained record.
An exact quote now has to contain the claim's numerical value, sign and unit,
and any named date. Attribution spans are checked against their referenced lines.
Coverage checks flag omitted numbers, named dates and the source's named publisher.
Identifiers, URLs, hashes and retrieval metadata cannot supply numerical evidence.

Selected social variants are checked against both the article and the numbered
source record before the existing compiler consumes them. Alt text is checked
against its admitted asset specification. A bad suggestion keeps the existing
copy for that output; valid suggestions for other outputs still reach the compiler.
Publisher continues to decide each claim flag. These checks establish exact
record matches; Publisher still judges meaning and context.

The first live runtime probe succeeded with agy 1.5.5, configured as
`gemini-3.8-flash-high` / high (`CONFIGURED_NOT_OBSERVED`). The retained runtime
artifact and exact hashes are in [validation-decision114.json](validation-decision114.json).
Forty focused tests passed in 11.72 seconds, including recorded output through
the actual compiler, forced failure, wrong quotes, omitted claims and selective
fallback. No test used a live store or made a public write.

The branch starts at the current Publisher operating-root HEAD. The remote
default branch is 910 commits behind it and lacks the active article consumer.
This new delivery remains unmerged for the Ops review requested by this run;
the earlier integration below describes the original decision-105 version.
Two CC-124 pieces with saved flag decisions and exact published alt/copy
readbacks remain acceptance work. The saved CPI-preview assist timed out after
120 seconds and continued without suggestions; it is not successful-use evidence.
No historical article is edited or new publication created to manufacture it.

## Original decision 105 implementation

Decision 105 is wired into the existing native article `submit` path. Publisher
still writes and edits. Nothing calls a model for a plan-status post. No schedule
changes are included.

Every successful writer/revision submission sends the draft, source pack as
numbered lines, and each planned image/chart's spec and caption to agy 1.5.3.
It includes the existing owner's article card and TradingView capture before the
light pass; `advance` reuses them. The executable runs in an empty temporary
folder, using `gemini-3.8-flash-high` / high, with a 120-second call timeout.
The prompt begins `Do not call any tool`. Stream input handles full source packs
without Windows' command-line length limit. Model and effort remain
`CONFIGURED_NOT_OBSERVED`.

The submit result points to `agy_light_assist_v1.json` beside the article package.
Its revision directory retains the prompt, numbered source lines, raw output,
hashes, version and UTC start/end clocks. It contains alt text, four social
variants, the claim list, and exact source/unmatched/coverage flags. An unchanged
submission reuses its result, including a failed result; it never retries in a
loop.

Before `advance`, Publisher reads the artifact and records its choices through
the existing CLI:

```powershell
python scripts/run_native_desktop_editorial.py agy-review --binding <same-binding.json> --response <review.json>
```

The review contains `prompt_sha256`, `use_alt_text`, `use_variants`, and a
`decisions` array with one `claim_id`, `action` (`KEEP` or `FIXED`), and substantive
`reason` for every flag. `FIXED` also supplies a `correction` reference to the
actual Publisher repair. Changed prose uses the ordinary writer/revision path;
the light pass never edits the body or a number. A revised draft gets a new
assistance prompt hash within the same operation.

`advance` feeds selected alt text into the existing media manifest and selected
X, Threads, Telegram and Discord copy into the eight-channel compiler. The
compiler still supplies the real canonical link, Main scenarios, notices, media
and credits. Preview-host, public-time, execution-detail, new-number, asset-spec,
length and ordinary compiler checks reject a bad suggestion while retaining the
existing package. The article's run metadata records the actual consumer use and
Publisher's decisions. The existing Substack transport asks for the exact alt
text and reads back its presence.

A failed, timed-out, empty or malformed call records `AGY_UNAVAILABLE`; the
article continues with its existing copy. Unreviewed suggestions are visible
inputs and do not veto a piece.

Verification is in [validation.json](validation.json). The tests replay actual
agy output and force failures; they exercise native submit/review and actual
compiler consumption. `runtime-probe.json` records the first successful call from
`A:\Capital Chronicle\ContentOps`. `recorded-call` retains a sandboxed timeout;
`recorded-call-print` retains a complete successful light pass without that
optional CLI flag. `recorded-stream-call` proves a full source packet larger than
32 KiB reaches the same model using stream input.

The next two CC-124 pieces still need actual publication evidence: their saved
claim lists, alt text and variants, every flag decision, and published alt/copy
readbacks. On 9 November the day's two slots were already used. The retained
CC-124 record next admits the pre-US wrap at **10 November 18:30 GMT+7**. Decision
93's daily cap is preserved. No replacement article or edited historical post is
used to manufacture this acceptance evidence.
