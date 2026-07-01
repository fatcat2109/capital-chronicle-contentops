// V6 Feedback backlog next article brief adapter.
// Generated from committed local/manual-only packet; no network/env/browser/provider access.

export const feedbackBacklogNextArticleBriefPacket = {
  "blocked_controls": [
    "approve",
    "dispatch",
    "publish",
    "schedule",
    "send"
  ],
  "brief_candidate": {
    "audience_need": "Multiple operator-supplied questions ask for plain-English cash-flow and revenue-quality context.",
    "brief_id": "next_article_brief_candidate_backlog_candidate_cash_flow_quality_explainer",
    "brief_title": "Review-only brief candidate: Cash-flow quality explainer for audience follow-up",
    "canonical_draft_requested": false,
    "editorial_angle": "Explain how cash conversion, revenue quality, and dividend coverage fit together without giving financial advice.",
    "not_financial_advice": true,
    "publication_or_dispatch_requested": false,
    "required_operator_review_notes": [
      "Confirm the source feedback text is approved for editorial planning use.",
      "Attach a separate source pack before any canonical draft is requested.",
      "Keep all copy educational and non-advisory."
    ],
    "suggested_outline": [
      "Restate the audience question in plain English.",
      "Define the key financial-quality concepts without advice wording.",
      "Show caveats operators should verify before drafting.",
      "Close with educational takeaways and human-review notes."
    ],
    "working_headline": "Cash-flow quality explainer for audience follow-up"
  },
  "browser_session_used": false,
  "candidate_review_status": "ready_for_operator_review_only",
  "canonical_draft_created": false,
  "credential_read_made": false,
  "env_value_read_made": false,
  "exact_payload_hash": "63c639189791ee71dd6ac33365c34b890b2d91558212e538467d5735c30251c6",
  "forbidden_financial_advice_or_signal_wording_present": false,
  "live_publish_performed_by_contentops": false,
  "llm_provider_call_made": false,
  "network_call_made": false,
  "next_article_brief_packet_id": "feedback_backlog_next_article_brief_63c639189791ee71",
  "non_readiness_claims": {
    "api_readiness_claimed": false,
    "canonical_draft_readiness_claimed": false,
    "dispatch_readiness_claimed": false,
    "live_readiness_claimed": false,
    "llm_summary_claimed": false,
    "public_url_verification_claimed": false
  },
  "operator_review_required": true,
  "packet_kind": "feedback_backlog_next_article_brief_candidate_v0",
  "platform_api_used": false,
  "provider_call_made": false,
  "public_url_fetch_made": false,
  "schema_version": "6.0.0",
  "selected_backlog_candidate_id": "backlog_candidate_cash_flow_quality_explainer",
  "selected_priority_score": 36,
  "selected_source_feedback_item_ids": [
    "operator_feedback_substack_question_001",
    "operator_feedback_x_reply_001"
  ],
  "selected_source_platforms": [
    "substack",
    "x"
  ],
  "selected_topic_tags": [
    "cash_conversion",
    "dividend_coverage",
    "explainer",
    "free_cash_flow",
    "reader_education",
    "revenue_quality"
  ],
  "selection_method": "deterministic_highest_priority_score_then_candidate_id",
  "source_audit_index_hash": "b968984b920bbf93edef7941ab3c93f229db393f6be7bcf0025a713b82cc5477",
  "source_audit_index_packet_id": "manual_distribution_registry_audit_index_b968984b920bbf93",
  "source_backlog_summary_hash": "24b783562e91a600284c252c85a4e6757e11b1030743850869ef6d39c93addd8",
  "source_backlog_summary_packet_id": "operator_feedback_backlog_summary_24b783562e91a600",
  "source_feedback_intake_hash": "4b0ff2791a5398184621325ba8ce5fe843963cbc826885e29eb823f5a05e7dd4",
  "source_feedback_intake_packet_id": "operator_supplied_feedback_intake_4b0ff2791a539818",
  "source_pack_required_before_drafting": true,
  "task_label": "TASK_CONTENTOPS_V6_FEEDBACK_BACKLOG_REVIEW_TO_NEXT_ARTICLE_BRIEF_LOOP_V0"
} as const;
