#!/usr/bin/env node
/**
 * ContentOps Tier-2 Remotion render driver.
 *
 * Reads a compiled render-job batch (renderer-target schema), bundles the
 * Remotion entrypoint once, and renders each scene job as an isolated silent
 * H.264 MP4. Python owns caching, QA, audio finishing, assembly, and the
 * immutable package lock; this driver only renders what it is handed and
 * reports a receipt. It performs no network calls and no uploads.
 */
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');

function arg(name, fallback = null) {
  const idx = process.argv.indexOf(name);
  if (idx === -1 || idx + 1 >= process.argv.length) return fallback;
  return process.argv[idx + 1];
}

const batchPath = arg('--batch');
const receiptPath = arg('--receipt');
const chromePath = arg('--chrome', null);
const concurrency = parseInt(arg('--concurrency', '2'), 10) || 2;

if (!batchPath || !receiptPath) {
  console.error('usage: render-job.mjs --batch <batch.json> --receipt <receipt.json> [--chrome <path>] [--concurrency N]');
  process.exit(2);
}

const batch = JSON.parse(fs.readFileSync(batchPath, 'utf8'));
const scenes = Array.isArray(batch.scenes) ? batch.scenes : [];
const rows = [];

const started = Date.now();
let serveUrl = null;

try {
  serveUrl = await bundle({
    entryPoint: path.join(projectRoot, 'src', 'index.ts'),
    // Do not let Webpack watch or emit anything outside the project.
    webpackOverride: (config) => config,
    onProgress: () => {},
  });
} catch (err) {
  fs.writeFileSync(receiptPath, JSON.stringify({status: 'bundle_failed', error: String(err && err.message ? err.message : err)}, null, 2));
  console.error('bundle_failed', err);
  process.exit(1);
}

for (const scene of scenes) {
  const row = {
    scene_id: scene.scene_id,
    composition_id: 'Scene',
    output_path: scene.output_path,
    width: scene.width,
    height: scene.height,
    fps: scene.fps,
    duration_in_frames: scene.duration_in_frames,
    status: 'rendered',
  };
  const outDir = path.dirname(scene.output_path);
  fs.mkdirSync(outDir, {recursive: true});
  const t0 = Date.now();
  try {
    const composition = await selectComposition({
      serveUrl,
      id: 'Scene',
      inputProps: {job: scene},
      ...(chromePath ? {browserExecutable: chromePath} : {}),
    });
    await renderMedia({
      composition: {...composition, fps: scene.fps, durationInFrames: scene.duration_in_frames, width: scene.width, height: scene.height},
      serveUrl,
      codec: 'h264',
      outputLocation: scene.output_path,
      inputProps: {job: scene},
      concurrency,
      ...(chromePath ? {browserExecutable: chromePath} : {}),
      // Deterministic, no hardware encoder dependence.
      crf: 18,
    });
    row.elapsed_ms = Date.now() - t0;
  } catch (err) {
    row.status = 'failed';
    row.error = String(err && err.message ? err.message : err).slice(0, 800);
    row.elapsed_ms = Date.now() - t0;
  }
  rows.push(row);
}

const receipt = {
  status: rows.every((r) => r.status === 'rendered') ? 'ok' : 'partial',
  batch_id: batch.batch_id,
  motion_system_version: batch.motion_system_version,
  renderer_profile: batch.renderer_profile,
  scenes: rows,
  rendered_count: rows.filter((r) => r.status === 'rendered').length,
  failed_count: rows.filter((r) => r.status === 'failed').length,
  network_call_performed: false,
  upload_performed: false,
  total_elapsed_ms: Date.now() - started,
};
fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2));
console.log(JSON.stringify({status: receipt.status, rendered: receipt.rendered_count, failed: receipt.failed_count}));
process.exit(receipt.status === 'ok' ? 0 : 1);
