#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const rendererRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const moduleRoot = process.env.CONTENTOPS_REMOTION_NODE_MODULES || path.join(rendererRoot, 'node_modules');
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
const serveUrl = await bundle({
  entryPoint: path.join(rendererRoot, 'src', 'index.ts'),
  publicDir: batch.public_dir,
  onProgress: () => {},
});
const rows = [];
for (const job of batch.jobs || []) {
  const row = {
    beat_id: job.beat_id,
    scene_id: job.scene_id,
    variant_id: job.variant_id,
    output_path: job.output_path,
    cache_key: job.cache_key,
    captions_visible: job.captions_visible,
    status: 'RENDERED',
  };
  const t0 = Date.now();
  try {
    fs.mkdirSync(path.dirname(job.output_path), {recursive: true});
    const inputProps = {job};
    const common = browserExecutable ? {browserExecutable} : {};
    const composition = await selectComposition({serveUrl, id: 'RetentionNativeBeat', inputProps, ...common});
    await renderMedia({
      serveUrl,
      composition: {
        ...composition,
        durationInFrames: job.duration_in_frames,
        fps: job.fps,
        width: job.width,
        height: job.height,
      },
      codec: 'h264',
      crf: job.proxy ? 24 : 18,
      concurrency: 2,
      outputLocation: job.output_path,
      inputProps,
      muted: true,
      ...common,
    });
  } catch (error) {
    row.status = 'FAILED';
    row.error = String(error?.message || error).slice(0, 1200);
  }
  row.elapsed_ms = Date.now() - t0;
  rows.push(row);
}
const receipt = {
  status: rows.every((row) => row.status === 'RENDERED') ? 'PASS' : 'BLOCK',
  renderer: 'remotion',
  renderer_version: '4.0.507',
  rows,
  runtime_ms: Date.now() - started,
  network_calls: 0,
  uploads: 0,
  browser_profile_used: false,
};
fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2));
console.log(JSON.stringify({status: receipt.status, rendered: rows.filter((row) => row.status === 'RENDERED').length}));
process.exit(receipt.status === 'PASS' ? 0 : 1);
