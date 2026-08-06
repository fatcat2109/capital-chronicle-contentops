import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { coreV0SoakSnapshot as s } from '../data/coreV0SoakSnapshot';

function openView() {
  render(createElement(App));
  fireEvent.click(document.getElementById('nav-core_v0_shadow_soak')!);
}

describe('CORE V0 Repeated Shadow Soak UI', () => {
  it('shows SHADOW_ONLY mode, kill-switch state, and locked live actions', () => {
    openView();

    expect(screen.getAllByText(/Repeated Shadow Soak and Recovery/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText('SHADOW_ONLY').length).toBeGreaterThan(0);
    expect(screen.getByText(/LIVE ACTIONS LOCKED/)).toBeInTheDocument();
    expect(screen.getAllByText(s.kill_switch_state).length).toBeGreaterThan(0);
  });

  it('renders a snapshot generated from a real run', () => {
    openView();

    expect(s.generated_from_real_run).toBe(true);
    expect(s.schema_version).toBe('contentops.core_v0_repeated_shadow_soak.v1');
  });

  it('never claims calendar uptime for an accelerated logical soak', () => {
    openView();

    expect(s.soak_class).toContain('NOT_CALENDAR_UPTIME');
    expect(s.slo.calendar_uptime_claimed).toBe(false);
    // The phrase appears in the banner and again in the SLO detail column, so assert
    // presence rather than uniqueness.
    expect(screen.getAllByText(/accelerated logical soak/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/calendar days of\s+availability/i).length).toBeGreaterThan(0);
  });

  it('claims neither a full-suite PASS nor a CI PASS', () => {
    openView();

    expect(s.slo.full_suite_pass_claimed).toBe(false);
    expect(s.slo.ci_pass_claimed).toBe(false);
  });

  it('shows every logical newsroom day with its window decisions', () => {
    openView();

    expect(s.logical_days.length).toBeGreaterThan(0);
    for (const day of s.logical_days) {
      expect(screen.getAllByText(day.logical_day_id).length).toBeGreaterThan(0);
      expect(day.windows_completed).toBe(day.intake_window_count);
    }
  });

  it('gives every case an explicit outcome and terminal state', () => {
    openView();

    for (const day of s.logical_days) {
      for (const c of day.cases) {
        expect(c.outcome).toBeTruthy();
        expect(c.terminal_state).toBeTruthy();
        if (c.review_result !== 'PASS') {
          expect(c.terminal_state).not.toBe('REVIEW_READY');
        }
      }
    }
  });

  it('shows Capital Chronicle transformation fidelity', () => {
    openView();

    const faithful = s.logical_days.flatMap((d) =>
      d.cases.filter((c) => c.faithful_transformation),
    );
    expect(faithful.length).toBeGreaterThan(0);
    expect(s.slo.cohort_counts.capital_chronicle_transformations).toBeGreaterThan(0);
  });

  it('lists every recovery drill with its result', () => {
    openView();

    expect(s.recovery_drills.length).toBe(16);
    for (const drill of s.recovery_drills) {
      expect(screen.getAllByText(drill.drill).length).toBeGreaterThan(0);
    }
  });

  it('shows incidents and reconciliation without any blind retry', () => {
    openView();

    expect(s.reconciliation.auto_retried).toBe(0);
    expect(s.reconciliation.duplicate_simulated_objects_created).toBe(0);
    expect(s.reconciliation.resolution_states.length).toBeGreaterThanOrEqual(3);
    expect(screen.getByText(/Incidents and reconciliation/i)).toBeInTheDocument();
  });

  it('shows every SLO measurement with its exact denominator', () => {
    openView();

    expect(s.slo.measurements.length).toBeGreaterThanOrEqual(17);
    const legal = ['PASS', 'FAIL', 'INSUFFICIENT_EVIDENCE', 'NOT_APPLICABLE', 'UNMEASURABLE'];
    for (const m of s.slo.measurements) {
      expect(legal).toContain(m.verdict);
      expect(screen.getAllByText(m.measurement).length).toBeGreaterThan(0);
    }
  });

  it('shows the launch-readiness disposition and every remaining blocker', () => {
    openView();

    expect(s.launch_readiness_disposition).toBe('READY_WITH_EXPLICIT_CAVEATS');
    expect(screen.getAllByText(s.launch_readiness_disposition).length).toBeGreaterThan(0);
    expect(s.remaining_launch_blockers.length).toBeGreaterThan(0);
    for (const blocker of s.remaining_launch_blockers) {
      expect(screen.getByText(blocker)).toBeInTheDocument();
    }
  });

  it('shows the launch edge binding all eight hashes with both actors', () => {
    openView();

    expect(s.launch_edge.required_bindings.length).toBe(8);
    for (const binding of s.launch_edge.required_bindings) {
      expect(screen.getAllByText(binding).length).toBeGreaterThan(0);
    }
    expect(s.launch_edge.authorization_actors_exercised).toContain('AUTONOMOUS_POLICY');
    expect(s.launch_edge.authorization_actors_exercised).toContain('OPERATOR_DECISION');
    expect(s.launch_edge.human_approval_universally_mandatory).toBe(false);
    expect(s.launch_edge.boolean_approval_accepted_as_authority).toBe(false);
  });

  it('shows all four operating modes', () => {
    openView();

    for (const mode of [
      'AUTONOMOUS_DEFAULT',
      'SUPERVISED_OPERATOR_GATE',
      'SHADOW_ONLY',
      'KILL_SWITCH',
    ]) {
      expect(s.operating_modes_supported).toContain(mode);
      expect(screen.getAllByText(mode).length).toBeGreaterThan(0);
    }
  });

  it('executes zero operations and never runs the outbox', () => {
    openView();

    expect(s.launch_edge.operations_executed).toBe(0);
    expect(s.launch_edge.simulated_operation_count).toBeGreaterThan(0);
    expect(s.launch_edge.distinct_idempotency_keys).toBe(
      s.launch_edge.simulated_operation_count,
    );
  });

  it('shows durable state, determinism, runtime and cost', () => {
    openView();

    expect(s.durable.lost_work_items).toBe(0);
    expect(s.durable.duplicate_durable_claims).toBe(0);
    expect(s.durable.restart_reconstruction_status).toBe('PASS');
    expect(s.determinism.identical_artifacts).toBe(s.determinism.compared_artifacts);
    expect(s.runtime.external_cost).toBe('NONE_NO_PAID_API_OR_MODEL_CALL');
    expect(screen.getAllByText(s.runtime.external_cost).length).toBeGreaterThan(0);
  });

  it('states that Work Package F was not started', () => {
    openView();

    expect(s.work_package_f_started).toBe(false);
    expect(screen.getByText(/not started/i)).toBeInTheDocument();
  });

  it('carries no live-authority flag set true anywhere in the snapshot', () => {
    const flags = [
      'publication_authority',
      'dispatch_authority',
      'public_write_authority',
      'approval_captured',
      'credential_read_performed',
      'provider_call_performed',
      'network_call_performed',
      'browser_or_cdp_action_performed',
      'scheduler_or_outbox_action_performed',
      'public_write_performed',
      'upstream_write_performed',
    ];
    const walk = (node: unknown): void => {
      if (Array.isArray(node)) {
        node.forEach(walk);
      } else if (node && typeof node === 'object') {
        for (const [key, value] of Object.entries(node as Record<string, unknown>)) {
          if (flags.includes(key)) expect(value).toBe(false);
          walk(value);
        }
      }
    };
    walk(s);
  });
});
