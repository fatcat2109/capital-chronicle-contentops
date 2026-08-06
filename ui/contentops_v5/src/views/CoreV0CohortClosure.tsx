import { coreV0CohortSnapshot as s } from '../data/coreV0CohortSnapshot';
import { Panel, StatusChip, Metric, SectionLabel } from '../ui/primitives';
import { IconLayers, IconBlock, IconImage } from '../ui/icons';

type StatusKind = 'verified' | 'blocked' | 'review';

const PASS_OUTCOME = 'PACKAGE_REVIEW_PASSED';

function outcomeStatus(outcome: string): StatusKind {
  if (outcome === PASS_OUTCOME) return 'verified';
  if (outcome === 'DUPLICATE_OR_LOW_DELTA' || outcome === 'HISTORICAL_NOT_CURRENT') return 'review';
  return 'blocked';
}

function pct(share: number): string {
  return `${Math.round(share * 100)}%`;
}

/**
 * Read-only operator view of one CORE V0 diversified cohort shadow run.
 * Local-only: no network, no credentials, no dispatch path.
 */
export function CoreV0CohortClosure() {
  const counts = s.outcome_counts;
  const passing = s.cases.filter((c) => c.outcome === PASS_OUTCOME);
  const charted = s.cases.filter((c) => c.chart_qa_status === 'PASS');
  const visualPassed = s.cases.filter((c) => c.visual_status === 'PASS');

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            CORE V0 Closure · Work Package D
          </div>
          <h1 className="mt-2 flex items-center gap-2 text-2xl font-semibold tracking-tight text-fg">
            <IconLayers className="h-6 w-6 text-accent" />
            Diversified Cohort Shadow Run
          </h1>
          <p className="mt-1 text-sm font-medium text-fg-muted">
            One local command across {s.corpus.case_count} governed cases. Zero public writes.
          </p>
        </div>
        <StatusChip status="review" icon>{s.operating_mode}</StatusChip>
      </header>

      <div className="flex items-start gap-3 rounded-xl border border-status-blocked/30 bg-status-blocked/5 p-4">
        <IconBlock className="mt-0.5 h-4 w-4 shrink-0 text-status-blocked" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold uppercase tracking-wide text-fg">
            LIVE ACTIONS LOCKED — SHADOW_ONLY
          </p>
          <p className="mt-1 text-[12px] leading-relaxed text-fg-muted">
            Publication, dispatch, and public-write authority are all false. No credential
            read, provider call, browser/CDP action, network intake, or scheduler execution
            occurred. Cases are historical governed evaluation material and are never
            presented as current news.
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Metric
          label="Review passed"
          value={String(counts.eligible_review_passed)}
          status="verified"
          hint={`lanes: ${s.lanes_with_passing_package.join(', ')}`}
        />
        <Metric label="Review blocked" value={String(counts.package_review_blocked)} status="blocked" hint="truthful block" />
        <Metric
          label="Held / suppressed"
          value={String(counts.permission_blocked + counts.evidence_blocked + counts.visual_rights_blocked + counts.duplicate_or_low_delta)}
          status="review"
          hint="hard gates held"
        />
        <Metric label="No publication" value={String(counts.no_publication)} status="review" hint="valid outcome" />
      </div>

      <Panel title="Domain coverage" subtitle={`${s.corpus.domain_family_count} required families`}>
        <div className="flex flex-wrap gap-2">
          {Object.entries(s.corpus.coverage.cases_by_family).map(([family, ids]) => (
            <span
              key={family}
              className="rounded-md border border-line bg-surface-2 px-2 py-1 font-mono text-[11px] text-fg-muted"
            >
              {family} · {(ids as readonly string[]).length}
            </span>
          ))}
        </div>
        <p className="mt-3 text-[12px] text-fg-muted">
          All families represented:{' '}
          <span className="font-mono text-fg">
            {s.corpus.coverage.all_families_represented ? 'yes' : 'no'}
          </span>{' '}
          · fabricated content:{' '}
          <span className="font-mono text-fg">{s.corpus.fabricated_content ? 'yes' : 'no'}</span>
        </p>
      </Panel>

      <Panel title="Portfolio concentration" subtitle="daily cohort">
        <div className="grid gap-3 md:grid-cols-2">
          {Object.entries(s.portfolio_daily.dimensions).map(([dimension, row]) => {
            const d = row as { distinct_values: number; max_share: number; is_concentrated: boolean };
            return (
              <div key={dimension} className="rounded-lg border border-line bg-surface-2 px-3 py-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-mono text-[11px] text-fg">{dimension}</p>
                  <StatusChip status={d.is_concentrated ? 'review' : 'verified'}>
                    {d.is_concentrated ? 'concentrated' : 'balanced'}
                  </StatusChip>
                </div>
                <p className="mt-1 text-[11px] text-fg-muted">
                  {d.distinct_values} distinct · max share {pct(d.max_share)}
                </p>
              </div>
            );
          })}
        </div>
        <p className="mt-3 text-[11px] leading-relaxed text-fg-muted">
          Threshold {pct(s.portfolio_daily.concentration_threshold)}. Concentration penalties
          reorder eligible cases only — evidence, permission, freshness, and material-delta
          gates remain hard gates and diversity never forces filler.
        </p>
      </Panel>

      <Panel title="Cohort cases" subtitle="every case has an explicit outcome">
        <div className="space-y-2">
          {s.cases.map((c) => (
            <div key={c.case_id} className="rounded-lg border border-line bg-surface-2 px-3 py-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-mono text-[12px] text-fg">{c.case_id}</p>
                <StatusChip status={outcomeStatus(c.outcome)}>{c.outcome}</StatusChip>
              </div>
              <p className="mt-1 font-mono text-[11px] text-fg-muted">
                {c.lane} · {c.domain_family} · {c.source_family}
              </p>
              <p className="mt-1 text-[11px] text-fg-muted">
                review: <span className="font-mono text-fg">{String(c.review_result ?? 'not produced')}</span>
                {' · '}visual: <span className="font-mono text-fg">{String(c.visual_status ?? 'n/a')}</span>
                {' · '}SEO: <span className="font-mono text-fg">{String(c.seo_contract_status ?? 'n/a')}</span>
                {' · '}chart: <span className="font-mono text-fg">{String(c.chart_qa_status ?? 'n/a')}</span>
                {' · '}terminal: <span className="font-mono text-fg">{c.terminal_state}</span>
              </p>
              {c.tier1_explicit_outcome_count ? (
                <p className="mt-1 text-[11px] text-fg-muted">
                  Tier-1: {c.tier1_supported_count}/{c.tier1_explicit_outcome_count} built
                  {c.tier1_blocked_destinations.length
                    ? ` · blocked: ${c.tier1_blocked_destinations.join(', ')}`
                    : ''}
                </p>
              ) : null}
              {c.gate_reason ? (
                <p className="mt-1 text-[11px] leading-relaxed text-fg-muted">{c.gate_reason}</p>
              ) : null}
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Visuals, rights, and charts" subtitle="provenance-bound only">
        <div className="grid gap-3 md:grid-cols-3">
          <Metric label="Visual PASS" value={String(visualPassed.length)} status="verified" hint="policy resolved" />
          <Metric label="Charts QA PASS" value={String(charted.length)} status="verified" hint="authorized values only" />
          <Metric
            label="Rights blocked"
            value={String(counts.visual_rights_blocked)}
            status="blocked"
            hint="unreviewed asset withheld"
          />
        </div>
        <ul className="mt-3 space-y-1">
          {charted.map((c) => (
            <li key={c.case_id} className="flex items-start gap-2 font-mono text-[11px] text-fg-muted">
              <IconImage className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent" />
              <span>
                {c.chart_title} — partial period:{' '}
                <span className="text-fg">{String(c.chart_partial_period)}</span>
              </span>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-[11px] leading-relaxed text-fg-muted">
          Charts plot only values already authorized in a governed packet. No forecast,
          probability, scenario, or analytical calculation was created, and generated
          graphics never depict a real scene as though photographed.
        </p>
      </Panel>

      <Panel title="Tier-1 destinations" subtitle={`${s.tier1_destination_count} destinations`}>
        <div className="flex flex-wrap gap-2">
          {s.tier1_destinations.map((platform) => (
            <span
              key={platform}
              className="rounded-md border border-line bg-surface-2 px-2 py-1 font-mono text-[11px] text-fg-muted"
            >
              {platform}
            </span>
          ))}
        </div>
        <p className="mt-3 text-[11px] leading-relaxed text-fg-muted">
          Package fabric: <span className="font-mono text-fg">{s.package_fabric}</span>
        </p>
        <p className="mt-1 text-[11px] leading-relaxed text-fg-muted">
          Instagram Business fails closed when no rights-cleared visual asset exists. No
          image is fabricated to satisfy a platform contract.
        </p>
      </Panel>

      <Panel title="Canonical review and durable state" subtitle="one engine, one store">
        <SectionLabel>Review engine</SectionLabel>
        <p className="mt-1 font-mono text-[11px] text-fg-muted">{s.review_engine}</p>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <Metric
            label="Replay"
            value={s.replay_verification.all_replays_valid ? 'valid' : 'invalid'}
            status={s.replay_verification.all_replays_valid ? 'verified' : 'blocked'}
            hint={`${s.replay_verification.work_items_replayed} work items`}
          />
          <Metric label="Public objects" value={String(s.shadow_readback.public_objects_created)} status="verified" hint="none created" />
          <Metric label="External cost" value="none" status="verified" hint="no paid API" />
        </div>
        <ul className="mt-3 space-y-1">
          {Object.entries(s.durable.terminal_states).map(([id, state]) => (
            <li key={id} className="font-mono text-[11px] text-fg-muted">
              {id} — <span className="text-fg">{String(state)}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-[11px] leading-relaxed text-fg-muted">
          Only a case whose canonical review passed reaches REVIEW_READY. Blocked cases
          terminate as blocked, duplicate-suppressed, or deferred — never as review-ready.
        </p>
      </Panel>

      <Panel title="Passing packages" subtitle="one per input lane">
        <ul className="space-y-1">
          {passing.map((c) => (
            <li key={c.case_id} className="font-mono text-[11px] text-fg-muted">
              PASS {c.lane} — {c.case_id} · {c.domain_family}
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
