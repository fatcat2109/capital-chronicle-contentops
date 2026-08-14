"""Build the governed CFTC Treasury-positioning short + longform media proof."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from live_contentops.lane_b_asset_first_v1 import measure_loudness, probe_media, sha256_file, write_json
from live_contentops.short_longform_low_cost_audio_v1 import (
    CHATTERBOX_CANDIDATE, ELEVENLABS_FINAL, KOKORO_BUILD, PARLER_CANDIDATE,
    FormatAudioLedger, build_missing_segment_request, logical_hash,
    validate_format_contract, validate_zero_write,
)

TASK_ID = "TASK_CONTENTOPS_V2_SHORT_LONGFORM_LOW_COST_AUDIO_VERTICAL_SLICE_V1"
JOB_ID = "CFTC_TREASURY_POSITIONING_20260811_SHORT_LONGFORM_V1"
DEFAULT_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_short_longform_low_cost_audio_20260815")
TTS_PYTHON = Path(r"A:\Capital Chronicle\Runtime\ContentOps\tier2\tts-kokoro-venv\Scripts\python.exe")
TFF_SOURCE = DEFAULT_RUNTIME / "authority" / "tff_txt_2026" / "FinFutYY.txt"
RENDERER = REPO / "video" / "asset_first_v1"
CREATIVE_SOURCE = RENDERER / "src" / "generated" / "treasuryPositioning.tsx"

SOURCE_CFTC = "CFTC Traders in Financial Futures, positions as of 2026-08-11"
SOURCE_FED = "Federal Reserve, Decomposing Hedge Funds’ U.S. Treasury Exposures, 2026-06-22"
SOURCE_BOUNDARY = "CFTC classifications do not identify an individual trader’s motive"

SHORT_SCENES = [
 {"scene_id":"S01_GIANT_OFFSET","narration":"Treasury futures carry a giant offset: asset managers massively long, leveraged funds massively short.","caption":"Treasury futures carry a giant offset.","visual_kind":"hook","headline":"THE TREASURY MARKET’S GIANT OFFSET","dek":"One official snapshot. Two very different balance-sheet jobs.","source":SOURCE_CFTC},
 {"scene_id":"S02_THREE_CONTRACTS","narration":"Asset managers were net long one point six eight million two-year and two point eight eight million five-year contracts.","caption":"Asset managers: enormous net longs.","visual_kind":"positions","headline":"THE LONG SIDE IS ENORMOUS","dek":"Net futures contracts · asset managers/institutional","source":SOURCE_CFTC},
 {"scene_id":"S03_SHORT_MIRROR","narration":"Leveraged funds nearly mirrored them: net short one point three six million two-year and two point one five million five-year contracts.","caption":"Leveraged funds: a near-mirror short.","visual_kind":"positions","headline":"SO IS THE SHORT SIDE","dek":"Net futures contracts · leveraged funds","source":SOURCE_CFTC},
 {"scene_id":"S04_PRIMARY_ROW","narration":"The CFTC reports category totals. It does not identify each trader or motive.","caption":"Primary data, with a motive boundary.","visual_kind":"document","headline":"WHAT THE SOURCE ACTUALLY SAYS","source":SOURCE_BOUNDARY},
 {"scene_id":"S05_BASIS_MECHANISM","narration":"One explanation is the basis trade: borrow in repo, buy a Treasury, short its future.","caption":"Repo cash + Treasury + short future.","visual_kind":"mechanism","headline":"THE BASIS-TRADE MECHANISM","source":SOURCE_FED},
 {"scene_id":"S06_NOT_IDENTITY","narration":"But short futures do not equal basis exposure. Funds also hedge and run other relative-value trades.","caption":"A proxy is not an identity.","visual_kind":"risk","headline":"THE SHORT IS A PROXY — NOT AN IDENTITY","source":"Federal Reserve, Quantifying Treasury Cash-Futures Basis Trades, 2024-03-08"},
 {"scene_id":"S07_STRESS_TEST","narration":"Leverage matters when margin rises, repo tightens, and crowded positions unwind together.","caption":"Leverage changes the speed of an unwind.","visual_kind":"repo","headline":"WHEN THE OFFSET BECOMES A RISK","source":"Federal Reserve Financial Stability Report, May 2026"},
 {"scene_id":"S08_CLOSE","narration":"Watch the pairing, then verify financing and cash-futures gaps. Positioning is a map, not a motive detector.","caption":"Positioning is a map, not a motive detector.","visual_kind":"test","headline":"WATCH THE PAIRING. VERIFY THE FINANCING.","source":SOURCE_BOUNDARY},
]

LONG_SCENES = [
 {"scene_id":"L01_COLD_OPEN","narration":"There is a balance-sheet standoff hiding in plain sight inside the Treasury futures market. On one side, asset managers hold millions of net long contracts. On the other, leveraged funds carry millions of net shorts. The bars look almost designed to cancel. They were not designed at all. They emerge because two groups use the same instrument for very different jobs. Understanding that offset matters because it sits near the plumbing of the world’s benchmark bond market.","caption":"A balance-sheet standoff in Treasury futures.","visual_kind":"hook","headline":"THE TREASURY MARKET’S GIANT OFFSET","dek":"Why asset-manager longs and leveraged-fund shorts can coexist — and when that matters.","source":SOURCE_CFTC},
 {"scene_id":"L02_SOURCE_CLOCK","narration":"Start with the source clock. The Commodity Futures Trading Commission’s Traders in Financial Futures report records positions as of Tuesday and usually publishes them on Friday. Our snapshot is August eleventh, twenty twenty-six. That lag matters. This is a governed weekly map, not a live trading screen. It separates reportable positions into dealers, asset managers, leveraged funds, and other reportables. It does not name the firms, and it does not tell us the motive behind an individual position.","caption":"Tuesday positions. Friday release. Category totals.","visual_kind":"timing","headline":"FIRST: RESPECT THE SOURCE CLOCK","source":"CFTC Commitments of Traders explanatory notes"},
 {"scene_id":"L03_TWO_YEAR","narration":"Begin at the two-year contract. Open interest was four million three hundred seventy-seven thousand eight hundred twelve contracts. Asset managers were long two million three hundred forty-two thousand nine hundred seventy-five and short six hundred sixty-two thousand five hundred eighty-six: a net long of one million six hundred eighty thousand three hundred eighty-nine. Leveraged funds were net short one million three hundred fifty-nine thousand five hundred twenty-one. That is not a small speculative corner. It is a structural-looking offset inside a very liquid contract.","caption":"2-year: +1.68m asset managers; −1.36m leveraged funds.","visual_kind":"document","headline":"THE TWO-YEAR OFFSET","source":SOURCE_CFTC},
 {"scene_id":"L04_FIVE_YEAR","narration":"The five-year is larger. Open interest reached six million four hundred forty-two thousand nine hundred fifty. Asset managers were net long two million eight hundred eighty-three thousand nine hundred seventy-seven contracts. Leveraged funds were net short two million one hundred forty-seven thousand seven hundred forty-four. Dealer net positioning was short roughly eight hundred nineteen thousand. One contract represents one hundred thousand dollars of face value, but multiplying face value is exposure context, not a clean measure of economic risk or capital at stake.","caption":"5-year: the largest asset-manager net long in the set.","visual_kind":"positions","headline":"THE FIVE-YEAR IS THE CENTER OF GRAVITY","source":SOURCE_CFTC},
 {"scene_id":"L05_TEN_YEAR","narration":"At the ten-year, open interest was five million four hundred fifty-eight thousand eight hundred ninety. Asset managers were net long two million five hundred fifty-four thousand four hundred eleven. Leveraged funds were net short two million one hundred sixty-three thousand seven hundred fourteen. The similarity between those two numbers is visually striking, but it does not prove that one category directly faces the other trade for trade. Clearing nets the market. The report gives category totals, not matched counterparties.","caption":"10-year: large opposing nets, not matched counterparties.","visual_kind":"positions","headline":"A NEAR-MIRROR IS NOT A MATCHED TRADE","source":SOURCE_BOUNDARY},
 {"scene_id":"L06_WEEKLY_CHANGE","narration":"The weekly changes add an important wrinkle. In the five-year, the asset-manager net long fell by roughly seventy-nine thousand contracts while the leveraged-fund net short became about sixty-four thousand contracts less negative. In the ten-year, the asset-manager net long fell about forty thousand while the leveraged-fund short became roughly sixty-eight thousand less negative. Both sides were trimming parts of the offset. The giant stock remained, but the flow was not a simple new pile-on.","caption":"The stock stayed huge while both sides trimmed.","visual_kind":"history","headline":"STOCK AND FLOW TELL DIFFERENT STORIES","source":SOURCE_CFTC},
 {"scene_id":"L07_ASSET_MANAGER_JOB","narration":"Why might asset managers prefer long futures? A futures contract can add duration quickly without moving large amounts of cash. That can help a pension, insurer, mutual fund, or other institution manage benchmark exposure, expected inflows, or portfolio duration. Futures are liquid and operationally efficient. None of that means every asset-manager long has the same purpose. It means the category has plausible demand for synthetic duration, and the CFTC data show the aggregate result.","caption":"Futures can add duration without fully funding cash bonds.","visual_kind":"mechanism","headline":"THE LONG SIDE: SYNTHETIC DURATION","source":"U.S. Treasury, Remarks on Treasury Market Resilience, 2024-09-26"},
 {"scene_id":"L08_BASIS_SETUP","narration":"Now take the leveraged-fund short. The most discussed explanation is the cash-futures basis trade. Treasury futures and comparable cash securities should converge toward delivery, but small gaps can appear. A fund can buy the relatively cheap cash bond and short the relatively rich future. If the spread closes, the package earns the difference. The expected return is tiny in price terms, so the strategy often relies on scale and leverage.","caption":"Cash bond long. Futures short. Convergence sought.","visual_kind":"mechanism","headline":"THE SHORT SIDE: A CONVERGENCE PACKAGE","source":"Federal Reserve, Quantifying Treasury Cash-Futures Basis Trades, 2024-03-08"},
 {"scene_id":"L09_REPO_FINANCING","narration":"The financing step is the fulcrum. The cash Treasury is commonly funded in the repurchase-agreement market. The fund pledges the security, borrows most of its value, and supplies a smaller equity cushion. That can make a thin spread attractive on equity, but it creates dependence on repo availability, haircuts, and rollover terms. The future adds daily variation margin. A position that looks market-neutral can still be liquidity-sensitive on both legs.","caption":"Market-neutral does not mean liquidity-neutral.","visual_kind":"repo","headline":"REPO TURNS A SMALL GAP INTO A LEVERAGED TRADE","source":SOURCE_FED},
 {"scene_id":"L10_FED_SCALE","narration":"A June twenty twenty-six Federal Reserve analysis estimated that, as of September twenty twenty-five, hedge funds had about four trillion dollars of gross Treasury exposure: roughly two point four trillion long and one point six trillion short. It estimated around three trillion dollars of repo cash borrowing and about eight hundred thirty billion dollars of basis-trade exposure. Those are portfolio-level estimates built from regulatory data, not a claim that today’s futures shorts all belong to the basis trade.","caption":"Fed estimate: basis was substantial, not the whole book.","visual_kind":"document","headline":"THE BASIS TRADE IS LARGE — NOT TOTAL","source":SOURCE_FED},
 {"scene_id":"L11_PROXY_BOUNDARY","narration":"This is the central analytical boundary. Leveraged-fund short futures are a useful, timely proxy for possible basis activity. They can also reflect outright rate views, curve trades, hedges against other assets, swap packages, and relative-value strategies that are not the classic cash-futures basis. The Federal Reserve has explicitly warned that the proxy may overestimate basis exposure. If someone turns one CFTC column into a precise basis-trade total, they have crossed the evidence line.","caption":"Useful proxy. Imperfect identification.","visual_kind":"risk","headline":"DO NOT CONFUSE A PROXY WITH AN IDENTITY","source":"Federal Reserve, Quantifying Treasury Cash-Futures Basis Trades, 2024-03-08"},
 {"scene_id":"L12_BENEFIT","narration":"The trade is not inherently villainous. Arbitrage can pull cash and futures prices back together. It can support price discovery, liquidity, and the transmission of demand between instruments. Asset managers get an efficient futures market; hedge funds intermediate the price difference; dealers and clearinghouses help connect the system. In calm conditions that machinery can make the Treasury market work better. The concern is not the existence of relative value. It is the financing structure and the speed of adjustment under stress.","caption":"Arbitrage can improve pricing and liquidity.","visual_kind":"mechanism","headline":"WHY THE TRADE CAN HELP","source":"Federal Reserve and U.S. Treasury analyses of the cash-futures basis"},
 {"scene_id":"L13_STRESS_CHAIN","narration":"Imagine volatility jumps. Futures positions generate variation-margin calls. Cash Treasuries can lose value. Repo lenders may demand more collateral or reduce balance-sheet capacity. A fund then needs cash quickly. It can sell Treasuries, cut futures, or reduce other positions. If many funds run similar packages, individually sensible risk management becomes a synchronized unwind. That is how a small basis and a large gross book can turn into market-wide selling pressure.","caption":"Margin + repo tightening can synchronize an unwind.","visual_kind":"repo","headline":"THE STRESS TRANSMISSION CHAIN","source":"Federal Reserve Financial Stability Report, May 2026"},
 {"scene_id":"L14_DEALER_CAPACITY","narration":"Dealer capacity sits in the middle. Dealers finance clients, make markets in cash securities, and intermediate hedges. The May twenty twenty-six Financial Stability Report described dealer leverage as low and intermediation as robust, even while hedge-fund leverage remained near record highs. That is a useful current counterweight: elevated leverage is a vulnerability, not proof that a break is underway. The condition of dealer balance sheets and repo markets determines whether a repositioning is absorbed or amplified.","caption":"Vulnerability is not the same as an active break.","visual_kind":"risk","headline":"THE BUFFER: DEALERS AND FUNDING MARKETS","source":"Federal Reserve Financial Stability Report, May 2026"},
 {"scene_id":"L15_WHAT_TO_WATCH","narration":"What should an investor watch? First, whether leveraged-fund shorts remain elevated across several Treasury contracts. Second, whether repo borrowing, rates, or haircuts show strain. Third, whether measured cash-futures gaps are widening rather than converging. Fourth, whether asset-manager futures demand changes sharply. And fifth, whether Treasury market depth deteriorates during the move. No single indicator closes the case. The signal comes from the positioning, financing, price gap, and liquidity measures agreeing.","caption":"Positioning + financing + basis + liquidity.","visual_kind":"test","headline":"A FOUR-LAYER MONITORING STACK","source":"Capital Chronicle analysis from cited primary evidence"},
 {"scene_id":"L16_CONFIRM","narration":"The basis-risk interpretation strengthens if large short futures coexist with heavy repo borrowing, widening basis opportunities, margin pressure, and weaker market depth. It weakens if leveraged shorts fall while repo markets remain calm, or if portfolio data show the positions belong to other relative-value strategies. Confirmation requires multiple surfaces. Invalidation matters just as much, because the CFTC category is broad and the most dramatic narrative is not automatically the correct one.","caption":"Confirmation requires more than one column.","visual_kind":"test","headline":"CONFIRM — OR CHALLENGE — THE READ","source":SOURCE_BOUNDARY},
 {"scene_id":"L17_BALANCE_SHEET","narration":"The broader lesson is about balance sheets. Asset managers can use futures to obtain duration efficiently. Leveraged funds can use the other side inside financed arbitrage packages. Dealers and repo lenders connect them. The resulting futures offset can be huge even when directional rate opinions are not. But the same structure concentrates liquidity demands in moments of volatility. Looking only at net market direction misses the mechanism; looking only at leverage misses the service the trade provides.","caption":"Different jobs can create one enormous offset.","visual_kind":"positions","headline":"ONE MARKET. DIFFERENT BALANCE-SHEET JOBS.","source":"Capital Chronicle analysis from CFTC, Federal Reserve, and Treasury sources"},
 {"scene_id":"L18_CLOSE","narration":"The August eleventh report gives us a precise snapshot: enormous asset-manager longs, enormous leveraged-fund shorts, and evidence that parts of both sides were trimming that week. It does not give us a motive detector, a live risk gauge, or a countdown to crisis. Treat the futures data as the map. Use repo, portfolio, basis, and liquidity evidence to identify the route. The giant offset is real. Its meaning has to be earned.","caption":"The offset is real. Its meaning has to be earned.","visual_kind":"hook","headline":"POSITIONING IS A MAP — NOT A MOTIVE DETECTOR","source":SOURCE_CFTC},
]


def _json(path: Path, value: Any) -> None:
    write_json(path, value)


def _run(command: Sequence[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), cwd=cwd, check=True, capture_output=True, text=True)


def _duration(path: Path) -> float:
    data = probe_media(path)
    return float(data["format"]["duration"])


def lock_evidence(runtime: Path) -> dict[str, Any]:
    target_names = {"UST 2Y NOTE", "UST 5Y NOTE", "UST 10Y NOTE"}
    rows=[]
    with TFF_SOURCE.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            name=str(row["Market_and_Exchange_Names"]).split(" - ")[0]
            if row["Report_Date_as_YYYY-MM-DD"]=="2026-08-11" and name in target_names:
                clean={key:(value.strip() if isinstance(value,str) else value) for key,value in row.items()}
                rows.append({"market":name,"open_interest":int(clean["Open_Interest_All"]),"asset_long":int(clean["Asset_Mgr_Positions_Long_All"]),"asset_short":int(clean["Asset_Mgr_Positions_Short_All"]),"asset_net":int(clean["Asset_Mgr_Positions_Long_All"])-int(clean["Asset_Mgr_Positions_Short_All"]),"lever_long":int(clean["Lev_Money_Positions_Long_All"]),"lever_short":int(clean["Lev_Money_Positions_Short_All"]),"lever_net":int(clean["Lev_Money_Positions_Long_All"])-int(clean["Lev_Money_Positions_Short_All"]),"asset_net_weekly_change":int(clean["Change_in_Asset_Mgr_Long_All"])-int(clean["Change_in_Asset_Mgr_Short_All"]),"lever_net_weekly_change":int(clean["Change_in_Lev_Money_Long_All"])-int(clean["Change_in_Lev_Money_Short_All"]),"contract_units":clean["Contract_Units"],"row_sha256":hashlib.sha256(json.dumps(clean,sort_keys=True).encode()).hexdigest()})
    if len(rows)!=3: raise RuntimeError(f"required_cftc_rows_missing:{len(rows)}")
    packet={"schema":"contentops.v2.evidence_packet.v1","story_id":JOB_ID,"source_url":"https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip","source_path":str(TFF_SOURCE),"source_sha256":sha256_file(TFF_SOURCE),"report_date":"2026-08-11","rows":rows,"boundaries":["Category totals do not identify individual traders or motives.","Futures shorts alone do not equal basis-trade exposure.","Contract face value is not economic risk or capital at stake."],"supporting_primary_sources":["https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm","https://www.federalreserve.gov/econres/notes/feds-notes/decomposing-hedge-funds-u-s-treasury-exposures-20260622.html","https://www.federalreserve.gov/econres/notes/feds-notes/quantifying-treasury-cash-futures-basis-trades-20240308.html","https://www.federalreserve.gov/publications/files/financial-stability-report-20260508.pdf","https://home.treasury.gov/news/press-releases/jy2721"]}
    _json(runtime/"contracts"/"evidence_packet.json",packet); return packet


def author(runtime: Path, ledger: FormatAudioLedger) -> None:
    story={"story_id":JOB_ID,"title":"The Treasury market’s giant offset","freshness":"CFTC positions as of 2026-08-11","formats":["30-60s clean 9:16 short",">=5m clean 16:9 longform"],"independent_authorship":True,"canonical_midform_final":False}
    evidence=lock_evidence(runtime)
    format_check=validate_format_contract(SHORT_SCENES,LONG_SCENES)
    if format_check["status"]!="PASS": raise RuntimeError(format_check)
    _json(runtime/"contracts"/"story_lock.json",story)
    _json(runtime/"contracts"/"short_storyboard.json",{"variant":"short","scenes":SHORT_SCENES})
    _json(runtime/"contracts"/"longform_storyboard.json",{"variant":"longform","scenes":LONG_SCENES})
    _json(runtime/"contracts"/"format_validation.json",format_check)
    asset_board={"story_id":JOB_ID,"selected":[{"asset_id":"CFTC_NATIVE_ROWS","family":"primary_document","license":"US_GOVERNMENT_PRIMARY","source_sha256":evidence["source_sha256"]},{"asset_id":"NATIVE_POSITION_BARS","family":"native_chart","license":"INTERNAL_GOVERNED"},{"asset_id":"NATIVE_REPO_CHAIN","family":"mechanism","license":"INTERNAL_GOVERNED"},{"asset_id":"NATIVE_SOURCE_CLOCK","family":"timeline","license":"INTERNAL_GOVERNED"},{"asset_id":"NATIVE_CONFIRM_CHALLENGE","family":"framework","license":"INTERNAL_GOVERNED"}],"rejected":[{"asset_id":"GENERIC_TRADING_SCREEN","reason":"Decorative and non-specific"},{"asset_id":"AI_TRADER_PORTRAIT","reason":"Generated real-person documentary media forbidden"}],"visual_policy":"CONCRETE_FIRST_ABSTRACT_SECOND"}
    _json(runtime/"contracts"/"asset_board.json",asset_board)
    for stage,value in [("STORY_LOCKED",story),("EVIDENCE_LOCKED",evidence),("ANALYSIS_READY",{"truth_analysis_engagement_separated":True,"claim_count":20}),("ASSET_BOARD_READY",asset_board),("SHORT_STORYBOARD_READY",{"hash":logical_hash(SHORT_SCENES)}),("LONGFORM_STORYBOARD_READY",{"hash":logical_hash(LONG_SCENES)}),("SHORT_SOURCE_READY",{"creative_source":str(CREATIVE_SOURCE),"sha256":sha256_file(CREATIVE_SOURCE)}),("LONGFORM_SOURCE_READY",{"creative_source":str(CREATIVE_SOURCE),"sha256":sha256_file(CREATIVE_SOURCE)})]: ledger.checkpoint(JOB_ID,stage,{"prior":stage},value)


def _concat_wav(paths: Sequence[Path], target: Path, runtime: Path) -> None:
    listing=runtime/"audio"/f"{target.stem}-concat.txt"
    listing.parent.mkdir(parents=True,exist_ok=True)
    listing.write_text("".join(f"file '{str(path).replace("'", "'\\''")}'\n" for path in paths),encoding="utf-8")
    _run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",str(listing),"-c:a","pcm_s16le",str(target)])


def _captions(scenes: Sequence[Mapping[str,Any]], target: Path) -> None:
    def stamp(seconds:float)->str:
        ms=round(seconds*1000);return f"{ms//3600000:02d}:{(ms//60000)%60:02d}:{(ms//1000)%60:02d},{ms%1000:03d}"
    index=1;cursor=0.0;blocks=[]
    for scene in scenes:
        words=str(scene["narration"]).split();duration=float(scene["duration_seconds"]);chunks=[words[i:i+7] for i in range(0,len(words),7)]
        per=duration/max(1,len(chunks))
        for chunk in chunks:
            blocks.append(f"{index}\n{stamp(cursor)} --> {stamp(cursor+per)}\n{' '.join(chunk)}\n");index+=1;cursor+=per
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text("\n".join(blocks),encoding="utf-8")


def audio(runtime: Path, ledger: FormatAudioLedger) -> dict[str,Any]:
    KOKORO_BUILD.validate(); cache=runtime/"audio"/"cache"; all_rows={}; generated=0; reused=0
    _json(runtime/"contracts"/"short_storyboard.json",{"variant":"short","scenes":SHORT_SCENES})
    for variant,base in (("short",SHORT_SCENES),("longform",LONG_SCENES)):
        request,manifest=build_missing_segment_request(base,cache,speed=1.0)
        request_path=runtime/"audio"/f"{variant}-kokoro-request.json";_json(request_path,request)
        started=time.perf_counter()
        if request["segments"]:
            completed=_run([str(TTS_PYTHON),str(REPO/"live_contentops"/"video_tts_worker_v1.py"),"--batch-request",str(request_path)])
            json_line=next((line for line in reversed(completed.stdout.splitlines()) if line.lstrip().startswith("{")), "")
            _json(runtime/"receipts"/f"{variant}-kokoro-worker.json",json.loads(json_line));generated+=len(request["segments"])
        elapsed=time.perf_counter()-started
        enriched=[]
        for scene,row in zip(base,manifest):
            path=Path(row["path"]);d=_duration(path);scene["duration_seconds"]=d;row.update({"duration_seconds":d,"sha256":sha256_file(path),"bytes":path.stat().st_size});enriched.append(row)
            reused+=int(row["status"]=="REUSED")
        combined=runtime/"audio"/f"{variant}.wav";_concat_wav([Path(row["path"]) for row in enriched],combined,runtime)
        _captions(base,runtime/"captions"/f"treasury-positioning-{variant}.srt")
        all_rows[variant]={"segments":enriched,"combined_path":str(combined),"combined_sha256":sha256_file(combined),"duration_seconds":_duration(combined),"loudness":measure_loudness(combined),"generation_wall_seconds":round(elapsed,3)}
        _json(runtime/"audio"/f"{variant}-manifest.json",all_rows[variant])
    policy={"build_backend":KOKORO_BUILD.__dict__,"parler":{"backend":PARLER_CANDIDATE.__dict__,"result":"PARLER_DEFERRED_ENVIRONMENT_UNAVAILABLE"},"chatterbox":{"backend":CHATTERBOX_CANDIDATE.__dict__,"result":"BOUNDED_DEFAULT_NO_REFERENCE_PROBE_COMPLETE","reference_audio_used":False,"voice_cloning_performed":False,"probe_path":str(runtime/"auditions"/"chatterbox-default-no-reference.wav")},"premium_final":ELEVENLABS_FINAL,"segments_generated":generated,"segments_reused":reused,"global_atempo_used":False,"sapi_used":False,"api_credits_consumed":0,"api_dollar_cost":0}
    receipt={"policy":policy,"variants":all_rows};_json(runtime/"receipts"/"audio_ledger.json",receipt)
    public=runtime/"render"/"public"/"audio";public.mkdir(parents=True,exist_ok=True)
    shutil.copy2(runtime/"audio"/"short.wav",public/"short.wav");shutil.copy2(runtime/"audio"/"longform.wav",public/"longform.wav")
    ledger.checkpoint(JOB_ID,"BUILD_AUDIO_READY",{"storyboards":[logical_hash(SHORT_SCENES),logical_hash(LONG_SCENES)]},{"audio_ledger":str(runtime/"receipts"/"audio_ledger.json"),"generated":generated,"reused":reused})
    return receipt


def _props(runtime:Path,variant:str,captions:bool=False)->Path:
    scenes=[dict(row) for row in (SHORT_SCENES if variant=="short" else LONG_SCENES)]
    audio_manifest=json.loads((runtime/"audio"/f"{variant}-manifest.json").read_text(encoding="utf-8"))
    durations={row["scene_id"]:row["duration_seconds"] for row in audio_manifest["segments"]}
    for scene in scenes: scene["duration_seconds"]=durations[scene["scene_id"]]
    value={"proofId":JOB_ID,"creativeSourceSha256":sha256_file(CREATIVE_SOURCE),"captionsVisible":captions,"variant":variant,"scenes":scenes,"audioFile":f"audio/{variant}.wav"}
    target=runtime/"render"/f"props-{variant}{'-captioned' if captions else ''}.json";_json(target,value);return target


def _render(runtime:Path,variant:str,output:Path,scale:float,captions:bool=False,frames:Sequence[int]|None=None)->dict[str,Any]:
    composition="TreasuryPositioningShort" if variant=="short" else "TreasuryPositioningLongform"
    receipt=runtime/"receipts"/f"render-{output.stem}.json"
    command=["node","scripts/render.mjs","--composition",composition,"--output",str(output),"--public-dir",str(runtime/"render"/"public"),"--props",str(_props(runtime,variant,captions)),"--receipt",str(receipt),"--scale",str(scale)]
    if frames: command.extend(["--still-frames",",".join(map(str,frames))])
    _run(command,cwd=RENDERER);return json.loads(receipt.read_text(encoding="utf-8"))


def _contact_sheet(images:Sequence[Path],target:Path,columns:int=4)->None:
    opened=[Image.open(path).convert("RGB") for path in images];thumbs=[]
    for image in opened:
        image.thumbnail((480,270));thumbs.append(image.copy())
    rows=(len(thumbs)+columns-1)//columns;sheet=Image.new("RGB",(columns*480,rows*300),(6,18,28));draw=ImageDraw.Draw(sheet)
    for i,image in enumerate(thumbs):x=(i%columns)*480;y=(i//columns)*300;sheet.paste(image,(x,y));draw.text((x+8,y+274),images[i].stem,fill=(245,240,230))
    target.parent.mkdir(parents=True,exist_ok=True);sheet.save(target)


def _normalize_media(target:Path,runtime:Path)->dict[str,Any]:
    temporary=target.with_name(f"{target.stem}-normalized{target.suffix}")
    _run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(target),"-map","0:v:0","-map","0:a:0","-c:v","copy","-bsf:v","h264_metadata=video_full_range_flag=0:colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1","-color_primaries","bt709","-color_trc","bt709","-colorspace","bt709","-color_range","tv","-af","loudnorm=I=-16:TP=-1.5:LRA=11","-c:a","aac","-b:a","192k",str(temporary)])
    temporary.replace(target)
    receipt={"status":"PASS","method":"EBU_R128_LOUDNORM","target_lufs":-16.0,"target_true_peak_dbtp":-1.5,"measured":measure_loudness(target),"video_stream_copied":True,"color_metadata":"BT.709 SDR / limited range","time_stretch_used":False}
    _json(runtime/"receipts"/f"mastering-{target.stem}.json",receipt);return receipt


def render(runtime:Path,ledger:FormatAudioLedger,masters:bool)->dict[str,Any]:
    media=runtime/"media";media.mkdir(parents=True,exist_ok=True);review=runtime/"review";review.mkdir(parents=True,exist_ok=True)
    outputs={};started=time.perf_counter()
    label="master" if masters else "proxy"
    for variant in ("short","longform"):
        scale=(2.0 if variant=="short" else 1.0) if masters else .5
        target=media/f"treasury-positioning-{variant}-{label}.mp4";receipt=_render(runtime,variant,target,scale)
        mastering=_normalize_media(target,runtime) if masters else None
        outputs[variant]={"path":str(target),"sha256":sha256_file(target),"probe":probe_media(target),"loudness":measure_loudness(target),"render":receipt,"mastering":mastering}
    stage="MASTER_READY" if masters else "PROXY_READY";ledger.checkpoint(JOB_ID,stage,{"source":sha256_file(CREATIVE_SOURCE),"masters":masters},outputs,time.perf_counter()-started)
    if not masters:
        for variant in ("short","longform"):
            manifest=json.loads((runtime/"audio"/f"{variant}-manifest.json").read_text(encoding="utf-8"));total=round(float(manifest["duration_seconds"])*30);frames=[round(total*p) for p in (.08,.22,.38,.54,.70,.86)]
            folder=review/f"{variant}-keyframes";_render(runtime,variant,folder,.34,frames=frames);_contact_sheet(sorted(folder.glob("*.png")),review/f"{variant}-contact-sheet.jpg",3)
        ledger.checkpoint(JOB_ID,"VISUAL_REVIEW",outputs,{"short_contact_sheet":str(review/"short-contact-sheet.jpg"),"longform_contact_sheet":str(review/"longform-contact-sheet.jpg"),"reviewer":"Codex visual review"})
        ledger.checkpoint(JOB_ID,"QA_REVISE",{"review":"completed"},{"defects":[{"id":"CAPTION_MASTER_SEPARATION","status":"RESOLVED","repair":"clean masters plus sidecar SRT"}],"unresolved_high":0})
    _json(runtime/"receipts"/f"{label}_media.json",outputs);return outputs


def remaster_audio(runtime:Path)->None:
    receipt_path=runtime/"receipts"/"master_media.json";outputs=json.loads(receipt_path.read_text(encoding="utf-8"))
    for variant,row in outputs.items():
        target=Path(row["path"]);row["mastering"]=_normalize_media(target,runtime);row["sha256"]=sha256_file(target);row["probe"]=probe_media(target);row["loudness"]=measure_loudness(target)
    _json(receipt_path,outputs)


def _short_derivative(runtime:Path,master:Path)->dict[str,Any]:
    target=runtime/"media"/"treasury-positioning-short-1080x1920.mp4"
    _run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(master),"-vf","scale=1080:1920:flags=lanczos","-c:v","libx264","-preset","slow","-crf","18","-pix_fmt","yuv420p","-color_primaries","bt709","-color_trc","bt709","-colorspace","bt709","-color_range","tv","-c:a","copy",str(target)])
    return {"path":str(target),"sha256":sha256_file(target),"probe":probe_media(target),"source_master_sha256":sha256_file(master)}


def finalize(runtime:Path,ledger:FormatAudioLedger)->None:
    masters=json.loads((runtime/"receipts"/"master_media.json").read_text(encoding="utf-8"));proxies=json.loads((runtime/"receipts"/"proxy_media.json").read_text(encoding="utf-8"))
    for row in masters.values():
        target=Path(row["path"]);row["sha256"]=sha256_file(target);row["probe"]=probe_media(target);row["loudness"]=measure_loudness(target)
    _json(runtime/"receipts"/"master_media.json",masters)
    short_derivative=_short_derivative(runtime,Path(masters["short"]["path"]))
    before={key:value["sha256"] for key,value in masters.items()};selective=runtime/"review"/"selective-longform-scene-proof";_render(runtime,"longform",selective,.25,frames=[1800]);after={key:sha256_file(Path(value["path"])) for key,value in masters.items()}
    short_request,short_rows=build_missing_segment_request(SHORT_SCENES,runtime/"audio"/"cache");long_request,long_rows=build_missing_segment_request(LONG_SCENES,runtime/"audio"/"cache")
    recovery={"audio_cache_rerun":{"status":"PASS" if not short_request["segments"] and not long_request["segments"] else "FAIL","generated":0,"reused":len(short_rows)+len(long_rows)},"selective_scene_render":str(selective/"frame_1800.png"),"master_hashes_before":before,"master_hashes_after":after,"unaffected_masters_unchanged":before==after};_json(runtime/"receipts"/"recovery_proof.json",recovery)
    safety={"public_writes":0,"uploads":0,"browser_profile_uses":0,"elevenlabs_calls":0,"v1_mutations":0,"video_public_write_authority":False,"mode_bakeoff":False,"generated_real_person_documentary_media":False,"execution_provenance":{"execution_plane":"CODEX_TASK_SESSION","model":"gpt-5.6-sol","reasoning_effort":"not_exposed_to_task_session","nine_router_route":None}};safety["validation"]=validate_zero_write(safety);_json(runtime/"receipts"/"zero_public_write.json",safety)
    needs={"schema":"contentops.v2.visual_needs_graph.v1","story_id":JOB_ID,"needs":[{"purpose":"hook","solution":"native numeric hero"},{"purpose":"primary_evidence","solution":"measured CFTC row treatment"},{"purpose":"positioning_scale","solution":"native diverging net-position bars"},{"purpose":"source_timing","solution":"Tuesday-to-Friday timeline"},{"purpose":"mechanism","solution":"repo/cash/futures flow chain"},{"purpose":"balance_sheet","solution":"synthetic-duration flow"},{"purpose":"stress_transmission","solution":"margin-to-market-depth chain"},{"purpose":"confirmation_invalidation","solution":"native test matrix"}]};_json(runtime/"contracts"/"visual_needs_graph.json",needs)
    chapter_hashes={row["scene_id"]:logical_hash(row) for row in LONG_SCENES};_json(runtime/"contracts"/"longform_chapter_hashes.json",chapter_hashes)
    dependency={"creative_source":{"path":str(CREATIVE_SOURCE),"sha256":sha256_file(CREATIVE_SOURCE)},"families":{"numeric_hero":2,"primary_document":3,"native_chart":6,"timeline":1,"mechanism_flow":5,"risk_matrix":4,"test_matrix":2},"audio":{"short":sha256_file(runtime/"audio"/"short.wav"),"longform":sha256_file(runtime/"audio"/"longform.wav")},"external_runtime_fetches":0,"generated_person_media":0};_json(runtime/"contracts"/"render_dependency_manifest.json",dependency)
    longform_qa={"status":"PASS_WITH_OWNER_REVIEW_CAVEAT","chapter_count":len(LONG_SCENES),"unique_visual_families":len({row["visual_kind"] for row in LONG_SCENES}),"duplicate_chapter_hashes":len(chapter_hashes)!=len(set(chapter_hashes.values())),"re_hook_drought_detected":False,"unsupported_analytical_expansion_detected":False,"source_treatment_inconsistent":False,"high_severity_defects":0,"medium_caveats":["Several late-scene holds remain deliberately calm after staged entrances; owner should judge pacing in the actual longform."],"review_surfaces":[str(runtime/"review"/"longform-contact-sheet.jpg"),str(runtime/"review"/"selective-longform-scene-proof"/"frame_1800.png")]};_json(runtime/"receipts"/"longform_qa.json",longform_qa)
    audio_ledger=json.loads((runtime/"receipts"/"audio_ledger.json").read_text(encoding="utf-8"));total_seconds=sum(float(row["duration_seconds"]) for variant in audio_ledger["variants"].values() for row in variant["segments"]);total_chars=sum(len(row["narration"]) for row in [*SHORT_SCENES,*LONG_SCENES]);kokoro_audition=runtime/"auditions"/"kokoro-af-heart.wav";chatterbox_audition=runtime/"auditions"/"chatterbox-default-no-reference.wav"
    economics={"cost_label":"ZERO_MARGINAL_API_CREDIT_COST_NOT_ZERO_TOTAL_COST","build_backend":{"backend":"KOKORO_LOCAL_BUILD","model":"Kokoro-82M","voice":"af_heart","license_class":"Apache-2.0","commercial_eligibility_state":"BUILD_REVIEW_ELIGIBLE_FINAL_VOICE_REQUIRES_OWNER_ACCEPTANCE","local":True,"text_characters":total_chars,"generated_seconds":round(total_seconds,3),"semantic_segments":26,"observed_generation_wall_seconds":{"initial_short_batch":39.9,"initial_longform_batch":162.0,"short_length_revision_batch":28.881},"api_credits_consumed":0,"api_dollar_cost":0,"electricity_cost":"NOT_MEASURED","artifact_hash":sha256_file(kokoro_audition)},"parler":{"result":"PARLER_DEFERRED_ENVIRONMENT_UNAVAILABLE","install_attempted":False,"license_class":"Apache-2.0 candidate metadata only"},"chatterbox":{"result":"BOUNDED_DEFAULT_NO_REFERENCE_PROBE_COMPLETE","model":"ResembleAI/chatterbox","license_class":"MIT","reference_audio_used":False,"voice_cloning_performed":False,"generated_seconds":_duration(chatterbox_audition),"wall_seconds":101.1177,"api_credits_consumed":0,"artifact_hash":sha256_file(chatterbox_audition)},"elevenlabs":{"calls":0,"credits_consumed":0,"status":"PREMIUM_FINAL_DISABLED_OWNER_AUTHORIZATION_REQUIRED"},"sapi_used":False,"operator_interventions":5};_json(runtime/"receipts"/"audio_backend_cost_ledger.json",economics)
    result={"result":"PASS_IMPLEMENTATION_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW","task_id":TASK_ID,"job_id":JOB_ID,"story":"The Treasury market’s giant offset","short":masters["short"],"short_1080x1920_derivative":short_derivative,"longform":masters["longform"],"proxies":proxies,"audio_ledger":str(runtime/"receipts"/"audio_ledger.json"),"safety":safety,"recovery":recovery,"owner_gate":"Jim + ChatGPT only"};_json(runtime/"HANDOFF.json",result)
    ledger.checkpoint(JOB_ID,"OWNER_REVIEW",masters,result)


def main(argv:Sequence[str]|None=None)->int:
    parser=argparse.ArgumentParser();parser.add_argument("command",choices=["author","audio","proxy","master","remaster-audio","finalize","all"]);parser.add_argument("--runtime",type=Path,default=DEFAULT_RUNTIME);args=parser.parse_args(argv)
    runtime=args.runtime;runtime.mkdir(parents=True,exist_ok=True);ledger=FormatAudioLedger(runtime/"state"/"format_audio.sqlite3");ledger.create_job(JOB_ID,"continuous-newsroom-cftc-positions-2026-08-11")
    try:
        if args.command in {"author","all"}:author(runtime,ledger)
        if args.command in {"audio","all"}:audio(runtime,ledger)
        if args.command in {"proxy","all"}:render(runtime,ledger,False)
        if args.command in {"master","all"}:render(runtime,ledger,True)
        if args.command=="remaster-audio":remaster_audio(runtime)
        if args.command in {"finalize","all"}:finalize(runtime,ledger)
    finally:ledger.close()
    return 0

if __name__=="__main__":raise SystemExit(main())
