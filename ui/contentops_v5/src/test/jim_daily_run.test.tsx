import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';

function openView() {
  render(createElement(App));
  fireEvent.click(document.getElementById('nav-jim_daily_run')!);
}

describe('Jim Daily Content Run UI', () => {
  it('renders review-only daily run surface for Jim', () => {
    openView();

    expect(screen.getAllByText(/Jim Daily Content Run/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText('JIM_FINAL_REVIEW_REQUIRED').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Jim final review required/i).length).toBeGreaterThan(0);
    expect(screen.getByText('No provider API')).toBeInTheDocument();
    expect(screen.getByText('No platform dispatch')).toBeInTheDocument();
  });

  it('renders Lane C as blocked without artifact evidence', () => {
    openView();

    expect(screen.getAllByText('Artifact-backed macro brief').length).toBeGreaterThan(0);
    expect(screen.getByText('Lane C blocked without approved artifact evidence')).toBeInTheDocument();
    expect(screen.getByText('Attach approved artifact evidence before drafting.')).toBeInTheDocument();
  });

  it('does not add inputs links or enabled publish controls', () => {
    openView();

    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    for (const button of screen.getAllByRole('button').filter((b) => !(b as HTMLButtonElement).disabled)) {
      expect(button.textContent ?? '').not.toMatch(/publish now|post now|send now|schedule now|dispatch live|verify public url/i);
    }
  });

  it('renders intent to variant preview bundle as placeholders only', () => {
    openView();

    expect(screen.getByText('Content Intent + Platform Variant Preview Bundle')).toBeInTheDocument();
    expect(screen.getAllByText('JIM_REVIEW_REQUIRED_PREVIEW_ONLY').length).toBeGreaterThan(0);
    expect(screen.getByText('Platform previews')).toBeInTheDocument();
    expect(screen.getAllByText('manual_export_ready=false · dispatch_ready=false').length).toBeGreaterThan(0);
    expect(screen.getAllByText('PREVIEW_PLACEHOLDER_READY_FOR_JIM_REVIEW').length).toBeGreaterThan(0);
    expect(screen.getAllByText('BLOCKED_WAITING_FOR_INPUTS').length).toBeGreaterThan(0);
  });

  it('renders variant preview safety flags without live readiness', () => {
    openView();

    expect(screen.getByText('Variant Preview Safety Flags')).toBeInTheDocument();
    expect(screen.getByText('final_public_copy_created')).toBeInTheDocument();
    expect(screen.getByText('llm_provider_called')).toBeInTheDocument();
    expect(screen.getByText('platform_api_called')).toBeInTheDocument();
    expect(screen.getAllByText('publish_ready').length).toBeGreaterThan(0);
    expect(screen.getAllByText('dispatch_ready').length).toBeGreaterThan(0);
  });


  it('renders manual export approval workbench without dispatch authority', () => {
    openView();

    expect(screen.getByText('Manual Export + Approval Packet Workbench')).toBeInTheDocument();
    expect(screen.getAllByText('JIM_APPROVAL_REQUIRED_MANUAL_EXPORT_ONLY').length).toBeGreaterThan(0);
    expect(screen.getByText('Ready after Jim approval')).toBeInTheDocument();
    expect(screen.getAllByText('public_postable=false · dispatch_ready=false · public_url_verified=false').length).toBeGreaterThan(0);
    expect(screen.getByText(/valid_for_dispatch=false/i)).toBeInTheDocument();
  });


  it('renders redacted audit metrics loop as operator-supplied review only', () => {
    openView();

    expect(screen.getByText('Redacted Audit + Metrics Import Loop')).toBeInTheDocument();
    expect(screen.getAllByText('JIM_REVIEW_REQUIRED_OPERATOR_SUPPLIED_METRICS_ONLY').length).toBeGreaterThan(0);
    expect(screen.getByText('Baseline promoted')).toBeInTheDocument();
    expect(screen.getAllByText('operator_supplied_values_only=true · network_called=false · baseline_promoted=false').length).toBeGreaterThan(0);
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });


  it('renders local canonical draft preview as deterministic review-only output', () => {
    openView();

    expect(screen.getByText('Local Canonical Draft Preview + Review')).toBeInTheDocument();
    expect(screen.getByText('deterministic_template_no_llm')).toBeInTheDocument();
    expect(screen.getByText('local_draft_preview_created_for_review')).toBeInTheDocument();
    expect(screen.getByText('pending_operator_review')).toBeInTheDocument();
    expect(screen.getByText('final_article_approved=false')).toBeInTheDocument();
    expect(screen.getByText(/ready_for_llm_drafting=false/i)).toBeInTheDocument();
    expect(screen.getByText(/enabled_publish_send_dispatch_approve_controls=false/i)).toBeInTheDocument();
  });


  it('renders canonical draft final review platform variants as preview-only output', () => {
    openView();

    expect(screen.getByText('Canonical Draft Final Review + Platform Variant Preview')).toBeInTheDocument();
    expect(screen.getByText('ready_for_operator_final_review')).toBeInTheDocument();
    expect(screen.getByText('platform_variant_preview_created_for_operator_review')).toBeInTheDocument();
    expect(screen.getByText('final_review_preview_11fc52e6e452c4d3')).toBeInTheDocument();
    expect(screen.getByText('platform_payloads_approved=false')).toBeInTheDocument();
    expect(screen.getByText(/platform_variants_are_preview_only=true/i)).toBeInTheDocument();
    expect(screen.getByText(/ready_for_auto_publish=false/i)).toBeInTheDocument();
    expect(screen.getAllByText(/ready_for_dispatch=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/llm_provider_call_made=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/public_url_verification_performed=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText('status=preview_only').length).toBeGreaterThan(0);
  });


  it('renders platform variant approval packet preview as locked review-only output', () => {
    openView();

    expect(screen.getByText('Platform Variant Approval Packet Preview')).toBeInTheDocument();
    expect(screen.getByText('approval_packet_preview_created_for_operator_review')).toBeInTheDocument();
    expect(screen.getByText('approval_preview_28f5ef142e404225')).toBeInTheDocument();
    expect(screen.getAllByText(/approved=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/dispatchable=false/i).length).toBeGreaterThan(0);
    expect(screen.getByText('actual_operator_approval_recorded=false')).toBeInTheDocument();
    expect(screen.getByText('dispatch_outbox_ready=false')).toBeInTheDocument();
    expect(screen.getAllByText(/approval_ledger_entry_created=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/platform_payloads_approved=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/ready_for_dispatch=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/live_action_allowed=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/network_call_made=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/credential_read_made=false/i).length).toBeGreaterThan(0);
  });


  it('renders dispatch outbox dry-run preview as locked review-only output', () => {
    openView();

    expect(screen.getByText('Dispatch Outbox Dry-Run Preview')).toBeInTheDocument();
    expect(screen.getByText('dispatch_outbox_dry_run_created_for_operator_review')).toBeInTheDocument();
    expect(screen.getByText('outbox_dry_run_7cfc24c5b0c0eded')).toBeInTheDocument();
    expect(screen.getAllByText(/dispatchable=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/executable=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/approved=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText('executable_outbox_entry_created=false').length).toBeGreaterThan(0);
    expect(screen.getAllByText('dispatch_attempted=false').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/real_outbox_entry_created=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/dispatch_request_count=0/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/webhook_request_count=0/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/platform_api_request_count=0/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/kill_switch_active=true/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/ready_for_dispatch=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/live_action_allowed=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/network_call_made=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/credential_read_made=false/i).length).toBeGreaterThan(0);
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });


  it('renders dispatch outbox operator runbook recovery preview as locked read-only output', () => {
    openView();

    expect(screen.getByText('Dispatch Outbox Operator Runbook + Recovery Preview')).toBeInTheDocument();
    expect(screen.getByText('operator_recovery_runbook_created_for_review')).toBeInTheDocument();
    expect(screen.getByText('operator_recovery_e30e17729faebb93')).toBeInTheDocument();
    expect(screen.getByText('Operator preflight checklist')).toBeInTheDocument();
    expect(screen.getByText('Dry-run replay plan')).toBeInTheDocument();
    expect(screen.getByText('Rollback and stop conditions')).toBeInTheDocument();
    expect(screen.getByText('Failure mode recovery matrix')).toBeInTheDocument();
    expect(screen.getByText('Evidence collection checklist')).toBeInTheDocument();
    expect(screen.getAllByText(/recovery_runbook_created=true/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/manual_fallback_plan_created=true/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/failure_mode_matrix_created=true/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/executable_outbox_entry_created=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/real_outbox_entry_created=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/dispatch_outbox_ready=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/dispatch_attempted=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/dispatch_request_count=0/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/webhook_request_count=0/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/platform_api_request_count=0/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/scheduler_enabled=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/retry_enabled=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/kill_switch_active=true/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/ready_for_dispatch=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/live_action_allowed=false/i).length).toBeGreaterThan(0);
    const panel = screen.getByText('Dispatch Outbox Operator Runbook + Recovery Preview').closest('section')!;
    expect(within(panel).queryByRole('link')).not.toBeInTheDocument();
    expect(within(panel).queryByRole('button')).not.toBeInTheDocument();
    expect(within(panel).queryByRole('textbox')).not.toBeInTheDocument();
  });

});
