# Six-Surface Accepted-Package Shadow E2E

Execution date: `2026-08-17`

Result: `PASS_SHADOW_PUBLICATION_CLOSED_LOOP`

The runtime report and per-surface receipts remain outside Git at:

`.task-runtime/v2-publication-adapter-reconciliation-provider-contract-correction-v1/shadow_demo/`

## Inputs

- longform:
  `pkg_33715fff75a0204cf430bbb763cb5ff9b6339e370b323c1d754aa6a91f24b4db`;
- Short:
  `pkg_2dfe4af587fd8135d04bae456b8c5b30a1560be91232b34f520cf7f05a71c0b2`.

These were read from the accepted native multiformat/multilingual task runtime. The run did not
render, transcode, synthesize audio, read a credential, or contact a provider.

## Surface result

| Surface | Package | Provider object | Draft/public semantics | Final state |
|---|---|---|---|---|
| YouTube normal video | longform | deterministic fake video ID | simulated public readback | `READBACK_CONFIRMED` |
| YouTube Shorts | Short | deterministic fake video ID | simulated public readback; Shorts flag unresolved by API | `READBACK_CONFIRMED` |
| TikTok | Short | none | `SEND_TO_USER_INBOX`; draft only; creator finalization required; public false | `READBACK_CONFIRMED` |
| Instagram Reel | Short | deterministic fake media ID | Instagram Login contract | `READBACK_CONFIRMED` |
| Instagram Story | Short | deterministic fake media ID | Facebook Login contract; no permalink dependency | `READBACK_CONFIRMED` |
| Facebook Page Reel | Short | deterministic fake video ID | Page-token `me/video_reels` contract | `READBACK_CONFIRMED` |

## Ambiguous acceptance

Positive proof:

- fake provider accepts media, client receives ambiguous timeout;
- state becomes `UNKNOWN_WRITE`;
- blind retry is blocked;
- readback discovers and reconciles the object;
- final state is `READBACK_CONFIRMED`.

Unresolved proof:

- the same ambiguous path enters `UNKNOWN_WRITE`;
- blind retry is blocked;
- readback does not establish an object;
- success is not manufactured;
- state remains `UNKNOWN_WRITE`.

## Operation counters

Every counter is zero: real provider writes, draft/private/unlisted writes, browser actions,
credential reads, V1 mutations, scheduler mutations, Remotion renders, localized picture renders,
audio generations, XHIGH, MAX and ULTRA.
