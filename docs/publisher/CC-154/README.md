# CC-154 — site-first Publisher delivery

Publisher now exports the exact reviewed article package as `site_publication_candidate_v1.json`. A bound native readback of its exact site URL and admitted public-copy hash unlocks social dispatch. Social uses the site URL and runs before Substack; pending social browser work defers Substack so its code tab cannot park unfinished social actions.

The existing durable coordinator, store, outbox, dispatch identities, native begin/submit protocol, JIT identity checks, rights/public-copy guard, KILL_SWITCH and UNKNOWN_WRITE recovery remain the owners. No scheduler, second publisher, mailbox read, email-code entry or automated human-help wait was added. Historical sealed plans retain their policy. New lifecycle plans use `SITE_FIRST_V1`.

A code-screen return records `SUBSTACK_DRAFT_AWAITING_OWNER`, the exact draft ID, page ID and URL. Decision 54 governs the retained tab: leave it open and untouched for Jim. A later exact readback can confirm the same Substack object without another draft or publish call. Substack confirmation is reported separately from the site.

## Acceptance limit

A read-only synthetic test against the actual CC-149 Web consumer rejects a valid site-only publication record with **NEWSROOM_CANONICAL_REQUIRED**. It also restricts package lookup to `substack:<id>` and derives the article route from the Substack slug. See [consumer-compatibility.json](consumer-compatibility.json). The current mirror hook only triggers after that Substack-dependent feed append, so reusing it unchanged would retain the circular dependency.

Codex Web must consume the reviewed candidate without inventing a confirmed Substack outlet, render its `expected_site_url`, and expose the admitted article copy hash for readback. Ops must integrate the Publisher branch and wire that consumer. Until then the next article live on the site and social within its window is **not proven**. No live publication or deployment was attempted in this engineering run.

## Evidence

- [execution.json](execution.json): actual launch configuration, deployed-source base and external consumer identity. Model/effort: gpt-6.1-sol/high, CONFIGURED_NOT_OBSERVED; no editorial model calls.
- `site-and-native.xml`: focused site/native checks, including actual native observation binding in isolated test stores.
- `native-compatibility.xml`: retained October native publication/recovery tests plus site cases, 26 passed before the final follow-up checks.
- `compatibility-initial-failure.xml`: first compatibility run, 107 passed / six historical-fixture failures; fixtures were then explicitly pinned to their retained Substack-first epoch.

The branch starts from the deployed live-root commit `a4d60fe0d10de97a06603a8de6b6c3e88c79edcd` to preserve its integrated publication and recovery fixes. `origin/master` at dispatch was `5be8fc63317be06d8319f3dd51ac4137a107cbb5`, which predates those dependencies. Only CC-154 changes follow the live-root base. This run never merges or applies the branch to a live root.
