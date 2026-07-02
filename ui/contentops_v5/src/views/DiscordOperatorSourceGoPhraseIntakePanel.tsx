// Capital Chronicle ContentOps V5 — Discord operator source + GO phrase intake panel.
// Read-only. No network, storage, credentials, dispatch, webhook validation, or live action.

import {
  discordDestinationBindingProof,
  discordOperatorSourceGoPhraseIntakePacket,
  normalizedOperatorSourceGoPhraseCandidate,
  operatorGoPhraseEvidence,
  operatorSourceGoPhraseSafetySignature,
} from '../data/discordOperatorSourceGoPhraseIntakeAdapter';
import { Metric, Panel, StatusChip } from '../ui/primitives';

export function DiscordOperatorSourceGoPhraseIntakePanel() {
  const packet = discordOperatorSourceGoPhraseIntakePacket;
  const normalized = normalizedOperatorSourceGoPhraseCandidate;

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
        <Metric label="Destination proof" value={discordDestinationBindingProof.destination_proof_hash} status="verified" />
        <Metric label="Safety hash" value={operatorSourceGoPhraseSafetySignature.safety_signature_hash} status="verified" />
      </div>

      <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted font-mono">
        <div>operator_source_go_phrase_intake_status=blocked</div>
        <div>operator_source_artifact_path={packet.operator_source_artifact_path || 'missing'}</div>
        <div>operator_go_phrase_recorded={String(packet.operator_go_phrase_recorded)}</div>
        <div>operator_go_phrase_valid={String(packet.operator_go_phrase_valid)}</div>
        <div>operator_go_phrase_value_stored=false</div>
        <div>destination_binding_confirmed={String(packet.destination_binding_confirmed)}</div>
        <div>request_envelope_executable=false</div>
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
