import { coreV0SoakSnapshot as s } from '../data/coreV0SoakSnapshot';
import { Panel, StatusChip, Metric, SectionLabel } from '../ui/primitives';
import { IconClock, IconBlock, IconShield, IconAlert } from '../ui/icons';

type StatusKind = 'verified' | 'blocked' | 'review';

/** An incident is a drill that did not pass. When the soak is clean this list is empty,
 *  so the shape is declared explicitly rather than inferred from an empty literal. */
interface SoakIncident {
  readonly drill: string;
  readonly observed_behaviour: string;
}

const PASS = 'PASS';

function verdictStatus(verdict: string): StatusKind {
  if (verdict === PASS) return 'verified';
  if (verdict === 'FAIL') return 'blocked';
  return 'review';
}

function outcomeStatus(reviewResult: string | null): StatusKind {
  if (reviewResult === PASS) return 'verified';
  return 'blocked';
}

function shortHash(value: string | null | undefined): string {
  return value ? `${String(value).slice(0, 12)}…` : '—';
}

function num(value: number | null | undefined): string {
  return value === null || value === undefined ? '—' : String(value);
}

/**
 * Read-only operator view of one accelerated multi-day CORE V0 shadow soak.
 * Local-only: no network, no credentials, no dispatch path.
 */
