// Render the actual canonical React workspace from its owning read model, without a runtime.
import { build } from 'esbuild';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve, relative } from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath, pathToFileURL } from 'node:url';

const [input, output, ...options] = process.argv.slice(2);
if (!input || !output) throw new Error('workspace JSON and HTML output paths required');
const retainedNews = options.includes('--retained-news');
const ownerReview = options.includes('--owner-review') || retainedNews;
const contextIndex = options.indexOf('--context');
const reviewContext = contextIndex < 0 ? { captured_at_utc: new Date().toISOString() }
  : JSON.parse(readFileSync(options[contextIndex + 1], 'utf8'));
const ui = resolve(dirname(fileURLToPath(import.meta.url)), '..');
let inputText = readFileSync(input, 'utf8');
let inputData = JSON.parse(inputText);
if (retainedNews) {
  if (inputData.consumer_view !== 'contentops.retained_news.private_preview.v1' || inputData.scope !== 'PRIVATE_PREVIEW_ONLY')
    throw new Error('PRIVATE_RETAINED_NEWS_ARTIFACT_REQUIRED');
  const articles = inputData.native_edition.filter(item => item.availability === 'AVAILABLE').map(item => ({
    ...item, previews: [], publication: {...item.publication,
      destinations: item.publication.destinations.map(destination => ({...destination, cached_readiness: 'NOT_SUPPLIED'}))},
    media_assets: item.media_assets.map(asset => {
      const {content_base64, preview_content_base64, ...metadata} = asset;
      const encoded = content_base64 ?? preview_content_base64;
      if (createHash('sha256').update(Buffer.from(encoded, 'base64')).digest('hex') !== (content_base64 ? asset.sha256 : asset.preview_sha256))
        throw new Error('RETAINED_NEWS_MEDIA_CHANGED');
      return {...metadata, preview_data_url: `data:${asset.preview_content_type ?? asset.content_type};base64,${encoded}`};
    })
  }));
  inputData = {owner_edition: {...inputData.owner_edition, ready: articles.length,
    held: 0, missing: inputData.native_edition.length - articles.length, held_candidates: [], preview_count: 0,
    publication_authority: false}, native_edition: articles};
  inputText = JSON.stringify(inputData);
}
if (ownerReview) {
  const edition = inputData.owner_edition;
  if (!edition?.operation_ids?.length) throw new Error('EXACT_OWNER_EDITION_REQUIRED');
  const articles = edition.operation_ids.map(id => {
    const matches = (inputData.native_edition ?? []).filter(a => a.run_id === id);
    if (matches.length > 1) throw new Error('DUPLICATE_EDITION_ARTICLE:' + id);
    return matches[0];
  }).filter(Boolean);
  if (!articles.length) throw new Error('EXISTING_EDITION_ARTICLE_REQUIRED');
  const missing = edition.operation_ids.filter(id => !articles.some(a => a.run_id === id));
  // Display projection only: preserve the complete selected records, omit unrelated history.
  // In particular article/previews/media_assets objects are never rewritten for export.
  const data = { owner_edition: edition, native_edition: articles };
  // Link the existing original bytes, keeping reduced preview objects unchanged.
  reviewContext.original_media_links = {};
  for (const article of articles) for (const asset of article.media_assets ?? []) {
    if (retainedNews) continue; // Authored safe artifact embeds bytes; no host path exists.
    const original = resolve(asset.path);
    if (createHash('sha256').update(readFileSync(original)).digest('hex') !== asset.sha256)
      throw new Error('ORIGINAL_MEDIA_BYTES_CHANGED:' + asset.asset_id);
    reviewContext.original_media_links[asset.sha256] = relative(dirname(resolve(output)), original)
      .split('\\').map(encodeURIComponent).join('/');
  }
  const compiled = await build({ stdin: { contents: `
    import React from 'react';
    import {createRoot} from 'react-dom/client';
    import {ReportEditorialWorkspace} from './src/views/ReportEditorialWorkspace.tsx';
    const {data,context} = JSON.parse(document.getElementById('owner-review-data').textContent);
    createRoot(document.getElementById('owner-review-root')).render(
      React.createElement(ReportEditorialWorkspace,{data,mode:'owner-review',reviewContext:context}));
  `, resolveDir: ui, loader: 'tsx' }, bundle: true, write: false, platform: 'browser', format: 'iife',
    jsx: 'automatic', minify: true, define: { 'import.meta.env': '{}', 'process.env.NODE_ENV': '"production"' } });
  const script = compiled.outputFiles[0].text.replace(/<\/script/gi, '<\\/script');
  // Preserve exact numeric spellings (for example4.0) in accepted hash-bound assets.
  // The browser still parses ordinary JSON numbers; this avoids a checksum-only rewrite.
  const rawInput = JSON.parse(inputText, (_key, value, source) =>
    typeof value === 'number' ? JSON.rawJSON(source.source) : value);
  const rawData = { owner_edition: rawInput.owner_edition, native_edition: articles.map(item =>
    rawInput.native_edition.find(a => a.run_id === item.run_id)) };
  const payload = JSON.stringify({ data: rawData, context: reviewContext }).replace(/</g, '\\u003c');
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'">
  <title>Capital Chronicle · Prepared newsroom review</title><style>
  *{box-sizing:border-box;min-width:0}html{scroll-behavior:smooth}body{margin:0;background:#f4f3ee;color:#1c3338;font:17px/1.65 system-ui,Arial,sans-serif}
  main{max-width:1000px;margin:auto;padding:32px 28px 72px}h1,h2,h3{line-height:1.22;letter-spacing:-.02em}h1{font-size:2.4rem;margin:.3em 0}h2{font-size:1.9rem}h3{font-size:1.2rem}p{margin:.85em 0}
  .eyebrow{color:#526b68;font-size:.8rem;letter-spacing:.1em;text-transform:uppercase;font-weight:700}.owner-intro{padding:12px 4px 20px}.review-mode{background:#e6eeea;border-left:4px solid #40746b;padding:14px 18px;border-radius:4px}.review-counts{font-weight:650}.guide-links{display:flex;gap:20px;flex-wrap:wrap}
  a{color:#14685f;text-decoration-thickness:.08em;text-underline-offset:.18em}a,code,p,figcaption{overflow-wrap:anywhere}a:focus-visible,button:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #b96c20;outline-offset:4px}
  .reading-controls{background:#fff;border:1px solid #ced9d1;border-radius:14px;padding:20px;margin:8px 0 24px;display:grid;gap:15px}.reading-controls label{display:grid;gap:6px;font-size:.9rem;font-weight:650}select{width:100%;padding:10px;border:1px solid #9aada7;border-radius:6px;background:#fff;color:inherit;font:inherit}button{font:inherit;padding:9px 14px;background:#fff;border:1px solid #9aada7;border-radius:7px;color:inherit;cursor:pointer}button:disabled{opacity:.4;cursor:default}.story-step{display:flex;justify-content:space-between;align-items:center;gap:10px}.story-step span{font-size:.9rem;white-space:nowrap}
  .report-copy{background:#fff;border:1px solid #ced9d1;border-radius:14px;padding:34px;margin:24px 0}.article-dek{font-size:1.15rem;color:#435c5c}.article-state,.source-notice,.channel-boundary{font-size:.9rem;color:#526764}.dated-sources{border-top:1px solid #d9e1db;margin-top:30px;padding-top:10px}.dated-sources p{font-size:.9rem}
  figure{margin:28px 0}figure>img{display:block;max-height:520px;object-fit:contain;object-position:left center;background:#f6f6f2}img{max-width:100%;height:auto}figcaption{font-size:.8rem;color:#526764;margin:10px 0}.media-enlarge>div{max-height:80vh;overflow:auto!important;background:#edf1ec}.media-enlarge img{max-height:none;object-fit:initial}details{padding:14px 0;border-bottom:1px solid #d9e1db}summary{cursor:pointer;font-weight:650}details p,li{overflow-wrap:anywhere}details details{font-size:.9rem}code{font-size:.82rem}.owner-guide{padding:16px 4px}.owner-guide h2{font-size:1.5rem}.release-decision{background:#e6eeea;border-radius:12px;padding:20px;margin:24px 0}.release-decision>summary{font-size:1.2rem}.review-footer{font-size:.85rem;color:#526764}li{margin:12px 0}
  @media(max-width:600px){body{font-size:16px}main{padding:16px 12px 50px}h1{font-size:1.9rem}h2{font-size:1.55rem}.report-copy{padding:20px 17px}.reading-controls{padding:16px}button{font-size:.85rem;padding:9px}.story-step span{font-size:.8rem}.release-decision{padding:16px}figure>img{max-height:400px}}
  </style></head><body><main id="owner-review-root"><p>Opening the private owner edition…</p></main>
  <noscript><p>This offline reader needs JavaScript for story/channel navigation. No approval or publication action is available. Enable JavaScript and reopen this file.</p></noscript>
  <script id="owner-review-data" type="application/json">${payload}</script><script>${script}</script></body></html>`;
  mkdirSync(dirname(resolve(output)), { recursive: true });
  writeFileSync(output, html, 'utf8');
  console.log(JSON.stringify({ html_path: resolve(output), bytes: Buffer.byteLength(html), component: 'ReportEditorialWorkspace',
    mode: 'OFFLINE_READ_ONLY_OWNER_REVIEW', selected_articles: articles.length,
    selected_previews: articles.reduce((n, a) => n + a.previews.length, 0),
    required_operation_ids: edition.operation_ids, missing_operation_ids: missing,
    requires_server: false, public_write_performed: false }));
  process.exit(0);
}
const bundle = resolve(dirname(output), 'workspace-renderer.cjs');
mkdirSync(dirname(bundle), { recursive: true });
await build({ stdin: { contents: `
  import React from 'react';
  import {renderToStaticMarkup} from 'react-dom/server';
  import {ReportEditorialWorkspace} from './src/views/ReportEditorialWorkspace.tsx';
  export function render(data) {return renderToStaticMarkup(React.createElement(ReportEditorialWorkspace,{data}));}
`, resolveDir: ui, loader: 'tsx' }, bundle: true, platform: 'node', format: 'cjs', outfile: bundle, jsx: 'automatic', define: { 'import.meta.env': '{}' } });
const { default: compiled } = await import(pathToFileURL(bundle).href);
const body = compiled.render(JSON.parse(readFileSync(input, 'utf8')));
const html = `<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ContentOps — bản biên tập chưa xuất bản</title><style>
*{box-sizing:border-box;min-width:0;overflow-wrap:anywhere}body{margin:0;background:#f3f1eb;color:#172f35;font:17px/1.65 Arial,sans-serif}main{width:100%;max-width:1060px;margin:auto;padding:28px}h1,h2,h3,h4{line-height:1.25}h3{font-size:1.6rem}.report-copy{background:white;border:1px solid #cbd5ce;border-radius:12px;padding:24px;margin:24px 0}.report-body{white-space:pre-wrap;overflow-wrap:anywhere}details{padding:10px 0}summary{cursor:pointer;font-weight:600}a{color:#15676a;overflow-wrap:anywhere}p,figcaption{overflow-wrap:anywhere}img{max-width:100%;height:auto}figure{margin:22px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}button,select{font:inherit;max-width:100%}section,article,div{min-width:0}@media(max-width:600px){main{padding:12px}.report-copy{padding:16px}body{font-size:16px}h3{font-size:1.3rem}}
</style><main><h1>Bàn biên tập ContentOps</h1><p>Bản đọc từ kho biên tập hiện có · chưa xuất bản · lịch production đang tạm dừng.</p>${body}</main></html>`;
writeFileSync(output, html, 'utf8');
console.log(JSON.stringify({ html_path: resolve(output), bytes: Buffer.byteLength(html), component: 'ReportEditorialWorkspace', public_write_performed: false }));
