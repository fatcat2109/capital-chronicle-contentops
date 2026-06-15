# Grounded Research Brief Contract (After 0128)

**Task:** `TASK_CONTENTOPS_0128_GROUNDED_RESEARCH_BRIEF_CONTRACT_RECOVERY_V0`

## Purpose
A **Grounded Research Brief** is an explicit data contract for injecting manually gathered news and context into the Capital Chronicle ContentOps pipeline. It is the sole mechanism by which "world state" enters the local repository without triggering forbidden automated LLM web scraping or API fetching.

### What It Is
- A structured representation of news and events explicitly curated by the operator.
- A source list containing clear provenance, credibility notes, freshness labels, and limitations.
- A sequence of deterministic claims (e.g., factual citations, educational framing) that pin context for downstream LLM draft review.

### What It Is Not
- **It is NOT an automated fetcher:** The repository performs NO fetching, searching, scraping, or provider LLM calls to construct this brief. The operator must supply it.
- **It is NOT artifact-backed CC output:** Capital Chronicle "alpha" artifacts are cryptographic signals indicating market regimes. This brief merely provides qualitative news context. It is strictly forbidden to claim artifact-backed status here.
- **It is NOT a public-ready draft:** The brief defines the truth boundaries. It does not dictate the final prose.

## Core Principle: News is a Hook, Not a Signal
We do not trade the news. We do not issue signals based on central bank speeches or single data prints. News serves strictly as an educational hook to explain macro mechanics, data sufficiency problems, or failure forensics.

Any claim attempting to smuggle market execution language ("buy", "sell", "target", "signal", "execution") is deterministically blocked by the validator.

## Source and Claim Requirements
- **Sources:** Must define a URL, a publication or accessed date, and explicit notes on credibility, freshness, and limitations. 
- **Claims:** Must declare risk levels. "Factual" or "Current" claims must carry the `has_citation=true` flag and reference a specific `source_id`.

## Pipeline Feed (0129 Draft Review)
This validated brief contract directly feeds into the upcoming **Task 0129 (LLM-Assisted Draft Review)**. In 0129, external copywriters will submit drafts. Those drafts will be cross-referenced against the `claims` defined in this brief. If a draft introduces claims not supported by this brief, it will fail review.

## Milestone Status
*Note: There is no Project Sources refresh after this task. Refresh bundles are reserved for major architectural milestones.*
