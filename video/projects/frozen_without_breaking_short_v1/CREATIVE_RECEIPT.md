# Creative Receipt — Frozen Without Breaking Native Short V1

## Execution identity

- Story/film: `frozen_without_breaking_owner_polish_v1`
- Assignment: `NATIVE_9_16_SHORT_CREATIVE_AUTHOR`
- Model: `gpt-5.6-sol`
- Reasoning effort: `xhigh`
- Authored project: `video/projects/frozen_without_breaking_short_v1/`
- Creative status: source-authored candidate only; no owner acceptance is claimed.

## Hook and editorial angle

Hook: **“How can jobs fall—and unemployment fall too?”**

Angle: make the apparent contradiction resolve on screen before naming the diagnosis. The Short
moves through three proofs: the household-survey arithmetic behind the falling unemployment
rate; the simultaneous cooling of hiring, quitting, and firing; and an economy producing more
with almost no additional labor hours. The editorial landing is not collapse and not optimism.
It is a low-hire, low-quit, low-fire freeze in which aggregate motion survives while worker
mobility narrows.

Truth and analysis remain separate. Exact observations carry source/date/status furniture.
“Freeze” and “less room” are Capital Chronicle synthesis, not an official classification or a
forecast. No motive is assigned to the July labor-force stock change, and productivity is not
attributed to AI.

## Final English narration

The intended delivery is intimate and controlled at approximately 150 words per minute. The
full narration is 150 words and is divided into the following semantic segments:

1. **Contradiction / hook**

   How can jobs fall—and unemployment fall too?

2. **Payroll observation and uncertainty**

   July payrolls fell 23,000. That preliminary move is too small to clear BLS’s usual
   significance threshold.

3. **Household-survey arithmetic**

   The household survey gives the arithmetic: employment fell 87,000; the labor force,
   264,000; the number unemployed, 178,000.

4. **Rate resolution**

   So the rate fell to 4.1 percent without more household employment.

5. **Flow diagnosis**

   Now watch the doors. June hiring, quitting, and layoffs and discharges were all below February
   2020 rates: 3.4, 2.0, and 1.1 percent.

6. **Memorable synthesis**

   Low hire. Low quit. Low fire.

7. **Private-demand counterweight**

   Yet real final sales to private domestic purchasers grew at a 3.9 percent annualized rate in
   the second quarter.

8. **Output, hours, and productivity**

   Nonfarm-business output rose 2.5 percent from a year earlier on just 0.2 percent more hours.
   Productivity rose 2.2 percent—preliminary, and not proof that AI caused it.

9. **Human consequence**

   The economy can keep moving while workers can’t.

10. **Diagnosis / close**

    This isn’t a broad layoff collapse. It’s a freeze—with less room for whatever comes next.

The deterministic audio handoff path encoded in the composition is
`public/assets/audio/narration/frozen_without_breaking_short_en.wav`.

## Governed anchors used

| Anchor ID | Viewer-facing use | Preserved status/caveat |
|---|---|---|
| `EMP001` | July payroll employment `−23K` | Preliminary; one-month estimate does not clear the usual BLS 90% significance threshold. |
| `UNC002` | Usual significance-threshold caveat | The Short does not overread the one-month point estimate or introduce the unused numeric threshold. |
| `EMP002` | July unemployment rate `4.1%` | Official CPS estimate. |
| `EMP011` | Household employment `−87K` | Monthly CPS sampling uncertainty is large. |
| `EMP010` | Labor force `−264K` | No individual motive or flow is inferred. |
| `EMP012` | Number unemployed `−178K` | Used only to explain the rate arithmetic with a smaller labor force. |
| `JOL002` | June hire rate `3.4%` versus February 2020 `3.9%` | June data, below the stated pre-pandemic comparison. |
| `JOL003` | June quit rate `2.0%` versus February 2020 `2.3%` | June data, below the stated pre-pandemic comparison. |
| `JOL004` | June layoffs/discharges rate `1.1%` versus February 2020 `1.3%` | Low layoffs alone are explicitly not presented as proof of health. |
| `GDP002` | Private domestic final sales `+3.9%` annualized | Q2 advance estimate; private-demand counterweight, not a forecast. |
| `PRO002` | Q2 output `+2.5%` y/y and hours `+0.2%` y/y | Preliminary; visually compared without claiming a causal mechanism. |
| `PRO001` | Q2 productivity `+2.2%` y/y | Preliminary; the Short explicitly rejects an AI-causality inference. |

