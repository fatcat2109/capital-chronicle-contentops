# Pre-Alpha Operator Markdown Export

**Version:** AFTER_0121
**Status:** Local-only operator readable rendering.

## Overview
The `pre-alpha-daily-operator-markdown-export` command provides a human-readable Markdown rendering of the daily ContentOps workbench. 

It composes the existing deterministic pre-alpha packets (Content Run, Manual Templates, Publish Record, Performance Record, Performance Review) into a single, copy/paste-friendly daily view.

## Safety & Boundaries
- **No Publishing:** This Markdown export is for local operator readability only. It does not publish.
- **No Platform API Calls:** It does not schedule, format platform-specific request payloads, or send any network requests.
- **No Scraping/Metrics Ingestion:** It does not scrape or ingest metrics automatically. All performance numbers rely on the local manual operator entry.
- **Operator Final Check Mandatory:** The output explicitly contains checklists and warnings requiring the operator to review constraints manually.
- **Audit Source:** The underlying JSON summaries remain the deterministic audit source; the Markdown is strictly a convenience rendering layer.

## How to Run
```bash
python -m live_contentops.cli pre-alpha-daily-operator-markdown-export
```
Output will be returned directly to standard out as Markdown text.

## Typical Output Sections
1. **Safety Header:** Pins the exact limitations of the run.
2. **Run Summary:** High-level status indicating what is ready or blocked.
3. **Ready for Operator Review:** All clean items with their source details, limitations, and copy/paste text block.
4. **Blocked or Not Ready:** Items needing operator attention before they can proceed.
5. **Platform Manual Templates:** Organized by platform, containing formatted copy/paste strings and soft length constraints.
6. **Publish/Performance/Review Reminders:** Daily local post-publish reminders.
7. **Next Operator Actions:** A unified queue of required next manual steps.
