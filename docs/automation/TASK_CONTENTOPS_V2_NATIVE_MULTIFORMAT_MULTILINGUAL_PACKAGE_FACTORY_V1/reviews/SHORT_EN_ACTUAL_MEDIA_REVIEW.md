# English Native Short — Actual-Media Creative Review

## Verdict

`BOUNDED_REPAIR_REQUIRED`

The English 9:16 Short is structurally strong and visually coherent, but the exact owner-review
media does not yet clear the factual-label and phone-readability gate. The required changes are
localized. Do not redesign the Short, replace its asset universe, change its central angle, or
expand its duration except as minimally required to preserve natural delivery of the corrected
measure names.

This is an XHIGH actual-media creative review, not owner acceptance. Voice timbre was explicitly
not judged.

## Media inspected

- English clean owner-review MP4:
  `.task-runtime/v2-native-multiformat-multilingual-package-factory-v1/renders/owner_review/frozen_without_breaking_short_en_clean.mp4`
- English contact sheet:
  `.task-runtime/v2-native-multiformat-multilingual-package-factory-v1/renders/owner_review/contacts/short_en_contact.png`
- English burned-caption sample:
  `.task-runtime/v2-native-multiformat-multilingual-package-factory-v1/renders/owner_review/contacts/short_en_caption_sample.png`
- Exact English caption sidecars:
  `.task-runtime/v2-native-multiformat-multilingual-package-factory-v1/audio/en/short/captions/captions.en.srt`
  and `captions.en.json`

The MP4 is a valid `1080x1920`, `30 fps`, `58.000 s` H.264/AAC deliverable. Transition frames,
placed-audio silence structure, exact caption timings, and representative frames at the main
handoffs were inspected read-only.

## Material repair 1 — restore the governed measure names

The current compression drops scope that materially defines three official measures.

### 1A. Private-demand measure

At `00:35.267–00:39.683`, narration/caption currently says:

> Yet private domestic final sales grew at a 3.9 percent annualized rate in the second quarter.

The on-screen label is `PRIVATE DOMESTIC FINAL SALES`. Governed anchor `GDP002` is **real final
sales to private domestic purchasers**. Omitting `real` loses the inflation-adjusted status;
omitting `to private domestic purchasers` turns the official measure name into an ambiguous
shorthand.

Required exact replacement:

> Yet real final sales to private domestic purchasers grew at a 3.9 percent annualized rate in
> the second quarter.

On screen, use the exact two-line label `REAL FINAL SALES TO / PRIVATE DOMESTIC PURCHASERS` and
retain `Q2 · ANNUALIZED · ADVANCE ESTIMATE`.

### 1B. Productivity-sector scope

At `00:41.600–00:49.771`, narration/caption currently says `Output rose 2.5 percent ... on just
0.2 percent more hours`, while the on-screen labels are only `OUTPUT` and `HOURS`. Governed
anchors `PRO001` and `PRO002` are explicitly **nonfarm-business** output, hours, and
productivity—not economy-wide output and hours.

Required exact replacement:

> Nonfarm-business output rose 2.5 percent from a year earlier on just 0.2 percent more hours.
> Productivity rose 2.2 percent—preliminary, and not proof that AI caused it.

On screen, relabel the two bars `NONFARM-BUSINESS OUTPUT` and `NONFARM-BUSINESS HOURS`, or add one
clearly readable shared header `NONFARM BUSINESS SECTOR` immediately above them. Retain `Q2 ·
YEAR OVER YEAR · PRELIMINARY` and the no-AI-causality line.

### 1C. JOLTS separation-rate scope

At `00:24.191–00:31.487`, narration/caption says `hiring, quitting, and layoffs`, while the
governed `1.1%` series and the on-screen label are **layoffs and discharges** (`JOL004`).

Required narration/caption wording:

> Now watch the doors. June hiring, quitting, and layoffs and discharges were all below February
> 2020 rates: 3.4, 2.0, and 1.1 percent.

The existing on-screen `LAYOFFS / DISCHARGES` label is correct and should remain.

These are label repairs, not a request for new analysis or new numbers. Regenerate only the
affected professional narration segments and rebuild the exact EN SRT/timed JSON from their
actual placed durations.

## Material repair 2 — make mandatory evidence furniture phone-readable

