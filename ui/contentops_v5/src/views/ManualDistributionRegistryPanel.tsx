import { manualDistributionEvidenceRegistry, manualDistributionRegistryAuditIndex, manualDistributionRegistryPlatforms } from '../data/manualDistributionEvidenceRegistryAdapter';
import { Panel, StatusChip } from '../ui/primitives';

const packetRoles = ['export', 'approval', 'handoff', 'url', 'metrics'] as const;

const shortHash = (value: string) => `${value.slice(0, 12)}...${value.slice(-8)}`;

export function ManualDistributionRegistryPanel() {
  return (
    <Panel
      title="Manual Distribution Registry v0"
      subtitle={`registry_hash=${manualDistributionEvidenceRegistry.registry_hash}`}
      actions={<StatusChip status="blocked">fixture/manual/operator-supplied</StatusChip>}
    >
      <div className="overflow-hidden rounded-xl border border-line bg-surface-2/70">
        <div className="grid grid-cols-[1fr_1.25fr_1.1fr_1.1fr_1.3fr] gap-3 border-b border-line px-4 py-3 font-mono text-[10px] font-bold uppercase tracking-[0.12em] text-fg-subtle">
          <div>Platform</div>
          <div>Status</div>
          <div>Metrics hash</div>
          <div>URL hash</div>
          <div>Safety / controls</div>
        </div>
        <div className="divide-y divide-line">
          {manualDistributionRegistryPlatforms.map((platform) => (
            <div key={platform.platform} className="grid grid-cols-[1fr_1.25fr_1.1fr_1.1fr_1.3fr] gap-3 px-4 py-3 text-xs leading-relaxed">
              <div>
                <div className="font-semibold text-fg">{platform.platform_label}</div>
                <div className="mt-1 font-mono text-[10px] text-fg-subtle">{platform.platform}</div>
              </div>
              <div>
                <StatusChip status="blocked">{platform.lane_status}</StatusChip>
                <div className="mt-2 font-mono text-[10px] text-fg-muted">registry={shortHash(manualDistributionEvidenceRegistry.registry_hash)}</div>
              </div>
              <div className="break-all font-mono text-[10px] text-accent">{shortHash(platform.source_packets.metrics.hash)}</div>
              <div className="break-all font-mono text-[10px] text-accent">{shortHash(platform.source_packets.url.hash)}</div>
              <div>
                <div className="font-mono text-[10px] text-status-blocked">
                  api_used={String(platform.safety_flags.api_used)} | url_network_verified={String(platform.safety_flags.url_network_verified)} | metrics_network_verified={String(platform.safety_flags.metrics_network_verified)} | controls_enabled={String(platform.safety_flags.enabled_publish_send_dispatch_approve_controls)}
                </div>
                <div className="mt-2 text-fg-muted">blocked controls: {Array.from(new Set([...platform.blocked_controls, 'schedule'])).join(', ')}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="border-t border-line bg-surface-1/60 px-4 py-4">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.12em] text-fg-subtle">Audit Index / Operator Review Readiness</div>
          <div className="mt-2 text-sm font-semibold text-fg">manual operator review only - not live readiness</div>
          <div className="mt-3 grid gap-3 lg:grid-cols-3">
            <div className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="font-mono text-[10px] text-fg-muted">readiness={manualDistributionRegistryAuditIndex.registry_readiness_status}</div>
              <div className="sr-only">ready_for_manual_operator_review_only</div>
              <div className="mt-1 font-mono text-[10px] text-fg-muted">source_path_audit_status={manualDistributionRegistryAuditIndex.source_path_audit_status}</div>
              <div className="mt-1 font-mono text-[10px] text-fg-muted">registry={shortHash(manualDistributionRegistryAuditIndex.registry_hash)}</div>
              <div className="mt-1 font-mono text-[10px] text-fg-muted">audit_index={shortHash(manualDistributionRegistryAuditIndex.exact_payload_hash)}</div>
              <div className="mt-1 font-mono text-[10px] text-fg-muted">source_path_audit={shortHash(manualDistributionRegistryAuditIndex.source_path_audit_hash)}</div>
            </div>
            <div className="rounded-lg border border-line bg-surface-2 p-3 font-mono text-[10px] text-status-ready">
              <div>all_paths_exist={String(manualDistributionRegistryAuditIndex.all_paths_exist)}</div>
              <div>all_packet_ids_match={String(manualDistributionRegistryAuditIndex.all_packet_ids_match)}</div>
              <div>all_hashes_match={String(manualDistributionRegistryAuditIndex.all_hashes_match)}</div>
              <div>all_paths_within_docs_automation={String(manualDistributionRegistryAuditIndex.all_paths_within_docs_automation)}</div>
              <div>no_url_like_source_paths={String(manualDistributionRegistryAuditIndex.no_url_like_source_paths)}</div>
            </div>
            <div className="rounded-lg border border-line bg-surface-2 p-3 font-mono text-[10px] text-status-blocked">
              <div>live_readiness_claimed={String(manualDistributionRegistryAuditIndex.non_readiness_claims.live_readiness_claimed)}</div>
              <div>api_readiness_claimed={String(manualDistributionRegistryAuditIndex.non_readiness_claims.api_readiness_claimed)}</div>
              <div>public_url_verification_claimed={String(manualDistributionRegistryAuditIndex.non_readiness_claims.public_url_verification_claimed)}</div>
              <div>platform_auth_readiness_claimed={String(manualDistributionRegistryAuditIndex.non_readiness_claims.platform_auth_readiness_claimed)}</div>
              <div>dispatch_readiness_claimed={String(manualDistributionRegistryAuditIndex.non_readiness_claims.dispatch_readiness_claimed)}</div>
              <div>network_call_made={String(manualDistributionRegistryAuditIndex.network_call_made)}</div>
              <div>provider_call_made={String(manualDistributionRegistryAuditIndex.provider_call_made)}</div>
              <div>env_value_read_made={String(manualDistributionRegistryAuditIndex.env_value_read_made)}</div>
              <div>credential_read_made={String(manualDistributionRegistryAuditIndex.credential_read_made)}</div>
              <div>browser_session_used={String(manualDistributionRegistryAuditIndex.browser_session_used)}</div>
              <div>public_url_fetch_made={String(manualDistributionRegistryAuditIndex.public_url_fetch_made)}</div>
              <div>live_publish_performed_by_contentops={String(manualDistributionRegistryAuditIndex.live_publish_performed_by_contentops)}</div>
              <div>enabled_publish_send_dispatch_approve_controls={String(manualDistributionRegistryAuditIndex.enabled_publish_send_dispatch_approve_controls)}</div>
            </div>
          </div>
          <div className="mt-3 grid gap-3 lg:grid-cols-2">
            <div className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="text-xs font-semibold uppercase tracking-[0.12em] text-fg-subtle">Blockers</div>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-fg-muted">
                {manualDistributionRegistryAuditIndex.blockers.map((blocker) => <li key={blocker}>{blocker}</li>)}
              </ul>
            </div>
            <div className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="text-xs font-semibold uppercase tracking-[0.12em] text-fg-subtle">Caveats</div>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-fg-muted">
                {manualDistributionRegistryAuditIndex.caveats.map((caveat) => <li key={caveat}>{caveat}</li>)}
              </ul>
            </div>
          </div>
        </div>
        <div className="border-t border-line bg-surface-1/60 px-4 py-4">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.12em] text-fg-subtle">Packet drilldown audit</div>
          <div className="mt-3 grid gap-3 lg:grid-cols-3">
            {manualDistributionRegistryPlatforms.map((platform) => (
              <div key={`${platform.platform}-packet-drilldown`} className="rounded-lg border border-line bg-surface-2 p-3">
                <div className="text-sm font-semibold text-fg">{platform.platform_label} packet bindings</div>
                <div className="mt-3 space-y-2">
                  {packetRoles.map((role) => {
                    const packet = platform.source_packets[role];
                    return (
                      <div key={`${platform.platform}-${role}`} className="rounded-md border border-line bg-surface-1 p-2">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-mono text-[10px] font-bold uppercase tracking-[0.12em] text-fg-subtle">{role}</span>
                          <span className="break-all font-mono text-[10px] text-accent">{shortHash(packet.hash)}</span>
                        </div>
                        <div className="mt-1 break-all font-mono text-[10px] text-fg-muted">packet_id={packet.packet_id}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Panel>
  );
}
