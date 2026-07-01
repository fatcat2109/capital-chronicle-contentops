// V6 Manual Distribution Evidence Registry adapter.
// Generated from committed fixture-only registry packet; no network/env/browser access.

export const manualDistributionEvidenceRegistry = {
  "schema_version": "6.0.0",
  "registry_kind": "manual_distribution_evidence_registry_v0",
  "registry_status": "fixture_manual_operator_supplied_only",
  "platforms": [
    {
      "platform": "substack",
      "platform_label": "Substack",
      "lane_status": "fixture_manual_operator_supplied",
      "canonical_ui_label": "Substack manual publication evidence",
      "source_packets": {
        "export": {
          "packet_id": "substack_manual_export_e556b07116d81110",
          "hash": "e556b07116d81110da7f8b96f5e5d39b80d65ce16c0c190eb51cdc9fdbd1f335",
          "source_path": "docs/automation/V6_SUBSTACK_MANUAL_EXPORT_ARTICLE_STUDIO/sample_substack_manual_export_article_studio_packet.json"
        },
        "approval": {
          "packet_id": "substack_manual_approval_export_evidence_ba20cf65f42da369",
          "hash": "ba20cf65f42da3691a30690fc90be7f09ac0b446ced30920a5f489595d80ffb8",
          "source_path": "docs/automation/V6_SUBSTACK_MANUAL_APPROVAL_EXPORT_EVIDENCE/sample_substack_manual_approval_export_evidence_packet.json"
        },
        "handoff": {
          "packet_id": "substack_manual_export_operator_handoff_e1b56c301ad76877",
          "hash": "e1b56c301ad768777b1478a4b3f334e1b92bfb4b923535cbebc1b50b78cf13f6",
          "source_path": "docs/automation/V6_SUBSTACK_MANUAL_EXPORT_OPERATOR_HANDOFF/sample_substack_manual_export_operator_handoff_packet.json"
        },
        "url": {
          "packet_id": "substack_manual_publication_url_audit_cc4097c256f27c86",
          "hash": "cc4097c256f27c8616ef99d73ea1a142a8a99a13498e8bc5f82a3cbcfa40bd40",
          "source_path": "docs/automation/V6_SUBSTACK_MANUAL_PUBLICATION_URL_AUDIT_IMPORT/sample_substack_manual_publication_url_audit_import_packet.json"
        },
        "metrics": {
          "packet_id": "substack_publication_audit_review_83d3fdcfab6bba6f",
          "hash": "83d3fdcfab6bba6f5502f8a06b78c439ddea7b2d720f0003977c692154456871",
          "source_path": "docs/automation/V6_SUBSTACK_PUBLICATION_AUDIT_REVIEW_METRICS_SUMMARY/sample_substack_publication_audit_review_metrics_summary_packet.json"
        }
      },
      "manual_operator_supplied": true,
      "metric_provenance": "operator_supplied_manual_entry_not_network_verified",
      "url_provenance": "operator_supplied_not_network_verified",
      "blocked_controls": [
        "approve",
        "dispatch",
        "publish",
        "schedule",
        "send"
      ],
      "safety_flags": {
        "api_used": false,
        "network_call_made": false,
        "url_network_verified": false,
        "metrics_network_verified": false,
        "env_value_read_made": false,
        "credential_read_made": false,
        "browser_session_used": false,
        "live_publish_performed_by_contentops": false,
        "enabled_publish_send_dispatch_approve_controls": false
      }
    },
    {
      "platform": "linkedin",
      "platform_label": "LinkedIn",
      "lane_status": "fixture_manual_operator_supplied",
      "canonical_ui_label": "LinkedIn manual publication evidence",
      "source_packets": {
        "export": {
          "packet_id": "linkedin_manual_export_79cc3f65a34689de",
          "hash": "79cc3f65a34689de30155e4bed6764ffb5c947ab300b6399e61d88b30934088e",
          "source_path": "docs/automation/V6_LINKEDIN_MANUAL_EXPORT/sample_linkedin_manual_export_packet.json"
        },
        "approval": {
          "packet_id": "linkedin_manual_approval_export_evidence_6fefc99b74dd9e5b",
          "hash": "6fefc99b74dd9e5b8fd282dbe8361b4ed200be6b66b9112ad2273eb8a3451884",
          "source_path": "docs/automation/V6_LINKEDIN_MANUAL_APPROVAL_EXPORT_EVIDENCE/sample_linkedin_manual_approval_export_evidence_packet.json"
        },
        "handoff": {
          "packet_id": "linkedin_manual_operator_handoff_48edd2fac668bdc2",
          "hash": "48edd2fac668bdc23ff673eca24969c3ead5122499c85882fb121a3092d2b93e",
          "source_path": "docs/automation/V6_LINKEDIN_MANUAL_OPERATOR_HANDOFF/sample_linkedin_manual_operator_handoff_packet.json"
        },
        "url": {
          "packet_id": "linkedin_manual_publication_url_audit_501e7b85a5a3beef",
          "hash": "501e7b85a5a3beef3c7104ab529682cee2a367d7fa5c179717c60652a15185d7",
          "source_path": "docs/automation/V6_LINKEDIN_MANUAL_PUBLICATION_URL_AUDIT_IMPORT/sample_linkedin_manual_publication_url_audit_import_packet.json"
        },
        "metrics": {
          "packet_id": "linkedin_publication_audit_review_b14aa8810b74a9c6",
          "hash": "b14aa8810b74a9c672a2271503b38f92a7747361b8c73c770200143ab7095a3d",
          "source_path": "docs/automation/V6_LINKEDIN_PUBLICATION_AUDIT_REVIEW_METRICS_SUMMARY/sample_linkedin_publication_audit_review_metrics_summary_packet.json"
        }
      },
      "manual_operator_supplied": true,
      "metric_provenance": "operator_supplied_manual_entry_not_network_verified",
      "url_provenance": "operator_supplied_not_network_verified",
      "blocked_controls": [
        "approve",
        "dispatch",
        "publish",
        "schedule",
        "send"
      ],
      "safety_flags": {
        "api_used": false,
        "network_call_made": false,
        "url_network_verified": false,
        "metrics_network_verified": false,
        "env_value_read_made": false,
        "credential_read_made": false,
        "browser_session_used": false,
        "live_publish_performed_by_contentops": false,
        "enabled_publish_send_dispatch_approve_controls": false
      }
    },
    {
      "platform": "x",
      "platform_label": "X",
      "lane_status": "fixture_manual_operator_supplied",
      "canonical_ui_label": "X manual publication evidence",
      "source_packets": {
        "export": {
          "packet_id": "x_manual_export_00705bd0bac1e58a",
          "hash": "00705bd0bac1e58ab8f9ffc61c70b3058fbab81813193640352be6776ffb7067",
          "source_path": "docs/automation/V6_X_MANUAL_EXPORT/sample_x_manual_export_packet.json"
        },
        "approval": {
          "packet_id": "x_manual_approval_export_evidence_029ea52504bc707f",
          "hash": "029ea52504bc707f1ab48d37e36278f885819da229bfb73167046823990c0f01",
          "source_path": "docs/automation/V6_X_MANUAL_APPROVAL_EXPORT_EVIDENCE/sample_x_manual_approval_export_evidence_packet.json"
        },
        "handoff": {
          "packet_id": "x_manual_operator_handoff_fc7bd7206e4bcbac",
          "hash": "fc7bd7206e4bcbac3d9d8e44a4fcfc37dad1240e6084eca50d510ccfbea8c96b",
          "source_path": "docs/automation/V6_X_MANUAL_OPERATOR_HANDOFF/sample_x_manual_operator_handoff_packet.json"
        },
        "url": {
          "packet_id": "x_manual_publication_url_audit_bfa2b9e33779b582",
          "hash": "bfa2b9e33779b5828041826bce3d29f0d0846f125148bfddd05097387cef9aad",
          "source_path": "docs/automation/V6_X_MANUAL_PUBLICATION_URL_AUDIT_IMPORT/sample_x_manual_publication_url_audit_import_packet.json"
        },
        "metrics": {
          "packet_id": "x_publication_audit_review_2417b5a05058d6c0",
          "hash": "2417b5a05058d6c096c417aab27257e5a4a80258c8ccfafdb2cc897458acc705",
          "source_path": "docs/automation/V6_X_PUBLICATION_AUDIT_REVIEW_METRICS_SUMMARY/sample_x_publication_audit_review_metrics_summary_packet.json"
        }
      },
      "manual_operator_supplied": true,
      "metric_provenance": "operator_supplied_manual_entry_not_network_verified",
      "url_provenance": "operator_supplied_not_network_verified",
      "blocked_controls": [
        "approve",
        "dispatch",
        "publish",
        "schedule",
        "send"
      ],
      "safety_flags": {
        "api_used": false,
        "network_call_made": false,
        "url_network_verified": false,
        "metrics_network_verified": false,
        "env_value_read_made": false,
        "credential_read_made": false,
        "browser_session_used": false,
        "live_publish_performed_by_contentops": false,
        "enabled_publish_send_dispatch_approve_controls": false
      }
    }
  ],
  "safety_summary": "No platform API, env, credential, browser session, public URL fetch/scrape, live post, reply, DM, like, repost, quote, schedule, approve, send, publish, or dispatch action.",
  "registry_hash": "7f75feba8ed20f2d98b4ee15aff0f41a4271a76e3634fbec2563d17bc8f66fac",
  "registry_packet_id": "manual_distribution_evidence_registry_7f75feba8ed20f2d"
} as const;

