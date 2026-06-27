# Discord Real Content Filled Intake Instructions

Jim fills this workflow only with real Capital Chronicle content.

## Required inputs

- Use real Capital Chronicle content only.
- Include `source_artifact_path` pointing to source content file.
- Include `source_evidence_paths` when numeric claims are present.
- Choose `target_name` and `content_type` correctly:
  - `announcements` -> `announcement`
  - `substack_drops` -> `substack_drop`
  - `product_updates` -> `product_update`
- Keep `not_approved=true`, `not_dispatchable=true`, and `not_public_postable=true` until later approval task.
- Keep `template_only=false` only when real content is actually provided.

## Safety rules

- Do not paste webhook URLs or secrets.
- Do not include buy/sell/hold recommendations.
- Do not include position sizing guidance.
- Do not include guaranteed predictions.
- Do not reuse dry-run payloads, sample payloads, templates, or prior test messages as real content.

## CLI examples

Blocked framework packet, no real content yet:

```powershell
python -m live_contentops.discord_real_content_filled_intake --template docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json --output docs/automation/DISCORD_REAL_CONTENT_FILLED_INTAKE/filled_intake_packet.json
```

Future real source artifact intake:

```powershell
python -m live_contentops.discord_real_content_filled_intake --source-artifact <real_content_artifact_path> --target announcements --content-type announcement --output docs/automation/DISCORD_REAL_CONTENT_FILLED_INTAKE/filled_intake_packet.json
```
