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
  it('opens exact maintained versions and keeps partial coverage, dates and preparation distinct', () => {
    const snapshot = data();
    const version = { run_id: 'controlled-current', article_identity: 'current-id', article: snapshot.article!,
      previews: snapshot.previews, review: { decision: 'KEEP', rationale: 'Controlled revision-bound decision.' },
      publication: { state: 'PREPARED', next_operation: 'publication-status', destinations: [] },
      accepted_at_utc: '2026-10-22T12:00:00Z', analysis_as_of_utc: '2026-10-21T00:00:00Z', analysis_age_seconds: 172800,
      source_dates: [{ source_id: 'SOURCE_1', publisher: 'Controlled agency', url: 'https://example.com/dated', published_at_utc: '2026-10-20T00:00:00Z', age_seconds: 259200 }],
      next_observation: 'Does the next dated release retain this change?', last_source_check_utc: '2026-10-22T14:00:00Z',
      source_check_scope: 'A check is not a new event.' };
    const prior = { ...version, article_identity: 'prior-id', run_id: 'controlled-prior', article: { ...version.article, title: 'Earlier accepted copy' },
      prepared_state: 'INVALIDATED_BY_SOURCE_REVIEW' };
    snapshot.maintained_stories = [{ story_identity: 'exact-chain', title: 'Maintained controlled story', state: 'KEEP',
      reader_question: 'Which fact changed?', current_view: 'A dated interpretation with uncertainty.',
      countercase: 'A competing explanation remains supported.',
      current_article_identity: 'current-id', prior_article_identity: 'prior-id', next_observation: version.next_observation,
      conditional_thesis_test: 'If new transactions persist, the retained thesis strengthens.',
      next_observation_details: { observable: version.next_observation, expected_at_utc: null, date_state: 'UNKNOWN_NOT_SUPPLIED',
        source_review_id: 'controlled-review', sources: ['https://example.com/dated'], discriminator: 'Conditional only',
        missing_evidence: 'Subsequent disclosure and event date remain unestablished.', scope: 'PRODUCER_REVIEW_OBSERVATION_NOT_NEW_EVENT' },
      latest_assessment: { decision: 'USE_UNCHANGED', summary: 'Later retained check keeps the version without erasing its fact delta.',
        cutoff_utc: '2026-10-22T00:00:00Z', reviewed_at_utc: '2026-10-22T14:00:00Z', missing_sources: [] },
      change: { decision: 'USE_UNCHANGED', summary: 'Retain the accepted interpretation until the named gap is resolved.',
        interpretation_changed: true, prior_interpretation: 'Prior interpretation.', current_interpretation: 'Current interpretation.',
        coverage_complete: false, missing_sources: [{ url: 'https://example.com/missing', status: 'UNAVAILABLE' }],
        source_changes: [{ item_id: 'controlled', state: 'CORRECTED', before: { proposition: 'Old source proposition.' }, after: { proposition: 'Corrected source proposition.' } }] },
      current_version: version, versions: [prior, version], observed_at_utc: '2026-10-23T00:00:00Z' }];
    render(<ReportEditorialWorkspace data={snapshot} />);
    const panel = within(screen.getByRole('region', { name: 'Maintained stories' }));
    const toggle = panel.getByText('Maintained controlled story').closest('summary')!;
    fireEvent.click(toggle);
    expect(toggle.parentElement).toHaveAttribute('open');
    expect(panel.getByText('Which fact changed?')).toBeInTheDocument();
    expect(panel.getByText(/A competing explanation remains supported/)).toBeInTheDocument();
    expect(panel.getByText(/Later retained check keeps/)).toBeInTheDocument();
    expect(panel.getByText('Does the next dated release retain this change?')).toBeInTheDocument();
    expect(panel.getByText(/Expected disclosure date: Unknown/)).toBeInTheDocument();
    expect(panel.getByText(/Thesis test: If new transactions persist/)).toBeInTheDocument();
    expect(panel.getByText('Subsequent disclosure and event date remain unestablished.')).toBeInTheDocument();
    expect(panel.getByRole('link', { name: 'Observation source context' })).toHaveAttribute('href', 'https://example.com/dated');
    expect(panel.getByText(/Source coverage is partial/)).toBeInTheDocument();
    expect(panel.getByRole('link', { name: 'Named source gap' })).toHaveAttribute('href', 'https://example.com/missing');
    expect(panel.getByText(/Analysis as of/)).toHaveTextContent('2 days old');
    expect(panel.getByText(/Last source assessment/)).toHaveTextContent('2026-10-22T14:00:00Z');
    expect(panel.getByText(/Prior source: Old source proposition/)).toBeInTheDocument();
    expect(panel.getByText(/Current interpretation: Current interpretation/)).toBeInTheDocument();
    expect(panel.getByText(/prior preparation is invalidated/)).toBeInTheDocument();
    expect(panel.getAllByText(/8\/8 destination previews/)).toHaveLength(2);
    expect(screen.getByRole('region', { name: 'Maintained stories' }).querySelectorAll('[data-story-version]')).toHaveLength(2);
    expect(panel.getAllByText(/Canonical link pending/)).toHaveLength(16);
  });
  it('keeps dated audience HOLD separate from research questions and frozen opportunities', () => {
    const snapshot = data();
    snapshot.audience_learning = {
      current: { policy: { policy_version: 'control-policy', decision: 'HOLD_NO_POLICY_CHANGE', sample_count: 2, confidence: 0.25 },
        feedback: [{ observation_id: 'obs', collected_at_utc: '2026-10-21', scheduled_for_utc: '2026-09-08', semantic_state: 'NO_OBSERVED_PUBLIC_QUESTIONS' }], metrics_model_calls: 0 },
      opportunities: [{ run_id: 'control-run', snapshot_sha256: 'hash', policy: { policy_version: 'old-policy' }, feedback_count: 1, next_operation: 'Resume the same frozen request.' }],
      follow_up_briefs: [{ feedback_effect: 'No audience demand inferred.', ranked_questions: [{ rank: 1, candidate_id: 'q', question: 'What did the new release change?',
        action: 'Reuse the retained article until evidence changes.', missing_evidence: ['New primary release'], exact_article_match: { run_id: 'old', article_identity: 'article-old' } }], next_operation: 'Compare one source edition.' }] };
    render(<ReportEditorialWorkspace data={snapshot} />);
    const panel = within(screen.getByRole('region', { name: 'Audience learning' }));
    expect(panel.getByText(/HOLD NO POLICY CHANGE/)).toBeInTheDocument();
    expect(panel.getByText(/a later read does not reconstruct/)).toHaveTextContent('2026-09-08');
    expect(panel.getByRole('link', { name: 'Retained article' })).toHaveAttribute('href', '#article-article-old');
    expect(panel.getByText('No audience demand inferred.')).toBeInTheDocument();
    expect(panel.getByText(/control-run/)).toHaveTextContent('old-policy');
  });
  it('shows actual continuation states and destination-local blockers without claiming login', () => {
    const snapshot = data();
    snapshot.native_edition = [{ run_id: 'same-run', article_identity: 'same-article',
      article: snapshot.article!, previews: snapshot.previews, review: { decision: 'KEEP', rationale: 'Exact retained source.' },
      publication: { state: 'PENDING_NATIVE', operation_scope: 'OWNER_MANUAL_ISOLATED', next_operation: 'publication-tool-begin',
        next_command: 'python scripts/run_native_desktop_editorial.py publication-tool-begin --binding exact.json',
        destinations: [{ destination: 'substack', status: 'NATIVE_NEO_TOOL_PENDING', cached_readiness: 'NOT_VERIFIED',
          blocker: 'CURRENT_IDENTITY_REQUIRED' }, { destination: 'telegram', status: 'NOT_DISPATCHED',
          cached_readiness: 'NOT_VERIFIED', blocker: 'WAITING_CANONICAL' }] } }];
    render(<ReportEditorialWorkspace data={snapshot} />);
    const continuation = screen.getByLabelText('Publication continuation');
    expect(continuation).toHaveTextContent('Publication: PENDING NATIVE');
    expect(continuation).toHaveTextContent('CURRENT IDENTITY REQUIRED');
    expect(continuation).toHaveTextContent('WAITING CANONICAL');
    expect(continuation).toHaveTextContent('This manual edition has no dispatch authority');
    expect(continuation).toHaveTextContent('--binding exact.json');
  });
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
      evidence: [{ source_id: 'SOURCE_1', publisher: 'CFTC', url: 'https://www.cftc.gov/example', published_at_utc: '' },
        { source_id: 'SOURCE_2', publisher: 'Issuer', url: 'https://www.sec.gov/Archives/example.htm', published_at_utc: '2025-07-24T00:00:00Z', published_at_source: '2025-07-24' }],
      previews: snapshot.previews }];
    render(<ReportEditorialWorkspace data={snapshot} />);
    const edition = screen.getByLabelText('Ấn bản newsroom');
    expect(within(edition).getByText('Three separate gold questions')).toBeInTheDocument();
    expect(within(edition).getByText(/Separate contract risks/)).toBeInTheDocument();
    expect(within(edition).getByText(/What is actually owned/)).toBeInTheDocument();
    expect(within(edition).getByText(/Không cung cấp ngày xuất bản/)).toBeInTheDocument();
    expect(within(edition).getByText(/2025-07-24 \(date only; release time not supplied\)/)).toBeInTheDocument();
    expect(edition.textContent).not.toContain('2025-07-24T00:00:00Z');
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
