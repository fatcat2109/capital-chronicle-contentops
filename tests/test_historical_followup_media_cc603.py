"""A retrospective chart compares its last visible close, preserving capture time."""
from datetime import datetime, timedelta, timezone
import pytest
from live_contentops import publication_image_contract_v1 as contract

CAPTURE=datetime(2026,11,16,tzinfo=timezone.utc)
END=datetime(2026,11,13,0,45,tzinfo=timezone.utc)


def inputs():
    snapshot={'tv_symbol':'COINBASE:BTCUSD','sha256':'a'*64,'captured_at_utc':CAPTURE.isoformat(),
        'visible_from_utc':(END-timedelta(days=2)).isoformat(),'visible_to_utc':END.isoformat(),
        'visible_last_price':70881.3,'page_title':'BTCUSD 65000'}
    quote={'market':'BTCUSD','instrument':'BTCUSD','price':70881.3,'quoted_at_utc':END.isoformat(),
        'known_at_utc':(END+timedelta(days=1)).isoformat(),'source_path':'retained-bars.sqlite3',
        'source_sha256':'b'*64,'price_basis':'plan_bar_close'}
    return snapshot,quote


def test_historical_scale_uses_the_visible_close_and_preserves_the_later_capture():
    snapshot,quote=inputs()
    bound=contract.bind_scale('BTCUSD',snapshot,quote=quote)
    checked=contract.validate_scale('BTCUSD',bound)
    assert checked['comparison_basis']=='VISIBLE_WINDOW_CLOSE'
    assert checked['comparison_at_utc']==END.isoformat() and checked['captured_at_utc']==CAPTURE.isoformat()
    assert checked['difference_pct']==0 and checked['quote']['known_at_utc']==quote['known_at_utc']


@pytest.mark.parametrize('change,cause', [
    ({'visible_last_price':75000},'PRICE_SCALE_MISMATCH'),
    ({'visible_to_utc':(CAPTURE+timedelta(hours=1)).isoformat()},'HISTORICAL_WINDOW_INVALID'),
])
def test_wrong_visible_prices_and_future_windows_still_refuse(change,cause):
    snapshot,quote=inputs()
    with pytest.raises(contract.ImageContractError,match=cause):
        contract.bind_scale('BTCUSD',{**snapshot,**change},quote=quote)


def test_a_current_quote_cannot_certify_the_historical_window():
    snapshot,quote=inputs()
    with pytest.raises(contract.ImageContractError,match='PLAN_QUOTE_STALE'):
        contract.bind_scale('BTCUSD',snapshot,quote={**quote,'quoted_at_utc':CAPTURE.isoformat()})
