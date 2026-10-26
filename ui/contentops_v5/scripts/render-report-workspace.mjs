// Render the actual canonical React workspace from its owning read model, without a runtime.
import { build } from 'esbuild';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const [input, output] = process.argv.slice(2);
if (!input || !output) throw new Error('workspace JSON and HTML output paths required');
const ui = resolve(dirname(fileURLToPath(import.meta.url)), '..');
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
