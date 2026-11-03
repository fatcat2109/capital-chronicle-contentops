# CC-177: integrate the retained Publisher deliveries

Base: operating branch `codex/contentops-local-publisher-20261030` at
`a4d60fe0d10de97a06603a8de6b6c3e88c79edcd`.
Jim decision 39 permits ContentOps operating-root fast-forward and a rollback tag.
The default branch, Main live root, schedules and public objects are unchanged.

Launch readback: `--model gpt-6.1-sol`,
`-c model_reasoning_effort="high"`, `CONFIGURED_NOT_OBSERVED`.
This engineering run invokes no editorial models.

CC-043: ported only 1cc1f908/beba137c/d88a36a3 from the reviewed CC-042 lineage.
Conflicts retain the current frozen-request guidance, latency-aware media checks,
publication-feed validation and optional-field handling, while adding desk citation
validation and the fixture-publication refusal. The initial source/schema/rights
selection passed 117 tests (`cc043-tests.xml`). Retained previews remain historical;
this run does not create or reapprove an article.

CC-044: ported 5167a6cc/41e77bfa (ten-channel metrics and failed-read accounting).
CC-047: ported f527ce33 (rights-bound source routes, coverage, new-binding cap 20).
Issued six/ten-request bindings keep their exact original limits.

CC-015's renderer is already in the operating root. It remains a local structured
renderer, not a replacement for the approved native MAX editorial owner.
CC-135's append-only feed producer is already in the operating root; the external
Main/site consumer is distinct from that producer.

Final validation, operating-root identity and outstanding consumer dependencies are
recorded below when the integration checks complete.

The coverage/engagement selection passed 110 targeted tests
(`coverage-engagement-tests.xml`).

External consumer readback: Main's pushed CC-122 consumer at
`e8f565d8f8a617c10b992253a49a6d8fc31a92b8` reads the production-day measurement
and last confirmed post only. `tools/product/contentops_digest_v1.py` has no
weekly engagement/coverage reader, and `main_daily_digest_v1.py` does not render
those sections. Installing Publisher's exporters cannot add that Main consumer.
CC-136 remains BLOCKED in the current backlog: its reviewed helper refused
`GIT_CHECKOUT_CONTROL_CHANGED` at `35e4e2d45a386be310782877ca6bcec46abd5c67`.
The requested next action belongs to Ops and Codex Main, not Publisher.
CC-014's backlog explicitly leaves its recurring export binding until after NFP.
These are real consumer dependencies, not launch/configuration/effort gates.

Final scoped validation: 537 distinct backend tests pass after correcting the one
baseline-reproduced stale workspace assertion; 40 focused UI tests pass;
TypeScript/Vite build passes. Initial 309-pass/one-failure output is retained in
`consumer-regressions.xml`; `workspace-current-policy.xml` supersedes that file's
single stale failure. No media validator or publication gate was weakened.
No added text artifact contains encoded image bytes.

CC-015 disposition: SUPERSEDED for public editorial integration by CC-043's
public desk projection plus the current native MAX writer/compiler path. The old
subscriber-field/AST-policy renderer remains intact as a local-only historical
utility. Its old private/subscriber input contract is not a public desk-export
adapter and is not connected to the public publisher. This is the integration
choice under CC-177's explicit supersession option; it does not claim the old
four-format renderer is running in the newsroom.

CC-043, CC-044, CC-047 and CC-135 must retain BUILT_UNMERGED until their named
Main consumers are wired. CC-177 cannot truthfully become DONE while those
external dependencies remain. Publisher will install all its tested code and
report the exact external causes, rather than mark a branch delivery as live
end-to-end completion.
