# CC-359 — correct the 9 November zone updates

Uses the supplied BACKLOG correction verbatim, followed by the two standard notices. The two old status rows and all original public objects remain unchanged. The existing status-post package, production store, Native Neo executor and DurablePublicationCoordinator own all new sends and recovery. No schedule changes.

One correction on each of the five named destinations. Telegram and Threads bind their reply to the EUR/USD original, with both originals retained in the frozen payload. Discord's configured webhook has no native message-reply capability, so it posts a new correction. No confirmed X or Notes original was found in the store or visible profile history; they receive new corrections, with no invented parent identity. X carries the supplied correction and notices as one ordered thread within its 280-character limit.

The correction includes an owned fact card showing both source zones and that neither had been reached at the original clocks. No new analytical claim or model-authored copy is added. The native roles are not invoked for owner-supplied text.

A focused regression found and fixed the coordinator's omission of registered Substack Notes status posts from its dispatch list. The correction's consumer test proves all five destinations receive the frozen bytes once, repeat execution sends nothing, originals remain unchanged, and a changed reply target is refused. Telegram multipart and URL photo paths both bind the exact reply ID.

Validation: 16 passed, 104 deselected in 32.56s (correction, status publication and selected coordinator regressions), then 13 passed in 3.20s (correction and Discord adapter). One pytest process at a time. The fresh Discord GET exposed its image in embed.image with an empty attachments list; the adapter now checks both locations and supplies the known channel's public URL when the webhook omits guild_id. The test also rejects mismatched image bytes.

Launch command line read back from PID 38460: gpt-6.1-sol/high, CONFIGURED_NOT_OBSERVED; runtime model/effort telemetry unavailable. All source changes are integrated in A:\Capital Chronicle\ContentOps. The operating-root CLI used the production store. Five dispatches and five reconciliations are confirmed, with zero pending native requests. Both historical rows retain their original text. See [final-verification.json](final-verification.json).

Published and read back on 9 November 2026: Telegram at 20:57 GMT+7; X at 20:59 GMT+7; Notes at 21:01 GMT+7. Telegram's public page verifies the reply to 104; Threads' provider reply edge verifies its EUR/USD parent. X's card was inspected and compared after platform resizing (mean absolute channel difference below 0.66/255); Notes retained the exact original PNG SHA256. Discord's GET verifies the exact text and image embed; its CDN and proxy return HTTP 403 for a later binary re-download, which remains a recorded limit rather than an image-byte-match claim. Discord uses a new webhook post because that transport cannot make native message replies.

| Destination | Correction |
|---|---|
| Telegram | https://t.me/CapitalChronicle/107 |
| Discord | https://discord.com/channels/1519310996030750782/1519311669216673802/1569350151401639966 |
| Threads | https://www.threads.com/@official.capitalchronicle/post/DfhfaevlDDY |
| X | https://x.com/Capitalnicle/status/2119792055350337767 (notices in reply 2119792058236129749) |
| Substack Notes | https://substack.com/@deancapitalchronicle/note/c-382817690 |
