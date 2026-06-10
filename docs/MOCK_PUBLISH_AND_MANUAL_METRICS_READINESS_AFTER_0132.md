# Mock Publish and Manual Metrics Readiness (0132)

## Mock Publish Flow
The mock publish flow represents a deterministic local simulation that wires the 0130 dry-run payloads and 0131 approval ledgers into a mock execution outcome.
- **Not Real Publish**: There is no live platform request, no API client, and no real transport layer.
- **No Credentials**: No secrets or `.env` files are read.
- **No Scheduler**: The mock execution is immediate and synchronous in test scenarios.

## Manual Metrics Readiness
This contract defines expectations for how the success of a mocked (or eventually live) post will be measured.
- **Operator-Entered Only**: No platform scraping or automated metrics APIs are invoked. All values must be entered manually by an operator.
- **Null Policy**: Missing metrics are explicitly kept as `null` rather than coerced to `zero` to ensure data integrity during early pipeline testing.

## Relationship to other systems
- Depends on a validated 0130 `platform_dry_run_payload`.
- Requires an `operator_approved_for_mock_publish` state from the 0131 `approval_ledger`.
- Forms the basis for eventual live publication supervised platforms. 0130 legacy skipped tests do not govern this implementation.
