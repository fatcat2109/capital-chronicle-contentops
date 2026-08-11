#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const moduleRoot = process.env.CONTENTOPS_REMOTION_NODE_MODULES || path.join(root, 'node_modules');
const bundlerModule = await import(pathToFileURL(path.join(moduleRoot, '@remotion', 'bundler', 'dist', 'index.js')).href);
const rendererModule = await import(pathToFileURL(path.join(moduleRoot, '@remotion', 'renderer', 'dist', 'esm', 'index.mjs')).href);
const {bundle} = bundlerModule;
const {renderMedia, selectComposition} = rendererModule;
const value = (flag, fallback = null) => {
  const index = process.argv.indexOf(flag);
  return index >= 0 && index + 1 < process.argv.length ? process.argv[index + 1] : fallback;
};
const batchPath = value('--batch');
const receiptPath = value('--receipt');
const browserExecutable = value('--browser');
if (!batchPath || !receiptPath) throw new Error('usage: render-batch --batch FILE --receipt FILE');
const batch = JSON.parse(fs.readFileSync(batchPath, 'utf8'));
const started = Date.now();
const serveUrl = await bundle({entryPoint: path.join(root, 'src', 'index.ts'), publicDir: batch.public_dir, onProgress: () => {}});
const rows = [];
for (const job of batch.jobs || []) {
  const row = {scene_id: job.scene_id, output_path: job.output_path, cache_key: job.cache_key, status: 'RENDERED'};
  const t0 = Date.now();
  try {
    fs.mkdirSync(path.dirname(job.output_path), {recursive: true});
    const props = {job};
    const composition = await selectComposition({serveUrl, id: 'Tier2V2Scene', inputProps: props, ...(browserExecutable ? {browserExecutable} : {})});
    await renderMedia({serveUrl, composition: {...composition, durationInFrames: job.duration_in_frames, fps: job.fps, width: job.width, height: job.height}, codec: 'h264', crf: 19, concurrency: 2, outputLocation: job.output_path, inputProps: props, ...(browserExecutable ? {browserExecutable} : {})});
  } catch (error) {
    row.status = 'FAILED'; row.error = String(error?.message || error).slice(0, 1000);
  }
  row.elapsed_ms = Date.now() - t0;
  rows.push(row);
}
const receipt = {status: rows.every((row) => row.status === 'RENDERED') ? 'PASS' : 'BLOCK', rows, runtime_ms: Date.now()-started, network_calls: 0, uploads: 0};
fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2));
console.log(JSON.stringify({status: receipt.status, rendered: rows.filter((row) => row.status === 'RENDERED').length}));
process.exit(receipt.status === 'PASS' ? 0 : 1);
