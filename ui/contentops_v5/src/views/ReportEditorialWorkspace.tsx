import { useState } from 'react';
import type { ReportWorkspaceData } from '../dailyAppTypes';

const DESTINATIONS = ['telegram', 'discord', 'x', 'linkedin', 'facebook_page', 'instagram_business', 'threads', 'youtube'];
const display = (value: string) => value.replace(/_/g, ' ');
function previewText(payload: Record<string, unknown>): string {
  const text = payload.full_text ?? [payload.text ?? payload.root_text ?? '', ...(Array.isArray(payload.reply_texts) ? payload.reply_texts : [])].join('\n\n');
  return String(text).replace(/https:\/\/capitalchronicle\.substack\.com\/p\/pending-publication-[a-z0-9]+/g, '[Canonical link pending]');
}

export function ReportEditorialWorkspace({ data }: { data?: ReportWorkspaceData }) {
  const [selected, select] = useState('');
  const workspaces = data?.workspaces?.length ? data.workspaces : data ? [data] : [];
  const workspace = workspaces.find(w => w.latest_report?.report_id === selected) ?? workspaces[0];
  const report = workspace?.latest_report;
  const result = workspace?.latest_simple_result;
  const controlled = result?.model_execution_state === 'INJECTED_REPLAY_ONLY';
  return <section className="daily-panel report-workspace" aria-label="Capital Chronicle report workspace">
    <header><span>Editorial workspace</span><h2>Capital Chronicle report → article → previews</h2></header>
    {data?.feed && <details open><summary>Main intelligence feed · {data.feed.configured_bundle_count} configured exports</summary>
      <p>Coverage: {data.feed.coverage} · last scan {data.feed.observed_at_utc}</p>
      <p>{data.feed.new_events} newly received events · report age at scan {workspace?.report_age_at_last_scan_seconds ?? 'unavailable'} seconds</p>
      <p>Producer revision: {data.feed.producer_commit}</p>
      <ul>{data.feed.events.map((event, i) => <li key={`${event.report_id}-${event.report_version}-${i}`}>{event.report_id} v{event.report_version} · {event.state}{event.blockers?.length ? ` · ${event.blockers.join(', ')}` : ''}</li>)}</ul>
      {data.feed.gaps.map((gap, i) => <p key={i}>Feed blocker: {gap.state}</p>)}
    </details>}
    {data?.headline_export && <p role="note">Headline handoff: {data.headline_export.source_rows_scanned} source rows inspected · {data.headline_export.eligible_rows} permitted projections · {data.headline_export.missing_rows} named gaps. {data.headline_export.coverage}</p>}
    {data?.headline_export && <p>Independent acquired items: {data.headline_export.independent_items ?? 0} · Main-origin recirculation: {data.headline_export.main_origin_recirculated_items ?? 0}. Counts describe the latest bounded batch.</p>}
    {data?.source_inventory && <p>Retained permitted inventory: {data.source_inventory.independent_items} independent · {data.source_inventory.main_origin_recirculated_items} Main-origin recirculated projections.</p>}
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
