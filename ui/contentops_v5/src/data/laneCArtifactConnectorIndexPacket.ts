import { LaneCArtifactConnectorIndexPacket } from '../types';

export const laneCArtifactConnectorIndexPacket: LaneCArtifactConnectorIndexPacket = {
  blocked_reasons: [
    "artifact_connector_not_live",
    "artifact_connector_not_live",
    "artifact_connector_not_live",
    "artifact_connector_not_live",
    "artifact_connector_not_live",
    "manual_verification_required"
  ],
  connector_families: [
    {
      allowed_consumer_surfaces: [
        "ContentInventory",
        "DraftInspector"
      ],
      allowed_path_pattern: "fixtures/lane_c/connectors/artifact_packet/*.json",
      connector_family: "local_capital_chronicle_artifact_packet",
      connector_id: "local_capital_chronicle_artifact_packet",
      current_status: "blocked_review_only",
      dqr_handling: "preserve_unresolved_not_cleared",
      freshness_requirement: "max_age_seconds: 86400",
      missing_degraded_proxy_label_handling: "preserve_labels_and_warn",
      next_required_gate: "lane_c_artifact_intake_validation",
      prohibited_effects: [
        "no_network",
        "no_live_dispatch",
        "no_repo_mutation"
      ],
      readiness_handling: "enforce_blocked_unless_manual_override",
      required_file_kinds: [
        "json"
      ],
      required_hash_fields: [
        "packet_hash",
        "hash_algorithm"
      ],
      required_identity_fields: [
        "task_label",
        "matrix_version"
      ],
      required_lineage_fields: [
        "source_baseline_commit"
      ]
    },
    {
      allowed_consumer_surfaces: [
        "ContentInventory",
        "DraftInspector"
      ],
      allowed_path_pattern: "fixtures/lane_c/connectors/lineage_manifest/*.json",
      connector_family: "local_capital_chronicle_lineage_manifest",
      connector_id: "local_capital_chronicle_lineage_manifest",
      current_status: "blocked_review_only",
      dqr_handling: "preserve_unresolved_not_cleared",
      freshness_requirement: "max_age_seconds: 86400",
      missing_degraded_proxy_label_handling: "preserve_labels_and_warn",
      next_required_gate: "lane_c_cryptographic_lineage_verification",
      prohibited_effects: [
        "no_network",
        "no_live_dispatch",
        "no_repo_mutation"
      ],
      readiness_handling: "enforce_blocked_unless_manual_override",
      required_file_kinds: [
        "json"
      ],
      required_hash_fields: [
        "packet_hash",
        "hash_algorithm"
      ],
      required_identity_fields: [
        "task_label",
        "matrix_version"
      ],
      required_lineage_fields: [
        "source_baseline_commit"
      ]
    },
    {
      allowed_consumer_surfaces: [
        "ContentInventory",
        "DraftInspector"
      ],
      allowed_path_pattern: "fixtures/lane_c/connectors/dqr_snapshot/*.json",
      connector_family: "local_capital_chronicle_dqr_snapshot",
      connector_id: "local_capital_chronicle_dqr_snapshot",
      current_status: "blocked_review_only",
      dqr_handling: "preserve_unresolved_not_cleared",
      freshness_requirement: "max_age_seconds: 86400",
      missing_degraded_proxy_label_handling: "preserve_labels_and_warn",
      next_required_gate: "lane_c_dqr_gate",
      prohibited_effects: [
        "no_network",
        "no_live_dispatch",
        "no_repo_mutation"
      ],
      readiness_handling: "enforce_blocked_unless_manual_override",
      required_file_kinds: [
        "json"
      ],
      required_hash_fields: [
        "packet_hash",
        "hash_algorithm"
      ],
      required_identity_fields: [
        "task_label",
        "matrix_version"
      ],
      required_lineage_fields: [
        "source_baseline_commit"
      ]
    },
    {
      allowed_consumer_surfaces: [
        "ContentInventory",
        "DraftInspector"
      ],
      allowed_path_pattern: "fixtures/lane_c/connectors/source_health/*.json",
      connector_family: "local_capital_chronicle_source_health_snapshot",
      connector_id: "local_capital_chronicle_source_health_snapshot",
      current_status: "blocked_review_only",
      dqr_handling: "preserve_unresolved_not_cleared",
      freshness_requirement: "max_age_seconds: 86400",
      missing_degraded_proxy_label_handling: "preserve_labels_and_warn",
      next_required_gate: "lane_c_source_health_audit",
      prohibited_effects: [
        "no_network",
        "no_live_dispatch",
        "no_repo_mutation"
      ],
      readiness_handling: "enforce_blocked_unless_manual_override",
      required_file_kinds: [
        "json"
      ],
      required_hash_fields: [
        "packet_hash",
        "hash_algorithm"
      ],
      required_identity_fields: [
        "task_label",
        "matrix_version"
      ],
      required_lineage_fields: [
        "source_baseline_commit"
      ]
    },
    {
      allowed_consumer_surfaces: [
        "ContentInventory",
        "DraftInspector"
      ],
      allowed_path_pattern: "fixtures/lane_c/connectors/forecast_readiness/*.json",
      connector_family: "local_capital_chronicle_forecast_readiness_snapshot",
      connector_id: "local_capital_chronicle_forecast_readiness_snapshot",
      current_status: "blocked_review_only",
      dqr_handling: "preserve_unresolved_not_cleared",
      freshness_requirement: "max_age_seconds: 86400",
      missing_degraded_proxy_label_handling: "preserve_labels_and_warn",
      next_required_gate: "lane_c_forecast_readiness_check",
      prohibited_effects: [
        "no_network",
        "no_live_dispatch",
        "no_repo_mutation"
      ],
      readiness_handling: "enforce_blocked_unless_manual_override",
      required_file_kinds: [
        "json"
      ],
      required_hash_fields: [
        "packet_hash",
        "hash_algorithm"
      ],
      required_identity_fields: [
        "task_label",
        "matrix_version"
      ],
      required_lineage_fields: [
        "source_baseline_commit"
      ]
    },
    {
      allowed_consumer_surfaces: [
        "ContentInventory",
        "DraftInspector"
      ],
      allowed_path_pattern: "fixtures/lane_c/connectors/manual_evidence/*.json",
      connector_family: "local_manual_operator_evidence_packet",
      connector_id: "local_manual_operator_evidence_packet",
      current_status: "manual_only",
      dqr_handling: "preserve_unresolved_not_cleared",
      freshness_requirement: "max_age_seconds: 86400",
      missing_degraded_proxy_label_handling: "preserve_labels_and_warn",
      next_required_gate: "evidence_vault_manual_pilot_audit",
      prohibited_effects: [
        "no_network",
        "no_live_dispatch",
        "no_repo_mutation"
      ],
      readiness_handling: "enforce_blocked_unless_manual_override",
      required_file_kinds: [
        "json",
        "md"
      ],
      required_hash_fields: [
        "packet_hash",
        "hash_algorithm"
      ],
      required_identity_fields: [
        "task_label",
        "matrix_version"
      ],
      required_lineage_fields: [
        "source_baseline_commit"
      ]
    }
  ],
  connector_family_count: 6,
  generated_at_epoch: 0,
  hash_algorithm: "sha256",
  local_only_classification: "local_only_review",
  matrix_version: "0175AG_LANE_C_ARTIFACT_CONNECTOR_INDEX_V1",
  missing_proofs: [
    "cryptographic_manifest_proof",
    "manual_operator_review_proof"
  ],
  next_required_gate: "lane_c_connector_index_operator_signoff",
  packet_hash: "2c5b4a3661adc5b25e2b36a66c8be4bfc349c2fa7359fc1610f158d9a6719ede",
  path_boundaries: [
    {
      allowed_path_pattern: "fixtures/lane_c/connectors/artifact_packet/*.json",
      local_only: true,
      symbolic_only: true
    },
    {
      allowed_path_pattern: "fixtures/lane_c/connectors/lineage_manifest/*.json",
      local_only: true,
      symbolic_only: true
    },
    {
      allowed_path_pattern: "fixtures/lane_c/connectors/dqr_snapshot/*.json",
      local_only: true,
      symbolic_only: true
    },
    {
      allowed_path_pattern: "fixtures/lane_c/connectors/source_health/*.json",
      local_only: true,
      symbolic_only: true
    },
    {
      allowed_path_pattern: "fixtures/lane_c/connectors/forecast_readiness/*.json",
      local_only: true,
      symbolic_only: true
    },
    {
      allowed_path_pattern: "fixtures/lane_c/connectors/manual_evidence/*.json",
      local_only: true,
      symbolic_only: true
    }
  ],
  proof_requirement_count: 6,
  readiness_decisions: [
    {
      blocked_reasons: [
        "artifact_connector_not_live"
      ],
      connector_id: "local_capital_chronicle_artifact_packet",
      decision: "blocked_review_only"
    },
    {
      blocked_reasons: [
        "artifact_connector_not_live"
      ],
      connector_id: "local_capital_chronicle_lineage_manifest",
      decision: "blocked_review_only"
    },
    {
      blocked_reasons: [
        "artifact_connector_not_live"
      ],
      connector_id: "local_capital_chronicle_dqr_snapshot",
      decision: "blocked_review_only"
    },
    {
      blocked_reasons: [
        "artifact_connector_not_live"
      ],
      connector_id: "local_capital_chronicle_source_health_snapshot",
      decision: "blocked_review_only"
    },
    {
      blocked_reasons: [
        "artifact_connector_not_live"
      ],
      connector_id: "local_capital_chronicle_forecast_readiness_snapshot",
      decision: "blocked_review_only"
    },
    {
      blocked_reasons: [
        "manual_verification_required"
      ],
      connector_id: "local_manual_operator_evidence_packet",
      decision: "manual_only"
    }
  ],
  safety_flags: {
    "no_autonomous_posting": true,
    "no_credential_read": true,
    "no_current_state_mutation": true,
    "no_dispatch_ready_promotion": true,
    "no_dqr_clear": true,
    "no_env_read": true,
    "no_fake_market_numbers": true,
    "no_ingestion_repo_mutation": true,
    "no_live_connector_enabled": true,
    "no_network_call": true,
    "no_provider_platform_api_call": true,
    "no_public_postable_promotion": true,
    "no_raw_vendor_redistribution": true,
    "no_readiness_clear": true,
    "no_scheduler": true,
    "no_scraping": true
  },
  source_baseline_commit: "2d9cfa897f78bd510fa24ed876131519f775bc9e",
  task_label: "TASK_CONTENTOPS_0175AG_LANE_C_ARTIFACT_CONNECTOR_INDEX_V0"
};
