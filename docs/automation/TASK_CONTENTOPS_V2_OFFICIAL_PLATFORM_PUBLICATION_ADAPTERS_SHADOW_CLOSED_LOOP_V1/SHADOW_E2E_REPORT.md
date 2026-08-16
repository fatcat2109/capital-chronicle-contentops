# Six-Surface Shadow Closed-Loop Report

Execution date: `2026-08-16`

Result: `PASS_SHADOW_PUBLICATION_CLOSED_LOOP`

Runtime report (intentionally outside Git):

`.task-runtime/v2-official-platform-publication-adapters-shadow-closed-loop-v1/shadow_demo/shadow_demo_report.json`

## Accepted real package inputs

- longform: `pkg_33715fff75a0204cf430bbb763cb5ff9b6339e370b323c1d754aa6a91f24b4db`
- Short: `pkg_2dfe4af587fd8135d04bae456b8c5b30a1560be91232b34f520cf7f05a71c0b2`

These are the real accepted English manifests emitted by the merged native multiformat /
multilingual package factory. The demo read them from the accepted task worktree. It did not
render, transcode, synthesize audio or contact a provider.

## Surface traces

Every trace executed:

`PACKAGE -> DESTINATION -> PREPARE -> WRITE_AUTHORITY_REQUIRED -> CONTROLLED FAKE EXECUTION -> PROCESSING -> PUBLISHED_UNCONFIRMED -> READBACK -> RECONCILIATION -> READBACK_CONFIRMED`

| Surface | Package | Attempt | Fake provider object | Final state |
|---|---|---|---|---|
| YouTube normal video | longform | `pubatt_18ccbb598bfc291b908d856d72720cc4c1e2942272c1e5c5a0e89ba1ee823719` | `ytv_1566f1913d8b6b61` | `READBACK_CONFIRMED` |
| YouTube Shorts | Short | `pubatt_81f1c01e9c00d30e4f09780aeb6b9d101602c2d18f644dd2afcc3908a67e03c5` | `yts_47a1796d72cc33da` | `READBACK_CONFIRMED` |
| TikTok | Short | `pubatt_dc8f56a3cef3967ba9d6994f640b882d153229efd8d36e9182b7a7b1becc5a82` | `tt_1eb6f600e9dd1146` | `READBACK_CONFIRMED` technical shadow only; live policy remains blocked |
| Instagram Reel | Short | `pubatt_a723449d715b21756419dc0e551c9d54b77a456899092cfb37fff03eb2294441` | `igr_ae47ef49ccd74789` | `READBACK_CONFIRMED` |
| Instagram Story | Short | `pubatt_c49d24dd3b70604f371e092c919d8c07496407377cedb921b82f728cab154103` | `igs_730e30f3e0eef5a1` | `READBACK_CONFIRMED` |
| Facebook Reel | Short | `pubatt_2d7ec0f5259241d04a0729cbcac03302468de2d48fd780156ef2b6690621f930` | `fbr_0fced95f530245e0` | `READBACK_CONFIRMED` |

YouTube Shorts reconciliation records that the Data API exposes no verified Shorts-specific flag;
the later canary must add public product-level classification readback. TikTok reconciliation
proves the request/state contract, not autonomous eligibility.

## `UNKNOWN_WRITE` proof

Positive recovery attempt:

- attempt: `pubatt_cac65998a101a225512372727a6a4cb7eaf913ea64d064511c9bb08e71c6a973`
- fake provider accepted Facebook Reel media, then the simulated client received an ambiguous
  timeout;
- state changed to `UNKNOWN_WRITE`;
- blind retry raised `UnknownWriteRetryError` and was recorded as blocked;
- provider readback found `fbr_40254348bd641f32` using the already-known initialized video ID;
- destination, title, description, upload/processing/publishing phases and permalink matched;
- final state: `READBACK_CONFIRMED`.

Negative unresolved attempt:

- attempt: `pubatt_a010e7fff39b7ae0a7ef2ec60b4c761d4b6af4318946a3cffe5911a8e6cc6712`
- the same ambiguous-acceptance path entered `UNKNOWN_WRITE` and blocked blind retry;
- readback did not establish an object or completed phases;
- reconciliation did not manufacture success;
- final state remained `UNKNOWN_WRITE`.

## Zero-operation receipt

| Operation | Count |
|---|---:|
| Real provider writes | 0 |
| Private/unlisted/draft writes | 0 |
| Provider network calls from fake execution | 0 |
| Browser actions | 0 |
| Credential reads | 0 |
| V1 mutations | 0 |
| Scheduler mutations | 0 |
| Remotion renders | 0 |
| Localized picture renders | 0 |
| Audio generations | 0 |
| MAX/ULTRA calls | 0 |
