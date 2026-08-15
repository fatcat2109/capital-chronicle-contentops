import {writeFileSync} from 'node:fs';

const [endpointBase, targetUrl, outputPath] = process.argv.slice(2);
if (!endpointBase || !targetUrl || !outputPath) {
  throw new Error('usage: render_full_page.mjs <endpoint-base> <url> <output>');
}

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
let pages;
for (let attempt = 0; attempt < 50; attempt += 1) {
  try {
    pages = await (await fetch(`${endpointBase}/json`)).json();
    if (pages.length) break;
  } catch {}
  await delay(100);
}
if (!pages?.length) throw new Error('edge devtools endpoint unavailable');

const page = pages.find((entry) => entry.type === 'page') ?? pages[0];
const socket = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener('open', resolve, {once: true});
  socket.addEventListener('error', reject, {once: true});
});

let requestId = 0;
const pending = new Map();
socket.addEventListener('message', (event) => {
  const message = JSON.parse(event.data);
  if (!message.id || !pending.has(message.id)) return;
  const {resolve, reject} = pending.get(message.id);
  pending.delete(message.id);
  if (message.error) reject(new Error(JSON.stringify(message.error)));
  else resolve(message.result);
});
const send = (method, params = {}) => new Promise((resolve, reject) => {
  const id = ++requestId;
  pending.set(id, {resolve, reject});
  socket.send(JSON.stringify({id, method, params}));
});

await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', {
  width: 1440,
  height: 1000,
  deviceScaleFactor: 1,
  mobile: false,
});
await send('Page.navigate', {url: targetUrl});
for (let attempt = 0; attempt < 100; attempt += 1) {
  const {result} = await send('Runtime.evaluate', {
    expression: 'document.readyState',
    returnByValue: true,
  });
  if (result.value === 'complete') break;
  await delay(50);
}
await delay(250);
const metrics = await send('Page.getLayoutMetrics');
const width = Math.ceil(metrics.cssContentSize.width);
const height = Math.ceil(metrics.cssContentSize.height);
const screenshot = await send('Page.captureScreenshot', {
  format: 'png',
  fromSurface: true,
  captureBeyondViewport: true,
  clip: {x: 0, y: 0, width, height, scale: 1},
});
writeFileSync(outputPath, Buffer.from(screenshot.data, 'base64'));
process.stdout.write(JSON.stringify({width, height, outputPath}) + '\n');
socket.close();
