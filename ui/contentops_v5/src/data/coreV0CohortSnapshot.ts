// Generated from a real `core-v0-shadow-demo --evaluation-corpus` run.
// Do not hand-edit: regenerate with scripts/generate_cohort_snapshot.py.
export const coreV0CohortSnapshot = {
  "accepted_publication_history": [
    {
      "article_mode": "analysis",
      "as_of_utc": "2026-07-11T02:00:00Z",
      "case_id": "history-us-treasury-curve-2026-07-13",
      "content_mode": "numeric_official_record",
      "disposition": "SELECTED",
      "domain_family": "rates_or_credit",
      "duplicate_key": "us-treasury-curve-2026-07-13",
      "entities": [
        "U.S. Department of the Treasury"
      ],
      "geography": "US",
      "history_class": "ACCEPTED_PUBLICATION_AUTHORIZED",
      "lane": "capital_chronicle",
      "material_class": "committed_accepted_publication_history",
      "packet_id": "cc-evidence-9052ed65ac6cec10",
      "presented_as_current_news": false,
      "published_at_utc": "2026-07-13T00:00:00Z",
      "schema_version": "contentops.core_v0_evaluation_corpus.v1",
      "sector": "government_bonds",
      "source_artifact_paths": [
        "docs/automation/DATABASE_PUBLICATION_AUTHORITY_AND_CONTENTOPS_FULL_LIVE_CLOSURE_V1/contentops_database_publication_live_20260714_1/capital_chronicle_content_evidence_packet_v2.json",
        "docs/automation/TIER1_EDITORIAL_REVISION_AND_SEO_QUALITY_V2/contentops_tier1_editorial_revision_seo_v2_20260714_1/capital_chronicle_content_evidence_packet_v2.json",
        "docs/automation/V6_DAILY_EDITORIAL_SCHEDULE/governed_fabric_preflight_rehearsal_v1/capital_chronicle_content_evidence_packet_v2.json"
      ],
      "source_family": "story_scoped_publication_evidence_v1",
      "story_type": "market_move",
      "title": "U.S. Treasury Curve Steepens as 30-Year Yield Reaches 5.10%",
      "update_chain": "ust-daily-par-yield-curve",
      "visual_type": "chart_and_document_excerpt"
    }
  ],
  "approval_captured": false,
  "browser_or_cdp_action_performed": false,
  "cases": [
    {
      "adjusted_rank": 3,
      "adjusted_score": 6.66666667,
      "base_rank": 2,
      "base_score": 66.66666667,
      "base_score_source": "universal_news_candidate_fabric_v2.score_candidate",
      "case_id": "case-economic-release-ust-newsroom",
      "chart_partial_period": false,
      "chart_qa_status": "PASS",
      "chart_title": "U.S. Treasury Par Yield Curve: 2026-07-13",
      "concentration_penalty": 60.0,
      "content_mode": "numeric_official_release",
      "deferred_by_portfolio_concentration": false,
      "domain_family": "economic_release",
      "gate_reason": null,
      "geography": "US",
      "governed_disposition": "ELIGIBLE_CANDIDATE",
      "hard_gate_failure": false,
      "lane": "newsroom",
      "material_class": "historical_evaluation_material",
      "outcome": "PACKAGE_REVIEW_PASSED",
      "penalty_dimensions": [
        "entities",
        "geography",
        "sector",
        "source_family",
        "visual_type"
      ],
      "portfolio_disposition": "SELECTED",
      "portfolio_disposition_reason": "Cleared hard gates and holds the top diversity-adjusted position.",
      "presented_as_current_news": false,
      "rank_changed_by_concentration": true,
      "review_blocked_roles": [],
      "review_result": "PASS",
      "review_role_count": 8,
      "sector": "government_bonds",
      "seo_contract_status": "COMPLETE",
      "source_family": "story_scoped_publication_evidence_v1",
      "story_type": "data_release",
      "terminal_state": "REVIEW_READY",
      "tier1_blocked_count": 0,
      "tier1_blocked_destinations": [],
      "tier1_explicit_outcome_count": 9,
      "tier1_supported_count": 9,
      "visual_adaptation_bindings": [
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "newsletter_chart_figure",
          "derivative_sha256": "2d2a5b8cb616510fa977fb7d1a9411c2f44a6545be83cf92335b7bfed33ad064",
          "platform_id": "substack_newsletter",
          "source_asset_id": "treasury_2s10s_history",
          "target_aspect_ratio": "3:2",
          "target_height": 971,
          "target_width": 1456
        },
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "landscape_feed_card",
          "derivative_sha256": "acff88c29bdf9b46dfd35053d3d073f63be7825d0b70008ae1b1148d63e530dc",
          "platform_id": "linkedin",
          "source_asset_id": "treasury_2s10s_history",
          "target_aspect_ratio": "1.91:1",
          "target_height": 628,
          "target_width": 1200
        },
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "landscape_summary_card",
          "derivative_sha256": "560c41640adf453516d3aa87781ceae4210d1a0724d4af30e230ca379d700d88",
          "platform_id": "x_twitter",
          "source_asset_id": "treasury_curve_snapshot",
          "target_aspect_ratio": "16:9",
          "target_height": 675,
          "target_width": 1200
        },
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "landscape_feed_card",
          "derivative_sha256": "8e2f79461371ce07b041a3e0277a75ccaded445929eb5585864125d8ea228122",
          "platform_id": "facebook_page",
          "source_asset_id": "treasury_curve_snapshot",
          "target_aspect_ratio": "1.91:1",
          "target_height": 628,
          "target_width": 1200
        },
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "channel_preview_image",
          "derivative_sha256": "7a2daebdf9eba3e766f55da0e5fda5f49ee51e19c5d24767a1a421fa88b35aea",
          "platform_id": "telegram",
          "source_asset_id": "treasury_2s10s_history",
          "target_aspect_ratio": "16:9",
          "target_height": 720,
          "target_width": 1280
        },
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "community_square_image",
          "derivative_sha256": "0b50f951472ce46db96a43ed75ebe03a6398b82bb71f9c2f6e37112539631209",
          "platform_id": "youtube_community",
          "source_asset_id": "treasury_curve_snapshot",
          "target_aspect_ratio": "1:1",
          "target_height": 1080,
          "target_width": 1080
        },
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "embed_preview_image",
          "derivative_sha256": "7a2daebdf9eba3e766f55da0e5fda5f49ee51e19c5d24767a1a421fa88b35aea",
          "platform_id": "discord",
          "source_asset_id": "treasury_2s10s_history",
          "target_aspect_ratio": "16:9",
          "target_height": 720,
          "target_width": 1280
        },
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "feed_portrait_primary",
          "derivative_sha256": "35b8fab518a712e1f18b3024b6dfacbb64e73ecdd106bc4ad36d6ea025f47962",
          "platform_id": "instagram_business",
          "source_asset_id": "treasury_curve_snapshot",
          "target_aspect_ratio": "4:5",
          "target_height": 1350,
          "target_width": 1080
        },
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "feed_portrait_secondary",
          "derivative_sha256": "35b8fab518a712e1f18b3024b6dfacbb64e73ecdd106bc4ad36d6ea025f47962",
          "platform_id": "threads",
          "source_asset_id": "treasury_curve_snapshot",
          "target_aspect_ratio": "4:5",
          "target_height": 1350,
          "target_width": 1080
        }
      ],
      "visual_adaptation_blocked": [],
      "visual_adaptation_count": 9,
      "visual_rights_cleared": 3,
      "visual_status": "PASS",
      "visual_strategy": "CHART_LED_WITH_SOURCE_EXCERPT",
      "visual_type": "chart_and_document_excerpt"
    },
    {
      "adjusted_rank": 2,
      "adjusted_score": 16.0,
      "base_rank": 1,
      "base_score": 100.0,
      "base_score_source": "governed_packet_authorized_claim_counts",
      "case_id": "case-rates-ust-curve",
      "chart_partial_period": false,
      "chart_qa_status": "PASS",
      "chart_title": "U.S. Treasury Par Yield Curve: 2026-07-13",
      "concentration_penalty": 84.0,
      "content_mode": "numeric_official_record",
      "deferred_by_portfolio_concentration": false,
      "domain_family": "rates_or_credit",
      "gate_reason": null,
      "geography": "US",
      "governed_disposition": "ELIGIBLE_CANDIDATE",
      "hard_gate_failure": false,
      "lane": "capital_chronicle",
      "material_class": "historical_evaluation_material",
      "outcome": "PACKAGE_REVIEW_PASSED",
      "penalty_dimensions": [
        "content_mode",
        "domain_family",
        "entities",
        "geography",
        "sector",
        "source_family",
        "visual_type"
      ],
      "portfolio_disposition": "SELECTED",
      "portfolio_disposition_reason": "Cleared hard gates and holds the top diversity-adjusted position.",
      "presented_as_current_news": false,
      "rank_changed_by_concentration": true,
      "review_blocked_roles": [],
      "review_result": "PASS",
      "review_role_count": 8,
      "sector": "government_bonds",
      "seo_contract_status": "COMPLETE",
      "source_family": "story_scoped_publication_evidence_v1",
      "story_type": "data_release",
      "terminal_state": "REVIEW_READY",
      "tier1_blocked_count": 0,
      "tier1_blocked_destinations": [],
      "tier1_explicit_outcome_count": 9,
      "tier1_supported_count": 9,
      "visual_adaptation_bindings": [
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "newsletter_chart_figure",
          "derivative_sha256": "2d2a5b8cb616510fa977fb7d1a9411c2f44a6545be83cf92335b7bfed33ad064",
          "platform_id": "substack_newsletter",
          "source_asset_id": "treasury_2s10s_history",
          "target_aspect_ratio": "3:2",
          "target_height": 971,
          "target_width": 1456
        },
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "landscape_feed_card",
          "derivative_sha256": "acff88c29bdf9b46dfd35053d3d073f63be7825d0b70008ae1b1148d63e530dc",
          "platform_id": "linkedin",
          "source_asset_id": "treasury_2s10s_history",
          "target_aspect_ratio": "1.91:1",
          "target_height": 628,
          "target_width": 1200
        },
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "landscape_summary_card",
          "derivative_sha256": "560c41640adf453516d3aa87781ceae4210d1a0724d4af30e230ca379d700d88",
          "platform_id": "x_twitter",
          "source_asset_id": "treasury_curve_snapshot",
          "target_aspect_ratio": "16:9",
          "target_height": 675,
          "target_width": 1200
        },
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "landscape_feed_card",
          "derivative_sha256": "8e2f79461371ce07b041a3e0277a75ccaded445929eb5585864125d8ea228122",
          "platform_id": "facebook_page",
          "source_asset_id": "treasury_curve_snapshot",
          "target_aspect_ratio": "1.91:1",
          "target_height": 628,
          "target_width": 1200
        },
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "channel_preview_image",
          "derivative_sha256": "7a2daebdf9eba3e766f55da0e5fda5f49ee51e19c5d24767a1a421fa88b35aea",
          "platform_id": "telegram",
          "source_asset_id": "treasury_2s10s_history",
          "target_aspect_ratio": "16:9",
          "target_height": 720,
          "target_width": 1280
        },
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "community_square_image",
          "derivative_sha256": "0b50f951472ce46db96a43ed75ebe03a6398b82bb71f9c2f6e37112539631209",
          "platform_id": "youtube_community",
          "source_asset_id": "treasury_curve_snapshot",
          "target_aspect_ratio": "1:1",
          "target_height": 1080,
          "target_width": 1080
        },
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "embed_preview_image",
          "derivative_sha256": "7a2daebdf9eba3e766f55da0e5fda5f49ee51e19c5d24767a1a421fa88b35aea",
          "platform_id": "discord",
          "source_asset_id": "treasury_2s10s_history",
          "target_aspect_ratio": "16:9",
          "target_height": 720,
          "target_width": 1280
        },
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "feed_portrait_primary",
          "derivative_sha256": "35b8fab518a712e1f18b3024b6dfacbb64e73ecdd106bc4ad36d6ea025f47962",
          "platform_id": "instagram_business",
          "source_asset_id": "treasury_curve_snapshot",
          "target_aspect_ratio": "4:5",
          "target_height": 1350,
          "target_width": 1080
        },
        {
          "chart_label_preservation_rule": "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED",
          "crop_applied": false,
          "derivative_role": "feed_portrait_secondary",
          "derivative_sha256": "35b8fab518a712e1f18b3024b6dfacbb64e73ecdd106bc4ad36d6ea025f47962",
          "platform_id": "threads",
          "source_asset_id": "treasury_curve_snapshot",
          "target_aspect_ratio": "4:5",
          "target_height": 1350,
          "target_width": 1080
        }
      ],
      "visual_adaptation_blocked": [],
      "visual_adaptation_count": 9,
      "visual_rights_cleared": 3,
      "visual_status": "PASS",
      "visual_strategy": "CHART_LED_WITH_SOURCE_EXCERPT",
      "visual_type": "chart_and_document_excerpt"
    },
    {
      "adjusted_rank": 1,
      "adjusted_score": 18.0,
      "base_rank": 3,
      "base_score": 30.0,
      "base_score_source": "governed_packet_authorized_claim_counts",
      "case_id": "case-regulation-joint-rule",
      "chart_partial_period": null,
      "chart_qa_status": null,
      "chart_title": null,
      "concentration_penalty": 12.0,
      "content_mode": "official_rule_text",
      "deferred_by_portfolio_concentration": false,
      "domain_family": "regulation_or_law",
      "gate_reason": null,
      "geography": "US",
      "governed_disposition": "ELIGIBLE_CANDIDATE",
      "hard_gate_failure": true,
      "lane": "capital_chronicle",
      "material_class": "historical_evaluation_material",
      "outcome": "PACKAGE_REVIEW_BLOCKED",
      "penalty_dimensions": [
        "geography"
      ],
      "portfolio_disposition": "SELECTED",
      "portfolio_disposition_reason": "Cleared hard gates and holds the top diversity-adjusted position.",
      "presented_as_current_news": false,
      "rank_changed_by_concentration": true,
      "review_blocked_roles": [
        "adversarial_final_reviewer"
      ],
      "review_result": "BLOCK",
      "review_role_count": 8,
      "sector": "financial_regulation",
      "seo_contract_status": "COMPLETE",
      "source_family": "nonnumeric_story_scoped_publication_evidence_v1",
      "story_type": "official_action",
      "terminal_state": "REVIEW_BLOCKED",
      "tier1_blocked_count": 1,
      "tier1_blocked_destinations": [
        "instagram_business"
      ],
      "tier1_explicit_outcome_count": 9,
      "tier1_supported_count": 8,
      "visual_adaptation_bindings": [],
      "visual_adaptation_blocked": [
        "instagram_business"
      ],
      "visual_adaptation_count": 0,
      "visual_rights_cleared": 0,
      "visual_status": "PASS",
      "visual_strategy": "TEXT_ONLY_POLICY_PERMITTED",
      "visual_type": "text_only"
    },
    {
      "adjusted_rank": 5,
      "adjusted_score": -9.0,
      "base_rank": 5,
      "base_score": 15.0,
      "base_score_source": "governed_packet_authorized_claim_counts",
      "case_id": "case-politics-fomc-minutes",
      "chart_partial_period": null,
      "chart_qa_status": null,
      "chart_title": null,
      "concentration_penalty": 24.0,
      "content_mode": "official_document_metadata",
      "deferred_by_portfolio_concentration": true,
      "domain_family": "politics_or_policy",
      "gate_reason": "Adjusted score -9.0 is below the configured portfolio balance floor 0.0 after concentration penalties from portfolio-rolling-2026-07-15.",
      "geography": "US",
      "governed_disposition": "ELIGIBLE_CANDIDATE",
      "hard_gate_failure": false,
      "lane": "capital_chronicle",
      "material_class": "historical_evaluation_material",
      "outcome": "DEFER_FOR_PORTFOLIO_BALANCE",
      "penalty_dimensions": [
        "geography",
        "source_family"
      ],
      "portfolio_disposition": "DEFER_FOR_PORTFOLIO_BALANCE",
      "portfolio_disposition_reason": "Adjusted score -9.0 is below the configured portfolio balance floor 0.0 after concentration penalties from portfolio-rolling-2026-07-15.",
      "presented_as_current_news": false,
      "rank_changed_by_concentration": false,
      "review_blocked_roles": [],
      "review_result": null,
      "review_role_count": null,
      "sector": "monetary_policy",
      "seo_contract_status": null,
      "source_family": "story_scoped_publication_evidence_v1",
      "story_type": "official_action",
      "terminal_state": "DEFERRED_FOR_PORTFOLIO_BALANCE",
      "tier1_blocked_count": null,
      "tier1_blocked_destinations": [],
      "tier1_explicit_outcome_count": null,
      "tier1_supported_count": null,
      "visual_adaptation_bindings": [],
      "visual_adaptation_blocked": [],
      "visual_adaptation_count": null,
      "visual_rights_cleared": null,
      "visual_status": null,
      "visual_strategy": null,
      "visual_type": "text_only"
    },
    {
      "adjusted_rank": 4,
      "adjusted_score": 6.0,
      "base_rank": 4,
      "base_score": 30.0,
      "base_score_source": "governed_packet_authorized_claim_counts",
      "case_id": "case-us-equities-apple-10q",
      "chart_partial_period": null,
      "chart_qa_status": null,
      "chart_title": null,
      "concentration_penalty": 24.0,
      "content_mode": "official_filing_metadata",
      "deferred_by_portfolio_concentration": false,
      "domain_family": "us_equities_or_big_tech",
      "gate_reason": null,
      "geography": "US",
      "governed_disposition": "ELIGIBLE_CANDIDATE",
      "hard_gate_failure": true,
      "lane": "capital_chronicle",
      "material_class": "historical_evaluation_material",
      "outcome": "PACKAGE_REVIEW_BLOCKED",
      "penalty_dimensions": [
        "geography",
        "source_family"
      ],
      "portfolio_disposition": "SELECTED",
      "portfolio_disposition_reason": "Cleared hard gates and holds the top diversity-adjusted position.",
      "presented_as_current_news": false,
      "rank_changed_by_concentration": false,
      "review_blocked_roles": [
        "adversarial_final_reviewer"
      ],
      "review_result": "BLOCK",
      "review_role_count": 8,
      "sector": "information_technology",
      "seo_contract_status": "COMPLETE",
      "source_family": "story_scoped_publication_evidence_v1",
      "story_type": "official_action",
      "terminal_state": "REVIEW_BLOCKED",
      "tier1_blocked_count": 1,
      "tier1_blocked_destinations": [
        "instagram_business"
      ],
      "tier1_explicit_outcome_count": 9,
      "tier1_supported_count": 8,
      "visual_adaptation_bindings": [],
      "visual_adaptation_blocked": [
        "instagram_business"
      ],
      "visual_adaptation_count": 0,
      "visual_rights_cleared": 0,
      "visual_status": "PASS",
      "visual_strategy": "TEXT_ONLY_POLICY_PERMITTED",
      "visual_type": "text_only"
    },
    {
      "adjusted_rank": null,
      "adjusted_score": null,
      "base_rank": null,
      "base_score": null,
      "base_score_source": null,
      "case_id": "case-sector-usgs-ridgecrest",
      "chart_partial_period": null,
      "chart_qa_status": null,
      "chart_title": null,
      "concentration_penalty": null,
      "content_mode": "official_event_metadata",
      "deferred_by_portfolio_concentration": false,
      "domain_family": "sector_or_industry",
      "gate_reason": "Historical material only; NO_PUBLICATION is the valid outcome.",
      "geography": "US",
      "governed_disposition": "HISTORICAL_NOT_CURRENT",
      "hard_gate_failure": true,
      "lane": "capital_chronicle",
      "material_class": "historical_evaluation_material",
      "outcome": "HISTORICAL_NOT_CURRENT",
      "penalty_dimensions": [],
      "portfolio_disposition": null,
      "portfolio_disposition_reason": null,
      "presented_as_current_news": false,
      "rank_changed_by_concentration": null,
      "review_blocked_roles": [],
      "review_result": null,
      "review_role_count": null,
      "sector": "infrastructure_and_natural_hazard",
      "seo_contract_status": null,
      "source_family": "story_scoped_publication_evidence_v1",
      "story_type": "official_action",
      "terminal_state": "NO_PUBLICATION",
      "tier1_blocked_count": null,
      "tier1_blocked_destinations": [],
      "tier1_explicit_outcome_count": null,
      "tier1_supported_count": null,
      "visual_adaptation_bindings": [],
      "visual_adaptation_blocked": [],
      "visual_adaptation_count": null,
      "visual_rights_cleared": null,
      "visual_status": null,
      "visual_strategy": null,
      "visual_type": "text_only"
    },
    {
      "adjusted_rank": null,
      "adjusted_score": null,
      "base_rank": null,
      "base_score": null,
      "base_score_source": null,
      "case_id": "case-capital-chronicle-duplicate-replay",
      "chart_partial_period": null,
      "chart_qa_status": null,
      "chart_title": null,
      "concentration_penalty": null,
      "content_mode": "numeric_official_record",
      "deferred_by_portfolio_concentration": false,
      "domain_family": "capital_chronicle_analysis",
      "gate_reason": "Same governed update chain already assigned; no new delta.",
      "geography": "US",
      "governed_disposition": "DUPLICATE_OR_LOW_DELTA",
      "hard_gate_failure": true,
      "lane": "capital_chronicle",
      "material_class": "historical_evaluation_material",
      "outcome": "DUPLICATE_OR_LOW_DELTA",
      "penalty_dimensions": [],
      "portfolio_disposition": null,
      "portfolio_disposition_reason": null,
      "presented_as_current_news": false,
      "rank_changed_by_concentration": null,
      "review_blocked_roles": [],
      "review_result": null,
      "review_role_count": null,
      "sector": "government_bonds",
      "seo_contract_status": null,
      "source_family": "story_scoped_publication_evidence_v1",
      "story_type": "data_release",
      "terminal_state": "DUPLICATE_SUPPRESSED",
      "tier1_blocked_count": null,
      "tier1_blocked_destinations": [],
      "tier1_explicit_outcome_count": null,
      "tier1_supported_count": null,
      "visual_adaptation_bindings": [],
      "visual_adaptation_blocked": [],
      "visual_adaptation_count": null,
      "visual_rights_cleared": null,
      "visual_status": null,
      "visual_strategy": null,
      "visual_type": "chart_and_document_excerpt"
    },
    {
      "adjusted_rank": null,
      "adjusted_score": null,
      "base_rank": null,
      "base_score": null,
      "base_score_source": null,
      "case_id": "case-geopolitics-ofac-context-only",
      "chart_partial_period": null,
      "chart_qa_status": null,
      "chart_title": null,
      "concentration_penalty": null,
      "content_mode": "official_entity_snapshot",
      "deferred_by_portfolio_concentration": false,
      "domain_family": "geopolitics_trade_or_supply_chain",
      "gate_reason": "Source-family permission ceiling is CONTEXT_ONLY; reporting not granted.",
      "geography": "global",
      "governed_disposition": "PERMISSION_BLOCKED",
      "hard_gate_failure": true,
      "lane": "newsroom",
      "material_class": "historical_evaluation_material",
      "outcome": "PERMISSION_BLOCKED",
      "penalty_dimensions": [],
      "portfolio_disposition": null,
      "portfolio_disposition_reason": null,
      "presented_as_current_news": false,
      "rank_changed_by_concentration": null,
      "review_blocked_roles": [],
      "review_result": null,
      "review_role_count": null,
      "sector": "sanctions_and_trade",
      "seo_contract_status": null,
      "source_family": "dbh2_ofac_official_entity_snapshot",
      "story_type": "geopolitical_event",
      "terminal_state": "REVIEW_BLOCKED",
      "tier1_blocked_count": null,
      "tier1_blocked_destinations": [],
      "tier1_explicit_outcome_count": null,
      "tier1_supported_count": null,
      "visual_adaptation_bindings": [],
      "visual_adaptation_blocked": [],
      "visual_adaptation_count": null,
      "visual_rights_cleared": null,
      "visual_status": null,
      "visual_strategy": null,
      "visual_type": "text_only"
    },
    {
      "adjusted_rank": null,
      "adjusted_score": null,
      "base_rank": null,
      "base_score": null,
      "base_score_source": null,
      "case_id": "case-economic-release-federal-register",
      "chart_partial_period": null,
      "chart_qa_status": null,
      "chart_title": null,
      "concentration_penalty": null,
      "content_mode": "official_document_metadata",
      "deferred_by_portfolio_concentration": false,
      "domain_family": "economic_release",
      "gate_reason": "Governed candidate carries a context_only_evidence blocker.",
      "geography": "US",
      "governed_disposition": "EVIDENCE_BLOCKED",
      "hard_gate_failure": true,
      "lane": "newsroom",
      "material_class": "historical_evaluation_material",
      "outcome": "EVIDENCE_BLOCKED",
      "penalty_dimensions": [],
      "portfolio_disposition": null,
      "portfolio_disposition_reason": null,
      "presented_as_current_news": false,
      "rank_changed_by_concentration": null,
      "review_blocked_roles": [],
      "review_result": null,
      "review_role_count": null,
      "sector": "federal_rulemaking",
      "seo_contract_status": null,
      "source_family": "dbh2_federal_register_official_document",
      "story_type": "official_action",
      "terminal_state": "REVIEW_BLOCKED",
      "tier1_blocked_count": null,
      "tier1_blocked_destinations": [],
      "tier1_explicit_outcome_count": null,
      "tier1_supported_count": null,
      "visual_adaptation_bindings": [],
      "visual_adaptation_blocked": [],
      "visual_adaptation_count": null,
      "visual_rights_cleared": null,
      "visual_status": null,
      "visual_strategy": null,
      "visual_type": "text_only"
    },
    {
      "adjusted_rank": null,
      "adjusted_score": null,
      "base_rank": null,
      "base_score": null,
      "base_score_source": null,
      "case_id": "case-commodity-visual-rights-blocked",
      "chart_partial_period": null,
      "chart_qa_status": null,
      "chart_title": null,
      "concentration_penalty": null,
      "content_mode": "context_visual_only",
      "deferred_by_portfolio_concentration": false,
      "domain_family": "fx_commodity_energy_or_materials",
      "gate_reason": "No rights-cleared visual asset; unreviewed image withheld.",
      "geography": "global",
      "governed_disposition": "VISUAL_RIGHTS_BLOCKED",
      "hard_gate_failure": true,
      "lane": "newsroom",
      "material_class": "historical_evaluation_material",
      "outcome": "VISUAL_RIGHTS_BLOCKED",
      "penalty_dimensions": [],
      "portfolio_disposition": null,
      "portfolio_disposition_reason": null,
      "presented_as_current_news": false,
      "rank_changed_by_concentration": null,
      "review_blocked_roles": [],
      "review_result": null,
      "review_role_count": null,
      "sector": "energy",
      "seo_contract_status": null,
      "source_family": "dbh2_usgs_official_physical_event",
      "story_type": "supply_chain_event",
      "terminal_state": "REVIEW_BLOCKED",
      "tier1_blocked_count": null,
      "tier1_blocked_destinations": [],
      "tier1_explicit_outcome_count": null,
      "tier1_supported_count": null,
      "visual_adaptation_bindings": [],
      "visual_adaptation_blocked": [],
      "visual_adaptation_count": null,
      "visual_rights_cleared": null,
      "visual_status": "BLOCK",
      "visual_strategy": null,
      "visual_type": "unreviewed_search_image"
    }
  ],
  "concentration_penalties": [
    {
      "adjusted_rank": 1,
      "adjusted_score": 18.0,
      "base_rank": 3,
      "base_score": 30.0,
      "base_score_source": "governed_packet_authorized_claim_counts",
      "case_id": "case-regulation-joint-rule",
      "concentration_penalty": 12.0,
      "disposition": "SELECTED",
      "penalties_applied": [
        {
          "dimension": "geography",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "US"
        }
      ],
      "rank_changed_by_concentration": true
    },
    {
      "adjusted_rank": 2,
      "adjusted_score": 16.0,
      "base_rank": 1,
      "base_score": 100.0,
      "base_score_source": "governed_packet_authorized_claim_counts",
      "case_id": "case-rates-ust-curve",
      "concentration_penalty": 84.0,
      "disposition": "SELECTED",
      "penalties_applied": [
        {
          "dimension": "domain_family",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "rates_or_credit"
        },
        {
          "dimension": "entities",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "U.S. Department of the Treasury"
        },
        {
          "dimension": "sector",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "government_bonds"
        },
        {
          "dimension": "geography",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "US"
        },
        {
          "dimension": "source_family",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "story_scoped_publication_evidence_v1"
        },
        {
          "dimension": "content_mode",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "numeric_official_record"
        },
        {
          "dimension": "visual_type",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "chart_and_document_excerpt"
        }
      ],
      "rank_changed_by_concentration": true
    },
    {
      "adjusted_rank": 3,
      "adjusted_score": 6.66666667,
      "base_rank": 2,
      "base_score": 66.66666667,
      "base_score_source": "universal_news_candidate_fabric_v2.score_candidate",
      "case_id": "case-economic-release-ust-newsroom",
      "concentration_penalty": 60.0,
      "disposition": "SELECTED",
      "penalties_applied": [
        {
          "dimension": "entities",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "U.S. Department of the Treasury"
        },
        {
          "dimension": "sector",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "government_bonds"
        },
        {
          "dimension": "geography",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "US"
        },
        {
          "dimension": "source_family",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "story_scoped_publication_evidence_v1"
        },
        {
          "dimension": "visual_type",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "chart_and_document_excerpt"
        }
      ],
      "rank_changed_by_concentration": true
    },
    {
      "adjusted_rank": 4,
      "adjusted_score": 6.0,
      "base_rank": 4,
      "base_score": 30.0,
      "base_score_source": "governed_packet_authorized_claim_counts",
      "case_id": "case-us-equities-apple-10q",
      "concentration_penalty": 24.0,
      "disposition": "SELECTED",
      "penalties_applied": [
        {
          "dimension": "geography",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "US"
        },
        {
          "dimension": "source_family",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "story_scoped_publication_evidence_v1"
        }
      ],
      "rank_changed_by_concentration": false
    },
    {
      "adjusted_rank": 5,
      "adjusted_score": -9.0,
      "base_rank": 5,
      "base_score": 15.0,
      "base_score_source": "governed_packet_authorized_claim_counts",
      "case_id": "case-politics-fomc-minutes",
      "concentration_penalty": 24.0,
      "disposition": "DEFER_FOR_PORTFOLIO_BALANCE",
      "penalties_applied": [
        {
          "dimension": "geography",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "US"
        },
        {
          "dimension": "source_family",
          "penalty_amount": 12.0,
          "prior_history_basis": {
            "history_window_end_utc": "2026-07-15T00:00:00Z",
            "history_window_start_utc": "2026-04-16T00:00:00Z",
            "prior_count": 1,
            "prior_share": 1.0,
            "rolling_report_id": "portfolio-rolling-2026-07-15",
            "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
            "threshold": 0.34
          },
          "value": "story_scoped_publication_evidence_v1"
        }
      ],
      "rank_changed_by_concentration": false
    }
  ],
  "corpus": {
    "case_count": 10,
    "coverage": {
      "all_families_represented": true,
      "cases_by_family": {
        "capital_chronicle_analysis": [
          "case-capital-chronicle-duplicate-replay"
        ],
        "economic_release": [
          "case-economic-release-federal-register",
          "case-economic-release-ust-newsroom"
        ],
        "fx_commodity_energy_or_materials": [
          "case-commodity-visual-rights-blocked"
        ],
        "geopolitics_trade_or_supply_chain": [
          "case-geopolitics-ofac-context-only"
        ],
        "politics_or_policy": [
          "case-politics-fomc-minutes"
        ],
        "rates_or_credit": [
          "case-rates-ust-curve"
        ],
        "regulation_or_law": [
          "case-regulation-joint-rule"
        ],
        "sector_or_industry": [
          "case-sector-usgs-ridgecrest"
        ],
        "us_equities_or_big_tech": [
          "case-us-equities-apple-10q"
        ]
      },
      "families_represented": 9,
      "families_required": 9
    },
    "domain_family_count": 9,
    "fabricated_content": false,
    "governed_artifact_paths": [
      "docs/automation/CONTENTOPS_FAST_SHIP_MULTI_STORY_PLATFORM_NATIVE_OPERATOR_PACKAGES_V1/canonical_content_evidence_packets_v3.json",
      "docs/automation/CONTENTOPS_NONNUMERIC_STORY_AUTHORITY_CONSUMPTION_AND_FIRST_EDITORIAL_SHADOW_DRAFT_V1/generic_v3_claim_packet_and_editorial_outcome.json",
      "docs/automation/CONTENTOPS_UNIVERSAL_NEWS_EVENT_CANDIDATE_FABRIC_V2_AND_CROSS_DOMAIN_ASSIGNMENT_CANARY_V1/cross_domain_candidate_pool.json",
      "docs/automation/CONTENTOPS_VERIFIER_DERIVED_PERMISSION_GENERIC_CLAIM_PACKET_AND_CROSS_DOMAIN_EDITORIAL_SHADOW_V1/generic_v3_claim_packet_and_editorial_outcome.json"
    ],
    "material_class": "historical_evaluation_material"
  },
  "credential_read_performed": false,
  "decision_window_id": "2026-07-15",
  "decision_window_start_utc": "2026-07-15T00:00:00Z",
  "dispatch_authority": false,
  "durable": {
    "terminal_states": {
      "wi_case_capital_chronicle_duplicate_replay": "DUPLICATE_SUPPRESSED",
      "wi_case_commodity_visual_rights_blocked": "REVIEW_BLOCKED",
      "wi_case_economic_release_federal_register": "REVIEW_BLOCKED",
      "wi_case_economic_release_ust_newsroom": "REVIEW_READY",
      "wi_case_geopolitics_ofac_context_only": "REVIEW_BLOCKED",
      "wi_case_politics_fomc_minutes": "DEFERRED_FOR_PORTFOLIO_BALANCE",
      "wi_case_rates_ust_curve": "REVIEW_READY",
      "wi_case_regulation_joint_rule": "REVIEW_BLOCKED",
      "wi_case_sector_usgs_ridgecrest": "NO_PUBLICATION",
      "wi_case_us_equities_apple_10q": "REVIEW_BLOCKED"
    },
    "work_item_ids": [
      "wi_case_economic_release_ust_newsroom",
      "wi_case_rates_ust_curve",
      "wi_case_regulation_joint_rule",
      "wi_case_politics_fomc_minutes",
      "wi_case_us_equities_apple_10q",
      "wi_case_sector_usgs_ridgecrest",
      "wi_case_capital_chronicle_duplicate_replay",
      "wi_case_geopolitics_ofac_context_only",
      "wi_case_economic_release_federal_register",
      "wi_case_commodity_visual_rights_blocked"
    ]
  },
  "external_cost": "NONE_NO_PAID_API_OR_MODEL_CALL",
  "generated_from_real_run": true,
  "hard_gate_excluded": [
    {
      "case_id": "case-sector-usgs-ridgecrest",
      "exclusion_reason": "HISTORICAL_NOT_CURRENT",
      "hard_gate_failure": true
    },
    {
      "case_id": "case-capital-chronicle-duplicate-replay",
      "exclusion_reason": "DUPLICATE_OR_LOW_DELTA",
      "hard_gate_failure": true
    },
    {
      "case_id": "case-geopolitics-ofac-context-only",
      "exclusion_reason": "PERMISSION_BLOCKED",
      "hard_gate_failure": true
    },
    {
      "case_id": "case-economic-release-federal-register",
      "exclusion_reason": "EVIDENCE_BLOCKED",
      "hard_gate_failure": true
    },
    {
      "case_id": "case-commodity-visual-rights-blocked",
      "exclusion_reason": "VISUAL_RIGHTS_BLOCKED",
      "hard_gate_failure": true
    }
  ],
  "lanes_with_passing_package": [
    "capital_chronicle",
    "newsroom"
  ],
  "network_call_performed": false,
  "operating_mode": "SHADOW_ONLY",
  "outcome_counts": {
    "deferred_for_portfolio_balance": 1,
    "duplicate_or_low_delta": 1,
    "eligible_review_passed": 2,
    "evidence_blocked": 1,
    "no_publication": 1,
    "package_review_blocked": 2,
    "permission_blocked": 1,
    "visual_rights_blocked": 1
  },
  "package_fabric": "multi_story_platform_native_operator_packages_v1.build_platform_native_variant",
  "platform_visual_adaptation": {
    "adapted_destination_counts": {
      "case-economic-release-ust-newsroom": 9,
      "case-rates-ust-curve": 9,
      "case-regulation-joint-rule": 0,
      "case-us-equities-apple-10q": 0
    },
    "adapter": "core_v0_platform_visual_adaptation_v1.adapt_package_visuals",
    "blocked_destinations_by_case": {
      "case-economic-release-ust-newsroom": [],
      "case-rates-ust-curve": [],
      "case-regulation-joint-rule": [
        "instagram_business"
      ],
      "case-us-equities-apple-10q": [
        "instagram_business"
      ]
    },
    "derivative_hashes_by_case": {
      "case-economic-release-ust-newsroom": {
        "discord": "7a2daebdf9eba3e766f55da0e5fda5f49ee51e19c5d24767a1a421fa88b35aea",
        "facebook_page": "8e2f79461371ce07b041a3e0277a75ccaded445929eb5585864125d8ea228122",
        "instagram_business": "35b8fab518a712e1f18b3024b6dfacbb64e73ecdd106bc4ad36d6ea025f47962",
        "linkedin": "acff88c29bdf9b46dfd35053d3d073f63be7825d0b70008ae1b1148d63e530dc",
        "substack_newsletter": "2d2a5b8cb616510fa977fb7d1a9411c2f44a6545be83cf92335b7bfed33ad064",
        "telegram": "7a2daebdf9eba3e766f55da0e5fda5f49ee51e19c5d24767a1a421fa88b35aea",
        "threads": "35b8fab518a712e1f18b3024b6dfacbb64e73ecdd106bc4ad36d6ea025f47962",
        "x_twitter": "560c41640adf453516d3aa87781ceae4210d1a0724d4af30e230ca379d700d88",
        "youtube_community": "0b50f951472ce46db96a43ed75ebe03a6398b82bb71f9c2f6e37112539631209"
      },
      "case-rates-ust-curve": {
        "discord": "7a2daebdf9eba3e766f55da0e5fda5f49ee51e19c5d24767a1a421fa88b35aea",
        "facebook_page": "8e2f79461371ce07b041a3e0277a75ccaded445929eb5585864125d8ea228122",
        "instagram_business": "35b8fab518a712e1f18b3024b6dfacbb64e73ecdd106bc4ad36d6ea025f47962",
        "linkedin": "acff88c29bdf9b46dfd35053d3d073f63be7825d0b70008ae1b1148d63e530dc",
        "substack_newsletter": "2d2a5b8cb616510fa977fb7d1a9411c2f44a6545be83cf92335b7bfed33ad064",
        "telegram": "7a2daebdf9eba3e766f55da0e5fda5f49ee51e19c5d24767a1a421fa88b35aea",
        "threads": "35b8fab518a712e1f18b3024b6dfacbb64e73ecdd106bc4ad36d6ea025f47962",
        "x_twitter": "560c41640adf453516d3aa87781ceae4210d1a0724d4af30e230ca379d700d88",
        "youtube_community": "0b50f951472ce46db96a43ed75ebe03a6398b82bb71f9c2f6e37112539631209"
      },
      "case-regulation-joint-rule": {},
      "case-us-equities-apple-10q": {}
    },
    "packages_adapted": 4,
    "single_canonical_adaptation_path": true
  },
  "portfolio_daily": {
    "basis": "CURRENT_DECISION_WINDOW_CANDIDATES",
    "case_count": 5,
    "concentrated_dimensions": [
      "geography",
      "sector",
      "source_family",
      "visual_type"
    ],
    "concentration_threshold": 0.34,
    "decision_window_id": "2026-07-15",
    "dimensions": {
      "content_mode": {
        "concentrated_values": [],
        "counts": {
          "numeric_official_record": 1,
          "numeric_official_release": 1,
          "official_document_metadata": 1,
          "official_filing_metadata": 1,
          "official_rule_text": 1
        },
        "distinct_values": 5,
        "is_concentrated": false,
        "max_share": 0.2,
        "shares": {
          "numeric_official_record": 0.2,
          "numeric_official_release": 0.2,
          "official_document_metadata": 0.2,
          "official_filing_metadata": 0.2,
          "official_rule_text": 0.2
        }
      },
      "domain_family": {
        "concentrated_values": [],
        "counts": {
          "economic_release": 1,
          "politics_or_policy": 1,
          "rates_or_credit": 1,
          "regulation_or_law": 1,
          "us_equities_or_big_tech": 1
        },
        "distinct_values": 5,
        "is_concentrated": false,
        "max_share": 0.2,
        "shares": {
          "economic_release": 0.2,
          "politics_or_policy": 0.2,
          "rates_or_credit": 0.2,
          "regulation_or_law": 0.2,
          "us_equities_or_big_tech": 0.2
        }
      },
      "entities": {
        "concentrated_values": [],
        "counts": {
          "Apple Inc.": 1,
          "CFPB": 1,
          "CFTC": 1,
          "FDIC": 1,
          "FHFA": 1,
          "Federal Open Market Committee": 1,
          "NCUA": 1,
          "OCC": 1,
          "SEC": 1,
          "U.S. Department of the Treasury": 2
        },
        "distinct_values": 10,
        "is_concentrated": false,
        "max_share": 0.181818,
        "shares": {
          "Apple Inc.": 0.090909,
          "CFPB": 0.090909,
          "CFTC": 0.090909,
          "FDIC": 0.090909,
          "FHFA": 0.090909,
          "Federal Open Market Committee": 0.090909,
          "NCUA": 0.090909,
          "OCC": 0.090909,
          "SEC": 0.090909,
          "U.S. Department of the Treasury": 0.181818
        }
      },
      "geography": {
        "concentrated_values": [
          "US"
        ],
        "counts": {
          "US": 5
        },
        "distinct_values": 1,
        "is_concentrated": true,
        "max_share": 1.0,
        "shares": {
          "US": 1.0
        }
      },
      "sector": {
        "concentrated_values": [
          "government_bonds"
        ],
        "counts": {
          "financial_regulation": 1,
          "government_bonds": 2,
          "information_technology": 1,
          "monetary_policy": 1
        },
        "distinct_values": 4,
        "is_concentrated": true,
        "max_share": 0.4,
        "shares": {
          "financial_regulation": 0.2,
          "government_bonds": 0.4,
          "information_technology": 0.2,
          "monetary_policy": 0.2
        }
      },
      "source_family": {
        "concentrated_values": [
          "story_scoped_publication_evidence_v1"
        ],
        "counts": {
          "nonnumeric_story_scoped_publication_evidence_v1": 1,
          "story_scoped_publication_evidence_v1": 4
        },
        "distinct_values": 2,
        "is_concentrated": true,
        "max_share": 0.8,
        "shares": {
          "nonnumeric_story_scoped_publication_evidence_v1": 0.2,
          "story_scoped_publication_evidence_v1": 0.8
        }
      },
      "visual_type": {
        "concentrated_values": [
          "chart_and_document_excerpt",
          "text_only"
        ],
        "counts": {
          "chart_and_document_excerpt": 2,
          "text_only": 3
        },
        "distinct_values": 2,
        "is_concentrated": true,
        "max_share": 0.6,
        "shares": {
          "chart_and_document_excerpt": 0.4,
          "text_only": 0.6
        }
      }
    },
    "diversity_never_forces_filler": true,
    "excluded_ids": [
      "case-capital-chronicle-duplicate-replay",
      "case-commodity-visual-rights-blocked",
      "case-economic-release-federal-register",
      "case-geopolitics-ofac-context-only",
      "case-sector-usgs-ridgecrest"
    ],
    "exclusion_reasons": {
      "case-capital-chronicle-duplicate-replay": "DUPLICATE_OR_LOW_DELTA",
      "case-commodity-visual-rights-blocked": "VISUAL_RIGHTS_BLOCKED",
      "case-economic-release-federal-register": "EVIDENCE_BLOCKED",
      "case-geopolitics-ofac-context-only": "PERMISSION_BLOCKED",
      "case-sector-usgs-ridgecrest": "HISTORICAL_NOT_CURRENT"
    },
    "hard_gates_remain_authoritative": true,
    "history_window_end_utc": null,
    "history_window_start_utc": null,
    "included_current_candidate_ids": [
      "case-economic-release-ust-newsroom",
      "case-politics-fomc-minutes",
      "case-rates-ust-curve",
      "case-regulation-joint-rule",
      "case-us-equities-apple-10q"
    ],
    "included_prior_selected_ids": [],
    "report_id": "portfolio-daily-2026-07-15",
    "report_label": "daily",
    "report_logical_hash": "c0af1f275434e959a1faac079a7d7b3f4f1f7a1bf403ffe20b90934d778d0eb8",
    "schema_version": "contentops.core_v0_portfolio_windows.v1",
    "window_end_utc": "2026-07-15T22:30:00Z",
    "window_start_utc": "2026-05-01T00:00:00Z"
  },
  "portfolio_decision": {
    "concentration_threshold": 0.34,
    "decision_logical_hash": "d4883c145f65e867a5647700a98851ded7ca58d0eea0f241aed82a948a4aa56e",
    "decision_window_id": "2026-07-15",
    "decisions": [
      {
        "adjusted_rank": 1,
        "adjusted_score": 18.0,
        "base_rank": 3,
        "base_score": 30.0,
        "base_score_source": "governed_packet_authorized_claim_counts",
        "case_id": "case-regulation-joint-rule",
        "concentration_penalty": 12.0,
        "disposition": "SELECTED",
        "disposition_reason": "Cleared hard gates and holds the top diversity-adjusted position.",
        "domain_family": "regulation_or_law",
        "lane": "capital_chronicle",
        "penalties_applied": [
          {
            "dimension": "geography",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "US"
          }
        ],
        "produces_package": true,
        "rank_changed_by_concentration": true,
        "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1"
      },
      {
        "adjusted_rank": 2,
        "adjusted_score": 16.0,
        "base_rank": 1,
        "base_score": 100.0,
        "base_score_source": "governed_packet_authorized_claim_counts",
        "case_id": "case-rates-ust-curve",
        "concentration_penalty": 84.0,
        "disposition": "SELECTED",
        "disposition_reason": "Cleared hard gates and holds the top diversity-adjusted position.",
        "domain_family": "rates_or_credit",
        "lane": "capital_chronicle",
        "penalties_applied": [
          {
            "dimension": "domain_family",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "rates_or_credit"
          },
          {
            "dimension": "entities",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "U.S. Department of the Treasury"
          },
          {
            "dimension": "sector",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "government_bonds"
          },
          {
            "dimension": "geography",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "US"
          },
          {
            "dimension": "source_family",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "story_scoped_publication_evidence_v1"
          },
          {
            "dimension": "content_mode",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "numeric_official_record"
          },
          {
            "dimension": "visual_type",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "chart_and_document_excerpt"
          }
        ],
        "produces_package": true,
        "rank_changed_by_concentration": true,
        "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1"
      },
      {
        "adjusted_rank": 3,
        "adjusted_score": 6.66666667,
        "base_rank": 2,
        "base_score": 66.66666667,
        "base_score_source": "universal_news_candidate_fabric_v2.score_candidate",
        "case_id": "case-economic-release-ust-newsroom",
        "concentration_penalty": 60.0,
        "disposition": "SELECTED",
        "disposition_reason": "Cleared hard gates and holds the top diversity-adjusted position.",
        "domain_family": "economic_release",
        "lane": "newsroom",
        "penalties_applied": [
          {
            "dimension": "entities",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "U.S. Department of the Treasury"
          },
          {
            "dimension": "sector",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "government_bonds"
          },
          {
            "dimension": "geography",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "US"
          },
          {
            "dimension": "source_family",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "story_scoped_publication_evidence_v1"
          },
          {
            "dimension": "visual_type",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "chart_and_document_excerpt"
          }
        ],
        "produces_package": true,
        "rank_changed_by_concentration": true,
        "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1"
      },
      {
        "adjusted_rank": 4,
        "adjusted_score": 6.0,
        "base_rank": 4,
        "base_score": 30.0,
        "base_score_source": "governed_packet_authorized_claim_counts",
        "case_id": "case-us-equities-apple-10q",
        "concentration_penalty": 24.0,
        "disposition": "SELECTED",
        "disposition_reason": "Cleared hard gates and holds the top diversity-adjusted position.",
        "domain_family": "us_equities_or_big_tech",
        "lane": "capital_chronicle",
        "penalties_applied": [
          {
            "dimension": "geography",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "US"
          },
          {
            "dimension": "source_family",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "story_scoped_publication_evidence_v1"
          }
        ],
        "produces_package": true,
        "rank_changed_by_concentration": false,
        "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1"
      },
      {
        "adjusted_rank": 5,
        "adjusted_score": -9.0,
        "base_rank": 5,
        "base_score": 15.0,
        "base_score_source": "governed_packet_authorized_claim_counts",
        "case_id": "case-politics-fomc-minutes",
        "concentration_penalty": 24.0,
        "disposition": "DEFER_FOR_PORTFOLIO_BALANCE",
        "disposition_reason": "Adjusted score -9.0 is below the configured portfolio balance floor 0.0 after concentration penalties from portfolio-rolling-2026-07-15.",
        "domain_family": "politics_or_policy",
        "lane": "capital_chronicle",
        "penalties_applied": [
          {
            "dimension": "geography",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "US"
          },
          {
            "dimension": "source_family",
            "penalty_amount": 12.0,
            "prior_history_basis": {
              "history_window_end_utc": "2026-07-15T00:00:00Z",
              "history_window_start_utc": "2026-04-16T00:00:00Z",
              "prior_count": 1,
              "prior_share": 1.0,
              "rolling_report_id": "portfolio-rolling-2026-07-15",
              "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
              "threshold": 0.34
            },
            "value": "story_scoped_publication_evidence_v1"
          }
        ],
        "produces_package": false,
        "rank_changed_by_concentration": false,
        "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1"
      }
    ],
    "defer_below_adjusted_score": 0.0,
    "deferred_case_ids": [
      "case-politics-fomc-minutes"
    ],
    "diversity_never_forces_filler": true,
    "eligible_count": 5,
    "hard_gates_remain_authoritative": true,
    "held_case_ids": [],
    "max_selected": null,
    "no_publication": false,
    "penalties_applied_before_production": true,
    "penalty_per_concentrated_value": 12.0,
    "reordered_case_ids": [
      "case-economic-release-ust-newsroom",
      "case-rates-ust-curve",
      "case-regulation-joint-rule"
    ],
    "rolling_report_id": "portfolio-rolling-2026-07-15",
    "rolling_report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
    "schema_version": "contentops.core_v0_portfolio_windows.v1",
    "selected_case_ids": [
      "case-economic-release-ust-newsroom",
      "case-rates-ust-curve",
      "case-regulation-joint-rule",
      "case-us-equities-apple-10q"
    ]
  },
  "portfolio_rolling": {
    "basis": "ACCEPTED_PUBLICATION_HISTORY_PLUS_CURRENT_SELECTED_STATE",
    "blocked_or_rejected_counted_as_published_history": false,
    "case_count": 1,
    "concentrated_dimensions": [
      "content_mode",
      "domain_family",
      "entities",
      "geography",
      "sector",
      "source_family",
      "visual_type"
    ],
    "concentration_threshold": 0.34,
    "decision_window_id": "2026-07-15",
    "dimensions": {
      "content_mode": {
        "concentrated_values": [
          "numeric_official_record"
        ],
        "counts": {
          "numeric_official_record": 1
        },
        "distinct_values": 1,
        "is_concentrated": true,
        "max_share": 1.0,
        "shares": {
          "numeric_official_record": 1.0
        }
      },
      "domain_family": {
        "concentrated_values": [
          "rates_or_credit"
        ],
        "counts": {
          "rates_or_credit": 1
        },
        "distinct_values": 1,
        "is_concentrated": true,
        "max_share": 1.0,
        "shares": {
          "rates_or_credit": 1.0
        }
      },
      "entities": {
        "concentrated_values": [
          "U.S. Department of the Treasury"
        ],
        "counts": {
          "U.S. Department of the Treasury": 1
        },
        "distinct_values": 1,
        "is_concentrated": true,
        "max_share": 1.0,
        "shares": {
          "U.S. Department of the Treasury": 1.0
        }
      },
      "geography": {
        "concentrated_values": [
          "US"
        ],
        "counts": {
          "US": 1
        },
        "distinct_values": 1,
        "is_concentrated": true,
        "max_share": 1.0,
        "shares": {
          "US": 1.0
        }
      },
      "sector": {
        "concentrated_values": [
          "government_bonds"
        ],
        "counts": {
          "government_bonds": 1
        },
        "distinct_values": 1,
        "is_concentrated": true,
        "max_share": 1.0,
        "shares": {
          "government_bonds": 1.0
        }
      },
      "source_family": {
        "concentrated_values": [
          "story_scoped_publication_evidence_v1"
        ],
        "counts": {
          "story_scoped_publication_evidence_v1": 1
        },
        "distinct_values": 1,
        "is_concentrated": true,
        "max_share": 1.0,
        "shares": {
          "story_scoped_publication_evidence_v1": 1.0
        }
      },
      "visual_type": {
        "concentrated_values": [
          "chart_and_document_excerpt"
        ],
        "counts": {
          "chart_and_document_excerpt": 1
        },
        "distinct_values": 1,
        "is_concentrated": true,
        "max_share": 1.0,
        "shares": {
          "chart_and_document_excerpt": 1.0
        }
      }
    },
    "diversity_never_forces_filler": true,
    "excluded_ids": [
      "case-capital-chronicle-duplicate-replay",
      "case-commodity-visual-rights-blocked",
      "case-economic-release-federal-register",
      "case-geopolitics-ofac-context-only",
      "case-sector-usgs-ridgecrest"
    ],
    "exclusion_reasons": {
      "case-capital-chronicle-duplicate-replay": "DUPLICATE_OR_LOW_DELTA",
      "case-commodity-visual-rights-blocked": "VISUAL_RIGHTS_BLOCKED",
      "case-economic-release-federal-register": "EVIDENCE_BLOCKED",
      "case-geopolitics-ofac-context-only": "PERMISSION_BLOCKED",
      "case-sector-usgs-ridgecrest": "HISTORICAL_NOT_CURRENT"
    },
    "hard_gates_remain_authoritative": true,
    "historical_dates_preserved": true,
    "history_window_days": 90,
    "history_window_end_utc": "2026-07-15T00:00:00Z",
    "history_window_start_utc": "2026-04-16T00:00:00Z",
    "included_current_candidate_ids": [],
    "included_prior_selected_ids": [
      "history-us-treasury-curve-2026-07-13"
    ],
    "presented_as_current_news": false,
    "report_id": "portfolio-rolling-2026-07-15",
    "report_label": "rolling",
    "report_logical_hash": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
    "schema_version": "contentops.core_v0_portfolio_windows.v1",
    "window_end_utc": "2026-07-11T02:00:00Z",
    "window_start_utc": "2026-07-11T02:00:00Z"
  },
  "portfolio_rolling_with_current_state": {
    "basis": "ACCEPTED_PUBLICATION_HISTORY_PLUS_CURRENT_SELECTED_STATE",
    "blocked_or_rejected_counted_as_published_history": false,
    "case_count": 5,
    "concentrated_dimensions": [
      "content_mode",
      "domain_family",
      "geography",
      "sector",
      "source_family",
      "visual_type"
    ],
    "concentration_threshold": 0.34,
    "decision_window_id": "2026-07-15",
    "dimensions": {
      "content_mode": {
        "concentrated_values": [
          "numeric_official_record"
        ],
        "counts": {
          "numeric_official_record": 2,
          "numeric_official_release": 1,
          "official_filing_metadata": 1,
          "official_rule_text": 1
        },
        "distinct_values": 4,
        "is_concentrated": true,
        "max_share": 0.4,
        "shares": {
          "numeric_official_record": 0.4,
          "numeric_official_release": 0.2,
          "official_filing_metadata": 0.2,
          "official_rule_text": 0.2
        }
      },
      "domain_family": {
        "concentrated_values": [
          "rates_or_credit"
        ],
        "counts": {
          "economic_release": 1,
          "rates_or_credit": 2,
          "regulation_or_law": 1,
          "us_equities_or_big_tech": 1
        },
        "distinct_values": 4,
        "is_concentrated": true,
        "max_share": 0.4,
        "shares": {
          "economic_release": 0.2,
          "rates_or_credit": 0.4,
          "regulation_or_law": 0.2,
          "us_equities_or_big_tech": 0.2
        }
      },
      "entities": {
        "concentrated_values": [],
        "counts": {
          "Apple Inc.": 1,
          "CFPB": 1,
          "CFTC": 1,
          "FDIC": 1,
          "FHFA": 1,
          "NCUA": 1,
          "OCC": 1,
          "SEC": 1,
          "U.S. Department of the Treasury": 3
        },
        "distinct_values": 9,
        "is_concentrated": false,
        "max_share": 0.272727,
        "shares": {
          "Apple Inc.": 0.090909,
          "CFPB": 0.090909,
          "CFTC": 0.090909,
          "FDIC": 0.090909,
          "FHFA": 0.090909,
          "NCUA": 0.090909,
          "OCC": 0.090909,
          "SEC": 0.090909,
          "U.S. Department of the Treasury": 0.272727
        }
      },
      "geography": {
        "concentrated_values": [
          "US"
        ],
        "counts": {
          "US": 5
        },
        "distinct_values": 1,
        "is_concentrated": true,
        "max_share": 1.0,
        "shares": {
          "US": 1.0
        }
      },
      "sector": {
        "concentrated_values": [
          "government_bonds"
        ],
        "counts": {
          "financial_regulation": 1,
          "government_bonds": 3,
          "information_technology": 1
        },
        "distinct_values": 3,
        "is_concentrated": true,
        "max_share": 0.6,
        "shares": {
          "financial_regulation": 0.2,
          "government_bonds": 0.6,
          "information_technology": 0.2
        }
      },
      "source_family": {
        "concentrated_values": [
          "story_scoped_publication_evidence_v1"
        ],
        "counts": {
          "nonnumeric_story_scoped_publication_evidence_v1": 1,
          "story_scoped_publication_evidence_v1": 4
        },
        "distinct_values": 2,
        "is_concentrated": true,
        "max_share": 0.8,
        "shares": {
          "nonnumeric_story_scoped_publication_evidence_v1": 0.2,
          "story_scoped_publication_evidence_v1": 0.8
        }
      },
      "visual_type": {
        "concentrated_values": [
          "chart_and_document_excerpt",
          "text_only"
        ],
        "counts": {
          "chart_and_document_excerpt": 3,
          "text_only": 2
        },
        "distinct_values": 2,
        "is_concentrated": true,
        "max_share": 0.6,
        "shares": {
          "chart_and_document_excerpt": 0.6,
          "text_only": 0.4
        }
      }
    },
    "diversity_never_forces_filler": true,
    "excluded_ids": [
      "case-capital-chronicle-duplicate-replay",
      "case-commodity-visual-rights-blocked",
      "case-economic-release-federal-register",
      "case-geopolitics-ofac-context-only",
      "case-sector-usgs-ridgecrest"
    ],
    "exclusion_reasons": {
      "case-capital-chronicle-duplicate-replay": "DUPLICATE_OR_LOW_DELTA",
      "case-commodity-visual-rights-blocked": "VISUAL_RIGHTS_BLOCKED",
      "case-economic-release-federal-register": "EVIDENCE_BLOCKED",
      "case-geopolitics-ofac-context-only": "PERMISSION_BLOCKED",
      "case-sector-usgs-ridgecrest": "HISTORICAL_NOT_CURRENT"
    },
    "hard_gates_remain_authoritative": true,
    "historical_dates_preserved": true,
    "history_window_days": 90,
    "history_window_end_utc": "2026-07-15T00:00:00Z",
    "history_window_start_utc": "2026-04-16T00:00:00Z",
    "included_current_candidate_ids": [
      "case-economic-release-ust-newsroom",
      "case-rates-ust-curve",
      "case-regulation-joint-rule",
      "case-us-equities-apple-10q"
    ],
    "included_prior_selected_ids": [
      "history-us-treasury-curve-2026-07-13"
    ],
    "presented_as_current_news": false,
    "report_id": "portfolio-rolling-2026-07-15",
    "report_label": "rolling",
    "report_logical_hash": "bd0cdad8cd9e1140a7dfb84891aefd364264863fad641517e0dc85cb166071bf",
    "schema_version": "contentops.core_v0_portfolio_windows.v1",
    "window_end_utc": "2026-07-15T22:30:00Z",
    "window_start_utc": "2026-05-01T00:00:00Z"
  },
  "pre_production_eligible_case_ids": [
    "case-economic-release-ust-newsroom",
    "case-politics-fomc-minutes",
    "case-rates-ust-curve",
    "case-regulation-joint-rule",
    "case-us-equities-apple-10q"
  ],
  "provider_call_performed": false,
  "public_write_authority": false,
  "public_write_performed": false,
  "publication_authority": false,
  "replay_verification": {
    "all_replays_valid": true,
    "work_items_replayed": 10
  },
  "review_engine": "editorial_review_orchestrator_v2.run_editorial_review",
  "rolling_report_logical_hash_used_by_selection": "084f26cafafe256be53792d5d778e9d2b825c994d61e3feb95015466866c6cb1",
  "scheduler_or_outbox_action_performed": false,
  "schema_version": "contentops.core_v0_cohort_shadow_run.v1",
  "shadow_readback": {
    "destinations_contacted": [],
    "public_objects_created": 0,
    "public_urls": [],
    "readback_kind": "SHADOW_SIMULATED_NO_PUBLIC_OBJECT"
  },
  "task_label": "TASK_CONTENTOPS_CORE_V0_DIVERSITY_SEO_IMAGE_AND_CHART_CLOSURE_V1",
  "tier1_destination_count": 9,
  "tier1_destinations": [
    "substack_newsletter",
    "linkedin",
    "x_twitter",
    "facebook_page",
    "telegram",
    "youtube_community",
    "discord",
    "instagram_business",
    "threads"
  ],
  "upstream_write_performed": false
} as const;

export type CoreV0CohortSnapshot = typeof coreV0CohortSnapshot;
