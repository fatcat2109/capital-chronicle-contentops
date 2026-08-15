import { mkdir } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const taskRoot = path.resolve(scriptDir, '..');
const articlePath = path.join(taskRoot, 'article', 'article.html');
const renderDir = path.join(taskRoot, 'render');

await mkdir(renderDir, { recursive: true });

const browser = await chromium.launch({
  executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  headless: true,
});

try {
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1100 },
    deviceScaleFactor: 1,
  });

  await page.goto(pathToFileURL(articlePath).href, { waitUntil: 'networkidle' });
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(
      [...document.images].map((img) => img.complete
        ? Promise.resolve()
        : new Promise((resolve, reject) => {
            img.addEventListener('load', resolve, { once: true });
            img.addEventListener('error', reject, { once: true });
          })),
    );
  });

  await page.screenshot({
    path: path.join(renderDir, 'article-desktop-full.png'),
    fullPage: true,
  });

  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: path.join(renderDir, 'article-desktop-hero.png'),
  });

  await page.locator('.document-card').screenshot({
    path: path.join(renderDir, 'article-desktop-source-treatment.png'),
  });

  await page.locator('.fed-panel').screenshot({
    path: path.join(renderDir, 'article-desktop-policy-panel.png'),
  });

  const metrics = await page.evaluate(() => ({
    title: document.title,
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    scrollHeight: document.documentElement.scrollHeight,
    images: [...document.images].map((img) => ({
      src: img.getAttribute('src'),
      complete: img.complete,
      naturalWidth: img.naturalWidth,
      naturalHeight: img.naturalHeight,
    })),
  }));
  process.stdout.write(`${JSON.stringify(metrics, null, 2)}\n`);
} finally {
  await browser.close();
}
