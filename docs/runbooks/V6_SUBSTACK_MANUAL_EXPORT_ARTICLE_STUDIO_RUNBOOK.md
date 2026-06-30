# V6 Substack Manual Export Article Studio Runbook

Use the canonical V5 dashboard only: `ui/contentops_v5/`.

## Operator review steps

1. Open Writer Studio and review the canonical article draft.
2. Open AI Writer / SEO Lab and review SEO title and description.
3. Open Platform Preview and compare the Substack preview hash.
4. Open Manual Export and inspect the manual-copy payload.
5. Open Approval Queue and Evidence Vault for pending approval and packet evidence.

## Required visible labels

- `sample_fixture_only`
- `manual copy only`
- `Substack API not used`
- `live publish disabled`
- `no runtime proof`

## Prohibited actions

- Do not call Substack API.
- Do not publish live.
- Do not read credentials, env values, browser sessions, cookies, or local storage.
- Do not use provider APIs.
- Do not dispatch to Discord or any platform.

The packet is evidence for human review only. It is not a publishing authorization.
