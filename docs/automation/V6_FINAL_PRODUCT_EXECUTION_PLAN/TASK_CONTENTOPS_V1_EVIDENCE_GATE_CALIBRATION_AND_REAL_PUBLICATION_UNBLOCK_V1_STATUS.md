# V1 Evidence Gate Calibration and Real Publication Unblock — Current Status

Authority date: 2026-08-12

Task: `TASK_CONTENTOPS_V1_EVIDENCE_GATE_CALIBRATION_AND_REAL_PUBLICATION_UNBLOCK_V1`

Result: `NOT_ACCEPTED_HARD_LIVE_CYCLE_LIMIT_REACHED`

This packet records the bounded continuation result. It is not a PASS, does not accept FDA-G,
and grants no additional publication authority.

## Preserved implementation and controls

- Existing V1 calibration work was preserved on
  `task/v1-evidence-gate-calibration-real-publication-unblock-v1`.
- The canonical operator pause fuse is checked before outbound 9Router text requests.
- `STOP_ALL_CONTENTOPS_BACKGROUND.cmd` activates the fuse before stopping proven ContentOps
  processes; ambiguous processes and both persistent browser profiles are preserved.
- `RESUME_CONTENTOPS_LLM.cmd` requires explicit operator action and does not start the app.
- Continuous intake is zero-LLM. Only scheduled editorial windows and explicit Run Now may enter
  the expensive editorial path.
- Cycle limits remain 5 logical calls, 8 provider attempts, 80,000 tokens, and 400,000 tokens per
  active day. Quota/pause/budget exhaustion does not authorize paid-family fallback walking.

## Offline blocker replay

The prior Decision 5 replay is fixed and reaches evidence success, article creation, review PASS,
and package creation with `PUBLIC_WRITE=false`. The original exception was
`ValueError: rolling_x_article_revision_made_no_change`; the source desk label entered the SEO
keyword path and caused a deterministic review failure that the reviser could not change. The
fix selects a claim-bound keyword.

Replay evidence:

- viability artifact:
  `A:\Capital Chronicle\Runtime\ContentOps\evidence_gate_calibration_shadow_v1\prior_blocker_replay_v4\rolling_x_newsroom_cycle_evidence_v1.json`
- SHA-256: `566bc3588c7e794675d6c987864b8c432408d1a0915aa6a118f7aa1980b2f7c17`
- evidence: `SUCCESS`
- article: present
- review: `PASS`
- revisions: `0`
- package: created / shadow ready
- public write: `false`
- unknown write: `false`

## Builder provider discipline

Exactly one minimal Gemini preflight was used. The requested identity was
`vx/gemini-3.5-flash(high)`; it returned HEALTHY/HTTP 2xx in 4.7967 seconds. Reported usage was
2,120 tokens. No credential value or secret material was exposed.

Exactly two real LLM-capable production cycles were used:

1. `operator-requested-operator-trigger-db0531ef52e7446bac30e13a` ended
   `REJECTED/NO_PUBLICATION`, with 2 logical calls, 1 provider attempt, 76,724 accounted tokens,
   zero article/package/dispatch, zero public write, zero UNKNOWN_WRITE, and zero pending
   reconciliation. Cycle evidence SHA-256:
   `6f8695cbde71e4b9256c9c4d7efdea78ba0cad4d5b063943c5ae5880dcb44cdc`.
2. `operator-requested-operator-trigger-f16e0e6e018f430cb476e644` ended
   `REJECTED/NO_PUBLICATION`, with 2 logical calls, 1 provider attempt, 70,901 accounted tokens,
   zero article/package/dispatch, zero public write, zero UNKNOWN_WRITE, and zero pending
   reconciliation. Cycle evidence SHA-256:
   `d362cdb52164c7d1605b3f8fa349aeee462e9d78fcf30cc06272a7f053d9986d`.

The maximum of two live cycles is exhausted. A third cycle was not run.

## Final offline correction after cycle two

Cycle two showed that the RSS loader capped results before evaluating relevance, freshness, and
point-in-time eligibility. The exact story therefore retained only WSJ even though a current
independent corroborating result existed lower in the feed. Source commit
`e42c23f1762e60de0c86f8893d761ec25be4dccb` now:

- normalizes the event-bearing query;
- validates the feed publisher name and origin host against the reputable-secondary allowlist;
- excludes post-cutoff and low-relevance listings before the result cap;
- keeps one candidate per origin and ranks current relevant candidates deterministically; and
- recognizes The Jerusalem Post (`jpost.com`) as a reputable secondary source.

An exact read-only replay of cycle-two rank 10 at its original evaluation cutoff returns The
Jerusalem Post plus WSJ, targeted-evidence adapter `PASS`, claim contract `PASS`, one supported
claim, and `publication_authority=false`. This is offline/read-only evidence, not the required
production publication proof.

Focused regression after this correction: 127 passed. Compile and diff checks passed. Pytest
also emitted the known non-failing Windows temporary-directory cleanup warning after completion.

## Current safety state and blocker

- production app: stopped
- operator LLM fuse: paused
- production store: preserved; integrity `ok`; schema `9`
- Chrome ingestion profile/CDP 9222: preserved
- Edge publishing profile/CDP 9223: preserved
- public writes in both live attempts: `0`
- UNKNOWN_WRITE: `0`
- pending reconciliation: `0`
- master integration: not performed

Exact next blocker:
`OWNER_AUTHORIZATION_REQUIRED_FOR_A_NEW_CONTROLLED_LIVE_PROOF_AFTER_HARD_LIMIT`.

The task cannot be called complete and the branch cannot be integrated to master without a new
owner decision permitting another bounded live proof. Until then, keep the app stopped and the
operator LLM fuse active.
