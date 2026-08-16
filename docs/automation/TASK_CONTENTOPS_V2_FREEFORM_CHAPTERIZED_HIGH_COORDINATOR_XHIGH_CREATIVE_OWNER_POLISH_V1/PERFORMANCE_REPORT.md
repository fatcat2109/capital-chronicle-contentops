# Performance Report

## Prepared bundle and dirty review

- Final prepared-bundle key: `9c2bcca341254f67fb8447a935690bcabcdc8aaa8aa164c68c5b2b041f6c35ee`
- Final bundle wall time: `5.563s`
- Every changed chapter lock reused the same prepared bundle.
- Chapter 2 opening dirty range, first pass, concurrency 4: `59.534s`; it exposed the handoff safe-margin defect.
- Chapter 2 opening dirty range, repaired pass, concurrency 8: `58.384s`.
- Chapter 1 authority dirty range, frames 0–520, concurrency 8: `19.568s`.
- Chapter 7 authority dirty range, frames 940–1520, concurrency 8: `123.967s`.

## Concurrency and hardware encode benchmark

An identical 45-second Chapter 4 range was rendered from the same prepared bundle at 1280×720 through required hardware H.264:

| Concurrency | Wall time |
|---:|---:|
| 2 | `225.087s` |
| 4 | `159.904s` |
| 6 | `163.349s` |
| 8 | `155.438s` |

Selected review concurrency: `8`. Hardware encode succeeded through Remotion/NVENC. The owner lock remained software x264 CRF 14 because the supported hardware path did not expose the same CRF quality contract.

## Changed-chapter lock renders

| Chapter | Cache key prefix | Wall time | Lock stream bitrate |
|---|---|---:|---:|
| 1 | `3644adb46921` | `145.993s` | `3,091,738 bps` |
| 2 | `425b7d0e7786` | `387.946s` | `3,542,270 bps` |
| 3 | `4dd8c7ca6e41` | `1,429.111s` | `3,538,028 bps` |
| 4 | `bea13f5a96c6` | `366.571s` | `4,178,904 bps` |
| 6 | `ca567a09399c` | `709.913s` | `2,541,742 bps` |
| 7 | `99c968545fe7` | `1,044.214s` | `2,879,323 bps` |

Total changed-picture lock time: `4,083.748s` (`68:03.748`). Chapter 3 was the dominant compositional cost.

An identical post-lock Chapter 1 request returned `cache=HIT` with the same key, SHA-256, and recorded probe in `0.9s`, without invoking Remotion.

## Assembly and verification

- First concat attempt failed safely because repaired Remotion locks and reused Chapter 5 disagreed on pixel-range metadata.
- H.264 VUI correction to yuv420p limited BT.709 used stream-copy bitstream filtering for all seven units.
- Seven-unit picture concat used stream copy and completed in `0.490s`.
- Final AAC/faststart mux copied video; observed wall time was approximately `61s`.
- Complete final-master video+audio decode: `24.482s`, exit `0`.
- Six dense actual-master contact sheets: `23.5s`.
- No separate attachment encode was required.
- 4K render time: `0s`.

Audio-build wall time was not instrumented in the original successful invocation; the build receipt records exact inputs, outputs, duration, sizes, and hashes rather than inventing a timing value.

## Network and cost

- Network use: one bounded official Federal Reserve source download plus two direct Incompetech CC BY 4.0 music downloads.
- Pixabay candidates were not used.
- No ElevenLabs, HeyGen, broadcaster scraping, paid premium API, or platform write.
- Separately billed media/API cost: `$0`.
