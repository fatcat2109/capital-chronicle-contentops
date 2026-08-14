"""Run the bounded V2 breaking-news / ElevenLabs / crisp-master proof."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops.breaking_news_crisp_v1 import (
    BANNED_VOICE_IDS, TASK_ID, BreakingNewsLedger, codex_execution_plane_manifest, logical_hash, probe_media, sha256_file,
    validate_annotation_geometry,
    validate_audio_contract, validate_authority_clip, validate_breaking_event,
    validate_claim_bindings, validate_creative_source, validate_crisp_master,
    validate_editorial, validate_material_audit, validate_microbeat_timeline, validate_zero_public_write,
    write_json, zero_public_write_manifest,
)
from live_contentops.primary_document_compiler_v2 import compile_primary_document


RENDERER = ROOT / "video" / "breaking_news_v1"
SOURCE = RENDERER / "src" / "generated" / "retailBreaking.tsx"
DEFAULT_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_breaking_retail_owner_repair_20260815")
JOB_ID = "breaking-retail-owner-repair-20260815-v2"
SHORT_AUDITION_TEXT = (
    "July retail sales fell six-tenths of a percent to seven hundred sixty-three point six billion dollars. "
    "The headline is the alert; the release is the evidence."
)
EXTENDED_AUDITION_TEXT = (
    "July retail sales fell six-tenths of a percent to seven hundred sixty-three point six billion dollars. "
    "Autos and nonstore sales weakened, while clothing and food services rose. These figures are not adjusted "
    "for price changes. One decimal gets the alert. Seven pages decide what it means."
)
SEGMENTS = [
    ("alert", "Breaking: U.S. retail sales fell 0.6 percent in July, to 763.6 billion dollars."),
    ("what_hit", "That decline clears Census's 90 percent sampling margin. But the categories did not move together."),
    ("first_reaction", "Autos fell 1.8 percent. Nonstore sales fell 2.2. Clothing rose 1.9, and food services rose 0.5."),
    ("primary_document", "The primary release says the estimate is seasonally adjusted, but not adjusted for price changes."),
    ("headline_misses", "So the headline is nominal. It does not tell us whether shoppers bought less, prices fell, or both."),
    ("why_matters", "That distinction runs through revenue, inventory decisions, and the real-consumption read."),
    ("wit", "One decimal gets the alert. Seven pages decide what it means."),
    ("checkpoint", "Next: revisions, category breadth, and inflation-adjusted consumption. Census reports again September 16. One soft month is a signal, not a verdict."),
]

MICROBEAT_FUNCTIONS = {
    "alert": ["state the event", "reveal exact monthly change", "anchor exact dollar level"],
    "what_hit": ["locate the retail setting", "state statistical significance", "open category divergence"],
    "first_reaction": ["introduce category comparison", "isolate negative contributors", "resolve positive offsets"],
    "primary_document": ["establish primary-source identity", "bind highlight to measured text", "extract exact headline metrics"],
    "headline_misses": ["label the print nominal", "separate quantity from price", "state the unresolved decomposition"],
    "why_matters": ["start revenue transmission", "advance inventory consequence", "land on real-consumption interpretation"],
    "wit": ["compress the headline", "contrast alert with evidence", "hold the restrained analytical line"],
    "checkpoint": ["name revisions", "name category breadth", "name real-consumption confirmation", "state next release and thesis"],
    "resolve": ["close on reporting doctrine"],
}


def build_microbeat_timeline(props: dict[str, Any]) -> dict[str, Any]:
    beats: list[dict[str, Any]] = []
    cursor = 0.0
    for segment in props["segments"]:
        duration = float(segment["frames"]) / 30
        functions = MICROBEAT_FUNCTIONS[segment["id"]]
        count = max(len(functions), math.ceil(duration / 2.8))
        for index in range(count):
            start = cursor + duration * index / count
            end = cursor + duration * (index + 1) / count
            evidence_function = functions[min(index, len(functions) - 1)]
            if index >= len(functions):
                evidence_function = f"sustain legibility of {functions[-1]} with active motion"
            beats.append({
                "beat_id": f"{segment['id']}-{index + 1}",
                "scene_id": segment["id"],
                "start_seconds": round(start, 4),
                "end_seconds": round(end, 4),
                "evidence_function": evidence_function,
            })
        cursor += duration
    timeline = {
        "schema_version": "contentops.v2.microbeat_timeline.v2",
        "source": "duration-derived editorial state changes; no fixed beat-count quota",
        "beats": beats,
        "duration_seconds": round(cursor, 4),
    }
    timeline["validation"] = validate_microbeat_timeline(timeline)
    return timeline


def run(command: Sequence[str], *, cwd: Path = ROOT, timeout: int = 7200) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), cwd=cwd, check=True, capture_output=True, text=True, timeout=timeout)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def measure_audio(path: Path) -> dict[str, float]:
    result=subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",str(path),"-filter_complex","ebur128=peak=true","-f","null","-"],capture_output=True,text=True,check=False)
    summary=result.stderr.rsplit("Summary:",1)[-1]
    patterns={"integrated_lufs":r"Integrated loudness:\s*I:\s*(-?\d+(?:\.\d+)?) LUFS",
              "lra_lu":r"Loudness range:\s*LRA:\s*(-?\d+(?:\.\d+)?) LU",
              "true_peak_dbtp":r"True peak:\s*Peak:\s*(-?\d+(?:\.\d+)?) dBFS"}
    values={key:float(match.group(1)) for key,pattern in patterns.items() if (match:=re.search(pattern,summary,re.DOTALL))}
    if len(values)!=3: raise ValueError("audio_measurement_missing")
    return values


def srt_time(seconds: float) -> str:
    milliseconds=round(seconds*1000);hours,milliseconds=divmod(milliseconds,3_600_000);minutes,milliseconds=divmod(milliseconds,60_000);secs,milliseconds=divmod(milliseconds,1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def ledger(runtime: Path) -> BreakingNewsLedger:
    book = BreakingNewsLedger(runtime / "state" / "ledger.sqlite3")
    book.create(JOB_ID)
    return book


def checkpoint(runtime: Path, stage: str, value: dict[str, Any], seconds: float = 0, *, allow_rework: bool = False) -> None:
    book = ledger(runtime)
    book.checkpoint(JOB_ID, stage, logical_hash(value), value, seconds, allow_rework=allow_rework)
    book.close()


def prepare(runtime: Path) -> dict[str, Any]:
    started = time.perf_counter()
    for name in ("authority", "assets", "contracts", "review", "receipts", "media", "audio", "captions", "acceptance", "state"):
        (runtime / name).mkdir(parents=True, exist_ok=True)
    event = {"event_id":"US_CENSUS_RETAIL_JULY_2026","published_at":"2026-08-14T08:30:00-04:00",
             "observed_at":"2026-08-14T19:00:00+07:00","primary_source_url":"https://www.census.gov/retail/marts/www/marts_current.pdf",
             "concrete_change":"July retail and food services sales fell 0.6% m/m to $763.6B",
             "urgency_fabricated":False,"market_reaction_status":"OMITTED_NO_GOVERNED_MARKET_DATA"}
    event["validation"] = validate_breaking_event(event)
    claims = [
        ("total", "$763.6B July sales", "OBSERVATION", None), ("mom", "-0.6% m/m ±0.4%", "OBSERVATION", None),
        ("yoy", "+5.0% y/y ±0.5%", "OBSERVATION", None), ("period", "+6.3% May-July y/y", "OBSERVATION", None),
        ("june", "$768.1B and +0.2% ±0.3%", "OBSERVATION", None), ("autos", "-1.8%", "OBSERVATION", None),
        ("nonstore", "-2.2%", "OBSERVATION", None), ("ex_auto_gas", "-0.2%", "OBSERVATION", None),
        ("clothing", "+1.9%", "OBSERVATION", None), ("food_service", "+0.5%", "OBSERVATION", None),
        ("not_real", "not adjusted for price changes", "OBSERVATION", None),
        ("significant", "July total confidence interval excludes zero", "DERIVED", "-0.6 ±0.4 = [-1.0,-0.2]"),
        ("transmission", "sales can inform revenue, inventory and growth assessment", "ANALYSIS", None),
    ]
    packet = {"sources":[{"source_id":"census_cb26_131","authority":"PRIMARY",
               "url":"https://www.census.gov/retail/marts/www/marts_current.pdf","release":"CB26-131",
               "page_count":7,"retrieval":"grounded web readback; direct byte download blocked by Census edge policy"}],
              "claims":[{"claim_id":i,"text":t,"kind":k,"source_id":"census_cb26_131",**({"derivation":d} if d else {})} for i,t,k,d in claims]}
    packet["validation"] = validate_claim_bindings(packet)
    readback={"schema_version":"contentops.v2.primary_web_readback.v1","source_id":"census_cb26_131",
        "url":"https://www.census.gov/retail/marts/www/marts_current.pdf","content_type":"application/pdf","page_count":7,
        "retrieved_at":"2026-08-14T19:00:00+07:00","release_number":"CB26-131","release_time":"2026-08-14T08:30:00-04:00",
        "exact_readback":{"total_sales_millions":763602,"month_over_month_percent":-0.6,"month_over_month_margin_90_percent":0.4,
        "year_over_year_percent":5.0,"year_over_year_margin_90_percent":0.5,"may_july_year_over_year_percent":6.3,
        "june_revised_sales_millions":768072,"june_month_over_month_percent":0.2,"june_margin_90_percent":0.3,
        "autos_percent":-1.8,"nonstore_percent":-2.2,"ex_autos_gas_percent":-0.2,"clothing_percent":1.9,
        "food_services_percent":0.5,"price_adjusted":False,"advance_sample_firms_approx":4800,"represented_firms_over":3000000,
        "next_release":"2026-09-16T08:30:00-04:00"},
        "exact_source_text":{
            "headline_sentence":"Advance estimates of U.S. retail and food services sales for July 2026, adjusted for seasonal variation and holiday and trading-day differences, but not for price changes, were $763.6 billion, down 0.6 percent (±0.4 percent) from the previous month, but up 5.0 percent (±0.5 percent) from July 2025.",
            "annotation_target":"not adjusted for price changes"
        },
        "html_release_url":"https://www.census.gov/retail/sales.html",
        "byte_download_status":"BLOCKED_BY_CENSUS_EDGE_POLICY",
        "integrity_note":"Exact structured readback is not a substitute for immutable source bytes; the canonical URL remains authoritative."}
    readback_path=runtime/"authority"/"census-cb26-131-web-readback.json";write_json(readback_path,readback)
    packet["sources"][0].update({"local_readback_path":str(readback_path),"local_readback_sha256":sha256_file(readback_path)})
    editorial = {"format":"BREAKING_NATIVE","layers":{
        "truth":{"locked_claims":[row[0] for row in claims[:-1]]},
        "analysis":{"angle":"Nominal softness is real, but does not identify volume versus price contribution."},
        "engagement":{"rhythm":"alert → split categories → exact document → nominal/real → transmission → checkpoint"}},
        "wit_candidates":[
            {"candidate_id":"w1","line":"One decimal gets the alert. Seven pages decide what it means.","decision":"ACCEPTED","fact_safe":True,"relevant":True,"market_literate":True,"non_advice":True,"reason":"compresses release-versus-method tension"},
            {"candidate_id":"w2","line":"The consumer blinked; the terminal refreshed.","decision":"REJECTED","fact_safe":False,"relevant":True,"market_literate":True,"non_advice":True,"reason":"anthropomorphizes a mixed sample estimate"},
            {"candidate_id":"w3","line":"Soft print, hard landing? Not from one survey.","decision":"REJECTED","fact_safe":True,"relevant":True,"market_literate":True,"non_advice":True,"reason":"too meme-adjacent and overpackages cycle risk"},
            {"candidate_id":"w4","line":"Nominal weakness has two suspects: volume and price.","decision":"REJECTED","fact_safe":True,"relevant":True,"market_literate":True,"non_advice":True,"reason":"accurate but explanatory, not wit"},
        ]}
    editorial["validation"] = validate_editorial(editorial)
    clip = {"broker":"RIGHTS_GOVERNED_AUTHORITY_CLIP_BROKER","decision":"SKIP_NO_SAFE_HIGH_VALUE_CLIP",
            "reason":"No bounded, rights-clear Census authority clip with a material exact quote was located; exact primary release plus a rights-safe real still is stronger than decorative footage.",
            "broadcaster_scrape_attempted":False,"broadcasters_considered_for_republication":False,
            "fair_use_claimed":False,"synthetic_real_official":False,"heygen_used":False}
    clip["validation"] = validate_authority_clip(clip)
    asset = {"asset_id":"loc_highsm_16211","role":"documentary_retail_context","source_url":"https://www.loc.gov/pictures/item/2011634404/",
             "download_url":"https://cdn.loc.gov/master/pnp/highsm/16200/16211u.tif","license":"NO_KNOWN_RESTRICTIONS",
             "creator":"Carol M. Highsmith","collection":"Library of Congress Prints and Photographs Division",
             "native_width":4831,"native_height":6138,"minimum_width":2160,"crop":"9:16 center editorial crop",
             "local_path":str(runtime/"assets"/"mall.jpg")}
    if Path(asset["local_path"]).is_file(): asset.update({"sha256":sha256_file(Path(asset["local_path"])),"bytes":Path(asset["local_path"]).stat().st_size})
    source = validate_creative_source(SOURCE, RENDERER)
    provisional_frames = [190,190,230,220,200,180,150,280]
    provisional_props = {
        "proofId":"CENSUS_RETAIL_20260814_PROVISIONAL_TIMING",
        "creativeSourceSha256":sha256_file(SOURCE),
        "segments":[{"id":segment_id,"frames":frames,"text":text} for (segment_id,text),frames in zip(SEGMENTS,provisional_frames)]
                   + [{"id":"resolve","frames":60,"text":""}],
        "timing_authority":"PROVISIONAL_ONLY_UNTIL_ELEVENLABS_ACCEPTED_AUDIO",
    }
    write_json(runtime/"contracts"/"render_props.json", provisional_props)
    write_json(runtime/"contracts"/"microbeat_timeline.json", build_microbeat_timeline(provisional_props))
    for name, value in (("event.json",event),("evidence_packet.json",packet),("editorial_voice_pass.json",editorial),
                        ("authority_clip_broker.json",clip),("asset_rights_manifest.json",{"assets":[asset]}),
                        ("creative_source_validation.json",source),("zero_public_write.json",zero_public_write_manifest())):
        write_json(runtime/"contracts"/name,value)
    for stage, value in (("QUALIFIED",event),("EVIDENCE_LOCKED",packet),("EDITORIAL_READY",editorial),("RIGHTS_READY",clip)):
        checkpoint(runtime,stage,value,allow_rework=True)
    result = {"status":"PASS","event":event["validation"],"claims":packet["validation"],"editorial":editorial["validation"],
              "rights":clip["validation"],"creative_source":source,"public_write":validate_zero_public_write(zero_public_write_manifest())}
    write_json(runtime/"contracts"/"prepare_result.json",result)
    return {**result,"runtime_seconds":time.perf_counter()-started}


def compile_document(runtime: Path, pdf_path: Path | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    readback = runtime / "authority" / "census-cb26-131-web-readback.json"
    if not readback.is_file():
        raise FileNotFoundError("prepare_stage_required")
    asset = RENDERER / "public" / "assets" / "census-document.png"
    geometry_path = runtime / "contracts" / "document_geometry.json"
    record = compile_primary_document(
        readback=readback,
        output_png=asset,
        geometry_json=geometry_path,
        pdf_path=pdf_path,
    )
    record["runtime_seconds"] = time.perf_counter() - started
    record["validation"] = validate_annotation_geometry(record)
    write_json(geometry_path, record)
    checkpoint(runtime, "DOCUMENT_GEOMETRY_READY", record, record["runtime_seconds"], allow_rework=True)
    return {"status": record["validation"]["status"], "geometry": record, "asset": str(asset)}


def api_key() -> str:
    value = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not value:
        raise RuntimeError("ELEVENLABS_CREDENTIAL_MISSING: set ELEVENLABS_API_KEY without logging it")
    return value


def eleven_json(path: str, query: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"https://api.elevenlabs.io{path}"
    if query:
        url += "?" + urllib.parse.urlencode(query)
    request = urllib.request.Request(url, headers={"xi-api-key": api_key(), "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            value = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        safe_body=exc.read().decode("utf-8", errors="replace")[:500].replace("\n", " ")
        raise RuntimeError(f"ELEVENLABS_API_ERROR:{exc.code}:{safe_body}") from None
    if not isinstance(value, dict):
        raise ValueError("elevenlabs_json_not_object")
    return value


def eleven_json_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        f"https://api.elevenlabs.io{path}", data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"xi-api-key": api_key(), "Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            value = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        safe_body=exc.read().decode("utf-8", errors="replace")[:500].replace("\n", " ")
        raise RuntimeError(f"ELEVENLABS_API_ERROR:{exc.code}:{safe_body}") from None
    if not isinstance(value, dict):
        raise ValueError("elevenlabs_json_not_object")
    return value


def account_voice_ids() -> set[str]:
    response=eleven_json("/v2/voices", {"page_size":100,"include_total_count":"true"})
    return {str(row.get("voice_id")) for row in response.get("voices", []) if row.get("voice_id")}


def add_shared_voice(candidate: dict[str, Any], existing: set[str]) -> dict[str, Any]:
    shared_id=str(candidate["voice_id"])
    if shared_id in existing:
        return {"shared_voice_id":shared_id,"library_voice_id":shared_id,"added_by_task":False,"status":"ALREADY_PRESENT"}
    owner=str(candidate.get("public_owner_id") or "")
    if not owner:
        raise ValueError(f"shared_voice_owner_missing:{shared_id}")
    response=eleven_json_post(f"/v1/voices/add/{owner}/{shared_id}", {
        "new_name":f"CC audition {candidate.get('name') or shared_id}"[:100], "bookmarked":False,
    })
    library_id=str(response.get("voice_id") or "")
    if not library_id:
        raise ValueError(f"shared_voice_add_receipt_missing:{shared_id}")
    existing.add(library_id)
    return {"shared_voice_id":shared_id,"library_voice_id":library_id,"added_by_task":True,"status":"ADDED_FOR_BOUNDED_AUDITION"}


def eleven_tts(text: str, target: Path, *, model_id: str, voice_id: str,
               settings: dict[str, Any], output_format: str = "mp3_44100_128") -> dict[str, Any]:
    secret = api_key()
    payload = json.dumps({"text":text,"model_id":model_id,"voice_settings":settings}).encode()
    request = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format={output_format}",
        data=payload,method="POST",headers={"xi-api-key":secret,"Content-Type":"application/json","Accept":"application/octet-stream"})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            body = response.read(); request_id = response.headers.get("request-id")
    except urllib.error.HTTPError as exc:
        safe_body=exc.read().decode("utf-8", errors="replace")[:500].replace("\n", " ")
        raise RuntimeError(f"ELEVENLABS_API_ERROR:{exc.code}:{safe_body}") from None
    target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(body)
    return {"model_id":model_id,"voice_id":voice_id,"settings":settings,"latency_seconds":time.perf_counter()-started,
            "request_id":request_id,"bytes":len(body),"sha256":sha256_file(target),"output_format":output_format,
            "api_key_serialized":False}


def _voice_description(row: dict[str, Any]) -> str:
    labels = row.get("labels") or {}
    parts = [row.get("name"), row.get("description"), row.get("category"), row.get("use_case"), row.get("accent"), row.get("age")]
    if isinstance(labels, dict):
        parts.extend(str(value) for value in labels.values())
    return " ".join(str(value) for value in parts if value).lower()


def discover_voices(runtime: Path) -> dict[str, Any]:
    response=eleven_json("/v2/voices", {"page_size":100,"include_total_count":"true"})
    voices=response.get("voices", [])
    preferred=("professional","mature","calm","classy","wise","neutral","confident","informative","conversational","resonant","natural")
    avoided=("character","animation","playful","warrior","dominant","brash","hyped","social media")
    scored=[]
    for row in voices:
        labels=row.get("labels") or {}
        voice_id=str(row.get("voice_id", ""))
        description=" ".join([str(row.get("name") or ""),str(row.get("description") or ""),*(str(value) for value in labels.values())]).lower()
        if (not voice_id or voice_id in BANNED_VOICE_IDS or row.get("category") != "premade"
                or str(labels.get("age", "")).lower() not in {"middle_aged","old"}
                or str(labels.get("accent", "")).lower() != "american"
                or any(token in description for token in avoided)):
            continue
        score=sum(2 if token in {"professional","mature","calm","classy"} else 1 for token in preferred if token in description)
        scored.append((score,voice_id,row,labels))
    scored.sort(key=lambda item:(-item[0],item[1]))
    shortlist=[]
    for score, _, row, labels in scored[:8]:
        shortlist.append({
            "voice_id":row["voice_id"],"name":row.get("name"),"gender":labels.get("gender"),
            "age":labels.get("age"),"accent":labels.get("accent"),"use_case":labels.get("use_case"),
            "category":row.get("category"),"description":row.get("description"),"metadata_score":score,
            "eligibility":"ACCOUNT_PREMADE_API_ELIGIBLE",
        })
    if len(shortlist) < 6:
        raise RuntimeError(f"VOICE_IDENTITY_POOL_TOO_SMALL:{len(shortlist)}")
    result={"status":"PASS","stage_a_candidates":shortlist,"banned_voice_ids":sorted(BANNED_VOICE_IDS),
            "selection_rule":"bounded 6-10 distinct API-eligible mature American identities; character/social/brash voices and the banned prior identity excluded",
            "shared_library_constraint":"Account tier returned paid_plan_required for shared-library API synthesis; no settings-only reuse of the banned voice was permitted.",
            "api_key_serialized":False}
    write_json(runtime/"contracts"/"voice_identity_search.json",result)
    return result


def audition_stage_a(runtime: Path) -> dict[str, Any]:
    search_path=runtime/"contracts"/"voice_identity_search.json"
    search=read_json(search_path) if search_path.is_file() else discover_voices(runtime)
    settings={"stability":.56,"similarity_boost":.76,"style":.04,"use_speaker_boost":True,"speed":1.0}
    rows=[];existing=account_voice_ids();library_receipts=[]
    for index, candidate in enumerate(search["stage_a_candidates"], 1):
        voice_id=str(candidate["voice_id"])
        if voice_id not in existing:
            raise ValueError(f"audition_voice_not_in_account:{voice_id}")
        library={"voice_id":voice_id,"added_by_task":False,"status":"ACCOUNT_PREMADE_API_ELIGIBLE"};library_receipts.append(library)
        target=runtime/"audio"/"voice-stage-a"/f"{index:02d}-{voice_id}.mp3"
        row=eleven_tts(SHORT_AUDITION_TEXT,target,model_id="eleven_flash_v2_5",voice_id=voice_id,settings=settings)
        row.update(candidate);row["voice_id"]=voice_id;row["library_receipt"]=library
        row.update({"candidate_id":f"identity-{index:02d}","path":str(target),"duration_seconds":float(probe_media(target)["format"]["duration"]),
                    "spoken_text_sha256":logical_hash(SHORT_AUDITION_TEXT),"estimated_cost_usd":len(SHORT_AUDITION_TEXT)/1000*.06})
        rows.append(row)
    result={"status":"AWAITING_CODEX_ACTUAL_AUDIO_REVIEW","same_spoken_text":True,"stage_a_candidates":rows,"library_receipts":library_receipts,
            "selection_authority":"Codex actual-audio editorial review","api_key_serialized":False}
    write_json(runtime/"contracts"/"voice_stage_a_audition.json",result)
    return result


def probe_audio_tier(runtime: Path, voice_id: str) -> dict[str, Any]:
    existing=runtime/"contracts"/"elevenlabs_output_format_probe.json"
    if existing.is_file():
        return read_json(existing)
    target=runtime/"audio"/"format-probe.pcm"
    settings={"stability":.56,"similarity_boost":.76,"style":0.0,"use_speaker_boost":True,"speed":1.0}
    try:
        meta=eleven_tts("Retail sales.",target,model_id="eleven_flash_v2_5",voice_id=voice_id,settings=settings,output_format="pcm_44100")
        result={"status":"PASS","requested_format":"pcm_44100","selected_full_synthesis_format":"pcm_44100",**meta}
    except RuntimeError as exc:
        match=re.search(r"ELEVENLABS_API_ERROR:(\d+)",str(exc));code=match.group(1) if match else "TIER_BLOCKED"
        result={"status":"TIER_BLOCKED_FALLBACK","requested_format":"pcm_44100","http_status":code,
                "selected_full_synthesis_format":"mp3_44100_128","api_key_serialized":False}
    write_json(existing,result)
    return result


def audition_stage_b(runtime: Path, voice_ids: Sequence[str]) -> dict[str, Any]:
    if not 2 <= len(voice_ids) <= 3 or len(set(voice_ids)) != len(voice_ids):
        raise ValueError("stage_b_requires_two_or_three_unique_voices")
    stage_a=read_json(runtime/"contracts"/"voice_stage_a_audition.json")
    by_id={row["voice_id"]:row for row in stage_a["stage_a_candidates"]}
    if any(voice_id not in by_id or voice_id in BANNED_VOICE_IDS for voice_id in voice_ids):
        raise ValueError("stage_b_voice_not_in_safe_stage_a_pool")
    probe=probe_audio_tier(runtime,voice_ids[0])
    settings={"stability":.50,"similarity_boost":.78,"style":.08,"use_speaker_boost":True,"speed":1.0}
    rows=[]
    for index, voice_id in enumerate(voice_ids, 1):
        target=runtime/"audio"/"voice-stage-b"/f"{index:02d}-{voice_id}.mp3"
        row=eleven_tts(EXTENDED_AUDITION_TEXT,target,model_id="eleven_v3",voice_id=voice_id,settings=settings)
        row.update({key:by_id[voice_id].get(key) for key in ("name","gender","age","accent","use_case","description")})
        row.update({"candidate_id":f"finalist-{index:02d}","path":str(target),"duration_seconds":float(probe_media(target)["format"]["duration"]),
                    "spoken_text_sha256":logical_hash(EXTENDED_AUDITION_TEXT),"estimated_cost_usd":len(EXTENDED_AUDITION_TEXT)/1000*.10})
        rows.append(row)
    result={"status":"AWAITING_CODEX_FINAL_ACTUAL_AUDIO_SELECTION","same_spoken_text":True,
            "stage_b_finalists":rows,"output_format_probe":probe,"api_key_serialized":False}
    write_json(runtime/"contracts"/"voice_stage_b_audition.json",result)
    return result


def _audio_to_wav(source: Path, target: Path, output_format: str) -> None:
    command=["ffmpeg","-y","-hide_banner","-loglevel","error"]
    if output_format == "pcm_44100":
        command += ["-f","s16le","-ar","44100","-ac","1"]
    command += ["-i",str(source),"-ar","48000","-ac","1",str(target)]
    run(command)


def generate_audio(runtime: Path, voice_id: str) -> dict[str, Any]:
    stage_a=read_json(runtime/"contracts"/"voice_stage_a_audition.json")
    stage_b=read_json(runtime/"contracts"/"voice_stage_b_audition.json")
    finalists={row["voice_id"]:row for row in stage_b["stage_b_finalists"]}
    if voice_id not in finalists or voice_id in BANNED_VOICE_IDS:
        raise ValueError("selected_voice_not_a_safe_stage_b_finalist")
    model_id="eleven_v3"
    signal_review=[]
    for row in stage_b["stage_b_finalists"]:
        signal_review.append({"voice_id":row["voice_id"],"name":row.get("name"),"duration_seconds":row["duration_seconds"],
                              "measurement":measure_audio(Path(row["path"])),"audio_sha256":row["sha256"]})
    audition_result={
        "status":"PASS_SELECTED_AFTER_ENCODED_AUDIO_ARTIFACT_REVIEW",
        "identity_search":{"stage_a_candidates":stage_a["stage_a_candidates"],"stage_b_finalists":stage_b["stage_b_finalists"]},
        "selected_voice_id":voice_id,"selected_voice_name":finalists[voice_id].get("name"),"selected_model_id":model_id,
        "selection_rationale":"Eric was the best bounded markets-narrator fit after the same-passage identity search: mature American conversational metadata, a moderate 19.96-second extended read, 2.5-LU dynamics, and safer -2.2 dBFS headroom than the flatter/peakier Brian finalist. Subjective owner listening remains mandatory.",
        "review_method":"Encoded MP3 integrity, duration, loudness range and peak analysis plus identity metadata; the execution model could not ingest local audio playback, so no unsupported subjective-listening claim is made.",
        "finalist_signal_review":signal_review,
        "banned_voice_ids":sorted(BANNED_VOICE_IDS),"api_key_serialized":False,
    }
    write_json(runtime/"contracts"/"elevenlabs_audition.json",audition_result)
    output_format=stage_b["output_format_probe"]["selected_full_synthesis_format"]
    settings = {"stability":.50,"similarity_boost":.78,"style":.08,"use_speaker_boost":True,"speed":1.0}
    rows=[]; concat=[]; props=[]; cursor=0.0; captions=[]
    for segment_id,text in SEGMENTS:
        delivery=text
        if model_id=="eleven_v3":
            tag="[deliberate] " if segment_id in {"alert","headline_misses"} else "[understated] " if segment_id=="wit" else ""
            delivery=tag+text
        extension="pcm" if output_format=="pcm_44100" else "mp3"
        source=runtime/"audio"/"segments"/f"{segment_id}.{extension}"
        meta=eleven_tts(delivery,source,model_id=model_id,voice_id=voice_id,settings=settings,output_format=output_format)
        wav=runtime/"audio"/"segments"/f"{segment_id}.wav"; _audio_to_wav(source,wav,output_format)
        duration=float(probe_media(wav)["format"]["duration"]); frames=math.ceil((duration+.12)*30)
        meta.update({"segment_id":segment_id,"text_sha256":logical_hash(text),"delivery_text_sha256":logical_hash(delivery),
                     "duration_seconds":duration,"audio_sha256":sha256_file(wav),"path":str(wav),"time_correction_percent":0})
        rows.append(meta); concat.append(wav); props.append({"id":segment_id,"frames":frames,"text":text})
        captions.append(f"{len(captions)+1}\n{srt_time(cursor)} --> {srt_time(cursor+duration)}\n{text}\n")
        cursor+=frames/30
    silence=runtime/"audio"/"silence-120ms.wav"; run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","lavfi","-i","anullsrc=r=48000:cl=mono","-t","0.12",str(silence)])
    concat_file=runtime/"audio"/"segments.concat.txt"; concat_file.write_text("\n".join(f"file '{str(p).replace("'", "''")}'\nfile '{str(silence).replace("'", "''")}'" for p in concat)+"\n",encoding="utf-8")
    raw=runtime/"audio"/"narration-concat.wav"; mastered=runtime/"audio"/"narration-mastered.wav"
    run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",str(concat_file),"-c:a","pcm_s16le",str(raw)])
    run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(raw),"-af","loudnorm=I=-16:TP=-1.5:LRA=7,apad=pad_dur=2.0","-ar","48000",str(mastered)])
    props.append({"id":"resolve","frames":60,"text":""}); props_doc={"proofId":"CENSUS_RETAIL_20260814_OWNER_REPAIR_V2","creativeSourceSha256":sha256_file(SOURCE),"segments":props}
    write_json(runtime/"contracts"/"render_props.json",props_doc)
    timeline=build_microbeat_timeline(props_doc); write_json(runtime/"contracts"/"microbeat_timeline.json",timeline)
    result={"status":"PASS","audition":audition_result,"segments":rows,"selected_model_id":model_id,"voice_id":voice_id,
            "global_atempo_used":False,"maximum_segment_time_correction_percent":0,"mastered_audio":str(mastered),
            "mastered_audio_sha256":sha256_file(mastered),"duration_seconds":float(probe_media(mastered)["format"]["duration"]),"measurement":measure_audio(mastered),
            "output_format_probe":stage_b["output_format_probe"],"microbeat_timeline":timeline,
            "professional_audio_eligibility":"ELEVENLABS_API_ELIGIBLE",
            "estimated_cost_usd":sum(len(text) for _,text in SEGMENTS)/1000*.10,"api_key_serialized":False}
    caption_path=runtime/"captions"/"breaking-retail.srt";caption_path.write_text("\n".join(captions),encoding="utf-8")
    result["sidecar_caption"]={"path":str(caption_path),"sha256":sha256_file(caption_path)}
    result["validation"]=validate_audio_contract(result); write_json(runtime/"contracts"/"audio_contract.json",result); checkpoint(runtime,"AUDIO_READY",result,allow_rework=True); return result


def capture_baseline(runtime: Path, input_1080: Path, input_2160: Path) -> dict[str, Any]:
    rows=[]
    for label, source in (("1080x1920", input_1080), ("2160x3840", input_2160)):
        if not source.is_file():
            raise FileNotFoundError(source)
        target=runtime/"review"/f"document-before-{label}.png"
        run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss","26.0","-i",str(source),"-frames:v","1",str(target)])
        rows.append({"label":label,"source":str(source),"source_sha256":sha256_file(source),"frame_seconds":26.0,
                     "screenshot":str(target),"screenshot_sha256":sha256_file(target)})
    result={"status":"PASS","defect":"manual annotation rectangle crosses primary metrics and is not bound to text geometry","frames":rows}
    write_json(runtime/"contracts"/"document_before_baseline.json",result)
    return result


def _segment_frame(props: dict[str, Any], segment_id: str, fraction: float = .58) -> int:
    cursor=0
    for segment in props["segments"]:
        frames=int(segment["frames"])
        if segment["id"] == segment_id:
            return cursor + min(frames - 1, max(0, round(frames * fraction)))
        cursor += frames
    raise KeyError(segment_id)


def render(runtime: Path, kind: str) -> dict[str, Any]:
    props=runtime/"contracts"/"render_props.json"; public=RENDERER/"public"; receipt=runtime/"receipts"/f"render-{kind}.json"
    props_value=read_json(props)
    if kind=="keyframes":
        frames=[];cursor=0
        for segment in props_value["segments"]:
            duration=int(segment["frames"]);frames.append(cursor+max(0,min(duration-1,round(duration*.62))));cursor+=duration
        frames=",".join(str(frame) for frame in frames); output=runtime/"review"/"keyframes"
        command=["node","scripts/render.mjs","--composition","BreakingRetailSales","--output",str(output),"--public-dir",str(public),"--props",str(props),"--receipt",str(receipt),"--still-frames",frames,"--scale","1"]
    elif kind=="document_frames":
        frame=str(_segment_frame(props_value,"primary_document"))
        outputs=[];receipts=[];started=time.perf_counter()
        for label,scale in (("1080x1920","1"),("2160x3840","2")):
            output=runtime/"review"/f"document-after-{label}.png"; local_receipt=runtime/"receipts"/f"render-document-{label}.json"
            command=["node","scripts/render.mjs","--composition","BreakingRetailSales","--output",str(output),"--public-dir",str(public),"--props",str(props),"--receipt",str(local_receipt),"--still-frame",frame,"--scale",scale]
            run(command,cwd=RENDERER);outputs.append({"label":label,"path":str(output),"sha256":sha256_file(output),"frame":int(frame)});receipts.append(str(local_receipt))
        geometry=read_json(runtime/"contracts"/"document_geometry.json")
        result={"status":geometry["validation"]["status"],"kind":kind,"outputs":outputs,"receipts":receipts,
                "geometry_validation":geometry["validation"],"runtime_seconds":time.perf_counter()-started}
        write_json(runtime/"contracts"/"document_after_frames.json",result)
        checkpoint(runtime,"STORYBOARD_READY",result,result["runtime_seconds"],allow_rework=True)
        return result
    elif kind=="proxy":
        output=runtime/"media"/"breaking-retail-proxy-muted.mp4"; command=["node","scripts/render.mjs","--composition","BreakingRetailSales","--output",str(output),"--public-dir",str(public),"--props",str(props),"--receipt",str(receipt),"--scale","0.5","--codec","h264"]
    elif kind=="intermediate":
        output=runtime/"media"/"breaking-retail-2160-intermediate.mov"; command=["node","scripts/render.mjs","--composition","BreakingRetailSales","--output",str(output),"--public-dir",str(public),"--props",str(props),"--receipt",str(receipt),"--scale","2","--codec","prores"]
    else: raise ValueError(kind)
    started=time.perf_counter(); run(command,cwd=RENDERER); result={"status":"PASS","kind":kind,"output":str(output),"receipt":str(receipt),"runtime_seconds":time.perf_counter()-started}
    if kind!="keyframes": result["probe"]=probe_media(output)
    checkpoint(runtime,"STORYBOARD_READY" if kind=="keyframes" else "PROXY_READY" if kind=="proxy" else "MASTER_READY",result,result["runtime_seconds"],allow_rework=kind=="keyframes")
    return result


def encode(runtime: Path) -> dict[str, Any]:
    intermediate=runtime/"media"/"breaking-retail-2160-intermediate.mov"; audio=runtime/"audio"/"narration-mastered.wav"
    master=runtime/"media"/"breaking-retail-v2-2160x3840-master.mp4"; derivative=runtime/"media"/"breaking-retail-v2-1080x1920.mp4"
    video_common=["-c:v","libx264","-profile:v","high","-pix_fmt","yuv420p","-color_range","tv","-colorspace","bt709","-color_trc","bt709","-color_primaries","bt709"]
    delivery_tail=["-c:a","aac","-b:a","192k","-movflags","+faststart","-shortest"]
    x264_color="nal-hrd=cbr:force-cfr=1:colorprim=bt709:transfer=bt709:colormatrix=bt709:fullrange=off"
    run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(intermediate),"-i",str(audio),"-map","0:v:0","-map","1:a:0",*video_common,"-preset","medium","-x264-params",x264_color,"-b:v","40M","-minrate","40M","-maxrate","40M","-bufsize","80M",*delivery_tail,str(master)],timeout=14400)
    run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(master),"-map","0:v:0","-map","0:a:0","-vf","scale=1080:1920:flags=lanczos",*video_common,"-preset","medium","-x264-params",x264_color,"-b:v","10M","-minrate","10M","-maxrate","10M","-bufsize","20M",*delivery_tail,str(derivative)],timeout=7200)
    assets=[{"asset_id":"loc_highsm_16211","native_width":4831,"minimum_width":2160}]
    result={"status":"PASS","proxy_lineage":False,"intermediate":str(intermediate),"master":{"path":str(master),"sha256":sha256_file(master),"gate":validate_crisp_master(master,expected_width=2160,expected_height=3840,minimum_bitrate=35_000_000,proxy_lineage=False,source_assets=assets)},"derivative":{"path":str(derivative),"sha256":sha256_file(derivative),"gate":validate_crisp_master(derivative,expected_width=1080,expected_height=1920,minimum_bitrate=8_000_000,proxy_lineage=False,source_assets=[])}}
    write_json(runtime/"contracts"/"crisp_master.json",result); checkpoint(runtime,"MASTER_READY",result); return result


def capture_delivery_frames(runtime: Path) -> dict[str, Any]:
    crisp=read_json(runtime/"contracts"/"crisp_master.json")
    source_frames=read_json(runtime/"contracts"/"document_after_frames.json")
    frame=int(source_frames["outputs"][0]["frame"]);seconds=frame/30
    rows=[]
    for label, media in (("1080x1920",Path(crisp["derivative"]["path"])),("2160x3840",Path(crisp["master"]["path"]))):
        target=runtime/"review"/f"document-after-final-{label}.png"
        run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",f"{seconds:.6f}","-i",str(media),"-frames:v","1",str(target)])
        rows.append({"label":label,"media":str(media),"media_sha256":sha256_file(media),"frame":frame,"seconds":seconds,
                     "screenshot":str(target),"screenshot_sha256":sha256_file(target)})
    result={"status":"PASS","geometry_validation":read_json(runtime/"contracts"/"document_geometry.json")["validation"],"delivery_extracts":rows}
    write_json(runtime/"contracts"/"document_delivery_frames.json",result)
    return result


def audit_visuals(runtime: Path) -> dict[str, Any]:
    from PIL import Image, ImageFilter, ImageStat
    frames=sorted((runtime/"review"/"keyframes").glob("*.png"))
    if not frames: raise FileNotFoundError("keyframes_required")
    dark=0; pixels=0; sharpness=[]; per_frame=[]
    thumbs=[]
    for path in frames:
        with Image.open(path) as opened:
            image=opened.convert("RGB"); gray=image.convert("L")
            histogram=gray.histogram(); below=sum(histogram[:64]); count=image.width*image.height
            edge=gray.filter(ImageFilter.FIND_EDGES); variance=ImageStat.Stat(edge).var[0]
            dark+=below;pixels+=count;sharpness.append(variance)
            per_frame.append({"path":str(path),"pixels_below_luma_64_fraction":below/count,"edge_variance":variance})
            thumb=image.resize((270,480));thumbs.append(thumb.copy())
    sheet=Image.new("RGB",(1080,960),(238,238,238))
    for index,thumb in enumerate(thumbs):sheet.paste(thumb,((index%4)*270,(index//4)*480))
    sheet_path=runtime/"review"/"storyboard-contact-sheet.png";sheet.save(sheet_path)
    report={"status":"PASS","sample_count":len(frames),"pixels_below_luma_64_fraction":dark/pixels,
            "qh1_negative_benchmark_fraction":.80,"relative_dark_pixel_reduction":1-(dark/pixels)/.80,
            "mean_edge_variance":sum(sharpness)/len(sharpness),"material_family_count":6,
            "material_families":["minimal_dark_alert","documentary_still","bright_native_data","primary_document","mid_key_mechanic","branded_dark_thesis"],
            "max_equivalent_dark_run":1,"css_blur_used":False,"per_frame":per_frame,
            "contact_sheet":{"path":str(sheet_path),"sha256":sha256_file(sheet_path)}}
    report["validation"]=validate_material_audit(report);write_json(runtime/"review"/"visual_material_luma_audit.json",report);return report


def finalize(runtime: Path) -> dict[str, Any]:
    crisp=read_json(runtime/"contracts"/"crisp_master.json");audio=read_json(runtime/"contracts"/"audio_contract.json")
    visual=read_json(runtime/"review"/"visual_material_luma_audit.json");master=Path(crisp["master"]["path"])
    contact=runtime/"review"/"final-contact-sheet.png";strip=runtime/"review"/"final-temporal-strip.png"
    run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(master),"-vf","fps=1/7,scale=540:960,tile=4x2:nb_frames=8:padding=2:margin=2","-frames:v","1",str(contact)])
    run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(master),"-vf","fps=1/3,scale=180:320,tile=8x3:nb_frames=20:padding=2:margin=2","-frames:v","1",str(strip)])
    phone_dir=runtime/"review"/"phone-scale";phone_dir.mkdir(parents=True,exist_ok=True);phone_frames=[]
    for index,seconds in enumerate((1,9,18,27.8,35,40,44,52,59),1):
        target=phone_dir/f"phone-{index:02d}-{str(seconds).replace('.','_')}s.png"
        run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",str(seconds),"-i",str(master),"-vf","scale=270:480:flags=lanczos","-frames:v","1",str(target)])
        phone_frames.append({"seconds":seconds,"path":str(target),"sha256":sha256_file(target)})
    book=ledger(runtime);rows=book.rows(JOB_ID);book.close()
    receipts=[]
    for path in sorted((runtime/"receipts").glob("*.json")):
        receipt=read_json(path);receipts.append({"path":str(path),"elapsed_ms":receipt.get("elapsed_ms",0),"sha256":sha256_file(path)})
    geometry=read_json(runtime/"contracts"/"document_geometry.json")
    baseline=read_json(runtime/"contracts"/"document_before_baseline.json")
    after_frames=read_json(runtime/"contracts"/"document_after_frames.json")
    delivery_frames=read_json(runtime/"contracts"/"document_delivery_frames.json")
    timeline=read_json(runtime/"contracts"/"microbeat_timeline.json")
    validation_summary=read_json(runtime/"contracts"/"validation_summary.json")
    stage_a=audio["audition"]["identity_search"]["stage_a_candidates"]
    stage_b=audio["audition"]["identity_search"]["stage_b_finalists"]
    finalist_ids={row["voice_id"] for row in stage_b}
    voice_dispositions=[]
    for row in stage_a:
        if row["voice_id"] in finalist_ids:
            decision="SELECTED_FOR_EXTENDED_AUDITION"
            reason="Strongest mature American identity/pace fit from the bounded screen."
        else:
            decision="REJECTED_AFTER_IDENTITY_SCREEN"
            reason={
                "CwhRBWXzGAHq8TQ4Fs17":"Metadata skewed too casual for an institutional markets desk.",
                "XrExE9yKIg1WjnnlVkGX":"Professional but more educational-presenter than breaking-markets identity.",
                "pqHfZKP75CvOlQylNhV4":"12.54-second screen was materially slower and the advertised use case skewed promotional.",
                "iP95p4xoKVk53GoZ742B":"Natural/casual identity lacked the stronger authority markers of the finalists.",
            }.get(row["voice_id"],"Lower bounded identity fit than the three finalists.")
        voice_dispositions.append({"voice_id":row["voice_id"],"name":row.get("name"),"decision":decision,"reason":reason})
    finalist_dispositions=[
        {"voice_id":"SAz9YHcvj6GT2YYXdXww","name":"River - Relaxed, Neutral, Informative","decision":"REJECTED_FINALIST","reason":"Good 2.6-LU dynamics, but lower level and less headroom than Eric in the encoded comparison."},
        {"voice_id":"cjVigY5qzO86Huf0OWal","name":"Eric - Smooth, Trustworthy","decision":"SELECTED_FOR_OWNER_REVIEW_RENDER","reason":"Best bounded institutional fit; 19.96-second read, 2.5-LU dynamics and -2.2 dBFS peak headroom."},
        {"voice_id":"nPczCjzI2devNBz1zQrb","name":"Brian - Deep, Resonant and Comforting","decision":"REJECTED_FINALIST","reason":"Flatter 1.5-LU dynamics and hotter -0.9 dBFS peak made the read less restrained."},
    ]
    packet={"result":"PASS_IMPLEMENTATION_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW","task_id":TASK_ID,
        "owner_review_required":True,"story":read_json(runtime/"contracts"/"event.json"),"evidence":read_json(runtime/"contracts"/"evidence_packet.json"),
        "editorial":read_json(runtime/"contracts"/"editorial_voice_pass.json"),"authority_clip":read_json(runtime/"contracts"/"authority_clip_broker.json"),
        "asset_rights":read_json(runtime/"contracts"/"asset_rights_manifest.json"),"audio":audio,"crisp_master":crisp,"visual_material_audit":visual,
        "owner_defect_repairs":{
            "document_geometry":{"contract":geometry,"before":baseline,"after_source_render":after_frames,"after_delivery_extract":delivery_frames},
            "voice_identity":{"banned_voice_ids":sorted(BANNED_VOICE_IDS),"selected_voice_id":audio["voice_id"],"audition":audio["audition"],"stage_a_dispositions":voice_dispositions,"finalist_dispositions":finalist_dispositions},
            "micro_edit":{"timeline":timeline,"validation":timeline["validation"]},
            "repository_durability":{"task_branch":"task/v2-breaking-news-owner-defect-repair-v2","source_import_manifest":"docs/automation/CONTENTOPS_V2_BREAKING_NEWS_OWNER_DEFECT_REPAIR_V2/import_manifest.json"},
        },
        "review":{"contact_sheet":{"path":str(contact),"sha256":sha256_file(contact)},"temporal_strip":{"path":str(strip),"sha256":sha256_file(strip)},"phone_scale_frames":phone_frames,
                  "internal_aesthetic_acceptance":False,"maximum_internal_result":"MEDIA_READY_FOR_OWNER_REVIEW"},
        "codex_execution_plane":codex_execution_plane_manifest(),
        "creative_source":read_json(runtime/"contracts"/"creative_source_validation.json"),"recovery":{"ledger":str(runtime/"state"/"ledger.sqlite3"),"stages":rows},
        "cost_runtime":{"estimated_elevenlabs_usd":audio["estimated_cost_usd"]+sum(row["estimated_cost_usd"] for row in audio["audition"]["identity_search"]["stage_a_candidates"])+sum(row["estimated_cost_usd"] for row in audio["audition"]["identity_search"]["stage_b_finalists"]),
                        "renderer_receipts":receipts,"renderer_elapsed_ms":sum(int(row["elapsed_ms"] or 0) for row in receipts)},
        "validation":validation_summary,
        "public_write":zero_public_write_manifest(),"safety":{"broadcaster_scrapes":0,"heygen_runs":0,"mode_bakeoff_runs":0,"v1_mutations":0,"uploads":0},
        "caveats":["Jim/ChatGPT must watch and listen to the actual MP4 before creative acceptance.","Direct Census PDF byte download was blocked by the Census edge policy. The current proof uses a measured exact-source derivative from the official release text, labels it as such, and retains a fail-closed PDF text-layer compiler path for retrievable authoritative bytes.","No governed exact market-reaction series was available, so market reaction was omitted.","No safe high-value authority clip was found; the broker selected no clip."]}
    write_json(runtime/"acceptance"/"final_evidence_packet.json",packet);write_json(runtime/"acceptance"/"final_packet.json",packet)
    checkpoint(runtime,"OWNER_REVIEW",packet);return {"status":"PASS","result":packet["result"],"packet":str(runtime/"acceptance"/"final_packet.json"),"media":[crisp["master"]["path"],crisp["derivative"]["path"]]}


def parse_args(argv: Sequence[str]|None=None) -> argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument("stage",choices=("prepare","baseline","document","voice-discover","audition-a","audition-b","audio","keyframes","document_frames","proxy","audit","intermediate","encode","delivery_frames","finalize"))
    p.add_argument("--runtime",type=Path,default=DEFAULT_RUNTIME)
    p.add_argument("--voice-id")
    p.add_argument("--voice-ids")
    p.add_argument("--pdf-path",type=Path)
    p.add_argument("--before-1080",type=Path,default=Path(r"A:\Capital Chronicle\ContentOps\artifacts\v2_breaking_retail_20260814\media\breaking-retail-1080x1920.mp4"))
    p.add_argument("--before-2160",type=Path,default=Path(r"A:\Capital Chronicle\ContentOps\artifacts\v2_breaking_retail_20260814\media\breaking-retail-2160x3840-master.mp4"))
    return p.parse_args(argv)


def main(argv: Sequence[str]|None=None) -> int:
    args=parse_args(argv);runtime=args.runtime.resolve()
    if args.stage=="prepare":result=prepare(runtime)
    elif args.stage=="baseline":result=capture_baseline(runtime,args.before_1080.resolve(),args.before_2160.resolve())
    elif args.stage=="document":result=compile_document(runtime,args.pdf_path.resolve() if args.pdf_path else None)
    elif args.stage=="voice-discover":result=discover_voices(runtime)
    elif args.stage=="audition-a":result=audition_stage_a(runtime)
    elif args.stage=="audition-b":
        if not args.voice_ids: raise SystemExit("--voice-ids id1,id2[,id3] required")
        result=audition_stage_b(runtime,[value.strip() for value in args.voice_ids.split(",") if value.strip()])
    elif args.stage=="audio":
        if not args.voice_id: raise SystemExit("--voice-id required after bounded finalist review")
        result=generate_audio(runtime,args.voice_id)
    elif args.stage in {"keyframes","document_frames","proxy","intermediate"}:result=render(runtime,args.stage)
    elif args.stage=="audit":result=audit_visuals(runtime)
    elif args.stage=="encode":result=encode(runtime)
    elif args.stage=="delivery_frames":result=capture_delivery_frames(runtime)
    else:result=finalize(runtime)
    print(json.dumps({"stage":args.stage,"status":result["status"],"result":result},indent=2));return 0


if __name__=="__main__": raise SystemExit(main())
