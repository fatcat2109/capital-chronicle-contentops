"""The existing card renderer uses its exact confirmed article's held snapshot."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json

import pytest

from live_contentops import plan_call_cards_v1 as cards, tradingview_snapshot_v1 as tv
from test_plan_analysis_distribution_cc435 import ready, confirm
from test_plan_analysis_pages_cc432 import source
from test_tradingview_plan_overlay_cc459 import captured


def test_confirmed_page_chart_feeds_social_consumer_after_capture_failure(ready,tmp_path,monkeypatch):
    store,packet,original=ready
    _,asset=captured('EURUSD')
    packet['media_assets']=[asset]
    with store.get_connection() as c:
        c.execute('UPDATE outbox_messages SET payload=? WHERE message_id=?',(json.dumps(packet),packet['page_id']))
    taken=asset['tradingview_snapshot']
    start=datetime.fromisoformat(taken['captured_at_utc'].replace('Z','+00:00'))
    hours={'60':8,'240':48,'D':120}[taken['interval']]
    row={'key':original,'symbol':'EURUSD','plan_id':packet['plan_id'],'source_plan':packet['source_plan'],
         'analysis_publication':{'canonical_url':'https://capitalchronicle.substack.com/p/full-original-plan'},
         'at_utc':start.isoformat(),'levels':{'valid_until_utc':(start+timedelta(hours=hours)).isoformat()}}
    source=cards._confirmed_page_snapshot(store,row)
    assert source==taken
    folder=tmp_path/'consumer';folder.mkdir()
    (folder/'tradingview_capture_v1.json').write_text(json.dumps({'key':original,'market':'EURUSD',
        'status':'IMAGE_HELD','cause':'TRADINGVIEW_SNAPSHOT_TIMEOUT','first_cause':'TRADINGVIEW_SNAPSHOT_TIMEOUT',
        'attempts':2,'started_at_utc':start.isoformat()}),encoding='utf-8')
    monkeypatch.setattr(tv,'OUTCOMES',tmp_path/'outcomes.jsonl')
    def forbidden(*a,**kw):pytest.fail('The held exact page chart must avoid another browser capture')
    observed=tv.plan_snapshot(row,folder,source_snapshot=source,snapshot=forbidden,now=start+timedelta(minutes=30))
    assert observed['tradingview_snapshot']['sha256']==taken['sha256']
    assert observed['tradingview_snapshot']['captured_at_utc']==taken['captured_at_utc']
    tv.validate_snapshot_asset(observed)
    state=json.loads((folder/'tradingview_capture_v1.json').read_bytes())
    assert state['status']=='CAPTURED' and state['attempts']==2
    assert state['first_cause']=='TRADINGVIEW_SNAPSHOT_TIMEOUT'
    # A page snapshot keeps its original aspect and attribution. The fresh
    # card template's different capture shape must not crop or recapture it.
    from live_contentops import plan_status_posts_v1 as posts
    row.update(kind='setup',instrument_title='EUR/USD')
    row['levels']['image_source_plan']={'held':'original plan'}
    image,credit=posts._post_image(row,tmp_path/'card',source_snapshot=source,snapshot=forbidden)
    assert credit and image['tradingview_snapshot']['sha256']==taken['sha256']
    tv.validate_snapshot_asset(image)
    changed=deepcopy(row);changed['analysis_publication']['canonical_url']='https://capitalchronicle.substack.com/p/another-plan'
    assert cards._confirmed_page_snapshot(store,changed) is None
    changed=deepcopy(row);changed['source_plan']['registration_hash']='wrong'
    assert cards._confirmed_page_snapshot(store,changed) is None
    assert cards._confirmed_page_snapshot(store,row,ratio='4:5') is None


@pytest.mark.parametrize('field,value',[('tv_symbol','SP:SPX'),('interval','D'),('capture_ratio','4:5'),('sha256','0'*64)])
def test_source_snapshot_cannot_substitute_market_timeframe_ratio_or_bytes(tmp_path,monkeypatch,field,value):
    _,asset=captured('EURUSD');taken=asset['tradingview_snapshot']
    start=datetime.fromisoformat(taken['captured_at_utc'].replace('Z','+00:00'))
    hours={'60':8,'240':48,'D':120}[taken['interval']]
    row={'key':'card','symbol':'EURUSD','at_utc':start.isoformat(),
         'levels':{'valid_until_utc':(start+timedelta(hours=hours)).isoformat()}}
    changed={**taken,field:value}
    monkeypatch.setattr(tv,'OUTCOMES',tmp_path/'outcomes.jsonl')
    with pytest.raises(tv.SnapshotError,match='SOURCE_PAGE_SNAPSHOT_BINDING_CHANGED'):
        tv.plan_snapshot(row,tmp_path/'post',source_snapshot=changed,now=start+timedelta(minutes=30))
