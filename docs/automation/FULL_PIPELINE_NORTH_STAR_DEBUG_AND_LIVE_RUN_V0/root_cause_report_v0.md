# Full Pipeline North-Star Root Cause Report V0

- Previous defective Telegram message ID: `59`
- Previous Telegram text-only detected: `true`
- Previous Telegram missing article link/fallback: `true`

## Findings

- Image generation failed because The committed media spec was planning-only and set generation_allowed_now=false; the previous live runner treated that as acceptable instead of building or finding the required source-backed media assets.
- Telegram fell short because The previous runner called the text send path execute_telegram_post and built no article export, public URL, or local fallback reference for the Telegram payload.
- Substack remains blocked because The available automated Substack path is browser-profile based, so this repair uses local Markdown/HTML export and marks Substack as requiring operator browser assist.
- X remains blocked because The available X paths are browser/CDP supervised or operator-outcome recording paths, not a bounded non-browser send adapter for this task.

## Repair

Do not send another text-only post. Build a ContentOps-owned source-backed FRED/EIA chart pack from data, require at least three visuals distributed through the article export, then send one operator-approved Telegram photo replacement only if the duplicate guard permits it.
