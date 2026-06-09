# Pre-Alpha Content Performance Review Packet (After 0117)

Task: `TASK_CONTENTOPS_0117_LOCAL_CONTENT_PERFORMANCE_REVIEW_PACKET_V0`

LOCAL ONLY | DETERMINISTIC ONLY | MANUAL METRICS ONLY | NO API | NO SCRAPING | NO LLM | NO STATISTICAL CLAIMS

## Purpose

The `PreAlphaContentPerformanceReviewPacket` provides a safe, local, deterministic review of content performance based entirely on operator-entered manual metrics. It establishes a feedback loop to generate conservative editorial hypotheses without risking API leakage, automated scraping, or AI hallucinations.

## Core Principles

- **Manual Data Only**: The review only consumes data from manual performance records. It does not fetch, scrape, or ingest analytics automatically.
- **Conservative Observations**: The module generates hypotheses and observations (e.g., "In this manually recorded sample, X has the most records"). It explicitly forbids imperative posting advice ("post this format tomorrow") or financial signaling ("buy/sell/hold").
- **No Statistical Significance**: The module explicitly avoids claiming statistical significance. It recognizes that manual samples are often small and biased.
- **Null Metric Preservation**: If a metric is missing (null), it stays missing. It is excluded from direct numerical comparisons but counted to highlight gaps in manual observation.
- **Insufficient Sample Warnings**: If fewer than 3 valid records are available, the packet passes but flags `insufficient_sample=true` and limits its hypotheses.

## Forbidden Actions

- No LLM generation is used.
- No platform APIs are called.
- No posting or scheduling actions are enabled (`public_postable: false`, `auto_publish: false`).
- No credential or environment reads are performed.

## Operator CLI UX

This review is an optional post-publish command. It is not required for daily drafting or publishing.

```
python -m live_contentops.cli pre-alpha-content-performance-review-summary
```

It returns a JSON summary detailing the review scope, sample size, conservative findings, and strict safety flag confirmations.
