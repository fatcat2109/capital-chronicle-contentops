import { manualDistributionEvidenceRegistry, manualDistributionRegistryPlatforms } from '../data/manualDistributionEvidenceRegistryAdapter';
import { Panel, StatusChip } from '../ui/primitives';

const shortHash = (value: string) => `${value.slice(0, 12)}?${value.slice(-8)}`;

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
      </div>
    </Panel>
  );
}