export const manualDistributionRegistryPlatforms = manualDistributionEvidenceRegistry.platforms;


export const manualDistributionRegistryAuditIndex = {
  "schema_version": "6.0.0",
  "audit_index_kind": "manual_distribution_registry_audit_index_v0",
  "registry_packet_id": "manual_distribution_evidence_registry_7f75feba8ed20f2d",
  "registry_hash": "7f75feba8ed20f2d98b4ee15aff0f41a4271a76e3634fbec2563d17bc8f66fac",
  "source_path_audit_packet_id": "manual_distribution_registry_source_path_audit_0a88829f638feac4",
  "source_path_audit_hash": "0a88829f638feac498a669966b6d5b0fc5d83adb1dacb7f16ab93070d868155c",
  "platforms_included": [
    "Substack",
    "LinkedIn",
    "X"
  ],
  "registry_status": "fixture_manual_operator_supplied_only",
  "source_path_audit_status": "passed",
  "all_paths_exist": true,
  "all_packet_ids_match": true,
  "all_hashes_match": true,
  "all_paths_within_docs_automation": true,
  "no_url_like_source_paths": true,
  "registry_readiness_status": "ready_for_manual_operator_review_only",
  "blockers": [
    "live/provider/platform execution disabled",
    "platform API/auth/dispatch readiness is out of scope",
    "approve/send/publish/dispatch/schedule controls remain blocked"
  ],
  "caveats": [
    "fixture/operator-supplied/manual only",
    "public URL reachability is not verified",
    "platform-side state is not proven",
    "operator review is required before any external manual action"
  ],
  "next_manual_operator_action": "review committed registry and audit packets locally; do not dispatch or perform live platform actions from ContentOps",
  "non_readiness_claims": {
    "live_readiness_claimed": false,
    "api_readiness_claimed": false,
    "public_url_verification_claimed": false,
    "platform_auth_readiness_claimed": false,
    "dispatch_readiness_claimed": false
  },
  "network_call_made": false,
  "provider_call_made": false,
  "env_value_read_made": false,
  "credential_read_made": false,
  "browser_session_used": false,
  "public_url_fetch_made": false,
  "live_publish_performed_by_contentops": false,
  "enabled_publish_send_dispatch_approve_controls": false,
  "exact_payload_hash": "b968984b920bbf93edef7941ab3c93f229db393f6be7bcf0025a713b82cc5477",
  "audit_index_packet_id": "manual_distribution_registry_audit_index_b968984b920bbf93"
} as const;
