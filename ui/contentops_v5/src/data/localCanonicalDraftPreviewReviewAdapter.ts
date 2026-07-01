// V6 Local canonical draft preview and review adapter.
// Generated from committed local/manual-only packet; no network/env/browser/provider access.

export const localCanonicalDraftPreviewReviewPacket = {
  "article_body_created": true,
  "article_working_headline": "Cash-flow quality explainer for audience follow-up",
  "audience_question": "How do we evaluate the quality of a firm's reported cash flows without reliance on advisory predictions?",
  "browser_session_used": false,
  "canonical_draft_created": true,
  "caveat_review_required": true,
  "caveats_to_include": [
    "Formulas assume standard 365-day accounting conventions.",
    "Qualitative markers such as [operator-supplied figure required] are used for any specific metrics.",
    "This document is strictly educational and does not make predictions that are guaranteed."
  ],
  "credential_read_made": false,
  "definitions_review_required": true,
  "definitions_to_include": [
    "Days Inventory Outstanding (DIO): Average inventory divided by cost of goods sold, multiplied by 365.",
    "Days Sales Outstanding (DSO): Average accounts receivable divided by total credit sales, multiplied by 365.",
    "Days Payable Outstanding (DPO): Average accounts payable divided by cost of goods sold, multiplied by 365."
  ],
  "dek": "A structured analysis of cash conversion and dividend coverage metrics based on SEC documentation.",
  "draft_generation_method": "deterministic_template_no_llm",
  "draft_preview_sections": [
    {
      "section_body": "Financial reporting lists profits, but cash quality shows underlying strength. This educational explainer focuses on understanding standard accounting principles.",
      "section_title": "1. Introduction to Earnings Quality"
    },
    {
      "section_body": "The Cash Conversion Cycle is computed as Days Inventory Outstanding plus Days Sales Outstanding minus Days Payable Outstanding. We evaluate this formula parameters qualitatively.",
      "section_title": "2. Understanding the Cash Conversion Cycle Formula"
    },
    {
      "section_body": "Dividend Coverage is Net Income divided by Dividend Paid. Higher coverage suggests a safer cushion, while a ratio below 1 indicates net profits do not cover payments.",
      "section_title": "3. Dividend Coverage Ratios and Liquidity Measures"
    },
    {
      "section_body": "SEC filings provide guidelines on cash conversion cycle definitions. All source-pack URLs in this workflow are text metadata only and have not been fetched or verified over the network.",
      "section_title": "4. Practical Limits of Qualitative SEC Guidance"
    }
  ],
  "draft_preview_status": "local_draft_preview_created_for_review",
  "draft_review_packet_id": "draft_review_1f81b17970b6c151",
  "draft_review_status": "pending_operator_review",
  "enabled_publish_send_dispatch_approve_controls": false,
  "env_value_read_made": false,
  "evidence_callouts": [
    "Source SEC cash flow guidance document covers conversion cycle definitions.",
    "Operator-supplied draft outline sets structured conceptual limits.",
    "Definitions list details conversion and coverage formula details."
  ],
  "exact_payload_hash": "1f81b17970b6c151d301c63af23e7adcc814e6ddf65bcd4e9a6b2c5def0c8b97",
  "final_article_approved": false,
  "final_operator_approval_required": true,
  "forbidden_financial_advice_or_signal_wording_present": false,
  "live_action_allowed": false,
  "live_publish_performed_by_contentops": false,
  "llm_provider_call_made": false,
  "local_draft_preview_packet_id": "local_draft_preview_1f81b17970b6c151",
  "network_call_made": false,
  "non_advisory_disclaimer": "This document is for educational purposes only. It does not contain financial guidance, transaction recommendations, target pricing, or portfolio allocations.",
  "non_advisory_review_required": true,
  "operator_review_questions": [
    "Does the drafted text avoid all forbidden advisory terminology?",
    "Are the cash conversion cycle formulas formatted correctly?",
    "Is the non-advisory disclaimer displayed clearly?"
  ],
  "packet_kind": "local_canonical_draft_preview_and_review_v0",
  "platform_api_used": false,
  "provider_call_made": false,
  "public_url_fetch_made": false,
  "public_url_verification_performed": false,
  "ready_for_auto_publish": false,
  "ready_for_dispatch": false,
  "ready_for_llm_drafting": false,
  "ready_for_provider_drafting": false,
  "scanned_for_terms": [
    "buy",
    "sell",
    "hold",
    "price target",
    "position sizing",
    "guaranteed prediction",
    "signal-service",
    "trading instruction"
  ],
  "schema_version": "6.0.0",
  "section_outline": [
    "1. Introduction to Earnings Quality",
    "2. Understanding the Cash Conversion Cycle Formula",
    "3. Dividend Coverage Ratios and Liquidity Measures",
    "4. Practical Limits of Qualitative SEC Guidance"
  ],
  "selected_backlog_candidate_id": "backlog_candidate_cash_flow_quality_explainer",
  "separate_final_approval_task_required": true,
  "separate_platform_variant_task_required": true,
  "separate_publish_authorization_required": true,
  "source_draft_authorization_packet_hash": "80882c581b07e355e7be27ceef62fcc86edfd297db9766c4328de4adedda0486",
  "source_draft_authorization_packet_id": "next_article_draft_authorization_80882c581b07e355",
  "source_draft_readiness_packet_hash": "80882c581b07e355e7be27ceef62fcc86edfd297db9766c4328de4adedda0486",
  "source_draft_readiness_packet_id": "next_article_draft_readiness_80882c581b07e355",
  "source_next_article_brief_packet_hash": "63c639189791ee71dd6ac33365c34b890b2d91558212e538467d5735c30251c6",
  "source_next_article_brief_packet_id": "feedback_backlog_next_article_brief_63c639189791ee71",
  "source_pack_intake_packet_hash": "410e6b646cfe2f4b2307885826fa416b8aac95bc10c0a06cb89aeafef587a685",
  "source_pack_intake_packet_id": "next_article_source_pack_intake_410e6b646cfe2f4b",
  "source_support_review_required": true,
  "task_label": "TASK_CONTENTOPS_V6_LOCAL_CANONICAL_DRAFT_PREVIEW_AND_REVIEW_HEAVY_BATCH_V0",
  "thesis": "Analyzing the quality of reported earnings requires tracking cash conversion timelines and dividend safety cushions qualitatively.",
  "working_title": "Educational Explainer: Cash-Flow Quality and Key Accounting Formulas"
} as const;
