# V6 Discord Live-Capable Supervised Pilot Adapter Contract

Local-only adapter scaffold. Disabled by default.

## Safety Boundary

- No Discord API or webhook calls.
- No env or `.env` reads.
- No webhook values, tokens, headers, bodies, or endpoint values.
- No executable HTTP request artifacts.
- No browser sessions.
- No public URLs or metrics.
- No live dispatch approval or publication readiness claim.

## Future-Live Requirements

Future execution remains blocked until separate explicit live task supplies:

- exact operator confirmation;
- credential-presence membership-only proof;
- destination binding;
- payload hash revalidation;
- kill switch;
- redacted audit;
- manual fallback.
