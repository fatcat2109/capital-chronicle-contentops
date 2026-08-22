# One Live Desktop-Primary Hybrid Canary

Authority date: 2026-08-23

Classification:

`PASS_ONE_LIVE_DESKTOP_PRIMARY_HYBRID_CANARY_9_SURFACE_RECONCILED`

The exact locked article was published once to Capital Chronicle Substack, read back, and then
distributed through exactly eight accepted destination packages. All nine destination records are
durably `RECONCILED_CONFIRMED`; `UNKNOWN_WRITE=0`.

This is canary evidence only. It does not claim `V1_FINAL_PRODUCT_ACCEPTED`, start 4/32, enable any
Desktop Automation, merge `master`, or grant another public write.

## Locked identity

- title: `State Department Approves Possible APKWS II Sale to Italy`;
- mode: `DATA_OR_DOCUMENT_LENS`;
- evidence: `official-primary-ffb8e742e0932254c29d`;
- Markdown SHA-256: `32bff9996e59bd924e9d41f10b4ed29fcbf9a431a38f187ee727929c12585d65`;
- HTML SHA-256: `2d037d6df2956779157b37a6d7ddc848a5f3b9111db339eb7bde3cbb1d1c5286`;
- release lock: `6c6f0c54117cf4d88478f1773de08c51c769d7e22e218af948ce5e24717c7241`;
- canonical article media: `0`.

Fresh prewrite JIT returned `READY` for all 9 exact identities with 9 active probes and no existing
unknown write. The starting branch SHA was the owner-required
`bcdada4674402be42d1624cdd1ea5029617aef98`.

## Public reconciliation

| Destination | Identity | Public object | Final readback |
| --- | --- | --- | --- |
| Substack | `capitalchronicle.substack.com` | [article](https://capitalchronicle.substack.com/p/state-department-approves-possible), `212337344` | Strict canonical readback plus public DOM; title and representative locked body boundaries match |
| Telegram | `@CapitalChronicle` | [post 66](https://t.me/CapitalChronicle/66) | Strict destination readback plus public DOM |
| Discord | channel `1519311669216673802` | `1540835756237660271` | Strict webhook destination-local readback |
| X | `@Capitalnicle` | [thread root](https://x.com/Capitalnicle/status/2091277088196383065) | Strict Edge readback plus public DOM |
| LinkedIn | Jim Pham | [share](https://www.linkedin.com/feed/update/urn:li:share:7497043017552277504/), `urn:li:share:7497043017552277504` | Native API proved the object but exposed limited content readback; independent public DOM matched identity/title/copy, and following the visible `lnkd.in` link resolved to the exact canonical URL |
| Facebook | Capital Chronicle Page | [post](https://www.facebook.com/1342369584748125/posts/1378354604482956), `106091951705748_1378354604482956` | Strict Meta Graph destination-local readback; guest browser was login-walled and was not used for certainty |
| Instagram | `official.capitalchronicle` | [post](https://www.instagram.com/p/DcW4tH6IF9R/), `17864143506663122` | Strict Meta Graph readback plus public DOM |
| Threads | `official.capitalchronicle` | [thread root](https://www.threads.com/@official.capitalchronicle/post/DcW4uleEzqm), `18138785134579167` | Strict Threads API readback plus public DOM |
| YouTube | `@CapitalChronicleYouTube` | [Community post](https://www.youtube.com/post/UgkxNTGL3K7fiqXMISPX71CEegWGHMz6PVN3) | Strict Edge readback plus public DOM |

X and Threads used the already accepted native `ordered_reply_chain` package shapes: one X package
created its root plus two ordered thread replies; one Threads package created its root plus one
ordered thread reply. These remain exactly two of the eight derivative destination-package attempts,
not additional derivatives or test objects.

Every derivative's immutable durable payload contains the exact observed Substack URL. No payload
contains `pending-publication` or an unresolved `[[SOURCE:...]]` marker.

## Safety and restore

- exactly 1 canonical attempt and 8 derivative destination-package attempts;
- exactly 9 canonical dispatch records; no extra dispatch ID;
- no blind retry and no recovery public write;
- `UNKNOWN_WRITE=0` before and after;
- all four V1 Desktop Automations remain `PAUSED`;
- 4/32 was not started;
- no writer or new evidence was invoked;
- runtime restored to its pre-task `SHADOW_ONLY` mode;
- LLM pause marker cleared and canonical Daily App supervisor/listener restored.

The transport receipt preserves the truthful intermediate LinkedIn adapter limitation. The final
receipt adds the independent public-browser reconciliation that closed it without another write.
Machine evidence and review screenshots are adjacent to this file.

Focused current publication, identity, Desktop-operator, Substack-adapter, and eight-platform tests
passed `161/161`; script compilation, CodeGraph currentness, and `git diff --check` also passed. A
broader run additionally exposed 18 failures in unchanged legacy Daily App lifecycle fixtures: those
fixtures return the historical publication classification and no longer cross the current managed
production-day qualification gate. The final machine receipt records that pre-existing fixture drift
without treating it as canary certainty.
