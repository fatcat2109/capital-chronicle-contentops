// V6 Substack manual export article studio adapter.
// Static fixture only. No network, no credentials, no storage, no publish.

export const substackManualExportArticleStudioPacket = {
  "approval_status": "pending",
  "article_body_markdown": "# Capital Chronicle Educational Briefing: Evaluate historical volatility in macro calendar commentaries\n\n_Process-led analysis tailored for general_financial_education_\n\n## Thesis\nMethodological transparency and rigorous historical context are essential when reviewing Evaluate historical volatility in macro calendar commentaries.\n\n## Briefing\nThis briefing grounds our editorial desk's approach to Evaluate historical volatility in macro calendar commentaries. By focusing on the Focus on data transparency, process, and methodology over trading recommendations, we analyze historical patterns without offering directional investment advice.\n\n## Methodology and Source Review\nWe review the sources provided: Macro volatility series database release v1, Fed calendar notes 2026. A key limitation of historical macro data is lag and revision. Operators must verify primary sources before documenting findings.\n\n## Historical Context and Range Analysis\nStatistical ranges from prior cycles provide a benchmark. When volatility spikes, it is critical to separate market noise from structural policy shifts.\n\n## Operator conclusion\nA disciplined operator relies on verified context, explicit assumptions, and clear disclaimers to ensure community integrity under V6_EDUCATIONAL_DISCLAIMER.\n\n---\nManual copy only. Substack API not used. Live publish disabled. No runtime proof.",
  "article_subtitle": "Process-led analysis tailored for general_financial_education",
  "article_title": "Capital Chronicle Educational Briefing: Evaluate historical volatility in macro calendar commentaries",
  "blockers": [
    "live_publish_disabled",
    "operator_approval_pending"
  ],
  "browser_session_used": false,
  "canonical_slug_candidate": "evaluate-historical-volatility-in-macro-calendar-commentaries",
  "env_lines_serialized": false,
  "exact_payload_hash": "e556b07116d81110da7f8b96f5e5d39b80d65ce16c0c190eb51cdc9fdbd1f335",
  "export_packet_id": "substack_manual_export_e556b07116d81110",
  "export_status": "ready_for_manual_review",
  "grounding_state": {
    "no_claims_of_live_public_publication": true,
    "no_fabricated_market_numbers": true,
    "no_invented_citations": true,
    "no_invented_urls": true,
    "required_human_review_items": [
      "Verify H.15 raw series",
      "Confirm risk disclaimer presence"
    ]
  },
  "hash_algorithm": "sha256_json_v6",
  "live_publish_allowed": false,
  "live_publish_performed": false,
  "manual_copy_payload": {
    "body_markdown": "# Capital Chronicle Educational Briefing: Evaluate historical volatility in macro calendar commentaries\n\n_Process-led analysis tailored for general_financial_education_\n\n## Thesis\nMethodological transparency and rigorous historical context are essential when reviewing Evaluate historical volatility in macro calendar commentaries.\n\n## Briefing\nThis briefing grounds our editorial desk's approach to Evaluate historical volatility in macro calendar commentaries. By focusing on the Focus on data transparency, process, and methodology over trading recommendations, we analyze historical patterns without offering directional investment advice.\n\n## Methodology and Source Review\nWe review the sources provided: Macro volatility series database release v1, Fed calendar notes 2026. A key limitation of historical macro data is lag and revision. Operators must verify primary sources before documenting findings.\n\n## Historical Context and Range Analysis\nStatistical ranges from prior cycles provide a benchmark. When volatility spikes, it is critical to separate market noise from structural policy shifts.\n\n## Operator conclusion\nA disciplined operator relies on verified context, explicit assumptions, and clear disclaimers to ensure community integrity under V6_EDUCATIONAL_DISCLAIMER.\n\n---\nManual copy only. Substack API not used. Live publish disabled. No runtime proof.",
    "copy_mode": "manual copy only",
    "operator_instructions": "Review in V5, then manually copy into Substack only if an operator separately approves outside this packet.",
    "safety_labels": [
      "sample_fixture_only",
      "manual copy only",
      "Substack API not used",
      "live publish disabled",
      "no runtime proof"
    ],
    "seo_description": "An educational briefing analyzing Evaluate historical volatility in macro calendar commentaries under the editorial angle: Focus on data transparency, process, and methodology over trading recommendations.",
    "seo_title": "Chronicle Watchlist: Evaluate historical volatility in macro calendar commentaries",
    "slug_candidate": "evaluate-historical-volatility-in-macro-calendar-commentaries",
    "subtitle": "Process-led analysis tailored for general_financial_education",
    "target": "substack_manual_copy",
    "title": "Capital Chronicle Educational Briefing: Evaluate historical volatility in macro calendar commentaries"
  },
  "network_call_made": false,
  "provider_call_made": false,
  "raw_secret_values_serialized": false,
  "recommended_next_task": "TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_APPROVAL_AND_EXPORT_EVIDENCE_HARDENING_V0",
  "sample_scope": "sample_fixture_only",
  "schema_version": "6.0.0",
  "seo_description": "An educational briefing analyzing Evaluate historical volatility in macro calendar commentaries under the editorial angle: Focus on data transparency, process, and methodology over trading recommendations.",
  "seo_title": "Chronicle Watchlist: Evaluate historical volatility in macro calendar commentaries",
  "source_article_packet_id": "article_engine_packet_d4a5afd3ecf03b1b",
  "source_canonical_hash": "d4a5afd3ecf03b1b93caf5b9dbd204d93eb80237eb8d368c9eea24680fabe44e",
  "task_label": "TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_EXPORT_AND_ARTICLE_STUDIO_ON_CANONICAL_V5_DASHBOARD_HEAVY_BATCH_V0",
  "warnings": [
    "sample_fixture_only",
    "manual_copy_only_no_substack_api",
    "no_runtime_proof"
  ]
} as const;

