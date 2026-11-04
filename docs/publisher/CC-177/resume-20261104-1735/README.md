# CC-177 resumed integration, 4 November 2026

The Publisher code is integrated. Completion still requires Main consumers outside
this lane: the weekly digest readers, the recurring CC-014 export binding and
CC-136's published-feed/site integration. CC-177 remains BLOCKED for those causes.

Removed `DIGEST_OUTPUT_MUST_BE_INSIDE_BACKLOG_WORKTREE` from both existing weekly
export scripts. An explicitly selected runtime output directory is now supported.
The store is still opened read-only. Tests execute the real scripts from outside
the repository, read their JSON/Markdown outputs and verify the store is unchanged.
No new publisher, scheduler, store or coordination record was introduced.

Code commit: `3d125a2e8d103f72ec9b347b98985092494d5e14`, pushed and fast-forwarded
into `A:\Capital Chronicle\ContentOps`. The initial 18 focused checks and 125
operating-root consumer checks passed (one pytest process at a time; no full suite).
Existing operating-root status entries and five pre-recorded WIP hashes survived.
The untracked inventory contains 1,032 individual paths; none was removed.

The installed scripts produced the real week-ending 2026-11-04 projections at
`A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\weekly\2026-11-04`:
coverage.json/coverage.md and engagement.json/engagement.md. Counts, availability
causes and file hashes are in `consumer-readback.json`. Main's existing CC-122
reader at e8f565d8 reads the production-day record and last post, but reads neither
of these weekly outputs. Ops/Codex Main must add those readers to its digest.

| Item | Current disposition | Remaining consumer work |
| --- | --- | --- |
| CC-043 | Source installed; real retained export accepted as 82 public records | Both configured editorial pointers still have zero desk exports. Ops/Codex Main must supply the recurring finished-run binding under CC-014. |
| CC-044 | Exporter installed; ten channels and their actual availability causes exported to runtime | Main weekly engagement reader/rendering. No new platform metrics or X session probe is claimed. |
| CC-047 | Source cap/routes and exporter installed; current coverage exported to runtime | Main weekly coverage reader/rendering. |
| CC-015 | SUPERSEDED by CC-043 public projection and native MAX/compiler | The retained subscriber renderer is preserved. |
| CC-135 | Producer installed; five sealed pieces validate; FOMC retains five outlets | CC-136 remains BLOCKED with GIT_CHECKOUT_CONTROL_CHANGED in the backlog; Ops must integrate/bind Main/site consumers. |

CC-014 itself is now live at `22ef8ab3759ae73a16d4920cad9e789975901a99`;
its integration result is main-live-cc-014-20261103T223713/result.json. That proves
installation, while its retained result still assigns recurring binding to Ops
after NFP. The real smoke export already held in ResearchRuns passes the current
public projection; it is dated source material, with its original generation clock
and SHA-256 recorded. No fixture or newly generated research was substituted.

Launch ancestry: gpt-6.1-sol/high, CONFIGURED_NOT_OBSERVED. No editorial calls,
public sends, schedule changes, app restarts or messages occurred. Live tag:
`contentops-live-20261104-cc177-weekly-export`; prior live source is retained at
`contentops-live-20261104-cc186-post-images` (91f38751).
