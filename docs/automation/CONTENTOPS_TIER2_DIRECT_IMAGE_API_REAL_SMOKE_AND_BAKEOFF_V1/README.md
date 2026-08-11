# Tier2 Direct Image API Real Smoke and Bakeoff V1 — Evidence

## Scope and revisions

- Task: `TASK_CONTENTOPS_TIER2_DIRECT_IMAGE_API_REAL_SMOKE_AND_BAKEOFF_V1`.
- Start HEAD: `cdb790d78e093421f0c9b09d430fd234ce3f247d`.
- Final task revision: the commit containing this packet. The exact local and remote SHA is
  established by post-push `rev-parse`/`ls-remote` readback in the final handoff.
- Task-owned source diff: `live_contentops/direct_image_api_v1.py`,
  `scripts/run_direct_image_bakeoff_v1.py`, and `tests/test_direct_image_api_v1.py`.
- Task-owned evidence: this directory. Generated context-index changes are staged separately
  after the final source change.
- Unrelated V1 evidence, ingestion sidecars/raw archives, runtime/store state, and browser or
  platform state were excluded.

## Credential and transport isolation

- Exact route: `POST https://ai.api-cheap.site/v1/images/generations`.
- Credential: `AI_API_CHEAP_API_KEY=PRESENT`; presence only is serialized.
- `NINE_ROUTER_API_KEY` was present at the initial environment check but was not read or used.
  A guarded-environment test fails on any attempted access to that name.
- No credential, authorization header, signed query string, or raw provider response is stored.
  The committed sanitized-artifact scan passed.
- This is a task-only diagnostic transport. It is not a 9Router route and grants no V1,
  browser, upload, platform, publication, or public-write authority.

## Process and artifact reconciliation

- Three pre-dispatch process checks reported
  `NO_MATCHING_PYTHON_IMAGE_GENERATION_PROCESS`; the post-run check reported the same.
- The existing `gpt-5.5` smoke image and two existing vertical bakeoff cells decoded as valid
  PNGs and were preserved by hash; they were not regenerated.
- Every dispatch intent is atomically journaled before the network call. An unfinished intent,
  timeout, disconnect, or worker loss becomes an ambiguous provider outcome with `NO_RETRY`.
- A post-run resume proof injected a transport that raises if called and completed with
  `resume_provider_calls=0`; the reconciled call count remained 9.

## Model outcomes

| Model | Smoke outcome | Calls | Bakeoff |
|---|---|---:|---|
| `gpt-5.5` | reconciled valid artifact | 1 reconciled | all 6 cells valid |
| `wan2.7-image-pro` | confirmed HTTP 400 rejection, `object{error}` | 1 | not run |
| `qwen-image-2.0` | confirmed HTTP 400 rejection, `object{error}` | 1 | not run |

The two HTTP 400 outcomes were not retried. Only the successful model entered the bakeoff.
Total generation calls, including the three reconciled earlier artifacts, were 9 of 24. No
ambiguous live outcome occurred. No winner was selected.

## Image artifact hashes and dimensions

| Cell | Dimensions | SHA-256 |
|---|---:|---|
| `gpt-5.5` smoke | 1122×1402 | `90d3ecf656fc5565ccb76eee515ae9e7ba46f57871f228a8d252ae13798130a2` |
| macro, landscape | 1672×941 | `195456f914e778eeb652ae27c16509cb0ab521f80fd32baf948967150396d833` |
| macro, vertical | 941×1672 | `b10e2bb4a3c69b8f37189cd4d7bb4ba5af6fc7b9300aaaa165319ab12945aff2` |
| corporate, landscape | 1672×941 | `836d137e12adac062332c8c1a262568bc3e99a2e1f9ac890fc50f4d4eb5a045b` |
| corporate, vertical | 941×1672 | `55ddb9e7f788a5ef43d21deffa81df4c2a789c6a10ade6b291f1b72294cac06a` |
| trade, landscape | 1672×941 | `e6f4bb556c5d991eb136fc4040a1e823a09add173ff4186418453391cb38a518` |
| trade, vertical | 941×1672 | `5985ded013cd217689f1a8d05f2fbbf8dab43319fd88cf9cd21da985e5c8ea7e` |

Contact sheets:

- `gpt-5_5__contact_sheet.jpg`: 1440×1158,
  `f34c50c3185388867dfbf345d0ae30e687c83ca230f9e4ec619c5f43f7337070`.
- `all_models__landscape.jpg`: 1440×434,
  `1b5da8bae7165e87129f5ccf382ff27c97ba318064156dca4b3f78b61af916e4`.
- `all_models__vertical.jpg`: 1440×434,
  `35c944fbdbbfe07035554010ea66718818e9297e3647ff06b8a8b2047eac56e6`.

## Validation

- `python -m pytest tests/test_direct_image_api_v1.py -q`: 17 passed.
- Coverage includes exact endpoint/payload, credential isolation and redaction, exact HTTP
  auth/route/model/capability/upstream/timeout classification, malformed responses, hard-wall
  timing, disconnect/worker-loss ambiguity, `NO_RETRY`, artifact resume, and unfinished-journal
  recovery.
- Ruff focused check: passed.
- `git diff --check`: passed.
- Sanitized artifact secret scan: passed.
- Deterministic context-index regeneration and `CODEGRAPH_CURRENT` check are required after the
  final source/evidence changes and recorded in the final handoff.

The generated images remain illustrative creative assets only, never documentary or factual
evidence. Visual review remains provisional and owner-controlled.
