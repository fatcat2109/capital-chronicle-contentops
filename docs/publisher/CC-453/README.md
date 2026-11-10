# CC-453: main-account Substack delivery

The publication stays at `capitalchronicle.substack.com`. New Notes use
`@capitalchronicle`, as Ops Product verified after Jim signed in (decision 119).
Existing articles, Notes, links, author names and issued request bytes retain
their original identities. No publication profile setting is changed.

The existing registry, handoff and minute executor share the main Notes identity.
The executor reads its profile URL from the existing route configuration. Its
browser step verifies the exact profile URL, handle and own-profile edit control
before a write. Note extraction uses the request's bound author.

Readback of an existing Note retains its URL's author. Recovery without a public
identity reads the original immutable publish request to retain that author.
An empty main-account feed cannot establish absence of an uncertain secondary
account write. The original coordinator, request hashes, claims and duplicate
checks remain the publication owners.

Validation: 56 targeted account, native transport and rationale cases, including
execution of the actual JavaScript identity and Note extraction steps; 67
targeted distribution, card and registry cases. A fixed-date card fixture now
uses that date at the write boundary. Production expiry remains enforced.
See [account tests](account-tests.xml) and [consumer tests](consumer-tests.xml).

The branch starts at the existing operating HEAD
`6df166df521a4c51f2b0414ccfdd1d7cbdaa97e5`. Fresh `origin/master` is its ancestor,
854 commits behind. This retains installed Publisher fixes and unrelated work.
The top-level launch arguments specify `gpt-6.1-sol/max`;
actual model telemetry is `CONFIGURED_NOT_OBSERVED`. No editorial model was called.

Live verification and the final remaining cause are recorded below after the
bounded coordinator continuation. Test results alone do not prove publication.
