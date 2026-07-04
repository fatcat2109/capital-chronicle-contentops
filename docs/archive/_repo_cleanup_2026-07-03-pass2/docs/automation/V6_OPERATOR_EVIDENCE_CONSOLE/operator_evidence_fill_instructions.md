# Operator Evidence Fill Instructions

Jim, please use this console folder to submit verified evidence.

## Core Workflow Steps
* **Step 1**: Jim copies the file `operator_evidence_fixture.blank.json` to `operator_evidence_fixture.json` and fills it with verified manual evidence.
* **Step 2**: Antigravity runs the validator lane after the filled fixture is available.
* **Step 3**: The validator scans the inputs and refreshes evidence/source submission status.

Note: Filling out the fixture does NOT automatically trigger approval, outbox posting, payload hash generation, or live dispatch.

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
