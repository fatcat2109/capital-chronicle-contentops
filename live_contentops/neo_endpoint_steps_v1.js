// CC-436. Only the supported Neo browser SDK and visible DOM are used here.
// Python prefixes `input` and `page`; no site API, cookies or application state.
const snap = async () => await page.snapshot();
const find = (s, role, name) => s.refs.find(r => r.role === role && r.name === name);
const normalize = s => String(s).replace(/[‘’]/g,"'").replace(/[“”]/g,'"')
  .replace(/\s+/g,' ').trim();
const unwrap = r => {
  if (r.writtenToFile && r.path) return {neo_output_file:r.path};
  if (!Object.prototype.hasOwnProperty.call(r,'value')) throw new Error('NEO_DOM_OBSERVATION_UNAVAILABLE');
  return r.value;
};

if (input.phase === 'identity') {
  const s = await snap();
  const correct = input.destination === 'x'
    ? /link "Profile"[^\n]*url="https:\/\/x.com\/Capitalnicle"/.test(s.text)
      && !!find(s, 'link', 'Edit profile')
    : /@deancapitalchronicle/.test(s.text) && !!find(s, 'button', 'Edit profile');
  return {authenticated: correct, observed_identity: correct ? input.expected_identity : null,
    observed_at_utc: new Date().toISOString()};
}

if (input.phase === 'expose_note_upload') {
  // Neo's snapshot omits Substack's hidden file inputs. Expose the existing
  // image input for Neo upload; never click its native file-dialog button.
  return unwrap(await page.evaluateInPage(() => {
    const dialog = document.querySelector('[role="dialog"]');
    const fields = Array.from((dialog || document).querySelectorAll('input[type="file"]'));
    const field = fields.find(e => /image/.test(e.accept));
    if (!field) return {ready:false};
    field.style.cssText = 'display:block;visibility:visible;position:relative;width:180px;height:30px;opacity:1';
    field.setAttribute('aria-label','CC436 image upload');
    return {ready:true};
  }));
}

if (input.phase === 'composer' || input.phase === 'publish' || input.phase === 'validate') {
  const s = await snap();
  const editors = unwrap(await page.evaluateInPage(() =>
    Array.from((document.querySelector('[role="dialog"]') || document).querySelectorAll('[contenteditable="true"][role="textbox"]'))
      .filter(e => e.getClientRects().length).map(e => e.innerText)));
  if (input.phase === 'composer') return editors;
  const posts = input.posts;
  const name = input.destination === 'x' && posts.length > 1 ? 'Post all'
    : input.reply_parent ? 'Reply' : 'Post';
  const buttons = s.refs.filter(r => r.role === 'button' && r.name === name);
  const button = buttons[buttons.length - 1];
  if (editors.length !== posts.length || editors.some((p,i) => normalize(p) !== normalize(posts[i])) || !button) {
    return {status:'FAILED_BEFORE_WRITE', definite_no_write:true, stage:'BEFORE_PUBLISH_CLICK',
      reason_code:'NEO_COMPOSER_PAYLOAD_MISMATCH', pre_click_posts:editors};
  }
  if (input.phase === 'validate') return {status:'PREPARED',post_count:editors.length};
  // This clock precedes the one publish click. Any lost return is readback-only.
  const dispatched_at_utc = new Date().toISOString();
  await page.click(button.ref);
  return {status:'CLICKED', stage:'PUBLISH_CLICK_ATTEMPTED', dispatched_at_utc,
    pre_click_posts:editors};
}

if (input.phase === 'readback') {
  // AX/read omit note paragraphs and do not expose image URLs or original clocks.
  // Read only the rendered object; never fetch a private endpoint in the page.
  return unwrap(await page.evaluateInPage(() => {
    const visible = e => !!e && e.getClientRects().length > 0;
    const links = e => Array.from(e.querySelectorAll('a[href]')).map(a => ({text:a.innerText,url:a.href,
      expanded_url:a.getAttribute('title'), card_visible:visible(a) && !!a.querySelector('[class*="previewCardContent"]')}));
    const imageUrls = e => Array.from(e.querySelectorAll('img')).filter(visible)
      .map(i => i.currentSrc || i.src).filter(u => /^https:\/\//.test(u));
    const tweets = Array.from(document.querySelectorAll('article[data-testid="tweet"]')).map(e => {
      const time = e.querySelector('a[href*="/status/"] time');
      const url = time && time.closest('a').href;
      const text = e.querySelector('[data-testid="tweetText"]');
      const postLinks = links(e);
      return {public_object_url:url, public_object_id:url && url.match(/status\/(\d+)/)?.[1],
        observed_text:text?.innerText || '', published_at_utc:time?.getAttribute('datetime'),
        links:postLinks, public_image_urls:Array.from(e.querySelectorAll('img'))
          .map(i=>i.currentSrc||i.src).filter(u=>/^https:\/\/pbs.twimg.com\/media\//.test(u))};
    }).filter(e=>e.public_object_url && /^https:\/\/x.com\/Capitalnicle\/status\//i.test(e.public_object_url));
    const notes = Array.from(document.querySelectorAll('main .FeedProseMirror')).filter(visible).map(e => {
      const root = e.closest('article,[class*="feedPermalinkUnit"]') || e.parentElement?.parentElement?.parentElement;
      const ancestors = [root,root.parentElement,root.parentElement?.parentElement].filter(Boolean);
      const owner = ancestors.find(a=>a.querySelector('a[href*="/@deancapitalchronicle/note/c-"]')) || root;
      const url = links(owner).find(a=>/^https:\/\/substack.com\/@deancapitalchronicle\/note\/c-\d+$/.test(a.url))?.url
        || (/^https:\/\/substack.com\/@deancapitalchronicle\/note\/c-\d+$/.test(location.href) ? location.href : null);
      return {public_object_url:url,public_object_id:url?.match(/note\/(c-\d+)/)?.[1],
        observed_text:e.innerText, links:links(owner), public_image_urls:imageUrls(owner)};
    }).filter(e=>e.public_object_url);
    return {url:location.href,tweets,notes};
  }));
}
throw new Error('NEO_UNSUPPORTED_PHASE');
