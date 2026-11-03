# CC-135: one sealed record per published piece

`published_content_v1.jsonl` is the read-only publication projection consumed by
CC-136/CC-014. Its operating location is
`A:\Capital Chronicle\Runtime\ContentOps\published_content_v1.jsonl`.
The durable SQLite lifecycle and `DurablePublicationCoordinator` still own every
send, identity, readback and recovery. This change creates no queue or schedule.

Each compact UTF-8 JSON line contains `content_id`, `type`, `title`, `standfirst`,
`published_at_utc`, `recorded_at_utc`, `outlets[]` (`name`, `url`), optional
`event_id`, `conditional_calls[]`, `rights_class`, `visibility`, the analysis
notice and any required conflicts notice. Types are ARTICLE, EVENT_PREVIEW,
EVENT_REVIEW and DESK_NOTE. A missing explicit event identity remains null;
titles never invent one. The original retrospective FOMC piece remains ARTICLE.
The export's analysis notice is metadata; backfill does not edit historical posts.

`content_sha256` is the SHA-256 of all other fields serialized with sorted keys,
compact separators, UTF-8, `ensure_ascii=False`, and `allow_nan=False`. This is
the exact seal contract already consumed by CC-136's
`desk_record_published_reports_v1.py`. The current CC-014 reader keeps calls
private until its own CC-134 projection change; this item changes no Main code.

Publication and recording clocks are separate. Public Substack `time[datetime]`
or `post_date` supplies the original publication timestamp. Dispatch, source,
event and retrieval times are never substitutes. New native Substack readback
requests ask for that field. Historical issued requests remain byte-stable.
When a post is already public but an original clock or file write is unavailable,
the result names `PUBLICATION_RECORD_PENDING`; a retry never republishes it.

The file records the confirmed outlets at its first sealed export. It never
includes an UNKNOWN_WRITE, pending or merely planned outlet. Later distribution
recovery stays with the original coordinator; it cannot rewrite that snapshot
or append a second line for the same piece. The corpus joins each outlet to its
exact dispatch reconciliation. Discord links combine that confirmed message
identity with the existing channel and an observed guild identity.

Writers take a nonblocking OS lock on the feed, validate every existing seal,
identity and complete newline, then append and fsync. Retries leave the original
bytes unchanged. Conflicting identities, duplicate JSON keys, nonfinite numbers,
broken seals and torn tails refuse without rewriting the file.

The existing public-output guard is shared by the feed and the coordinator's
prewrite boundary. Decision 40 amends decision 35: a general conditional call
must carry a condition, bullish/bearish direction, market, horizon, invalidation,
the analysis notice and the confirmed conflicts line. Its full text must be
present in the source article. Unconditional calls, execution instructions,
sizes, profit targets, DEMO details, private labels and prediction-market numbers
remain refused. Source/number admission, chart lineage, source rights and native
render review remain with their existing owners. `CC_OWN_ANALYSIS` describes
Capital Chronicle's original prose; it grants no new rights to third-party data.

The one-shot backfill opens the existing lifecycle with SQLite `mode=ro` and
`query_only`. It validates all records before appending. It excludes removed
objects and unconfirmed drafts, with no provider writes or historical reposts.

```powershell
python scripts/backfill_published_content_v1.py --observations docs/publisher/CC-135/original-publication-observations.json
python scripts/backfill_published_content_v1.py --observations docs/publisher/CC-135/original-publication-observations.json --apply
```

The public archive and both exact canonical pages were read with BrowserOS Neo.
The observation file preserves the original timestamps. It also records the
existing authenticated Discord webhook GET used solely for non-secret guild
and channel metadata. No credential, session, post or account was changed.

Engineering launch: explicit `--model gpt-6.1-sol` and
`-c model_reasoning_effort="max"` read back from the running top-level exec;
`CONFIGURED_NOT_OBSERVED`. Base: operating tag
`contentops-live-20261103-cc124-recovery-snapshot` (`1bfdaf8e717340e7c5ae11ac94513affca8e7b00`).
CC-135 cites decision 39 for Publisher's own tested operating-root fast-forward;
the default branch is never merged and unrelated operating-root WIP is preserved.

## Verified delivery

- Source `a22c260bc1a737036ea2ac93a238974938c63512` fast-forwarded the same
  operating branch under `contentops-live-20261103-cc135`. All 42 prior WIP
  entries, tracked dirty-file hashes and staged/unstaged diffs were unchanged.
  [Source integration evidence](source-integration.json).
- The operating-root backfill appended two records. FOMC has exactly Substack,
  Telegram, Discord, Facebook and X; its original publication clock is preserved.
  The earlier oil piece has ten confirmed outlets, including the owner-selected
  LinkedIn company copy. Removed posts and the pending CPI draft were excluded.
- A second actual invocation returned ALREADY_RECORDED for both pieces and left
  the live feed's SHA-256 unchanged. The source database's size and modification
  clock were unchanged. [Live backfill evidence](live-backfill-result.json).
- 294 targeted guard/coordinator/finished-publication regression checks passed;
  215 subsequent feed/backfill/native-protocol/guard checks passed. These are
  overlapping selections, not 509 distinct tests. The exact CC-136 consumer
  at `d646f03e8` read both sealed records from a copied feed as public reports.
  [Copied-store compatibility](../../../tests/evidence/cc-135/copied-backfill-compatibility.json).

No new public article, provider send, Main edit, schedule change, process restart
or running-service code reload is claimed. Future native publication through this
source has deterministic test coverage, not a new observed live send. CC-014/site
live integration remains with its existing owners.
