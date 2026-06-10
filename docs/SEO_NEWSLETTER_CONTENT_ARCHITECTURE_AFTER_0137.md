# SEO Newsletter Content Architecture Spec (0137)

## Purpose
This spec defines the content taxonomy, newsletter issue blueprint, and SEO metadata policy for future content distribution. It establishes structural guarantees around safety disclaimers, offline placeholder boundaries, and strict manual-send gating without enabling any actual website, CMS, or mailing list integrations.

## Content Pillars
The architecture permits specific predefined local editorial pillars (e.g., `macro_education`, `data_sufficiency`). Every pillar strictly requires explicit source policies and forbids any trading signal language.

## SEO Policy
- No real domain requirements (placeholder URLs only).
- No public sitemap generation.
- No public RSS generation.
- Mandates `no_financial_advice` and `no_signal_language` parameters.

## Newsletter Architecture
The newsletter configuration strictly forces `manual_send_only = true` and `manual_metrics_entry_only = true`. All real external mailing list API integrations, subscriber data retention, and pixel tracking are disabled.

## Restrictions
- **No Public Website Build**: This task prepares the abstract architecture, not the physical site.
- **No Active Newsletter**: There is no email sender or SMTP capability.
- **No Real SEO Crawl**: Content acts locally; there is no indexation.
