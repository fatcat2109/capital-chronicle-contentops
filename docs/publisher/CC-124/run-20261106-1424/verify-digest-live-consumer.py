"""Read the live consumer using actual current time; prepare or send no digest."""
import sys, json
from pathlib import Path
from datetime import datetime, time, timedelta, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.substack_daily_digest_v1 import live_canonicals, packets, BANGKOK
from live_contentops.published_content_v1 import PRODUCTION_STORE, DEFAULT_FEED, read_records, utc

CANONICAL = "https://capitalchronicle.substack.com/p/dated-capital-chronicle-review-capital"
store=ContentOpsDurableStore(PRODUCTION_STORE,auto_migrate=False)
now=datetime.now(timezone.utc)
live=[r for r in live_canonicals(store) if r["url"]==CANONICAL]
feed=[r for r in read_records(DEFAULT_FEED) if any(o["name"]=="substack" and o["url"]==CANONICAL for o in r["outlets"])]
allocated=packets(store)
used_urls={a["url"] for p in allocated for a in p["articles"]}
local=now.astimezone(BANGKOK)
cutoff=datetime.combine(local.date(),time(19),BANGKOK)
if local>=cutoff:cutoff+=timedelta(days=1)
assert len(live)==1
assert CANONICAL not in used_urls
assert cutoff-timedelta(days=1)<utc(live[0]["published_at_utc"])<=cutoff
packet={"observed_at_utc":now.isoformat(),"consumer":"live_contentops.substack_daily_digest_v1.prepare_daily_digest -> live_canonicals",
        "production_store":str(PRODUCTION_STORE),"feed_path":str(DEFAULT_FEED),
        "live_canonical":live[0],"published_feed_rows":len(feed),"not_already_allocated":True,
        "next_cutoff_utc":cutoff.astimezone(timezone.utc).isoformat(),
        "next_cutoff_GMT7":cutoff.strftime("%-d %b %Y %H:%M") if sys.platform!="win32" else cutoff.strftime("%d %b %Y %H:%M"),
        "eligible_for_next_daily_digest":True,"email_sent":False,
        "delivery":"WEB_ONLY_ARTICLE; existing once-daily email-digest consumer selects this confirmed canonical at 19:00 GMT+7",
        "clock":"Actual current clock; no future clock supplied to a mutating consumer",
        "schedule_changed":False,"public_write_performed":False}
Path(__file__).with_name("digest-live-consumer.json").write_text(json.dumps(packet,indent=2)+"\n",encoding="utf-8")
print(json.dumps(packet))
