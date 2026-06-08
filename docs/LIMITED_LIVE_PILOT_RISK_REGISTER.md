# LIMITED LIVE PILOT RISK REGISTER

| Risk | Severity | Likelihood | Detection | Mitigation | Required Gate Before Live |
|---|---|---|---|---|---|
| Accidental public posting | High | Medium | Audit log | Strict default NO-GO policy | Dedicated private staging channel / manual review only |
| Secret leakage | Critical | Low | Scanners | Secret manager, no keys in repo | Implement dedicated offline secret manager |
| Platform policy mismatch | High | Medium | Review | Manual policy gate | Operator verify TOS / API limits manually |
| Scope mismatch | High | Medium | Platform rejected | Enforce staging contracts | Verify API scopes (e.g. basic profile vs full) |
| Malformed content | Low | High | Validation | Schema contracts, formatting | Strong dry-run validation |
| Financial advice / market-call phrasing | Critical | Low | Policy engine | Strict regex, local LLM evaluation | Policy engine regex checks must be mature |
| Political/partisan drift | High | Low | Policy engine | Sentiment/bias evaluation | Policy engine regex/classifier must be mature |
| Unsupported current-event claims | High | Medium | Audit log | Require verified sources bundle | Strict source mapping |
| Provider hallucination | High | High | Human approval | Human-in-the-loop validation | Operator review prior to GO |
| Rate-limit errors | Low | High | Error logs | Backoff logic | Implement rate limiter in adapter |
| Duplicate posts | Medium | Medium | Audit log | Cache / idempotency keys | Ensure unique identifiers per post |
| Wrong account/channel | Critical | Low | Error logs | Staging IDs only | Hardcode testing IDs initially |
| Stale approval | Medium | Low | Queue | TTL on approvals | Expire pending requests after 24 hours |
| Missing rollback/delete/correction plan | High | Low | Incident | Define Delete API | Implement 'unpublish' adapter method |
| Metrics ingestion mismatch | Low | Low | Observability | Simple logging | Wait for V2 |
| Reputational risk | Critical | Low | Brand monitoring | Private staging first | Only execute pilot in private environment |
| Over-automation | High | Low | Audit | Force manual step | Autonomous posting strictly DISABLED |
