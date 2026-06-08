# TELEGRAM PRIVATE STAGING DRY-RUN OPERATOR PACKET

**IMPORTANT: Do not paste any Telegram bot tokens or real chat IDs into this document, into git, or into the chat window. No network/API execution is occurring in this packet.**

## 1. Current Decision
**NO-GO FOR LIVE CREDENTIALS NOW.** 
The system remains in a strictly local dry-run state.

## 2. Rationale for Telegram Private Staging
Telegram is selected as the optimal first future pilot platform due to:
- Native support for strictly private, invite-only sandbox channels.
- Simple, deterministic bot API that avoids complex OAuth scopes.
- Immediate visibility into output formatting via native mobile/desktop apps without public exposure.

## 3. Operator Prerequisites (Offline)
Before a future GO, the operator must:
1. Create a private Telegram channel specifically for staging.
2. Create a Telegram Bot via BotFather.
3. Add the bot to the private staging channel as an admin.
4. Capture the Bot Token and Chat ID offline. **DO NOT COMMIT THESE.**

## 4. Required Local Artifacts
- `cc-contentops` output bundle (JSON).
- Local policy engine approval.
- Local provider dry-run payload.

## 5. Required Dry-Run Validation Gates
- **Policy Gate:** Must pass local deterministic regex checks.
- **Approval Gate:** Operator must explicitly approve the payload.
- **Provider Dry-Run Gate:** Must succeed locally without real keys.
- **Telegram Dry-Run Gate:** Must generate a deterministic Telegram-shaped JSON payload locally without a real token.

## 6. Manual Review Steps
For every test dispatch, the operator must:
1. Read the exact generated payload in the terminal.
2. Confirm the payload matches the safe local source bundle.
3. Explicitly type the manual approval confirmation.

## 7. Content Scope
- **Allowed:** Summaries of known safe Local Source Bundles only.
- **Forbidden:** No financial advice, no partisan persuasion, no guaranteed predictions. No autonomous replies or DMs.

## 8. Simulated Message Review Checklist
- Does the simulated payload accurately reflect the constraints?
- Is the text under Telegram's 4096 character limit?
- Are Markdown/HTML tags closed properly?

## 9. Caveat Checklist
- Does the post clearly contain a required caveat indicating it is experimental?
- Is the source explicitly cited?

## 10. Kill-Switch Checklist
- Is the local kill-switch file currently `ACTIVE` (blocking)? 
- Does the operator know how to toggle it?

## 11. Rollback/Correction Checklist (For Future Live)
- Operator must be able to manually delete the message using their native Telegram client.

## 12. STOP Conditions
- If the dry-run generates any unexpected replies, DMs, or out-of-scope content.
- If a secret is accidentally echoed to the console.

## 13. Future Explicit GO Requirements
A future task will require the explicit operator command:
`"I confirm the Telegram bot token and private chat ID are securely configured offline. Authorize staging deployment."`
