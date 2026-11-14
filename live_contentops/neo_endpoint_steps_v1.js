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

// CC-466 uses this same endpoint for bound web-only plan pages.
if (input.phase === 'plan_substack_front') {
  await page.cdp('Page.bringToFront','{}');
  return {front:true};
}
if (input.phase === 'plan_substack_identity') {
  const s=await snap();
  return {authenticated:s.text.includes('Publisher dashboard') && s.refs.some(r=>r.name==='Capital Chronicle'),
    observed_identity:'capitalchronicle.substack.com',observed_at_utc:new Date().toISOString()};
}
if (input.phase === 'plan_substack_editor_identity') {
  return unwrap(await page.evaluateInPage(data=>({
    authenticated:location.origin==='https://capitalchronicle.substack.com'
      && document.querySelector('textarea[aria-label="title"]')?.value===data.title
      && document.querySelector('textarea[placeholder="Add a subtitle…"]')?.value===data.subtitle
      && Array.from(document.querySelectorAll('button')).some(b=>b.innerText==='Capital Chronicle'),
    observed_identity:'capitalchronicle.substack.com',observed_at_utc:new Date().toISOString()
  }),input.payload));
}
if (input.phase === 'plan_substack_intercept') {
  return unwrap(await page.evaluateInPage(()=>{
    const click=HTMLInputElement.prototype.click;
    const show=e=>{e.style.cssText='display:block;visibility:visible;position:fixed;bottom:4px;left:4px;width:180px;height:30px;opacity:1;z-index:9999';e.setAttribute('aria-label','CC466 editor upload');if(!e.isConnected)document.body.append(e);};
    HTMLInputElement.prototype.click=function(...args){if(this.type==='file'){show(this);return;}return click.apply(this,args);};
    document.addEventListener('click',e=>{if(e.target instanceof HTMLInputElement&&e.target.type==='file'){e.preventDefault();e.stopImmediatePropagation();show(e.target);}},true);
    return {installed:true};
  }));
}
if (input.phase === 'plan_substack_uploaded') {
  return unwrap(await page.evaluateInPage(()=>({src:document.querySelector('.ProseMirror img')?.getAttribute('data-attrs')
    ? JSON.parse(document.querySelector('.ProseMirror img').getAttribute('data-attrs')).src
    : document.querySelector('.ProseMirror img')?.src})));
}
if (input.phase === 'plan_substack_clear') {
  return unwrap(await page.evaluateInPage(()=>{const e=document.querySelector('.ProseMirror');e.focus();
    e.dispatchEvent(new KeyboardEvent('keydown',{key:'a',code:'KeyA',ctrlKey:true,bubbles:true,cancelable:true}));
    e.dispatchEvent(new KeyboardEvent('keydown',{key:'Backspace',code:'Backspace',bubbles:true,cancelable:true}));
    return {sent:true};}));
}
if (input.phase === 'plan_substack_paste') {
  return unwrap(await page.evaluateInPage(html=>{const e=document.querySelector('.ProseMirror');e.focus();
    const dt=new DataTransfer();dt.setData('text/html',html);
    e.dispatchEvent(new ClipboardEvent('paste',{bubbles:true,cancelable:true,clipboardData:dt}));return {sent:true};},input.html));
}
if (input.phase === 'plan_substack_check') {
  return unwrap(await page.evaluateInPage(data=>{
    const n=t=>String(t).replace(/[‘’]/g,"'").replace(/[“”]/g,'"').replace(/\s+/g,' ').trim();
    const e=document.querySelector('.ProseMirror');const text=n(e.innerText);
    const images=Array.from(e.querySelectorAll('img'));
    let body=text;for(const a of data.media)body=n(body.replace(n(a.caption),' '));
    return {verified:body===n(data.expected_text) && images.length===data.media.length
      && data.media.every((a,i)=>images[i].alt===a.alt_text && text.includes(n(a.caption))),pre_click_body:e.innerText};
  },{expected_text:input.expected_text,media:input.media}));
}
if (input.phase === 'plan_substack_email') {
  return unwrap(await page.evaluateInPage(()=>({enabled:Array.from(document.querySelectorAll('input[type=checkbox]'))
    .find(e=>e.parentElement.innerText.includes('Send via email'))?.checked})));
}
if (input.phase === 'plan_substack_publish') {
  const safe=unwrap(await page.evaluateInPage(()=>!Array.from(document.querySelectorAll('input[type=checkbox]')).some(e=>e.checked)));
  const button=find(await snap(),'button','Publish now');
  if(!safe||!button)return {status:'FAILED_BEFORE_WRITE',definite_no_write:true,public_write_performed:false,stage:'BEFORE_PUBLISH_CLICK',reason_code:'PLAN_SUBSTACK_WEB_ONLY_NOT_CONFIRMED'};
  const dispatched_at_utc=new Date().toISOString();await page.click(button.ref);
  return {status:'CLICKED',dispatched_at_utc};
}
if (input.phase === 'plan_substack_published') {
  const s=await snap();const match=s.url.match(/\/publish\/posts\/detail\/(\d+)\/share-center/);
  const url=s.text.match(/https:\/\/capitalchronicle\.substack\.com\/p\/[a-z0-9-]+/);
  return {public_object_id:match?.[1],public_object_url:url?.[0],share_center_reached_utc:new Date().toISOString()};
}
if (input.phase === 'plan_substack_code_handoff') {
  const s=await snap();
  if(!s.text.includes('Check your email'))throw new Error('CODE_DIALOG_NOT_OBSERVED');
  // Never read, snapshot or evaluate the mailbox. The code tab stays untouched.
  const codePage=s.url.match(/\/publish\/post\/(\d+)/)?.[1];
  const mail=await browser.open('https://mail.google.com/');
  return {draft_id:codePage,page_id:page.id,page_url:s.url,gmail_page_id:mail.id};
}
if (input.phase === 'plan_substack_readback') {
  return unwrap(await page.evaluateInPage(()=>({status:'SUCCESS',observed_identity:'capitalchronicle.substack.com',
    public_object_url:location.href,observed_text:document.body.innerText,
    article_text:document.querySelector('.body.markup')?.innerText,
    published_at_utc:document.querySelector('time')?.dateTime,
    public_image_urls:Array.from(document.querySelectorAll('figure img')).map(i=>{
      const attrs=i.getAttribute('data-attrs');return attrs?JSON.parse(attrs).src:i.src;}),
    media:Array.from(document.querySelectorAll('figure')).filter(f=>f.querySelector('img')).map(f=>({
      alt_text:f.querySelector('img').alt,caption:f.querySelector('figcaption')?.innerText})),observed_at_utc:new Date().toISOString()})));
}

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
    const fields=Array.from(document.querySelectorAll('#contenteditable-root[contenteditable="true"]'));
    const field=fields.find(e=>e.getClientRects().length && getComputedStyle(e).visibility!=='hidden');
    if (!field) return {ready:false,prompt:fields.map(e=>e.getAttribute('aria-label')).find(Boolean)||null};
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
      const views=e.querySelector('a[href$="/analytics"]');
      return {public_object_url:url, public_object_id:url && url.match(/status\/(\d+)/)?.[1],
        observed_text:text?.innerText || '', published_at_utc:time?.getAttribute('datetime'),
        public_views_text:views?.innerText || null, public_views_label:views?.getAttribute('aria-label') || null,
        metrics_observed_at_utc:new Date().toISOString(),
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
