# Pre-Alpha Operator Markdown Export (After 0125)

**Task:** `TASK_CONTENTOPS_0125_APPROVED_ARTIFACT_INTAKE_TO_DAILY_MARKDOWN_WORKBENCH_BRIDGE_V0`

## Purpose
This document outlines the capabilities of the pre-alpha daily operator Markdown export (`pre-alpha-daily-operator-markdown-export`). As of task 0125, it serves as the unified Daily Operator Workbench, acting as a human-readable, read-only control plane projection.

## 0125 Addition: Artifact Intake Queue Bridge
The export now includes a read-only projection of the `Approved Capital Chronicle Artifact Intake Queue`. This surfaces:
- The count of accepted vs. blocked incoming artifacts.
- The details of accepted artifacts (Source ID, Content Type, Freshness, Limitations, Data Sufficiency, DQR, and Forecast Readiness).
- The blocked reasons for unsafe or incomplete artifacts.

**Crucial Constraint:** This is a display-only UX bridge. 
- It does **not** create a draft-generation path from approved artifacts yet.
- It does **not** route artifacts into public-postable, publish-ready, auto-approved, or platform-template states. 
- It explicitly warns the operator that artifacts are only accepted for local ContentOps review, maintaining the system's hard safety boundaries.

## Existing Capabilities Preserved
- **Safety Header:** Explicitly states the absence of platform APIs, web scraping, schedulers, and automatic metrics.
- **Run Summary:** Aggregates the local seed and draft queue statuses.
- **Ready for Operator Review:** Surfaces generated platform manual templates ready for copy/paste.
- **Blocked or Not Ready:** Lists items that require manual upstream resolution.
- **Post-Publish Reminders:** Prompts the operator for manual publish records, manual performance records, and content performance reviews.
- **Next Operator Actions:** Deterministically recommends the next safest operator task.
- **No Publish Fallback:** Explicitly states that output is never inferred to be published without manual verification.
