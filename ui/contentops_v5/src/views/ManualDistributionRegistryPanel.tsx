import { manualDistributionEvidenceRegistry, manualDistributionRegistryPlatforms } from '../data/manualDistributionEvidenceRegistryAdapter';
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
