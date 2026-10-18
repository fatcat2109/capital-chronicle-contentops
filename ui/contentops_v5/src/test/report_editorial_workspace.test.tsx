import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ReportEditorialWorkspace } from '../views/ReportEditorialWorkspace';
import type { ReportWorkspaceData } from '../dailyAppTypes';

function data(): ReportWorkspaceData {
  return { schema_version: 'contentops.cc_report_editorial_workspace.v1', state: 'AVAILABLE', report_events_received: 2,
    latest_report: { report_id: 'asset-report:XNGUSD', report_version: 2, change_kind: 'CORRECTION', source_report_sha256: 'a'.repeat(64),
      known_at_cutoff_utc: '2026-10-18T13:03:41Z', claims: [], horizon_blocks: [], missing_claims: [], materiality_rationale: 'Controlled UI correction example.' },
    latest_simple_result: { classification: 'DRAFT_READY', model_execution_state: 'INJECTED_REPLAY_ONLY', draft_count: 1, preview_count: 8 },
    article: { title: 'Controlled canonical draft', dek: 'Controlled test output only.', substack_body_markdown: 'Dated report context. [[SOURCE:SOURCE_1]]' },
    previews: ['telegram', 'discord', 'x', 'linkedin', 'facebook_page', 'instagram_business', 'threads', 'youtube'].map(destination => ({
      destination, preview_id: `preview-${destination}`, article_identity: 'article-control', claim_lineage: [{ report_id: 'asset-report:XNGUSD', report_version: 2 }],
      payload: { text: `${destination}: controlled native text\n\nhttps://capitalchronicle.substack.com/p/pending-publication-abcd` } })),
    history: [{ report_version: 1, state: 'SUPERSEDED', article_identity: 'old-article', preview_ids: ['old-preview'], superseded_by_version: 2 }],
    named_blocker: null, public_write_performed: false };
}

describe('Main report editorial workspace', () => {
  it('shows canonical copy, eight native previews and lineage with controlled-output label', () => {
    render(<ReportEditorialWorkspace data={data()} />);
    expect(screen.getByText('Controlled canonical draft')).toBeInTheDocument();
    expect(screen.getByText(/no fresh Gemini writer execution/)).toBeInTheDocument();
    for (const destination of ['telegram', 'discord', 'x', 'linkedin', 'facebook page', 'instagram business', 'threads', 'youtube']) {
      expect(screen.getByText(`${destination} · Compiled preview`)).toBeInTheDocument();
    }
    expect(screen.getAllByText(/Canonical link pending/)).toHaveLength(8);
    expect(screen.queryByRole('link', { name: /pending-publication/ })).not.toBeInTheDocument();
    expect(screen.getByText(/old-article/)).toBeInTheDocument();
  });

  it('shows the exact pause blocker and zero created previews without claiming a draft', () => {
    const paused = data(); paused.article = null; paused.previews = []; paused.history = [];
    paused.named_blocker = 'LLM_OPERATOR_PAUSED'; paused.latest_simple_result = { classification: 'DRAFT_BLOCKED', model_execution_state: 'PAUSED_BEFORE_PROVIDER_CALL' };
    render(<ReportEditorialWorkspace data={paused} />);
    expect(screen.getByText('Draft unavailable')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('LLM_OPERATOR_PAUSED');
    expect(screen.getAllByText(/· Not created/)).toHaveLength(8);
    expect(screen.queryByText('Controlled canonical draft')).not.toBeInTheDocument();
  });

  it('withdraws current copy while retaining historical identities', () => {
    const withdrawn = data(); withdrawn.article = null; withdrawn.previews = []; withdrawn.latest_simple_result = null;
    withdrawn.latest_report = { ...withdrawn.latest_report!, report_version: 3, withdrawal_only: true };
    withdrawn.named_blocker = 'CLAIMS_WITHDRAWN'; withdrawn.history[0].state = 'WITHDRAWN';
    render(<ReportEditorialWorkspace data={withdrawn} />);
    expect(screen.getByText('Claims withdrawn')).toBeInTheDocument();
    expect(screen.getByText(/no replacement article is generated/)).toBeInTheDocument();
    const history = screen.getByText(/old-article/);
    expect(within(history).getByText('WITHDRAWN')).toBeInTheDocument();
    expect(screen.queryByText('Controlled canonical draft')).not.toBeInTheDocument();
  });
});
