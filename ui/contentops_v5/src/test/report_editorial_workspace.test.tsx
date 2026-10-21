import { fireEvent, render, screen, within } from '@testing-library/react';
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
  it('shows latest admitted public lineage as producer attestation', () => {
    const snapshot = data();
    snapshot.main_admission_summary = [{ report_id: 'asset-report:UKOIL', report_version: 4,
      report_sha256: 'b'.repeat(64), claims: 24, native_public_excerpts: 23,
      provenance_state: 'PRODUCER_ATTESTED_NATIVE_PUBLIC_EXCERPTS', independent_native_runtime_verified: false,
      known_at_cutoff_utc: '2026-10-20T20:00:00Z' }];
    snapshot.main_admission_summary.push({ ...snapshot.main_admission_summary[0], report_id: 'asset-report:LEGACY',
      known_at_cutoff_utc: null });
    render(<ReportEditorialWorkspace data={snapshot} />);
    expect(screen.getByText(/UKOIL v4 · 24 luận điểm được phép · 23 trích đoạn/)).toBeInTheDocument();
    expect(screen.getByText(/chưa phải bằng chứng độc lập về phiên chạy model/)).toBeInTheDocument();
    expect(screen.getByText(/LEGACY.*chưa lưu mốc báo cáo/)).toBeInTheDocument();
  });
  it('leads with the current edition and keeps prior full copy in history', () => {
    const snapshot = data();
    const article = (run_id: string, title: string) => ({ run_id, article_identity: run_id,
      article: { title, dek: 'Dated mechanism', substack_body_markdown: '## Reading\n\nFull retained copy.' },
      reader_question: 'Which mechanism?', review: { decision: 'KEEP', rationale: 'Exact dated source.' },
      previews: snapshot.previews });
    snapshot.owner_edition = { edition_id: 'current', title: 'Current owner edition', operation_ids: ['new'],
      held_candidates: [{ title: 'Options positioning', reason: 'No current chain.' }],
      ready: 1, held: 1, missing: 0, preview_count: 8,
      opportunity_counts: { new: 0, update: 0, keep: 1, hold: 1, source_blocked: 1 } };
    snapshot.native_edition = [article('old', 'Prior accepted article'), article('new', 'Current useful article')];
    snapshot.native_edition[0].source_review = { decision: 'USE_UNCHANGED', reader_change_summary: 'Same observation; retain original prose.' };
    render(<ReportEditorialWorkspace data={snapshot} />);
    expect(screen.getByRole('heading', { name: 'Current owner edition' })).toBeInTheDocument();
    expect(screen.getByLabelText('Tình trạng ấn bản')).toHaveTextContent('1 bài sẵn đọc · 1 đề tài giữ chờ · 0 bài còn thiếu');
    expect(screen.getByLabelText('Kết quả cơ hội biên tập')).toHaveTextContent('0 bài mới · 0 cập nhật · 1 giữ nguyên · 1 giữ chờ · 1 thiếu nguồn');
    const edition = screen.getByLabelText('Ấn bản newsroom');
    expect(within(edition).getByText('Current useful article')).toBeInTheDocument();
    expect(within(edition).queryByText(/Prior accepted/)).not.toBeInTheDocument();
    expect(edition.querySelectorAll('[data-edition-destination]')).toHaveLength(8);
    const history = screen.getByText('Bài và phiên bản trước (1)').closest('details')!;
    expect(history).not.toHaveAttribute('open');
    expect(within(history).getByText(/Prior accepted article/)).toBeInTheDocument();
    expect(within(history).getByText('Full retained copy.')).toBeInTheDocument();
    expect(within(history).getByText(/Same observation; retain original prose/)).toBeInTheDocument();
  });
  it('shows edition angle, dated sources, revision review and every native preview', () => {
    const snapshot = data();
    snapshot.native_edition = [{ run_id: 'edition-real-owner-controlled-test', article_identity: 'edition-test',
      article: { title: 'Three separate gold questions', dek: 'Price, leverage and custody.', substack_body_markdown: '## Mechanism\n\n**Dated educational interpretation.** [[SOURCE:SOURCE_1]]\n\n[Agency source](https://www.cftc.gov/example)\n\n- Exact dated scope.' },
      angle: 'Separate contract risks', reader_question: 'What is actually owned?', mode: 'EVERGREEN_EXPLAINER',
      review: { decision: 'KEEP', rationale: 'Bounded educational scope and exact source dates retained.' },
      evidence: [{ source_id: 'SOURCE_1', publisher: 'CFTC', url: 'https://www.cftc.gov/example', published_at_utc: '' }],
      previews: snapshot.previews }];
    render(<ReportEditorialWorkspace data={snapshot} />);
    const edition = screen.getByLabelText('Ấn bản newsroom');
    expect(within(edition).getByText('Three separate gold questions')).toBeInTheDocument();
    expect(within(edition).getByText(/Separate contract risks/)).toBeInTheDocument();
    expect(within(edition).getByText(/What is actually owned/)).toBeInTheDocument();
    expect(within(edition).getByText(/Không cung cấp ngày xuất bản/)).toBeInTheDocument();
    expect(edition.querySelectorAll('[data-edition-destination]')).toHaveLength(8);
    expect(within(edition).getByText('Mechanism')).toBeInTheDocument();
    expect(within(edition).getByText('Dated educational interpretation.').tagName).toBe('STRONG');
    expect(within(edition).getByRole('link', { name: 'Agency source' })).toHaveAttribute('href', 'https://www.cftc.gov/example');
    expect(within(edition).getByRole('listitem')).toHaveTextContent('Exact dated scope.');
  });
  it('keeps independent evidence, recirculation, controlled conversion and media visible', () => {
    const snapshot = data();
    snapshot.headline_export = { source_rows_scanned: 0, eligible_rows: 4, missing_rows: 1, coverage: 'bounded', observed_at_utc: '2026-10-19T06:30:00Z', independent_items: 2, main_origin_recirculated_items: 2, gaps: [{ state: 'SOURCE_RIGHTS_MISSING' }] };
    snapshot.conversion = { independent_drafts: 1, main_drafts: 1, fresh_provider_drafts: 0, controlled_drafts: 2 };
    snapshot.independent_results = [{ classification: 'INDEPENDENT_NEWS_DRAFT', model_execution_state: 'INJECTED_REPLAY_ONLY', article_identity: 'independent-1', article: { title: 'EIA grid source-backed draft', dek: 'Dated observation', substack_body_markdown: 'Attributed source context' }, previews: snapshot.previews, media_assets: [{ asset_id: 'chart', caption: 'Grid source comparison', path: '/retained/chart.png', sha256: 'bound-chart', underlying_source_rights_status: 'public_domain' }] }];
    render(<ReportEditorialWorkspace data={snapshot} />);
    expect(screen.getByText(/Independent acquired items: 2/)).toHaveTextContent('Main-origin recirculation: 2');
    expect(screen.getByText(/Draft conversion/)).toHaveTextContent('0 fresh provider');
    expect(screen.getByText('EIA grid source-backed draft')).toBeInTheDocument();
    expect(screen.getByText(/1 rendered media artifacts/)).toBeInTheDocument();
    expect(screen.getByText(/Grid source comparison/)).toHaveTextContent('public_domain');
    expect(screen.getByText('SOURCE RIGHTS MISSING')).toBeInTheDocument();
  });
  it('shows multi-asset feed coverage, lifecycle and exact headline permission gaps', () => {
    const gas = data();
    gas.report_history = [{ report_id: 'asset-report:XNGUSD', report_version: 1, status: 'ADMITTED', change_kind: 'NEW_REPORT' }];
    const oil = data();
    oil.latest_report = { ...oil.latest_report!, report_id: 'asset-report:USOIL', contract_revision: 'asset-analysis-report-v1.1.0' };
    oil.article = { ...oil.article!, title: 'Oil report controlled article' };
    const combined = { ...gas, workspaces: [gas, oil],
      feed: { producer_commit: 'producer-control', observed_at_utc: '2026-10-18T17:00:00Z', configured_bundle_count: 4, new_events: 4,
        coverage: 'CONFIGURED_IMMUTABLE_EXPORTS_ONLY', events: [{ report_id: 'asset-report:USOIL', report_version: 1, state: 'LINEAGE_ONLY_NOOP' }], gaps: [] },
      headline_export: { source_rows_scanned: 500, eligible_rows: 2, missing_rows: 500, coverage: 'BOUNDED_INCREMENTAL_PREFIXES_NOT_HISTORICAL_COMPLETENESS', observed_at_utc: '2026-10-18T17:00:00Z' } };
    render(<ReportEditorialWorkspace data={combined} />);
    expect(screen.getByText(/500 source rows inspected/)).toHaveTextContent('2 permitted projections');
    expect(screen.getByText(/LINEAGE_ONLY_NOOP/)).toBeInTheDocument();
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'asset-report:USOIL' } });
    expect(screen.getByText('Oil report controlled article')).toBeInTheDocument();
    expect(screen.getByText('asset-analysis-report-v1.1.0')).toBeInTheDocument();
    expect(screen.queryByText('Controlled canonical draft')).not.toBeInTheDocument();
  });
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
