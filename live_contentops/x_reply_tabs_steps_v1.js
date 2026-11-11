// Decision 123: visible DOM reads only. This file contains no submit action.
const s = await page.snapshot();
const result = await page.evaluateInPage(() => {
  const visible = e => e && e.getClientRects().length > 0;
  const profile = document.querySelector('a[data-testid="AppTabBar_Profile_Link"]');
  const authenticated = profile && new URL(profile.href).pathname.toLowerCase() === '/capitalnicle';
  const scope = document.querySelector('[role="dialog"]') || document;
  const editors = Array.from(scope.querySelectorAll('[contenteditable="true"][role="textbox"]'))
    .filter(visible).map(e => e.innerText.replace(/\r\n/g, '\n'));
  const count = label => {
    const m = String(label || '').match(/^([\d,]+)(?:\s|$)/);
    return m ? Number(m[1].replace(/,/g, '')) : null;
  };
  const rows = Array.from(document.querySelectorAll('article[data-testid="tweet"]')).filter(visible).map(e => {
    const time = e.querySelector('a[href*="/status/"] time');
    const link = time?.closest('a');
    const match = link && new URL(link.href).pathname.match(/^\/([\w]+)\/status\/(\d+)$/);
    if (!match) return null;
    const quote = Array.from(e.querySelectorAll('a[href*="/Capitalnicle/status/"]'))
      .find(a => !a.contains(time));
    const metrics = {};
    const likes = count(e.querySelector('[data-testid="like"], [data-testid="unlike"]')?.getAttribute('aria-label'));
    const views = count(e.querySelector('a[href$="/analytics"]')?.getAttribute('aria-label'));
    if (likes !== null) metrics.likes = likes;
    if (views !== null) metrics.views = views;
    return {handle:match[1], tweet_id:match[2], url:'https://x.com/'+match[1]+'/status/'+match[2],
      posted_utc:time.getAttribute('datetime'), text:e.querySelector('[data-testid="tweetText"]')?.innerText || '',
      ...(quote ? {quoted_author_handle:'Capitalnicle'} : {}), metrics,
      metrics_observed_at_utc:new Date().toISOString()};
  }).filter(Boolean);
  const current = location.pathname.match(/^\/Capitalnicle\/status\/(\d+)$/i);
  if (current) {
    // A reply's detail page renders its ancestor chain before the focal post.
    // Only its immediately preceding, visibly rendered ancestor supplies an edge.
    const index = rows.findIndex(r => r.tweet_id === current[1]);
    if (index > 0) rows[index].in_reply_to_status_id = rows[index - 1].tweet_id;
  }
  return {authenticated:Boolean(authenticated), editors, rows};
});
if (result.writtenToFile || !Object.prototype.hasOwnProperty.call(result, 'value'))
  throw new Error('REPLY_DOM_RESULT_UNAVAILABLE');
return { ...result.value, url:s.url,
  textboxes:s.refs.filter(r => r.role === 'textbox').map(r => ({ref:r.ref,name:r.name})),
  signed_out:/(?:link|button) "(?:Log in|Sign in)"/.test(s.text),
  reply_control_present:s.refs.some(r => r.role === 'button' && r.name === 'Reply'),
  observed_at_utc:new Date().toISOString()};
