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

// CC-454 extends this same transport for the two restored article destinations.
if (input.phase === 'article_identity') {
  const s = await snap();
  const company = input.destination === 'linkedin_company';
  const correct = company
    ? /^https:\/\/www\.linkedin\.com\/company\/143198922\/admin\//.test(s.url)
      && !!find(s, 'button', 'Start a post') && /heading "Capital Chronicle"/.test(s.text)
    : /^https:\/\/www\.youtube\.com\/@CapitalChronicleYouTube\/posts/.test(s.url)
      && s.refs.some(r => r.role === 'link' && ['Tùy chỉnh kênh', 'Customize channel'].includes(r.name))
      && s.refs.some(r => r.role === 'tab' && ['Bài đăng', 'Posts'].includes(r.name));
  return {authenticated:correct, observed_identity:correct ? input.expected_identity : null,
    ...(company && correct ? {observed_stable_id:'143198922'} : {}), observed_at_utc:new Date().toISOString()};
}

if (input.phase === 'article_editor') {
  return unwrap(await page.evaluateInPage(() => {
    const field=document.querySelector('#contenteditable-root[contenteditable="true"]');
    if (!field) return {ready:false};
    field.setAttribute('role','textbox');field.setAttribute('aria-label','CC454 article text');
    return {ready:true};
  }));
}

if (input.phase === 'article_intercept_upload') {
  return unwrap(await page.evaluateInPage(destination => {
    window.__cc454UploadInterception?.restore();
    const scope = destination === 'linkedin_company'
      ? document.querySelector('[role="dialog"]') : document.querySelector('[role="main"]') || document.body;
    if (!scope) return {installed:false};
    const original=HTMLInputElement.prototype.click;
    const show=field=>{
      field.style.cssText='display:block;visibility:visible;position:relative;width:180px;height:30px;opacity:1';
      field.removeAttribute('aria-hidden');field.setAttribute('aria-label','CC454 article image');
      if (!field.isConnected || !field.getClientRects().length) scope.append(field);
    };
    // Stop both scripted input.click() and a label's default file-selection
    // action. The real input keeps its platform change handler for Neo upload.
    const listener=e=>{
      if (e.target instanceof HTMLInputElement && e.target.type==='file') {
        e.preventDefault();e.stopImmediatePropagation();show(e.target);
      }
    };
    const intercept=function(){if(this.type==='file'){show(this);return;}return original.call(this);};
    HTMLInputElement.prototype.click=intercept;
    document.addEventListener('click',listener,true);
    window.__cc454UploadInterception={restore(){
      if (HTMLInputElement.prototype.click===intercept) HTMLInputElement.prototype.click=original;
      document.removeEventListener('click',listener,true);
    }};
    return {installed:HTMLInputElement.prototype.click===intercept};
  }, input.destination));
}

if (input.phase === 'article_upload_restore') {
  return unwrap(await page.evaluateInPage(() => {
    window.__cc454UploadInterception?.restore();delete window.__cc454UploadInterception;
    return {restored:true};
  }));
}

if (input.phase === 'article_publish') {
  const s = await snap();
  const editors = unwrap(await page.evaluateInPage(destination => {
    const scope = destination === 'linkedin_company'
      ? document.querySelector('[role="dialog"]') : document;
    return Array.from(scope?.querySelectorAll(destination === 'linkedin_company'
      ? '[contenteditable="true"][role="textbox"]' : '#contenteditable-root[contenteditable="true"]') || [])
      .filter(e => e.getClientRects().length).map(e => e.innerText);
  }, input.destination));
  const buttons=s.refs.filter(r=>r.role==='button' && ['Post','Đăng'].includes(r.name));
  const button=buttons[buttons.length-1];
  if (!button || editors.length !== 1 || input.posts.length !== 1
      || normalize(editors[0]) !== normalize(input.posts[0])) {
    return {status:'FAILED_BEFORE_WRITE',definite_no_write:true,stage:'BEFORE_PUBLISH_CLICK',
      reason_code:'NEO_COMPOSER_PAYLOAD_MISMATCH',pre_click_posts:editors};
  }
  const dispatched_at_utc=new Date().toISOString();
  await page.click(button.ref);
  return {status:'CLICKED',stage:'PUBLISH_CLICK_ATTEMPTED',dispatched_at_utc,pre_click_posts:editors};
}

