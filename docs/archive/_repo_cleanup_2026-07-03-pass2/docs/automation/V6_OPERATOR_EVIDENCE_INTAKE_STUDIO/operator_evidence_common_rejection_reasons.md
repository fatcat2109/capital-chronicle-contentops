# Operator Evidence Common Rejection Reasons

This document highlights common mistakes and reasons why submitted evidence is rejected during automated and human checks.

## Common Rejection Scenarios

1. **Empty or Placeholder Values**:
   - Leaving slots blank or using placeholder strings (e.g. containing `"PLACEHOLDER"` or `"REPLACE_"`).
2. **Inclusion of Secrets or API Keys**:
   - Pasting API keys, tokens, auth headers, passwords, or private key segments.
3. **Webhook Disclosure**:
   - Including raw Discord webhooks or server endpoints.
4. **Environment File Paths**:
   - Referencing `.env` file names or other dynamic local settings.
5. **Dynamic Local Folder Paths**:
   - Paths containing local system tags like `AppData`, `Temp`, or specific local user folders.
6. **Financial Advice or Trading Signals**:
   - Including buy/sell recommendations, price targets, guaranteed predictions, or trading indicators.
7. **Fabricated / Unverified Citations**:
   - Submitting fake citations, dead URLs, or mock sources that cannot be manually verified.
8. **Premature Platform Posting Claims**:
   - Setting dispatch flags or asserting that the output is ready for direct public deployment.
