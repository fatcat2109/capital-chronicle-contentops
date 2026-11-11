"""Build the private CC-465 gallery from held public records and real chart downloads.

No fixture market data enters this page. Incomplete source fields stay absent;
the production gate holds the corresponding images. This page is not sent.
"""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import sys

REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO))
from live_contentops.image_template_inputs_v1 import bind,from_plan,MARKETS,ORDER,et
from live_contentops.plan_call_cards_v1 import card_plan
from scripts.image_templates_cc465 import build,write

ROOT=Path(__file__).parent
EXPORT=Path(r"A:\Capital Chronicle\ResearchRuns\plan-status-v1\plan-status.public.json")
EVENT=Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc338-cpi-preview-20261110-v1\run_context_v1.json")


def main():
    export=json.loads(EXPORT.read_bytes());context=json.loads(EVENT.read_bytes())
    jobs=[];plans={};sources={}
    def add(data,name,snapshot=True,numbers=(1,)):
        path=ROOT/"inputs"/(name+".json");write(path,data)
        for master in ("W","T"):
            for image_number in numbers:
                snap=ROOT/"media/captures"/data.get("market","USDJPY")/master/"snapshot.json"
                jobs.append({"input_path":str(path.resolve()),"master":master,"image_number":image_number,
                             **({"snapshot_path":str(snap.resolve())} if snapshot and image_number==1 else {})})
    for market in ORDER:
        candidates=[p for p in export["plans"] if p.get("asset_id")==market and p.get("status") in {"WAITING","EXPIRED","FILLED"}]
        raw=max(candidates,key=lambda p:p.get("registered_at_utc", ""))
        sources[market]=raw
        row={"key":"cc465-"+market.lower(),"symbol":market,"at_utc":raw["registered_at_utc"],
             "state":raw["status"],"source_plan":raw,"levels":card_plan(raw)}
        data=from_plan(row);plans[market]=data
        add(data,market.lower()+"-call")
        if raw.get("status")=="EXPIRED" and raw.get("outcome",{}).get("state")=="NOT_SCORED_UNTRIGGERED":
            result=deepcopy(data);result.pop("source_binding")
            result.update(template="result",post_id=data["post_id"]+"-expiry",
                          result={"r":None,"outcome_label":"Expired, no entry","held_text":"",
                                  "entry_time_et":"","exit_time_et":et(raw.get("status_at_utc") or raw.get("expires_at_utc"))})
            add(bind(result,raw),market.lower()+"-result")
    # The original event's Main-sourced probabilities retain 44%, 31%, 15%.
    # This is a layout preview on a later real chart, NOT a historical depiction.
    readings={"base_case":("In line","Core at 0.2% m/m","Small relief; the detail decides."),
              "alternative":("Hot","Core at 0.3% m/m","Rates and the dollar rise; gold and equities fall."),
              "third":("Soft","Core at 0.1% m/m","Rates and the dollar fall; gold and equities rise.")}
    source_scenarios=context["article"]["scenario_analysis"]
    scenarios=[]
    for i,source in enumerate(source_scenarios):
        name,trigger,reading=list(readings.values())[i]
        scenarios.append({"name":name,"trigger":trigger,"reading":reading,
                          "probability_pct":float(source["probability"].rstrip('%')),
                          "reactions":[{"market":"XAUUSD","direction":"up" if i in {0,2} else "down"},
                                       {"market":"USDJPY","direction":"down" if i in {0,2} else "up"}]})
    event={"schema":"image_input_v1","post_id":"cc465-retained-cpi-layout","template":"event","market":"USDJPY",
           "event":{"name":"US CPI, October","time_et":"10 Nov, 8:30 AM ET","scenarios":scenarios},
           "alt_text":"Real TradingView chart used to inspect the event template. Retained CPI probabilities are from the 10 November Main event record."}
    source={"article":context["article"],"probabilities":[s["probability_pct"] for s in scenarios],"event_time":"2026-11-10T13:30:00Z"}
    add(bind(event,source),"event",numbers=(1,2))
    resolved=export.get("scored_calls") or []
    row_values=[]
    for result in resolved:
        raw=next(p for p in export["plans"] if p["plan_id"]==result["plan_id"])
        plan=card_plan(raw)
        chance=(raw.get("scenario_analysis",{}).get("base_case") or {}).get("probability_pct")
        row_values.append({"market":result["asset_id"],"direction":"LONG" if result["direction"]=="BULLISH" else "SHORT",
                           "horizon_label":"Mid-term","main_probability_pct":chance,
                           "outcome_label":"Expired, no entry" if result["result"]=="EXPIRED" else "Stopped at invalidation",
                           "r":None})
    week={"schema":"image_input_v1","post_id":"cc465-held-weekly","template":"weekly",
          "week":{"start":"6 Nov","end":"11 Nov","calls_closed":len(resolved),"hit_rate_pct":None,
                  "total_r":None,"avg_r":None,"rows":row_values,"wrong_note":""}}
    add(bind(week,{"public_export":export,"closed_count":len(resolved)}),"weekly",snapshot=False)
    # Use only the held reference prices. Missing day moves remain visibly absent.
    rows=[]
    for market,raw in sources.items():
        last=(raw.get("forecast_probabilities") or {}).get("reference_price")
        rows.append({"market":market,"last":last,"change_1d_pct":None,"state_word":"",
                     "view_line":"No view" if not raw.get("direction") else ("Bullish" if raw["direction"]=="BULLISH" else "Bearish"),
                     "driver_line":""})
    morning={"schema":"image_input_v1","post_id":"cc465-held-map","template":"map","market":"USDJPY",
             "map":{"date_et":"Wed 11 Nov","lead_line":"The dollar remains the main driver.","rows":rows}}
    add(bind(morning,export),"morning-map",numbers=(1,2))
    write(ROOT/"gallery-manifest.json",{"images":jobs,
          "preview_limit":"Historical held plans on current real charts show layout only; public dispatch is held. R scores and daily moves are not fabricated."})
    assets,failures=build(ROOT/"gallery-manifest.json",ROOT/"media/gallery")
    print(json.dumps({"images":len(assets),"returned_for_revision":len(failures),"gallery":str(ROOT/"media/gallery/gallery.html")}))


if __name__=="__main__":main()
