# CC-537: daily trend board

The existing `scripts/plan_status_posts.py --publish` minute entry consumes
`A:\Capital Chronicle\ResearchRuns\plan-status-v1\desk-board.public.json`,
independently of plan-state export freshness and of whether Main traded.
There is no added task, timer, model call, publisher or database.

`live_contentops/daily_trend_board_v1.py` formats Main's six states, mean-close
levels and all qualifying side-specific historical rows. The board's own rule
is printed. A change from the adjacent observed trading session supplies the
headline. A first observation does not invent yesterday's state. New York's
17:00 close, including daylight saving and weekday sessions, selects the daily
identity; completed D1 timestamps retain CC-528's open-time meaning.

The sole coordinator receives the exact frozen copy and media for Discord,
Substack Notes and X. X uses complete own-thread posts; long Discord copy uses
separately identified parts. The confirmed CC-536 method page supplies the link.
The board is outside article accounting. Source corrections after issuance
never replace that day's bytes. Uncertain writes are read back before any retry,
including when the producer file disappears. An old unsent day cannot starve
today's board. Three distinct, reconciled public days are required for acceptance.

Decision 82 selects a new TradingView download for the changed lead market,
or gold when no state changes. The capture uses Neo's existing window and its
`codex/cc537-trend-board` group, a guest chart and the download tool. No native
file chooser is used. After the existing bounded capture owner's two failures,
the fallback graphic displays the six source-bound states and mean levels.
Its exact bytes and source facts are checked at the coordinator's image boundary.

## Producer fields needed

CC-528's public V1 schema currently supplies states and side-specific results.
The requested absolute mean prices and historical date windows are absent.
The consumer accepts these public additions, without computing substitutes:

| Board field | Meaning |
| --- | --- |
| `markets.<symbol>.yardstick.mean_close_20` | Main's actual 20-session mean close |
| `markets.<symbol>.yardstick.mean_close_50` | Main's actual 50-session mean close |
| `rows_whose_condition_holds_now[].sample_period.start/end` | Exact historical sample dates, `YYYY-MM-DD` |

A `sample_period` on the market or measured table is accepted when it applies
to every contained row. Per-row periods take precedence. No source outside the
board supplies a public number. The public V1 `this_side` tuple is read as
`[n, win_fraction, mean_r, t, first_half_r, second_half_r, read]`; pooled-side
results and win fractions never substitute for that side's mean R.

Absent fields return `BOARD_PUBLIC_FIELDS_ABSENT` with exact JSON paths, before
media or publication. This prevents fabricated public means/windows; it is not
a model, effort, launch, same-reviewer or worktree check. A source older than one
trading day, or a freshly rewritten file with old underlying daily bars, posts
nothing and names its age. Named analyst triggers and private decision fields
are excluded from public copy, as the item's Ops Product instruction requires.

## Verification

`tests.xml` covers the six-market source-to-coordinator path, three controlled
fixture days, duplicate runs, lost responses, absent sources, stale bars,
source tampering, New York close selection and the installed minute entry.
The fixture days are not live publication evidence. Live source inspection,
installed consumer readback, tags and the remaining acceptance are recorded in
`live-result.json` after integration.
