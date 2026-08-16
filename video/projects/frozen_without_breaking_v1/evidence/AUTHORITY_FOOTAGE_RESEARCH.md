# Authority Footage Research

Research date: 2026-08-15
Scope: isolated U.S. labor-market longform experiment only

## Recommendation

Use the Federal Reserve Board's July 29, 2026 FOMC press-conference recording, with conditions. The strongest clip is the prepared-remarks labor-market baseline at `00:00:53.700–00:01:08.650`. It gives the film a precise pre-release institutional view to test against the July Employment Situation published nine days later.

The Board's reuse policy makes the spoken, Board-produced recording supportable for reuse, but the same policy separately restricts Board seals, logos, and official insignia. The official 16:9 camera frame visibly contains a Board seal. The delivered film assets therefore use a fixed `640x720` crop (`x=240, y=0` from the `1280x720` official frame) that removes the Board seal throughout while retaining Chairman Warsh and the U.S. flag. Do not restore the uncropped frame without written Board permission.

Rights classification for the delivered cropped clips: `RIGHTS_SUPPORTABLE_WITH_CONDITIONS`.

An official-domain check of BLS and Department of Labor surfaces found the July 2026 data release and schedule, but no comparably relevant July-report talking-person briefing or statement with a clearer reusable media path. The FOMC recording is therefore the best current official-human source located; it is analytically useful precisely because it records the central bank's view before the later payroll report.

## Exact official source

- Event page: <https://www.federalreserve.gov/monetarypolicy/fomcpresconf20260729.htm>
- Official player instantiated by that page: <https://players.brightcove.net/66043936001/default_default/index.html?videoId=6402426667112>
- Federal Reserve Board Brightcove account: `66043936001`
- Brightcove video ID: `6402426667112`
- Official title: `FOMC Press Conference July 29, 2026`
- Recorded duration reported by the player metadata: `2704.021` seconds (`45:04`)
- Official transcript: <https://www.federalreserve.gov/mediacenter/files/FOMCpresconf20260729.pdf>
- Speaker identity: Kevin Warsh, Chairman of the Board of Governors and Chairman of the FOMC. Official biography: <https://www.federalreserve.gov/aboutthefed/bios/board/warsh.htm>
- Event date: July 29, 2026
- Board reuse policy: <https://www.federalreserve.gov/disclaimer.htm>
- Editorial comparison release: BLS Employment Situation—July 2026, released August 7, 2026: <https://www.bls.gov/news.release/empsit.nr0.htm>

The official event page directly embeds the above Board-account Brightcove asset and links the transcript. I found no non-Board production credit or separate rights notice on the event page, player metadata, captions, or transcript.

## Rights basis and limits

The Board's copyright/trademark policy says that, unless otherwise indicated, information on the Board website is public domain and may be copied and distributed without permission; it asks users to cite the Board. It also says that non-Board-associated material requires permission from its source.

The same policy is explicit that Board seals, logos, and official insignia may not be used or reproduced without the Board's written permission. That restriction matters here because a Board seal is visible at camera right in the official full frame. The delivered derivatives remove it by crop. This is a substantive rights control, not an aesthetic crop.

Conditions for use:

- Credit `Board of Governors of the Federal Reserve System, FOMC Press Conference, July 29, 2026` in `SOURCES.md` and, if practical, in a discreet source/date lower-third.
- Use only the delivered seal-free crops, or a tighter crop/mask that also excludes all Board seals/logos/insignia.
- Do not use the recording or surrounding design to imply Federal Reserve sponsorship, approval, partnership, or endorsement.
- Do not extract the Board seal, Board flag, logo, or lectern mark as a graphic element.
- Keep Chairman Warsh's authentic voice. Do not clone, synthesize, lip-sync, or materially alter his words.
- Preserve the July 29 date on screen or in immediate narration. These remarks preceded the July jobs report by nine days and are not a reaction to it.
- The conclusion here is a provenance/reuse assessment for this experiment, not legal advice.

No separate privacy/publicity blocker was identified for chair-only speech delivered by the sitting Chairman in his official capacity at the Board's public press conference. The no-endorsement and no-synthetic-manipulation conditions still apply.

## Third-party questioners and media risk

The press conference includes credentialed journalists from commercial organizations. Their voices, faces, questions, names, and employer marks may carry separate copyright, publicity, trademark, or contractual concerns even though the Board hosts the recording.

Accordingly:

