// Capital Chronicle ContentOps V5 — canonical three-story package review console.
// Read-only forensic surface. No decision capture, dispatch, publication, or external action.

import { useMemo, useState } from 'react';
import { useApp } from '../state';
import {
  canonicalReviewStories,
  canonicalReviewSummary,
  selectCanonicalReviewRole,
  selectCanonicalReviewStory,
  selectCanonicalReviewVariant,
  type CanonicalReviewStory,
} from '../data/operatorPackageReviewAdapter';
import { EvidenceChip, Panel, StatusChip } from '../ui/primitives';

const ROLE_LABELS: Record<string, string> = {
  assignment_editor: 'Assignment editor',
  evidence_planner: 'Evidence planner',
  reporter_writer: 'Reporter / writer',
  quantitative_editor: 'Quantitative editor',
  visual_editor: 'Visual editor',
  copy_editor: 'Copy editor',
  platform_editor: 'Platform editor',
  adversarial_final_reviewer: 'Adversarial final reviewer',
};

const PLATFORM_LABELS: Record<string, string> = {
  substack_newsletter: 'Substack newsletter',
  linkedin: 'LinkedIn',
  x_twitter: 'X / Twitter',
  facebook_page: 'Facebook page',
  telegram: 'Telegram',
  youtube_community: 'YouTube community',
};

function HashValue({ children }: { children: string }) {
  return (
    <span className="break-all font-mono text-[11px] leading-relaxed text-fg-muted">
      {children}
    </span>
  );
}

function IdentityRow({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="grid gap-1 border-b border-line/70 py-2.5 last:border-0 md:grid-cols-[9rem_1fr]">
      <dt className="font-mono text-[10px] font-bold uppercase tracking-[0.12em] text-fg-subtle">
        {label}
      </dt>
      <dd className={mono ? 'break-all font-mono text-[11px] text-fg-muted' : 'text-[12px] text-fg'}>
        {value}
      </dd>
    </div>
  );
}

