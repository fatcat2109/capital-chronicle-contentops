# Goal40 private release candidate review

Status: `PRIVATE_ENGINEERING_CANDIDATE_REVIEW_IN_PROGRESS`.
This is the same unfinished Goal40. Production remains paused; public-write authority is zero.

## Open the review

[Open the four-package player](C:/Users/bullw/.codex/worktrees/v2-current-native-factory/ContentOps/.task-runtime/goal39/runtime/cohort_review/goal40/review.html).

The page has four buttons and direct links to each clean video, captions, source
package and available captioned social video. Every file is local; nothing is uploaded.

| Package | Actual output | Present limit |
|---|---|---|
| Retail, English | 41 seconds; 1,230 frames; 13 measured caption phrases; clean and social video | Listening and final AV acceptance outstanding |
| Japan, English | 42.133 seconds of picture; 1,264 frames; 13 measured caption phrases; corrected bars and dedicated closing credits | Final continuous visual and listening acceptance outstanding |
| Retail, Spanish | Same 1,230 encoded picture frames; measured local narration; 10 summary caption cues; localized metadata | Original English graphics retained; Spanish listening gate outstanding |
| The Number Before the Story | 411.9 seconds; 12,357 frames; seven chapters; 117 exact measured narration phrases; 1920Ã—1080/30fps | Final continuous visual and listening acceptance outstanding |

Four private packages exist. No package has acquired final audiovisual, voice,
rights-release, platform or publication acceptance from these engineering results.

## What the candidate establishes

Japan preserves its original job/run and the original 30.452-second quarantine.
Native editorial reordering corrected the early payoff without changing its facts.
The measured-caption and final-picture successors preserve that history. The final
credit correction reuses narration/captions and changes only picture/mux/package
descendants in the existing ledger.

The longform is a dated measurement explainer, not current news or a forecast.
It uses the existing chapter owner and retained source/rights records. Three
chapters received native timing corrections to fit actual phrase audio. Four fitting
chapter durations were preserved. All 117 phrase waves were reused without faster
speech, fresh synthesis, text truncation or padding a short into a longform.

Spanish uses the existing local `ef_dora / 1.45` route. Its new narration, timing,
captions and metadata are separate from the English source package; exact clean
picture-stream identity is preserved. The 23-profile/six-surface capability snapshot
retains unavailable translation, voice, dependency and listening HOLDs.

## Repeat the bounded local operations

Run from the existing isolated checkout:

```powershell
Set-Location 'C:/Users/bullw/.codex/worktrees/v2-current-native-factory/ContentOps'
python -m video.unattended_core_factory_v1.manual status --config .task-runtime/goal39/config.json
python -m video.unattended_core_factory_v1.manual longform-reflow --config .task-runtime/goal39/config.json --revision goal40-provenance-closure
python -m video.unattended_core_factory_v1.manual longform-package --config .task-runtime/goal39/config.json --revision goal40-provenance-closure --caption-revision reflowed_phrases
python -m video.unattended_core_factory_v1.manual review-cohort --config .task-runtime/goal39/config.json --revision goal40 --packet .task-runtime/goal40/cohort-review-spec.json
```

These commands require the retained local runtime, source packets, free model/voice
files and canonical installed dependencies. They do not install, schedule, invoke
a model worker or authorize platform operations. Runtime files are preserved locally
and are not assumed to be present in a fresh clone.

## Verification and remaining work

The six focused test files passed: **67 tests**. Actual media, source seals, native
returns and package identities are recorded in [the integration evidence](INTEGRATION_EVIDENCE_V1.json).
Rendered frames and Neo playback establish their recorded checks only. Playback
reaching `ended` does not establish that a reviewer continuously saw every frame
or heard the narration.

Independent review identified two provenance gaps and two interruption gaps. The
first code corrections passed 39 focused tests; fresh exact-request native returns and
new Spanish/longform packages are built. The seven unchanged longform chapter
renders were reused only after exact current source/cache/frame/hash checks. The
117-wave inventory is a current remeasurement, not retroactive proof of the
original incomplete request. Independent correction review returned CHANGES_REQUIRED: semantic verdict enforcement,
recovery artifact sealing, accepted-package visibility and mux-repair crash recovery.
Those four paths are corrected; 67 focused tests pass, and the actual Spanish/recovery
replays preserve current packages and run IDs. Independent recheck remains pending.

CodeGraph refreshed and its freshness check passed. Scoped candidate commit
`98c53742` is pushed; PR91 readback confirms that exact head, OPEN/DRAFT, on
the unchanged PR90 base. No CI checks were reported. Independent correction
review and full Goal40 closure remain pending.

The [owning checkpoint](CHECKPOINT.md) retains interruptions and failed attempts.
