import { ResearchPackageDecision } from './ResearchPackageDecision';
import { useState } from 'react';
import type { ReportWorkspaceData } from '../dailyAppTypes';

const DESTINATIONS = ['telegram', 'discord', 'x', 'linkedin', 'facebook_page', 'instagram_business', 'threads', 'youtube'];
const display = (value: string) => value.replace(/_/g, ' ');
const gapText: Record<string, string> = {
  CURRENT_MARKET_QUOTES_AND_RELATIVE_RATE_PATH_NOT_VERIFIED: 'Chưa có giá và kỳ vọng chênh lệch lãi suất hiện tại.',
  CURRENT_METAL_CURVE_REAL_YIELDS_AND_FLOWS_NOT_VERIFIED: 'Chưa có đường cong kim loại, lợi suất thực và dòng vốn hiện tại.',
  CURRENT_REPLACEMENT_STORAGE_RELEASE_NOT_YET_RETAINED: 'Cần bản tồn kho gas mới từ nguồn thay thế.',
  INDEX_OPTION_CHAIN_EXPIRY_SETTLEMENT_IV_AND_OPEN_INTEREST_NOT_RETAINED: 'Thiếu chuỗi quyền chọn chỉ số, kỳ hạn, thanh toán, biến động hàm ý và vị thế mở.',
  ISSUER_SPECIFIC_CURRENT_FILING_AND_REVISION_NOT_RETAINED: 'Cần hồ sơ mới và lịch sửa đổi của đúng doanh nghiệp.',
  CURRENT_MARKET_ONCHAIN_DATA_AND_PROPOSAL_FINALIZATION_NOT_VERIFIED: 'Chưa xác minh dữ liệu thị trường/on-chain hiện tại và tình trạng cuối của đề xuất.',
};
function previewText(payload: Record<string, unknown>): string {
  const text = payload.full_text ?? [payload.text ?? payload.root_text ?? '', ...(Array.isArray(payload.reply_texts) ? payload.reply_texts : [])].join('\n\n');
  return String(text).replace(/https:\/\/capitalchronicle\.substack\.com\/p\/pending-publication-[a-z0-9]+/g, '[Canonical link pending]');
}

