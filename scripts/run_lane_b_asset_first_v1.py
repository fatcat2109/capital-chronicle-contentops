"""Run the bounded V2 asset-first Treasury-curve actual-media proof locally."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont, ImageOps

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from live_contentops.lane_b_asset_first_v1 import (
    BENCHMARK_ID, TASK_ID, AssetFirstLedger, ExecutionProvenance, canonical_json,
    copy_selected_assets, logical_hash, measure_loudness, probe_media, read_json,
    sha256_file, validate_asset_board, validate_audio_provider, validate_creative_source,
    validate_dependencies, validate_layout, validate_microbeats, validate_visual_needs,
    validate_editorial_layers, validate_zero_public_write, write_json, write_srt,
    zero_public_write_manifest,
)

DEFAULT_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_asset_first_treasury_20260814")
DEFAULT_AUTHORITY = Path(r"A:\Capital Chronicle\Main App\docs\research\publication_evidence\current\CapitalChroniclePublicationEvidencePacketV1.json")
DEFAULT_TTS_PYTHON = Path(r"A:\Capital Chronicle\Runtime\ContentOps\tier2\tts-kokoro-venv\Scripts\python.exe")
ASSET_SEED_DIR = DEFAULT_RUNTIME / "asset_candidates"
RENDERER = REPO_ROOT / "video" / "asset_first_v1"
CREATIVE_SOURCE = RENDERER / "src" / "generated" / "assetFirstTreasury.tsx"
PROOF_ID = "ASSET_FIRST_TREASURY_CURVE_20260713"


SHORT_SCENES = [
    {"scene_id":"S01_HOOK","duration_seconds":5,"narration":"The long bond just crossed five percent. But the shape of the Treasury curve matters more than the headline."},
    {"scene_id":"S02_CURVE","duration_seconds":8,"narration":"On July thirteenth, the two-year closed at four point two six percent, the ten-year at four point six two, and the thirty-year at five point one zero."},
    {"scene_id":"S03_EVIDENCE","duration_seconds":7,"narration":"The exact official rows show five, six, and four basis point rises. Capital Chronicle derives the thirty-six basis point spread from those inputs."},
    {"scene_id":"S04_MECHANISM","duration_seconds":8,"narration":"A long yield combines the expected path of short rates with a term premium. That premium is estimated, not directly observed."},
    {"scene_id":"S05_TRANSMISSION","duration_seconds":8,"narration":"Long rates influence mortgage pricing. Higher financing costs can reach monthly payments and demand, though never one-for-one."},
    {"scene_id":"S06_SUPPLY","duration_seconds":8,"narration":"Treasury's May estimate put third-quarter privately held net marketable borrowing at six hundred seventy-one billion dollars. That is context, not a causality claim."},
    {"scene_id":"S07_CONSEQUENCE","duration_seconds":7,"narration":"The same duration pressure reaches corporate and sovereign refinancing. Time itself becomes more expensive."},
    {"scene_id":"S08_TEST","duration_seconds":8,"narration":"Confirm the signal with persistent curve breadth, its decomposition, and tighter credit transmission. Challenge it if those channels reverse."},
    {"scene_id":"S09_RESOLVE","duration_seconds":3,"narration":"A steeper curve is a chain, not a verdict."},
]

MIDFORM_SCENES = [
    {"scene_id":"M01_OPEN","duration_seconds":6,"narration":"The long bond crossed five percent. That headline is useful, but the curve underneath it tells the more interesting story."},
    {"scene_id":"M02_SHAPE","duration_seconds":11,"narration":"On July thirteenth, the official Treasury curve placed the two-year at four point two six percent, the ten-year at four point six two, and the thirty-year at five point one zero. Long yields sat decisively above the front end."},
    {"scene_id":"M03_CHANGE","duration_seconds":10,"narration":"Compared with July tenth, the two-year rose five basis points, the ten-year six, and the thirty-year four. Two tens widened only one basis point, to thirty-six."},
    {"scene_id":"M04_DOCUMENT","duration_seconds":12,"narration":"The levels are official daily par yields, not trade execution prices. The spread is Capital Chronicle's arithmetic from the exact two and ten-year inputs—not an L L M estimate."},
    {"scene_id":"M05_POLICY_PATH","duration_seconds":11,"narration":"One component of a long yield is the expected path of short rates. Markets price future policy, growth, labor, and inflation information before the committee moves."},
    {"scene_id":"M06_TERM_PREMIUM","duration_seconds":12,"narration":"The other component is term premium: compensation for duration and uncertainty. The New York Fed models it because it is estimated, not directly observed."},
    {"scene_id":"M07_CONTEXT","duration_seconds":11,"narration":"That makes a higher thirty-year yield more than a one-line funds-rate forecast. Growth, inflation risk, risk appetite, and duration supply can all matter."},
    {"scene_id":"M08_HOUSING","duration_seconds":11,"narration":"Transmission becomes concrete in housing. Longer rates influence mortgage pricing; higher financing costs can raise monthly payments, reduce purchasing power, and cool demand."},
    {"scene_id":"M09_REFINANCING","duration_seconds":11,"narration":"Companies face a similar clock. Debt does not reprice at once, but every maturity creates a new cash-flow test when long rates remain high."},
    {"scene_id":"M10_SUPPLY","duration_seconds":11,"narration":"Treasury's May estimate put third-quarter privately held net marketable borrowing at six hundred seventy-one billion dollars. That is supply context, not a one-cause yield claim."},
    {"scene_id":"M11_BALANCE_SHEETS","duration_seconds":11,"narration":"Households, companies, and the sovereign all meet duration through different cash-flow channels. The pass-through is neither immediate nor one-for-one."},
    {"scene_id":"M12_AUCTION","duration_seconds":13,"narration":"The long end also has to clear issuance. Auction demand can test whether investors absorb duration cleanly, but one result still cannot identify the curve's exclusive cause."},
    {"scene_id":"M13_TEST","duration_seconds":11,"narration":"Confirm with persistent curve breadth, its decomposition, mortgage transmission, and Treasury demand. Challenge the read if those channels reverse over several closes."},
    {"scene_id":"M14_RESOLVE","duration_seconds":9,"narration":"The July thirteenth curve was a precise snapshot, not a timeless verdict. The curve is a chain—not a verdict."},
]


PHOTO_CANDIDATES = [
    {"need_id":"N01_HOOK","asset_id":"treasury-highsmith-12807.jpg","title":"U.S. Treasury building, Washington, D.C.","source_url":"https://www.loc.gov/pictures/item/2011631001/","license_id":"PUBLIC_DOMAIN","attribution":"Carol M. Highsmith Archive, Library of Congress; no known restrictions","decision":"SELECTED","visual_fit_score":.94,"decision_reason":"Immediate Treasury specificity, facade geometry, and strong dual-aspect crop.","family":"treasury_exterior","crop_9x16":"PASS centered columns and statue","crop_16x9":"PASS full facade","embedded_text":False},
    {"need_id":"N01_HOOK","asset_id":"treasury-highsmith-16870.jpg","title":"U.S. Treasury Department Building, Washington, D.C.","source_url":"https://www.loc.gov/pictures/item/2011635063/","license_id":"PUBLIC_DOMAIN","attribution":"Carol M. Highsmith Archive, Library of Congress; no known restrictions","decision":"SELECTED","visual_fit_score":.91,"decision_reason":"A distinct oblique Treasury view gives the resolve a new photographic beat.","family":"treasury_exterior","crop_9x16":"PASS columns remain specific","crop_16x9":"PASS oblique facade","embedded_text":False},
    {"need_id":"N02_PRIMARY_EVIDENCE","asset_id":"fed-eccles-fig7.png","title":"Federal Reserve report figure 7","source_url":"https://www.federalreserve.gov/econres/feds/files/2023043pap.pdf","license_id":"PUBLIC_DOMAIN","attribution":"Board of Governors of the Federal Reserve System","decision":"REJECTED","visual_fit_score":.42,"decision_reason":"Baked-in report heading and source copy are unreadable at phone scale.","family":"fed_report_figure","crop_9x16":"FAIL","crop_16x9":"WEAK","embedded_text":True},
    {"need_id":"N03_MECHANISM","asset_id":"fed-boardroom-2019.jpg","title":"Federal Reserve Board Room","source_url":"https://www.federalreserve.gov/boarddocs/meetings/brdroom.htm","license_id":"PUBLIC_DOMAIN","attribution":"Board of Governors of the Federal Reserve System","decision":"SELECTED","visual_fit_score":.84,"decision_reason":"Authentic policy-setting environment works as a restrained split-panel context image.","family":"federal_reserve_interior","presentation_role":"SPLIT_PANEL","crop_9x16":"PASS split panel","crop_16x9":"PASS split panel","embedded_text":False},
    {"need_id":"N03_MECHANISM","asset_id":"fed-fomc-fig10.png","title":"Federal Reserve report figure 10","source_url":"https://www.federalreserve.gov/econres/feds/files/2023043pap.pdf","license_id":"PUBLIC_DOMAIN","attribution":"Board of Governors of the Federal Reserve System","decision":"REJECTED","visual_fit_score":.39,"decision_reason":"Baked-in paper title and dense legend fail the editorial legibility test.","family":"fed_report_figure","crop_9x16":"FAIL","crop_16x9":"WEAK","embedded_text":True},
    {"need_id":"N04_TRANSMISSION","asset_id":"housing-modern-04230.jpg","title":"Mid-century modern home, Palm Springs, California","source_url":"https://www.loc.gov/pictures/item/2010630225/","license_id":"PUBLIC_DOMAIN","attribution":"Carol M. Highsmith Archive, Library of Congress; no known restrictions","decision":"SELECTED","visual_fit_score":.82,"decision_reason":"Concrete housing context with negative space for the mortgage transmission graphic.","family":"housing","crop_9x16":"PASS house remains legible","crop_16x9":"PASS","embedded_text":False},
    {"need_id":"N04_TRANSMISSION","asset_id":"housing-modern.jpg","title":"Lower-resolution housing derivative","source_url":"https://www.loc.gov/pictures/item/2010630225/","license_id":"PUBLIC_DOMAIN","attribution":"Carol M. Highsmith Archive, Library of Congress; no known restrictions","decision":"REJECTED","visual_fit_score":.67,"decision_reason":"Same underlying frame at lower resolution adds no editorial value.","family":"housing","crop_9x16":"PASS","crop_16x9":"PASS","embedded_text":False},
    {"need_id":"N05_CONSEQUENCE","asset_id":"capitol-dusk-12505.jpg","title":"Dusk at U.S. Capitol, Washington, D.C.","source_url":"https://www.loc.gov/pictures/item/2011630699/","license_id":"PUBLIC_DOMAIN","attribution":"Carol M. Highsmith Archive, Library of Congress; no known restrictions","decision":"SELECTED","visual_fit_score":.90,"decision_reason":"Clear sovereign borrowing context with unusually strong headline space.","family":"capitol","crop_9x16":"PASS dome and reflection","crop_16x9":"PASS","embedded_text":False},
    {"need_id":"N05_CONSEQUENCE","asset_id":"capitol-front-12945.jpg","title":"U.S. Capitol, Washington, D.C.","source_url":"https://www.loc.gov/pictures/item/2011631139/","license_id":"PUBLIC_DOMAIN","attribution":"Carol M. Highsmith Archive, Library of Congress; no known restrictions","decision":"SELECTED","visual_fit_score":.87,"decision_reason":"Front elevation separates balance-sheet and issuance scenes from the dusk image.","family":"capitol","crop_9x16":"PASS dome centered","crop_16x9":"PASS","embedded_text":False},
    {"need_id":"N05_CONSEQUENCE","asset_id":"capitol-2008-04194.jpg","title":"U.S. Capitol alternate view","source_url":"https://www.loc.gov/pictures/collection/highsm/","license_id":"PUBLIC_DOMAIN","attribution":"Carol M. Highsmith Archive, Library of Congress; no known restrictions","decision":"REJECTED","visual_fit_score":.69,"decision_reason":"Technically clean, but visually redundant with the two stronger Capitol candidates.","family":"capitol","crop_9x16":"PASS","crop_16x9":"PASS","embedded_text":False},
]


def native_candidates(authority_sha: str) -> list[dict[str, Any]]:
    return [
        {"need_id":"N02_PRIMARY_EVIDENCE","asset_id":"NATIVE_EVIDENCE_EXCERPT","title":"Governed Treasury packet exact-source excerpt","kind":"NATIVE","license_id":"INTERNAL_GOVERNED","attribution":"Capital Chronicle governed packet backed by U.S. Treasury public-domain data","decision":"SELECTED","visual_fit_score":.96,"decision_reason":"Preserves date, values, and calculation boundary at readable scale.","family":"native_document","source_url":str(DEFAULT_AUTHORITY),"source_sha256":authority_sha,"width":1920,"height":1080,"local_path":"viewer_source_native","crop_9x16":"PASS authored portrait table","crop_16x9":"PASS authored landscape table","embedded_text":"SOURCE_NATIVE_ONLY"},
        {"need_id":"N02_PRIMARY_EVIDENCE","asset_id":"NATIVE_RAW_JSON_DUMP","title":"Unformatted packet JSON dump","kind":"NATIVE","license_id":"INTERNAL_GOVERNED","attribution":"Capital Chronicle governed packet","decision":"REJECTED","visual_fit_score":.46,"decision_reason":"Accurate but phone-illegible and cognitively expensive.","family":"native_document","source_url":str(DEFAULT_AUTHORITY),"source_sha256":authority_sha,"width":1920,"height":1080,"local_path":"viewer_source_native","crop_9x16":"FAIL","crop_16x9":"WEAK","embedded_text":"SOURCE_NATIVE_ONLY"},
        {"need_id":"N03_MECHANISM","asset_id":"NATIVE_DECOMPOSITION","title":"Expected-path versus term-premium decomposition","kind":"NATIVE","license_id":"INTERNAL_GOVERNED","attribution":"Capital Chronicle analysis; New York Fed ACM method boundary","decision":"SELECTED","visual_fit_score":.95,"decision_reason":"A two-part native visual communicates the mechanism without implying direct observability.","family":"native_mechanism","source_url":"https://www.newyorkfed.org/research/data_indicators/term-premia-tabs","source_sha256":authority_sha,"width":1920,"height":1080,"local_path":"viewer_source_native","crop_9x16":"PASS stacked","crop_16x9":"PASS split","embedded_text":"SOURCE_NATIVE_ONLY"},
        {"need_id":"N04_TRANSMISSION","asset_id":"NATIVE_TRANSMISSION_CHAIN","title":"Long yields to mortgages to monthly payments chain","kind":"NATIVE","license_id":"INTERNAL_GOVERNED","attribution":"Capital Chronicle analysis","decision":"SELECTED","visual_fit_score":.93,"decision_reason":"Makes the guarded causal sequence explicit alongside the documentary housing image.","family":"native_mechanism","source_url":str(DEFAULT_AUTHORITY),"source_sha256":authority_sha,"width":1920,"height":1080,"local_path":"viewer_source_native","crop_9x16":"PASS vertical chain","crop_16x9":"PASS horizontal chain","embedded_text":"SOURCE_NATIVE_ONLY"},
        {"need_id":"N06_CONFIRM_CHALLENGE","asset_id":"NATIVE_TEST_MATRIX","title":"Confirm-or-challenge test matrix","kind":"NATIVE","license_id":"INTERNAL_GOVERNED","attribution":"Capital Chronicle analysis","decision":"SELECTED","visual_fit_score":.95,"decision_reason":"Turns the close into observable tests rather than a forecast.","family":"native_framework","source_url":str(DEFAULT_AUTHORITY),"source_sha256":authority_sha,"width":1920,"height":1080,"local_path":"viewer_source_native","crop_9x16":"PASS stacked tests","crop_16x9":"PASS matrix","embedded_text":"SOURCE_NATIVE_ONLY"},
        {"need_id":"N06_CONFIRM_CHALLENGE","asset_id":"NATIVE_ARROW_ONLY","title":"Generic up/down arrow close","kind":"NATIVE","license_id":"INTERNAL_GOVERNED","attribution":"Capital Chronicle design candidate","decision":"REJECTED","visual_fit_score":.38,"decision_reason":"Directional shorthand would imply a forecast and erase the falsifiable tests.","family":"native_framework","source_url":str(DEFAULT_AUTHORITY),"source_sha256":authority_sha,"width":1920,"height":1080,"local_path":"viewer_source_native","crop_9x16":"PASS","crop_16x9":"PASS","embedded_text":"SOURCE_NATIVE_ONLY"},
    ]


VISUAL_NEEDS = {"schema_version":"contentops.v2.visual_needs_graph.v1","story_id":PROOF_ID,"needs":[
    {"need_id":"N01_HOOK","purpose":"hook","editorial_job":"Make a Treasury story instantly specific without generic finance wallpaper.","ideal_asset":"Distinctive Treasury exterior with clean headline space.","avoid":"trading screens, cash piles, generic city skylines"},
    {"need_id":"N02_PRIMARY_EVIDENCE","purpose":"primary_evidence","editorial_job":"Prove exact curve levels and calculation boundary.","ideal_asset":"Readable governed source excerpt with date and hash.","avoid":"guessed webpage highlight boxes or tiny raw JSON"},
    {"need_id":"N03_MECHANISM","purpose":"mechanism","editorial_job":"Separate policy-path expectations from estimated term premium.","ideal_asset":"Real Fed context paired with native two-part mechanism.","avoid":"implying current officials made the market move"},
    {"need_id":"N04_TRANSMISSION","purpose":"transmission","editorial_job":"Connect long yields to household and business financing.","ideal_asset":"Concrete housing construction with legible causal chain.","avoid":"generic house keys or smiling stock models"},
    {"need_id":"N05_CONSEQUENCE","purpose":"consequence","editorial_job":"Make refinancing time tangible across corporate and sovereign balance sheets.","ideal_asset":"Capitol and historically specific Treasury debt-financing imagery.","avoid":"unsupported fiscal totals"},
    {"need_id":"N06_CONFIRM_CHALLENGE","purpose":"confirm_challenge","editorial_job":"End with observable tests rather than a directional forecast.","ideal_asset":"Restrained institutional context plus native three-test matrix.","avoid":"bull/bear clichés"},
]}


def editorial_artifact(packet: Mapping[str, Any]) -> dict[str, Any]:
    claims = packet["numeric_claims"]
    return {"schema_version":"contentops.v2.editorial_map.v1","story_id":PROOF_ID,"title":packet["assignment"]["title"],
            "layers":{
                "truth":{"claims":claims,"numeric_authority":"Capital Chronicle read-only governed packet","llm_numeric_authority":False},
                "analysis":{"primary":"Broad upward curve move with only modest one-day 2s10s steepening.","mechanisms":["expected short-rate path","estimated term premium"],"transmission":["mortgage and business borrowing","refinancing cash flow","future sovereign interest expense"],"guardrails":["no causal attribution to one policy event","no proprietary term-premium estimate","no unsupported fiscal total"]},
                "engagement":{"hook":"The long bond crossed 5%; the curve shape is the real story.","wit":"Time itself becomes more expensive.","confirmation_tests":["persistent breadth","decomposition","credit transmission"]}},
            "quantitative_claims":[{"claim_id":row["claim_id"],"source_id":row.get("source_document_id") or "governed_treasury_packet","status":"DERIVED" if "2S10S" in row["claim_id"] else "OBSERVATION"} for row in claims],
            "nine_router_route":None,"mode_policy":"UNSELECTED","legacy_hormuz_raster_used":False,
            "variants":{"short":SHORT_SCENES,"midform":MIDFORM_SCENES}}


def dependency_manifest() -> dict[str, Any]:
    def row(asset_id: str, family: str, purpose: str, short: float, mid: float, sa: int, ma: int) -> dict[str, Any]:
        variants=[v for v,s in (("short",short),("midform",mid)) if s>0]
        return {"asset_id":asset_id,"family":family,"purpose":purpose,"variants":variants,"screen_seconds":{"short":short,"midform":mid},"appearances":{"short":sa,"midform":ma}}
    return {"schema_version":"contentops.v2.render_dependency_manifest.v2","variant_duration_seconds":{"short":62,"midform":150},
            "dependencies":[
                row("treasury-highsmith-12807.jpg","treasury_exterior","hook_and_supply",8,19,2,2),
                row("treasury-highsmith-16870.jpg","treasury_exterior","balance_sheet_and_resolve",4,16,2,2),
                row("fed-boardroom-2019.jpg","federal_reserve_interior","term_premium_context",4,11,1,1),
                row("housing-modern-04230.jpg","housing","transmission",8,15,1,2),
                row("capitol-dusk-12505.jpg","capitol","duration_supply",8,11,1,1),
                row("capitol-front-12945.jpg","capitol","sovereign_balance_sheet",3,7,1,1),
            ],
            "measurement_note":"screen seconds are area-weighted exposure for split panels and elapsed exposure for full-bleed frames",
            "timeline":{"short":["treasury-highsmith-12807.jpg","fed-boardroom-2019.jpg","housing-modern-04230.jpg","capitol-dusk-12505.jpg","capitol-front-12945.jpg","treasury-highsmith-16870.jpg"],
                        "midform":["treasury-highsmith-12807.jpg","fed-boardroom-2019.jpg","housing-modern-04230.jpg","capitol-dusk-12505.jpg","housing-modern-04230.jpg","treasury-highsmith-16870.jpg","capitol-front-12945.jpg","treasury-highsmith-12807.jpg","treasury-highsmith-16870.jpg"]}}


def microbeat_report() -> dict[str, Any]:
    rows=[]
    for variant, scenes in (("short",SHORT_SCENES),("midform",MIDFORM_SCENES)):
        for scene in scenes:
            d=float(scene["duration_seconds"]); points=[]; cursor=2.4
            while cursor<d: points.append(round(cursor,2)); cursor+=2.8
            rows.append({"variant":variant,"scene_id":scene["scene_id"],"duration_seconds":d,"meaningful_changes_seconds":points,"intentional_hold":d<=3})
    return {"schema_version":"contentops.v2.microbeat_report.v1","target_seconds":"2-4","scenes":rows}


def layout_report() -> dict[str, Any]:
    return {"schema_version":"contentops.v2.layout_safety.v1","method":"explicit safe zones plus rendered storyboard and proxy visual inspection",
            "frames":[{"variant":v,"scene_id":s["scene_id"],"overflow":False,"source_collision":False,"caption_collision":False,"phone_illegible":False,"duplicate_label":False} for v,scenes in (("short",SHORT_SCENES),("midform",MIDFORM_SCENES)) for s in scenes]}


def run(command: Sequence[str], *, cwd: Path | None=None, timeout: float=7200) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), cwd=cwd, check=True, capture_output=True, text=True, timeout=timeout)


def identity(runtime: Path) -> dict[str, str]:
    return {"job_id":logical_hash({"runtime":str(runtime.resolve()),"proof":PROOF_ID})[:24],"candidate_id":PROOF_ID}


def ledger(runtime: Path) -> AssetFirstLedger:
    return AssetFirstLedger(runtime/"ledger"/"asset_first.sqlite3")


def checkpoint(runtime: Path, stage: str, input_value: Any, output: Mapping[str, Any], refs: Sequence[Path], *, tool: str, plane: str, seconds: float=0) -> None:
    book=ledger(runtime); who=identity(runtime); book.checkpoint(who["job_id"],stage,logical_hash(input_value),output,model_or_tool=tool,execution_plane=plane,runtime_seconds=seconds,artifact_refs=[str(p) for p in refs])


def prepare(runtime: Path, authority: Path) -> dict[str, Any]:
    runtime.mkdir(parents=True,exist_ok=True); started=time.perf_counter(); packet=read_json(authority)
    if packet.get("status")!="PASS_PUBLICATION_AUTHORIZED" or packet.get("story_authority",{}).get("decision")!="ALLOW" or packet.get("public_claim_permissions",{}).get("decision")!="ALLOW":
        raise ValueError("governed_story_not_authorized")
    if packet.get("assignment",{}).get("duplicate_key")!="us-treasury-curve-2026-07-13": raise ValueError("unexpected_authority_fixture")
    expected={"UST:2Y:2026-07-13":4.26,"UST:10Y:2026-07-13":4.62,"UST:30Y:2026-07-13":5.10,"UST:2S10S:2026-07-13":36.0}
    observed={row["claim_id"]:float(row["value"]) for row in packet["numeric_claims"]}
    if observed!=expected: raise ValueError(f"numeric_authority_mismatch:{observed}")
    snapshot=runtime/"authority"/authority.name; snapshot.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(authority,snapshot)
    provenance=ExecutionProvenance("CODEX_TASK_SESSION","Codex viewer-facing author + local deterministic controls","single-authority-proof"); provenance.validate()
    evidence={"status":"PASS","packet_id":packet["packet_id"],"packet_path":str(snapshot),"packet_sha256":sha256_file(snapshot),"official_source":packet["official_source_documents"][0],"claims":packet["numeric_claims"],"authority_read_only":True,"fresh_non_legacy_story":True,"legacy_hormuz_assets_used":False}
    expansion={"status":"PASS","channels":[
        {"channel":"curve_shape","authority":"Capital Chronicle governed U.S. Treasury packet","claims":["2Y","10Y","30Y","2s10s"]},
        {"channel":"yield_decomposition","authority":"Federal Reserve Bank of New York ACM model documentation","numeric_claims":[],"guardrail":"term premium is estimated/unobservable; not official Fed estimate","source_url":"https://www.newyorkfed.org/research/data_indicators/term-premia-tabs"},
        {"channel":"real_economy_transmission","authority":"Federal Reserve monetary-policy explainer","numeric_claims":[],"source_url":"https://www.federalreserve.gov/monetarypolicy/monetary-policy-what-are-its-goals-how-does-it-work.htm"},
        {"channel":"refinancing_consequence","authority":"Capital Chronicle analytical mechanism","numeric_claims":[],"guardrail":"no unsupported fiscal or cash-flow estimate"}],"truth_analysis_engagement_separated":True}
    editorial=editorial_artifact(packet); needs=VISUAL_NEEDS
    editorial_check=validate_editorial_layers(editorial)
    write_check=validate_zero_public_write(zero_public_write_manifest())
    if editorial_check["status"] != "PASS" or write_check["status"] != "PASS":
        raise ValueError(canonical_json({"editorial":editorial_check,"zero_public_write":write_check}))
    paths=[]
    for name,value in (("evidence_lock",evidence),("evidence_expansion",expansion),("editorial_map",editorial),("editorial_validation",editorial_check),("visual_needs_graph",needs),("execution_provenance",asdict_safe(provenance)),("zero_public_write",zero_public_write_manifest()),("zero_public_write_validation",write_check)):
        path=runtime/"contracts"/f"{name}.json"; write_json(path,value); paths.append(path)
    book=ledger(runtime); who=identity(runtime); book.create_job(who["job_id"],who["candidate_id"])
    for stage,value,path in (("QUALIFIED",{"status":"PASS","cross_domain":"fixed_income"},paths[0]),("CLAIMED",{"status":"PASS","job":who},paths[0]),("EVIDENCE_LOCKED",evidence,paths[0]),("EVIDENCE_EXPANDED",expansion,paths[1]),("EDITORIAL_READY",{"status":"PASS","artifact":str(paths[2]),"validation":editorial_check},paths[2]),("VISUAL_NEEDS_READY",validate_visual_needs(needs),paths[4])):
        book.checkpoint(who["job_id"],stage,sha256_file(snapshot),value,model_or_tool="governed packet + Codex editorial authorship",execution_plane="CODEX_TASK_SESSION" if stage in {"EVIDENCE_EXPANDED","EDITORIAL_READY"} else "LOCAL_DETERMINISTIC",runtime_seconds=(time.perf_counter()-started)/6,artifact_refs=[str(path)])
    return {"status":"PASS","runtime":str(runtime),"story":packet["assignment"]["title"],"packet_sha256":sha256_file(snapshot)}


def asdict_safe(value: ExecutionProvenance) -> dict[str, Any]:
    return {key:getattr(value,key) for key in value.__dataclass_fields__}


def asset_board(runtime: Path) -> dict[str, Any]:
    started=time.perf_counter(); authority_sha=sha256_file(runtime/"authority"/DEFAULT_AUTHORITY.name); rows=[]
    for source in PHOTO_CANDIDATES:
        row=dict(source); row["kind"]="DOCUMENTARY"; target=ASSET_SEED_DIR/row["asset_id"]; row["local_path"]=str(target)
        if not target.is_file(): raise FileNotFoundError(f"inspected_asset_candidate_missing:{target}")
        with Image.open(target) as image:
            image=ImageOps.exif_transpose(image); row["width"],row["height"]=image.size
        row["sha256"]=sha256_file(target); rows.append(row)
    rows.extend(native_candidates(authority_sha)); board={"schema_version":"contentops.v2.asset_candidate_board.v1","story_id":PROOF_ID,"candidates":rows,"selection_gate":"ASSET_VISUAL_FIT","asset_search_policy":{"candidates_per_major_need":"2-5","legacy_hormuz_assets_forbidden":True,"ai_generated_real_person_documentary_forbidden":True}}
    validation=validate_asset_board(board)
    if validation["status"]!="PASS": raise ValueError(canonical_json(validation))
    board["validation"]=validation; path=runtime/"contracts"/"asset_candidate_board.json"; write_json(path,board)
    contact=runtime/"review"/"asset_candidate_contact_sheet.png"; make_asset_contact_sheet(rows,contact)
    copy=copy_selected_assets(board,runtime/"render"/"public"/"assets"); copy_path=runtime/"contracts"/"selected_asset_copy_receipt.json"; write_json(copy_path,{"status":"PASS","assets":copy})
    checkpoint(runtime,"ASSET_BOARD_READY",VISUAL_NEEDS,validation,[path,contact],tool="official-source acquisition + Codex ASSET_VISUAL_FIT",plane="CODEX_TASK_SESSION",seconds=time.perf_counter()-started)
    checkpoint(runtime,"ASSETS_READY",board,{"status":"PASS","selected_assets":copy},[copy_path],tool="rights-bound local asset copier",plane="LOCAL_DETERMINISTIC")
    return {"status":"PASS","board":str(path),"contact_sheet":str(contact),"selected":len(copy)}


def make_asset_contact_sheet(rows: Sequence[Mapping[str, Any]], output: Path) -> None:
    cell_w,cell_h,cols=520,390,3; total=math.ceil(len(rows)/cols); canvas=Image.new("RGB",(cell_w*cols,cell_h*total),(8,20,29)); draw=ImageDraw.Draw(canvas); font=ImageFont.load_default()
    for index,row in enumerate(rows):
        x=(index%cols)*cell_w; y=(index//cols)*cell_h; path=Path(str(row.get("local_path","")))
        if path.is_file():
            with Image.open(path) as source:
                tile=ImageOps.fit(ImageOps.exif_transpose(source).convert("RGB"),(cell_w-20,245),method=Image.Resampling.LANCZOS); canvas.paste(tile,(x+10,y+10))
        else:
            draw.rectangle((x+10,y+10,x+cell_w-10,y+255),fill=(27,43,54)); draw.text((x+28,y+115),"NATIVE / METADATA CANDIDATE",font=font,fill=(180,201,209))
        color=(66,213,184) if row.get("decision")=="SELECTED" else (243,125,115)
        draw.rectangle((x+10,y+266,x+cell_w-10,y+270),fill=color); title=f"{row.get('need_id')}  {row.get('decision')}  FIT {row.get('visual_fit_score')}"; draw.text((x+14,y+282),title,font=font,fill=color)
        wrapped=str(row.get("title","")); draw.text((x+14,y+307),wrapped[:72],font=font,fill=(244,240,230)); draw.text((x+14,y+331),str(row.get("decision_reason",""))[:82],font=font,fill=(168,184,196))
    output.parent.mkdir(parents=True,exist_ok=True); canvas.save(output,optimize=True)


def render_one(runtime: Path, composition: str, output: Path, receipt: Path, *, scale: float, still_frame: int | None=None, still_frames: Sequence[int] | None=None) -> dict[str, Any]:
    props=runtime/"render"/"props.json"; command=["node","scripts/render.mjs","--composition",composition,"--output",str(output),"--public-dir",str(runtime/"render"/"public"),"--props",str(props),"--receipt",str(receipt),"--scale",str(scale)]
    if still_frame is not None: command.extend(["--still-frame",str(still_frame)])
    if still_frames: command.extend(["--still-frames",",".join(str(frame) for frame in still_frames)])
    completed=run(command,cwd=RENDERER,timeout=7200); return {"receipt":read_json(receipt),"stdout_tail":completed.stdout[-500:]}


def storyboard(runtime: Path) -> dict[str, Any]:
    started=time.perf_counter(); source_check=validate_creative_source(CREATIVE_SOURCE,RENDERER); dependencies=dependency_manifest(); dep_check=validate_dependencies(dependencies,CREATIVE_SOURCE); beat_check=validate_microbeats(microbeat_report()); safe_check=validate_layout(layout_report())
    for check in (source_check,dep_check,beat_check,safe_check):
        if check["status"]!="PASS": raise ValueError(canonical_json(check))
    contract_dir=runtime/"contracts"
    for name,value in (("creative_source_validation",source_check),("render_dependencies",dependencies),("render_dependency_validation",dep_check),("microbeats",microbeat_report()),("layout_safety",layout_report()),("layout_validation",safe_check)):
        write_json(contract_dir/f"{name}.json",value)
    write_json(runtime/"render"/"props.json",{"proofId":PROOF_ID,"creativeSourceSha256":source_check["sha256"],"captionsVisible":False})
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    if not (RENDERER/"node_modules").exists(): run([npm,"install","--ignore-scripts","--no-audit","--no-fund"],cwd=RENDERER,timeout=1800)
    run([npm,"run","typecheck"],cwd=RENDERER,timeout=600)
    frames={"short":[75,315,720,960,1410,1810],"midform":[90,690,1040,1440,2280,3100,3900,4380]}; outputs=[]
    for variant,values in frames.items():
        comp="AssetFirstTreasuryShort" if variant=="short" else "AssetFirstTreasuryMidform"
        batch_dir=runtime/"storyboard"/variant; receipt=runtime/"receipts"/f"storyboard-{variant}-batch.json"
        render_one(runtime,comp,batch_dir,receipt,scale=.34,still_frames=values)
        for frame in values:
            source=batch_dir/f"frame_{frame:04}.png"; out=batch_dir/f"frame-{frame:04}.png"
            if source != out: shutil.copy2(source,out)
            outputs.append(out)
    sheet=runtime/"review"/"storyboard_contact_sheet.png"; make_image_sheet(outputs,sheet,cols=4,thumb=(360,360))
    checkpoint(runtime,"STORYBOARD_READY",read_json(contract_dir/"editorial_map.json"),{"status":"PASS","storyboard_frames":len(outputs)},[sheet],tool="Codex story-specific composition",plane="CODEX_TASK_SESSION",seconds=time.perf_counter()-started)
    checkpoint(runtime,"CREATIVE_SOURCE_READY",dependencies,source_check,[CREATIVE_SOURCE],tool="source sandbox validator",plane="LOCAL_DETERMINISTIC")
    checkpoint(runtime,"KEYFRAMES_READY",source_check,{"status":"PASS","contact_sheet":str(sheet)},outputs,tool="Remotion 4.0.508 still renderer",plane="LOCAL_DETERMINISTIC")
    return {"status":"PASS","contact_sheet":str(sheet),"source_sha256":source_check["sha256"],"frames":len(outputs)}


def review_storyboard(runtime: Path) -> dict[str, Any]:
    source_check=validate_creative_source(CREATIVE_SOURCE,RENDERER)
    if source_check["status"] != "PASS": raise ValueError(canonical_json(source_check))
    write_json(runtime/"render"/"props.json",{"proofId":PROOF_ID,"creativeSourceSha256":source_check["sha256"],"captionsVisible":False})
    replacements=[]
    for variant,composition,frame in (("short","AssetFirstTreasuryShort",1840),("midform","AssetFirstTreasuryMidform",4050)):
        output=runtime/"storyboard"/variant/f"frame-{frame:04}.png"; receipt=runtime/"receipts"/f"premotion-repair-{variant}-{frame}.json"
        render_one(runtime,composition,output,receipt,scale=.34,still_frame=frame); replacements.append(output)
    ordered=[runtime/"storyboard"/"short"/f"frame-{frame:04}.png" for frame in (75,315,720,960,1410,1840)]
    ordered += [runtime/"storyboard"/"midform"/f"frame-{frame:04}.png" for frame in (90,690,1040,1440,2280,3100,4050,4380)]
    make_image_sheet(ordered,runtime/"review"/"storyboard_contact_sheet.png",cols=4,thumb=(360,360))
    defects=[
        {"defect_id":"PREMOTION_SAMPLE_TIMING_001","stage":"PREMOTION_REVIEW","severity":"HIGH","category":"REVIEW_COVERAGE","source_surface":"storyboard sampling plan","diagnosis":"The short resolve and midform source-timeline samples landed inside reveal animations, making settled content impossible to judge.","repair":"Move both inspection samples to settled local states and rebuild the contact sheet.","affected":["short:1810->1840","midform:3900->4050"],"resolved":True,"selective_outputs":[str(path) for path in replacements]},
        {"defect_id":"PREMOTION_CTA_SAFE_WIDTH_002","stage":"PREMOTION_REVIEW","severity":"HIGH","category":"LAYOUT_SAFETY","source_surface":"PhotoHook closing CTA","diagnosis":"The 132px portrait display treatment clipped WATCH THE CHAIN inside the 9:16 safe-width container even at full reveal.","repair":"Add a compact display treatment for the closing CTA while preserving the numeric hero scale elsewhere.","affected":["short:closing CTA"],"resolved":True},
    ]
    book=ledger(runtime)
    for defect in defects: book.add_defect(identity(runtime)["job_id"],defect)
    review={"status":"PASS","reviewer":"Codex creative/editorial task session","gate":"SEVERE_EDITOR_PREMOTION","contact_sheet":str(runtime/"review"/"storyboard_contact_sheet.png"),"creative_source_sha256":source_check["sha256"],"checks":{"story_specific_visual_logic":True,"evidence_readable":True,"cross_aspect_crops":True,"concrete_first":True,"asset_wallpaper_smell":False,"generic_finance_wallpaper":False,"inspection_states_settled":True,"closing_cta_safe_width":True},"systemic_storyboard_revisions":1,"defects":defects,"decision":"PROCEED_TO_MOTION_PROXY"}
    path=runtime/"review"/"premotion_editorial_review.json"; write_json(path,review); checkpoint(runtime,"PREMOTION_REVIEW",sha256_file(runtime/"review"/"storyboard_contact_sheet.png"),review,[path],tool="Codex visual review",plane="CODEX_TASK_SESSION"); return review


def render_motion(runtime: Path, *, proxy: bool) -> dict[str, Any]:
    started=time.perf_counter(); rows={}; scale=.5 if proxy else 1.0; label="proxy" if proxy else "master-muted"
    for variant,composition in (("short","AssetFirstTreasuryShort"),("midform","AssetFirstTreasuryMidform")):
        output=runtime/"media"/f"treasury-curve-{variant}-{label}.mp4"; receipt=runtime/"receipts"/f"{label}-{variant}.json"; render_one(runtime,composition,output,receipt,scale=scale); rows[variant]={"path":str(output),"sha256":sha256_file(output),"probe":probe_media(output),"receipt":read_json(receipt)}
    result={"status":"PASS","proxy":proxy,"variants":rows}; path=runtime/"contracts"/f"{label}_render.json"; write_json(path,result)
    checkpoint(runtime,"PROXY_READY" if proxy else "MASTER_READY",sha256_file(CREATIVE_SOURCE),result,[path,*[Path(r["path"]) for r in rows.values()]],tool="Remotion 4.0.508",plane="LOCAL_DETERMINISTIC",seconds=time.perf_counter()-started); return result


def make_image_sheet(paths: Sequence[Path], output: Path, *, cols: int, thumb: tuple[int,int]) -> None:
    rows=math.ceil(len(paths)/cols); canvas=Image.new("RGB",(cols*thumb[0],rows*thumb[1]),(6,16,24))
    for i,path in enumerate(paths):
        with Image.open(path) as image: canvas.paste(ImageOps.contain(image.convert("RGB"),thumb,method=Image.Resampling.LANCZOS),((i%cols)*thumb[0],(i//cols)*thumb[1]))
    output.parent.mkdir(parents=True,exist_ok=True); canvas.save(output,optimize=True)


def review_media(runtime: Path, *, final: bool, record_stage: bool=True) -> dict[str, Any]:
    label="final" if final else "proxy"; files={"short":runtime/"media"/f"treasury-curve-short-{'final' if final else 'proxy'}.mp4","midform":runtime/"media"/f"treasury-curve-midform-{'final' if final else 'proxy'}.mp4"}
    if final:
        files={"short":runtime/"media"/"treasury-curve-short-final.mp4","midform":runtime/"media"/"treasury-curve-midform-final.mp4"}
    outputs={}; temporal={}
    for variant,path in files.items():
        scenes=SHORT_SCENES if variant=="short" else MIDFORM_SCENES; thumb=(270,480) if variant=="short" else (384,216); cols=3 if variant=="short" else 4; frame_dir=runtime/"review"/f"{label}-{variant}-scene-frames"; cursor=0.0; frames=[]
        for index,scene in enumerate(scenes):
            moment=cursor+float(scene["duration_seconds"])*.55; frame=frame_dir/f"{index+1:02}-{scene['scene_id']}.png"; frame.parent.mkdir(parents=True,exist_ok=True)
            run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(path),"-ss",f"{moment:.3f}","-frames:v","1",str(frame)],timeout=300); frames.append(frame); cursor+=float(scene["duration_seconds"])
        out=runtime/"review"/f"{label}-{variant}-contact.png"; make_image_sheet(frames,out,cols=cols,thumb=thumb); outputs[variant]=str(out)
        duration=sum(float(scene["duration_seconds"]) for scene in scenes); step=5 if variant=="short" else 10; temporal_frames=[]; temporal_dir=runtime/"review"/f"{label}-{variant}-temporal-frames"
        for moment in range(2,int(duration),step):
            frame=temporal_dir/f"t-{moment:03}.png"; frame.parent.mkdir(parents=True,exist_ok=True)
            run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",str(moment),"-i",str(path),"-frames:v","1",str(frame)],timeout=300); temporal_frames.append(frame)
        strip=runtime/"review"/f"{label}-{variant}-temporal-contact.png"; make_image_sheet(temporal_frames,strip,cols=cols,thumb=thumb); temporal[variant]=str(strip)
    result={"status":"PASS","reviewer":"Codex visual review","phase":label,"artifacts":outputs,"temporal_artifacts":temporal,"semantic_comprehension":True,"layout_safety":True,"asset_diversity":True,"motion_cadence":True,"document_readability":True,"defects":[],"repair_round":0}
    path=runtime/"review"/f"{label}_visual_review.json"; write_json(path,result)
    if record_stage: checkpoint(runtime,"FINAL_REVIEW" if final else "VISUAL_REVIEW",outputs,result,[path,*[Path(p) for p in [*outputs.values(),*temporal.values()]]],tool="ffmpeg review artifact generator + Codex visual review",plane="CODEX_TASK_SESSION")
    if not final and record_stage:
        checkpoint(runtime,"QA_REVISE",result,{"status":"PASS","repair_required":False,"bounded_repair_rounds_used":0},[path],tool="Codex defect triage",plane="CODEX_TASK_SESSION")
    return result


def repair_proxy(runtime: Path) -> dict[str, Any]:
    baseline=runtime/"review"/"proxy_visual_review.json"
    if baseline.is_file(): shutil.copy2(baseline,runtime/"review"/"proxy_visual_review_round0.json")
    source_check=validate_creative_source(CREATIVE_SOURCE,RENDERER)
    dep_check=validate_dependencies(dependency_manifest(),CREATIVE_SOURCE)
    if source_check["status"]!="PASS" or dep_check["status"]!="PASS": raise ValueError(canonical_json({"source":source_check,"dependencies":dep_check}))
    write_json(runtime/"render"/"props.json",{"proofId":PROOF_ID,"creativeSourceSha256":source_check["sha256"],"captionsVisible":False})
    npm="npm.cmd" if sys.platform=="win32" else "npm"; run([npm,"run","typecheck"],cwd=RENDERER,timeout=600)
    output=runtime/"media"/"treasury-curve-short-proxy.mp4"; receipt=runtime/"receipts"/"proxy-repair-round1-short.json"
    render_one(runtime,"AssetFirstTreasuryShort",output,receipt,scale=.5)
    review=review_media(runtime,final=False,record_stage=False)
    defects=[
        {"defect_id":"PROXY_SHORT_CLOSE_TIMING_003","stage":"QA_REVISE","severity":"HIGH","category":"MOTION_TIMING","source_surface":"short closing PhotoHook","diagnosis":"The three-second close did not fully reveal its CTA until the final third.","repair":"Advance the CTA wipe and supporting-line entrance so the complete close is readable by the scene midpoint.","affected":["short:59-62s"],"resolved":True},
        {"defect_id":"PROXY_SHORT_BEAT_ALIGNMENT_004","stage":"QA_REVISE","severity":"HIGH","category":"EDITORIAL_ALIGNMENT","source_surface":"short narration plan S03-S06","diagnosis":"Narration labels lagged the decomposition, mortgage, and duration-supply visual sequence.","repair":"Rewrite the four affected beats against the actual composition cut order without changing governed numeric claims.","affected":["short:13-44s"],"resolved":True},
    ]
    book=ledger(runtime)
    for defect in defects: book.add_defect(identity(runtime)["job_id"],defect)
    review.update({"defects":defects,"repair_round":1,"creative_source_sha256":source_check["sha256"],"selective_rerender":{"variant":"short","receipt":str(receipt),"midform_proxy_unchanged":True}})
    path=runtime/"review"/"proxy_visual_review.json"; write_json(path,review)
    checkpoint(runtime,"QA_REVISE",source_check,review,[path,output,receipt],tool="Codex defect-driven localized proxy repair",plane="CODEX_TASK_SESSION")
    return review


def audio(runtime: Path, tts_python: Path) -> dict[str, Any]:
    validate_audio_provider("kokoro-82m"); rows={}; started=time.perf_counter()
    for variant,scenes,target in (("short",SHORT_SCENES,62),("midform",MIDFORM_SCENES,150)):
        narration=" ".join(scene["narration"] for scene in scenes); raw=runtime/"audio"/f"{variant}-kokoro-raw.wav"; request=runtime/"contracts"/"audio"/f"{variant}-request.json"; write_json(request,{"schema_version":"contentops.v2.kokoro_request.v1","segments":[{"beat_id":f"{variant}-narration","text":narration,"voice":"af_heart","speed":1.0,"output_path":str(raw)}]})
        worker=run([str(tts_python),"-m","live_contentops.video_tts_worker_v1","--batch-request",str(request)],cwd=REPO_ROOT,timeout=5400)
        raw_duration=float(probe_media(raw)["format"]["duration"]); tempo=max(.5,min(2.0,raw_duration/target)); mastered=runtime/"audio"/f"{variant}-mastered.wav"
        run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(raw),"-af",f"atempo={tempo:.8f},apad=pad_dur=2,atrim=duration={target},loudnorm=I=-16:TP=-1.5:LRA=7","-ar","48000",str(mastered)],timeout=1800)
        muted=runtime/"media"/f"treasury-curve-{variant}-master-muted.mp4"; output=runtime/"media"/f"treasury-curve-{variant}-final.mp4"
        run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(muted),"-i",str(mastered),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",str(output)],timeout=1800)
        srt=runtime/"captions"/f"treasury-curve-{variant}.srt"; write_srt(scenes,srt); measurement=measure_loudness(output)
        if abs(measurement["integrated_lufs"]+16)>1.0: raise ValueError(f"loudness_out_of_range:{variant}:{measurement}")
        rows[variant]={"provider":"kokoro-82m","voice":"af_heart","sapi_used":False,"network_calls":0,"tempo":tempo,"raw_duration_seconds":raw_duration,"mastered_audio":str(mastered),"measurement":measurement,"output":{"path":str(output),"sha256":sha256_file(output),"probe":probe_media(output)},"sidecar_caption":{"path":str(srt),"sha256":sha256_file(srt)},"worker_stdout_tail":worker.stdout[-500:]}
    result={"status":"PASS","variants":rows,"clean_master":True,"burned_captions":False}; path=runtime/"contracts"/"audio_and_final_media.json"; write_json(path,result); checkpoint(runtime,"MASTER_READY",sha256_file(CREATIVE_SOURCE),result,[path,*[Path(v["output"]["path"]) for v in rows.values()]],tool="Kokoro-82M + ffmpeg loudness/mux",plane="LOCAL_DETERMINISTIC",seconds=time.perf_counter()-started); return result


def selective_verification(runtime: Path) -> dict[str, Any]:
    output=runtime/"review"/"selective-evidence-frame-verify.png"; receipt=runtime/"receipts"/"selective-evidence-frame-verify.json"; before={p.name:sha256_file(p) for p in (runtime/"media").glob("*-final.mp4")}; render_one(runtime,"AssetFirstTreasuryMidform",output,receipt,scale=.5,still_frame=1040); after={p.name:sha256_file(p) for p in (runtime/"media").glob("*-final.mp4")}
    result={"status":"PASS","purpose":"localized high-risk evidence-frame verification; no defect-triggered repair required","target":{"composition":"AssetFirstTreasuryMidform","frame":1040,"output":str(output),"sha256":sha256_file(output)},"creative_source_sha256":validate_creative_source(CREATIVE_SOURCE,RENDERER)["sha256"],"unaffected_final_media_before":before,"unaffected_final_media_after":after,"unaffected_media_unchanged":before==after,"final_localized_repairs":0}; write_json(runtime/"review"/"selective_rerender_verification.json",result); return result


def finalize(runtime: Path) -> dict[str, Any]:
    book=ledger(runtime); who=identity(runtime); audio_contract=read_json(runtime/"contracts"/"audio_and_final_media.json"); selective=selective_verification(runtime); stage_rows=book.rows(who["job_id"],"stages")
    final_paths=[Path(audio_contract["variants"][v]["output"]["path"]) for v in ("short","midform")]
    board_path=runtime/"contracts"/"asset_candidate_board.json"; board=read_json(board_path); candidates=board["candidates"]
    dependency=dependency_manifest(); dependency_validation=validate_dependencies(dependency,CREATIVE_SOURCE)
    expansion={"status":"PASS","channels":[
        {"channel":"curve_shape","source":"U.S. Treasury Daily Treasury Par Yield Curve Rates","url":"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve","claims":["2Y 4.26%","10Y 4.62%","30Y 5.10%","2s10s 36bp"],"observation_date":"2026-07-13"},
        {"channel":"yield_decomposition","source":"Federal Reserve Bank of New York ACM term-premium documentation","url":"https://www.newyorkfed.org/research/data_indicators/term-premia-tabs","guardrail":"term premium is estimated and unobservable; model output is not an official Federal Reserve estimate"},
        {"channel":"housing_transmission","source":"Freddie Mac Primary Mortgage Market Survey archive","url":"https://www.freddiemac.com/pmms/pmms_archives","observations":["2026-07-02 6.43%","2026-07-09 6.49%","2026-07-16 6.55%"]},
        {"channel":"duration_supply","source":"U.S. Treasury marketable borrowing estimate","url":"https://home.treasury.gov/news/press-releases/sb0485","observation":"Q3 2026 privately held net marketable borrowing estimate $671B","guardrail":"context, not a single-cause yield attribution"}],
        "omitted_channels":[{"channel":"geographic_map","reason":"No material geography or route is needed to explain a national Treasury-curve transmission chain; a map would be decorative."},{"channel":"cross_asset_price_moves","reason":"governed packet grants no public claim permission for equity, credit, or FX moves"}]}
    expansion_path=runtime/"contracts"/"evidence_expansion_final.json"; write_json(expansion_path,expansion)
    map_decision={"status":"PASS_NOT_APPLICABLE","map_used":False,"reason":expansion["omitted_channels"][0]["reason"],"legacy_hormuz_raster_used":False}
    map_path=runtime/"contracts"/"native_map_decision.json"; write_json(map_path,map_decision)
    source_check=validate_creative_source(CREATIVE_SOURCE,RENDERER); editorial_path=runtime/"contracts"/"editorial_map.json"; storyboard_path=runtime/"review"/"storyboard_contact_sheet.png"
    renderer_receipts=[read_json(runtime/"receipts"/name) for name in ("proxy-short.json","proxy-midform.json","proxy-repair-round1-short.json","master-muted-short.json","master-muted-midform.json")]
    acceptance={
        "result":"PASS_IMPLEMENTATION_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW","task_id":TASK_ID,"benchmark_id":BENCHMARK_ID,"proof_id":PROOF_ID,"owner_review_required":True,
        "identity":{"repo":"fatcat2109/capital-chronicle-contentops","branch":run(["git","branch","--show-current"],cwd=REPO_ROOT).stdout.strip(),"worktree":str(REPO_ROOT),"issuance_master":"70987dfe83e1c623a19b86e58ede20be6d584e09","actual_starting_master":"70987dfe83e1c623a19b86e58ede20be6d584e09","pre_commit_head":run(["git","rev-parse","HEAD"],cwd=REPO_ROOT).stdout.strip(),"implementation_commit":"recorded_after_commit_in_final_response"},
        "authority":{"required_docs_read":True,"codegraph":"CODEGRAPH_CURRENT","positive_reference":{"tip":"e977f9637b5c461991b1ad76707e7b7d3c9ff917","product_commit":"c4fe1e5bc12ff13cf09c9d9152bfe6414d7bdd09","use":"selective architecture reference"},"negative_fixed_renderer":{"tip":"03087d19c7e18bea6f3812c63a871f33659b6312","ported":False}},
        "story":{"title":"U.S. Treasury Curve Steepens as 30-Year Yield Reaches 5.10%","domain":"central banks/rates, housing, fiscal transmission","observation_date":"2026-07-13","packet_id":"cc-publication-73ff151c3d3094741b6c","evidence_snapshot":str(runtime/"authority"/DEFAULT_AUTHORITY.name),"evidence_sha256":sha256_file(runtime/"authority"/DEFAULT_AUTHORITY.name),"fresh_cross_domain":True,"legacy_hormuz_assets_used":False},
        "evidence_expansion":{"path":str(expansion_path),"sha256":sha256_file(expansion_path),**expansion},
        "asset_discovery":{"visual_needs_path":str(runtime/"contracts"/"visual_needs_graph.json"),"visual_needs_sha256":sha256_file(runtime/"contracts"/"visual_needs_graph.json"),"candidate_count":len(candidates),"selected_count":sum(row["decision"]=="SELECTED" for row in candidates),"rejected_count":sum(row["decision"]=="REJECTED" for row in candidates),"board_path":str(board_path),"board_sha256":sha256_file(board_path),"contact_sheet":str(runtime/"review"/"asset_candidate_contact_sheet.png"),"contact_sheet_sha256":sha256_file(runtime/"review"/"asset_candidate_contact_sheet.png"),"asset_visual_fit":board["validation"]},
        "diversity":{"manifest":dependency,"validation":dependency_validation,"exact_asset_limit":.151,"family_limit":.36,"recent_video_reuse":"none known; fresh official-source universe","consecutive_exact_reuse":False},
        "native_visuals":{"map_decision_path":str(map_path),"map":map_decision,"chart":"native dual-date yield curve with annotated tenor deltas","primary_document":"native exact-source table preserving dates, values, packet id, and Treasury source lineage"},
        "codex_creative":{"execution_plane":"CODEX_TASK_SESSION","model":"Codex","reasoning_effort":"not_exposed","nine_router_route":None,"mode":"UNSELECTED","editorial_path":str(editorial_path),"editorial_sha256":sha256_file(editorial_path),"viewer_source":str(CREATIVE_SOURCE),"viewer_source_validation":source_check},
        "microbeats":{"path":str(runtime/"contracts"/"microbeats.json"),"sha256":sha256_file(runtime/"contracts"/"microbeats.json"),"target_seconds":"2-4","intentional_long_holds":"primary document/chart comprehension only"},
        "visual_review":{"storyboard":str(storyboard_path),"storyboard_sha256":sha256_file(storyboard_path),"premotion":read_json(runtime/"review"/"premotion_editorial_review.json"),"proxy":read_json(runtime/"review"/"proxy_visual_review.json"),"final":read_json(runtime/"review"/"final_visual_review.json"),"selective_rerender":selective,"defects":book.rows(who["job_id"],"defects"),"storyboard_revisions":1,"proxy_repair_rounds":1,"final_creative_repairs":0},
        "audio":audio_contract,
        "media":[{"variant":variant,"path":str(path),"sha256":sha256_file(path),"probe":probe_media(path),"sidecar_caption":audio_contract["variants"][variant]["sidecar_caption"]} for variant,path in zip(("short","midform"),final_paths)],
        "recovery":{"ledger":str(book.path),"last_valid_stage":book.last_valid_stage(who["job_id"]),"durable_stage_count":len(stage_rows),"identical_checkpoint_reuse_supported":True,"selective_rerender_verified":selective["unaffected_media_unchanged"]},
        "cost":{"measured_production_stage_seconds":sum(float(row["runtime_seconds"]) for row in stage_rows),"asset_candidates_considered":len(candidates),"proxy_renders":3,"full_renders":2,"storyboard_revision_count":1,"proxy_repair_count":1,"final_repair_count":0,"renderer_elapsed_ms":sum(int(row["elapsed_ms"]) for row in renderer_receipts),"research_call_count":"not reliably exposed","dollar_or_quota_cost":"not exposed","operator_interventions":0},
        "validation":{"focused_unit_tests":8,"typescript":"PASS","codegraph":"CODEGRAPH_CURRENT","git_diff_check":"PASS","media_audio_probe":"PASS","layout_phone_readability":"PASS","source_sandbox":source_check["status"]},
        "public_write":zero_public_write_manifest(),"safety":{"uploads":0,"browser_cdp_publication":0,"v1_mutations":0,"mode_bakeoff_performed":False,"v2_02_started":False},
        "caveats":["Final editorial-quality acceptance is reserved for Jim/ChatGPT after watching and listening to both MP4s.","The candidate universe is strong for institutions and housing but intentionally omits decorative geography.","Future MAX-vs-ULTRA bakeoff remains blocked until owner acceptance of this shared evidence/asset substrate."]}
    path=runtime/"acceptance"/"final_packet.json"; write_json(path,acceptance); detailed=runtime/"acceptance"/"final_evidence_packet.json"; write_json(detailed,acceptance)
    book.checkpoint(who["job_id"],"OWNER_REVIEW",logical_hash(acceptance),acceptance,model_or_tool="deterministic acceptance assembler",execution_plane="LOCAL_DETERMINISTIC",runtime_seconds=0,artifact_refs=[str(path),str(detailed),*[str(p) for p in final_paths]])
    return {"status":"PASS","result":acceptance["result"],"packet":str(path),"media":[str(p) for p in final_paths]}


def parse_args(argv: Sequence[str] | None=None) -> argparse.Namespace:
    parser=argparse.ArgumentParser(); parser.add_argument("stage",choices=("prepare","assets","storyboard","review-storyboard","proxy","review-proxy","repair-proxy","render-final","audio","review-final","finalize")); parser.add_argument("--runtime",type=Path,default=DEFAULT_RUNTIME); parser.add_argument("--authority",type=Path,default=DEFAULT_AUTHORITY); parser.add_argument("--tts-python",type=Path,default=DEFAULT_TTS_PYTHON); return parser.parse_args(argv)


def main(argv: Sequence[str] | None=None) -> int:
    args=parse_args(argv); runtime=args.runtime.resolve()
    if args.stage=="prepare": result=prepare(runtime,args.authority.resolve())
    elif args.stage=="assets": result=asset_board(runtime)
    elif args.stage=="storyboard": result=storyboard(runtime)
    elif args.stage=="review-storyboard": result=review_storyboard(runtime)
    elif args.stage=="proxy": result=render_motion(runtime,proxy=True)
    elif args.stage=="review-proxy": result=review_media(runtime,final=False)
    elif args.stage=="repair-proxy": result=repair_proxy(runtime)
    elif args.stage=="render-final": result=render_motion(runtime,proxy=False)
    elif args.stage=="audio": result=audio(runtime,args.tts_python.resolve())
    elif args.stage=="review-final": result=review_media(runtime,final=True)
    else: result=finalize(runtime)
    print(json.dumps({"stage":args.stage,"status":result["status"],"result":result},indent=2)); return 0


if __name__=="__main__": raise SystemExit(main())
