# Manual Evidence Source Submission Recovery Runbook

Jim, use this runbook to resolve validation and refresh errors:

## Recovery Paths

1. **Error: Missing Fixture File**
   - *Action*: Ensure `operator_evidence_fixture.json` exists in `docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/`.

2. **Error: Invalid JSON Syntax**
   - *Action*: Use a JSON formatter to verify commas, quotes, brackets, and brace matching.

3. **Error: Placeholders Found**
   - *Action*: Scan for and replace any occurrences of `"PLACEHOLDER_REPLACE_BEFORE_REVIEW"` or `"REPLACE_"` with real, verified evidence.

4. **Error: Unsafe Keywords Detected**
   - *Action*: Scrub any secrets, API keys, tokens, session cookies, local folder directories, or server configs.

5. **Error: Source Reference Missing**
   - *Action*: Supply a verified, active web link or file path reference.

6. **Error: Source Preflight Bridge Blocked**
   - *Action*: Confirm the manual validator ran successfully and generated its `operator_fixture_resolution_snapshot.json` output first.

7. **Error: Lifecycle or Consolidation Mismatch**
   - *Action*: Rerun the complete refresh script to cascade state variables sequentially.

8. **Error: Upload Bundle Stale Metadata**
   - *Action*: Re-execute the generator script to ensure metadata HEAD pointers match current git logs.

9. **Error: Accidental Real Fixture Staging**
   - *Action*: Remove `operator_evidence_fixture.json` from git stage by running `git restore --staged docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json`.
