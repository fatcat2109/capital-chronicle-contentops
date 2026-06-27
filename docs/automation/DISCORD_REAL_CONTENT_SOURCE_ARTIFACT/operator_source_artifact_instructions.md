# Discord Real Content Source Artifact Instructions

Jim supplies exactly one real Capital Chronicle source artifact for later filled-intake work.

## Dropzone

Put one real source artifact in:

`docs/automation/DISCORD_REAL_CONTENT_SOURCE_ARTIFACT/inbox/`

Allowed formats:

- `.md`
- `.txt`
- `.json`

## Rules

- Use real Capital Chronicle content only.
- Do not paste secrets, webhook URLs, cookies, tokens, or private session data.
- Include evidence paths for numeric claims.
- Avoid buy/sell/hold language.
- Avoid position sizing guidance.
- Avoid guaranteed predictions.
- Choose target later unless source artifact clearly indicates announcement, Substack drop, or product update.
- This task does not approve or dispatch anything.

## CLI

Blocked framework packet, no real artifact yet:

```powershell
python -m live_contentops.discord_real_content_source_artifact --output docs/automation/DISCORD_REAL_CONTENT_SOURCE_ARTIFACT/source_artifact_packet.json
```

Optional future explicit artifact path:

```powershell
python -m live_contentops.discord_real_content_source_artifact --source-artifact docs/automation/DISCORD_REAL_CONTENT_SOURCE_ARTIFACT/inbox/<real_file.md> --output docs/automation/DISCORD_REAL_CONTENT_SOURCE_ARTIFACT/source_artifact_packet.json
```