No other numeric or factual claim is introduced.

## Stable viewer-facing English string map

All viewer-facing editorial copy lives in `src/strings.ts`. Stable keys and English values are:

| Stable key | English value |
|---|---|
| `brand.eyebrow` | CAPITAL CHRONICLE · LABOR |
| `brand.slug` | FROZEN WITHOUT BREAKING |
| `hook.jobs` | JOBS FELL. |
| `hook.unemployment` | UNEMPLOYMENT FELL. |
| `hook.question` | How can both be true? |
| `paradox.payroll.label` | PAYROLL EMPLOYMENT |
| `paradox.payroll.value` | −23K |
| `paradox.payroll.period` | JULY 2026 · PRELIMINARY |
| `paradox.rate.label` | UNEMPLOYMENT RATE |
| `paradox.rate.value` | 4.1% |
| `paradox.rate.period` | JULY 2026 · HOUSEHOLD SURVEY |
| `paradox.caveat` | The one-month payroll move does not clear BLS’s usual 90% significance threshold. |
| `arithmetic.kicker` | THE RATE’S ARITHMETIC |
| `arithmetic.subtitle.1` | Three monthly estimates. |
| `arithmetic.subtitle.2` | No story about motive. |
| `arithmetic.employment.label` | HOUSEHOLD EMPLOYMENT |
| `arithmetic.employment.value` | −87K |
| `arithmetic.laborForce.label` | LABOR FORCE |
| `arithmetic.laborForce.value` | −264K |
| `arithmetic.unemployed.label` | UNEMPLOYED |
| `arithmetic.unemployed.value` | −178K |
| `arithmetic.result.before` | THE RATE FELL |
| `arithmetic.result.after` | WITHOUT MORE EMPLOYMENT |
| `arithmetic.caveat` | Monthly CPS estimates are noisy. Stock changes do not identify individual motives or flows. |
| `doors.kicker` | NOW WATCH THE DOORS |
| `doors.subtitle.1` | Movement cooled on |
| `doors.subtitle.2` | all three thresholds. |
| `doors.then` | FEB 2020 |
| `doors.now` | JUN 2026 |
| `doors.hires` | HIRES |
| `doors.quits` | QUITS |
| `doors.layoffs` | LAYOFFS / DISCHARGES |
| `doors.hires.then` | 3.9% |
| `doors.hires.now` | 3.4% |
| `doors.quits.then` | 2.3% |
| `doors.quits.now` | 2.0% |
| `doors.layoffs.then` | 1.3% |
| `doors.layoffs.now` | 1.1% |
| `doors.thesis.1` | LOW HIRE. |
| `doors.thesis.2` | LOW QUIT. |
| `doors.thesis.3` | LOW FIRE. |
| `doors.caveat` | Low layoffs do not, by themselves, prove a healthy market. |
| `engine.kicker` | THE ECONOMY STILL MOVED |
| `engine.demand.label` | REAL FINAL SALES TO / PRIVATE DOMESTIC PURCHASERS (authored two-line label) |
| `engine.demand.value` | +3.9% |
| `engine.demand.note` | Q2 · ANNUALIZED · ADVANCE ESTIMATE |
| `engine.output.label` | OUTPUT |
| `engine.output.value` | +2.5% |
| `engine.hours.label` | HOURS |
| `engine.hours.value` | +0.2% |
| `engine.sector.label` | NONFARM BUSINESS SECTOR |
| `engine.productivity.label` | PRODUCTIVITY |
| `engine.productivity.value` | +2.2% |
| `engine.productivity.note` | more output per hour |
| `engine.period` | Q2 · YEAR OVER YEAR · PRELIMINARY |
| `engine.caveat` | The data measure a gap. They do not prove AI caused it. |
| `resolve.motion` | THE ECONOMY CAN KEEP MOVING |
| `resolve.stasis` | WHILE WORKERS CAN’T. |
| `resolve.notBreak` | NOT A BROAD LAYOFF COLLAPSE |
| `resolve.freeze` | A LOW-HIRE · LOW-QUIT / LOW-FIRE FREEZE (authored two-line lockup) |
| `resolve.watch` | LESS ROOM FOR WHATEVER COMES NEXT |
| `source.bls.employment` | BLS · EMPLOYMENT SITUATION · JULY 2026 |
| `source.bls.cps` | BLS · HOUSEHOLD SURVEY · JULY 2026 |
| `source.bls.jolts` | BLS JOLTS · JUNE 2026 |
| `source.bls.productivity` | BLS PRODUCTIVITY + BEA · Q2 2026 |
| `source.illustrative` | ILLUSTRATIVE FOOTAGE · NOT MEASURED WORKERS OR FACILITIES |
| `source.analysis` | CAPITAL CHRONICLE ANALYSIS |
| `caption.01` | How can jobs fall—and unemployment fall too? |
| `caption.02` | July payrolls fell 23,000. That preliminary move is too small to clear BLS’s usual significance threshold. |
| `caption.03` | The household survey gives the arithmetic: employment fell 87,000; the labor force, 264,000; the number unemployed, 178,000. |
| `caption.04` | So the rate fell to 4.1 percent without more household employment. |
| `caption.05` | Now watch the doors. June hiring, quitting, and layoffs and discharges were all below February 2020 rates: 3.4, 2.0, and 1.1 percent. |
| `caption.06` | Low hire. Low quit. Low fire. |
| `caption.07` | Yet real final sales to private domestic purchasers grew at a 3.9 percent annualized rate in the second quarter. |
| `caption.08` | Nonfarm-business output rose 2.5 percent from a year earlier on just 0.2 percent more hours. Productivity rose 2.2 percent—preliminary, and not proof that AI caused it. |
| `caption.09` | The economy can keep moving while workers can’t. |
| `caption.10` | This isn’t a broad layoff collapse. It’s a freeze—with less room for whatever comes next. |

