# CC-186 Instagram visual selection repair â€” 4 November 2026

The outgoing transport now preserves the reviewed image order instead of the
canonical asset-list order. An unresolved selected ID or file returns a definite
pre-write failure, and an unhosted selected chart cannot silently use an unrelated
retained title-card URL. These checks prevent the observed wrong-public-image
incident; they add no editorial review loop or blanket publication hold.

The actual incident is Instagram object `18140916916727008`,
<https://www.instagram.com/p/DfUAKIzgfPH/>. Its accepted CPI image was
`cpi-annual-history-r3` with SHA256
`2e94bde55b4ba794b39c25cc31d4cd2a49a99359bb7545ec5d0305f6111617cc`.
The prior public readback shows the old dark title card instead. The original
object and its immutable dispatch history were preserved. This source repair
does not replace that existing public image. The current Instagram adapter
reports that its content-publishing API does not support post edit; no deletion,
repost or public write was attempted here.

The existing `build_post_image_card` owner now renders up to two verbatim admitted
public observed facts, preserving their full periods, units and adjustment bases,
and the actual source publisher. When no such facts are present it uses the
admitted deck or article context. The legacy delivery-card seam reuses that same
renderer/content projection when an article is available. Source identity wins
over the epistemic state `CONFIRMED`; metadata-only callers remain compatible.
The card's facts and source are included in its binding and checked on reuse.
Enriched delivery cards use content-bound filenames, preserving older dispatched
files and their hash bindings.
Existing charts and licensed photos remain the preferred selected assets.

## Verification

- [Focused tests](focused-tests.xml): 42 passed, including actual retained CPI
  article/media plus its current reviewed per-destination choices reaching a
  mocked Instagram consumer with the exact chart SHA and hosted path.
- [Adjacent regressions](adjacent-regressions.xml): 33 Cloudinary and CPI
  derivative-revision tests passed; see [text output](adjacent-regressions.txt).
- [Before/after reproduction](reproduction-and-renders.json): extracting only the
  exact original resolver function from base
  `5150b4b01da742094dabd1ce3c65fbb597003071` reproduces both failures. Both pass
  with the patched resolver. `verify_visual_fix.py` repeats this locally without
  network calls, model calls or production-store writes.
- Local PNGs under `render/` were inspected by the Publisher builder and CC Desk.
  Both CPI fact paragraphs, monthly/annual adjustment distinctions and BLS source
  are readable without clipping or footer overlap. The delivery card also shows
  the original 14 October 2026 source date. The repeated `a` admission hash in
  this local formatting fixture is explicitly a fixture, never production approval.
- Initial fixture-projection failures are retained separately. The final fixture
  uses the retained current review's actual eight destination choices; no
  production validation or expected chart identity was weakened.

The repair was integrated by Publisher with a guarded fast-forward from
`0209cdfe1dac32f122116abd7431ef1b4610be6d` to
`885b908ed6c216357e9bdd1e93e6d00840a79523`, after retaining all intervening
CC-143 work. See [integration readback](operating-root-integration.json). All six
unrelated dirty tracked files retained their exact hashes. No operating-root
code was edited in place, no branch switch or app restart occurred, and no
schedule, production store or public object was changed.

[Native CLI import proof](native-cli-import-origins.json) loads the actual
`scripts/run_native_desktop_editorial.py` without invoking its main operation,
and verifies that its native role plus all three patched modules resolve to
`A:\Capital Chronicle\ContentOps` with the exact patched source hashes.
[Operating-root consumer tests](operating-root-consumer-tests.xml) pass 23
checks, including the retained CPI chart reaching the mocked Instagram adapter.
The distinct targeted test set is 75 tests (42 focused plus 33 adjacent); the
42 merged checks and 23 operating-root checks are reruns, not additional unique
tests. This proves installed source routing and mocked adapter behavior, not
a new public post. The original wrong-image Instagram object remains unchanged.

Only CC-186's Result line is updated for this repair; its existing Status, Branch,
Threads authorization and NFP acceptance conditions are retained.

## Pasteable audit handoff for Claude Ops

```text
Claude Ops â€” Jim requested the CC-186 Instagram visual repair and this audit.
Patch885b908ed6c216357e9bdd1e93e6d00840a79523 is integrated; CC Desk supplies the final evidence SHA.
Evidence: docs/publisher/CC-186/instagram-visual-fix-20261104/README.md.
The resolver preserves reviewed media order, including thread-root order, rather than canonical file order.
Missing selected IDs/files stop before transport; an unrelated hosted old-card URL is never substituted.
The existing card owner renders verbatim admitted public facts, periods/units and the true publisher.
Legacy delivery cards now reuse that owner; CONFIRMED is no longer printed as a publisher.
Before/after reproduction demonstrates both real selection failures on the prior live function.
75 distinct targeted tests pass; reruns:42 merged and23 operating-root consumer checks, all passing.
Native CLI resolves all patched files in ContentOps; exact CPI chart reaches mocked Instagram; PNGs inspected.
No public object was changed: https://www.instagram.com/p/DfUAKIzgfPH/ remains the old-image incident.
Current Instagram API adapter cannot edit post media; no delete/repost was attempted.
Audit source/CLI/live-consumer evidence and the unchanged old public object separately; retain Threads/NFP conditions.
```
