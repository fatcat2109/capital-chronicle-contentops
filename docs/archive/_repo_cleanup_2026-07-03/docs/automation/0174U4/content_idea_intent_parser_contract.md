# 0174U4 Content Idea Packet and Local Intent Parser Contract

Task: `TASK_CONTENTOPS_0174U4_CONTENT_IDEA_PACKET_AND_LOCAL_INTENT_PARSER_CONTRACT_V0`
Model: `0174U4_CONTENT_IDEA_INTENT_PARSER_CONTRACT_V1`

## Scope

Deterministic local-only parser for operator text. It creates review-only
ContentIdeaPacket and LocalIntentPacket records. It never calls LLM providers,
platform APIs, Telegram APIs, credentials, env, schedulers, scraping, DM flows,
or ingestion repo mutation paths.

## Core contract

- raw operator input is redacted and hash-bound;
- platform targets map to registry-known IDs;
- text lanes map to process, grounded-news, or future-artifact gates;
- approval-like text requires challenge;
- dispatch-like text is blocked;
- public postable and dispatch-ready remain false;
- human review remains required.

## Sample IDs

- raw input: `raw_input_413e4f1ea74d4ca59aec37c4`
- idea: `idea_1d2784149f866921b79354da`
- intent: `intent_248391f0f0f3d2f90d87338a`
- validation: `intent_validation_097b04e2658179f4d36eb5ec`

## Safety flags

All live/provider/platform/credential/scheduler/scraping/dispatch flags stay false.

## Next heavy batch

`TASK_CONTENTOPS_0174U5_EDITORIAL_BRIEF_AND_AI_WRITER_OUTPUT_CONTRACT_V0`