## Visual, motion, sound, and caption intent

### Visual and motion

- **0:00–0:04.5 — Contradiction:** a vertical subway current moves behind four cold glass
  planes. “JOBS FELL” and “UNEMPLOYMENT FELL” enter from opposing directions; the visual
  contradiction is legible without narration.
- **0:04–0:11.5 — Two official headlines:** `−23K` and `4.1%` occupy separate tilted evidence
  planes over an empty-office field. The BLS significance caveat remains on screen rather than
  being hidden in narration.
- **0:11–0:23 — Arithmetic, not anecdote:** three stock-change bars reveal the relative monthly
  changes. No person icon crosses a boundary, avoiding a false individual-flow or “gave up”
  claim. The frame resolves into `4.1% / WITHOUT MORE EMPLOYMENT`.
- **0:22.5–0:37 — The doors:** three native vertical shutters compare February 2020 with June
  2026, then close into the memorable low-hire/low-quit/low-fire phrase. The layoff-health caveat
  remains visible.
- **0:36.5–0:48 — The engine:** warehouse motion remains illustrative while the exact real-final-
  sales measure and native output/hours bars do the evidentiary work. A shared `NONFARM BUSINESS
  SECTOR` header preserves the scope of the BLS measures. Productivity appears as a separate
  measured result, with the no-AI-causality caveat.
- **0:47.5–0:58 — Freeze:** active office imagery dissolves into an empty office; cyan glass
  edges close inward and desaturate the field. Motion survives behind the “workers can’t” line,
  then the frame locks on the diagnosis rather than a recession forecast.

The visual system uses Capital Chronicle ink, paper, copper, cyan, ice, and restrained serif
contrast. It deliberately alternates documentary texture, numerical cards, native data motion,
and a final physical metaphor. Source furniture and the illustrative-footage label are always
part of the main visual, so the story remains intelligible with captions hidden.

### Sound

- Narration should be close, dry, and controlled, around 150 wpm, with short air after the hook,
  `4.1 percent`, each item in “low hire / low quit / low fire,” and the final word `freeze`.
- Sound design should remain sparse: one restrained low-frequency contradiction pulse; three
  soft mechanical shutter closures; a subtle motor bed during the output/hours scene; then a
  near-silent final freeze. No trailer booms, typing clichés, or constant music bed.
- Documentary clips are muted in source. Their real-world ambience must not accidentally imply
  the depicted people or facilities are the measured U.S. observations.
- The authored Remotion source currently wires only the governed professional narration asset.
  Any later bed/SFX implementation must be separately rights-safe, deterministic, and mixed
  below speech.

### Captions

- `FrozenWithoutBreakingShortClean` is the canonical clean composition.
- `FrozenWithoutBreakingShortBurnedCaptions` enables the optional burned-caption treatment.
- Captions occupy a lower gradient rail rather than a generic opaque subtitle card. One semantic
  phrase per cue is accented in cyan. Captions do not replace the main visual evidence and do
  not cover the source line.
