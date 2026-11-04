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
Ops under this run's explicit instructions; a pushed branch alone is not DONE.