The primary numbers and headlines are readable. Several mandatory source/status elements are
not readable at practical phone scale, particularly:

- the repeating bottom BLS/BEA source line;
- the top-right `ILLUSTRATIVE FOOTAGE · NOT MEASURED WORKERS OR FACILITIES` label;
- `FEB 2020` / `JUN 2026` inside the three-door comparison;
- the engine scene's `ADVANCE ESTIMATE` and `YEAR OVER YEAR · PRELIMINARY` furniture;
- the final `NOT A BROAD LAYOFF COLLAPSE` qualifier.

These elements are visible in the 1080p source but collapse into microtype in the contact sheet
and at an approximately 390-pixel-wide phone presentation. They carry provenance, comparison
period, estimate status, or thesis constraint and cannot function as decorative fine print.

Bounded repair:

- raise required source/status/caveat furniture to an effective minimum of approximately `22–24
  px` on the 1080-wide master, using two lines where needed rather than shrinking type;
- increase the final `NOT A BROAD LAYOFF COLLAPSE` qualifier to at least `24 px` with stronger
  contrast;
- keep source/date furniture inside the existing safe margins;
- confirm legibility on a 390-pixel-wide downscaled review frame, not only on the 1080p master;
- do not enlarge the furniture enough to compete with the thesis or data hierarchy.

After enlargement, move the burned-caption rail upward only if necessary to preserve a distinct
source zone. Do not let captions cover source/date/status text.

## Material repair 3 — correct the final lockup line break

At the final hold, the current lockup breaks after `LOW-`, producing:

`A LOW-HIRE · LOW-QUIT · LOW-`
`FIRE FREEZE`

The dangling hyphen weakens the closing diagnosis. Use an intentional semantic break such as:

`A LOW-HIRE · LOW-QUIT`
`LOW-FIRE FREEZE`

Three lines are also acceptable if required by the locale-safe geometry. Do not reduce the
headline below its current readable scale to keep it on one line.

## Elements that pass and should be preserved

- The opening contradiction is immediate and legible without captions.
- The `−23K` / `4.1%` evidence-plane handoff is clear, and the significance caveat remains
  visible rather than being hidden in narration.
- The household-survey section correctly uses stock-change bars rather than animating invented
  individual flows. `−87K`, `−264K`, `−178K`, and the `4.1%` resolution remain unclipped and
  hierarchically clear.
- The three-door visual is a native 9:16 idea rather than a crop. Its before/after rates remain
  distinct, and the `LOW HIRE / LOW QUIT / LOW FIRE` transition is materially readable despite
  the underlying doors.
- The demand/output/hours/productivity scene has good primary-number hierarchy and keeps the
  no-AI-causality constraint on screen.
- Documentary crops are tasteful, generic, and do not show a visible brand or imply that the
  depicted people/facilities are the measured U.S. observations.
- Motion changes follow information changes. The longer static holds occur in the arithmetic
  and diagnosis sections where reading earns them; no unexplained motion stall was found.
- Placed-audio cadence includes useful air after the hook, after `Low hire. Low quit. Low fire.`,
  before the productivity proof, and at the ending. No cadence repair is requested beyond the
  minimum timing accommodation needed for the corrected official measure names.
- The English sidecar cues are ordered, non-overlapping, and match the currently placed spoken
  text. The burned-caption sample is high contrast, remains inside safe margins, and does not
  cover the output/hours/productivity evidence or the bottom source line.
- The dense productivity caption is large but remains readable for its actual exposure. Do not
  convert the caption treatment into an opaque generic subtitle card.

## Exact acceptance check after repair

Return one new English clean owner-review MP4, one English burned-caption review sample, and the
regenerated exact English SRT/timed JSON. The bounded repair passes when:

1. narration, captions, and screen labels use the corrected `GDP002`, `PRO001/PRO002`, and
   `JOL004` measure names above;
2. the corrected estimate-status/source furniture is readable in a 390-pixel-wide review;
3. the final lockup no longer strands `LOW-` from `FIRE`;
4. captions remain clear of source furniture and main evidence;
5. all currently passing framing, motion, hierarchy, caveats, duration discipline, and
   illustrative-footage boundaries are preserved.

No broader creative rewrite is authorized by this review.
