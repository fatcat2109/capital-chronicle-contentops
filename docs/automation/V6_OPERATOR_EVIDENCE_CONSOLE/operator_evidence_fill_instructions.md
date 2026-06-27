# Operator Evidence Fill Instructions

Jim, please use this console folder to submit verified evidence.

## Instructions
1. Copy the file `operator_evidence_fixture.blank.json` to `operator_evidence_fixture.json` in this directory.
2. Complete each slot with verified manual evidence.
3. Once completed, run the validator:
   `python live_contentops/manual_evidence_fixture_validator_v6.py`

## Slots to Complete
* `operator_idea_source_ref`: Reference link or path to the original source.
* `topic_statement`: Short summary statement of facts.
* `factual_claims`: List of assertions made.
* `source_notes`: Notes detailing manual grounding checks.
* `citation_candidates`: List of citations for verification.
* `supporting_artifacts`: Local screenshot or documents.
* `limitation_notes`: Caveats or bounds of current claims.
* `no_signal_disclosure`: Affirmation that no financial signals or advice are present.
* `intended_content_lane`: Distribution target (e.g. Substack).
* `intended_canonical_article_angle`: Rationale or framing.