export function CoreV0ShadowSoak() {
  const counts = s.slo.cohort_counts;
  const drills = s.recovery_drills;
  const drillsPassed = drills.filter((d) => d.result === PASS).length;
  const edge = s.launch_edge;
  const incidents: readonly SoakIncident[] = s.incidents;
  const readyWithCaveats = s.launch_readiness_disposition === 'READY_WITH_EXPLICIT_CAVEATS';

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            CORE V0 Soak · Work Package E
          </div>
          <h1 className="mt-2 flex items-center gap-2 text-2xl font-semibold tracking-tight text-fg">
            <IconClock className="h-6 w-6 text-accent" />
            Repeated Shadow Soak and Recovery
          </h1>
          <p className="mt-1 text-sm font-medium text-fg-muted">
            {counts.logical_days} logical newsroom days · {counts.intake_windows_completed} of{' '}
            {counts.intake_windows_total} window decisions completed. Zero public writes.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <StatusChip status="review" icon>
            {s.operating_mode}
          </StatusChip>
          <StatusChip status="blocked">{s.kill_switch_state}</StatusChip>
        </div>
      </header>

      <div className="flex items-start gap-3 rounded-xl border border-status-blocked/30 bg-status-blocked/5 p-4">
        <IconBlock className="mt-0.5 h-4 w-4 shrink-0 text-status-blocked" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold uppercase tracking-wide text-fg">
            LIVE ACTIONS LOCKED — SHADOW_ONLY
          </p>
          <p className="mt-1 text-[12px] leading-relaxed text-fg-muted">
            This is an <span className="font-semibold text-fg">accelerated logical soak</span> over
            a deterministic clock. It is not a claim of {counts.logical_days} calendar days of
            availability; calendar uptime and live reliability remain for the separately
            authorized live cohort. Publication, dispatch, and public-write authority are all
            false. No credential read, provider call, browser/CDP action, network intake,
            scheduler execution, or outbox execution occurred.
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        <Metric
          label="Logical days"
          value={String(counts.logical_days)}
          status="verified"
          hint={`${counts.intake_windows_completed}/${counts.intake_windows_total} windows`}
        />
        <Metric
          label="Complete packages"
          value={String(counts.complete_packages)}
          status="verified"
          hint={`newsroom ${counts.packages_by_lane.newsroom ?? 0} · CC ${
            counts.packages_by_lane.capital_chronicle ?? 0
          }`}
        />
        <Metric
          label="Domains decided"
          value={String(counts.domains_decided_count)}
          status="verified"
          hint={`${counts.domain_count} produced a package`}
        />
        <Metric
          label="No publication"
          value={String(counts.no_publication_decisions)}
          status="review"
          hint="valid governed outcome"
        />
        <Metric
          label="Recovery drills"
          value={`${drillsPassed}/${drills.length}`}
          status={drillsPassed === drills.length ? 'verified' : 'blocked'}
          hint="deterministic injected failures"
        />
      </div>

      <Panel
        title="Launch readiness"
        subtitle="one machine-readable disposition with explicit blockers"
      >
        <div className="flex flex-wrap items-center gap-2">
          <StatusChip status={readyWithCaveats ? 'review' : 'blocked'} icon>
            {s.launch_readiness_disposition}
          </StatusChip>
          <span className="font-mono text-[11px] text-fg-subtle">
            verdicts: {Object.entries(s.slo.verdict_counts)
              .map(([k, v]) => `${k} ${v}`)
              .join(' · ')}
          </span>
        </div>
        <SectionLabel>Remaining launch blockers</SectionLabel>
        <ul className="mt-1 space-y-1.5">
          {s.remaining_launch_blockers.map((blocker) => (
            <li key={blocker} className="flex items-start gap-2 text-[12px] text-fg-muted">
              <IconAlert className="mt-0.5 h-3.5 w-3.5 shrink-0 text-status-review" />
              <span>{blocker}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-[11px] text-fg-subtle">
          Calendar uptime claimed:{' '}
          <span className="font-mono text-fg">{s.slo.calendar_uptime_claimed ? 'yes' : 'no'}</span>{' '}
          · full-suite PASS claimed:{' '}
          <span className="font-mono text-fg">
            {s.slo.full_suite_pass_claimed ? 'yes' : 'no'}
          </span>{' '}
          · CI PASS claimed:{' '}
          <span className="font-mono text-fg">{s.slo.ci_pass_claimed ? 'yes' : 'no'}</span>
        </p>
      </Panel>

      <Panel
        title="Logical newsroom days"
        subtitle="each day is a genuinely different governed decision"
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-[12px]">
            <thead>
              <tr className="border-b border-line text-[11px] uppercase tracking-wide text-fg-subtle">
                <th className="py-2 pr-3 font-semibold">Day</th>
                <th className="py-2 pr-3 font-semibold">Windows</th>
                <th className="py-2 pr-3 text-right font-semibold">Selected</th>
                <th className="py-2 pr-3 text-right font-semibold">Deferred</th>
                <th className="py-2 pr-3 text-right font-semibold">Packages</th>
                <th className="py-2 pr-3 text-right font-semibold">No pub.</th>
                <th className="py-2 pr-3 text-right font-semibold">Items</th>
                <th className="py-2 font-semibold">Day hash</th>
              </tr>
            </thead>
            <tbody>
              {s.logical_days.map((day) => (
                <tr key={day.logical_day_id} className="border-b border-line/60">
                  <td className="py-2 pr-3 font-mono text-fg">{day.logical_day_id}</td>
                  <td className="py-2 pr-3 font-mono text-fg-muted">
                    {day.windows_completed}/{day.intake_window_count}
                  </td>
                  <td className="py-2 pr-3 text-right font-mono text-fg-muted">
                    {day.selected_case_ids.length}
                  </td>
                  <td className="py-2 pr-3 text-right font-mono text-fg-muted">
                    {day.deferred_case_ids.length}
                  </td>
                  <td className="py-2 pr-3 text-right font-mono text-fg-muted">
                    {day.outcome_counts.eligible_review_passed}
                  </td>
                  <td className="py-2 pr-3 text-right font-mono text-fg-muted">
                    {day.outcome_counts.no_publication}
                  </td>
                  <td className="py-2 pr-3 text-right font-mono text-fg-muted">
                    {day.durable_work_item_count}
                  </td>
                  <td className="py-2 font-mono text-[11px] text-fg-subtle">
                    {shortHash(day.logical_day_hash)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel
        title="Case outcomes and Capital Chronicle fidelity"
        subtitle="every case reaches an explicit outcome on every day"
      >
        <div className="space-y-3">
          {s.logical_days.slice(0, 3).map((day) => (
            <div key={day.logical_day_id}>
              <p className="font-mono text-[11px] font-bold text-fg-subtle">
                {day.logical_day_id}
              </p>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {day.cases.map((c) => (
                  <span
                    key={c.case_id}
                    className="rounded-md border border-line bg-surface-2 px-2 py-1 font-mono text-[10px] text-fg-muted"
                    title={`${c.case_id} · ${c.terminal_state}`}
                  >
                    <StatusChip status={outcomeStatus(c.review_result)}>{c.outcome}</StatusChip>{' '}
                    {c.domain_family}
                    {c.faithful_transformation ? ' · CC faithful' : ''}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
        <p className="mt-3 text-[11px] text-fg-subtle">
          Capital Chronicle transformations: {counts.capital_chronicle_transformations} ·
          duplicate / update-chain decisions: {counts.duplicate_or_update_chain_decisions}
        </p>
      </Panel>

      <Panel
        title="Restart and recovery drills"
        subtitle={`${drillsPassed} of ${drills.length} deterministic injected failures passed`}
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-[12px]">
            <thead>
              <tr className="border-b border-line text-[11px] uppercase tracking-wide text-fg-subtle">
                <th className="py-2 pr-3 font-semibold">Drill</th>
                <th className="py-2 pr-3 font-semibold">Result</th>
                <th className="py-2 font-semibold">Observed</th>
              </tr>
            </thead>
            <tbody>
              {drills.map((d) => (
                <tr key={d.drill} className="border-b border-line/60">
                  <td className="py-2 pr-3 font-mono text-[11px] text-fg">{d.drill}</td>
                  <td className="py-2 pr-3">
                    <StatusChip status={d.result === PASS ? 'verified' : 'blocked'}>
                      {d.result}
                    </StatusChip>
                  </td>
                  <td className="py-2 text-[11px] text-fg-muted">{d.observed_behaviour}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel
        title="Incidents and reconciliation"
        subtitle="unknown writes never blind-retry"
      >
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-lg border border-line bg-surface-2 px-3 py-2">
            <SectionLabel>Incidents</SectionLabel>
            {incidents.length === 0 ? (
              <p className="mt-1 text-[12px] text-fg-muted">
                No incidents opened: every drill passed.
              </p>
            ) : (
              <ul className="mt-1 space-y-1">
                {incidents.map((incident) => (
                  <li key={incident.drill} className="font-mono text-[11px] text-status-blocked">
                    {incident.drill}: {incident.observed_behaviour}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="rounded-lg border border-line bg-surface-2 px-3 py-2">
            <SectionLabel>Unknown-write reconciliation</SectionLabel>
            <p className="mt-1 text-[12px] text-fg-muted">
              {s.reconciliation.unknown_write_simulations} simulation(s) ·{' '}
              {s.reconciliation.auto_retried} auto-retried ·{' '}
              {s.reconciliation.duplicate_simulated_objects_created} duplicate object(s)
            </p>
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {s.reconciliation.resolution_states.map((state) => (
                <span
                  key={state}
                  className="rounded-md border border-line px-2 py-0.5 font-mono text-[10px] text-fg-muted"
                >
                  {state}
                </span>
              ))}
            </div>
          </div>
        </div>
      </Panel>

      <Panel
        title="Launch edge (dry model)"
        subtitle="immutable authorized bytes a future live cohort would consume"
      >
        <div className="grid gap-3 md:grid-cols-3">
          <Metric
            label="Release intents"
            value={String(edge.release_intent_count)}
            status="verified"
            hint={`${edge.required_bindings.length} bound hashes each`}
          />
          <Metric
            label="Simulated operations"
            value={String(edge.simulated_operation_count)}
            status="review"
            hint={`${edge.distinct_idempotency_keys} distinct idempotency keys`}
          />
          <Metric
            label="Operations executed"
            value={String(edge.operations_executed)}
            status="verified"
            hint="outbox never executed"
          />
        </div>
        <SectionLabel>Bound hashes</SectionLabel>
        <div className="mt-1 flex flex-wrap gap-1.5">
          {edge.required_bindings.map((binding) => (
            <span
              key={binding}
              className="rounded-md border border-line bg-surface-2 px-2 py-1 font-mono text-[10px] text-fg-muted"
            >
              {binding}
            </span>
          ))}
        </div>
        <SectionLabel>Authorization</SectionLabel>
        <p className="mt-1 text-[12px] text-fg-muted">
          Actors exercised:{' '}
          <span className="font-mono text-fg">
            {edge.authorization_actors_exercised.join(' · ')}
          </span>
        </p>
        <p className="mt-1 text-[11px] text-fg-subtle">
          Boolean approval accepted as authority:{' '}
          <span className="font-mono text-fg">
            {edge.boolean_approval_accepted_as_authority ? 'yes' : 'no'}
          </span>{' '}
          · human approval universally mandatory:{' '}
          <span className="font-mono text-fg">
            {edge.human_approval_universally_mandatory ? 'yes' : 'no'}
          </span>
        </p>
        <p className="mt-1 text-[11px] text-fg-subtle">
          Invalidated by a bound-byte change:{' '}
          <span className="font-mono text-fg">
            {edge.invalidation_on_bound_byte_change.still_valid_after_byte_change === false
              ? 'yes'
              : 'no'}
          </span>{' '}
          · expiry enforced:{' '}
          <span className="font-mono text-fg">
            {edge.expiry_proof.expired ? 'yes' : 'no'}
          </span>
        </p>
        <SectionLabel>Operating modes supported</SectionLabel>
        <div className="mt-1 flex flex-wrap gap-1.5">
          {s.operating_modes_supported.map((mode) => (
            <StatusChip key={mode} status={mode === s.operating_mode ? 'review' : 'verified'}>
              {mode}
            </StatusChip>
          ))}
        </div>
      </Panel>

      <Panel
        title="SLO measurements"
        subtitle="every measurement carries its exact denominator"
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-[12px]">
            <thead>
              <tr className="border-b border-line text-[11px] uppercase tracking-wide text-fg-subtle">
                <th className="py-2 pr-3 font-semibold">Measurement</th>
                <th className="py-2 pr-3 text-right font-semibold">Numerator</th>
                <th className="py-2 pr-3 text-right font-semibold">Denominator</th>
                <th className="py-2 pr-3 font-semibold">Verdict</th>
                <th className="py-2 font-semibold">Detail</th>
              </tr>
            </thead>
            <tbody>
              {s.slo.measurements.map((m) => (
                <tr key={m.measurement} className="border-b border-line/60">
                  <td className="py-2 pr-3 font-mono text-[11px] text-fg">{m.measurement}</td>
                  <td className="py-2 pr-3 text-right font-mono text-fg-muted">
                    {num(m.numerator as number | null)}
                  </td>
                  <td className="py-2 pr-3 text-right font-mono text-fg-muted">
                    {num(m.denominator as number | null)}
                  </td>
                  <td className="py-2 pr-3">
                    <StatusChip status={verdictStatus(m.verdict)}>{m.verdict}</StatusChip>
                  </td>
                  <td className="py-2 text-[11px] text-fg-subtle">{m.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Durable state, determinism, runtime and cost" subtitle="accepted Wave 02 store">
        <div className="grid gap-3 md:grid-cols-4">
          <Metric
            label="Durable work items"
            value={String(s.durable.work_item_count)}
            status="verified"
            hint={`${s.durable.lost_work_items} lost · ${s.durable.duplicate_durable_claims} double-claimed`}
          />
          <Metric
            label="Restart reconstruction"
            value={s.durable.restart_reconstruction_status}
            status="verified"
            hint={`${s.durable.restart_reconstructions_passed}/${s.durable.restart_reconstructions_attempted} points`}
          />
          <Metric
            label="Deterministic artifacts"
            value={`${s.determinism.identical_artifacts}/${s.determinism.compared_artifacts}`}
            status="verified"
            hint="runtime excluded by design"
          />
          <Metric
            label="Runtime"
            value={`${s.runtime.total_runtime_seconds}s`}
            status="review"
            hint={`${s.runtime.mean_logical_day_runtime_seconds}s per logical day`}
          />
        </div>
        <p className="mt-3 text-[11px] text-fg-subtle">
          Schema version <span className="font-mono text-fg">{s.durable.schema_version}</span> ·
          external cost <span className="font-mono text-fg">{s.runtime.external_cost}</span> ·
          documented nondeterministic fields:{' '}
          <span className="font-mono text-fg">
            {s.determinism.documented_nondeterministic_fields.join(', ')}
          </span>
        </p>
      </Panel>

      <div className="flex items-start gap-3 rounded-xl border border-line bg-surface-2 p-4">
        <IconShield className="mt-0.5 h-4 w-4 shrink-0 text-fg-subtle" />
        <p className="text-[12px] leading-relaxed text-fg-muted">
          Work Package F (the exact authorized live cohort) is{' '}
          <span className="font-mono text-fg">
            {s.work_package_f_started ? 'started' : 'not started'}
          </span>
          . This shadow task grants no credential, provider, browser/CDP, scheduler, dispatch,
          publication, or public-write authority. Snapshot generated from a real run:{' '}
          <span className="font-mono text-fg">
            {s.generated_from_real_run ? 'yes' : 'no'}
          </span>
          .
        </p>
      </div>
    </div>
  );
}
