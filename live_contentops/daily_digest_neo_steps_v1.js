// CC-855 / CC-143: deterministic BrowserOS Neo helpers for Substack DAILY_EMAIL_DIGEST.
// Python prefixes `input` and `page`; uses only the supported Neo browser SDK and visible DOM.
// Never opens a mailbox, never reads Gmail, never touches other tabs or windows.
const snap = async () => await page.snapshot();
const find = (s, role, name) => s.refs.find(r => r.role === role && r.name === name);
const unwrap = r => {
  if (r.writtenToFile && r.path) return {neo_output_file: r.path};
  if (!Object.prototype.hasOwnProperty.call(r, 'value')) throw new Error('NEO_DOM_OBSERVATION_UNAVAILABLE');
  return r.value;
};

if (input.phase === 'digest_substack_delivery_controls') {
  const s = await snap();
  const controls = unwrap(await page.evaluateInPage(() => {
    const boxes = Array.from(document.querySelectorAll('input[type="checkbox"]')).map(el => {
      const label = (el.closest('label')?.innerText || el.parentElement?.innerText || el.getAttribute('aria-label') || '').trim();
      return {label, checked: !!el.checked, disabled: !!el.disabled};
    });
    const emailBox = boxes.find(b => /send via email/i.test(b.label));
    const scheduleBox = boxes.find(b => /schedule/i.test(b.label));
    return {
      boxes,
      email_found: !!emailBox,
      email_send_enabled: emailBox ? emailBox.checked : null,
      schedule_enabled: scheduleBox ? scheduleBox.checked : false,
    };
  }));
  const sendBtn = find(s, 'button', 'Send to everyone now') || find(s, 'button', 'Publish now');
  return {
    ...controls,
    web_only_button_present: !!find(s, 'button', 'Publish on web only'),
    publish_button_name: sendBtn ? sendBtn.name : null,
    observed_at_utc: new Date().toISOString(),
  };
}

if (input.phase === 'digest_substack_publish_email') {
  const controls = unwrap(await page.evaluateInPage(() => {
    const boxes = Array.from(document.querySelectorAll('input[type="checkbox"]')).map(el => {
      const label = (el.closest('label')?.innerText || el.parentElement?.innerText || el.getAttribute('aria-label') || '').trim();
      return {label, checked: !!el.checked};
    });
    const emailBox = boxes.find(b => /send via email/i.test(b.label));
    const scheduleBox = boxes.find(b => /schedule/i.test(b.label));
    return {
      email_send_enabled: !!(emailBox && emailBox.checked),
      schedule_enabled: !!(scheduleBox && scheduleBox.checked),
    };
  }));
  const s = await snap();
  const button = find(s, 'button', 'Send to everyone now') || find(s, 'button', 'Publish now');
  if (!controls.email_send_enabled || controls.schedule_enabled || !button) {
    return {
      status: 'FAILED_BEFORE_WRITE',
      definite_no_write: true,
      public_write_performed: false,
      stage: 'BEFORE_PUBLISH_CLICK',
      reason_code: !controls.email_send_enabled
        ? 'DIGEST_EMAIL_SEND_NOT_CONFIRMED'
        : controls.schedule_enabled
          ? 'DIGEST_SCHEDULE_TOGGLE_ENABLED'
          : 'DIGEST_PUBLISH_CONTROL_MISSING',
    };
  }
  const dispatched_at_utc = new Date().toISOString();
  await page.click(button.ref);
  return {
    status: 'CLICKED',
    button_name: button.name,
    dispatched_at_utc,
    email_send_enabled: true,
    web_publish_enabled: true,
  };
}

if (input.phase === 'digest_substack_readback_links') {
  return unwrap(await page.evaluateInPage(() => {
    const body = document.querySelector('.body.markup') || document.querySelector('article');
    const links = Array.from(body?.querySelectorAll('a[href]') || [])
      .map(a => ({text: (a.innerText || '').trim(), url: a.href}))
      .filter(item => /^https:\/\//.test(item.url));
    return {
      observed_links: links,
      observed_at_utc: new Date().toISOString(),
    };
  }));
}

if (input.phase === 'digest_substack_email_stats') {
  const s = await snap();
  const details = unwrap(await page.evaluateInPage(() => {
    const text = (document.body?.innerText || '').replace(/\s+/g, ' ').trim();
    return {
      url: location.href,
      text: text.slice(0, 8000),
    };
  }));
  const text = String(details.text || s.text || '');
  const recipMatch = text.match(/Recipients\s+([\d,]+)/i);
  const opensMatch = text.match(/([\d,]+)\s+opens?\b/i);
  const rateMatch = text.match(/Open rate\s+([\d.]+)%/i);
  const recipients = recipMatch ? parseInt(recipMatch[1].replace(/,/g, ''), 10) : null;
  const opens = opensMatch ? parseInt(opensMatch[1].replace(/,/g, ''), 10) : null;
  const open_rate_percent = rateMatch ? parseFloat(rateMatch[1]) : null;
  const confirmed = Number.isInteger(recipients) && recipients > 0;
  const parts = [];
  if (recipMatch) parts.push(`Recipients ${recipMatch[1]}`);
  if (rateMatch) parts.push(`Open rate ${rateMatch[1]}%`);
  if (opensMatch) parts.push(`${opensMatch[1]} opens`);
  return {
    dashboard_url: details.url || s.url || null,
    shown: parts.length ? parts.join('; ') : text.slice(0, 240),
    recipients,
    opens,
    open_rate_percent,
    email_delivery_confirmed: confirmed,
    observed_at_utc: new Date().toISOString(),
  };
}

throw new Error('DIGEST_NEO_UNKNOWN_PHASE:' + String(input.phase));
