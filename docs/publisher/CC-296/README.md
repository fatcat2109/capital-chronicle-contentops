# CC-296 LinkedIn member recovery

Base: Publisher operating root 260f0acf28e6868394834d030ea542b2f2bba732; it contains fetched origin/master 5be8fc63317be06d8319f3dd51ac4137a107cbb5. Existing unrelated WIP is preserved.

Configured top-level launch: gpt-6.1-sol/high, CONFIGURED_NOT_OBSERVED (PID 7564, started 6 November 2026 03:05 GMT+7). No editorial text has changed.

The original PPI dispatch is dispatch_2704c810355edb38f779637795ce85b0, operation cc124-next-article-20261105-a. Its two incidents retained only LinkedInAmbiguousWriteError, so their exact underlying provider failure cannot be reconstructed from those incidents. A current GET reproduces ConnectionResetError / WinError 10054 in ssl.SSLSocket.do_handshake, before an HTTP request can be sent. Curl independently reproduces a connection reset, including TLS 1.2/IPv4. network-phase.json preserves safe frame names only, with no credentials or request headers. This current reproduction does not retroactively prove the erased historical causes.

The second PPI attempt at 2026-11-05T01:02:17.919040Z followed the exact own-activity absence observation at 01:00:55.140Z, saved in the durable readbacks table at 01:01:32.370740Z. A further exact own-activity observation at 01:17:05.302Z proves absence after the second attempt. Original artifacts: CC-124/run-20261105-0610/linkedin-member-current-response.json and linkedin-post-retry-response.json. No exactly-once ordering violation was found.

The failing owner-absence regression is reproduced in baseline-test.txt. Generic media-comparison recovery replaced a valid own-activity absence return with a superseding request. The specialized coordinator still checks the exact operation, original intent, owner report, identity, loaded activity, target absence and observation age; the generic image check now leaves that observation available to those checks. Adapter ambiguity now preserves its safe cause and HTTP status through the existing coordinator incident.

First sub-step: 170 targeted tests passed in one pytest process (234.79 seconds), diagnostic-regression.xml. Further live transport recovery is in progress.

The second sub-step classifies a reset as definite no-write only when its exception traceback proves it occurred inside TLS handshake. Resets after send remain ambiguous. The existing coordinator uses its existing Neo executor when this exact pre-HTTP failure occurs. The saved native request binds the original intent hash, dispatch and failure cause; a resumed request reuses that action without calling the API again. Confirmed/ambiguous/rejected API writes do not trigger this fallback. No frozen copy, schedule or publisher changes.

Explicit LinkedIn completion now uses the existing transport-correction route after reconciled absence, while an object identity requires readback and cannot create a new post. 17 focused transport/correction tests pass (tls-fallback.xml); the additional exact native completion test passes (fallback-completion.xml).

A live retained PPI check found NATIVE_REVIEW_REVISION_CHANGED even though its native result and review notes still equal their exact publication seals (ef32ef642b4e5bfaab5fd973a80376e2d806bb570afd3bf02fa304d58cf08c17 and f6786092ecb7bb8eefa08d01b5493c14fa15c4baa29d059dfe003863c6168a5e). Recovery now accepts that already-dispatched sealed review only when the canonical object is confirmed, native result/review IDs/notes match, and every sealed artifact still hashes exactly. Source invalidations and changed native content, media or artifacts still refuse. A terminal no-write state may obtain fresh readback through the same coordinator. Seven targeted seal/compiler/readback tests pass (sealed-recovery.xml).
