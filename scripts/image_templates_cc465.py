"""CC-465 offline PNG preparation, gallery, vision review and existing-register samples.

No publishing, hosting, live-store writes, installation or scheduling. Capture
delegates to CC-463's existing guest snapshot worker and retains its originals.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.image_templates_v1 import CHART, TEMPLATES, render
from live_contentops.image_template_inputs_v1 import ORDER
from live_contentops.image_quality_v1 import code_check, combine, publication_sample, review_vision


def write(path, data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")


def capture_previews(root,markets,masters):
    from live_contentops import tradingview_snapshot_v1 as tv
    from live_contentops.publication_image_contract_v1 import bind_scale
    observations=[]
    for market in markets:
        for master in masters:
            folder=root/"captures"/market/master;folder.mkdir(parents=True,exist_ok=True)
            record_path=folder/"snapshot.json"
            if record_path.is_file():
                prior=json.loads(record_path.read_bytes())
                if Path(prior["path"]).is_file() and sha256(Path(prior["path"]).read_bytes()).hexdigest()==prior["sha256"]:
                    observations.append(prior);continue
            box=CHART[master];size=(box[2]-box[0],box[3]-box[1])
            try:
                # Keep an unadmitted preview if the current saved Main quote is
                # absent; never fabricate that quote or widen CC-463's limit.
                snapshot=tv.capture(market,"240",folder,chart_size=size,timeout=75,
                    worker=lambda args:tv._run_worker(args,timeout=75,python=None))
                try:snapshot=bind_scale(market,snapshot)
                except (ValueError,OSError,KeyError) as exc:snapshot["price_scale_cause"]=str(exc)
                write(record_path,snapshot);observations.append(snapshot)
                print(market,master,"CAPTURED",snapshot["width"],snapshot["height"],snapshot.get("price_scale_cause","SCALE_BOUND"),flush=True)
            except Exception as exc:
                cause={"market":market,"master":master,"cause":type(exc).__name__+":"+str(exc)[:300]}
                write(folder/"capture-failure.json",cause);print(market,master,cause["cause"],flush=True)
    write(root/"capture-results.json",{"recorded_at_utc":datetime.now(timezone.utc).isoformat(),"snapshots":observations})


def build(manifest_path,out_dir,*,vision=False):
    manifest=json.loads(Path(manifest_path).read_bytes());assets=[];failures=[]
    for job in manifest["images"]:
        try:
            data=json.loads(Path(job["input_path"]).read_bytes())
            snapshot=json.loads(Path(job["snapshot_path"]).read_bytes()) if job.get("snapshot_path") else None
            asset=render(data,job["master"],out_dir,snapshot,image_number=job.get("image_number",1),page=job.get("page",0))
            code=code_check(asset)
            prior_path=Path(asset["path"]).with_suffix(".json")
            prior=json.loads(prior_path.read_bytes()) if prior_path.is_file() else {}
            saved=prior.get("image_quality") or {}
            response=review_vision(asset) if vision else (saved.get("vision") if saved.get("image_sha256")==asset["sha256"]
                and saved.get("template_revision")==asset["image_template"]["template_revision"] else None) or {"points":{},"status":"NOT_RUN"}
            asset["image_quality"]=combine(code,response,new_template=True)
            write(Path(asset["path"]).with_suffix(".json"),asset)
            assets.append(asset)
            print(data["template"],job["master"],asset["sha256"],"code",code["score"],"vision",response.get("status"),flush=True)
        except Exception as exc:
            failures.append({"job":job,"cause":type(exc).__name__+":"+str(exc)[:350],
                             "field":getattr(exc,"field",None),"details":getattr(exc,"details",{})})
            print("HELD",job.get("input_path"),str(exc),getattr(exc,"field",""),flush=True)
    write(out_dir/"gallery-assets.json",{"assets":assets,"failures":failures})
    gallery(out_dir,assets,failures)
    return assets,failures


def gallery(root,assets,failures):
    sections=[]
    for template in TEMPLATES:
        cards=[]
        for asset in assets:
            meta=asset["image_template"];q=asset.get("image_quality") or {}
            if meta["template"]!=template:continue
            href=Path(asset["path"]).relative_to(root.resolve()).as_posix()
            name=f"{meta['input'].get('market','')} · {meta['master']} · image {meta['image_number']}"
            causes="; ".join((q.get("code") or {}).get("causes",[]))
            cards.append(f'<figure><a href="{escape(href)}"><img loading="lazy" src="{escape(href)}" alt="{escape(asset["alt_text"])}"></a><figcaption>{escape(name)}<br>Code {q.get("code",{}).get("score","?")}/10 · vision {q.get("vision",{}).get("status","NOT_RUN")}<br>{escape(causes)}</figcaption></figure>')
        sections.append(f'<section id="{template}"><h2>{template.title()}</h2><div class="grid">'+"".join(cards)+'</div></section>')
    reasons="".join(f'<li>{escape(str(f["cause"]))}: {escape(str(f.get("field") or ""))}</li>' for f in failures)
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CC-465 · Five image templates</title><style>
body{margin:0;background:#F5F5F0;color:#111;font:16px system-ui,sans-serif}main{max-width:1700px;padding:32px;margin:auto}h1{border-left:8px solid #FDCF09;padding-left:20px}nav{display:flex;gap:20px;flex-wrap:wrap}a{color:#1F5FBF}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:24px}figure{margin:0;padding:12px;border:1px solid #D4D4CC;background:#fff}img{width:100%;height:auto}figcaption{line-height:1.5;overflow-wrap:anywhere}section{margin-top:48px}aside{background:#ECECE6;padding:20px}</style><main><h1>Five image templates</h1>
<p>Private build preview. Open an image to inspect its original size. The image records retain source and capture clocks. A code score or local preview does not establish publication, owner acceptance or a completed weekly sample.</p>
<nav><a href="#call">Call</a><a href="#event">Event</a><a href="#result">Result</a><a href="#weekly">Weekly scorecard</a><a href="#map">Morning map</a></nav>'''+"".join(sections)+(f'<aside><h2>Images returned for revision</h2><ul>{reasons}</ul></aside>' if failures else '')+'</main></html>'
    (root/"gallery.html").write_text(html,encoding="utf-8")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    c=sub.add_parser("capture");c.add_argument("--output",type=Path,required=True);c.add_argument("--markets",nargs="+",default=list(ORDER),choices=ORDER);c.add_argument("--masters",nargs="+",default=["W","T"],choices=["W","T"])
    r=sub.add_parser("render");r.add_argument("--manifest",type=Path,required=True);r.add_argument("--output",type=Path,required=True);r.add_argument("--vision",action="store_true")
    v=sub.add_parser("review");v.add_argument("--asset",type=Path,required=True)
    a=sub.add_parser("sample");a.add_argument("--register",type=Path,required=True);a.add_argument("--day",required=True);a.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.command=="capture":capture_previews(args.output.resolve(),args.markets,args.masters)
    elif args.command=="render":args.output.mkdir(parents=True,exist_ok=True);build(args.manifest,args.output.resolve(),vision=args.vision)
    elif args.command=="review":
        asset=json.loads(args.asset.read_bytes());asset["image_quality"]=combine(code_check(asset),review_vision(asset),new_template=True);write(args.asset,asset)
        print(json.dumps({"asset":str(args.asset),"score":asset["image_quality"]["score"],"passed":asset["image_quality"]["passed"],"vision":asset["image_quality"]["vision"]["status"]}))
    else:
        records=[json.loads(line) for line in args.register.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        sample=publication_sample(records,args.day)
        write(args.output,sample)
        print(json.dumps({"selected":len(sample["images"]),"output":str(args.output)}))


if __name__=="__main__":main()
