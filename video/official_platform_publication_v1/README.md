# Official platform publication control plane V1

This package consumes `contentops.v2.platform_neutral_publication_package.v1` manifests and
builds non-secret official API request plans for:

- YouTube normal videos and Shorts;
- TikTok Direct Post (technical shadow contract only; autonomous internal use is policy-blocked);
- Instagram Reels and Stories;
- Facebook Page Reels.

The common control plane owns destination binding, deterministic attempt identity, state,
write-authority enforcement, `UNKNOWN_WRITE` recovery, and canonical receipts. Provider modules
retain their real differences in identity, readiness, initiation, transfer, processing,
publication and readback.

`ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY` and `LIVE_PROVIDER_WRITE_AUTHORITY = False` are constants.
There is no environment or CLI flag that enables real writes. The package contains no HTTP
client, OAuth implementation, credential read, browser path, scheduler, V1 import, FFmpeg path,
renderer, or audio generator. `fake_provider.py` is an in-memory deterministic fixture and is
the only way the downstream state machine runs in this task.

Run the local proof from the repository root with accepted real package manifests:

```text
python -m video.official_platform_publication_v1.shadow_demo \
  --longform-package <accepted-longform-package.json> \
  --short-package <accepted-short-package.json> \
  --output-root <task-runtime-output>
```

The command performs zero network calls and writes only local receipts/reports beneath the
selected output directory.
