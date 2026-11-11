# CC-495 — fresh, relevant reply facts

The existing private reply bot now checks section 7 of the voice guide before
drafting and immediately before sending. The 11 November rejected draft is the
incident behind these checks. Jim still sends any public reply himself.

| Voice-guide rule | Existing consumer's check |
|---|---|
| 1. Same-session fact, observed within 60 minutes before the target or after it | Actual observation timestamp and ET session date; a fresh report clock never refreshes the fact |
| 2. Daily figure, at most one trading day old | Observation date, trading-day calendar and the day stated in the sentence |
| 3. Positioning, at most three calendar days old | Actual as-of day; only a positioning target; never an explanation of today's move |
| 4. Historical base rate | Count, denominator, explicit historical period and completed-day cutoff |
| 5. Same market or an expressly explained driver | Distinct indices; a driver sentence names both markets and the relationship |
| 6. No usable fact, no draft | Candidate/source matching before either editorial call, with individual omission causes |
| 7. Never send a target older than 15 minutes | Current clock before media, after media/source checks and directly before the text API call |

Each refusal has a specific code in `x_reply_fact_policy_v1.py`. These checks
prevent the measured stale/wrong-market/late incident; model labels and launch
configuration do not gate the run. Old issued requests, sent drafts and public
objects retain their bytes. An old unsent pack must pass today's send checks.

The ordinary minute entry still calls `x_reply_bot_v1.refresh_due` before Main
export/publication work. It reads held completed bars, the normalized official
rate rows and the existing CPI reaction export. Their SQLite stores are opened
read-only. The same immutable source row or file is resolved again at send time.
No source acquisition, Main edit, schedule change or application restart is added.

One attributed price/yield may enter a reply under host rule 7 and Jim's decision
72 b. This does not grant redistribution of the underlying raw bar/rate tables.
CFDs and futures keep their instrument names and source units. Historical reaction
counts are computed separately by instrument, source, price basis and reaction
window; sources are never pooled, and a retained sample is named as such. No
consensus table, private account detail or execution identifier enters the copy.

The private message shows `Fact age` in plain words. Existing outbox run/event
records retain each candidate's cause, source gaps, post-to-draft, post-to-send
attempt and confirmed delivery minutes. Timings cover filtering, ranking,
drafting, checks and Telegram sending, including uncertain send attempts. The
five-draft cap, identity checks, Skip and uncertain-write deduplication remain.

`first-draft-timing.json` reconstructs the rejected delivery from its saved
request and call clocks. It was already 37.67 minutes old at the first tick;
ranking took 43.15 seconds and writing 62.73 seconds. The original tick sent
nothing, and reconciliation delivered the retained draft later, at 44.51 minutes.
This is the first-delivery startup/reconciliation case, not steady-state speed
evidence. New observations must establish the actual next-three-draft result.

Build evidence:

- `run-context.json`: operating base, actual launch arguments and preserved WIP.
- `reply-tests-initial.xml`: initial 75 passes and one obsolete 60-minute fixture.
- `reply-tests-second.xml`: 58 passes and two test-isolation fixture corrections.
- `fact-and-entry-tests.xml`: 27 passing policy, source-consumer and entry checks.
- `reply-tests.xml`: 62 passing final policy, bot, held-source and minute-entry checks.

Live integration, installed tests, source availability and the next three real
private deliveries are recorded separately when observed. A Bot API confirmation
proves private delivery; it does not prove a phone screen was opened or a public
reply was sent. No draft is manufactured to fill the acceptance count.