if (input.phase === 'article_readback') {
  return unwrap(await page.evaluateInPage(destination => {
    const visible=e=>!!e && e.getClientRects().length>0;
    const links=e=>Array.from(e.querySelectorAll('a[href]')).map(a=>{
      const u=new URL(a.href);const expanded=u.hostname==='www.youtube.com' && u.pathname==='/redirect'
        ? u.searchParams.get('q') : null;
      return {text:a.innerText,url:a.href,expanded_url:expanded};
    });
    const nodes=destination==='linkedin_company'
      ? document.querySelectorAll('[data-urn^="urn:li:activity:"]')
      : document.querySelectorAll('ytd-backstage-post-renderer');
    const posts=Array.from(nodes).filter(visible).map(e=>{
      const ls=links(e);
      const author=ls.find(l=>destination==='linkedin_company'
        ? /^https:\/\/www\.linkedin\.com\/company\/(?:143198922|capitalchronicle)(?:\/|$)/i.test(l.url)
        : /^https:\/\/www\.youtube\.com\/@CapitalChronicleYouTube(?:\/|$)/i.test(l.url));
      const id=destination==='linkedin_company' ? e.getAttribute('data-urn')
        : ls.find(l=>/^https:\/\/www\.youtube\.com\/post\//.test(l.url))?.url.split('/post/')[1];
      const url=destination==='linkedin_company'
        ? 'https://www.linkedin.com/feed/update/'+id+'/' : (id?'https://www.youtube.com/post/'+id:null);
      const body=e.querySelector(destination==='linkedin_company'?'.update-components-text':'#content-text');
      return {public_object_id:id,public_object_url:url,observed_text:body?.innerText || '',
        observed_identity:author?(destination==='linkedin_company'?'linkedin:company:143198922':'@CapitalChronicleYouTube'):null,
        ...(destination==='linkedin_company'&&author?{observed_stable_id:'143198922'}:{}),links:ls,
        public_image_urls:Array.from(e.querySelectorAll('img')).filter(visible).map(i=>i.currentSrc||i.src)
          .filter(u=>destination==='linkedin_company'?/^https:\/\/media\.licdn\.com\//.test(u):/^https:\/\/yt3\.ggpht\.com\//.test(u))};
    }).filter(p=>p.public_object_id && p.observed_identity);
    return {posts};
  }, input.destination));
}

if (input.phase === 'identity') {
  const s = await snap();
  const correct = input.destination === 'x'
    ? /link "Profile"[^\n]*url="https:\/\/x.com\/Capitalnicle"/.test(s.text)
      && !!find(s, 'link', 'Edit profile')
    : s.url === 'https://substack.com/' + input.expected_identity
      && !!find(s, 'link', input.expected_identity) && !!find(s, 'button', 'Edit profile');
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

if (input.phase === 'expose_composer') {
  return unwrap(await page.evaluateInPage(destination => {
    const scope=document.querySelector('[role="dialog"]') || document;
    const selector=destination==='x'
      ? '[data-testid^="tweetTextarea_"][contenteditable="true"][role="textbox"]'
      : '[contenteditable="true"][role="textbox"]';
    const fields=Array.from(scope.querySelectorAll(selector)).filter(e=>e.getClientRects().length);
    fields.forEach((e,i)=>e.setAttribute('aria-label','CC436 post text '+i));
    return {ready:fields.length>0,count:fields.length};
  },input.destination));
}

if (input.phase === 'add_post_focused') {
  return unwrap(await page.evaluateInPage(() => {
    const e=document.activeElement;
    return {focused:!!e && e.matches('button,[role="button"]')
      && e.getAttribute('aria-label')==='Add post' && !!e.closest('[role="dialog"]')};
  }));
}

if (input.phase === 'dismiss_focused') {
  return unwrap(await page.evaluateInPage(() => {
    const e=document.activeElement;
    return {focused:!!e && e.matches('button,[role="button"]')
      && ['Close','Cancel'].includes(e.getAttribute('aria-label') || e.innerText)
      && !!e.closest('[role="dialog"]')};
  }));
}

if (input.phase === 'composer' || input.phase === 'publish' || input.phase === 'validate') {
  const s = await snap();
  const posts = input.posts;
  const check = input.phase === 'composer' ? null : unwrap(await page.evaluateInPage(expected => {
    const norm = text => String(text).replace(/[‘’]/g,"'").replace(/[“”]/g,'"').replace(/\s+/g,' ').trim();
    const actual = Array.from((document.querySelector('[role="dialog"]') || document)
      .querySelectorAll('[contenteditable="true"][role="textbox"]'))
      .filter(e => e.getClientRects().length).map(e => e.innerText);
    return {count:actual.length, matches:actual.length === expected.length
      && actual.every((text,i) => norm(text) === norm(expected[i]))};
  }, posts));
  const editors = unwrap(await page.evaluateInPage(() =>
    Array.from((document.querySelector('[role="dialog"]') || document).querySelectorAll('[contenteditable="true"][role="textbox"]'))
      .filter(e => e.getClientRects().length).map(e => e.innerText)));
  if (input.phase === 'composer') return editors;
  const name = input.destination === 'x' && posts.length > 1 ? 'Post all'
    : input.destination === 'x' && input.reply_parent ? 'Reply' : 'Post';
  const buttons = s.refs.filter(r => r.role === 'button' && r.name === name);
  const button = buttons[buttons.length - 1];
  if (!check.matches || check.count !== posts.length || !button) {
    return {status:'FAILED_BEFORE_WRITE', definite_no_write:true, stage:'BEFORE_PUBLISH_CLICK',
      reason_code:'NEO_COMPOSER_PAYLOAD_MISMATCH', pre_click_posts:editors};
  }
  if (input.phase === 'validate') return {status:'PREPARED',post_count:check.count};
  // This clock precedes the one publish click. Any lost return is readback-only.
  const dispatched_at_utc = new Date().toISOString();
  await page.click(button.ref);
  return {status:'CLICKED', stage:'PUBLISH_CLICK_ATTEMPTED', dispatched_at_utc,
    pre_click_posts:editors};
}

if (input.phase === 'readback') {
  // AX/read omit note paragraphs and do not expose image URLs or original clocks.
  // Read only the rendered object; never fetch a private endpoint in the page.
  return unwrap(await page.evaluateInPage((identity) => {
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
      const noteUrl = value => {
        const u = new URL(value);
        return u.origin === 'https://substack.com' && !u.search && !u.hash
          && /\/note\/c-\d+$/.test(u.pathname) && (u.pathname.startsWith('/' + identity + '/note/')
            || /^\/profile\/\d+-[a-z0-9-]+\/note\/c-\d+$/i.test(u.pathname));
      };
      const owner = ancestors.find(a=>links(a).some(l=>noteUrl(l.url))) || root;
      const url = links(owner).find(a=>noteUrl(a.url))?.url
        || (noteUrl(location.href) ? location.href : null);
      return {public_object_url:url,public_object_id:url?.match(/note\/(c-\d+)/)?.[1],
        observed_text:e.innerText, links:links(owner), public_image_urls:imageUrls(owner)};
    }).filter(e=>e.public_object_url);
    return {url:location.href,tweets,notes};
  }, input.expected_identity));
}
throw new Error('NEO_UNSUPPORTED_PHASE');