- Exact caption cues live in `src/timing.ts`; caption copy uses the stable `caption.01` through
  `caption.10` keys.

## Chosen local assets

All selected documentary media are generic illustrative footage and are labeled that way in the
composition. The deterministic parent must stage the exact governed bytes beneath this project's
`public/assets/documentary/` directory without changing their filenames.

| Governed local source path | Project render path | Why it is used |
|---|---|---|
| `A:\Capital Chronicle\ContentOps-worktrees\v2-freeform-xhigh-owner-polish-v1\video\projects\frozen_without_breaking_v1\public\assets\documentary\commuters_subway_cc0_pexels_855749.mp4` | `assets/documentary/commuters_subway_cc0_pexels_855749.mp4` | Human motion and constrained passage for the opening contradiction. The London setting is never identified as U.S. evidence. |
| `A:\Capital Chronicle\ContentOps-worktrees\v2-freeform-xhigh-owner-polish-v1\video\projects\frozen_without_breaking_v1\public\assets\documentary\empty_office_pexels_7844843.mp4` | `assets/documentary/empty_office_pexels_7844843.mp4` | Negative space behind the conflicting headlines and the final stasis handoff. |
| `A:\Capital Chronicle\ContentOps-worktrees\v2-freeform-xhigh-owner-polish-v1\video\projects\frozen_without_breaking_v1\public\assets\documentary\job_interview_pexels_5438891.mp4` | `assets/documentary/job_interview_pexels_5438891.mp4` | Physical texture beneath the three governed labor-flow “doors”; never represented as a measured interview. |
| `A:\Capital Chronicle\ContentOps-worktrees\v2-freeform-xhigh-owner-polish-v1\video\projects\frozen_without_breaking_v1\public\assets\documentary\warehouse_workers_pexels_4293958.mp4` | `assets/documentary/warehouse_workers_pexels_4293958.mp4` | Physical production texture beneath the native output/hours data treatment. |
| `A:\Capital Chronicle\ContentOps-worktrees\v2-freeform-xhigh-owner-polish-v1\video\projects\frozen_without_breaking_v1\public\assets\documentary\office_workers_pexels_6549254.mp4` | `assets/documentary/office_workers_pexels_6549254.mp4` | Active-work counterimage before the final dissolve into the empty office. |

The self-checkout clip is not used. No authority clip, generated image, real-person synthetic
media, or unsupported automation metaphor is used.

## Duration, composition IDs, and locale/layout extension points

- Native frame: `1080x1920`, `9:16`
- Frame rate: `30 fps`
- Duration: `1740` frames / `58.0` seconds
- Clean composition ID: `FrozenWithoutBreakingShortClean`
- Optional burned-caption composition ID: `FrozenWithoutBreakingShortBurnedCaptions`
- Default locale: `en`
- Composition prop extension points: `locale`, `burnedCaptions`, `narrationSrc`, and
  `narrationEnabled`
- `src/strings.ts` owns all viewer-facing editorial copy and the stable-key contract.
- `localeStrings` is the governed translation-map insertion point for `en`, `es`, `pt-BR`, and
  `ja`; incomplete locales safely fall back to English rather than rendering partial copy.
- `localeLayout` provides per-locale font scale, headline width, caption width, and line-height
  controls so translation can preserve meaning while using language-specific type and line
  breaks. Japanese can receive its own governed font choice when the locale is actually authored.
- `src/timing.ts` isolates beat timing and caption cues from the language maps.

## Deterministic HIGH handoff

The deterministic HIGH parent must, outside this creative-author execution:

1. stage the five exact governed documentary assets at the declared project render paths and
   verify rights-manifest/hash continuity;
2. produce the exact professional English narration WAV from the narration above and stage it at
   `public/assets/audio/narration/frozen_without_breaking_short_en.wav`;
3. install or reuse the accepted pinned Remotion dependencies, enumerate both compositions, and
   perform TypeScript/composition validation;
4. render clean and captioned review proxies, perform actual-media visual/audio/caption QA, and
   return any bounded creative defects for a fresh governed repair;
5. only after review, execute required deterministic hashes, receipts, packaging, and evidence
   registration.

## Explicit execution boundary

I performed source authorship and wrote this creative receipt only. I performed **no**
deterministic render, dependency install, FFmpeg operation, test, hash, Git/routing change,
package operation, wait/monitor action, public/platform write, V1 action, or scheduler action.
