// Capital Chronicle ContentOps V5 — Discord operator source + GO phrase intake panel.
// Read-only. No network, storage, credentials, dispatch, webhook validation, or live action.

import {
  discordCredentialPresenceEvidence,
  discordDispatchDecisionReadiness,
  discordDispatchRoutePreview,
  discordDestinationBindingProof,
  discordKillSwitchEvidence,
  discordLivePreflightEvidence,
  discordOperatorInputContract,
  discordOperatorReviewDecisionPacket,
  discordOperatorSourceArtifactFixtureReview,
  discordOperatorSourceGoPhraseIntakePacket,
  discordPreDispatchReadiness,
  discordRedactedOperatorReviewPacket,
  discordReviewOnlyDryRunEnvelopeNormalization,
  normalizedOperatorSourceGoPhraseCandidate,
  operatorGoPhraseEvidence,
  operatorSourceGoPhraseSafetySignature,
} from '../data/discordOperatorSourceGoPhraseIntakeAdapter';
import { Metric, Panel, StatusChip } from '../ui/primitives';

export function DiscordOperatorSourceGoPhraseIntakePanel() {
  const packet = discordOperatorSourceGoPhraseIntakePacket;
  const normalized = normalizedOperatorSourceGoPhraseCandidate;
  const envelope = discordReviewOnlyDryRunEnvelopeNormalization;
  const fixtureReview = discordOperatorSourceArtifactFixtureReview;
  const livePreflight = discordLivePreflightEvidence;
  const inputContract = discordOperatorInputContract;
  const readiness = discordPreDispatchReadiness;
  const redactedReview = discordRedactedOperatorReviewPacket;
  const reviewDecision = discordOperatorReviewDecisionPacket;
  const dispatchDecision = discordDispatchDecisionReadiness;
  const routePreview = discordDispatchRoutePreview;

  return (
    <Panel
      title="V6 Discord operator source + GO phrase intake"
      subtitle={`${packet.task_label} · status: ${packet.intake_status}`}
      actions={<StatusChip status="blocked">{packet.intake_status}</StatusChip>}
    >
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        <Metric label="Intake packet" value={packet.intake_packet_id} status="blocked" />
        <Metric label="Normalized candidate" value={normalized.candidate_id} status="blocked" />
        <Metric label="Source artifact" value={packet.operator_source_artifact_path || 'missing'} status="blocked" />
        <Metric label="Source kind" value={packet.operator_source_artifact_kind} status="blocked" />
        <Metric label="Fixture only" value={String(packet.fixture_only)} status="blocked" />
        <Metric label="Real artifact claimed" value={String(packet.operator_source_artifact_real_claimed)} status="blocked" />
        <Metric label="Real artifact present" value={String(packet.real_operator_artifact_present)} status="blocked" />
        <Metric label="Real intake ready" value={String(packet.real_operator_artifact_intake_ready)} status="blocked" />
        <Metric label="Fixture/real separated" value={String(packet.fixture_vs_real_separation_enforced)} status="verified" />
        <Metric label="GO phrase valid" value={String(packet.operator_go_phrase_valid)} status="blocked" />
        <Metric label="Destination confirmed" value={String(packet.destination_binding_confirmed)} status="blocked" />
        <Metric label="Kill switch active" value={String(packet.kill_switch_active)} status="blocked" />
        <Metric label="Webhook key" value={packet.credential_presence_states.DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK} status="blocked" />
        <Metric label="Channel key" value={packet.credential_presence_states.DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL} status="blocked" />
        <Metric label="Kill-switch key" value={packet.credential_presence_states.CONTENTOPS_LIVE_KILL_SWITCH} status="blocked" />
        <Metric label="Phrase evidence" value={operatorGoPhraseEvidence.phrase_evidence_hash} status="verified" />
        <Metric label="Envelope normalized" value={String(packet.dry_run_envelope_normalization_performed)} status="verified" />
        <Metric label="Envelope hash" value={envelope.dry_run_request_envelope_hash} status="verified" />
        <Metric label="Envelope executable" value={String(envelope.request_envelope_executable)} status="blocked" />
        <Metric label="Destination proof" value={discordDestinationBindingProof.destination_proof_id} status="verified" />
        <Metric label="Kill-switch proof" value={discordKillSwitchEvidence.kill_switch_evidence_id} status="blocked" />
        <Metric label="Credential proof" value={discordCredentialPresenceEvidence.credential_presence_evidence_id} status="blocked" />
        <Metric label="Fixture review" value={fixtureReview.fixture_review_status} status="blocked" />
        <Metric label="Fixture review hash" value={fixtureReview.fixture_review_hash} status="verified" />
        <Metric label="Operator input contract" value={inputContract.operator_input_contract_status} status="blocked" />
        <Metric label="Input contract hash" value={inputContract.operator_input_contract_hash} status="verified" />
        <Metric label="Required inbox" value={inputContract.required_inbox_path} status="blocked" />
        <Metric label="Live preflight" value={livePreflight.live_preflight_status} status="blocked" />
        <Metric label="Live preflight hash" value={livePreflight.live_preflight_hash} status="verified" />
        <Metric label="Redacted review" value={redactedReview.redacted_operator_review_status} status="blocked" />
        <Metric label="Redacted review hash" value={redactedReview.redacted_operator_review_hash} status="verified" />
        <Metric label="Redaction performed" value={String(redactedReview.redaction_performed)} status="verified" />
        <Metric label="Review decision" value={reviewDecision.operator_review_decision_status} status="blocked" />
        <Metric label="Review decision hash" value={reviewDecision.operator_review_decision_hash} status="verified" />
        <Metric label="Decision" value={reviewDecision.decision} status="blocked" />
        <Metric label="Dispatch decision" value={dispatchDecision.dispatch_decision_readiness_status} status="blocked" />
        <Metric label="Dispatch decision hash" value={dispatchDecision.dispatch_decision_readiness_hash} status="verified" />
        <Metric label="Approval route candidate" value={String(dispatchDecision.approval_route_candidate_ready_not_dispatch)} status="blocked" />
        <Metric label="Jim final authority" value={String(dispatchDecision.jim_final_authority_required)} status="blocked" />
        <Metric label="Supervised live edge" value={String(dispatchDecision.supervised_live_edge_required)} status="blocked" />
        <Metric label="Dispatch route preview" value={routePreview.dispatch_route_preview_status} status="blocked" />
        <Metric label="Route class" value={routePreview.route_class} status="blocked" />
        <Metric label="Pre-dispatch readiness" value={readiness.pre_dispatch_readiness_status} status="blocked" />
        <Metric label="Safety hash" value={operatorSourceGoPhraseSafetySignature.safety_signature_hash} status="verified" />
      </div>

      <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted font-mono">
        <div>operator_source_go_phrase_intake_status=blocked</div>
        <div>operator_source_artifact_path={packet.operator_source_artifact_path || 'missing'}</div>
        <div>operator_source_artifact_kind={packet.operator_source_artifact_kind}</div>
        <div>operator_source_artifact_real_claimed={String(packet.operator_source_artifact_real_claimed)}</div>
        <div>non_real_fixture={String(packet.non_real_fixture)}</div>
        <div>fixture_only={String(packet.fixture_only)}</div>
        <div>not_public_postable={String(packet.not_public_postable)}</div>
        <div>real_operator_artifact_present={String(packet.real_operator_artifact_present)}</div>
        <div>real_operator_artifact_intake_ready={String(packet.real_operator_artifact_intake_ready)}</div>
        <div>fixture_vs_real_separation_enforced={String(packet.fixture_vs_real_separation_enforced)}</div>
        <div>operator_go_phrase_recorded={String(packet.operator_go_phrase_recorded)}</div>
        <div>operator_go_phrase_valid={String(packet.operator_go_phrase_valid)}</div>
        <div>operator_go_phrase_value_stored=false</div>
        <div>destination_binding_confirmed={String(packet.destination_binding_confirmed)}</div>
        <div>dry_run_envelope_normalization_performed=true</div>
        <div>dry_run_request_envelope_preview_created=true</div>
        <div>dry_run_request_envelope_id={packet.dry_run_request_envelope_id}</div>
        <div>dry_run_request_envelope_hash={packet.dry_run_request_envelope_hash}</div>
        <div>dry_run_request_body_hash_preview={packet.dry_run_request_body_hash_preview}</div>
        <div>dry_run_envelope_value_stored=false</div>
        <div>request_envelope_executable=false</div>
        <div>envelope_status={envelope.envelope_status}</div>
        <div>envelope_dispatchable={String(envelope.dispatchable)}</div>
        <div>destination_proof_id={packet.destination_proof_id}</div>
        <div>destination_proof_hash={packet.destination_proof_hash}</div>
        <div>kill_switch_evidence_id={packet.kill_switch_evidence_id}</div>
        <div>kill_switch_evidence_hash={packet.kill_switch_evidence_hash}</div>
        <div>credential_presence_evidence_id={packet.credential_presence_evidence_id}</div>
        <div>credential_presence_evidence_hash={packet.credential_presence_evidence_hash}</div>
        <div>fixture_review_id={packet.fixture_review_id}</div>
        <div>fixture_review_hash={packet.fixture_review_hash}</div>
        <div>fixture_review_status={packet.fixture_review_status}</div>
        <div>fixture_review_ready={String(packet.fixture_review_ready)}</div>
        <div>operator_input_contract_id={packet.operator_input_contract_id}</div>
        <div>operator_input_contract_hash={packet.operator_input_contract_hash}</div>
        <div>operator_input_contract_status={packet.operator_input_contract_status}</div>
        <div>operator_input_contract_required_inbox_path={inputContract.required_inbox_path}</div>
        <div>operator_input_contract_required_json_fields={JSON.stringify(inputContract.required_json_fields)}</div>
        <div>operator_input_contract_forbidden_fixture_markers={JSON.stringify(inputContract.forbidden_fixture_markers)}</div>
        <div>fixture_can_satisfy_contract={String(inputContract.fixture_can_satisfy_contract)}</div>
        <div>live_preflight_id={packet.live_preflight_id}</div>
        <div>live_preflight_hash={packet.live_preflight_hash}</div>
        <div>live_preflight_status={packet.live_preflight_status}</div>
        <div>redacted_operator_review_id={packet.redacted_operator_review_id}</div>
        <div>redacted_operator_review_hash={packet.redacted_operator_review_hash}</div>
        <div>redacted_operator_review_status={packet.redacted_operator_review_status}</div>
        <div>redacted_review_packet_ready={String(packet.redacted_review_packet_ready)}</div>
        <div>redaction_performed={String(redactedReview.redaction_performed)}</div>
        <div>redaction_fields={JSON.stringify(redactedReview.redaction_fields)}</div>
        <div>redacted_body_value_stored={String(redactedReview.body_value_stored)}</div>
        <div>redacted_go_phrase_value_stored={String(redactedReview.go_phrase_value_stored)}</div>
        <div>redacted_webhook_url_value_stored={String(redactedReview.webhook_url_value_stored)}</div>
        <div>redacted_credential_value_stored={String(redactedReview.credential_value_stored)}</div>
        <div>redacted_review_blocked_reasons={JSON.stringify(redactedReview.blocked_reasons)}</div>
        <div>operator_review_decision_id={packet.operator_review_decision_id}</div>
        <div>operator_review_decision_hash={packet.operator_review_decision_hash}</div>
        <div>operator_review_decision_status={packet.operator_review_decision_status}</div>
        <div>operator_review_decision_available={String(packet.operator_review_decision_available)}</div>
        <div>operator_review_decision_approved={String(packet.operator_review_decision_approved)}</div>
        <div>operator_review_decision_rejected={String(packet.operator_review_decision_rejected)}</div>
        <div>operator_review_decision_held={String(packet.operator_review_decision_held)}</div>
        <div>operator_review_decision_value={reviewDecision.decision}</div>
        <div>operator_review_decision_scope={reviewDecision.decision_scope}</div>
        <div>operator_review_decision_phrase_valid={String(reviewDecision.decision_phrase_valid)}</div>
        <div>operator_review_decision_notes_value_stored={String(reviewDecision.notes_value_stored)}</div>
        <div>operator_review_decision_blocked_reasons={JSON.stringify(reviewDecision.blocked_reasons)}</div>
        <div>dispatch_decision_readiness_id={packet.dispatch_decision_readiness_id}</div>
        <div>dispatch_decision_readiness_hash={packet.dispatch_decision_readiness_hash}</div>
        <div>dispatch_decision_readiness_status={packet.dispatch_decision_readiness_status}</div>
        <div>dispatch_decision_approval_route_candidate_ready_not_dispatch={String(packet.approval_route_candidate_ready_not_dispatch)}</div>
        <div>dispatch_decision_rejection_route_recorded_not_dispatch={String(packet.rejection_route_recorded_not_dispatch)}</div>
        <div>dispatch_decision_hold_route_recorded_not_dispatch={String(packet.hold_route_recorded_not_dispatch)}</div>
        <div>dispatch_decision_tier_model={JSON.stringify(dispatchDecision.dispatch_tier_model)}</div>
        <div>automation_first_alignment={String(dispatchDecision.automation_first_alignment)}</div>
        <div>jim_final_authority_required={String(dispatchDecision.jim_final_authority_required)}</div>
        <div>supervised_live_edge_required={String(dispatchDecision.supervised_live_edge_required)}</div>
        <div>dispatch_decision_request_envelope_executable={String(dispatchDecision.request_envelope_executable)}</div>
        <div>dispatch_decision_dispatchable={String(dispatchDecision.dispatchable)}</div>
        <div>dispatch_decision_ready_for_dispatch={String(dispatchDecision.ready_for_dispatch)}</div>
        <div>dispatch_decision_live_action_allowed={String(dispatchDecision.live_action_allowed)}</div>
        <div>dispatch_decision_blocked_reasons={JSON.stringify(dispatchDecision.blocked_reasons)}</div>
        <div>dispatch_route_preview_id={packet.dispatch_route_preview_id}</div>
        <div>dispatch_route_preview_hash={packet.dispatch_route_preview_hash}</div>
        <div>dispatch_route_preview_status={packet.dispatch_route_preview_status}</div>
        <div>dispatch_route_class={routePreview.route_class}</div>
        <div>dispatch_route_selection_reason={routePreview.route_selection_reason}</div>
        <div>route_preview_ready_not_dispatch={String(routePreview.route_preview_ready_not_dispatch)}</div>
        <div>dispatch_route_request_envelope_executable={String(routePreview.request_envelope_executable)}</div>
        <div>dispatch_route_dispatchable={String(routePreview.dispatchable)}</div>
        <div>dispatch_route_ready_for_dispatch={String(routePreview.ready_for_dispatch)}</div>
        <div>dispatch_route_live_action_allowed={String(routePreview.live_action_allowed)}</div>
        <div>dispatch_route_blocked_reasons={JSON.stringify(routePreview.blocked_reasons)}</div>
        <div>pre_dispatch_readiness_id={packet.pre_dispatch_readiness_id}</div>
        <div>pre_dispatch_readiness_hash={packet.pre_dispatch_readiness_hash}</div>
        <div>normalized_pre_dispatch_readiness_evaluated=true</div>
        <div>operator_review_ready={String(packet.operator_review_ready)}</div>
        <div>dispatch_attempted=false</div>
        <div>dispatch_request_count=0</div>
        <div>webhook_request_count=0</div>
        <div>ready_for_dispatch=false</div>
        <div>live_action_allowed=false</div>
        <div>credential_value_read_made=false</div>
        <div>env_value_read_made=false</div>
        <div>webhook_validation_performed=false</div>
        <div>blocked_reasons={JSON.stringify(packet.blocked_reasons)}</div>
        <div>operator_input_contract_blocked_reasons={JSON.stringify(inputContract.blocked_reasons)}</div>
        <div>live_preflight_blocked_reasons={JSON.stringify(livePreflight.blocked_reasons)}</div>
        <div>fixture_caveats={JSON.stringify(fixtureReview.fixture_caveats)}</div>
        <div>Locks: intake/normalization/fixture review only; no Discord send/webhook validation/outbox/ledger/scheduler/retry/provider/API/credential value read</div>
      </div>
    </Panel>
  );
}
