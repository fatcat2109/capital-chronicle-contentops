import { ResearchPackageDecision } from './ResearchPackageDecision';
import { EvolvingStoryWorkspace } from './EvolvingStoryWorkspace';
import { useEffect, useRef, useState } from 'react';
import type { ReportWorkspaceData, MaintainedNativeStory, OwnerReviewContext } from '../dailyAppTypes';

const DESTINATIONS = ['telegram', 'discord', 'x', 'linkedin', 'facebook_page', 'instagram_business', 'threads', 'youtube'];
const display = (value: string) => value.replace(/_/g, ' ');
const retainedSourceDate = (source: { published_at_source?: string; published_at_utc: string }) =>
  /^(?:\d{4}-\d{2}-\d{2}|(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4})$/.test(source.published_at_source ?? '')
    ? `${source.published_at_source} (date only; release time not supplied)`
    : source.published_at_utc || 'Không cung cấp ngày xuất bản';
const sourceDecision: Record<string, string> = {
  USE_UNCHANGED: 'Giữ nguyên bài', MATERIAL_FOLLOW_UP: 'Cần bài tiếp nối',
  CORRECTION_OR_WITHDRAWAL: 'Cần sửa hoặc rút phạm vi cũ', STALE_OR_SOURCE_GAP: 'Còn thiếu nguồn mới',
  EDITORIAL_REVISION: 'Editorial refinement of retained facts',
  RETAIN_EXACT_BYTES_DATED_SUPPORT: 'Giữ ảnh đã kiểm tra với nguồn có ngày cũ',
  REVALIDATE_CHANGED_SUPPORT: 'Kiểm tra lại ảnh theo nguồn đã đổi',
};
function InlineCopy({ text }: { text: string }) {
  return <>{text.split(/(\*\*[^*]+\*\*|\[[^\]]+\]\(https:\/\/[^)\s]+\))/g).map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={i}>{part.slice(2, -2)}</strong>;
    const link = /^\[([^\]]+)\]\((https:\/\/[^)\s]+)\)$/.exec(part);
    return link ? <a key={i} href={link[2]} target="_blank" rel="noreferrer">{link[1]}</a> : part;
  })}</>;
}
function ArticleParagraphs({ text }: { text: string }) {
  return <div>{text.replace(/\[\[SOURCE:(SOURCE_\d+)\]\]/g, '[$1]').split(/\n\s*\n/).map((block, i) =>
    /^#{1,6}\s/.test(block) ? <h4 key={i}>{block.replace(/^#{1,6}\s+/, '')}</h4>
      : block.startsWith('- ') ? <ul key={i}><li><InlineCopy text={block.slice(2)} /></li></ul>
      : <p key={i} style={{ overflowWrap: 'anywhere', whiteSpace: 'pre-line' }}><InlineCopy text={block} /></p>)}</div>;
}
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

