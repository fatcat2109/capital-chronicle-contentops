# V6 Next Task Pointer

Current task: `TASK_CONTENTOPS_V6_FINAL_RELEASE_GO_NO_GO_REHEARSAL_V0` — Final release rehearsal executed live/provider generation and dispatch. Broad dispatch succeeded for Substack, LinkedIn, X post/replies, Facebook Page, Telegram, Threads post/replies, and Discord; Instagram failed before publish because the selected image URL returned HTTP 404. Runner fallback media has been hardened; final verdict remains PARTIAL_FAILURE until scoped Instagram retry passes. (COMPLETED LOCALLY; commit pending)

Recommended next task:

```text
TASK_CONTENTOPS_V6_INSTAGRAM_MEDIA_BINDING_AND_IDEMPOTENT_RETRY_REHEARSAL_V0
```

Purpose: Verify a durable public Instagram media URL/binding, add idempotent retry controls so successful platforms are not reposted, run a scoped Instagram retry/readback, and reconcile final release readiness evidence.
