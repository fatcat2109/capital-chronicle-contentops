const { chromium } = require('playwright');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

(async () => {
  const renderDir = __dirname;
  const candidateDir = path.resolve(renderDir, '..');
  const htmlPath = path.join(candidateDir, 'publication.html');
  const pngPath = path.join(renderDir, 'full_page_desktop_1440.png');
  const pdfPath = path.join(renderDir, 'full_page_desktop.pdf');
  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
  const failed = [];

  const browser = await chromium.launch({ executablePath: edgePath, headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  page.on('requestfailed', request => failed.push({ url: request.url(), failure: request.failure() }));
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'networkidle' });
  await page.emulateMedia({ media: 'screen' });
  await page.screenshot({ path: pngPath, fullPage: true });
  await page.pdf({ path: pdfPath, printBackground: true, width: '1440px', height: '12000px', margin: { top: '0', right: '0', bottom: '0', left: '0' } });

  const metrics = await page.evaluate(() => ({
    title: document.title,
    width: document.documentElement.scrollWidth,
    height: document.documentElement.scrollHeight,
    bodyTextCharacters: document.body.innerText.length,
    images: [...document.images].map(img => ({
      src: img.getAttribute('src'),
      complete: img.complete,
      naturalWidth: img.naturalWidth,
      naturalHeight: img.naturalHeight,
      renderedWidth: Math.round(img.getBoundingClientRect().width),
      renderedHeight: Math.round(img.getBoundingClientRect().height),
    })),
  }));
  console.log(JSON.stringify({ metrics, failedRequests: failed }, null, 2));
  await browser.close();
})().catch(error => {
  console.error(error);
  process.exit(1);
});
