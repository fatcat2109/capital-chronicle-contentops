# Authority Model

## Runtime Authority Order

1. GitHub remote `fatcat2109/capital-chronicle-contentops` on `master`.
2. Committed repo files, tests, packets, and status ledgers.
3. [CURRENT_PROJECT_STATUS.md](../status/CURRENT_PROJECT_STATUS.md) and [current_project_status.json](../status/current_project_status.json).
4. Current V6 strategy docs listed in [REQUIRED_READING_INDEX.md](./REQUIRED_READING_INDEX.md).
5. This bootstrap folder.
6. Chat memory, pasted transcripts, no-extension response files, and ChatGPT Project Sources.

## Conflict Rule

If Project Sources or chat memory conflict with GitHub/repo files, repo wins.

If committed status docs conflict with newer committed packets/tests/code, stop and report `BLOCKED: status/repo authority conflict`.

## Role Split

- Antigravity: planner + builder. Researches, plans, edits, validates, commits, pushes.
- ChatGPT: thin alignment gate, repo evidence checker, and prompt framer.
- Jim: final authority.

## Runtime Safety

No live/API/browser/env/credential/provider action is authorized by this bootstrap.

Do not read or request raw env values, credential values, webhook URLs, provider keys, browser session secrets, cookies, localStorage, sessionStorage, token material, secret-derived hashes, lengths, prefixes, or suffixes.

Do not dispatch, publish, schedule, retry, execute outbox, execute approval ledger, validate webhook URL, scrape/fetch public URLs, DM, comment, like, react, or perform platform action unless a future exact approved task authorizes it.
