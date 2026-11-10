# CC-400 — Tested plan-status export contracts

Integrated into `A:\Capital Chronicle\ContentOps` at code commit
`0ed28cddf66c1b2c6a920f21def50dedaef07a6d`. The existing minute consumer recorded
`OK`, the tested contract version and its export clock at 16:17:29 GMT+7 on
10 November 2026. The installed dry run passes and all 17 contract checks pass
from that operating root. There are 72 distinct passing targeted checks across
the validation runs. No task or application was restarted.

The existing plan-status composer validates the export before creating an
outbox post. An unknown semantic version stops that run's publication and
records one incident in the existing store, keyed by the version. Repeated
minute runs reuse that incident. Invalid fields name their exact consumer path.
Main's own reader still checks source hashes, joins and its producer schema.

The tested formats are the installed pre-version `schema_version: 1.0.0`
(`legacy/schema-1.0.0` in consumer records) and CC-398's explicit
`contract_version: 2.0.0`, from producer commit
`215c7fa136959cb2453978dc4f3898f9c66ea4f8`. Version 2 has composer fixture
coverage; it was not present in the live export during this implementation.
An explicit untested version never falls back to the legacy format. Main's
explicit unavailable rows retain their first cause and do not suppress the
other available calls.

Ops Live runs this command after each integration that changes the export:

```powershell
python "A:\Capital Chronicle\ContentOps\scripts\plan_status_posts.py" --dry-run
```

Exit 0 with `validation: PASS` means the current export passed the consumer
contract, Main's reader and the actual post/destination composers. Exit 1 with
`validation: FAIL` reports the refusal and, for contract failures, `failed_field`.
The default export and store are the same ones the minute consumer reads.
Use `--export-dir <copy>` to check a proposed export. Preview output is JSON;
redirect it to a file when retaining the rendered copies.

The dry run renders new candidate posts and the retained format-4 posts bound
to plans in that export, including all seven registered destination text
packages. Retained cards keep their original parents. It preserves normal
queue/fill decisions, uses SQLite's read-only connection and creates no
incident, run record, media, browser request or public write. Image/media
publication remains with the existing preparation and coordinator path.

The live-export dry run and a copy with `zone` renamed are saved in
[live-dry-run.json](live-dry-run.json) and
[renamed-field-dry-run.json](renamed-field-dry-run.json). The latter must fail at
`status.plans[0].zone`, before a generic producer hash/schema error. Controlled
tests prove that an unknown version creates no outbox/dispatch, files one
incident across repeats, and cannot call the publisher. They also prove the
tested formats feed the real composer and that `--dry-run --publish` cannot
write through SQLite or call the publisher.

[composer-tests.xml](composer-tests.xml) and
[final-composer-tests.xml](final-composer-tests.xml) retain the targeted checks.
The installed checks are in [installed-tests.xml](installed-tests.xml), with
the actual default-export preview in [installed-dry-run.json](installed-dry-run.json).
Integration and the minute consumer's version readback are recorded in
[acceptance.json](acceptance.json) and [installed-consumer.json](installed-consumer.json).

The branch starts from operating commit
`50b449cf8eb758cd8f47d8cefc8d8daab3dd645a`, retaining the installed CC-399 and
CC-432 consumers; the fetched remote default is its ancestor. No Main source,
schedule or unrelated work is changed.

The parent launch arguments configure `gpt-6.1-sol` / `max`, labelled
`CONFIGURED_NOT_OBSERVED`. This deterministic implementation calls no
editorial model.
