import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';

function openView() {
  render(createElement(App));
  fireEvent.click(document.getElementById('nav-final_product_readiness')!);
}

describe('Final Product Readiness UI', () => {
  it('renders final readiness summary without live actions', () => {
    openView();

    expect(screen.getAllByText(/Final Product Readiness/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText('FINAL_PRODUCT_READY_FOR_LOCAL_OPERATOR_REVIEW_ONLY').length).toBeGreaterThan(0);
    expect(screen.getByText('TASK_0057 evidence')).toBeInTheDocument();
    expect(screen.getByText('safe audit pending')).toBeInTheDocument();
    expect(screen.getByText('dispatch_allowed_now=false')).toBeInTheDocument();
  });

  it('renders operator decision facts as read-only evidence', () => {
    openView();

    expect(screen.getByText('Operator Decision')).toBeInTheDocument();
    expect(screen.getByText('Ready for local operator review only')).toBeInTheDocument();
    expect(screen.getByText('Substack live publish accepted by committed evidence')).toBeInTheDocument();
    expect(screen.getByText('Public URL not verified')).toBeInTheDocument();
    expect(screen.getByText('Dispatch/live write locked')).toBeInTheDocument();
    expect(screen.getByText('Browser/CDP/network/env/credential action not performed')).toBeInTheDocument();
  });

  it('renders readiness verdict strip as review-only and not dispatch-ready', () => {
    openView();

    expect(screen.getByLabelText('Readiness Verdict')).toBeInTheDocument();
    expect(screen.getAllByText('FINAL_PRODUCT_READY_FOR_LOCAL_OPERATOR_REVIEW_ONLY').length).toBeGreaterThan(0);
    expect(screen.getByText('Dispatch: blocked')).toBeInTheDocument();
    expect(screen.getByText('Live write: blocked')).toBeInTheDocument();
    expect(screen.getByText('Public URL: not verified')).toBeInTheDocument();
    expect(screen.getByText('Next: Review V5 Final Product Readiness panel')).toBeInTheDocument();
  });

  it('renders evidence trail labels and committed local paths only', () => {
    openView();

    expect(screen.getByText('Evidence Trail')).toBeInTheDocument();
    expect(screen.queryByText('Packet Sources')).not.toBeInTheDocument();
    expect(screen.getByText('TASK_0057 Substack acceptance reconciliation')).toBeInTheDocument();
    expect(screen.getByText('V6 readiness evidence bundle')).toBeInTheDocument();
    expect(screen.getByText('V6 pipeline status matrix')).toBeInTheDocument();
    expect(screen.getByText('Final readiness packet')).toBeInTheDocument();
    expect(screen.getAllByText('docs/automation/V6_SUBSTACK_OPERATOR_DRAFT_COMMAND/task_0057_substack_live_publish_acceptance_reconciliation.json').length).toBeGreaterThan(0);
    expect(screen.getAllByText('docs/automation/V6_READINESS_EVIDENCE_BUNDLE/readiness_evidence_bundle_packet.json').length).toBeGreaterThan(0);
    expect(screen.getAllByText('docs/automation/V6_READINESS_EVIDENCE_BUNDLE/v6_pipeline_status_matrix.json').length).toBeGreaterThan(0);
    expect(screen.getByText('docs/automation/V6_FINAL_PRODUCT_READINESS/final_product_readiness_packet.json')).toBeInTheDocument();
  });

  it('renders remaining blockers without enabling dispatch', () => {
    openView();

    expect(screen.getByText('Remaining Blockers')).toBeInTheDocument();
    expect(screen.getByText('This is not dispatch clearance.')).toBeInTheDocument();
    expect(screen.getByText('Public URL verification is pending.')).toBeInTheDocument();
    expect(screen.getByText('Operator approval/live dispatch gates remain blocked: operator_approval_gate, supervised_dispatch_readiness.')).toBeInTheDocument();
    expect(screen.getByText('Future public URL audit must use operator-supplied public URL only.')).toBeInTheDocument();
    expect(screen.getByText('No browser/CDP/live/network/env/credential action is enabled here.')).toBeInTheDocument();
  });

  it('renders operator handoff checklist without adding inputs or links', () => {
    openView();

    expect(screen.getByText('Operator Handoff Checklist')).toBeInTheDocument();
    expect(screen.getByText('Review Final Readiness verdict')).toBeInTheDocument();
    expect(screen.getByText('Review Evidence Trail')).toBeInTheDocument();
    expect(screen.getByText('Confirm public URL is not verified')).toBeInTheDocument();
    expect(screen.getByText('Do not rerun live publish')).toBeInTheDocument();
    expect(screen.getByText('Use separate operator-supplied public URL audit only if needed')).toBeInTheDocument();
    expect(screen.getByText('Keep dispatch/live write locked')).toBeInTheDocument();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    const lockedActionButtons = screen.getAllByRole('button', { name: /Publish \/ Dispatch \/ Verify public URL/i });
    expect(lockedActionButtons).toHaveLength(1);
    expect(lockedActionButtons[0]).toBeDisabled();
  });

  it('proves unsafe actions stay disabled', () => {
    openView();

    const disabled = screen.getByRole('button', { name: /Publish \/ Dispatch \/ Verify public URL/i });
    expect(disabled).toBeDisabled();
    for (const button of screen.getAllByRole('button').filter((b) => !(b as HTMLButtonElement).disabled)) {
      expect(button.textContent ?? '').not.toMatch(/publish now|post now|send now|schedule now|dispatch live|verify credentials|verify public url/i);
    }
  });
});
