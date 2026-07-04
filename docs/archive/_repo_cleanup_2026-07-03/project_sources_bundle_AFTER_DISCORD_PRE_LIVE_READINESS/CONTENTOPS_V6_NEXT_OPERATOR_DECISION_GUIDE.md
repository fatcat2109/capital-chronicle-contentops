# ContentOps V6 Next Operator Decision Guide

## Current Decision Point

Discord lane is pre-live ready only. No live send has happened.

## Safe Options

### Option A - Pause

Keep accepted state at `5e3763f70a2d23a9841534aa8ea6560b68d176bc`. Do not run live task.

### Option B - Continue documentation consolidation

Refresh Project Sources, plans, and handoff docs only. Keep no-send invariant.

### Option C - Prepare separate future live task

Only if Jim explicitly chooses, create separate task requiring all items below.

## Minimum Future Live Task Gate

- exact operator GO phrase;
- exact payload preview and hash;
- destination binding;
- credential presence membership-only proof for `DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK`;
- payload hash revalidation;
- kill switch;
- redacted audit;
- single request budget;
- zero hidden retry;
- stop-on-uncertainty rule;
- manual fallback.

## Worker PASS Acceptance Rule

ChatGPT must verify GitHub remote commit, diff, and content before accepting any worker PASS. Project Sources help context only and do not replace repository verification.

## Stop Conditions

Stop if any task tries to read env or `.env`, read credential values, call Discord API or webhook, open browser, create executable request artifact, create public URL, create metrics, claim publication readiness, or claim live send completion.
