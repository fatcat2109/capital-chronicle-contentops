# Pre-Alpha Operator Workflow Consolidation (After 0118)

**Task:** `TASK_CONTENTOPS_0118_PRE_ALPHA_OPERATOR_WORKFLOW_CONSOLIDATION_AND_README_REFRESH_V0`
**Baseline:** `master`, HEAD `e45b784`, After Task 0117

This document establishes the current, unified daily workflow for a solo operator. As the system has grown through tasks 0108-0117, many granular components (publish records, performance records, performance reviews) were added. This document clarifies what is required, what is optional, and maps the exact sequence of operator actions.

Historical task documents remain in the repository as architectural and decision records, but this is the authoritative daily map.

---

## 1. Operator Daily Workflow Sequence

The workflow is designed to be highly conservative and entirely local. No publishing happens automatically, and no analytics are scraped.

1. **Check Status**: Ensure the system is safe and ready.
   `python -m live_contentops.cli status`
2. **Run Daily Operator Content Run**: Generate and review the daily local editorial packet and prompt variables.
   `python -m live_contentops.cli pre-alpha-daily-operator-content-run-summary`
3. **Inspect Platform Manual Templates**: Review the text generated for specific platform requirements.
   `python -m live_contentops.cli pre-alpha-platform-manual-templates-summary`
4. **Manually Publish**: Take the output from the templates, open the platform (e.g., LinkedIn, X) manually in your own browser, paste the content, and hit "Post". The system will **never** do this for you.
5. **Manually Record Publish Record**: After posting, save the URL, timestamp, and metadata locally as a manual publish record so the system knows the content went out.
   `python -m live_contentops.cli pre-alpha-manual-publish-record-summary`
6. **Manually Record Performance Metrics (Optional, Later)**: Wait 24-72 hours. Observe the public metrics manually. Input them into the manual performance record fixture.
   `python -m live_contentops.cli pre-alpha-manual-performance-record-summary`
7. **Run Local Content Performance Review (Optional, Later)**: Aggregate those manual metrics to generate conservative editorial hypotheses.
   `python -m live_contentops.cli pre-alpha-content-performance-review-summary`

---

## 2. Command Classification Map

To find out what commands are available:
`python -m live_contentops.cli operator-command-summary`

### Required Daily Commands
These are the core steps to prepare content for manual posting.
* `status`
* `pre-alpha-daily-operator-content-run-summary`
* `pre-alpha-platform-manual-templates-summary`
* `pre-alpha-manual-publish-record-summary`

### Optional Post-Publish Commands
These handle the manual recording of what happened *after* you hit post.
* `pre-alpha-manual-performance-record-summary`
* `pre-alpha-content-performance-review-summary`

### Internal/Debug Commands
Dozens of other commands exist in the CLI (e.g., `telegram-staging-contract`, `pre-alpha-manual-export-summary`). These are older tasks, safety bounds, or dry-run states. They are not part of the daily solo operator flow.

---

## 3. Packet Definitions and Limitations

* **Daily Operator Content Run Packet**: Consolidates prompt packs, draft packs, and review ledgers. **Does not** auto-publish or claim public-postable status.
* **Platform Manual Templates**: Formats text for specific networks. **Does not** contain API payloads, platform SDK calls, or scheduling instructions.
* **Manual Publish Record**: The sole source of truth that content was published. **Does not** infer publication without manual entry.
* **Manual Performance Record**: The sole source of metrics. **Does not** scrape, fetch, or ingest via APIs.
* **Content Performance Review**: Synthesizes hypotheses from performance records. **Does not** use LLMs to analyze data, does not invent metrics, and does not claim statistical significance.

## 4. Safety Checklist

Before adopting this workflow daily, ensure:
- `local_only` is true across all active packets.
- No `.env` credentials are required for any of the 7 core steps above.
- No platform APIs are authenticated or triggered.
- No external automated tools (e.g., Make, Zapier, Hootsuite) are wired to the output.

## 5. Next Recommended Build Direction

The immediate future should focus on closing the loop between the **Content Performance Review** hypotheses and the **Daily Operator Content Run**. Currently, hypotheses are generated but not automatically fed back into the next day's prompt generation. The next architectural phase should determine how to safely inject these conservative editorial constraints into the upstream local content pipeline without compromising deterministic safety.
