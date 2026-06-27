# Operator Evidence Submission Guide

This guide documents the procedures for submitting verified underlying evidence using the manual evidence fixture.

## Required Slots
All 10 slots must be supplied with non-empty, non-placeholder values:
1. `operator_idea_source_ref`: Reference path to verified source.
2. `topic_statement`: Short summary of the topic.
3. `factual_claims`: List of factual statements.
4. `source_notes`: Verification notes.
5. `citation_candidates`: List of citations.
6. `supporting_artifacts`: Local verification files/records.
7. `limitation_notes`: Contextual warnings or limitations.
8. `no_signal_disclosure`: Explicit confirmation of no financial advice.
9. `intended_content_lane`: Substack, Discord, or other channel.
10. `intended_canonical_article_angle`: Article framing angle.

## Verification Constraints
* Governance policies are dictated by the V6 Fast Ship Operating Profile.
* Under no circumstances should any slot contain raw credentials, webhook URLs, local config files, or authorization headers.
* Empty template placeholders are rejected as incomplete.