type EditorialMedia = NonNullable<NonNullable<ReportWorkspaceData['native_edition']>[number]['media_assets']>[number];
function MediaFigure({ asset: a, originalHref, readerDetails = true }: { asset: EditorialMedia; originalHref?: string; readerDetails?: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const opener = useRef<HTMLAnchorElement>(null);
  useEffect(() => {
    if (!expanded || !dialog.current) return;
    dialog.current.showModal();
    return () => { opener.current?.focus(); };
  }, [expanded]);
  const credit = a.reader_credit ?? a.attribution;
  const caption = a.reader_caption ?? a.caption;
  const embeddedCredit = a.modality === 'documentary_photo' && credit && a.source_page_url?.startsWith('https://')
    ? caption.indexOf(credit) : -1;
  const sources = a.modality === 'source_backed_chart' ? a.source_links ?? [] : [];
  const imageHref = originalHref ?? a.preview_data_url;
  return <figure data-media-asset={a.asset_id}>
    {a.preview_data_url && <a ref={opener} className="media-zoom" href={imageHref} target="_blank" rel="noreferrer" aria-label={`View full-size ${a.alt_text ?? a.caption}`}
      onClick={event => { if (!originalHref || a.modality === 'source_backed_chart') { event.preventDefault(); setExpanded(true); } }}>
      <img src={a.preview_data_url} alt={a.alt_text ?? a.caption} style={{ width: '100%', maxWidth: a.width ?? '100%', height: 'auto' }} />
    </a>}
    <figcaption>{embeddedCredit >= 0 ? <>{caption.slice(0, embeddedCredit)}
      <a href={a.source_page_url} target="_blank" rel="noreferrer">{credit}</a>{caption.slice(embeddedCredit + credit!.length)}</> : caption}{sources.length ? <> · {sources.length > 1 ? 'Sources: ' : 'Source: '}
      {sources.map((source,index) => <span key={source.document_id}>{index > 0 && '; '}
        <a href={source.url} target="_blank" rel="noreferrer">{source.label}</a></span>)}</>
      : credit && embeddedCredit < 0 && <> · {a.source_page_url?.startsWith('https://')
      ? <a href={a.source_page_url} target="_blank" rel="noreferrer">{credit}</a> : credit}</>}
      {a.license_url?.startsWith('https://') && <> · <a href={a.license_url} target="_blank" rel="noreferrer">{a.license_name ?? 'Reuse terms'}</a></>}
      {readerDetails && a.support_caption && <p style={{ margin: '8px 0' }}>{a.support_caption}</p>}
    {readerDetails && a.reader_table && <div className="media-reference-table" style={{ margin: '20px 0' }}>
      <table aria-label={a.reader_table.caption} style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed', fontSize: '0.9rem' }}>
        <caption style={{ textAlign: 'left', fontWeight: 650, paddingBottom: 10 }}>{a.reader_table.caption} · {a.reader_table.unit}</caption>
        <colgroup><col style={{ width: '52%' }} />{a.reader_table.columns.map(column => <col key={column} style={{ width: `${48 / a.reader_table!.columns.length}%` }} />)}</colgroup>
        <thead><tr><th scope="col" style={{ textAlign: 'left', padding: '9px 8px 9px 0', borderBottom: '1px solid #a8bab4' }}>Measure</th>
          {a.reader_table.columns.map(column => <th key={column} scope="col" style={{ textAlign: 'right', padding: '9px 0 9px 8px', borderBottom: '1px solid #a8bab4' }}>{column}</th>)}</tr></thead>
        <tbody>{a.reader_table.rows.map(row => <tr key={row.label}>
          <th scope="row" style={{ textAlign: 'left', fontWeight: 500, padding: '10px 8px 10px 0', borderBottom: '1px solid #d9e1db', overflowWrap: 'anywhere' }}>{row.label}</th>
          {row.values.map((value, index) => <td key={index} style={{ textAlign: 'right', padding: '10px 0 10px 8px', borderBottom: '1px solid #d9e1db', fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap' }}>{new Intl.NumberFormat('en-US', { maximumFractionDigits: 3 }).format(value)}</td>)}
        </tr>)}</tbody>
      </table>
      {a.reader_table.notes.map(note => <p key={note} style={{ fontSize: '0.85rem', margin: '8px 0' }}>{note}</p>)}
    </div>}
    </figcaption>
    {expanded && <dialog ref={dialog} aria-modal="true" aria-label={`Full-size ${a.alt_text ?? a.caption}`}
      onCancel={event => { event.preventDefault(); setExpanded(false); }}
      onKeyDown={event => {
        if (event.key === 'Escape') setExpanded(false);
        if (event.key === 'Tab' && !event.ctrlKey && !event.metaKey && !event.altKey) {
          event.preventDefault(); event.currentTarget.querySelector('button')?.focus();
        }
      }}
      style={{ position: 'fixed', inset: 0, width: '100vw', height: '100vh', maxWidth: 'none', maxHeight: 'none', margin: 0, zIndex: 20, overflow: 'auto', background: '#faf9f5' }}>
      <button type="button" autoFocus onClick={() => setExpanded(false)}>Close image</button>
      <img src={a.preview_data_url} alt={a.alt_text ?? a.caption} style={{ display: 'block', width: a.width ?? 'auto', maxWidth: 'none', height: 'auto' }} />
    </dialog>}
  </figure>;
}

function ArticleWithMedia({ text, assets = [], originals }: { text: string; assets?: EditorialMedia[]; originals?: Record<string, string> }) {
  const sections = text.split(/(?=^#{1,6}\s)/m).filter(Boolean);
  const placed = new Set<string>();
  const figure = (a: EditorialMedia) => <MediaFigure key={a.asset_id} asset={a} originalHref={originals?.[a.sha256]} />;
  return <>
    {assets.filter(a => a.modality === 'documentary_photo' && !a.placement_after).map(figure)}
    {sections.map((section, i) => {
      const heading = /^#{1,6}\s+([^\n]+)/.exec(section)?.[1].trim();
      const inline = assets.filter(a => !!heading && a.placement_after === heading);
      inline.forEach(a => placed.add(a.asset_id));
      return <div key={i}><ArticleParagraphs text={section.trim()} />{inline.map(figure)}</div>;
    })}
    {assets.filter(a => (a.modality !== 'documentary_photo' || a.placement_after) && !placed.has(a.asset_id)).map(figure)}
  </>;
}
function PackagePreview({ payload, assets = [], originals }: { payload: Record<string, unknown>; assets?: EditorialMedia[]; originals?: Record<string, string> }) {
  const posts = Array.isArray(payload.posts) ? payload.posts as Array<Record<string, unknown>> : [];
  const ids = new Set([...(Array.isArray(payload.media_asset_ids) ? payload.media_asset_ids : []),
    ...posts.flatMap(p => Array.isArray(p.media_asset_ids) ? p.media_asset_ids : [])]);
  const attached = assets.filter(a => ids.has(a.asset_id));
  // Display a complete photo attribution once, beside its image. The actual channel
  // payload is immutable and keeps its standalone credit, license and archive caveat.
  // Unknown/changed credits and missing images stay in the copy rather than being stripped.
  const figureCredits = new Set(attached.filter(a => a.preview_data_url && a.modality === 'documentary_photo'
    && a.reader_caption && (a.reader_credit ?? a.attribution) && a.license_url?.startsWith('https://')
    && a.source_page_url?.startsWith('https://')).flatMap(a => {
    // The compact transport uses the creator, while the figure may carry a fuller archive credit.
    const creator = 'creator_publisher' in a && typeof a.creator_publisher === 'string'
      ? a.creator_publisher.trim().replace(/\.$/, '') : '';
    return [a.reader_credit ?? a.attribution, creator].filter(Boolean).map(credit =>
      `Photo: [${credit}](${a.source_page_url}) · [${a.license_name ?? 'Reuse terms'}](${a.license_url}). ${a.reader_caption}`);
  }));
  const readingText = (text: string) => text.split(/\n\s*\n/).filter(block => !figureCredits.has(block.trim())).join('\n\n');
  return <>
    {posts.length ? posts.map((p, index) => <div key={index} data-preview-post={index}>
      <p><strong>{index === 0 ? 'Root post' : `Reply ${index}`}</strong></p>
      <ArticleParagraphs text={readingText(previewText({ text: p.text }))} />
    </div>) : <ArticleParagraphs text={readingText(previewText(payload))} />}
    {attached.map(a => <MediaFigure key={a.asset_id} asset={a} originalHref={originals?.[a.sha256]} readerDetails={false} />)}
  </>;
}

const storyState: Record<string, string> = { NEW: 'New story', UPDATE: 'Updated story', KEEP: 'Keep dated view',
  HOLD: 'Source gap — follow-up held', CORRECTION_OR_WITHDRAWAL: 'Correction or withdrawn scope' };
const datedAge = (seconds: number | null) => seconds === null ? 'age unavailable' : seconds < 3600
  ? 'less than an hour old' : seconds < 86400 ? `${Math.floor(seconds / 3600)} hours old` : `${Math.floor(seconds / 86400)} days old`;
function MaintainedStories({ stories }: { stories: MaintainedNativeStory[] }) {
  return <section aria-label="Maintained stories">
    <h2>Stories to follow</h2>
    <p>Open a story to see its dated view, what changed and the next useful observation. Earlier accepted copy remains readable. These are editorial records, not live market alerts or published output.</p>
    {stories.map(story => <details key={story.story_identity} id={'story-' + story.story_identity} data-maintained-story={story.story_identity} className="report-copy">
      <summary><strong>{story.title}</strong> · {storyState[story.state] ?? display(story.state)} · {story.versions.length} accepted {story.versions.length === 1 ? 'version' : 'versions'}</summary>
      <p><strong>Reader question:</strong> {story.reader_question ?? 'Not recorded in this accepted version.'}</p>
      <p>{story.current_view}</p>
      {story.countercase && <p><strong>Competing explanation and limits:</strong> {story.countercase}</p>}
      <p>Analysis as of {story.current_version.analysis_as_of_utc ?? 'not recorded'} · {datedAge(story.current_version.analysis_age_seconds)}.</p>
      <h3>What changed</h3>
      {story.lineage_gap && <p role="status">The exact prior version is unavailable in this readback. No replacement ancestry is inferred.</p>}
      <p>{story.change.summary ?? 'No source comparison has been recorded for this version. Its age alone establishes neither a material change nor current confirmation.'}</p>
      {story.latest_assessment && <div><h4>Latest source assessment</h4><p>{story.latest_assessment.summary}</p>
        <p>Assessment cutoff: {story.latest_assessment.cutoff_utc}. This later assessment does not erase the change between accepted versions.</p>
        {story.latest_assessment.missing_sources.map((s, i) => <p key={i}>{display(s.status)} · <a href={s.url}>Unresolved source check</a></p>)}
      </div>}
      {story.change.source_changes.length > 0 && <details><summary>Changed source propositions</summary>
        {story.change.source_changes.map((d, i) => <div key={d.item_id + i}><p>{display(d.state)}</p>
          {d.before?.proposition && <p>Prior source: {d.before.proposition}</p>}
          {d.after?.proposition && <p>Accepted source: {d.after.proposition}</p>}</div>)}
      </details>}
      {story.change.interpretation_changed && <details><summary>Interpretation changed between accepted versions</summary>
        <p>Prior interpretation: {story.change.prior_interpretation ?? 'Not separately recorded.'}</p>
        <p>Current interpretation: {story.change.current_interpretation ?? 'Not separately recorded.'}</p>
        <p>This compares authored analysis; a change in wording does not establish a new market fact.</p>
      </details>}
      {story.change.coverage_complete === false && <div role="status"><p>Source coverage is partial. Retained support does not resolve the missing checks.</p>
        {story.change.missing_sources.map((s, i) => <p key={i}>{display(s.status)} · <a href={s.url}>Named source gap</a></p>)}</div>}
      <h3>What to follow next</h3><p>{story.next_observation ?? 'No substantive next observation is recorded. Review the exact dated source before requesting new copy.'}</p>
      {story.next_observation_details && <div>
        <p>Expected disclosure date: {story.next_observation_details.expected_at_utc ?? 'Unknown — no date established by the retained source.'}</p>
        <p>Thesis test: {story.conditional_thesis_test ?? 'Not separately recorded.'}</p>
        <p>{story.next_observation_details.missing_evidence}</p>
        {story.next_observation_details.sources.map(url => <p key={url}><a href={url}>Observation source context</a></p>)}
      </div>}
      <p>Last source assessment: {story.current_version.last_source_check_utc ?? 'not recorded'}. {story.current_version.source_check_scope}</p>
      <h3>Accepted versions and source support</h3>
      {[...story.versions].reverse().map((version, index) => <details key={version.article_identity} data-story-version={version.article_identity}>
        <summary>{index === 0 ? 'Current accepted version' : 'Prior accepted version'} · {version.article.title}</summary>
        <p>Accepted {version.accepted_at_utc ?? 'time not recorded'} · analysis as of {version.analysis_as_of_utc ?? 'not recorded'}.</p>
        <p>Review: {version.review?.decision ?? 'not reviewed'} · Publication: {version.publication?.state ?? 'not prepared'} · {version.previews.length}/8 destination previews.</p>
        {version.prepared_state && <p role="status">The prior preparation is invalidated by its source review. The original text remains history.</p>}
        <p>{version.review?.rationale}</p>
        <h4>Source support and age</h4>
        {version.source_dates.map(s => <p key={s.source_id}>{s.publisher} · {s.clock_kind === 'MAIN_REPORT_CUTOFF' ? 'Main report cutoff, not source publication: ' : ''}{retainedSourceDate({ published_at_utc: s.published_at_utc ?? '', published_at_source: s.published_at_source ?? undefined })} · {datedAge(s.age_seconds)}<br />
          {s.url?.startsWith('https://') && <a href={s.url}>Read dated source</a>}</p>)}
        <p>Report attribution and underlying event confirmation remain distinct. A newer check does not change the source's publication date.</p>
        {!version.media_assets?.length && <p>Media gap: no inspected, rights-cleared image is bound. Text previews remain available.</p>}
        {version.media_assets?.map(a => <figure key={a.asset_id}>{a.preview_data_url && <img src={a.preview_data_url} alt={a.alt_text ?? a.caption} style={{ width: '100%', height: 'auto' }} />}<figcaption>{a.caption}</figcaption></figure>)}
        <details><summary>Full accepted article and SEO</summary><h4>{version.article.title}</h4><p>{version.article.dek}</p>
          <ArticleParagraphs text={version.article.substack_body_markdown} />
          <p>Search title: {version.article.search_title ?? 'not recorded'}</p><p>{version.article.meta_description}</p>
        </details>
        <details><summary>Eight destination packages</summary>{version.previews.map(p => <details key={p.preview_id}><summary>{display(p.destination)}</summary><ArticleParagraphs text={previewText(p.payload)} /></details>)}</details>
        <details><summary>Exact revision and publication record</summary><p>Article identity: {version.article_identity}</p><p>Operation: {version.run_id}</p>
          <p>Preparation: {version.prepared_state ?? version.publication?.state ?? 'not prepared'}. Review and preparation create no public post.</p>
          {version.publication?.destinations.map(d => <p key={d.destination}>{display(d.destination)}: {display(d.status)}{d.public_object_url && <> · <a href={d.public_object_url}>Observed object</a></>}</p>)}
        </details>
      </details>)}
    </details>)}
  </section>;
}

const channelNames: Record<string, string> = { telegram: 'Telegram', discord: 'Discord', x: 'X', linkedin: 'LinkedIn',
  facebook_page: 'Facebook Page', instagram_business: 'Instagram Business', threads: 'Threads', youtube: 'YouTube Community' };

function OwnerEditionReview({ data, context }: { data?: ReportWorkspaceData; context?: OwnerReviewContext }) {
  const edition = data?.owner_edition;
  const articles = edition?.operation_ids.flatMap(id => data?.native_edition?.filter(i => i.run_id === id) ?? []) ?? [];
  const [position, setPosition] = useState(0);
  const [channel, setChannel] = useState('canonical');
  const [releaseOpen, setReleaseOpen] = useState(false);
  const item = articles[position];
  const selectStory = (index: number) => { setPosition(index); setChannel('canonical'); };
  if (!edition || !item) return <section role="status"><h2>No selected owner edition</h2>
    <p>This read-only export has no selected articles. Ask the existing ContentOps owner to open the intended edition; no replacement content has been generated.</p></section>;
  const preview = item.previews.find(p => p.destination === channel);
  const pub = item.publication;
  const undispatched = articles.reduce((sum, a) => sum + (a.publication?.destinations.filter(d => d.status === 'NOT_DISPATCHED').length ?? 0), 0);
  return <section className="owner-review" aria-label="Private owner review">
    <header className="owner-intro" id="review-top">
      <p className="eyebrow">Capital Chronicle</p><h1>Newsroom</h1>
      <p className="review-mode" role="status"><strong>Private, read-only preview.</strong></p>
      <details><summary>Edition status</summary>
        <p className="review-counts">{edition.ready} ready · {edition.missing} missing · {edition.held} held · {edition.preview_count} channel previews · {undispatched} destination states not dispatched</p>
        <p>Snapshot: {context?.captured_at_utc ?? 'capture time not supplied'}. Source dates remain their original dates; these examples are not a production day.</p>
      </details>
      <nav className="guide-links" aria-label="Review guide"><a href="#how-v1-works">How V1 works</a>
        <a href="#release-decision" onClick={() => setReleaseOpen(true)}>Activation boundary</a></nav>
    </header>
    <div className="reading-controls">
      <label>Story <select aria-label="Choose story" value={position} onChange={e => selectStory(Number(e.target.value))}>
        {articles.map((a, i) => <option value={i} key={a.article_identity}>{i + 1}. {a.article.title}</option>)}</select></label>
      <div className="story-step"><button type="button" onClick={() => selectStory(position - 1)} disabled={position === 0}>Previous story</button>
        <span aria-live="polite">{position + 1} of {articles.length}</span>
        <button type="button" onClick={() => selectStory(position + 1)} disabled={position === articles.length - 1}>Next story</button></div>
      <label>Reading view <select aria-label="Choose reading view" value={channel} onChange={e => setChannel(e.target.value)}>
        <option value="canonical">Canonical article · Substack</option>
        {DESTINATIONS.map(d => <option key={d} value={d}>{channelNames[d]}</option>)}</select></label>
    </div>
    <article className="report-copy owner-article" data-owner-story={item.run_id} data-reading-view={channel} aria-label="Selected article">
      <h2>{channel === 'canonical' ? item.article.title : channelNames[channel]}</h2>
      {channel === 'canonical' && <><p className="article-dek">{item.article.dek}</p>
        {item.article.display_date && <p className="article-date">{item.article.display_date}</p>}</>}
      {channel === 'canonical' ? <>
        <ArticleWithMedia text={item.article.substack_body_markdown} assets={item.media_assets} originals={context?.original_media_links} />
      </> : preview ? <>
        <PackagePreview payload={preview.payload} assets={item.media_assets} originals={context?.original_media_links} /></> : <p role="status">No package is recorded for this destination.</p>}
      <details className="dated-sources" aria-label="Dated sources"><summary>Sources and dates</summary>
        <p>{item.article.source_date_notice}</p>
        {item.evidence?.map(s => <p key={s.source_id}><strong>{s.source_id} · {s.publisher}</strong><br />{retainedSourceDate(s)}<br />
          {s.url.startsWith('https://') ? <a href={s.url} target="_blank" rel="noreferrer">Read original source</a> : 'Retained public report; no external source URL recorded.'}</p>)}
        <p>A source check does not create a new event. Attributed reporting and independently confirmed event truth remain distinct.</p>
      </details>
    </article>
      <details className="owner-record"><summary>Owner record: review and preparation</summary>
        <p>Editorial review: {item.review?.decision ?? 'not recorded'} · Preparation: {pub?.state ?? 'not prepared'} · Not published</p>
        <p>Search title: {item.article.search_title ?? 'not separately recorded'}</p>
        <p>{item.article.meta_description}</p><p>Slug: {item.article.canonical_slug_candidate ?? 'not separately recorded'}</p><p>{item.review?.rationale}</p>
        <p>Article identity: <code>{item.article_identity}</code></p><p>Operation: <code>{item.run_id}</code>.</p>
        <p>These isolated manual examples have no dispatch authority. KEEP and PREPARED do not establish publication or current account readiness.</p>
        {pub?.destinations.map(d => <p key={d.destination}>{d.destination === 'substack' ? 'Substack' : channelNames[d.destination] ?? d.destination}: {display(d.status)} · readiness {display(d.cached_readiness)}</p>)}
      </details>
    <section className="owner-guide" id="how-v1-works"><h2>What you are reviewing</h2>
      <p>V1 turns admitted public reporting and public-safe Capital Chronicle research into a sourced article, lawful contextual photography and eight channel-specific packages. Substantial analysis uses two to five distinct useful charts drawn from primary data. A news or policy story may omit charts when no defensible useful comparison exists; its editorial reason stays in the record.</p>
      <details><summary>How to use the working manual newsroom</summary>
        <p>In the existing ContentOps Codex chat, ask: “Prepare an article about [your question]” or “Continue the existing [story]”. Codex uses the configured manual newsroom entry, handles the native requests and returns the reader. Resume the same operation after interruption; a changed question gets its own identity.</p>
        <p>Sol6.1 Light selects and prepares evidence and proposes visuals. Sol6.1 MAX decides the argument, data, chart forms, count and placement, then writes prose and SEO in that same context. A bounded revision stays with that writer. Luna MAX filters genuinely new X intake. Code retrieves, computes, renders and validates. Source changes invalidate affected review/preparation while preserving history.</p>
        <p>This offline file shows the selected edition. It does not send a question, run a model, refresh sources or record KEEP. Give revision/review instructions to the existing owner in Codex; no JSON assembly is needed from you.</p>
        <details><summary>Existing operator entry</summary><code>python scripts/run_native_desktop_editorial.py newsroom --operation-id &lt;stable-id&gt; --request-file &lt;UTF-8 request&gt;</code>
          <p><code>desk</code> reopens an export of the existing owner edition. Manual preparation remains isolated from production.</p></details>
      </details>
      <details><summary>What the release review checks</summary><ol>
        <li>People-first SEO and house voice: supported titles, descriptions and readable original copy; ranking remains unknown.</li>
        <li>Reporting quality: fact-led thesis, mechanism, serious countercase and next evidence, assessed against the existing publication study; no publisher-parity certification.</li>
        <li>Evidence-led analysis: exact source support and truthful dates; attributed reports remain distinct from confirmed events.</li>
        <li>Authentic lawful photographs: relevant archive context, exact identity/date/credit/license and inspected pixels.</li>
        <li>Useful quantitative charts: exact signed values, units, periods and actual/estimate/forecast or announced-setting distinctions.</li>
        <li>Existing V1 scope: eight modes, native roles, public-safe intake, review/history/corrections, canonical plus eight packages, recovery, four windows, privacy and guarded learning. Live operational dimensions remain unobserved.</li>
      </ol>{context?.acceptance_href && <a href={context.acceptance_href}>Exact acceptance matrix and evidence</a>}</details>
      <details><summary>Held story, history and measured availability</summary>
        {edition.held_candidates.map((h, i) => <p key={i}><strong>Held: {h.title}.</strong> {h.reason}</p>)}
        <p>Original articles, source captures, review versions and held candidates remain history. Revised copy and media need their own current review; a later capture does not create a new event.</p>
        <p>Real audience samples: {context?.audience?.sample_count ?? 'unavailable'}. Content: {context?.audience ? display(context.audience.content_state) : 'not supplied'}.
          Search: {context?.audience ? display(context.audience.search_state) : 'not supplied'}. Destination metrics: {context?.audience ? display(context.audience.destination_state) : 'not supplied'}.</p>
        <p>No traffic improvement, SEO ranking, audience uplift or publisher parity is inferred. Sustained output and platform behavior require actual authorized operation.</p>
        {context?.history_href && <a href={context.history_href}>Preserved historical evidence</a>}
      </details>
    </section>
    <details id="release-decision" className="release-decision" open={releaseOpen} onToggle={e => setReleaseOpen(e.currentTarget.open)}>
      <summary>Production activation needs Jim's decision</summary>
      <p>Private article acceptance does not enable production. Jim's remaining decision must name the code to deploy,
        whether to enable the same four newsroom windows, and the permitted publication destinations. Production,
        schedules, publication and V2/V3 remain paused until their respective authority changes.</p>
      <p>Fresh production articles require current sources, lawful media and exact review. These dated private examples
        are not copied into production or credited as a new production day.</p>
      <p>The existing coordinator publishes Substack first, reads it back, then prepares the eight derivatives with
        the real article URL. An uncertain write stops retries until readback and reconciliation.</p>
      <p>Calendar execution, published output and audience/search results require actual operating evidence.
        Private previews establish none of those results.</p>
      {context?.accepted_delivery_head && <p>Reviewed code: <code>{context.accepted_delivery_head}</code></p>}
    </details>
    <p className="review-footer"><a href="#review-top">Back to story navigation</a> · Close and reopen this HTML file to return; no preview process or local server is required.</p>
  </section>;
}

export function ReportEditorialWorkspace({ data, mode = 'workspace', reviewContext }: { data?: ReportWorkspaceData; mode?: 'workspace' | 'owner-review'; reviewContext?: OwnerReviewContext }) {
  if (mode === 'owner-review') return <OwnerEditionReview data={data} context={reviewContext} />;
  return <FullReportEditorialWorkspace data={data} />;
}

function FullReportEditorialWorkspace({ data }: { data?: ReportWorkspaceData }) {
  const [selected, select] = useState('');
  const [family, setFamily] = useState('ALL');
  const library = data?.foundation_library;
  const workspaces = data?.workspaces?.length ? data.workspaces : data ? [data] : [];
  const workspace = workspaces.find(w => w.latest_report?.report_id === selected) ?? workspaces[0];
  const report = workspace?.latest_report;
  const result = workspace?.latest_simple_result;
  const controlled = result?.model_execution_state === 'INJECTED_REPLAY_ONLY';
  const current = data?.owner_edition;
  const articles = current ? current.operation_ids.flatMap(id => data?.native_edition?.filter(i => i.run_id === id) ?? []) : data?.native_edition;
  const history = current ? data?.native_edition?.filter(i => !current.operation_ids.includes(i.run_id)) : [];
  const learning = data?.audience_learning;
  const policy = learning?.current?.policy;
  return <section className="daily-panel report-workspace" aria-label="Capital Chronicle report workspace" style={{ overflowWrap: 'anywhere', minWidth: 0 }}>
    <header><span>Editorial workspace</span><h2>{data?.maintained_stories?.length ? 'ContentOps story desk' : current?.title ?? 'Capital Chronicle report → article → previews'}</h2></header>
    {!!data?.maintained_stories?.length && <MaintainedStories stories={data.maintained_stories} />}
    <details><summary>Editorial method and operating boundary</summary><p>Luồng biên tập đích: Luna MAX lọc headline → 6.1 Sol Light chọn góc và chuẩn bị nguồn → 6.1 Sol MAX viết bài và SEO, tối đa một lượt sửa cùng writer. Lịch production giữ pause; chỉ bằng chứng thực thi mới xác nhận model đã chạy.</p></details>
    {current && <section aria-label="Tình trạng ấn bản"><p><strong>{current.ready} bài sẵn đọc · {current.held} đề tài giữ chờ · {current.missing} bài còn thiếu</strong> · {current.preview_count} bản xem trước · chưa xuất bản.</p>
      {current.opportunity_counts && <p aria-label="Kết quả cơ hội biên tập">{current.opportunity_counts.new} bài mới · {current.opportunity_counts.update} cập nhật · {current.opportunity_counts.keep} giữ nguyên · {current.opportunity_counts.hold} giữ chờ · {current.opportunity_counts.source_blocked} thiếu nguồn (trong các quyết định trên). Bài giữ nguyên không tính là bài mới.</p>}
      {current.opportunity_outcomes?.map(o => <p key={o.operation_id}>{o.reason}</p>)}
      {current.held_candidates.map((h, i) => <details key={i}><summary>Giữ chờ: {h.title}</summary><p>{h.reason}</p></details>)}
      <nav aria-label="Mục lục ấn bản">{articles?.map(a => <p key={a.article_identity}><a href={'#article-' + a.article_identity}>{a.article.title}</a></p>)}</nav>
    </section>}
    {learning && <section aria-label="Audience learning" className="report-copy">
      <h3>Audience feedback and next research</h3>
      {policy && <p><strong>{display(policy.decision ?? 'Unavailable')}</strong> · {policy.sample_count} distinct article samples · confidence {policy.confidence.toFixed(3)}. {display(policy.decision_reason ?? '')}</p>}
      <p>Preferences guide future selection, SEO and native copy. Evidence, uncertainty and source requirements still apply. Unavailable metrics stay unknown.</p>
      {learning.current?.feedback.map(f => <div key={f.observation_id}><p>{display(f.semantic_state)} · observed {f.collected_at_utc}. Scheduled checkpoint: {f.scheduled_for_utc}; a later read does not reconstruct that historical checkpoint.</p>
        <p>{Object.entries(f.native_metrics ?? {}).map(([k, v]) => `${display(k)}: ${v === null ? 'unavailable' : v}`).join(' · ')}</p></div>)}
      {learning.follow_up_briefs.map((b, i) => <div key={b.run_id ?? i}><p>{b.feedback_effect}</p>
        {b.brief_candidate && <p><strong>{b.brief_candidate.working_headline}</strong> · Observed reader question for source research; no factual answer or reply is authorized.</p>}
        <ol>{b.ranked_questions?.map(q => <li key={q.candidate_id}><strong>{q.question}</strong><p>{q.action} <a href={'#article-' + q.exact_article_match.article_identity}>Retained article</a></p><p>Evidence still needed: {q.missing_evidence.join('; ')}</p></li>)}</ol>
        <p>Next: {b.next_operation}</p>
      </div>)}
      <details><summary>Frozen learning context</summary>{learning.opportunities.map(o => <p key={o.run_id}>{o.run_id} · policy {o.policy.policy_version ?? 'unavailable'} · {o.feedback_count} dated feedback records. {o.next_operation}</p>)}</details>
    </section>}
    {!!data?.main_admission_summary?.length && <details><summary>Báo cáo Main mới nhất đã tiếp nhận</summary>
      <p>Đã kiểm tra liên kết nội dung công khai. Xác nhận model của bên tạo báo cáo chưa phải bằng chứng độc lập về phiên chạy model.</p>
      {data.main_admission_summary.map(r => <p key={r.report_id}>{r.report_id.replace('asset-report:', '')} v{r.report_version} · {r.claims} luận điểm được phép · {r.native_public_excerpts} trích đoạn có xác nhận model từ Main · {r.known_at_cutoff_utc ? 'mốc báo cáo ' + r.known_at_cutoff_utc : 'chưa lưu mốc báo cáo'}.</p>)}
    </details>}
    {!!articles?.length && <section aria-label="Ấn bản newsroom"><h3>Ấn bản newsroom · đọc và duyệt</h3>
      <p>Các bài đã qua validator; quyết định biên tập gắn với đúng bản bài. Chưa xuất bản.</p>
      {articles?.map(item => <article id={'article-' + item.article_identity} key={item.article_identity} className="report-copy" data-edition-run={item.run_id}>
        <h3>{item.article.title}</h3><p>{item.article.dek}</p>
        <p><strong>{item.review?.decision ?? 'Chờ đọc duyệt'}</strong> · {item.reader_question}</p>
        {item.prepared_state && <p role="status">The retained article remains available. This copy, source or media revision needs a current review before preparation.</p>}
        {item.source_review && <p>{sourceDecision[item.source_review.decision] ?? display(item.source_review.decision)}: {item.source_review.reader_change_summary}</p>}
        {item.report_id && <p>Bổ sung từ {item.report_id} bản {item.report_version}; phân tích Main có điều kiện, không phải xác nhận độc lập.</p>}
        <details open><summary>Đọc toàn bài</summary><ArticleWithMedia text={item.article.substack_body_markdown} assets={item.media_assets} /></details>
        <details><summary>Góc bài và quyết định đọc duyệt</summary><p>{item.angle ?? item.mode}</p><p>{item.review?.rationale}</p></details>
        {item.article.search_title && <details><summary>SEO và ngày nguồn</summary><p>{item.article.search_title}</p><p>{item.article.meta_description}</p><p>Slug: {item.article.canonical_slug_candidate}</p><p>{item.article.source_date_notice}</p></details>}
        <details><summary>Nguồn và ngày</summary>{item.evidence?.map(s => <p key={s.source_id} style={{ overflowWrap: 'anywhere' }}>
          {s.source_id} · {s.publisher} · {retainedSourceDate(s)} · {s.published_at_source === 'MAIN_REPORT_CUTOFF_NOT_SOURCE_RELEASE_TIME' ? 'Mốc báo cáo Main, không phải ngày phát hành nguồn' : 'Nguồn lưu giữ có ngày riêng'}<br />
          {s.url.startsWith('https://') ? <a href={s.url} target="_blank" rel="noreferrer">Đọc nguồn gốc</a> : 'Bản báo cáo công khai có định danh bất biến'}
        </p>)}</details>
        <p role="status">Release media: {item.release_media?.state ?? 'NOT VERIFIED'}{item.release_media?.blocker ? ` · ${item.release_media.blocker}` : ''}</p>
        {!item.media_assets?.length && <p role="status">Media gap: no inspected, rights-cleared image is bound to this article. Text previews remain available.</p>}
        <h4>{item.previews.length}/8 bản xem trước theo nền tảng</h4>
        {item.publication && <details aria-label="Publication continuation"><summary>Publication: {display(item.publication.state)}</summary>
          <p>Review and preparation create no public post. {item.publication.operation_scope === 'OWNER_MANUAL_ISOLATED'
            ? 'This manual edition has no dispatch authority.' : 'Dispatch requires existing operating authority and current destination proof.'}</p>
          <p>Next operation: {item.publication.next_operation}</p>
          {item.publication.dispatch_blocker && <p>Dispatch boundary: {display(item.publication.dispatch_blocker)}</p>}
          {item.publication.next_command && <pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{item.publication.next_command}</pre>}
          <p>Cached readiness is diagnostic. Only an actual object readback confirms publication.</p>
          {item.publication.destinations.map(d => <p key={d.destination}>{display(d.destination)}: {display(d.status)}
            {d.reconciliation_status ? ' · ' + display(d.reconciliation_status) : ''}
            {d.blocker ? ' · ' + display(d.blocker) : ''}
            {d.public_object_url && <> · <a href={d.public_object_url}>Observed object</a></>}</p>)}
        </details>}
        {item.previews.map(p => <details key={p.preview_id} data-edition-destination={p.destination}><summary>{display(p.destination)}</summary><div className="report-body"><PackagePreview payload={p.payload} assets={item.media_assets} /></div></details>)}
      </article>)}
    </section>}
    {!!history?.length && <details><summary>Bài và phiên bản trước ({history.length})</summary>{history.map(h => <details key={h.article_identity}><summary>{h.article.title} · {h.prepared_state ? 'chuẩn bị cũ mất hiệu lực' : h.source_review?.decision === 'USE_UNCHANGED' ? 'giữ dùng, không viết lại' : h.review?.decision ?? 'chưa duyệt'}</summary>
      {h.source_review && <p>{sourceDecision[h.source_review.decision] ?? display(h.source_review.decision)}: {h.source_review.reader_change_summary}</p>}
      {h.prepared_state && <p>Quyết định KEEP cũ không còn dùng để chuẩn bị phát hành. Văn bản gốc được giữ để đối chiếu.</p>}
      <ArticleParagraphs text={h.article.substack_body_markdown} />
      {h.evidence?.map(s => <p key={s.source_id}>{s.publisher} · {s.published_at_utc || 'Chưa xác minh ngày công bố'} · {s.url.startsWith('https://') ? <a href={s.url}>Nguồn gốc</a> : 'Báo cáo công khai đã lưu giữ'}</p>)}
      {h.media_assets?.map(a => <figure key={a.asset_id}>{a.preview_data_url && <img src={a.preview_data_url} alt={a.alt_text ?? a.caption} style={{ width: '100%', height: 'auto' }} />}<figcaption>{a.caption}</figcaption></figure>)}
      {h.previews.map(p => <details key={p.preview_id}><summary>{display(p.destination)}</summary><div className="report-body">{previewText(p.payload)}</div></details>)}</details>)}</details>}
    <details open={!current}><summary>Nguồn, sửa đổi và thư viện nghiên cứu</summary>
    {!!data?.source_reviews?.length && <section aria-label="So sánh nguồn và quyết định cập nhật">
      <h3>Nguồn đã thay đổi gì?</h3><p>Bài cũ giữ nguyên trong lịch sử. Đọc lại URL không tạo tuần quan sát mới.</p>
      {data.source_reviews.map(s => <article key={s.review_id} className="report-copy">
        <h4>{s.title}</h4><p><strong>{sourceDecision[s.decision] ?? display(s.decision)}</strong> · {s.reader_change_summary}</p>
        {s.invalidates_prepared_review && <p>Chuẩn bị phát hành bản cũ cần xem lại; chưa được dùng quyết định KEEP trước đây để phát hành.</p>}
        <p>Media: {sourceDecision[s.media_state] ?? display(s.media_state)}.</p>
        <details><summary>Đối chiếu nguồn, ngày và giới hạn</summary>
          {s.source_editions.map(e => <p key={e.item_id}>{e.proposition ?? 'Retained source identity; no new source proposition recorded.'}<br />Quan sát: {e.observation_date ?? 'không ghi'} · Công bố: {e.published_at_utc?.slice(0, 10) ?? 'chưa xác minh'} · Lấy nguồn: {e.retrieved_at_utc ?? 'not separately recorded in this revision'}<br />{e.period_relation ? display(e.period_relation) : 'No new observation period declared'} · {e.rights_state ?? 'See the exact retained source rights record'} · <a href={e.source_url}>Nguồn gốc</a></p>)}
          {s.source_attempts.map((a, i) => <p key={i}>{display(a.status)} · <a href={a.url}>Nguồn đã kiểm tra</a> · {a.observed_at_utc}</p>)}
          {!!s.removed_main_claim_ids.length && <p>Main đã rút: {s.removed_main_claim_ids.join(', ')}.</p>}
        </details>
      </article>)}
    </section>}
    {!!data?.native_article_reviews?.length && <section aria-label="Đọc duyệt bài native Codex"><h3>Đọc duyệt bài native Codex</h3>
      {data.native_article_reviews.map(r => <p key={r.package_revision}>{r.decision}: {r.rationale} · quyết định gắn đúng bản bài; chưa cấp quyền xuất bản.</p>)}
    </section>}
    {library && <section aria-label="Foundation research library">
      {library.stories?.length ? <EvolvingStoryWorkspace stories={library.stories} /> : null}
      <h3>Thư viện nghiên cứu đa tài sản</h3>
      {library.desk && <section aria-label="Bàn quyết định biên tập"><h4>Bàn quyết định biên tập</h4>
        <p>{library.desk.useful_research_packages} gói giữ dùng · {library.desk.decisions.HOLD} giữ chờ · {library.desk.decisions.REVISE} cần sửa · {library.desk.decisions.STALE} hết hiệu lực · {library.desk.decisions.UNREVIEWED} chưa đọc duyệt.</p>
        <p>{library.desk.kind_counts.NEWS} tin có ngày · {library.desk.kind_counts.BACKGROUND} bài nền · {library.desk.kind_counts.ANALYSIS} phân tích. Các loại không cộng thêm vào số gói.</p>
        <p>{library.desk.missing_current_input_coordinates.length} đầu vào hiện tại còn thiếu; {library.desk.affected_work.length} gói có việc cần xử lý qua owner hiện có.</p>
        {library.desk.affected_work.map(w => <p key={w.brief_id}>{w.brief_id}: {w.reason}</p>)}
      </section>}
      <p>{library.counts.useful_families} nhóm · {library.counts.independent_items} luận điểm từ {library.counts.independent_documents ?? 'các'} tài liệu độc lập · {library.counts.briefs} brief biên tập.</p>
      <p>Research-ready · {library.counts.fresh_provider_drafts} fresh-provider drafts · {library.counts.qualified} qualified · {library.counts.published} published. LLM pause giữ nguyên.</p>
      <p>{library.counts.editor_authored_packages ?? 0} gói nghiên cứu do biên tập soạn · {library.counts.native_previews ?? 0} native previews · {library.counts.media ?? 0} media. Quyết định nghiên cứu hiển thị riêng; chưa duyệt xuất bản, không tính là bài native Codex đã chạy.</p>
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
      {library.input_composition && <p>Đầu vào cho {library.input_composition.routine_window_count} cửa sổ hiện có: {library.input_composition.independent_research_items} luận điểm nghiên cứu · {library.input_composition.main_editorial_reports} báo cáo Main có nội dung biên tập · {library.input_composition.main_unchanged_reports} bản không thay đổi · {library.input_composition.main_history_only_reports} bản lịch sử. Chủ biên tập đích là Codex Desktop; lịch production vẫn tạm dừng.</p>}
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
        <p>{item.model_execution_state === 'INJECTED_REPLAY_ONLY' ? 'Controlled output — no fresh provider execution' : item.model_execution_state === 'NATIVE_DESKTOP_REQUEST_RETURN' ? 'Native Codex output recorded' : 'Provider output recorded'} · unpublished</p>
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
        {workspace.media_assets?.map(m => <figure key={m.asset_id}>
          {m.preview_data_url?.startsWith('data:image/png;base64,') && <img src={m.preview_data_url} alt={m.alt_text ?? m.caption} style={{ width: '100%', height: 'auto' }} />}
          <figcaption>{m.caption} · {m.reuse_state === 'EXACT_BYTES_REUSED_NO_RENDER' ? 'Giữ nguyên media đã đọc duyệt' : 'Nguồn media đã giữ'}</figcaption>
        </figure>)}
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
    </details>
  </section>;
}
