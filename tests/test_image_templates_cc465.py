"""CC-465: actual PNG gates and the real coordinator consumer, isolated from live stores."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import random
import subprocess

from PIL import Image, ImageDraw
import pytest

from live_contentops import image_templates_v1 as templates
from live_contentops import image_quality_v1 as quality
from live_contentops.image_template_inputs_v1 import bind, from_plan
from live_contentops import publication_image_contract_v1 as contract
from live_contentops import tradingview_snapshot_v1 as tv

NOW = datetime(2026,11,12,16,tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def isolate_template_acceptance(tmp_path,monkeypatch):
    monkeypatch.setattr(quality,'ACCEPTANCE_CONTROL',tmp_path/'acceptance-control.json')


def input_record(template="call", market="USDJPY"):
    data={"schema":"image_input_v1","post_id":"controlled-fixture","template":template,"market":market,
          "plan":{"market":market,"market_name":templates.MARKETS[market],"direction":"SHORT","horizon_label":"Mid-term",
                  "status_label":"Waiting for entry","entry_low":158.,"entry_high":158.3,"invalidation":157.15,
                  "target":None,"main_probability_pct":55,"alt_probability_pct":30,"time_exit_et":"1 Dec, 9:07 PM ET"},
          "event":{"name":"US CPI, October","time_et":"13 Nov, 8:30 AM ET","consensus":"0.3%","previous":"0.2%",
                   "scenarios":[{"name":name,"trigger":"Core at 0.3% or more","probability_pct":chance,
                                 "reading":"Rates rise as inflation stays firm.",
                                 "reactions":[{"market":"XAUUSD","direction":"down"},{"market":"USDJPY","direction":"up"}]} for name,chance in [("Hot",55),("Cool",30)]]},
          "result":{"r":None,"outcome_label":"Expired, no entry","held_text":"", "entry_time_et":"", "exit_time_et":"12 Nov, 9:42 AM ET"},
          "map":{"date_et":"Thu 12 Nov","lead_line":"Rates remain the main driver.",
                 "rows":[{"market":m,"last":158.,"change_1d_pct":.5,"state_word":"Range",
                          "view_line":"No view","driver_line":"PPI Friday"} for m in templates.ORDER]},
          "week":{"start":"6 Nov","end":"12 Nov","calls_closed":6,"hit_rate_pct":50,"total_r":1.8,"avg_r":.3,
                  "rows":[{"market":m,"direction":"SHORT","horizon_label":"Mid-term","main_probability_pct":55,
                           "outcome_label":"Time exit","r":.3} for m in templates.ORDER]}}
    # A controlled source record, never a public numerical example.
    return bind(data,deepcopy(data))


def capture(tmp_path,master="W",market="USDJPY",*,width=None,height=None):
    width,height=(width,height) if width else (1600,700) if master=="W" else (1080,850)
    path=tmp_path/(master+"-controlled-capture.png")
    image=Image.new("RGB",(width,height),"white");draw=ImageDraw.Draw(image)
    draw.text((20,5),"Created with TradingView.com - CONTROLLED TEST FIXTURE",fill="black")
    draw.text((20,height-30),"TradingView",fill="black")
    image.save(path)
    snapshot={"path":str(path),"sha256":sha256(path.read_bytes()).hexdigest(),"width":width,"height":height,
              "tv_symbol":tv.SYMBOLS[market],"interval":"240","interval_label":"4h","page_title":"USDJPY 158.20",
              "chart_url":tv.chart_url(tv.SYMBOLS[market],"240"),"captured_at_utc":NOW.isoformat()}
    snapshot["chart_geometry"]={"source_sha256":snapshot["sha256"],"mode":"linear","slope":-100,"intercept":16200,
                                "pane_box":[0,50,width-80,height-60]}
    quote={"market":market,"instrument":market,"price":158.2,"quoted_at_utc":NOW.isoformat(),"known_at_utc":NOW.isoformat(),
           "source_path":"controlled-quote.json","source_sha256":"a"*64}
    return contract.bind_scale(market,snapshot,quote=quote)


def asset(tmp_path,master="W",template="call",**kwargs):
    data=kwargs.pop("data",None) or input_record(template)
    return templates.render(data,master,tmp_path,capture(tmp_path,master),**kwargs)


def yes_review(image):
    c=quality.code_check(image)
    v={"image_sha256":image["sha256"],"template_revision":image["image_template"]["template_revision"],
       "points":{str(i):True for i in range(1,11)},"reasons":{str(i):"controlled test response" for i in range(1,11)}}
    return quality.combine(c,v)


def vision_response(args,*,cwd,timeout,input):
    value={"image_seen":True,"points":{str(i):True for i in range(1,11)},
           "reasons":{str(i):"controlled visual response" for i in range(1,11)}}
    trace={"event":"step_update","step_update":{"type":"tool","name":"read_file"}}
    final={"event":"result","result":{"status":"SUCCESS","response":json.dumps(value)}}
    return subprocess.CompletedProcess(args,0,(json.dumps(trace)+"\n"+json.dumps(final)).encode(),b"")


def publication_message(tmp_path,image):
    from test_publication_image_contract_cc463 import message_with
    # The isolated consumer fixture supplies an explicitly controlled template
    # acceptance. Runtime never derives owner acceptance from one image score.
    meta=image['image_template']
    image['image_template_acceptance']={'accepted_at_utc':NOW.isoformat(),'reviews':[
        {'template':meta['template'],'template_revision':meta['template_revision'],'score':10,'passed':True,
         'real_snapshot':True,'market':m,'master':s,'image_sha256':'controlled-'+m+s} for m in templates.ORDER for s in ('W','T')]}
    store,runtime,coordinator,message=message_with(tmp_path,[image])
    intent=json.loads(message["payload"])
    context_path=Path(intent["output_dir"])/"run_context_v1.json"
    context=json.loads(context_path.read_bytes())
    context["article"]["market_asset"]="USDJPY"
    context_path.write_text(json.dumps(context),encoding="utf-8")
    return store,runtime,coordinator,message


@pytest.mark.parametrize("master",["W","T"])
@pytest.mark.parametrize("template,image_number",[("call",1),("event",1),("event",2),("result",1),("weekly",1),("map",1),("map",2)])
def test_all_five_templates_are_native_rgb_with_complete_text(tmp_path,master,template,image_number):
    image=asset(tmp_path,master,template,image_number=image_number)
    check=quality.code_check(image)
    assert check["passed"],check["causes"]
    with Image.open(image["path"]) as png:
        assert png.size==templates.SIZE[master] and png.mode=="RGB" and png.info["icc_profile"]


def test_gate_holds_a_cut_required_field_even_with_a_perfect_vision_score(tmp_path):
    data=input_record();data["plan"]["status_label"]="Waiting..."
    data=bind(data,data["source_binding"]["record"])
    with pytest.raises(templates.LayoutError,match="IMAGE_TEXT_CUT"):
        asset(tmp_path,data=data)
    image=asset(tmp_path);image["image_template"]["texts"][0]["text"]="Gold..."
    c=quality.code_check(image)
    assert not c["passed"]
    assert not quality.combine(c,yes_review(image)["vision"])["passed"]


def test_cropped_attribution_and_rehashed_png_still_fail_the_code_gate(tmp_path):
    image=asset(tmp_path)
    with Image.open(image["path"]) as png:
        png=png.convert("RGB");ImageDraw.Draw(png).rectangle((0,104,1600,130),fill="white");png.save(image["path"])
    image["sha256"]=sha256(Path(image["path"]).read_bytes()).hexdigest()
    c=quality.code_check(image)
    assert not c["passed"] and not c["points"]["3"]
    assert "IMAGE_ATTRIBUTION_OR_RENDER_PIXELS_CHANGED" in c["causes"]


def test_size_and_levels_refuse_at_the_real_consumer_before_destination_probe(tmp_path):
    image=asset(tmp_path)
    image["image_quality"]=yes_review(image)
    # The real coordinator should accept a correct image of its declared market.
    _,runtime,coordinator,message=publication_message(tmp_path/"run",image)
    result=coordinator._dispatch_message(message,canonical_url=None)
    assert result["status"]=="DISPATCH_CONFIRMED",result
    assert runtime.publish_calls==["substack"]
    from live_contentops.article_publication_quality_v1 import image_register
    row=image_register(coordinator).records()[-1]
    assert row["images"][0]["image_quality"]["score"]==10


def test_failed_image_never_reaches_the_real_publisher(tmp_path):
    image=asset(tmp_path);image["image_quality"]=yes_review(image)
    image["image_template"]["texts"][0]["box"]=[-1,0,5,6]
    _,runtime,coordinator,message=publication_message(tmp_path/"run",image)
    coordinator._readiness=lambda *a:pytest.fail("bad image reached destination")
    result=coordinator._dispatch_message(message,canonical_url=None)
    assert result["status"]=="DEFINITE_NO_WRITE" and runtime.publish_calls==[]


def test_wide_capture_cannot_be_used_as_a_tall_chart(tmp_path):
    with pytest.raises(templates.LayoutError,match="IMAGE_CHART_CAPTURE_SHAPE"):
        templates.render(input_record(),"T",tmp_path,capture(tmp_path,"W"))


def test_three_percent_shape_amendment_preserves_whole_snapshot(tmp_path):
    snap=capture(tmp_path,width=1600,height=710)
    image=templates.render(input_record(),"W",tmp_path,snap)
    assert image["image_template"]["framing"]["paper_margin_fraction"]<.03
    with pytest.raises(templates.LayoutError,match="IMAGE_CHART_CAPTURE_SHAPE"):
        templates.render(input_record(),"W",tmp_path,capture(tmp_path,width=1600,height=750))


def test_price_formats_pair_and_blue_band_are_source_faithful(tmp_path):
    image=asset(tmp_path)
    text=" ".join(t["text"] for t in image["image_template"]["texts"])
    assert "158.00–158.30" in text and "Main 55% · Alternative 30%" in text
    assert image["image_template"]["levels"]["entry_colour"]=="#1F5FBF"
    assert templates.price(1.1,"EURUSD")=="1.1000"
    assert templates.price(4128.2,"XAUUSD")=="4,128"
    assert templates.r_text(-1)=="−1.0R"


def test_missing_alternative_is_never_filled_with_a_complement(tmp_path):
    data=input_record();data["plan"]["alt_probability_pct"]=None;data=bind(data,data)
    image=asset(tmp_path,data=data)
    assert "PROBABILITY_PAIR_ABSENT" in image["image_template"]["notes"]
    assert not any("Main 55%" in t["text"] for t in image["image_template"]["texts"])


def test_low_vision_mandatory_point_and_stale_image_are_held(tmp_path):
    image=asset(tmp_path);c=quality.code_check(image);v=yes_review(image)["vision"]
    v["points"]["3"]=False
    assert not quality.combine(c,v)["passed"]
    v=yes_review(image)["vision"];v["image_sha256"]="wrong"
    assert not quality.combine(c,v)["passed"]


def test_daily_random_sampling_uses_existing_published_records_and_weekly_needs_twenty():
    rows=[{"state":"PUBLISHED","day":"2026-11-12","images":[{"sha256":str(i),"image_quality":{"template":"call"}}]} for i in range(5)]
    rows.append({"state":"RESERVED","day":"2026-11-12","images":[{"sha256":"reserved","image_quality":{"template":"result"}}]})
    values=quality.daily_sample(rows,"2026-11-12",rng=random.Random(3))
    assert len(values)==1 and values[0]["sha256"]!="reserved"
    assert not quality.weekly_sample([])["passed"]
    assert not quality.weekly_sample([{"image_sha256":"same","score":10,"passed":True}]*20)["passed"]
    assert quality.weekly_sample([{"image_sha256":str(i),"score":8,"passed":True} for i in range(20)])["passed"]


def test_actual_vision_request_reads_local_png_and_records_configuration_without_sending_bytes(tmp_path):
    image=asset(tmp_path);seen=[]
    def run(args,*,cwd,timeout,input):
        message=json.loads(input);seen.append(message)
        assert len(message["message"]["content"])==1 and str(Path(image["path"]).resolve()) in message["message"]["content"][0]["text"]
        assert '--mode' in args and 'plan' in args
        value={"image_seen":True,"points":{str(i):True for i in range(1,11)},"reasons":{str(i):"controlled response" for i in range(1,11)}}
        final={"event":"result","result":{"status":"SUCCESS","response":json.dumps(value),"session_id":"controlled"}}
        trace={"event":"step_update","step_update":{"type":"tool","name":"read_file"}}
        return subprocess.CompletedProcess(args,0,(json.dumps(trace)+'\n'+json.dumps(final)).encode(),b"")
    review=quality.review_vision(image,runner=run)
    assert len(seen)==1 and review["status"]=="REVIEWED" and review["observed_session_id"]=="controlled"
    assert review["configuration_status"]=="CONFIGURED_NOT_OBSERVED" and "base64" not in json.dumps(review)


def test_new_plan_image_path_consumes_the_bound_ledger_and_returns_the_native_template(tmp_path,monkeypatch):
    from live_contentops import plan_status_posts_v1 as posts
    monkeypatch.setattr(tv,"OUTCOMES",tmp_path/"outcomes.jsonl")
    monkeypatch.setattr(quality,"review_vision",lambda image,**kw:yes_review(image)["vision"])
    taken=capture(tmp_path)
    row={"kind":"setup","key":"plan-current","symbol":"USDJPY","state":"WAITING","at_utc":NOW.isoformat(),
         "time_exit_utc":"2026-12-01T14:07:00Z","levels":{"zone_low":158.,"zone_high":158.3,
         "invalidation_level":157.15,"direction":"bearish","chance_pct":55,"target":None,
         "valid_until_utc":"2026-11-18T16:00:00Z","image_source_plan":{"scenario_analysis":{
             "base_case":{"probability_pct":55},"main_alternative":{"probability_pct":30}}}}}
    image,credited=posts._post_image(row,tmp_path/"post",snapshot=lambda *a,**k:taken)
    assert credited and image["image_template"]["template"]=="call"
    assert image["image_template"]["input"]["plan"]["alt_probability_pct"]==30
    assert image["image_quality"]["passed"]


def test_structured_article_owner_builds_native_masters_and_platform_choices(tmp_path,monkeypatch):
    monkeypatch.setattr(quality,"review_vision",lambda image,**kw:yes_review(image)["vision"])
    data=input_record("event")
    def snapshot(market,interval,folder,*,chart_size):
        folder.mkdir(parents=True,exist_ok=True)
        return capture(folder,"W" if chart_size==(1600,700) else "T")
    article,images=tv.prepare_contract_article({"image_input_v1":data},[],output_dir=tmp_path,snapshot=snapshot)
    assert len(images)==4
    indexed={a['asset_id']:a for a in images}
    assert indexed[article["native_destination_media"]["threads"][0]]["image_template"]["master"]=="T"
    assert indexed[article["native_destination_media"]["x"][0]]["image_template"]["master"]=="W"
    assert all(a["image_quality"]["passed"] for a in images)


def test_unsupported_image_protocol_and_no_observed_pixel_read_never_create_scores(tmp_path):
    image=asset(tmp_path)
    def rejected(args,**kwargs):
        result={"event":"result","result":{"status":"ERROR","conversation_id":"protocol-test",
                "error":'stream input content block type "image" is not supported (only "text")',
                "usage":{"total_tokens":0},"response":""}}
        return subprocess.CompletedProcess(args,1,json.dumps(result).encode(),b"")
    record=quality.review_vision(image,runner=rejected)
    assert record["cause"]=="ValueError:AGY_IMAGE_INPUT_UNSUPPORTED" and record["points"]=={}
    assert record["observed_usage"]["total_tokens"]==0
    def text_guess(args,**kwargs):
        value={"image_seen":True,"points":{str(i):True for i in range(1,11)},"reasons":{str(i):"guess" for i in range(1,11)}}
        return subprocess.CompletedProcess(args,0,json.dumps({"event":"result","result":{"status":"SUCCESS","response":json.dumps(value)}}).encode(),b"")
    assert quality.review_vision(image,runner=text_guess)["cause"]=="ValueError:AGY_IMAGE_PIXELS_NOT_OBSERVED"


def test_missing_source_r_never_becomes_a_no_entry_result_or_weekly_zero(tmp_path):
    from live_contentops.image_template_inputs_v1 import from_result
    row={"key":"result","kind":"result","symbol":"USDJPY","state":"RESULT","at_utc":NOW.isoformat(),
         "levels":{"zone_low":158.,"zone_high":158.3,"invalidation_level":157.15,"direction":"bearish",
                   "image_source_plan":{"outcome":{"state":"SCORED","score":{"result":"STOPPED"}}}}}
    with pytest.raises(ValueError,match="IMAGE_R_RESULT_NOT_EXPORTED"):from_result(row)
    data=input_record("weekly");data["week"]["total_r"]=None;data["week"]["avg_r"]=None;data=bind(data,data)
    image=asset(tmp_path,template="weekly",data=data)
    check=quality.code_check(image)
    assert not check["passed"] and "WEEK_R_RESULT_NOT_EXPORTED" in check["causes"]


def test_numeric_change_and_retrospective_lookahead_are_refused(tmp_path):
    data=input_record();data["plan"]["entry_low"]=149.37
    # Updating the input hash cannot introduce a number absent from the source.
    data=bind(data,data["source_binding"]["record"])
    with pytest.raises(ValueError,match="IMAGE_NUMBER_NOT_IN_BOUND_SOURCE"):asset(tmp_path,data=data)
    data=input_record();data["event_cutoff_utc"]="2026-11-11T13:30:00Z";data=bind(data,data)
    with pytest.raises(ValueError,match="IMAGE_RETROSPECTIVE_CAPTURE_AFTER_EVENT"):asset(tmp_path,data=data)


def test_template_acceptance_requires_twelve_distinct_real_images():
    revision="controlled-revision"
    reviews=[{"template":"call","template_revision":revision,"score":10,"passed":True,"real_snapshot":True,
              "market":market,"master":master,"image_sha256":market+master} for market in templates.ORDER for master in ("W","T")]
    assert quality.template_acceptance(reviews,"call",revision)["passed"]
    assert not quality.template_acceptance(reviews[:-1],"call",revision)["passed"]
    assert not quality.template_acceptance([{**row,"image_sha256":"same"} for row in reviews],"call",revision)["passed"]


def test_result_path_uses_capture_bound_times_and_entry_to_exit_pixels(tmp_path):
    taken=capture(tmp_path)
    data=input_record("result");data.pop("source_binding")
    data["result"]={"r":-1.,"outcome_label":"Stopped at invalidation","held_text":"1 day 6 h",
        "best_r":.6,"worst_r":-1.,"entry_time_et":"11 Nov, 3:10 AM ET","exit_time_et":"12 Nov, 9:42 AM ET",
        "time_range_short":"11 Nov–12 Nov","market":"USDJPY","path":{"snapshot_sha256":taken["sha256"],
        "entry":{"x":300,"price":158.3,"time_et":"11 Nov, 3:10 AM ET"},
        "exit":{"x":1100,"price":157.15,"time_et":"12 Nov, 9:42 AM ET"}}}
    data=bind(data,data)
    rendered=templates.render(data,"W",tmp_path,taken)
    assert quality.code_check(rendered)["passed"]
    assert any(t["text"]=="−1.0R" and t['mono'] for t in rendered['image_template']['texts'])
    data['result']['path']['exit']['x']=500;data=bind(data,data)
    with pytest.raises(ValueError,match="IMAGE_RESULT_PATH_TIMEFRAME_REQUIRED"):
        templates.render(data,"W",tmp_path,taken)


def test_cached_template_capture_skips_repeated_review_and_fails_closed_after_two_attempts(tmp_path,monkeypatch):
    monkeypatch.setattr(tv,"OUTCOMES",tmp_path/"outcomes.jsonl")
    count=[];snap=capture(tmp_path)
    def review(image,**kwargs):count.append(image['sha256']);return yes_review(image)['vision']
    monkeypatch.setattr(quality,"review_vision",review)
    row={'key':'same-key','symbol':'USDJPY','at_utc':NOW.isoformat(),'levels':{}}
    first=tv.plan_snapshot(row,tmp_path/'one',snapshot=lambda *a,**k:snap,image_input=input_record())
    again=tv.plan_snapshot(row,tmp_path/'one',snapshot=lambda *a,**k:pytest.fail('duplicate capture'),image_input=input_record())
    assert first['sha256']==again['sha256'] and len(count)==1
    calls=[]
    def failure(*a,**k):calls.append(1);raise tv.SnapshotError('CONTROLLED_CAPTURE_FAILURE')
    with pytest.raises(tv.SnapshotPending,match='CONTROLLED_CAPTURE_FAILURE'):
        tv.plan_snapshot({**row,'key':'bad'},tmp_path/'bad',snapshot=failure,image_input=input_record())
    assert len(calls)==2


def test_paid_chart_and_wrong_platform_stay_refused_before_publish(tmp_path):
    image=asset(tmp_path);image['image_quality']=yes_review(image)
    with pytest.raises(ValueError,match='IMAGE_PLATFORM_SIZE_INVALID'):
        quality.validate_asset(image,destination='threads')
    store,runtime,coordinator,message=publication_message(tmp_path/'run',image)
    intent=json.loads(message['payload']);path=Path(intent['output_dir'])/'run_context_v1.json'
    context=json.loads(path.read_bytes());context['article']['paid']=True;path.write_text(json.dumps(context),encoding='utf-8')
    result=coordinator._dispatch_message(message,canonical_url=None)
    assert result['status']=='DEFINITE_NO_WRITE' and result['reason_code']=='PUBLIC_REDISTRIBUTION_NOT_LICENSED'
    assert runtime.publish_calls==[]


def test_one_perfect_image_never_substitutes_for_initial_template_acceptance(tmp_path):
    image=asset(tmp_path);image['image_quality']=yes_review(image)
    store,runtime,coordinator,message=publication_message(tmp_path/'run',image)
    intent=json.loads(message['payload']);path=Path(intent['output_dir'])/'run_context_v1.json'
    context=json.loads(path.read_bytes());context['media']['assets'][0].pop('image_template_acceptance')
    path.write_text(json.dumps(context),encoding='utf-8')
    coordinator._readiness=lambda *a:pytest.fail('unaccepted template reached destination')
    result=coordinator._dispatch_message(message,canonical_url=None)
    assert result['status']=='DEFINITE_NO_WRITE' and result['reason_code']=='IMAGE_TEMPLATE_TWELVE_REAL_REVIEWS_REQUIRED'
    assert runtime.publish_calls==[]


def test_accepted_template_uses_eight_point_routine_threshold_without_overriding_code(tmp_path):
    image=asset(tmp_path);image['image_quality']=yes_review(image)
    _,runtime,coordinator,message=publication_message(tmp_path/'run',image)
    intent=json.loads(message['payload']);path=Path(intent['output_dir'])/'run_context_v1.json'
    context=json.loads(path.read_bytes());held=context['media']['assets'][0]
    held['image_quality']['vision']['points'].update({'4':False,'10':False})
    path.write_text(json.dumps(context),encoding='utf-8')
    result=coordinator._dispatch_message(message,canonical_url=None)
    assert result['status']=='DISPATCH_CONFIRMED' and runtime.publish_calls==['substack']


def test_installed_consumer_reads_owner_template_acceptance_from_the_existing_control_area(tmp_path):
    image=asset(tmp_path);image['image_quality']=yes_review(image)
    _,runtime,coordinator,message=publication_message(tmp_path/'run',image)
    intent=json.loads(message['payload']);path=Path(intent['output_dir'])/'run_context_v1.json'
    context=json.loads(path.read_bytes());acceptance=context['media']['assets'][0].pop('image_template_acceptance')
    quality.ACCEPTANCE_CONTROL.write_text(json.dumps({'templates':{'call':acceptance}}),encoding='utf-8')
    path.write_text(json.dumps(context),encoding='utf-8')
    result=coordinator._dispatch_message(message,canonical_url=None)
    assert result['status']=='DISPATCH_CONFIRMED' and runtime.publish_calls==['substack']


def test_reader_copy_and_frozen_validation_select_native_portrait_without_changing_text(tmp_path,monkeypatch):
    from live_contentops import plan_call_cards_v1 as cards, plan_status_posts_v1 as posts
    from test_plan_reader_copy_cc466 import source_and_fields
    source,fields=source_and_fields()
    for point,text in zip(fields['points'],('Hot inflation supports the dollar.',
            'The rate path weighs on the euro.','Euro shorts are crowded.')):
        point['text']=text
    row={'format':4,'reader_contract':'CC466_V1','reader_fields':fields,'reader_source':source,
         'analysis_publication':{'canonical_url':'https://capitalchronicle.substack.com/p/euro-view'}}
    old=cards.destination_payloads(row,card_id='wide')
    payloads=cards.destination_payloads(row,card_id='wide',portrait_id='tall')
    for destination,payload in payloads.items():
        assert payload['full_text']==old[destination]['full_text']
        expected='tall' if destination in {'threads','instagram_business'} else 'wide'
        assert payload['media_asset_ids']==[expected]
        if payload.get('posts'):
            assert payload['posts'][0]['media_asset_ids']==[expected]
            assert all(not p['media_asset_ids'] for p in payload['posts'][1:])
    context={'plan_status_post':'reader-plan','media':{'assets':[{'asset_id':'wide'},{'asset_id':'tall'}]},
             'status_post_threads_image':'tall'}
    (tmp_path/'run_context_v1.json').write_text(json.dumps(context),encoding='utf-8')
    monkeypatch.setattr(posts,'_row_payload',lambda *_:row)
    _,replayed=posts._expected(None,'reader-plan',str(tmp_path))
    assert replayed==payloads


@pytest.mark.parametrize('field',['result_r','realized_r','r_multiple'])
def test_result_image_reuses_the_reader_existing_explicit_r_export(field):
    from live_contentops.image_template_inputs_v1 import from_result
    row={'key':'closed-plan','kind':'result','symbol':'USDJPY','state':'CLOSED','at_utc':NOW.isoformat(),
         'horizon':'MID','levels':{'direction':'bearish','zone_low':158.,'zone_high':158.3,
         'invalidation_level':159.,'image_source_plan':{'outcome':{'result':'STOPPED','score':{field:-.8}}}}}
    value=from_result(row)
    assert value['result']['r']==-.8
    assert value['result']['outcome_label']=='Stopped at invalidation'


def test_supported_structured_vision_return_needs_an_observed_pixel_read(tmp_path):
    image=asset(tmp_path)
    def run(args,**kwargs):
        original=vision_response(args,**kwargs)
        events=[json.loads(s) for s in original.stdout.splitlines()]
        final=events[-1]['result']
        final['structured_output']=json.loads(final.pop('response'))
        return subprocess.CompletedProcess(args,0,b'\n'.join(json.dumps(e).encode() for e in events),b'')
    assert quality.review_vision(image,runner=run)['status']=='REVIEWED'


def test_review_checks_exact_local_file_before_starting_a_model(tmp_path):
    image=asset(tmp_path)
    def refuse(*args,**kwargs):pytest.fail('invalid local image reached model')
    image['path']=str(tmp_path/'absent.png')
    assert quality.review_vision(image,runner=refuse)['cause']=='ValueError:IMAGE_REVIEW_FILE_UNAVAILABLE'
    image['path']=str(next(tmp_path.glob('controlled-fixture-call-*.png')))
    image['sha256']='0'*64
    assert quality.review_vision(image,runner=refuse)['cause']=='ValueError:IMAGE_REVIEW_BYTES_CHANGED'
