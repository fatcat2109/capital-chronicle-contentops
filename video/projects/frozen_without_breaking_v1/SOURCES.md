# Sources and rights register

Final-edit status: dependency lock as of 2026-08-15. The tables below preserve the broader candidate audit; this final lock overrides their earlier `PENDING_FINAL_RENDER_AUDIT` cells.

`LIKELY_CANDIDATE` means the current narration or cinematic direction expects the source or asset to survive. `CONDITIONAL_CANDIDATE` means it may survive only if the edit earns it. `TEXTURE_CANDIDATE` is qualitative context, not quantitative authority. `RECOMMENDED_EXCLUDE` means keep the provenance record but do not use the asset absent a later documented reversal. Exact local hashes, byte sizes, and hash state are in [`research/SOURCE_HASHES.csv`](research/SOURCE_HASHES.csv).

## Final dependency lock

- Factual authorities used in narration or native graphics: `BLS_EMPLOYMENT`, `BLS_EMPLOYMENT_VINTAGES`, `BLS_EMPLOYMENT_TABLES`, `BLS_CES_SERIES`, `BLS_SURVEY_COMPARISON`, `BLS_JOLTS`, `DOL_CLAIMS`, `BLS_PRODUCTIVITY`, `BLS_COMPENSATION_PRICES`, `BEA_GDP`, `CENSUS_RETAIL`, `FED_FOMC_STATEMENT`, and `FED_PRESS_CONFERENCE`.
- Factual candidate not used: `FED_BEIGE_BOOK`. The wider fact ledger also retains unused research candidates so rejected avenues remain auditable.
- Documentary media used, muted and illustrative only: commuters, empty office, finance team, grocery cashier, health-care nurse, job interview, office workers, and warehouse workers. The Costco-branded self-checkout candidate is `UNUSED_EXCLUDED`.
- Generated conceptual illustrations used and labeled on screen: `frozen_concourse_imagegen_v1.png` and `load_bearing_healthcare_imagegen_v1.png`. Neither is factual authority.
- Federal Reserve media used: `FED_20260729_LABOR_BASELINE` and an excerpt of `FED_20260729_DUAL_MANDATE`; `FED_20260729_EQUILIBRIUM_REACTION` is unused. Exact ranges are in [`AUTHORITY_CLIPS.md`](AUTHORITY_CLIPS.md).
- Primary-document derivative used: `fed_transcript_page_01.png` as a low-opacity chronology texture. Page 12 is unused.
- Audio used: seven locally generated Kokoro narration WAVs, seven original procedural chapter beds, one original procedural paper/relay accent, and authentic Chair/room audio in the two authority excerpts. No Pexels source audio, licensed music, cloned voice, or external SFX-library sample is used.

## Factual primary sources expected in the film

The working fact IDs are in [`research/FACTS_USED_CANDIDATES.csv`](research/FACTS_USED_CANDIDATES.csv), with methodology and caveats in [`research/ECONOMIC_RESEARCH.md`](research/ECONOMIC_RESEARCH.md). These sources support candidate narration and native charts; they do not license an inference beyond the cited observation. Current-release URLs can roll forward, so the final edit must preserve or archive the exact vintage it shows.

