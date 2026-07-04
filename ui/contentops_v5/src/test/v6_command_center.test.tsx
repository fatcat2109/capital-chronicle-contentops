import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';

function openView() {
  render(createElement(App));
  fireEvent.click(document.getElementById('nav-v6_command_center')!);
}

describe('V6 Command Center', () => {
  it('renders Jim source-to-audit operator flow', () => {
    openView();
    expect(screen.getByText('Jim Source-to-Audit Command Center')).toBeInTheDocument();
    expect(screen.getByLabelText('Jim Source-to-Audit Operator Flow')).toBeInTheDocument();
    for (const label of ['Source intake', 'Canonical draft', 'Hash approval', 'Outbox readiness', 'Platform variants', 'Media selection', 'Manual dispatch / audit']) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it('renders the full north-star platform universe', () => {
    openView();
    expect(screen.getByText('Full Platform Universe')).toBeInTheDocument();
    for (const platform of ['Substack', 'LinkedIn', 'X', 'Discord', 'Telegram', 'Facebook Page', 'Threads', 'Instagram', 'TikTok', 'Generic Manual']) {
      expect(screen.getAllByText(platform).length).toBeGreaterThan(0);
    }
    expect(screen.getByText('Meta-family page distribution lane')).toBeInTheDocument();
    expect(screen.getByText('High-friction short-video lane')).toBeInTheDocument();
  });

  it('renders source-aware media candidate lanes', () => {
    openView();
    expect(screen.getByText('News Image Candidate Lane')).toBeInTheDocument();
    expect(screen.getByText('Official CPI release visual context')).toBeInTheDocument();
    expect(screen.getByText('metadata-only://official-release-thumbnail')).toBeInTheDocument();
    expect(screen.getByText(/google_scrape=false/i)).toBeInTheDocument();

    expect(screen.getByText('Internal Report Chart/Card Lane')).toBeInTheDocument();
    expect(screen.getByText('Internal alpha dispersion card')).toBeInTheDocument();
    expect(screen.getByText('Forecast-readiness checklist card')).toBeInTheDocument();
    expect(screen.getByText(/built_in_chart_preferred=true/i)).toBeInTheDocument();
  });

  it('renders hash-bound operator decision intake without unlocking dispatch', () => {
    openView();
    expect(screen.getByText('Operator Decision Intake')).toBeInTheDocument();
    for (const decision of ['approve', 'hold', 'reject']) {
      expect(screen.getAllByText(decision).length).toBeGreaterThan(0);
    }
    expect(screen.getByText('Canonical Substack payload approved for manual export evidence only.')).toBeInTheDocument();
    expect(screen.getByText('X wording needs another operator pass before any manual copy.')).toBeInTheDocument();
    expect(screen.getByText('Instagram lane is rejected until rights/account constraints are solved.')).toBeInTheDocument();
    expect(screen.getAllByText(/local-[0-9a-f]{8}-[0-9a-f]{8}/i).length).toBeGreaterThan(2);
    expect(screen.getAllByText(/decision_packet_id=decision_/i).length).toBe(3);
    expect(screen.getAllByText(/dispatch_permission_granted=false/i).length).toBe(3);
    expect(screen.getAllByText(/live_write_allowed=false/i).length).toBeGreaterThan(2);
  });

  it('renders local outbox readiness reconciliation as non-executable', () => {
    openView();
    expect(screen.getByText('Local Outbox Readiness Reconciliation')).toBeInTheDocument();
    for (const state of ['approved_manual_ready', 'held_for_revision', 'rejected_blocked', 'blocked_no_decision', 'blocked_live_scope_required']) {
      expect(screen.getAllByText(state).length).toBeGreaterThan(0);
    }
    expect(screen.getByText('Manual export evidence may be prepared by operator; no executable outbox exists.')).toBeInTheDocument();
    expect(screen.getAllByText('Collect an operator approve/hold/reject packet bound to this payload hash.').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/outbox_entry_created=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/outbox_dispatchable=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/dispatch_allowed_now=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/scheduler_or_retry_wired=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/approval_ledger_live_write_made=false/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/execute outbox locked/i).length).toBeGreaterThan(0);
  });

  it('renders Discord and Telegram operator bridge as redacted local-only status', () => {
    openView();
    expect(screen.getByText('Discord/Telegram Operator Bridge')).toBeInTheDocument();
    expect(screen.getByText('Discord bridge')).toBeInTheDocument();
    expect(screen.getByText('Telegram bridge')).toBeInTheDocument();
    expect(screen.getByText('dry_run_proven_no_send')).toBeInTheDocument();
    expect(screen.getByText('checkpoint_manual_only')).toBeInTheDocument();
    expect(screen.getByText(/webhook\/token\/url redacted and unread; send_attempted=false/i)).toBeInTheDocument();
    expect(screen.getByText(/bot token\/channel secret unread; api_called=false/i)).toBeInTheDocument();
    expect(screen.getAllByText(/message_send_attempted=false/i).length).toBe(2);
    expect(screen.getAllByText(/platform_api_called=false/i).length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText(/webhook_or_bot_token_read=false/i).length).toBe(2);
    expect(screen.getAllByText(/live_approval_ledger_written=false/i).length).toBe(2);
    for (const action of ['send Discord message blocked', 'send Telegram message blocked', 'read webhook URL blocked', 'read bot token blocked']) {
      expect(screen.getByText(action)).toBeInTheDocument();
    }
  });

  it('renders manual/deferred distribution lanes as local-only blocked handoffs', () => {
    openView();
    expect(screen.getByText('Manual/Deferred Distribution Lanes')).toBeInTheDocument();
    for (const lane of ['Facebook Page manual/deferred lane', 'Threads manual/deferred lane', 'Instagram manual/deferred lane', 'TikTok manual/deferred lane', 'Generic Manual manual/deferred lane']) {
      expect(screen.getByText(lane)).toBeInTheDocument();
    }
    for (const state of ['manual_handoff_only', 'blocked_deferred', 'fallback_manual_only']) {
      expect(screen.getAllByText(state).length).toBeGreaterThan(0);
    }
    expect(screen.getByText('Meta-family Facebook Page lane is advisory/manual only; Page/API posting and live edits are blocked.')).toBeInTheDocument();
    expect(screen.getByText('Threads lane is short-form manual copy only; platform API, browser posting, replies, and reactions are blocked.')).toBeInTheDocument();
    expect(screen.getByText('Instagram is deferred because media rights, account constraints, and upload path are not cleared.')).toBeInTheDocument();
    expect(screen.getByText('TikTok is last-priority video-script metadata only; no video asset, upload, account, or live execution path exists.')).toBeInTheDocument();
    expect(screen.getByText('Generic Manual is an operator fallback; it does not imply provider capability for any specific platform.')).toBeInTheDocument();
    expect(screen.getAllByText(/media_download_or_upload_performed=false/i).length).toBe(5);
    expect(screen.getAllByText(/credential_or_env_read=false/i).length).toBe(5);
    expect(screen.getAllByText(/approval_ledger_live_write_made=false/i).length).toBeGreaterThanOrEqual(5);
    for (const action of ['publish/post/edit/comment blocked', 'DM/reply/react blocked', 'call Meta/TikTok/platform API blocked', 'download or upload media blocked', 'read credential/env/session blocked']) {
      expect(screen.getAllByText(action).length).toBeGreaterThan(0);
    }
  });

  it('renders the final operator action strip without unlocking execution', () => {
    openView();
    expect(screen.getByText('Final Operator Action Strip')).toBeInTheDocument();
    for (const label of ['Approved manual export evidence', 'Hold/reject queue', 'Discord/Telegram bridge status handoff', 'Deferred social/manual lane handoff', 'Global locked execution flags']) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    expect(screen.getByText(/Jim may use the approved Substack payload hash for operator-owned manual export evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/Use Discord\/Telegram bridge rows as redacted status only/i)).toBeInTheDocument();
    expect(screen.getByText(/terminal_next_task=Archive stale one-off task scripts/i)).toBeInTheDocument();
    expect(screen.getAllByText(/operator_owned=true/i).length).toBe(5);
    expect(screen.getAllByText(/dispatch_allowed=false/i).length).toBe(5);
    expect(screen.getAllByText(/platform_api_allowed=false/i).length).toBe(5);
    expect(screen.getAllByText(/browser_or_cdp_allowed=false/i).length).toBe(5);
    expect(screen.getAllByText(/public_url_fetch_allowed=false/i).length).toBe(5);
    expect(screen.getAllByText(/credential_or_env_read_allowed=false/i).length).toBe(5);
    expect(screen.getAllByText(/approval_ledger_live_write_allowed=false/i).length).toBe(5);
    for (const action of ['execute outbox blocked', 'call platform/API/provider blocked', 'write live approval ledger blocked']) {
      expect(screen.getAllByText(action).length).toBeGreaterThan(0);
    }
  });

  it('keeps unsafe actions disabled and avoids inputs/links', () => {
    openView();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    const locked = screen.getByRole('button', { name: /Publish \/ Dispatch \/ Scrape \/ Download \/ Verify public URL/i });
    expect(locked).toBeDisabled();
    for (const button of screen.getAllByRole('button').filter((b) => !(b as HTMLButtonElement).disabled)) {
      expect(button.textContent ?? '').not.toMatch(/publish now|post now|send now|schedule now|dispatch live|verify credentials|verify public url|scrape|download/i);
    }
  });
});
