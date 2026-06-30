# V6 AI Research Canonical Article Engine Runbook

## Purpose

Process operator ideas into canonical Substack articles and downstream Discord summary seeds safely.

## Operational Steps

1. Formulate the operator idea topic, target audience, and editorial angle.
2. Compile verified source context documents and disclaimers.
3. Run the engine CLI in default dry-run mode:
   `python -m live_contentops.ai_research_canonical_article_engine_v6 --output out.json`
4. Confirm `provider_call_made=false` and `result_class=dry_run_fixture`.
5. Review generated sections to ensure zero forbidden terms were introduced.
6. Verify `canonical_payload_hash` is computed.
7. Pass the generated `discord_summary_seed` downstream to the Discord outbox spine.

## Troubleshooting

- **ValueError: forbidden_financial_advice_language**: Adjust the idea topic or notes to exclude restricted words like `buy`, `sell`, `hold`, `target`.
- **missing_api_key**: When running in live mode, ensure `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is present.
