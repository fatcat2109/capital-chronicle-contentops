# Source Intake Instructions & Compliance Guidelines

This document outlines the syntax constraints, validation rules, and compliance boundaries for operator-supplied source documents.

## Directory Location
All draft candidates to be processed by the intake parser must be placed in the inbox:
`docs/automation/V6_OPERATOR_RECOVERY_TO_EXPLICIT_LIVE_SCOPE_GATE_SOURCE_CANDIDATE/inbox/`

## Supported Formats
1. **JSON Files (`.json`)**:
   Must include a `"body"` field and an optional `"destination_label"` field.
   ```json
   {
     "body": "Your post content goes here.",
     "destination_label": "Announcements Channel"
   }
   ```
2. **Markdown Files (`.md`)**:
   Standard text file. The entire file content is processed as the raw message text.

## Parser Compliance Scans
The parser scans intake documents against the V6 Fast Ship Operating Profile policies:
1. **Placeholder Rejections**:
   The draft will be blocked if it contains debugging placeholders or template words:
   * `Viết nội dung thật ở đây`
   * `TODO`
   * `placeholder`
   * `lorem ipsum`
   * `sample only`
2. **Financial Advice Rejections**:
   Under the governance policy, no trading signals, position sizes, buy/sell/hold commands, or price predictions are allowed. Any document containing the following keywords is strictly blocked:
   * `buy`, `sell`, `hold`
   * `price target`
   * `position sizing`
   * `entry/exit`
   * `trade recommendation`
   * `guaranteed prediction`
   * `signal-service`
3. **Redaction Check**:
   No passwords, environment secret labels, or raw tokens may be present in the content body.