export const substackManualExportSafetyLabels = substackManualExportArticleStudioPacket.manual_copy_payload.safety_labels;


export const substackManualApprovalExportEvidencePacket = {
  "approval_export_evidence_hash": "ba20cf65f42da3691a30690fc90be7f09ac0b446ced30920a5f489595d80ffb8",
  "approval_export_evidence_packet_id": "substack_manual_approval_export_evidence_ba20cf65f42da369",
  "approval_status": "pending",
  "blocked_controls": [
    "approve",
    "send",
    "publish",
    "dispatch"
  ],
  "browser_session_used": false,
  "credential_read_made": false,
  "enabled_publish_send_dispatch_approve_controls": false,
  "env_value_read_made": false,
  "evidence_cards": [
    {
      "card_id": "article_source_packet",
      "card_type": "article_source_packet",
      "display_status": "bound",
      "hash": "d4a5afd3ecf03b1b93caf5b9dbd204d93eb80237eb8d368c9eea24680fabe44e",
      "source_id": "article_engine_packet_d4a5afd3ecf03b1b"
    },
    {
      "card_id": "substack_export_packet",
      "card_type": "substack_export_packet",
      "display_status": "bound",
      "hash": "e556b07116d81110da7f8b96f5e5d39b80d65ce16c0c190eb51cdc9fdbd1f335",
      "source_id": "substack_manual_export_e556b07116d81110"
    },
    {
      "card_id": "approval_checkpoint",
      "card_type": "approval_checkpoint",
      "display_status": "pending_review",
      "hash": "e556b07116d81110da7f8b96f5e5d39b80d65ce16c0c190eb51cdc9fdbd1f335",
      "source_id": "operator_review_status"
    },
    {
      "card_id": "manual_copy_checklist",
      "card_type": "manual_copy_checklist",
      "display_status": "ready_for_manual_copy",
      "hash": "50ab1ffc89c2f44e34e1bd8e73ff716af1a17449b59f4316cd49e43c961f690e",
      "source_id": "manual_copy_payload"
    },
    {
      "card_id": "blocked_live_publish_state",
      "card_type": "blocked_live_publish_state",
      "display_status": "blocked",
      "hash": "b654e7a930df0af32c0f4a9e5b0da9b8275053d0d2272002e4cd7e15b023f793",
      "source_id": "live_publish_allowed=false"
    }
  ],
  "exact_payload_hash": "e556b07116d81110da7f8b96f5e5d39b80d65ce16c0c190eb51cdc9fdbd1f335",
  "hash_algorithm": "sha256_json_v6",
  "live_publish_allowed": false,
  "live_publish_performed": false,
  "manual_copy_checklist": [
    {
      "check_id": "manual_copy_payload_present",
      "label": "Manual copy payload reviewed in V5",
      "required": true,
      "status": "pending_review"
    },
    {
      "check_id": "operator_confirms_no_live_publish",
      "label": "Operator confirms no publish/send/dispatch action is enabled",
      "required": true,
      "status": "pending_review"
    },
    {
      "check_id": "operator_confirms_substack_api_absent",
      "label": "Operator confirms Substack API was not used",
      "required": true,
      "status": "pending_review"
    },
    {
      "check_id": "operator_confirms_hash_match",
      "label": "Operator confirms exact payload hash before manual copy",
      "required": true,
      "status": "pending_review"
    }
  ],
  "manual_export_status": "ready_for_manual_copy",
  "network_call_made": false,
  "operator_review_proof": "pending operator review; deterministic fixture only; no runtime proof",
  "operator_review_status": "pending_review",
  "provider_call_made": false,
  "sample_scope": "sample_fixture_only",
  "schema_version": "6.0.0",
  "source_article_packet_id": "article_engine_packet_d4a5afd3ecf03b1b",
  "source_canonical_hash": "d4a5afd3ecf03b1b93caf5b9dbd204d93eb80237eb8d368c9eea24680fabe44e",
  "source_export_packet_id": "substack_manual_export_e556b07116d81110",
  "substack_api_used": false,
  "task_label": "TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_APPROVAL_AND_EXPORT_EVIDENCE_HARDENING_V0",
  "warnings": [
    "sample_fixture_only",
    "manual_copy_only_no_substack_api",
    "live_publish_disabled",
    "operator_review_pending"
  ]
} as const;

