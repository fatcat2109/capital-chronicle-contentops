// Capital Chronicle ContentOps V5 — Discord operator source + GO phrase intake panel.
// Read-only. No network, storage, credentials, dispatch, webhook validation, or live action.

import {
  discordCredentialPresenceEvidence,
  discordDestinationBindingProof,
  discordKillSwitchEvidence,
  discordOperatorSourceGoPhraseIntakePacket,
  discordPreDispatchReadiness,
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
  const readiness = discordPreDispatchReadiness;

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
        <Metric label="Pre-dispatch readiness" value={readiness.pre_dispatch_readiness_status} status="blocked" />
        <Metric label="Safety hash" value={operatorSourceGoPhraseSafetySignature.safety_signature_hash} status="verified" />
      </div>

      <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted font-mono">
        <div>operator_source_go_phrase_intake_status=blocked</div>
        <div>operator_source_artifact_path={packet.operator_source_artifact_path || 'missing'}</div>
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
        <div>Locks: intake/normalization only; no Discord send/webhook validation/outbox/ledger/scheduler/retry/provider/API/credential value read</div>
      </div>
    </Panel>
  );
}
