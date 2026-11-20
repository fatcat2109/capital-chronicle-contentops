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
const articleEditors = async destination => unwrap(await page.evaluateInPage(destination => {
  const scope = destination === 'linkedin_company' ? document.querySelector('[role="dialog"]') : document;
  return Array.from(scope?.querySelectorAll(destination === 'linkedin_company'
    ? '[contenteditable="true"][role="textbox"]' : '#contenteditable-root[contenteditable="true"]') || [])
    .filter(e => e.getClientRects().length).map(e => e.innerText);
}, destination));

// CC-466 uses this same endpoint for bound web-only plan pages.
if (input.phase === 'plan_substack_front') {
  await page.cdp('Page.bringToFront','{}');
  return {front:true};
}
if (input.phase === 'plan_substack_identity') {
  const s = await snap();
  const onPublisher = /^https:\/\/capitalchronicle\.substack\.com\/publish(?:\/|$)/.test(s.url)
    && s.text.includes('navigation "Publisher dashboard"');
  const account = find(s, 'button', "Capital Chronicle's avatar") || find(s, 'button', 'Capital Chronicle');
  const authenticated = onPublisher && !!account && !!find(s, 'button', 'Create');
  return {authenticated, observed_identity: authenticated ? 'capitalchronicle.substack.com' : null,
    observed_at_utc: new Date().toISOString()};
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
    const mediaMatch=images.length===data.media.length
      && data.media.every((a,i)=>images[i].alt===a.alt_text && text.includes(n(a.caption)));
    return {verified:body===n(data.expected_text) && mediaMatch,
      spacing_only_mismatch:body!==n(data.expected_text) && mediaMatch
        && body.replace(/\s/g,'')===n(data.expected_text).replace(/\s/g,''),pre_click_body:e.innerText};
  },{expected_text:input.expected_text,media:input.media}));
}
if (input.phase === 'plan_substack_email') {
  return unwrap(await page.evaluateInPage(()=>({enabled:Array.from(document.querySelectorAll('input[type=checkbox]'))
    .find(e=>e.parentElement.innerText.includes('Send via email'))?.checked})));
}
if (input.phase === 'plan_substack_publish' || input.phase === 'plan_substack_confirm') {
  const confirming = input.phase === 'plan_substack_confirm';
  const safe = confirming || unwrap(await page.evaluateInPage(() =>
    !Array.from(document.querySelectorAll('input[type=checkbox]')).some(e=>e.checked)));
  const button = find(await snap(), 'button', confirming ? 'Publish on web only' : 'Publish now');
  if (confirming && !button) return {status:'UNKNOWN_WRITE',stage:'PUBLISH_CLICK_ATTEMPTED'};
  const inWindow = !input.plan_entry_deadline_utc || Date.now() < Date.parse(input.plan_entry_deadline_utc);
  if (!safe || !button || !inWindow) return {status:'FAILED_BEFORE_WRITE',definite_no_write:true,
    public_write_performed:false,stage:'BEFORE_PUBLISH_CLICK',reason_code:inWindow
      ? 'PLAN_SUBSTACK_WEB_ONLY_NOT_CONFIRMED' : 'PLAN_ANALYSIS_ENTRY_WINDOW_ENDED_REVIEW_REQUIRED'};
  const dispatched_at_utc=new Date().toISOString();await page.click(button.ref);
  return {status:'CLICKED',dispatched_at_utc};
}
if (input.phase === 'plan_substack_published') {
  const s=await snap();
  const match=s.url.match(/^https:\/\/capitalchronicle\.substack\.com\/publish\/posts\/detail\/(\d+)\/share-center(?:[?#]|$)/);
  if (!match && input.published_row_draft_id && s.url === 'https://capitalchronicle.substack.com/publish/posts/published') {
    const detail = 'https://capitalchronicle.substack.com/publish/posts/detail/' + input.published_row_draft_id;
    const row = s.text.split('\n').find(line => line.startsWith('- link "' + input.published_row_title + ' ')
      && (line.includes('[url="' + detail + '"]') || line.includes('[url="' + detail + '?')));
    const href = row?.match(/\[url="([^"]+)"\]/)?.[1];
    if (href) return {published_detail_url: href};
  }
  const url=s.text.match(/https:\/\/capitalchronicle\.substack\.com\/p\/[a-z0-9-]+/);
  return {public_object_id:match?.[1],public_object_url:url?.[0],share_center_reached_utc:new Date().toISOString()};
}
if (input.phase === 'plan_substack_code_handoff') {
  const s=await snap();
  if(!s.text.includes('Check your email'))throw new Error('CODE_DIALOG_NOT_OBSERVED');
  // The operator records this screen before opening the mailbox for the owner.
  const codePage=s.url.match(/\/publish\/post\/(\d+)/)?.[1];
  return {draft_id:codePage,page_id:page.id,page_url:s.url};
}
if (input.phase === 'plan_substack_cancel_expired_code') {
  const screen = await snap();
  if (screen.url !== input.draft_url || !(Date.now() >= Date.parse(input.cancel_on_or_after_utc))) {
    return {closed:false};
  }
  const lines = screen.text.split('\n');
  const heading = /^(\s*)- dialog "Check your email"(?:\s|$)/;
  const start = lines.findIndex(line => heading.test(line));
  if (start < 0 || lines.slice(start + 1).some(line => heading.test(line))) return {closed:false};
  const indent = lines[start].match(heading)[1].length;
  const controls = [];
  for (const line of lines.slice(start + 1)) {
    if (!line.trim()) continue;
    if (line.length - line.trimStart().length <= indent) break;
    const button = line.match(/^\s*- button "(Cancel|close)" \[ref=([^\]]+)\]/);
    if (button && !line.includes('[disabled]')) controls.push(button);
  }
  const cancel = controls.find(([,name]) => name === 'Cancel') || controls[0];
  if (!cancel) return {closed:false};
  const sameDraft = unwrap(await page.evaluateInPage(data => location.href === data.url
    && document.querySelector('textarea[aria-label="title"]')?.value === data.title
    && !!document.querySelector('.ProseMirror'), {url:input.draft_url,title:input.title}));
  if (!sameDraft) return {closed:false};
  await page.click(cancel[2]);
  const after = await snap();
  const stillDraft = after.url === input.draft_url && !after.text.split('\n').some(line => heading.test(line))
    && !!(find(after, 'button', 'Continue') || find(after, 'button', 'Publish now'));
  return {closed:stillDraft, draft_url:after.url};
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

if (input.phase === 'article_restriction') {
  return unwrap(await page.evaluateInPage(()=>{
    const banner=document.querySelector('#external-links-banner');
    return {verification_required:!!banner && banner.getClientRects().length>0,
      platform_wording:banner?.innerText?.trim()||null};
  }));
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

if (input.phase === 'article_composer') {
  return {texts:await articleEditors(input.destination)};
}

if (input.phase === 'article_publish') {
  const s = await snap();
  const editors = await articleEditors(input.destination);
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
    let nodes=destination==='linkedin_company'
      ? document.querySelectorAll('[data-urn^="urn:li:activity:"]')
      : document.querySelectorAll('ytd-backstage-post-renderer');
    const permalink=destination==='linkedin_company'
      ? /^https:\/\/www\.linkedin\.com\/feed\/update\/(urn:li:activity:\d+)\/?(?:[?#].*)?$/.exec(location.href) : null;
    if (!nodes.length && permalink) {
      // LinkedIn's permalink uses its current semantic text/listitem layout;
      // the company admin feed still uses data-urn. Bind the ID to this exact
      // public URL and continue to require the post's actual company author.
      nodes=[...new Set(Array.from(document.querySelectorAll('main [data-testid="expandable-text-box"]'))
        .map(e=>e.closest('[role="listitem"]')).filter(Boolean))];
    }
    const posts=Array.from(nodes).filter(visible).map(e=>{
      const ls=links(e);
      const author=ls.find(l=>destination==='linkedin_company'
        ? /^https:\/\/www\.linkedin\.com\/company\/(?:143198922|capitalchronicle)(?:\/|$)/i.test(l.url)
        : /^https:\/\/www\.youtube\.com\/@CapitalChronicleYouTube(?:\/|$)/i.test(l.url));
      const id=destination==='linkedin_company' ? e.getAttribute('data-urn') || permalink?.[1]
        : ls.find(l=>/^https:\/\/www\.youtube\.com\/post\//.test(l.url))?.url.split('/post/')[1];
      const url=destination==='linkedin_company'
        ? 'https://www.linkedin.com/feed/update/'+id+'/' : (id?'https://www.youtube.com/post/'+id:null);
      const body=e.querySelector(destination==='linkedin_company'?'.update-components-text':'#content-text')
        || (destination==='linkedin_company'?e.querySelector('[data-testid="expandable-text-box"]'):null);
      if (destination==='linkedin_company') {
        for (const short of body?.innerText?.match(/https:\/\/lnkd\.in\/[A-Za-z0-9_-]+/g)||[]) {
          if (!ls.some(link=>link.url===short)) ls.push({text:short,url:short,expanded_url:null});
        }
      }
      return {public_object_id:id,public_object_url:url,observed_text:body?.innerText || '',
        observed_identity:author?(destination==='linkedin_company'?'linkedin:company:143198922':'@CapitalChronicleYouTube'):null,
        ...(destination==='linkedin_company'&&author?{observed_stable_id:'143198922'}:{}),links:ls,
        public_image_urls:Array.from(e.querySelectorAll('img')).filter(visible).flatMap(i=>{
          const urls=[i.currentSrc||i.src];
          if (destination==='linkedin_company' && i.getAttribute('srcset')) {
            const variants=i.getAttribute('srcset').split(',').map(s=>{
              const [url,width]=s.trim().split(/\s+/);return {url,width:parseInt(width,10)||0};
            }).sort((a,b)=>b.width-a.width);
            if (variants[0]) urls.push(variants[0].url);
          }
          return [...new Set(urls)];
        })
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

if (input.phase === 'note_exact_options') {
  return unwrap(await page.evaluateInPage(url=>{
    const roots=Array.from(document.querySelectorAll('[class*="feedPermalinkUnit"],article,[role="article"]'));
    const root=roots.find(e=>Array.from(e.querySelectorAll('a[href]')).some(a=>a.href===url));
    const button=root && Array.from(root.querySelectorAll('button')).find(b=>
      b.getAttribute('aria-label')==='More options' || b.title==='More options');
    if(!button) return {marked:false};
    button.setAttribute('aria-label','CC603 exact note options');
    return {marked:true};
  },input.public_url));
}

if (input.phase === 'note_inline_copy') {
  return unwrap(await page.evaluateInPage(text=>{
    const editor=Array.from(document.querySelectorAll('[contenteditable="true"][role="textbox"]'))
      .find(e=>e.getClientRects().length);
    if(!editor) throw Error('NOTE_EDITOR_REQUIRED');
    const escape=t=>t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    const html=text.split('\n').map(line=>'<p>'+escape(line).replace(/https:\/\/[^\s<>]+/g,
      url=>'<a href="'+url+'">'+(line.startsWith('Original: ') ? 'Open original call'
        : line.startsWith('Record: ') ? 'Open pinned scorecard' : url)+'</a>')+'</p>').join('');
    const data=new DataTransfer();data.setData('text/html',html);data.setData('text/plain',text);
    editor.focus();editor.dispatchEvent(new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true}));
    return {pasted:true};
  },input.text));
}

if (input.phase === 'quote_source') {
  return unwrap(await page.evaluateInPage(parent => {
    const norm = text => String(text || '').replace(/https?:\/\/\S+/g, '').replace(/\s+/g,' ').trim();
    const times = Array.from(document.querySelectorAll('article[data-testid="tweet"] a[href] time'));
    const clock = times.find(t => t.getClientRects().length &&
      t.closest('a').href.toLowerCase() === parent.public_object_url.toLowerCase());
    const source = clock?.closest('article[data-testid="tweet"]');
    const text = source?.querySelector('[data-testid="tweetText"]');
    const button = source?.querySelector('[data-testid="retweet"]');
    const matches = !!clock && Math.abs(Date.parse(clock.getAttribute('datetime')) -
      Date.parse(parent.source_posted_at_utc)) < 1000 && [text?.innerText, text?.textContent].some(t =>
      !!t && norm(t) === norm(parent.source_text));
    if (matches && button) button.setAttribute('aria-label','CC467 source quote menu');
    const url = clock?.closest('a').href;
    return {matches, menu_available:!!button, public_object_url:matches ? parent.public_object_url : url,
      public_object_id:url?.match(/status\/(\d+)/)?.[1]};
  }, input.quote_parent));
}

if (input.phase === 'quote_control_focused') {
  return unwrap(await page.evaluateInPage(control => {
    const e = document.activeElement;
    if (control === 'menu') return {focused:e?.matches('[data-testid="retweet"][aria-label="CC467 source quote menu"]')};
    if (control === 'card') return {focused:e?.getAttribute('aria-label') === 'CC467 observed quote source'};
    return {focused:e?.matches('[role="menuitem"]') && e.innerText.trim() === 'Quote'};
  }, input.control));
}

const quoteCard = async (parent, publicUrl, posts) => unwrap(await page.evaluateInPage(data => {
    const norm = text => String(text || '').replace(/https?:\/\/\S+/g, '').replace(/\s+/g,' ').trim();
    const editor = Array.from(document.querySelectorAll('[role="dialog"] [data-testid="tweetTextarea_0"][contenteditable="true"]'))
      .find(e => e.getClientRects().length);
    const scope = data.publicUrl ? Array.from(document.querySelectorAll('article[data-testid="tweet"]'))
      .find(e => e.querySelector('a[href*="/status/"] time')?.closest('a').href === data.publicUrl)
      : editor?.closest('[role="dialog"]');
    const parent = data.parent;
    const handle = new URL(parent.public_object_url).pathname.split('/')[1];
    const card = scope && Array.from(scope.querySelectorAll('button,[role="button"],[role="link"],[data-testid="quoteTweet"],[data-testid="card.wrapper"]'))
      .find(e => e.getClientRects().length && Array.from(e.querySelectorAll('[data-testid="tweetText"]'))
        // X wraps a rendered link over multiple lines inside a non-link span.
        .some(t => [t.innerText, t.textContent].some(text => !!text && norm(text) === norm(parent.source_text)))
        && e.innerText.toLowerCase().includes('@'+handle.toLowerCase())
        && Array.from(e.querySelectorAll('time')).some(t => Math.abs(Date.parse(t.getAttribute('datetime'))-Date.parse(parent.source_posted_at_utc)) < 1000));
    const link = card && Array.from(card.querySelectorAll('a[href*="/status/"] time')).map(t => t.closest('a').href)[0];
    const matches = !!card && (!link || link.toLowerCase() === parent.public_object_url.toLowerCase());
    if (matches && !link && data.publicUrl) card.setAttribute('aria-label','CC467 observed quote source');
    const observed = {matches, role:card?.getAttribute('role') || (card?.tagName==='BUTTON' ? 'button' : 'link'),
      public_object_url:matches && link ? parent.public_object_url : null,
      public_object_id:matches && link ? parent.public_object_id : null};
    if (!data.posts) return observed;

    const normalizeCopy = text => text.replace(/[‘’]/g,"'").replace(/[“”]/g,'"').replace(/\s+/g,' ').trim();
    const text = editor?.innerText || '';
    // Only the task's uploaded preview qualifies. The quoted card can contain
    // its own images or an avatar under the same attachments container.
    const chart = scope && Array.from(scope.querySelectorAll('[data-testid="attachments"] img[src^="blob:"]'))
      .some(e => !card?.contains(e) && e.getClientRects().length && e.complete && e.naturalWidth > 0);
    const submit = scope?.querySelector('button[data-testid="tweetButton"]');
    const enabled = !!submit?.getClientRects().length && !submit.disabled && submit.getAttribute('aria-disabled') !== 'true';
    const reason = !editor || data.posts.length !== 1 || normalizeCopy(text) !== normalizeCopy(data.posts[0])
      ? 'NEO_COMPOSER_PAYLOAD_MISMATCH' : !matches ? 'CC467_QUOTE_CARD_NOT_VERIFIED'
      : !chart ? 'CC467_CHART_PREVIEW_NOT_LOADED' : !enabled ? 'CC467_QUOTE_SUBMIT_NOT_READY' : null;
    if (!reason && submit.getAttribute('aria-label') !== 'CC467 quote Post') {
      submit.setAttribute('aria-label','CC467 quote Post');
    }
    return {...observed, chart_loaded:!!chart, reason_code:reason, pre_click_posts:editor ? [text] : []};
  }, {parent, publicUrl, posts}));

const waitForQuotePreview = timeout => page.waitForSelector(
  '[role="dialog"] [data-testid="attachments"] img[src^="blob:"]', {timeout});

if (input.phase === 'quote_card') {
  if (input.posts) await waitForQuotePreview(6000);
  return await quoteCard(input.quote_parent, input.public_url, input.posts);
}

if ((input.phase === 'publish' || input.phase === 'validate') && input.quote_parent) {
  const deadline = Date.parse(input.quote_parent.deadline_at_utc);
  const refused = (reason_code, pre_click_posts=[]) => ({status:'FAILED_BEFORE_WRITE', definite_no_write:true,
    stage:'BEFORE_PUBLISH_CLICK', reason_code, pre_click_posts});
  const expired = () => !Number.isFinite(deadline) || Date.now() >= deadline;
  if (expired()) return refused('CC467_SOURCE_OUTSIDE_FIVE_MINUTES');
  let observed, button;
  try {
    const preview = await waitForQuotePreview(Math.min(6000, Math.max(1, deadline - Date.now())));
    if (expired()) return refused('CC467_SOURCE_OUTSIDE_FIVE_MINUTES');
    if (!preview.matched) return refused('CC467_CHART_PREVIEW_NOT_LOADED');
    await page.waitForSelector('[role="dialog"] button[data-testid="tweetButton"]:not(:disabled):not([aria-disabled="true"])',
      {timeout:Math.min(6000, Math.max(1, deadline - Date.now()))});
    if (expired()) return refused('CC467_SOURCE_OUTSIDE_FIVE_MINUTES');
    observed = await quoteCard(input.quote_parent, null, input.posts);
    if (observed.reason_code) return refused(observed.reason_code, observed.pre_click_posts);
    button = find(await snap(), 'button', 'CC467 quote Post');
    if (!button) return refused('CC467_QUOTE_SUBMIT_NOT_READY', observed.pre_click_posts);
    observed = await quoteCard(input.quote_parent, null, input.posts);
    if (observed.reason_code) return refused(observed.reason_code, observed.pre_click_posts);
  } catch (_) {
    return refused('CC467_QUOTE_PRECLICK_OBSERVATION_FAILED');
  }
  if (expired()) return refused('CC467_SOURCE_OUTSIDE_FIVE_MINUTES', observed.pre_click_posts);
  if (input.phase === 'validate') return {status:'PREPARED', post_count:1, quote_card_verified:true, chart_loaded:true};
  const dispatched_at_utc = new Date().toISOString();
  try {
    await page.click(button.ref);
  } catch (_) {
    return {status:'UNKNOWN_WRITE', reason_code:'CC467_QUOTE_CLICK_RETURN_INCOMPLETE',
      stage:'PUBLISH_CLICK_ATTEMPTED', dispatched_at_utc, pre_click_posts:observed.pre_click_posts};
  }
  return {status:'CLICKED', stage:'PUBLISH_CLICK_ATTEMPTED', dispatched_at_utc, pre_click_posts:observed.pre_click_posts};
}

if (input.phase === 'composer' || input.phase === 'publish' || input.phase === 'validate') {
  let s = await snap();
  const posts = input.posts;
  const check = input.phase === 'composer' ? null : unwrap(await page.evaluateInPage(expected => {
    const norm = text => String(text).replace(/[‘’]/g,"'").replace(/[“”]/g,'"').replace(/\s+/g,' ').trim();
    const urls=new Set((expected || []).flatMap(t=>t.match(/https:\/\/[^\s<>"“”]+/g)||[]));
    const actual = Array.from((document.querySelector('[role="dialog"]') || document)
      .querySelectorAll('[contenteditable="true"][role="textbox"]'))
      .filter(e => e.getClientRects().length).map(e => {
        let text=e.innerText;
        for(const a of e.querySelectorAll('a[href]')) {
          if(['Open original call','Open pinned scorecard'].includes(a.innerText)
              && urls.has(a.href)) text=text.replace(a.innerText,a.href);
        }
        return text;
      });
    return {count:actual.length, matches:actual.length === expected.length
      && actual.every((text,i) => norm(text) === norm(expected[i]))};
  }, posts));
  const editors = unwrap(await page.evaluateInPage(expected => {
    const urls=new Set((expected || []).flatMap(t=>t.match(/https:\/\/[^\s<>"“”]+/g)||[]));
    return Array.from((document.querySelector('[role="dialog"]') || document).querySelectorAll('[contenteditable="true"][role="textbox"]'))
      .filter(e => e.getClientRects().length).map(e => {
        let text=e.innerText;
        for(const a of e.querySelectorAll('a[href]')) {
          if(['Open original call','Open pinned scorecard'].includes(a.innerText)
              && urls.has(a.href)) text=text.replace(a.innerText,a.href);
        }
        return text;
      });
  }, posts));
  if (input.phase === 'composer') return editors;
  const name = input.edit_existing ? 'Save' : input.destination === 'x' && posts.length > 1 ? 'Post all'
    : input.destination === 'x' && input.reply_parent ? 'Reply' : 'Post';
  const buttons = s.refs.filter(r => r.role === 'button' && r.name === name);
  let button = buttons[buttons.length - 1];
  if (!check.matches || check.count !== posts.length || !button) {
    return {status:'FAILED_BEFORE_WRITE', definite_no_write:true, stage:'BEFORE_PUBLISH_CLICK',
      reason_code:'NEO_COMPOSER_PAYLOAD_MISMATCH', pre_click_posts:editors};
  }
  if (input.phase === 'validate') return {status:'PREPARED',post_count:check.count};
  // Upload completion can leave Post disabled after text has matched. A click
  // on that control does nothing; it must not become an uncertain public write.
  const submit = unwrap(await page.evaluateInPage(name => {
    const matches = Array.from(document.querySelectorAll('button')).filter(e =>
      e.getClientRects().length && e.innerText.trim() === name);
    const target = matches[matches.length - 1];
    if (!target) return {marked:false};
    target.setAttribute('data-cc436-submit', 'true');
    return {marked:true};
  }, name));
  const ready = submit.marked && await page.waitForSelector(
    'button[data-cc436-submit="true"]:not(:disabled):not([aria-disabled="true"])', {timeout:20000});
  if (!ready || !ready.matched) {
    return {status:'FAILED_BEFORE_WRITE', definite_no_write:true, stage:'BEFORE_PUBLISH_CLICK',
      reason_code:'NEO_SUBMIT_NOT_READY', pre_click_posts:editors};
  }
  s = await snap();
  const settledButtons = s.refs.filter(r => r.role === 'button' && r.name === name);
  button = settledButtons[settledButtons.length - 1];
  if (!button) return {status:'FAILED_BEFORE_WRITE', definite_no_write:true, stage:'BEFORE_PUBLISH_CLICK',
    reason_code:'NEO_SUBMIT_NOT_READY', pre_click_posts:editors};
  // This clock precedes the one publish click. Any lost return is readback-only.
  const dispatched_at_utc = new Date().toISOString();
  await page.click(button.ref);
  return {status:'CLICKED', stage:'PUBLISH_CLICK_ATTEMPTED', dispatched_at_utc,
    pre_click_posts:editors};
}

if (input.phase === 'x_public_embed') {
  return unwrap(await page.evaluateInPage(() => {
    const rows = Array.from(document.querySelectorAll('.timeline-Tweet, [data-testid="tweet"]'));
    const tweets = rows.map(row => {
      const time = row.querySelector('time');
      const url = (time?.closest('a') || row.querySelector('.timeline-Tweet-timestamp'))?.href;
      const text = row.querySelector('.timeline-Tweet-text, [data-testid="tweetText"]');
      const permalink = url && new URL(url);
      const id = permalink && ['https://x.com', 'https://twitter.com'].includes(permalink.origin)
        && permalink.pathname.match(/^\/Capitalnicle\/status\/(\d+)$/i)?.[1];
      return {
        public_object_id: id,
        public_object_url: id && 'https://x.com/Capitalnicle/status/' + id,
        observed_text: text?.innerText || '',
        published_at_utc: time?.dateTime,
        text_truncated: /…$/.test(text?.innerText || '') || !!row.querySelector('[data-testid="tweet-text-show-more-link"]'),
        links: Array.from(text?.querySelectorAll('a[href]') || []).map(a => ({url:a.href, text:a.innerText})),
        public_image_urls: Array.from(row.querySelectorAll('img')).map(i => i.currentSrc || i.src)
          .filter(url => /^https:\/\/pbs.twimg.com\/media\//.test(url)),
      };
    });
    return {url:location.href, tweets};
  }));
}
if (input.phase === 'readback') {
  // AX/read omit note paragraphs and do not expose image URLs or original clocks.
  // Read only the rendered object; never fetch a private endpoint in the page.
  return unwrap(await page.evaluateInPage((identity) => {
    const visible = e => !!e && e.getClientRects().length > 0;
    const links = e => Array.from(e.querySelectorAll('a[href]')).map(a => ({text:a.innerText,url:a.href, inline_visible:visible(a),
      expanded_url:a.getAttribute('title'), card_visible:visible(a) && !!a.querySelector('[class*="previewCardContent"]')}));
    const imageUrls = e => Array.from(e.querySelectorAll('img')).filter(visible)
      .map(i => i.currentSrc || i.src).filter(u => /^https:\/\//.test(u));
    const tweets = Array.from(document.querySelectorAll('article[data-testid="tweet"]')).map(e => {
      const time = e.querySelector('a[href*="/status/"] time');
      const url = time && time.closest('a').href;
      const text = e.querySelector('[data-testid="tweetText"]');
      const postLinks = links(e);
      const quoted = Array.from(e.querySelectorAll('button,[role="button"],[data-testid="quoteTweet"], [data-testid="card.wrapper"], [role="link"]'))
        .find(card => card !== e && card.querySelector('[data-testid="tweetText"]')
          && Array.from(card.querySelectorAll('time')).some(t => !t.closest('a') || t.closest('a').href !== url));
      const quotedTime = quoted && Array.from(quoted.querySelectorAll('a[href] time'))
        .find(t => t.closest('a').href !== url);
      const quotedUrl = quotedTime?.closest('a').href;
      const views=e.querySelector('a[href$="/analytics"]');
      return {public_object_url:url, public_object_id:url && url.match(/status\/(\d+)/)?.[1],
        observed_text:text?.innerText || '', published_at_utc:time?.getAttribute('datetime'),
        quote_parent_url:quotedUrl || null, quote_parent_id:quotedUrl?.match(/status\/(\d+)/)?.[1] || null,
        public_views_text:views?.innerText || null, public_views_label:views?.getAttribute('aria-label') || null,
        metrics_observed_at_utc:new Date().toISOString(),
        links:postLinks, public_image_urls:Array.from(e.querySelectorAll('img'))
          .filter(i=>!quoted?.contains(i)).map(i=>i.currentSrc||i.src).filter(u=>/^https:\/\/pbs.twimg.com\/media\//.test(u))};
    }).filter(e=>e.public_object_url && /^https:\/\/x.com\/Capitalnicle\/status\//i.test(e.public_object_url));
    const permalink = document.querySelector('main [class*="feedPermalinkUnit"]');
    const parentUrl = permalink && links(permalink).find(a=>a.url === location.href)?.url;
    const noteElements = Array.from(document.querySelectorAll('.FeedProseMirror')).filter(visible);
    const notes = noteElements.map(e => {
      const root = e.closest('article,[class*="feedPermalinkUnit"]') || e.parentElement?.parentElement?.parentElement;
      const ancestors = [root,root.parentElement,root.parentElement?.parentElement].filter(Boolean);
      const noteUrl = value => {
        const u = new URL(value);
        return u.origin === 'https://substack.com' && !u.search && !u.hash
          && /\/note\/c-\d+$/.test(u.pathname) && (u.pathname.startsWith('/' + identity + '/note/')
            || /^\/profile\/\d+-[a-z0-9-]+\/note\/c-\d+$/i.test(u.pathname));
      };
      const owner = ancestors.find(a=>links(a).some(l=>noteUrl(l.url))) || root;
      // A permalink opens over a home feed. Its URL cannot identify unrelated
      // background notes: require the object's own rendered timestamp link.
      const url = links(owner).find(a=>noteUrl(a.url))?.url;
      // The permalink's own reply list is separate from the related-note articles.
      // This visible relationship can identify an incomplete reply, not its copy.
      const replyParent = parentUrl && !permalink.contains(e) && !e.closest('article')
        && document.querySelector('main')?.contains(e) ? parentUrl : null;
      return {public_object_url:url,public_object_id:url?.match(/note\/(c-\d+)/)?.[1],
        observed_text:e.innerText,
        published_at_utc:Array.from(owner.querySelectorAll('time[datetime]'))
          .find(t=>t.closest('a')?.href===url)?.dateTime || owner.querySelector('time[datetime]')?.dateTime,
        text_truncated:/…$/.test(e.innerText) || links(owner).some(l=>/^see more$/i.test(l.text)),
        links:links(owner), public_image_urls:imageUrls(owner),
        ...(replyParent ? {reply_parent_url:replyParent,reply_parent_id:replyParent.match(/note\/(c-\d+)/)?.[1]} : {})};
    }).filter(e=>e.public_object_url);
    return {url:location.href,tweets,notes,visible_note_count:noteElements.length};
  }, input.expected_identity));
}
throw new Error('NEO_UNSUPPORTED_PHASE');
