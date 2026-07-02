# Stale Project Sources Delete Guide

## When Safe To Delete

All old ChatGPT Project Sources can be removed after this commit is verified on GitHub.

Verification means:

1. GitHub `master` contains `docs/CHATGPT_PROJECT_BOOTSTRAP/`.
2. All seven required files exist in that folder.
3. ChatGPT Project Instruction has been replaced with text from [CHATGPT_PROJECT_INSTRUCTION.md](./CHATGPT_PROJECT_INSTRUCTION.md).

## What To Delete

Delete old Project Sources that are:

- Raw transcripts.
- No-extension pasted responses.
- Old upload bundles.
- Stale prompts.
- Duplicated repo docs.
- Any file whose durable content is now in committed repo docs/status/packets.

## What To Keep

Best option: keep Project Sources empty.

If ChatGPT requires source material, upload only:

```text
docs/CHATGPT_PROJECT_BOOTSTRAP/
```

## If Unsure

Do not keep old sources for safety. Ask Antigravity to normalize important content into committed repo docs.

Rule: if it matters, commit it. If it is raw chat, delete it from Project Sources.
