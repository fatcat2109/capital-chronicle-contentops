# Operator Facts Intake Guide (V6 Readiness)

This guide documents what the operator (Jim) must fill to resolve the missing evidence block on the ContentOps pipeline.

## 1. What the Operator Must Fill
You must complete the fields defined in `manual_evidence_fixture_template.json` to verify the factual grounding of the content.

## 2. Accepted Evidence Shapes
- **local_doc_path**: Paths to verified local PDF or document records.
- **repo_file_path**: Relative repository paths to markdown/JSON sources.
- **screenshot_path**: Relative paths to captured confirmation images.
- **official_source_url_to_be_reviewed_later**: Web links pointing directly to primary data sources.
- **operator_note**: Written description explaining verification steps.

## 3. Rejected Unsafe Values
Under no circumstances should any slot contain:
- Webhook endpoints (e.g. `discord.com/api/webhooks`)
- Tokens or environment file variables (e.g. `.env`)
- Local browser profile references or session cookies

## 4. Safety Constraints
> [!WARNING]
> **No Fake Citations**: Do not invent fake sources, references, or metrics.
> **No Signal Service Framing**: Do not include financial advice, trading signals, or long/short recommendations.
> **Validation Only**: This lane verifies slot completeness and input hygiene; it does not validate truth or make content publishable.