| ID | Candidate status | Official primary source | Candidate purpose | Final-use confirmation |
|---|---|---|---|---|
| `BLS_EMPLOYMENT` | `LIKELY_CANDIDATE` | [July 2026 Employment Situation summary](https://www.bls.gov/news.release/empsit.nr0.htm); [full release](https://www.bls.gov/news.release/empsit.htm) | July payrolls, unemployment, participation, earnings, revisions, sector detail, and benchmark notice | `PENDING_FINAL_RENDER_AUDIT` |
| `BLS_EMPLOYMENT_VINTAGES` | `LIKELY_CANDIDATE` | Archived releases dated [2026-05-08](https://www.bls.gov/news.release/archives/empsit_05082026.htm), [2026-06-05](https://www.bls.gov/news.release/archives/empsit_06052026.htm), and [2026-07-02](https://www.bls.gov/news.release/archives/empsit_07022026.htm), plus the [2026-08-07 release](https://www.bls.gov/news.release/empsit.nr0.htm) | First-print versus revised April-July payroll history | `PENDING_FINAL_RENDER_AUDIT` |
| `BLS_EMPLOYMENT_TABLES` | `LIKELY_CANDIDATE` | [CES Table B-1](https://www.bls.gov/news.release/empsit.t17.htm), [CPS Table A-12](https://www.bls.gov/news.release/empsit.t12.htm), and [Employment Situation FAQ](https://www.bls.gov/news.release/empsit.faq.htm) | Industry concentration/diffusion, long-term unemployment, and sampling-uncertainty threshold | `PENDING_FINAL_RENDER_AUDIT` |
| `BLS_CES_SERIES` | `LIKELY_CANDIDATE` | [Total nonfarm payrolls, CES0000000001](https://data.bls.gov/timeseries/CES0000000001) and [health-care payrolls, CES6562000101](https://data.bls.gov/timeseries/CES6562000101) | Same-vintage calculation of health care's share of annual net job growth | `PENDING_FINAL_RENDER_AUDIT` |
| `BLS_SURVEY_COMPARISON` | `LIKELY_CANDIDATE` | [Comparing employment from the household and payroll surveys](https://www.bls.gov/web/empsit/ces_cps_trends.htm) and [January 2026 population-control effects](https://www.bls.gov/cps/methods/population-controls/experimental-series-accounting-for-January-2026-population-control-effects.htm) | CPS/CES divergence and the January level break | `PENDING_FINAL_RENDER_AUDIT` |
| `BLS_JOLTS` | `LIKELY_CANDIDATE` | [June 2026 Job Openings and Labor Turnover Survey](https://www.bls.gov/news.release/jolts.nr0.htm) | Openings, hires, quits, layoffs, and the low-flow thesis | `PENDING_FINAL_RENDER_AUDIT` |
| `DOL_CLAIMS` | `LIKELY_CANDIDATE` | [Weekly Unemployment Insurance Claims report](https://www.dol.gov/ui/data.pdf) | Initial claims through 2026-08-08 and insured unemployment through 2026-08-01 | `PENDING_FINAL_RENDER_AUDIT`; the live PDF updates weekly, so snapshot/hash the cited vintage before lock |
| `BLS_PRODUCTIVITY` | `LIKELY_CANDIDATE` | [Q2 2026 Productivity and Costs](https://www.bls.gov/news.release/prod2.nr0.htm) | Output, hours, productivity, unit labor costs, and preliminary labor share | `PENDING_FINAL_RENDER_AUDIT`; revision-prone |
| `BLS_COMPENSATION_PRICES` | `LIKELY_CANDIDATE` | [Q2 2026 Employment Cost Index](https://www.bls.gov/news.release/eci.nr0.htm), [July 2026 CPI](https://www.bls.gov/news.release/cpi.nr0.htm), and [July 2026 Real Earnings](https://www.bls.gov/news.release/realer.nr0.htm) | Nominal pay, benefits, inflation, and purchasing power | `PENDING_FINAL_RENDER_AUDIT` |
| `BEA_GDP` | `LIKELY_CANDIDATE` | [Q2 2026 GDP advance estimate](https://www.bea.gov/news/2026/gdp-advance-estimate-2nd-quarter-2026) | Aggregate output and real final sales to private domestic purchasers | `PENDING_FINAL_RENDER_AUDIT`; advance estimate |
| `CENSUS_RETAIL` | `CHRONOLOGY_CANDIDATE` | [July 2026 Advance Monthly Retail Trade report](https://www.census.gov/retail/marts/www/marts_current.pdf) | Establish that the July retail release arrived after the July FOMC meeting | `PENDING_FINAL_RENDER_AUDIT`; the current PDF rolls forward |
| `FED_FOMC_STATEMENT` | `LIKELY_CANDIDATE` | [July 29, 2026 FOMC statement](https://www.federalreserve.gov/newsevents/pressreleases/monetary20260729a.htm) | Policy rate, vote, dissents, official assessment, and chronology | `PENDING_FINAL_RENDER_AUDIT` |
| `FED_PRESS_CONFERENCE` | `LIKELY_CANDIDATE` | [Official event page](https://www.federalreserve.gov/monetarypolicy/fomcpresconf20260729.htm), [official Board player](https://players.brightcove.net/66043936001/default_default/index.html?videoId=6402426667112), and [official transcript PDF](https://www.federalreserve.gov/mediacenter/files/FOMCpresconf20260729.pdf) | Chairman Kevin Warsh's contemporaneous July 29 labor baseline and policy reasoning | `PENDING_FINAL_RENDER_AUDIT` |
| `FED_BEIGE_BOOK` | `TEXTURE_CANDIDATE` | [July 2026 Beige Book summary](https://www.federalreserve.gov/monetarypolicy/beigebook202607-summary.htm) | Qualitative corroboration of low hiring and low turnover | `PENDING_FINAL_RENDER_AUDIT`; anecdotes are not representative and are not the views of Federal Reserve officials |

The four local `data/fred_*.csv` files are candidate chart caches disseminated by FRED for identified BLS series. Their hashes are registered, but the underlying BLS releases and series above remain the factual authority. A final chart must cite the relevant BLS source, retain the data-vintage date, and distinguish observations from calculations.

## Pexels documentary candidates

Rights check performed 2026-08-15 against the [Pexels license summary](https://www.pexels.com/license/) and [Pexels Terms of Service](https://www.pexels.com/terms-of-service/), last updated there on 2024-11-15. Pexels says its photos and videos are free to use, attribution is not required, and modification is allowed. For non-CC0 content, the terms describe an irrevocable, worldwide, non-exclusive, royalty-free license to use, copy, modify, or adapt, subject to prohibited uses. The finished film is intended to be a composite new creative work, not standalone redistribution.

The same terms also warn that identifiable people, brands, property, privacy, publicity, and other third-party rights may still apply and that Pexels does not warrant that all releases have been obtained. Accordingly, every clip is illustrative only. Do not identify a depicted person as unemployed, laid off, sick, counted in the July release, or affiliated with Capital Chronicle; do not imply endorsement; and mute the source audio unless it receives a separate final audit. Creator credit is included even where not required.

| Local file | Candidate status | Creator and source | License basis | SHA-256 | Editorial constraint | Final-use confirmation |
|---|---|---|---|---|---|---|
| `assets/documentary/commuters_subway_cc0_pexels_855749.mp4` | `LIKELY_CANDIDATE` | [Pixabay via Pexels, asset 855749](https://www.pexels.com/video/time-lapse-video-of-people-at-subway-station-855749/) | Source page marks `Free to use (CC0)` | `1806e0509a8edac5fcc5ea241834d9a663637440100f6697bdaac4e4d67707f2` | London setting; abstract movement/flow motif only, never U.S. documentary evidence | `PENDING_FINAL_RENDER_AUDIT` |
| `assets/documentary/empty_office_pexels_7844843.mp4` | `LIKELY_CANDIDATE` | [RDNE Stock project via Pexels, asset 7844843](https://www.pexels.com/video/an-empty-office-7844843/) | Pexels License | `eed8257554d527753cc00b3eb4a11c6fae3b3bf999d0848e60fdbf672b4c3710` | Generic absence/low-hire motif only | `PENDING_FINAL_RENDER_AUDIT` |
| `assets/documentary/finance_team_pexels_7593886.mp4` | `CONDITIONAL_CANDIDATE` | [Pavel Danilyuk via Pexels, asset 7593886](https://www.pexels.com/video/workers-discussing-the-company-finances-7593886/) | Pexels License | `a2476bb11c24ec012df1ceaf4da487fc3b0e308f8fc03d61dffe90f231d185a7` | At most a short detail fragment; do not imply the people are U.S. financial workers in the release | `PENDING_FINAL_RENDER_AUDIT` |
| `assets/documentary/grocery_cashier_pexels_4121754.mp4` | `LIKELY_CANDIDATE` | [Jack Sparrow via Pexels, asset 4121754](https://www.pexels.com/video/couple-paying-at-the-counter-in-the-grocery-4121754/) | Pexels License | `01a1d3b34fb1c812a769fabe480f976640684158dc5b94e750a72c2d3d4eb998` | Aggregate retail/service-economy illustration only | `PENDING_FINAL_RENDER_AUDIT` |
| `assets/documentary/healthcare_nurse_pexels_6130024.mp4` | `LIKELY_CANDIDATE` | [RDNE Stock project via Pexels, asset 6130024](https://www.pexels.com/video/healthcare-worker-taking-care-of-sick-patient-6130024/) | Pexels License | `e552203429e49cfdc24b8897e27f744fa0fb41164c53216acad7cd6d35d7bd65` | Illustrates the sector; make no claim about the depicted worker or patient's health/employment status | `PENDING_FINAL_RENDER_AUDIT` |
| `assets/documentary/job_interview_pexels_5438891.mp4` | `CONDITIONAL_CANDIDATE` | [Tima Miroshnichenko via Pexels, asset 5438891](https://www.pexels.com/video/an-interviewer-talking-to-an-applicant-5438891/) | Pexels License | `3b38bbfc6ac98b4597f9930c2e7817373d08c06301a894b2d38c9d37211d7679` | At most a short detail fragment; no claim that this is a real vacancy or failed U.S. application | `PENDING_FINAL_RENDER_AUDIT` |
| `assets/documentary/office_workers_pexels_6549254.mp4` | `LIKELY_CANDIDATE` | [Tima Miroshnichenko via Pexels, asset 6549254](https://www.pexels.com/video/people-working-at-an-office-6549254/) | Pexels License | `6aedd3d855ca6a701b869def023534932a1de6b29d30b3eeb4722231311cbb25` | Generic occupied-office wide; no specific employer or labor-status claim | `PENDING_FINAL_RENDER_AUDIT` |
| `assets/documentary/self_checkout_pexels_7457422.mp4` | `RECOMMENDED_EXCLUDE` | [Max Medyk via Pexels, asset 7457422](https://www.pexels.com/video/man-doing-self-checkout-in-supermarket-7457422/) | Pexels License | `0b9a0e54c82a803a72a098e65d5ff857782938e7ff6ec98127510eab9977a55e` | Visible Costco branding and an unsupported automation/AI-causality implication; retain only for provenance unless a later crop and editorial ruling reverse exclusion | `PENDING_FINAL_RENDER_AUDIT` |
| `assets/documentary/warehouse_workers_pexels_4293958.mp4` | `LIKELY_CANDIDATE` | [Tiger Lily via Pexels, asset 4293958](https://www.pexels.com/video/men-working-in-the-warehouse-4293958/) | Pexels License | `73001ff2fd8b3c5ea0423da1efa9eeb201549e03bd083d1e96db5b3f51c38545` | Generic goods-sector/labor-demand physicality only | `PENDING_FINAL_RENDER_AUDIT` |

## Generated conceptual illustrations

These two images were generated on 2026-08-15 with the built-in OpenAI image-generation capability. They are candidates for metaphorical chapter treatments only. They are not factual or documentary authority, do not depict a claimed real event or institution, and contain no intended identifiable real person. Prompt summaries and limits are preserved in [`research/GENERATED_ILLUSTRATIONS.md`](research/GENERATED_ILLUSTRATIONS.md).

| Local file | Candidate status | Candidate purpose | SHA-256 | Mandatory limit | Final-use confirmation |
|---|---|---|---|---|---|
| `assets/illustrative/frozen_concourse_imagegen_v1.png` | `LIKELY_CANDIDATE`; `ILLUSTRATIVE_ONLY` | Opening/ending metaphor for stalled labor-market flows without a mass-layoff rupture | `ba320886d7cd88779008c79569361e2fa74e45dc35496f494e3e5b79d2db47b5` | Do not attribute a real geography, station, event, worker, or measured condition | `PENDING_FINAL_RENDER_AUDIT` |
| `assets/illustrative/load_bearing_healthcare_imagegen_v1.png` | `LIKELY_CANDIDATE`; `ILLUSTRATIVE_ONLY` | Metaphorical transition for health care's load-bearing role in net payroll growth | `0721e153059b4d0c40084f17b47210fe42b9d4123f9a60de727cbfcdb8f98ec6` | Do not attribute a real hospital, workforce, event, person, or measured condition | `PENDING_FINAL_RENDER_AUDIT` |

## Federal Reserve authority material

All three clip files derive from the Board of Governors' official July 29, 2026 FOMC press conference. Speaker: Kevin Warsh, Chairman of the Board of Governors and Chairman of the FOMC. Preferred credit: `Board of Governors of the Federal Reserve System, FOMC Press Conference, July 29, 2026.` Exact transcripts and technical details are in [`AUTHORITY_CLIPS.md`](AUTHORITY_CLIPS.md).

The [Board disclaimer](https://www.federalreserve.gov/disclaimer.htm) says that, unless otherwise indicated, information on the Board website is in the public domain and may be copied and distributed without permission, with Board citation requested. It separately says Board seals, logos, and official insignia may not be used or reproduced without written permission. The delivered clips were cropped to exclude the visible Board seal; the final composition must be visually checked again after any reframing, transition, or background treatment. Do not imply Federal Reserve endorsement.

Third-party press questions create a separate risk. Clip 1 is prepared remarks. Clips 2 and 3 begin after the questioner finishes and contain only the Chair's answer. Do not extend their handles or restore any reporter face, voice, outlet identification, or question text without a separate rights decision. The derived page-12 transcript image begins with a fragment of a reporter's question; if it survives, crop to the Chair's words only.

| ID / local file | Candidate status | Official-player source in/out | Candidate editorial purpose | SHA-256 | Final-use confirmation |
|---|---|---|---|---|---|
| `FED_20260729_LABOR_BASELINE` — `assets/authority/fed_fomc_2026-07-29_clip01_labor_baseline_use_640x720.mp4` | `LIKELY_CANDIDATE`; strongest cold-open time capsule | `00:00:53.700–00:01:08.650` | Establish the Chair's pre-August-7 claim that job gains kept pace with the workforce, then test it against the later Employment Situation | `cc20def7f08c405171d2d1899f52d4591899f9f810dfb3f52ae689fe7c60d5c5` | `PENDING_FINAL_RENDER_AUDIT` |
| `FED_20260729_DUAL_MANDATE` — `assets/authority/fed_fomc_2026-07-29_clip02_dual_mandate_use_640x720.mp4` | `LIKELY_CANDIDATE`; preferably a final-act J-cut/audio bridge | `00:24:04.050–00:24:31.900` | Present the Chair's policy judgment that price stability and full employment are not an either-or proposition | `5a3e389695dbd4294f7a0009b7c1c0d5c145d11d653dce0a714d65308109821f` | `PENDING_FINAL_RENDER_AUDIT` |
| `FED_20260729_EQUILIBRIUM_REACTION` — `assets/authority/fed_fomc_2026-07-29_clip03_equilibrium_reaction_use_640x720.mp4` | `RESERVE_CANDIDATE`; omit unless indispensable | `00:30:06.200–00:30:26.500` | Date and test the Chair's view that the labor market was near equilibrium; never present that view as a settled post-release fact | `6a70e6220847d614807c881a4248affefcd0da5dc7c0626a9a0b374b7cca8aa1` | `PENDING_FINAL_RENDER_AUDIT` |
| `assets/documents/fed_fomc_2026-07-29_transcript.pdf` | `LIKELY_CANDIDATE` source document | N/A | Primary-document treatment and exact text verification | `be77d850144d99365ba8c92749ad21525e39eb3577d66d105ce0907a6656cb97` | `PENDING_FINAL_RENDER_AUDIT` |
| `assets/documents/fed_transcript_page_01.png` | `LIKELY_CANDIDATE` derivative | Transcript page 1 | Prepared-remarks document treatment | `f705a4868959eba093841f24aaf6072a6222686819e020a7c8d8534ec7fd6881` | `PENDING_FINAL_RENDER_AUDIT` |
| `assets/documents/fed_transcript_page_12.png` | `CONDITIONAL_CANDIDATE` derivative | Transcript page 12 | Dual-mandate document treatment | `f4a2127522776b10a10e4823f79ed07888bea9aac0926617e6952934464bdd36` | `PENDING_FINAL_RENDER_AUDIT`; crop away the reporter-question fragment |

## Narration model and final voice

The final narration was generated locally on CPU with Kokoro `0.9.4`, American-English voice `am_michael`, speed `1.18`, 24 kHz mono WAV. Seven locked files total 1,893 spoken narrator words and determine the exact chapter durations in `assets/audio/narration/narration_manifest.json`. Files under `review/voice_tests/` remain evaluation artifacts and are not film audio.

- Model repository: [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M). The model card labels the repository `apache-2.0`, describes the weights as Apache licensed, and publishes the model SHA-256 `496dba118d1a58f5f3db2efc88dbdc216e0483fc89fe6e47ee1f2c53f18ad1e4`, matching the local weight file.
- Voice manifest: [official `VOICES.md`](https://huggingface.co/hexgrad/Kokoro-82M/raw/main/VOICES.md) lists `am_michael` with SHA-256 prefix `9a443b79`, matching the local tensor's full SHA-256 `9a443b79a4b22489a5b0ab7c651a0bcd1a30bef675c28333f06971abbd47bd37`.
- Inference library: [hexgrad/kokoro](https://github.com/hexgrad/kokoro), locally installed as `kokoro==0.9.4`; the local Apache 2.0 license file hashes to `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`.
- No separate per-voice license notice for `am_michael` was located. The current basis is that the voice tensor is distributed inside the Apache-2.0 model repository. Preserve the upstream license if redistributing the software, model, or voice files, and credit Kokoro in production provenance.
- `am_michael` is a stock model voice, not a request to clone or impersonate a real person. Do not assign it a human identity or market the output as a real speaker.
- Generation/provenance is implemented by `scripts/generate_narration.py`; the manifest records engine, voice, speed, sample rate, word counts, duration, and frame lock. Individual final WAV SHA-256 values are recorded in `research/SOURCE_HASHES.csv` and the execution receipt.

## Sound design status

`CONFIRMED_ORIGINAL_PROCEDURAL`. `scripts/generate_original_sound.py` created the seven chapter beds and the paper/relay accent deterministically from NumPy synthesis with no imported samples. The render packages the beds as 192 kb/s M4A and retains the source WAVs under `assets/audio/sound/`. There is no licensed music track or external SFX-library asset.

Native Pexels audio is muted. Authentic room tone retained inside a Federal Reserve clip is not original local sound design; it follows the Federal Reserve rights entry above.

## Final confirmation procedure

Before delivery:

1. Export the exact rendered media dependency list and exact spoken fact IDs.
2. Change only surviving entries from `PENDING_FINAL_RENDER_AUDIT` to confirmed; explicitly mark or prune unused candidates without rewriting history.
3. Re-hash every surviving source and derivative, plus the final narration WAV and each original sound file.
4. Check that no Federal Reserve seal/logo, reporter material, Costco mark, misleading identifiable-person treatment, generated image presented as documentary evidence, or unregistered source audio appears in any frame or channel.
5. Preserve source/date labels and the July 29 Fed versus August 7 jobs-report chronology.
