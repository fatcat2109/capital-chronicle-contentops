#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';

const rendererRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const value = (flag) => {
  const index = process.argv.indexOf(flag);
  return index >= 0 && index + 1 < process.argv.length ? process.argv[index + 1] : null;
};
const compositionId = value('--composition');
const output = value('--output');
const publicDir = value('--public-dir');
const propsPath = value('--props');
const receiptPath = value('--receipt');
const scale = Number(value('--scale') || '1');
if (!compositionId || !output || !publicDir || !propsPath || !receiptPath) {
  throw new Error('required: --composition --output --public-dir --props --receipt');
}
const inputProps = JSON.parse(fs.readFileSync(propsPath, 'utf8'));
const started = Date.now();
const serveUrl = await bundle({
  entryPoint: path.join(rendererRoot, 'src', 'index.ts'),
  publicDir,
  onProgress: () => {},
});
const composition = await selectComposition({serveUrl, id: compositionId, inputProps});
fs.mkdirSync(path.dirname(output), {recursive: true});
await renderMedia({
  serveUrl,
  composition,
  codec: 'h264',
  crf: scale < 1 ? 26 : 18,
  scale,
  concurrency: 2,
  outputLocation: output,
  inputProps,
  muted: true,
});
const receipt = {
  status: 'PASS',
  renderer: 'remotion',
  renderer_version: '4.0.507',
  composition_id: compositionId,
  output_path: output,
  captions_visible: inputProps.captionsVisible,
  authorship_sha256: inputProps.authorshipSha256 || null,
  scale,
  elapsed_ms: Date.now() - started,
  network_calls: 0,
  uploads: 0,
  browser_profile_used: false,
};
fs.mkdirSync(path.dirname(receiptPath), {recursive: true});
fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2) + '\n');