function BlockerGroup({
  label,
  blockers,
}: {
  label: string;
  blockers: string[];
}) {
  return (
    <div className="rounded-lg border border-status-blocked/25 bg-status-blocked/5 p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h3 className="font-mono text-[10px] font-bold uppercase tracking-[0.12em] text-status-blocked">
          {label}
        </h3>
        <span className="font-mono text-[10px] text-status-blocked">
          {blockers.length} BLOCKER{blockers.length === 1 ? '' : 'S'}
        </span>
      </div>
      <ul className="space-y-1.5">
        {blockers.map((blocker) => (
          <li key={blocker} className="flex gap-2 text-[11px] leading-relaxed text-fg-muted">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-status-blocked" />
            <span className="break-all font-mono">{blocker}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function StoryTabs({
  activeStory,
  onChange,
}: {
  activeStory: CanonicalReviewStory;
  onChange: (story: CanonicalReviewStory) => void;
}) {
  return (
    <div className="grid gap-2 lg:grid-cols-3" role="tablist" aria-label="Canonical story packages">
      {canonicalReviewStories.map((story, index) => {
        const active = story.storyId === activeStory.storyId;
        return (
          <button
            key={story.storyId}
            id={`canonical-story-tab-${story.storyId}`}
            type="button"
            role="tab"
            aria-selected={active}
            aria-controls="canonical-story-review-panel"
            onClick={() => onChange(story)}
            className={`group relative overflow-hidden rounded-xl border p-4 text-left transition-all duration-200 ${
              active
                ? 'border-accent/60 bg-accent/10 shadow-card'
                : 'border-line bg-surface-1 hover:-translate-y-0.5 hover:border-line-strong hover:bg-surface-2'
            }`}
          >
            <span className={`absolute inset-y-0 left-0 w-1 ${active ? 'bg-accent' : 'bg-transparent'}`} />
            <span className="flex items-start justify-between gap-3">
              <span className="min-w-0">
                <span className="block font-mono text-[10px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
                  Package {String(index + 1).padStart(2, '0')}
                </span>
                <span className="mt-1.5 block text-sm font-semibold leading-snug text-fg">
                  {story.article.title}
                </span>
              </span>
              <StatusChip status="blocked">HOLD</StatusChip>
            </span>
            <span className="mt-3 block truncate font-mono text-[10px] text-fg-subtle">
              {story.storyId}
            </span>
          </button>
        );
      })}
    </div>
  );
}

export function CanonicalPackageReviewConsole() {
  const { select } = useApp();
  const [activeStoryId, setActiveStoryId] = useState(
    canonicalReviewStories[0].storyId,
  );
  const story = useMemo(
    () =>
      canonicalReviewStories.find((item) => item.storyId === activeStoryId) ??
      canonicalReviewStories[0],
    [activeStoryId],
  );

  function activateStory(next: CanonicalReviewStory) {
    setActiveStoryId(next.storyId);
    select(selectCanonicalReviewStory(next));
  }

  const passCount = story.roles.filter((role) => role.status === 'PASS').length;
  const blockedCount = story.roles.length - passCount;

  return (
    <div className="space-y-6">
      <header className="relative overflow-hidden rounded-2xl border border-line bg-surface-1 p-6 shadow-card lg:p-8">
        <div className="pointer-events-none absolute -right-24 -top-32 h-80 w-80 rounded-full bg-accent/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-24 left-1/3 h-56 w-56 rounded-full bg-status-review/10 blur-3xl" />
        <div className="relative flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div className="max-w-3xl">
            <div className="mb-4 flex flex-wrap items-center gap-2">
              <StatusChip status="verified" icon>EXACT GIT EVIDENCE</StatusChip>
              <StatusChip status="review" icon>READ-ONLY</StatusChip>
              <EvidenceChip>DARK-EVIDENCE CONSOLE</EvidenceChip>
            </div>
            <p className="font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-accent">
              Canonical editorial operator packages
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-fg lg:text-4xl">
              Three-story package review console
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-fg-muted">
              Inspect the exact authority receipt, V3 evidence binding, canonical copy,
              role outcomes, blockers, and platform payload hashes before making an
              operator decision outside this surface.
            </p>
          </div>
          <div className="min-w-[18rem] rounded-xl border border-status-blocked/35 bg-status-blocked/10 p-4">
            <div className="font-mono text-[10px] font-bold uppercase tracking-[0.15em] text-status-blocked">
              Current recommendation
            </div>
            <div className="mt-2 text-2xl font-semibold tracking-tight text-status-blocked">
              {canonicalReviewSummary.recommendation}
            </div>
            <p className="mt-2 text-[11px] leading-relaxed text-fg-muted">
              All three packages remain HOLD. This recommendation is evidence display
              only and cannot execute a ledger decision.
            </p>
          </div>
        </div>
      </header>

      <section aria-label="Package review summary" className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        {[
          ['Packages', String(canonicalReviewSummary.packageCount), '3 exact story bindings'],
          ['Role outcomes', String(canonicalReviewSummary.roleCount), '8 deterministic roles each'],
          ['Platform payloads', String(canonicalReviewSummary.variantCount), '6 variants per package'],
          ['Unresolved blockers', String(canonicalReviewSummary.blockerCount), 'No authority upgraded'],
          ['Surface mode', 'READ ONLY', 'No decision or dispatch action'],
        ].map(([label, value, hint], index) => (
          <div
            key={label}
            className={`rounded-xl border p-4 shadow-card ${
              index === 3
                ? 'border-status-blocked/30 bg-status-blocked/5'
                : 'border-line bg-surface-1'
            }`}
          >
            <div className="font-mono text-[9.5px] font-bold uppercase tracking-[0.12em] text-fg-subtle">
              {label}
            </div>
            <div className="mt-2 text-xl font-semibold tracking-tight text-fg">{value}</div>
            <div className="mt-1 text-[10px] leading-snug text-fg-subtle">{hint}</div>
          </div>
        ))}
      </section>

      <StoryTabs activeStory={story} onChange={activateStory} />

      <section
        id="canonical-story-review-panel"
        role="tabpanel"
        aria-labelledby={`canonical-story-tab-${story.storyId}`}
        className="space-y-6"
      >
        <div className="grid gap-4 xl:grid-cols-[1.35fr_1fr]">
          <Panel
            title="Story + source identity"
            subtitle="Exact authority receipt and canonical V3 binding"
            actions={<StatusChip status="verified">BYTE BOUND</StatusChip>}
          >
            <dl>
              <IdentityRow label="Story ID" value={story.storyId} mono />
              <IdentityRow label="Candidate ID" value={story.candidateId} mono />
              <IdentityRow label="Source family" value={story.authority.sourceFamily} />
              <IdentityRow label="Official source" value={story.authority.sourceUrl} mono />
              <IdentityRow label="Repository" value={story.authority.repository} mono />
              <IdentityRow label="Producer commit" value={story.authority.producerCommit} mono />
              <IdentityRow label="Authority path" value={story.authority.artifactPath} mono />
              <IdentityRow label="Git blob SHA-1" value={story.authority.gitBlobSha1} mono />
              <IdentityRow label="Fetched bytes" value={`${story.authority.byteLength} bytes`} mono />
              <IdentityRow label="Byte SHA-256" value={story.authority.byteSha256} mono />
            </dl>
          </Panel>

          <div className="space-y-4">
            <Panel
              title="Package disposition"
              subtitle="Unsigned package; no decision captured"
              actions={<StatusChip status="review">{story.state}</StatusChip>}
            >
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg border border-line bg-surface-2 p-3">
                  <div className="font-mono text-[9px] font-bold uppercase tracking-wider text-fg-subtle">Editorial state</div>
                  <div className="mt-1.5 text-lg font-semibold text-status-blocked">{story.editorialState}</div>
                </div>
                <div className="rounded-lg border border-line bg-surface-2 p-3">
                  <div className="font-mono text-[9px] font-bold uppercase tracking-wider text-fg-subtle">Recommended</div>
                  <div className="mt-1.5 text-lg font-semibold text-status-blocked">{story.recommendation}</div>
                </div>
              </div>
              <div className="mt-4 space-y-3">
                <div>
                  <div className="mb-1 font-mono text-[9px] uppercase tracking-wider text-fg-subtle">Package hash</div>
                  <HashValue>{story.packageHash}</HashValue>
                </div>
                <div>
                  <div className="mb-1 font-mono text-[9px] uppercase tracking-wider text-fg-subtle">V3 packet</div>
                  <HashValue>{story.v3PacketId}</HashValue>
                </div>
                <div>
                  <div className="mb-1 font-mono text-[9px] uppercase tracking-wider text-fg-subtle">V3 logical hash</div>
                  <HashValue>{story.v3PacketLogicalHash}</HashValue>
                </div>
              </div>
            </Panel>

            <div className="rounded-xl border border-dashed border-status-blocked/45 bg-status-blocked/5 p-4">
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-full border border-status-blocked/30 bg-status-blocked/10 font-mono text-xs text-status-blocked">×</span>
                <div>
                  <h2 className="text-sm font-semibold text-fg">Execution boundary locked</h2>
                  <p className="mt-0.5 text-[11px] text-fg-muted">No approval ledger, dispatch, provider, browser, credential, or public-write capability is mounted.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
          <Panel
            title="Canonical article"
            subtitle={`${story.article.mode} · exact final render`}
            actions={<StatusChip status="verified">HASH BOUND</StatusChip>}
          >
            <article>
              <h2 className="text-2xl font-semibold leading-tight tracking-tight text-fg">
                {story.article.title}
              </h2>
              <div className="mt-4 whitespace-pre-line rounded-xl border border-line bg-bg/40 p-5 text-[14px] leading-7 text-fg-muted">
                {story.article.body}
              </div>
              <dl className="mt-4">
                <IdentityRow label="Article ID" value={story.article.id} mono />
                <IdentityRow label="Article SHA-256" value={story.article.hash} mono />
              </dl>
            </article>
          </Panel>

          <Panel
            title="Exact approved claims"
            subtitle="Article-used allowlist with citations and permissions"
            actions={<StatusChip status="verified">{story.claims.length} USED</StatusChip>}
          >
            <div className="space-y-3">
              {story.claims.map((claim, index) => (
                <div key={claim.id} className="rounded-xl border border-line bg-surface-2 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="font-mono text-[10px] font-bold uppercase tracking-wider text-accent">
                      Claim {String(index + 1).padStart(2, '0')}
                    </div>
                    <StatusChip status="verified">{claim.permission}</StatusChip>
                  </div>
                  <p className="mt-3 text-sm leading-relaxed text-fg">{claim.text}</p>
                  <div className="mt-3 border-t border-line pt-3">
                    <HashValue>{claim.id}</HashValue>
                    <div className="mt-2 font-mono text-[10px] text-fg-subtle">{claim.authority}</div>
                    {claim.citations.map((citation) => (
                      <div key={citation} className="mt-2 break-all text-[11px] leading-relaxed text-fg-muted">
                        {citation}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 rounded-lg border border-status-review/30 bg-status-review/5 p-3">
              <div className="font-mono text-[10px] font-bold uppercase tracking-wider text-status-review">Limitations</div>
              <ul className="mt-2 space-y-1.5">
                {story.limitations.map((limitation) => (
                  <li key={limitation} className="text-[11px] leading-relaxed text-fg-muted">• {limitation}</li>
                ))}
              </ul>
            </div>
          </Panel>
        </div>

        <Panel
          title="Eight-role canonical editorial handoff"
          subtitle="Deterministic, evidence-bound outcomes from the existing orchestrator"
          actions={
            <div className="flex gap-2">
              <StatusChip status="verified">{passCount} PASS</StatusChip>
              <StatusChip status="blocked">{blockedCount} BLOCK</StatusChip>
            </div>
          }
          bodyClassName="p-0"
        >
          <div className="grid md:grid-cols-2 xl:grid-cols-4">
            {story.roles.map((role, index) => {
              const passed = role.status === 'PASS';
              return (
                <button
                  key={role.role}
                  id={`canonical-role-${story.storyId}-${role.role}`}
                  type="button"
                  onClick={() => select(selectCanonicalReviewRole(story, role))}
                  className="group border-b border-r border-line p-4 text-left transition-colors hover:bg-surface-2"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-fg-subtle">
                      Role {String(index + 1).padStart(2, '0')}
                    </span>
                    <StatusChip status={passed ? 'verified' : 'blocked'}>{role.status}</StatusChip>
                  </div>
                  <h3 className="mt-3 text-sm font-semibold text-fg group-hover:text-accent">
                    {ROLE_LABELS[role.role] ?? role.role}
                  </h3>
                  <p className="mt-2 min-h-[2.5rem] text-[10px] leading-relaxed text-fg-subtle">
                    {role.blockers.length === 0 ? 'No role-level blockers.' : role.blockers.join(' · ')}
                  </p>
                  <div className="mt-3 truncate font-mono text-[9px] text-fg-subtle">{role.outputHash}</div>
                </button>
              );
            })}
          </div>
        </Panel>

        <div>
          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-fg">Blocker disposition</h2>
              <p className="mt-0.5 text-[11px] text-fg-muted">Freshness, visual, and adversarial gates remain authoritative.</p>
            </div>
            <StatusChip status="blocked">{story.blockers.unresolved.length} UNRESOLVED</StatusChip>
          </div>
          <div className="grid gap-3 lg:grid-cols-3">
            <BlockerGroup label="Freshness" blockers={story.blockers.freshness} />
            <BlockerGroup label="Visual" blockers={story.blockers.visual} />
            <BlockerGroup label="Adversarial" blockers={story.blockers.adversarial} />
          </div>
        </div>

        <Panel
          title="Six platform variants"
          subtitle="Exact platform payload hashes inherited by this package"
          actions={<StatusChip status="blocked">DISPATCH NOT AUTHORIZED</StatusChip>}
          bodyClassName="p-0"
        >
          <div className="grid md:grid-cols-2 xl:grid-cols-3">
            {story.variants.map((variant, index) => (
              <button
                key={variant.platform}
                id={`canonical-variant-${story.storyId}-${variant.platform}`}
                type="button"
                onClick={() => select(selectCanonicalReviewVariant(story, variant))}
                className="group border-b border-r border-line p-4 text-left transition-colors hover:bg-surface-2"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="font-mono text-[9px] font-bold uppercase tracking-wider text-fg-subtle">Payload {String(index + 1).padStart(2, '0')}</div>
                    <h3 className="mt-1.5 text-sm font-semibold text-fg group-hover:text-accent">
                      {PLATFORM_LABELS[variant.platform] ?? variant.platform}
                    </h3>
                  </div>
                  <StatusChip status="review">REVIEW</StatusChip>
                </div>
                <div className="mt-4 rounded-md border border-line bg-bg/40 p-2.5">
                  <HashValue>{variant.payloadHash}</HashValue>
                </div>
              </button>
            ))}
          </div>
        </Panel>
      </section>

      <footer className="flex flex-col gap-2 rounded-xl border border-line bg-surface-1 px-4 py-3 text-[10px] text-fg-subtle sm:flex-row sm:items-center sm:justify-between">
        <span className="font-mono">{canonicalReviewSummary.surfaceMode}</span>
        <span>Evidence display only · exact package decisions occur outside this console.</span>
      </footer>
    </div>
  );
}
