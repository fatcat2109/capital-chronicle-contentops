# CC-378 — Antigravity light text and claim check

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
