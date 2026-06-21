import { LaneCArtifactIntakeValidationPacket } from '../types';

export const laneCArtifactIntakePacket: LaneCArtifactIntakeValidationPacket = {
  artifact_candidate_count: 3,
  blocked_reasons: [
    "missing_manual_review",
    "stale_or_missing_freshness_metadata",
    "degraded_proxy_or_unverified_lineage"
  ],
  candidates: [
    {
      artifact_family: "financial_metrics",
      blocked_reasons: [
        "missing_manual_review"
      ],
      candidate_id: "valid_shape_but_blocked_missing_manual_review",
      citation_refs: [
        "source:bloomberg",
        "ref:fed_reserve"
      ],
      dispatch_ready: false,
      dqr_status: "unresolved_not_cleared",
      freshness_status: "fresh",
      limitation_notes: [
        "Valid schema, but pending human operator verification gate."
      ],
      lineage_ref: "commit:a1b2c3d4",
      local_artifact_ref: "fixtures/lane_c/artifact_valid_shape.json",
      missing_or_degraded_labels: [],
      public_postable: false,
      readiness_status: "ready_for_review_only",
      review_required: true,
      source_system: "capital_chronicle_future_artifact"
    },
    {
      artifact_family: "historical_reconciliation",
      blocked_reasons: [
        "stale_or_missing_freshness_metadata"
      ],
      candidate_id: "stale_or_missing_freshness_metadata",
      citation_refs: [],
      dispatch_ready: false,
      dqr_status: "unresolved_not_cleared",
      freshness_status: "stale_or_missing",
      limitation_notes: [
        "Stale freshness metadata. Time-to-live expired."
      ],
      lineage_ref: "commit:e5f6g7h8",
      local_artifact_ref: "fixtures/lane_c/artifact_stale_metadata.json",
      missing_or_degraded_labels: [
        "stale_metadata"
      ],
      public_postable: false,
      readiness_status: "blocked",
      review_required: true,
      source_system: "capital_chronicle_future_artifact"
    },
    {
      artifact_family: "external_aggregate",
      blocked_reasons: [
        "degraded_proxy_or_unverified_lineage"
      ],
      candidate_id: "degraded_proxy_or_unverified_lineage",
      citation_refs: [
        "source:unverified_proxy"
      ],
      dispatch_ready: false,
      dqr_status: "degraded",
      freshness_status: "fresh",
      limitation_notes: [
        "Degraded proxy data and missing cryptographic lineage proof."
      ],
      lineage_ref: "unverified",
      local_artifact_ref: "fixtures/lane_c/artifact_unverified_lineage.json",
      missing_or_degraded_labels: [
        "degraded_proxy",
        "unverified_lineage"
      ],
      public_postable: false,
      readiness_status: "blocked",
      review_required: true,
      source_system: "capital_chronicle_future_artifact"
    }
  ],
  generated_at_epoch: 0,
  hash_algorithm: "sha256",
  local_only_classification: "local_only_review",
  matrix_version: "0175AF_LANE_C_ARTIFACT_INTAKE_VALIDATION_PIPELINE_V1",
  missing_proofs: [
    "manual_operator_signoff",
    "freshness_handshake",
    "lineage_cryptographic_proof"
  ],
  next_required_gate: "lane_c_manual_operator_review",
  packet_hash: "2b95c8fd228af5f2704d44abb24c5827babc526b954d444624a61df75f7379d5",
  safety_flags: {
    autonomous_posting: false,
    credential_read: false,
    dispatch_ready: false,
    dqr_cleared: false,
    env_read: false,
    ingestion_repo_mutated: false,
    lane_c_enabled_for_review: true,
    live_ingestion_enabled: false,
    local_only: true,
    network_performed: false,
    platform_api_called: false,
    provider_api_called: false,
    public_postable: false,
    raw_response_logged: false,
    readiness_cleared: false,
    review_only: true,
    secret_output: false
  },
  source_baseline_commit: "c2033904839f33b20d4f9d39f92a01ef981ebf73",
  task_label: "TASK_CONTENTOPS_0175AF_LANE_C_ARTIFACT_INTAKE_VALIDATION_PIPELINE_V0",
  validation_check_count: 16,
  validation_checks: [
    {
      check_id: "artifact_identity_present",
      description: "Verify that artifact identity metadata is present.",
      passed: true
    },
    {
      check_id: "lineage_present",
      description: "Verify that lineage refs are populated.",
      passed: true
    },
    {
      check_id: "freshness_present",
      description: "Verify that freshness metadata is present.",
      passed: true
    },
    {
      check_id: "dqr_not_cleared_by_contentops",
      description: "Enforce that DQR has not been cleared by ContentOps.",
      passed: true
    },
    {
      check_id: "readiness_not_cleared_by_contentops",
      description: "Enforce that readiness state has not been cleared.",
      passed: true
    },
    {
      check_id: "missing_degraded_proxy_labels_preserved",
      description: "Ensure missing/degraded/proxy labels are preserved.",
      passed: true
    },
    {
      check_id: "citation_refs_present",
      description: "Ensure citation references are present.",
      passed: true
    },
    {
      check_id: "limitation_notes_present",
      description: "Ensure limitation notes are present.",
      passed: true
    },
    {
      check_id: "no_fake_market_numbers",
      description: "Ensure no fake market numbers are present.",
      passed: true
    },
    {
      check_id: "no_financial_advice",
      description: "Enforce no financial advice is offered.",
      passed: true
    },
    {
      check_id: "no_signal_language",
      description: "Enforce no signal language is present.",
      passed: true
    },
    {
      check_id: "public_postable_false",
      description: "Ensure public_postable is false.",
      passed: true
    },
    {
      check_id: "dispatch_ready_false",
      description: "Ensure dispatch_ready is false.",
      passed: true
    },
    {
      check_id: "no_ingestion_mutation",
      description: "Enforce no ingestion repository mutation.",
      passed: true
    },
    {
      check_id: "no_env_or_credential_read",
      description: "Verify that no env or credential values were read.",
      passed: true
    },
    {
      check_id: "no_network_or_api_call",
      description: "Verify that no network or API calls were executed.",
      passed: true
    }
  ]
};