export function ReportEditorialWorkspace({ data }: { data?: ReportWorkspaceData }) {
  const [selected, select] = useState('');
  const [family, setFamily] = useState('ALL');
  const library = data?.foundation_library;
  const workspaces = data?.workspaces?.length ? data.workspaces : data ? [data] : [];
  const workspace = workspaces.find(w => w.latest_report?.report_id === selected) ?? workspaces[0];
  const report = workspace?.latest_report;
  const result = workspace?.latest_simple_result;
  const controlled = result?.model_execution_state === 'INJECTED_REPLAY_ONLY';
  return <section className="daily-panel report-workspace" aria-label="Capital Chronicle report workspace">
    <header><span>Editorial workspace</span><h2>Capital Chronicle report → article → previews</h2></header>
    {library && <section aria-label="Foundation research library">
      <h3>Thư viện nghiên cứu đa tài sản</h3>
      {library.desk && <section aria-label="Bàn quyết định biên tập"><h4>Bàn quyết định biên tập</h4>
        <p>{library.desk.useful_research_packages} gói giữ dùng · {library.desk.decisions.HOLD} giữ chờ · {library.desk.decisions.REVISE} cần sửa · {library.desk.decisions.STALE} hết hiệu lực · {library.desk.decisions.UNREVIEWED} chưa đọc duyệt.</p>
        <p>{library.desk.kind_counts.NEWS} tin có ngày · {library.desk.kind_counts.BACKGROUND} bài nền · {library.desk.kind_counts.ANALYSIS} phân tích. Các loại không cộng thêm vào số gói.</p>
        <p>{library.desk.missing_current_input_coordinates.length} đầu vào hiện tại còn thiếu; {library.desk.affected_work.length} gói có việc cần xử lý qua owner hiện có.</p>
        {library.desk.affected_work.map(w => <p key={w.brief_id}>{w.brief_id}: {w.reason}</p>)}
      </section>}
      <p>{library.counts.useful_families} nhóm · {library.counts.independent_items} luận điểm từ {library.counts.independent_documents ?? 'các'} tài liệu độc lập · {library.counts.briefs} brief biên tập.</p>
      <p>Research-ready · {library.counts.fresh_provider_drafts} fresh-provider drafts · {library.counts.qualified} qualified · {library.counts.published} published. LLM pause giữ nguyên.</p>
      <p>{library.counts.editor_authored_packages ?? 0} gói nghiên cứu do biên tập soạn · {library.counts.native_previews ?? 0} native previews · {library.counts.media ?? 0} media. Quyết định nghiên cứu hiển thị riêng; chưa duyệt xuất bản, không tính là bài Simple.</p>
      <label>Nhóm chủ đề <select value={family} onChange={e => setFamily(e.target.value)}>
        <option value="ALL">Tất cả</option>{library.families.map(f => <option key={f.family} value={f.family}>{display(f.family)}</option>)}
      </select></label>
      {library.families.filter(f => family === 'ALL' || family === f.family).map(f => <article className="report-copy" key={f.family}>
        <h4>{display(f.family)} · {f.useful_items} luận điểm · {f.briefs} brief</h4>
        <p>Còn thiếu: {f.missing_inputs.map(g => gapText[g] ?? display(g)).join('; ')}</p>
        {library.items.filter(i => i.family === f.family).map(i => <details key={i.item_id}>
          <summary>{i.assets.join(', ')} · {display(i.context_kind)}</summary>
          <p>{i.proposition}</p><p>{i.horizons.join(' / ')}: câu hỏi biên tập, không phải dự báo.</p>
          <p>Nguồn ngày {i.published_at_utc ?? 'chưa xác minh ngày xuất bản'} · được biết lúc {i.known_at_utc}. Không xác minh giá thị trường hiện tại.</p>
          {i.source_modified_at_utc && <p>Ngày sửa nguồn: {i.source_modified_at_utc}; không thay thế ngày xuất bản.</p>}
          <p>{display(i.originality)} · {i.rights_state}</p><p>Câu hỏi tiếp: {i.next_editorial_question}</p>
          <a href={i.source_url} target="_blank" rel="noreferrer">Nguồn gốc</a>
          <details><summary>Provenance và quyền dùng</summary><p style={{ overflowWrap: 'anywhere' }}>Capture {i.source_capture_sha256}<br />Permission {i.permission_sha256}<br />Correction: {i.correction_of ?? 'không có chỉ định sửa bản trước'}</p></details>
        </details>)}
      </article>)}
      {library.briefs.filter(b => family === 'ALL' || b.families.includes(family)).map(b => <details key={b.brief_id}>
        <summary>{b.title} · brief do biên tập soạn</summary>
        <p>{b.audience_value}</p><p>{b.mechanism}</p><p>Giải thích cạnh tranh: {b.competing_explanation}</p>
        <ul>{b.scenarios.map(s => <li key={s}>{s}</li>)}</ul><h4>Điều kiện làm cách giải thích yếu đi</h4>
        <ul>{b.falsifiers.map(s => <li key={s}>{s}</li>)}</ul><p>Còn thiếu: {b.missing_inputs.join('; ')}</p>
        <p>Câu hỏi tiếp: {b.next_question}</p><details><summary>Luận điểm có nguồn</summary>
          {b.facts.map(f => <p key={f.item_id}>{f.text} <a href={f.source_url} target="_blank" rel="noreferrer">Nguồn</a></p>)}
        </details>
      </details>)}
      {!!library.packages?.length && <details><summary>Đọc các gói bài nghiên cứu và native previews</summary>
        {library.packages.filter(p => family === 'ALL' || library.briefs.find(b => b.brief_id === p.brief_id)?.families.includes(family)).map(p => <article className="report-copy" key={p.article_identity}>
          <h4>{p.article.title}</h4><ResearchPackageDecision item={p} /><p>Do biên tập soạn · chưa duyệt xuất bản · {p.source_revision_current ? 'khớp bản nguồn hiện tại' : 'nguồn đã đổi, phải xem lại'}.</p>
          <p>Kiểm tra cơ học: {p.validation.status}. Đọc duyệt ngữ nghĩa: {p.validation.semantic_editorial_review}.</p>
          <div className="report-body">{p.article.substack_body_markdown.replace(/\[\[SOURCE:(SOURCE_\d+)\]\]/g, '[$1]')}</div>
          {p.media_assets.map(m => <figure key={m.asset_id}>{m.preview_data_url?.startsWith('data:image/png;base64,') && m.preview_data_url.length < 2_000_030 && <img src={m.preview_data_url} alt={m.alt_text ?? m.caption} style={{ width: '100%', height: 'auto' }} />}<figcaption style={{ overflowWrap: 'anywhere' }}>{m.caption} · {m.sha256}</figcaption></figure>)}
          {Object.entries(p.previews).map(([destination, payload]) => <details key={destination}><summary>{display(destination)} · research preview</summary><div className="report-body">{previewText(payload)}</div></details>)}
        </article>)}
      </details>}
      {!!library.main_reports?.length && <details><summary>Báo cáo Main · nội dung quay về, không tính là nguồn độc lập</summary>
        {library.main_reports.filter(r => family === 'ALL' || r.families.includes(family)).map(r => <details key={r.report_id}>
          <summary>{r.asset_ids.join(', ')} · v{r.report_version} · {r.change_kind} · {r.withdrawn ? 'WITHDRAWN' : r.status}</summary>
          <p>{display(r.context_kind)}. Không xác minh trạng thái thị trường hiện tại.</p>
          <p>Claim đã đổi: {r.changed_claim_ids.join(', ') || 'Main không chỉ định claim thay đổi'}.</p>
          {r.public_claims.map(c => <article key={c.claim_id}><p>{c.producer_layer}: {c.text} · {c.exact_or_proxy} · {c.freshness_state} {c.basis_risk}</p>
            {c.evidence?.map(e => <p key={e.evidence_id}>Nguồn quan sát: {e.observation_time_utc ?? 'không ghi'} · biết lúc {e.known_at_utc ?? 'không ghi'} · {e.pit_state} · {e.rights_state}{' '}
              {e.source_url?.startsWith('https://') && <a href={e.source_url} target="_blank" rel="noreferrer">Nguồn</a>}</p>)}
          </article>)}
          {r.limitations?.map(l => <p key={l}>Giới hạn Main: {l}</p>)}
          {r.horizons.map(h => <p key={h.horizon}>{h.horizon} · {h.trading_sessions} phiên: {h.outlook}</p>)}
          <p>{r.next_editorial_question}</p>
        </details>)}
      </details>}
      {library.input_composition && <p>Đầu vào cho {library.input_composition.routine_window_count} cửa sổ hiện có: {library.input_composition.independent_research_items} luận điểm nghiên cứu · {library.input_composition.main_editorial_reports} báo cáo Main có nội dung biên tập · {library.input_composition.main_unchanged_reports} bản không thay đổi · {library.input_composition.main_history_only_reports} bản lịch sử. Owner Simple giữ nguyên; LLM đang tạm dừng.</p>}
      {library.gaps.map((g, i) => <p key={i}>Gap: {g.state}</p>)}
      <p>Bước chạy tiếp: {library.next_operation}</p>
    </section>}
    {data?.feed && <details open><summary>Main intelligence feed · {data.feed.configured_bundle_count} configured exports</summary>
      <p>Coverage: {data.feed.coverage} · last scan {data.feed.observed_at_utc}</p>
      <p>{data.feed.new_events} newly received events · report age at scan {workspace?.report_age_at_last_scan_seconds ?? 'unavailable'} seconds</p>
      <p>Producer revision: {data.feed.producer_commit}</p>
      <ul>{data.feed.events.map((event, i) => <li key={`${event.report_id}-${event.report_version}-${i}`}>{event.report_id} v{event.report_version} · {event.state}{event.blockers?.length ? ` · ${event.blockers.join(', ')}` : ''}</li>)}</ul>
      {data.feed.gaps.map((gap, i) => <p key={i}>Feed blocker: {gap.state}</p>)}
    </details>}
    {data?.headline_export && <p role="note">Headline handoff: {data.headline_export.source_rows_scanned} source rows inspected · {data.headline_export.eligible_rows} permitted projections · {data.headline_export.missing_rows} named gaps. {data.headline_export.coverage}</p>}
    {data?.headline_export && <p>Independent acquired items: {data.headline_export.independent_items ?? 0} · Main-origin recirculation: {data.headline_export.main_origin_recirculated_items ?? 0}. Counts describe the latest bounded batch.</p>}
    {data?.source_inventory && <p>Projections returned to Main: {data.source_inventory.independent_items} independent · {data.source_inventory.main_origin_recirculated_items} Main-origin recirculated projections.</p>}
    {data?.conversion && <p>Draft conversion: {data.conversion.independent_drafts} independent · {data.conversion.main_drafts} Main report · {data.conversion.fresh_provider_drafts} fresh provider · {data.conversion.controlled_drafts} controlled.</p>}
    {!!data?.headline_export?.gaps?.length && <details><summary>Source and permission gaps</summary><ul>{Array.from(new Set(data.headline_export.gaps.map(g => g.state))).map(g => <li key={g}>{display(g)}</li>)}</ul></details>}
    {!!data?.independent_results?.length && <details open><summary>Independent source-backed drafts ({data.independent_results.length})</summary>
      {data.independent_results.map(item => <article className="report-copy" key={item.article_identity}>
        <p>{item.model_execution_state === 'INJECTED_REPLAY_ONLY' ? 'Controlled output — no fresh provider execution' : 'Provider output recorded'} · unpublished</p>
        <h3>{item.article?.title}</h3><p>{item.article?.dek}</p><div className="report-body">{item.article?.substack_body_markdown.replace(/\[\[SOURCE:(SOURCE_\d+)\]\]/g, '[$1]')}</div>
        {item.evidence?.map(source => <p key={source.source_id}>{source.source_id} · {source.publisher} · {source.published_at_utc} · {source.url.startsWith('https://') ? <a href={source.url} target="_blank" rel="noreferrer">Read retained source locator</a> : 'Retained internal report identity'}</p>)}
        <p>{item.previews.length} / 8 native previews · {item.media_assets?.length ?? 0} rendered media artifacts · review required before publication</p>
        {item.media_assets?.map(asset => <figure key={asset.asset_id}>
          {asset.preview_data_url?.startsWith('data:image/png;base64,') && asset.preview_data_url.length <= 2_000_030 && <img src={asset.preview_data_url} alt={asset.alt_text ?? asset.caption} style={{ width: '100%', height: 'auto' }} />}
          <figcaption style={{ overflowWrap: 'anywhere' }}>{asset.caption} · {asset.underlying_source_rights_status} · SHA256 {asset.sha256}</figcaption></figure>)}
        {item.previews.map(preview => <details key={preview.preview_id}><summary>{display(preview.destination)} · Independent compiled preview</summary><div className="report-body">{previewText(preview.payload)}</div></details>)}
      </article>)}
    </details>}
    {data?.next_operation && <p>Next operation: {data.next_operation}</p>}
    {!report ? <p>No admitted report is recorded. Independent newsroom intake remains available.</p> : <>
      {workspaces.length > 1 && <label>Report <select value={report.report_id} onChange={e => select(e.target.value)}>
        {workspaces.map(w => <option key={w.latest_report?.report_id}>{w.latest_report?.report_id}</option>)}
      </select></label>}
      <div className="report-summary"><div><strong>{report.report_id}</strong><p>Version {report.report_version} · {display(report.change_kind ?? '')}</p></div>
        <div><strong>{workspace.article ? 'Draft available' : report.withdrawal_only ? 'Claims withdrawn' : 'Draft unavailable'}</strong>
          <p>{workspace.previews.length} / 8 compiled previews · unpublished</p></div></div>
      {controlled && <p role="note" className="daily-callout">Controlled output test — no fresh Gemini writer execution. These previews prove mechanics only.</p>}
      {workspace.latest_attempt && <p>Latest attempt: {display(workspace.latest_attempt.classification)} · {display(workspace.latest_attempt.model_execution_state ?? 'not recorded')}</p>}
      {workspace.named_blocker && <p role="status" className="daily-callout">Current blocker: <strong>{workspace.named_blocker}</strong></p>}
      <p>{report.materiality_rationale}</p>
      {workspace.freshness && <p>Freshness: {workspace.freshness.claims.join(', ') || 'No usable current claims'} · {display(workspace.freshness.scope)} · current market refresh {workspace.freshness.current_market_refresh_verified ? 'verified' : 'not verified'}</p>}
      <dl className="report-origin"><dt>Data cutoff</dt><dd>{report.known_at_cutoff_utc ?? 'Unavailable'}</dd>
        <dt>Contract</dt><dd>{report.contract_revision ?? 'Retained v1.0 report'}</dd>
        <dt>Main producer</dt><dd>{report.producer_binding?.producer_commit ?? 'Unbound'}</dd>
        <dt>Report hash</dt><dd>{report.source_report_sha256}</dd></dl>
      <details><summary>Evidence, uncertainty and claim lineage ({report.claims?.length ?? 0})</summary>
        <p>Report truth is separate from underlying event truth. Facts, CC analysis and conditional scenarios retain their labels.</p>
        {report.claims?.map(c => <article className="report-evidence" key={c.claim_id}>
          <strong>{c.claim_id} · {c.producer_layer}</strong><p>{c.text}</p><p>{c.basis_risk}</p>
          {c.evidence.map(e => <p key={e.evidence_id}>{e.evidence_id} · {e.pit_state} · {e.rights_state}{' '}
            {e.source_url?.startsWith('https://') && <a href={e.source_url} target="_blank" rel="noreferrer">Underlying source locator</a>}</p>)}
        </article>)}
        {report.horizon_blocks?.map(h => <p key={h.horizon}><strong>{h.horizon} · {h.trading_sessions} sessions</strong> — {h.outlook}</p>)}
        {!!report.missing_claims?.length && <p>Missing claims: {report.missing_claims.join(', ')}</p>}
      </details>
      <article className="report-copy"><h3>Canonical draft</h3>{workspace.article ? <>
        <h4>{workspace.article.title}</h4><p>{workspace.article.dek}</p>
        <div className="report-body">{workspace.article.substack_body_markdown.replace(/\[\[SOURCE:(SOURCE_\d+)\]\]/g, '[$1]')}</div>
      </> : <p>{report.withdrawal_only ? 'The newest report withdrew its public claims; no replacement article is generated.' : 'No qualified canonical copy exists for this report version.'}</p>}</article>
      <h3>Eight channel previews</h3><p>Preview only. The canonical link is unbound; final dispatch payloads require real Substack readback.</p>
      <div className="report-previews">{DESTINATIONS.map(destination => {
        const preview = workspace.previews.find(p => p.destination === destination);
        return <details key={destination}><summary>{display(destination)} · {preview ? 'Compiled preview' : 'Not created'}</summary>
          {preview ? <><div className="report-body">{previewText(preview.payload)}</div>
            <p>Preview identity: {preview.preview_id}</p><p>Article: {preview.article_identity}</p>
            <details><summary>Claim → evidence → section → derivative lineage</summary><pre>{JSON.stringify(preview.claim_lineage, null, 2)}</pre></details>
          </> : <p>{workspace.named_blocker ?? 'Waiting for a qualified draft.'}</p>}
        </details>;
      })}</div>
      {!!workspace.history.length && <details><summary>Superseded or withdrawn content ({workspace.history.length})</summary>
        {workspace.history.map(h => <p key={h.article_identity}><strong>{h.state}</strong> · report v{h.report_version} → v{h.superseded_by_version} · {h.article_identity} · {h.preview_ids.length} affected previews</p>)}
      </details>}
      {!!workspace.report_history?.length && <details><summary>Report lifecycle ({workspace.report_history.length})</summary>
        {workspace.report_history.map((r, i) => <p key={i}>{r.report_id} v{r.report_version} · {r.change_kind} · {r.status}</p>)}
      </details>}
      {!!workspace.opportunities?.length && <details><summary>Selected and deferred opportunities</summary>
        {workspace.opportunities.map((o, i) => <article key={i}><strong>{o.classification}</strong><p>{o.exact_next_blocker}</p>
          {o.report_candidates.map(r => <p key={r.report_id}>{r.report_id} v{r.report_version} · {r.state}</p>)}</article>)}
      </details>}
    </>}
  </section>;
}
