# Beat the desk: four weekly rounds

Test whether readers return to make six forecasts and inspect a complete result. Use the existing Discord announcement webhook and its official poll capability. The registry identifies this route as WEBHOOK_API; it does not establish that a separate Discord bot can retrieve voters. The cheapest pilot therefore scores **the crowd**, the desk and a trend rule. An individual leaderboard is a later extension, not a claimed capability of this launch.

**One action that starts the test — Jim:** issue “Launch CC-429 Beat the desk, Week 1” to Publisher with the attached six-poll draft. Publisher handles that later run through the existing coordinator and Discord transport, extending that transport's structured payload only as needed. This item prepares the plan and request bodies; it does not send polls, install that extension, create a bot or add a schedule. No new account or paid product is needed for the proposed webhook route.

## Rules fixed before opening

- Markets: Gold (XAUUSD), S&P 500 (US500), EUR/USD, USD/JPY, WTI (USOIL), Bitcoin (BTCUSD). Up means the named price rises; for USD/JPY it means a stronger dollar against the yen. WTI is not Brent. Bitcoin is not a different token or proxy.
- Open the six polls on Sunday between 09:00 and 09:01 ET. Set each native poll's duration to 24 hours; its returned expiry is its final deadline, no later than Monday 09:01 ET for an on-time launch. If the launch misses that opening range, move the entire proposed round to the next week before sending anything. Never shorten a live round silently.
- Choices: Up, Down, Flat. One choice per poll; voters may change it while the native poll remains open. The crowd's forecast is the unique plurality at final expiry. A tie or zero votes is an abstention, not a forced direction. Vote shares are participation statistics, not calibrated probabilities.
- Reference: the completed 15-minute bar ending Monday 09:45 ET. End: the completed bar ending Friday 12:00 ET. The same instrument, close convention, bar source and interval apply to all three contestants. Keep the original source/known-at clocks and exact instrument mapping.
- Main's weekly desk direction must be saved before the poll opens and explicitly target that same interval. Do not convert its conditional entry probability, target-before-stop probability or different-horizon forecast into a weekly terminal call. If a matched desk forecast is absent, show it as absent and still score the crowd and available baseline. Report the paired denominator separately.
- Freeze the trend rule before the poll opens: Main's existing PREVIOUS_SESSION direction, using only daily closes known by that freeze. RetainedCallBars.baselines already defines positive change as LONG, negative as SHORT and zero as FLAT. PAST_12_MONTHS is a separately named secondary comparison, never substituted after seeing the result. Preserve missing history and its source age.
- Main's existing realized-outcome scorer, score_outcome, supplies directional_correctness for UP, DOWN and NEUTRAL. Map LONG/BULLISH to UP, SHORT/BEARISH to DOWN and FLAT to NEUTRAL. Pass probability=None: do not invent a Brier probability from a direction. Its existing neutral tolerance is an absolute fractional change of at most 0.0001: Flat means a move within 0.01% in either direction. The adapter needs a complete outcome contract and matching observations; missing endpoints remain unresolved.
- The public table shows categorical forecasts, correct/resolved counts and Main's permitted computed moves. Do not publish raw broker bars, account details, trades, sizes, targets or P&L. Existing data feeds the scorer internally under decision 62; public redistribution of the underlying series is excluded by host rule 7 / decision 44.

## Four proposed rounds

These dates are the prepared example, not a schedule change. If Jim starts later, shift all four complete weeks together and publish the replacement dates before voting.

| Week | Poll opens, ET | Forecast interval, ET | Purpose |
|---|---|---|---|
| 1 | 15 Nov 2026, 09:00–09:01 | 16 Nov 09:45 to 20 Nov 12:00 | Prove six polls, exact expiries, final vote counts and three-way source matching. |
| 2 | 22 Nov 2026, 09:00–09:01 | 23 Nov 09:45 to 27 Nov 12:00 | Repeat without changing the rules; record holiday/source gaps rather than invent endpoints. |
| 3 | 29 Nov 2026, 09:00–09:01 | 30 Nov 09:45 to 4 Dec 12:00 | Measure repeat participation and response to the prior result. |
| 4 | 6 Dec 2026, 09:00–09:01 | 7 Dec 09:45 to 11 Dec 12:00 | Close the test with all 24 market-rounds, including abstentions and unresolved rows. |

All records retain UTC. Published dates and questions use ET after America/New_York conversion. The noon Friday endpoint is fixed in advance; market availability is still checked against Main's exact source rather than assumed from a calendar date.

## Operations and scoring

Publisher uses the current pinned Discord destination, not a channel supplied by a respondent. Before any later send, the existing coordinator binds the exact body and destination and prevents duplicates. Keep each returned message ID, actual expiry and poll answer ID. Discord says to use returned answer IDs, not assume they start at one. Recover an uncertain write by reading the exact existing message; never blindly send another poll.

After expiry, make one bounded read of each known message through the existing webhook API. Preserve the final answer counts and the results-finalized flag. If Discord has not finalized the result, leave that round pending for the next normal manual step; add no watcher or new update consumer. A webhook's ability to publish a poll does not prove voter-identity access. Keep the pilot aggregate. Do not scrape Discord, Telegram Web or personal accounts for names.

At the Friday close, reuse Main's held completed bars and existing scorer. A later change of desk view is a separate version and does not replace the round's original direction. Preserve the original result and append any source correction in the existing result owner. A returned HTTP success is a poll-creation result; a saved score is not proof the public leaderboard was read back.

Publish one compact weekly result through the existing route: market; crowd choice and voter count; desk choice; trend choice; observed end direction; each contestant's correct/resolved count. Use one row per market, plus unresolved/absent counts. An abstention is not counted as correct or incorrect. For comparisons, use only the same resolved rows where both contestants supplied a direction. Publish the denominator beside every rate. No prize, cash entry, copied-trading promise or claim of an investment edge.

Read-only API references: [Discord poll structure, limits and voters](https://docs.discord.com/developers/resources/poll), [execute webhook including poll](https://docs.discord.com/developers/resources/webhook#execute-webhook), and [get webhook message](https://docs.discord.com/developers/resources/webhook#get-webhook-message). The poll schema permits up to ten answers, a 300-character question, 55-character answers and duration in hours. The draft stays inside those limits.

Reuse references: CC-391's MainReadOnlyScorerV1 and RetainedCallBars.baselines; tools/data_foundation/realized_outcome_ingestion_and_forecast_scoring_v1.py::score_outcome; CC-409's public record; CC-414's held bars. The source contracts were read at Main delivery 19eed756eb3b6ec794cf1be2e9e8aca447a586ed. No Main code or state was changed. This preparation does not claim a weekly forecast adapter is installed or that a round has been scored.

## Continue or stop after week four

Proposed thresholds: at least 20 votes on the median market in week one; week-four median votes at least half of week one's; six result rows each week with gaps shown; and no unresolved duplicate/wrong-destination incident. Track aggregate votes, not invented unique voters or subscriber conversions. Anonymous or aggregate totals cannot measure individual retention. Ask one optional public question after week four: was the complete score comparison useful enough to return?

If participation is below those thresholds, keep the result and stop the pilot. If it passes, propose the smallest next iteration. Four weeks and at most 24 market outcomes cannot establish a forecasting edge. Reader copy carries: “Capital Chronicle offers analysis only, not financial advice or recommendations.”