export const substackManualExportOperatorHandoffPacket = {
  "approval_export_evidence_hash": "ba20cf65f42da3691a30690fc90be7f09ac0b446ced30920a5f489595d80ffb8",
  "approval_export_evidence_packet_id": "substack_manual_approval_export_evidence_ba20cf65f42da369",
  "approval_status": "pending",
  "article_title": "Capital Chronicle Educational Briefing: Evaluate historical volatility in macro calendar commentaries",
  "blocked_controls": [
    "approve",
    "send",
    "publish",
    "dispatch",
    "schedule"
  ],
  "blockers": [
    "operator_approval_pending",
    "live_publish_disabled",
    "manual_copy_only",
    "substack_api_disabled"
  ],
  "browser_session_used": false,
  "credential_read_made": false,
  "enabled_publish_send_dispatch_approve_controls": false,
  "env_value_read_made": false,
  "evidence_cards": [
    {
      "card_id": "canonical_article_source",
      "card_type": "canonical_article_source",
      "display_status": "bound",
      "hash": "d4a5afd3ecf03b1b93caf5b9dbd204d93eb80237eb8d368c9eea24680fabe44e",
      "source_id": "article_engine_packet_d4a5afd3ecf03b1b"
    },
    {
      "card_id": "manual_export_payload",
      "card_type": "manual_export_payload",
      "display_status": "bound",
      "hash": "e556b07116d81110da7f8b96f5e5d39b80d65ce16c0c190eb51cdc9fdbd1f335",
      "source_id": "substack_manual_export_e556b07116d81110"
    },
    {
      "card_id": "approval_export_evidence_packet",
      "card_type": "approval_export_evidence_packet",
      "display_status": "bound",
      "hash": "ba20cf65f42da3691a30690fc90be7f09ac0b446ced30920a5f489595d80ffb8",
      "source_id": "substack_manual_approval_export_evidence_ba20cf65f42da369"
    },
    {
      "card_id": "manual_copy_checklist",
      "card_type": "manual_copy_checklist",
      "display_status": "pending_review",
      "hash": "b66662531829b372797e2c0327104625cac7e582eb96c8dc6f74e6c7a8b54a28",
      "source_id": "operator_handoff_checklist"
    },
    {
      "card_id": "blocked_live_publish_state",
      "card_type": "blocked_live_publish_state",
      "display_status": "blocked",
      "hash": "b654e7a930df0af32c0f4a9e5b0da9b8275053d0d2272002e4cd7e15b023f793",
      "source_id": "live_publish_allowed=false"
    },
    {
      "card_id": "operator_handoff_packet",
      "card_type": "operator_handoff_packet",
      "display_status": "ready_for_manual_review",
      "hash": "91a85172a22da6c50971f36bef61dc7e6b197f870c098383802afb247126364c",
      "source_id": "operator_handoff"
    }
  ],
  "exact_payload_hash": "6026312f893feba98fd01a88bf316bd94dd58bad23e3a5ef29abd6fcf864714a",
  "hash_algorithm": "sha256_json_v6",
  "live_publish_allowed": false,
  "live_publish_performed": false,
  "manual_copy_checklist": [
    {
      "check_id": "confirm_article_source",
      "label": "Confirm canonical article source packet and hash",
      "required": true,
      "status": "pending_review"
    },
    {
      "check_id": "confirm_export_payload",
      "label": "Confirm Substack manual export payload hash before copy",
      "required": true,
      "status": "pending_review"
    },
    {
      "check_id": "confirm_approval_evidence",
      "label": "Confirm approval/export evidence packet remains pending",
      "required": true,
      "status": "pending_review"
    },
    {
      "check_id": "confirm_manual_copy_only",
      "label": "Confirm manual copy only; no Substack API, publish, send, dispatch, or scheduler",
      "required": true,
      "status": "pending_review"
    }
  ],
  "manual_copy_only": true,
  "manual_copy_payload": {
    "body_markdown": "# Capital Chronicle Educational Briefing: Evaluate historical volatility in macro calendar commentaries\n\n_Process-led analysis tailored for general_financial_education_\n\n## Thesis\nMethodological transparency and rigorous historical context are essential when reviewing Evaluate historical volatility in macro calendar commentaries.\n\n## Briefing\nThis briefing grounds our editorial desk's approach to Evaluate historical volatility in macro calendar commentaries. By focusing on the Focus on data transparency, process, and methodology over trading recommendations, we analyze historical patterns without offering directional investment advice.\n\n## Methodology and Source Review\nWe review the sources provided: Macro volatility series database release v1, Fed calendar notes 2026. A key limitation of historical macro data is lag and revision. Operators must verify primary sources before documenting findings.\n\n## Historical Context and Range Analysis\nStatistical ranges from prior cycles provide a benchmark. When volatility spikes, it is critical to separate market noise from structural policy shifts.\n\n## Operator conclusion\nA disciplined operator relies on verified context, explicit assumptions, and clear disclaimers to ensure community integrity under V6_EDUCATIONAL_DISCLAIMER.\n\n---\nManual copy only. Substack API not used. Live publish disabled. No runtime proof.",
    "copy_mode": "manual copy only",
    "operator_instructions": "Review in V5, then manually copy into Substack only if an operator separately approves outside this packet.",
    "safety_labels": [
      "sample_fixture_only",
      "manual copy only",
      "Substack API not used",
      "live publish disabled",
      "no runtime proof"
    ],
    "seo_description": "An educational briefing analyzing Evaluate historical volatility in macro calendar commentaries under the editorial angle: Focus on data transparency, process, and methodology over trading recommendations.",
    "seo_title": "Chronicle Watchlist: Evaluate historical volatility in macro calendar commentaries",
    "slug_candidate": "evaluate-historical-volatility-in-macro-calendar-commentaries",
    "subtitle": "Process-led analysis tailored for general_financial_education",
    "target": "substack_manual_copy",
    "title": "Capital Chronicle Educational Briefing: Evaluate historical volatility in macro calendar commentaries"
  },
  "network_call_made": false,
  "operator_handoff_hash": "e1b56c301ad768777b1478a4b3f334e1b92bfb4b923535cbebc1b50b78cf13f6",
  "operator_handoff_packet_id": "substack_manual_export_operator_handoff_e1b56c301ad76877",
  "operator_handoff_status": "ready_for_manual_review",
  "operator_instructions": [
    "Open canonical V5 Manual Export, Approval Queue, and Evidence Vault views only.",
    "Compare article, export, approval/export evidence, and handoff hashes before manual copy.",
    "If separate human approval is granted outside this packet, manually copy the payload into Substack outside ContentOps.",
    "Do not use Substack API, live publish, dispatch, scheduler, provider calls, env values, credentials, browser sessions, cookies, localStorage, or tokens."
  ],
  "provider_call_made": false,
  "recommended_next_task": "TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_EXPORT_OPERATOR_HANDOFF_BROWSER_QA_OR_RELEASE_REVIEW_V0",
  "sample_scope": "sample_fixture_only",
  "schema_version": "6.0.0",
  "source_article_hash": "d4a5afd3ecf03b1b93caf5b9dbd204d93eb80237eb8d368c9eea24680fabe44e",
  "source_article_packet_id": "article_engine_packet_d4a5afd3ecf03b1b",
  "source_export_packet_id": "substack_manual_export_e556b07116d81110",
  "source_export_payload_hash": "e556b07116d81110da7f8b96f5e5d39b80d65ce16c0c190eb51cdc9fdbd1f335",
  "substack_api_used": false,
  "task_label": "TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_EXPORT_OPERATOR_HANDOFF_PACKET_V0",
  "warnings": [
    "sample_fixture_only",
    "manual_copy_only_no_substack_api",
    "live_publish_disabled",
    "operator_handoff_pending_review"
  ]
} as const;