- Clip 01 comes from prepared remarks and contains no questioner.
- Clips 02 and 03 are chair-only answer excerpts. Their local in/out points exclude every journalist's voice and image.
- Do not roll backward into the questions, use audience/reporter reaction shots, reproduce a journalist's question, or retain commercial outlet identifiers.
- If an edit needs the question's context, paraphrase the issue in original narration and then cut to the Chair's answer.
- Incidental room sound is acceptable only when no reporter speech is intelligible; the delivered clips contain chair speech only.

## Candidate clips

| Priority | ID | Official-player in/out | Local duration | Editorial purpose | Key risk |
|---|---|---:|---:|---|---|
| 1 | `FED_20260729_LABOR_BASELINE` | `00:00:53.700–00:01:08.650` | `15.015s` | Establish the Fed's July 29 baseline, then test it against the August 7 payroll release and revisions. | Must be labeled as a pre-release assessment, not a response to the July report. |
| 2 | `FED_20260729_DUAL_MANDATE` | `00:24:04.050–00:24:31.900` | `27.900s` | Humanize the policy conflict: the Chair rejects a strict price-stability/full-employment tradeoff. | It is a policy judgment, not empirical proof; the preceding journalist question is excluded. |
| 3 | `FED_20260729_EQUILIBRIUM_REACTION` | `00:30:06.200–00:30:26.500` | `20.400s` | State the policy reaction function when the labor market is viewed as near equilibrium. | `At equilibrium` is the Chair's July 29 assessment and must not be presented as settled fact after the August 7 release. |

Exact transcripts and hashes are in `AUTHORITY_CLIPS.md`.

## Acquisition and transformation

Acquisition used only the official event URL and its authorized Board Brightcove embed. No commercial broadcaster, social upload, random YouTube copy, browser session, cookie, credential, or paywalled source was used.

- Tooling: `yt-dlp 2026.03.17`; `ffmpeg 7.1.1`
- Official source rendition selected: `1280x720`, `29.97 fps`, H.264 video plus 48 kHz stereo AAC audio
- Source color: SDR BT.709
- Exact source-time section extraction was forced to keyframes.
- Film-use derivatives: `crop=640:720:240:0`, H.264/yuv420p, BT.709 tags, 48 kHz stereo AAC, approximate dialogue normalization to `-18 LUFS`, fast-start MP4
- Measured derivative loudness:
  - Clip 01: `-18.3 LUFS`, `-2.0 dBFS` sample peak
  - Clip 02: `-17.5 LUFS`, `-2.4 dBFS` sample peak
  - Clip 03: `-18.0 LUFS`, `-3.5 dBFS` sample peak

No reusable ingestion platform or helper was added; the three bounded derivatives were produced directly. The temporary uncropped source ranges and metadata JSON containing expiring CDN URLs were deleted after validation. They are recoverable from the official event/player while it remains online. This avoids leaving seal-bearing footage or transient signed media URLs in the reusable asset folder.

## Visual/editorial notes

- The official maximum is 720p, so do not make it a full-screen 4K hold. Treat it as a deliberately framed authority portrait, matte, split composition, or short bridge into data/workplace imagery.
- The `640x720` portrait crop is visually clean and stable. It keeps the speaker, microphones, lectern edge, and U.S. flag while excluding the Board seal.
- Clip 01 is visually more formal and downcast because the Chair reads prepared remarks. Clips 02 and 03 have stronger eye line and gestures.
- Prefer one or two clips, not all three by default. Clip 01 is the best factual/narrative hinge. Add Clip 02 only if the film explicitly develops the dual-mandate tension. Clip 03 is useful only if the film carefully distinguishes contemporaneous policy belief from later labor evidence.
- Let authentic room tone lead into each clip. Avoid a generic boxed talking head; the portrait crop can sit inside a wider causal composition, with the film's own typography and evidence occupying the negative space.

## Material deliberately rejected

- Commercial rebroadcasts and broadcaster-owned footage
- Random YouTube/social uploads
- Any reliance on assumed fair use
- Journalist questions, faces, voices, reaction shots, and outlet marks
- The uncropped Federal Reserve frame because the protected Board seal is visible
- Direct reuse of Board seals/logos/official insignia
- Ephemeral signed CDN URLs as durable provenance

## Research artifacts

- `research/authority_source_material/fed_fomc_2026-07-29_transcript.pdf`
- `research/authority_source_material/fed_fomc_2026-07-29.en.vtt`
- `research/authority_source_material/fed_board_disclaimer_2026-08-15.html`
- `research/authority_source_material/SHA256SUMS.txt`

These are research evidence, not viewer-facing film assets.
