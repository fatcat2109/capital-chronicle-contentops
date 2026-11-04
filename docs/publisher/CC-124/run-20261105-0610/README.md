# CC-124: 5 November article run

The September PPI retrospective is prepared in the existing production operation `cc124-next-article-20261105-a`. Publication and readback are still pending.

The branch starts at operating HEAD `f97eddbe97f68e03119ca8ae5ed7a8e3749e8085`; the remote default predates installed Publisher fixes. Current operating transport changes at `bd73f4ae` were preserved. Unrelated V6 ledgers and earlier-run files remain outside this item's commits.

The original BLS release is hash verified (`3ea265ba…`), published 15 October 2026 at 12:30Z and retained on 30 October. Its exact passages and the 24-month first-release history feed the live writer. Each history point was published by the event; subsequent revised prior-month figures are kept separate. The source recovery consumed one recorded retained-source request within the existing cap; no network request was made for that recovery.

The same MAX editor selected three useful charts, inspected the actual pixels, and found one defect in the nested-chart renderer: fractional percentages were rounded to integers and long labels clipped. The existing renderer now preserves requested precision, wraps labels and uses sufficient margins. Its 89 targeted tests passed serially in 22.42 seconds. Fix `9bb9de1e` is pushed and integrated under `contentops-live-20261105-cc124-chart-labels`. The live media consumer rendered the corrected chart; the editor accepted its exact hash after the one repair round. Passing charts and the licensed UK/2017 refinery photo were preserved.

The configured launch and native roles are `CONFIGURED_NOT_OBSERVED`; native invocation identities and exact returns are retained in the same operation. Light selected/prepared and `/root/ppi_max_writer` owns the MAX visual decisions, prose and rendered review. The user-reported interruption was reconciled only after verifying its worker was absent, releasing three exact own leases with their original fencing tokens. No other operation was restarted.

The source/value checks, chart tests, MAX media review, exact native stage returns and binary media paths/hashes are retained beside this file or in the bound runtime folder. No chat messages or schedules are changed. Screenshots and media bytes are kept as binary files; no image base64 is committed.
