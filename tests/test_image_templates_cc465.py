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


def input_record(template="call", market="USDJPY"):
    data={"schema":"image_input_v1","post_id":"controlled-fixture","template":template,"market":market,
          "plan":{"market":market,"market_name":templates.MARKETS[market],"direction":"SHORT","horizon_label":"Mid-term",
                  "status_label":"Waiting for entry","entry_low":158.,"entry_high":158.3,"invalidation":157.15,
                  "target":None,"main_probability_pct":55,"alt_probability_pct":30,"time_exit_et":"1 Dec, 9:07 PM ET"},
          "event":{"name":"US CPI, October","time_et":"13 Nov, 8:30 AM ET","consensus":"0.3%","previous":"0.2%",
                   "scenarios":[{"name":name,"trigger":"Core at 0.3% or more","probability_pct":chance,
                                 "reading":"Rates rise as inflation stays firm.",
                                 "reactions":[{"market":"XAUUSD","direction":"down"},{"market":"USDJPY","direction":"up"}]} for name,chance in [("Hot",55),("Cool",30)]]},
          "result":{"r":None,"outcome_label":"Expired, no entry","held_text":"", "entry_time_et":"", "exit_time_et":""},
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


def publication_message(tmp_path,image):
    from test_publication_image_contract_cc463 import message_with
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


def test_actual_vision_request_carries_png_and_records_configuration_without_printing_bytes(tmp_path):
    image=asset(tmp_path);seen=[]
    def run(args,*,cwd,timeout,input):
        message=json.loads(input);seen.append(message)
        assert message["message"]["content"][1]["source"]["type"]=="base64"
        value={"points":{str(i):True for i in range(1,11)},"reasons":{str(i):"controlled response" for i in range(1,11)}}
        final={"event":"result","result":{"status":"SUCCESS","response":json.dumps(value),"session_id":"controlled"}}
        return subprocess.CompletedProcess(args,0,json.dumps(final).encode(),b"")
    review=quality.review_vision(image,runner=run)
    assert len(seen)==1 and review["status"]=="REVIEWED" and review["observed_session_id"]=="controlled"
    assert review["configuration_status"]=="CONFIGURED_NOT_OBSERVED" and "base64" not in json.dumps(review)