export const substackManualPublicationUrlAuditImportPacket = {
  "approval_export_evidence_hash": "ba20cf65f42da3691a30690fc90be7f09ac0b446ced30920a5f489595d80ffb8",
  "approval_export_evidence_packet_id": "substack_manual_approval_export_evidence_ba20cf65f42da369",
  "blocked_controls": [
    "approve",
    "send",
    "publish",
    "dispatch",
    "schedule"
  ],
  "browser_session_used": false,
  "credential_read_made": false,
  "enabled_publish_send_dispatch_approve_controls": false,
  "env_value_read_made": false,
  "evidence_cards": [
    {
      "card_id": "operator_handoff_packet",
      "card_type": "operator_handoff_packet",
      "display_status": "bound",
      "hash": "e1b56c301ad768777b1478a4b3f334e1b92bfb4b923535cbebc1b50b78cf13f6",
      "source_id": "substack_manual_export_operator_handoff_e1b56c301ad76877"
    },
    {
      "card_id": "manual_export_payload",
      "card_type": "manual_export_payload",
      "display_status": "bound",
      "hash": "e556b07116d81110da7f8b96f5e5d39b80d65ce16c0c190eb51cdc9fdbd1f335",
      "source_id": "substack_manual_export_e556b07116d81110"
    },
    {
      "card_id": "approval_export_evidence_packet",
      "card_type": "approval_export_evidence_packet",
      "display_status": "bound",
      "hash": "ba20cf65f42da3691a30690fc90be7f09ac0b446ced30920a5f489595d80ffb8",
      "source_id": "substack_manual_approval_export_evidence_ba20cf65f42da369"
    },
    {
      "card_id": "canonical_article_source",
      "card_type": "canonical_article_source",
      "display_status": "bound",
      "hash": "d4a5afd3ecf03b1b93caf5b9dbd204d93eb80237eb8d368c9eea24680fabe44e",
      "source_id": "article_engine_packet_d4a5afd3ecf03b1b"
    },
    {
      "card_id": "operator_supplied_publication_url",
      "card_type": "operator_supplied_publication_url",
      "display_status": "operator_supplied_not_network_verified",
      "hash": "52a0c3b6e2d461acdc84556138ab533d5825fa571e69ee625480a17b58f6f3da",
      "source_id": "operator_supplied_publication_url"
    }
  ],
  "exact_payload_hash": "6026312f893feba98fd01a88bf316bd94dd58bad23e3a5ef29abd6fcf864714a",
  "hash_algorithm": "sha256_json_v6",
  "live_publish_performed_by_contentops": false,
  "manual_publication_claim_operator_supplied": true,
  "network_call_made": false,
  "operator_handoff_hash": "e1b56c301ad768777b1478a4b3f334e1b92bfb4b923535cbebc1b50b78cf13f6",
  "operator_handoff_packet_id": "substack_manual_export_operator_handoff_e1b56c301ad76877",
  "operator_review_status": "pending_review",
  "operator_supplied_publication_platform": "substack",
  "operator_supplied_publication_status": "manually_published_outside_contentops",
  "operator_supplied_publication_timestamp": "2026-07-01T05:00:00Z",
  "operator_supplied_publication_url": "https://capitalchronicle.substack.com/p/evaluate-historical-volatility-in-macro-calendar-commentaries",
  "operator_supplied_publication_url_hash": "52a0c3b6e2d461acdc84556138ab533d5825fa571e69ee625480a17b58f6f3da",
  "operator_supplied_url_verification_status": "operator_supplied_not_network_verified",
  "provider_call_made": false,
  "publication_audit_status": "manual_url_imported_pending_operator_review",
  "publication_url_audit_hash": "cc4097c256f27c8616ef99d73ea1a142a8a99a13498e8bc5f82a3cbcfa40bd40",
  "publication_url_audit_packet_id": "substack_manual_publication_url_audit_cc4097c256f27c86",
  "recommended_next_task": "TASK_CONTENTOPS_V6_SUBSTACK_PUBLICATION_AUDIT_REVIEW_OR_METRICS_SUMMARY_V0",
  "sample_scope": "sample_fixture_only",
  "schema_version": "6.0.0",
  "source_article_hash": "d4a5afd3ecf03b1b93caf5b9dbd204d93eb80237eb8d368c9eea24680fabe44e",
  "source_article_packet_id": "article_engine_packet_d4a5afd3ecf03b1b",
  "source_export_packet_id": "substack_manual_export_e556b07116d81110",
  "source_export_payload_hash": "e556b07116d81110da7f8b96f5e5d39b80d65ce16c0c190eb51cdc9fdbd1f335",
  "substack_api_used": false,
  "task_label": "TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_PUBLICATION_URL_AUDIT_IMPORT_LANE_V0",
  "url_network_verified": false,
  "warnings": [
    "sample_fixture_only",
    "operator_supplied_url_not_network_verified",
    "no_url_fetch_no_scrape",
    "manual_publication_claim_not_contentops_publish"
  ]
} as const;
