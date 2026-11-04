# CC-154 continuation — 5 November 2026

Site-first Publisher behavior remains integrated. Full acceptance is blocked by
the Web consumer's `NEWSROOM_CANONICAL_REQUIRED`, reproduced against both the
CC-246 consumer and its CC-254 successor. Both accept the equivalent Substack
positive control. See [consumer-compatibility.json](consumer-compatibility.json).
These are read-only synthetic compatibility checks, not public article readbacks.

The consumer still requires a Substack outlet, uses `substack:<id>` for package
lookup, and derives its route from the Substack slug. Web/Ops must consume the
existing reviewed `site_publication_candidate_v1.json`, render its
`expected_site_url`, and expose `article_content_sha256` for exact readback.
Publisher can then complete the next article's site and social window proof.
No Substack confirmation may be invented to bypass this dependency.

CC-146/149 are superseded by CC-207/246. The CC-246 preview hook belongs to
CC-248, currently PROPOSED; it runs after the Substack-dependent feed append and
does not resolve pre-Substack candidate deployment. This run did not integrate
that separate item or change the Web checkout.

The Publisher regression initially passed 183 cases and failed one stale count:
the route now sends a ninth social copy to the LinkedIn company page. The repaired
test checks the exact destination set, confirmation, the site canonical URL,
and duplicate-free resume while Substack is unavailable. All 17 site-first cases
then passed; Ruff and whitespace checks passed. The initial failure is retained
in [publisher-tests.xml](publisher-tests.xml); the corrected result is in
[site-first-tests.xml](site-first-tests.xml).

The branch starts from Publisher's operating-root HEAD
`ff2ecc21591b05a223c78261b15a89ec1e97743c`, preserving its integrated fixes.
The launch was read back as `gpt-6.1-sol/high`, CONFIGURED_NOT_OBSERVED.
No editorial calls, public sends, mailbox access, schedules, chat messages or
application control occurred. The retained telemetry and CC-172 files stay
unstaged and outside this item. Integration and final checks are recorded in
[validation.json](validation.json).
