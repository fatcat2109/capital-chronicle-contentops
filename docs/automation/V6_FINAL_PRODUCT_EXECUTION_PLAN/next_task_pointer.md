# V6 Next Task Pointer

Current task: `TASK_CONTENTOPS_V6_ARTICLE_EVIDENCE_MEDIA_QUALITY_HARDENING_V0` — Article evidence and media quality hardening is locally implemented and validated. Canonical article gates now enforce 2000+ words, source/citation density, and no raw public-body URLs; deterministic recovery drafts cannot pass publishability. Platform variants now include a media manifest, Telegram can use `sendPhoto`, Instagram no longer uses placeholder `picsum.photos` fallback media, and local chart rendering is available for operator-supplied CSV data. (COMPLETED LOCALLY; commit pending)

Recommended next task:

```text
TASK_CONTENTOPS_V6_FINAL_RELEASE_READINESS_EVIDENCE_INDEX_AND_OPERATOR_HANDOFF_V0
```

Purpose: Build a skeptical final-readiness evidence index tying prior live platform proof to the new stricter article/media gates, explicitly record the no-placeholder Instagram/media requirement and remaining API-unsupported caveats, and prepare the operator handoff for ongoing content operations.
