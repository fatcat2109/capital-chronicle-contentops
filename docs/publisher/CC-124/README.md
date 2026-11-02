# CC-124 — Standing publication interval

The standing entry refused the run at 02:13 GMT+7 on 3 November 2026:
`STANDING_PUBLICATION_NOT_YET_DUE`. Its next eligible time is **04:20:08.539332
GMT+7 on 3 November**. The existing 3.5-hour interval starts at the previous
canonical article's first verified readback; later readbacks do not restart it.

The actual CLI result is saved in [standing-result.json](standing-result.json).
[validation.json](validation.json) records the checks and the configured launch
model, `gpt-6.1-sol/max`, as `CONFIGURED_NOT_OBSERVED`. The operating source was
`672f57e5`; this branch starts from fresh `origin/master` and changes evidence only.

No article operation was created. No editorial role, source request or public
send ran. The shared lease was released. No implementation changed, so pytest
was unnecessary; the actual entry and read-only assertions verify the refusal.
The existing Publisher runner can resume CC-124 at or after 04:20:09 GMT+7,
subject to the current guards. No chat or schedule was changed.
