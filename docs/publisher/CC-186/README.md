# CC-186: images on every destination

Work is in progress on `backlog/cc-186-image-every-destination`. The dependency
base is the observed ContentOps live tag `contentops-live-20261104-cc124-thread-readback`,
commit `d210d8e2bfea9a8a5fe37d15a4c6429c05ccd69f`. The remote default branch
predates the installed Publisher fixes. Existing operating-root changes are preserved.

The top-level launch arguments configure `gpt-6.1-sol/max` on thread
`01a1a44a-844e-7f41-bcd8-d13aae5ce24f`, labelled `CONFIGURED_NOT_OBSERVED`.
No independent runtime model telemetry is claimed. This run performs its own
editorial work; it does not require a historical named agent.

Delivery is through the existing sole coordinator and adapters. Public-object
readback, image rights, exact source facts, identity, KILL_SWITCH and duplicate
prevention remain required. Tests use isolated fixtures. Integration belongs to
Publisher under Jim's decision 39 and this run's instructions; a pushed branch
alone is not DONE.

Resume on 4 November at 16:19 GMT+7 preserves the later installed CC-124, CC-171,
CC-183 and CC-154 fixes. The continued branch merges the pushed image-transport
sub-step with the observed operating-root HEAD `96891119f8bb212380167e3d40dae3e795d9d107`.
The active invocation is `01a1a5d9-b742-78a2-921c-44ae9bcbf17d`; observed launch
arguments configure `gpt-6.1-sol/max`, `CONFIGURED_NOT_OBSERVED`.

The focused card/LinkedIn/Discord/Cloudinary checks pass 38 tests. The complete
native publication regression file passes 15 tests, including immutable sent
artifacts, canonical-first routing, unknown-write readback and deduplication.
An interrupted earlier regression process produced no report and is not counted.
The image selection checks pass 22 tests. They prove that a retained public title
card cannot displace the selected local chart, and that the selected chart path
reaches the existing Neo and API consumers. MAX's channel-specific image choices
are retained.
