# Platform Adapter Selection Policy

This document establishes repo-wide policies for choosing between official APIs, supervised browser/CDP automation, and manual fallbacks.

## Selection Core Preference Rule
> Except for social platforms that provide a practical free official API for direct post/edit/comment workflows, prefer supervised browser/CDP adapters for paid-API platforms, overly restrictive platforms, high-friction app-review platforms, or platforms where official API automation is not worth the cost/complexity.

## CDP/Browser Governance & Strict Safeguards
CDP (Chrome DevTools Protocol) and browser automation must remain strictly supervised:
* **Cannot Bypass Checkpoints**:
  * Exact Preview
  * Payload Hash Verification
  * Destination Channel Binding
  * Jim's Approval Signature
  * Outbox Revalidation
  * Redacted Audit Logging
  * Idempotency Checks
  * Kill Switch Locks
  * Manual Fallback Routing
* **Strict Prohibitions**:
  * Selfbot behavior
  * Hidden posting or stealth activity
  * Direct Messaging (DMs)
  * Scraping third-party users/content
  * Automatic account switching
  * Cookie / localStorage / sessionStorage extraction
  * Raw token persistence in code/logs
  * Approval gate bypass
