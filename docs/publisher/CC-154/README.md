# CC-154 — site-first Publisher delivery

## Current continuation — 4 November 2026

The retained implementation is resumed on `backlog/cc-154-site-first-live` from
Publisher's operating-root HEAD `5a47b0bed8d5ea01b7ddaa2a26365e5586a09249`.
This preserves the newer publication/recovery fixes; `origin/master` still predates
them. Earlier CC-186 image and LinkedIn WIP remains unstaged and outside this item.

The native action packet now follows decisions 48, 52 and 63 consistently: use
the one existing Neo window, retain the Substack code tab untouched for Jim,
and continue other destinations in other task tabs without a human-help wait.
The production transport compiler is tested with a confirmed site URL in its
actual social payload, with zero model/source calls.

The current Web consumer was executed again, read only, with a sealed site-only
record. It still returns `NEWSROOM_CANONICAL_REQUIRED`; see
[resume-consumer-compatibility.json](resume-consumer-compatibility.json).
The consumer requires a Substack outlet, uses `substack:<id>` package lookup,
and renders Substack-slug routes. Its existing mirror trigger runs only after
the Substack-dependent published-record append. That cannot deploy the reviewed
candidate before Substack. Codex Web/Ops must adapt and integrate CC-146/149 to
consume `site_publication_candidate_v1.json`, render `expected_site_url`, and
expose `article_content_sha256` for readback. Publisher cannot edit that lane.

No new article, public send, mailbox access, schedule change or chat message was
made in this continuation. Full next-article/window acceptance remains incomplete
because the site consumer rejects the input, not because of a launch label,
worktree state or an internal provenance gate. Current integration/test evidence
is recorded in `resume-validation.json`; the records below describe the earlier run.

## Earlier delivery — retained evidence

This branch exports the exact reviewed article package as `site_publication_candidate_v1.json`. A bound native readback of its exact site URL and admitted public-copy hash unlocks social dispatch. Social uses the site URL and runs before Substack; pending social browser work defers Substack so its code tab cannot park unfinished social actions.

The existing durable coordinator, store, outbox, dispatch identities, native begin/submit protocol, JIT identity checks, rights/public-copy guard, KILL_SWITCH and UNKNOWN_WRITE recovery remain the owners. No scheduler, second publisher, mailbox read, email-code entry or automated human-help wait was added. Historical sealed plans retain their policy. New lifecycle plans use `SITE_FIRST_V1`.

A code-screen return records `SUBSTACK_DRAFT_AWAITING_OWNER`, the exact draft ID, page ID and URL. Decision 54 governs the retained tab: leave it open and untouched for Jim. A later exact readback can confirm the same Substack object without another draft or publish call. Substack confirmation is reported separately from the site.

## Acceptance limit

A read-only synthetic test against the actual CC-149 Web consumer rejects a valid site-only publication record with **NEWSROOM_CANONICAL_REQUIRED**. It also restricts package lookup to `substack:<id>` and derives the article route from the Substack slug. See [consumer-compatibility.json](consumer-compatibility.json). The current mirror hook only triggers after that Substack-dependent feed append, so reusing it unchanged would retain the circular dependency.

Codex Web must consume the reviewed candidate without inventing a confirmed Substack outlet, render its `expected_site_url`, and expose the admitted article copy hash for readback. Ops must integrate the Publisher branch and wire that consumer. Until then the next article live on the site and social within its window is **not proven**. No live publication or deployment was attempted in this engineering run.

## Evidence

Final regression: **123 passed** in one pytest process, covering the canonical coordinator, retained native continuation and site-first behavior. See [final-regression.xml](final-regression.xml). The separate native-executor selection passed 39 checks. Ruff passes on all eight changed source/test files.

- [execution.json](execution.json): actual launch configuration, deployed-source base and external consumer identity. Model/effort: gpt-6.1-sol/high, CONFIGURED_NOT_OBSERVED; no editorial model calls.
- `site-and-native.xml`: focused site/native checks, including synthetic native observation binding in isolated test stores.
- `native-compatibility.xml`: retained October native publication/recovery tests plus site cases, 26 passed before the final follow-up checks.
- `compatibility-initial-failure.xml`: first compatibility run, 107 passed / six historical-fixture failures; fixtures were then explicitly pinned to their retained Substack-first epoch.

The branch starts from the deployed live-root commit `a4d60fe0d10de97a06603a8de6b6c3e88c79edcd` to preserve its integrated publication and recovery fixes. `origin/master` at dispatch was `5be8fc63317be06d8319f3dd51ac4137a107cbb5`, which predates those dependencies. Only CC-154 changes follow the live-root base. This run never merges or applies the branch to a live root.
