# CC-143: web-first articles and one daily email digest

Status: BLOCKED on the daily 19:00 execution route and Substack email-delivery readback.
Code is integrated into `A:/Capital Chronicle/ContentOps` and pushed through
`dc03c1d0c3432db9446031ab4b503e810829b8f9`; newer commits only retain this evidence.
Branch: `backlog/cc-143-web-first-digest`.
Current evidence: [run-20261104-1744/runtime-result.json](run-20261104-1744/runtime-result.json).

## Verified

New ordinary Substack intents use WEB_ONLY; only a frozen digest selects email.
Historical issued intents and request hashes remain immutable. The existing
outbox, leases, NativeNeoExecutor and DurablePublicationCoordinator own selection,
exact-object sends and recovery. No scheduler, store or email provider was added.
The existing host tick and native Publisher standing/scheduled/publication entries
surface the exact due digest continuation. Selection resumes an unsent digest,
includes each confirmed article once, and carries late records into the next index.
The existing deterministic renderer binds an original date/article-count card to
the exact structured index; no model authored new prose or facts.

Web-only article `223408612` was read back live. Its retained exact publish
observation records email disabled and no code request; the dashboard shows no
email recipients. No replacement article was created.

Digest `cc143-digest-2026-11-03`, post `223456283`, was published on 4 November
at 18:11:42 GMT+7. It resumes the existing prior-day index: the FOMC and CPI
articles, with both exact links once. The email checkbox was checked and
"Send to everyone now" reached the share center without a code request.
The public post, exact text/links and the original card bytes were read back.
The coordinator records `WEB_CONFIRMED_EMAIL_READBACK_REQUIRED`, with
`web_confirmed=true` and `email_confirmed=false`. A successful publish click is
not claimed as subscriber delivery.

Public URL: https://capitalchronicle.substack.com/p/capital-chronicle-daily-digest-november

21 focused digest checks pass after the last media-readback repair; 64 installed
native/digest checks passed before that final focused correction. The earlier
173 publication checks also passed. These selections overlap. Tests verify
live entry use, distinct canonical recovery, exact links, missing/wrong/duplicate
link refusals, original media binding, frozen restart and no duplicate send.
The actual production coordinator completed public reconciliation after both
readback repairs. Six tracked WIP hashes and the original 42 status entries in
the operating root remain unchanged. No app was restarted.

Launch arguments observed `gpt-6.1-sol/high`; actual runtime telemetry remains
CONFIGURED_NOT_OBSERVED. No editorial model call occurred in this engineering run.

## Remaining outside causes and next actions

1. `CapitalChronicle_ContentOps_V1_Daily_App_Runtime` is Disabled. The installed
   existing tick therefore cannot establish daily 19:00 preparation, and the
   native continuation still needs an active Publisher executor. Ops must supply
   that existing execution route. This run changed no schedule or application.
2. Substack displays no recipient/delivery result after its stated processing
   interval. Its recipient-details panel asks Jim to confirm the publisher
   agreement and privacy policy; the agent did not accept legal terms or read a
   mailbox. Retain exact post `223456283`; only read back and reconcile it when
   delivery evidence is available. Never send again or create another digest to
   resolve this uncertainty.

GitHub temporarily rejected pushes during its reported Git Operations incident;
the code push later succeeded. Final source/evidence Git readback is recorded by
the run. No chat was messaged. No default branch, Main checkout or schedule changed.
The existing midterm post is excluded from this confirmed feed because its
retained reconciliation is `RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE`, not
because its data has been assigned an arbitrary usage label.
