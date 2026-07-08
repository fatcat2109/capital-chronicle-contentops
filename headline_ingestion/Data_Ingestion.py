import asyncio, json, random, os, re, hashlib
from datetime import datetime, timezone, timedelta
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

CDP_URL = "http://localhost:9222"
TARGET_URL_KEYWORD = "ListLatestTweetsTimeline"
MAX_EMPTY_SCROLLS = 20
MAX_UPTIME_HOURS = 12

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

import builtins
def print(*args, **kwargs):
    msg = " ".join(map(str, args))
    builtins.print(msg, **kwargs)
    with open(os.path.join(DATA_DIR, "ingestion.log"), "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def get_current_output_filename():
    return os.path.join(DATA_DIR, "capital_chronicle_ALL_DATA.json")

STATE_DIR = os.path.join(DATA_DIR, "state", "current")
SIDECAR_DIR = os.path.join(DATA_DIR, "intake", "headline_sidecars")
RAW_ARCHIVE_DIR = os.path.join(DATA_DIR, "raw_archive", "headline_cdp")

ALLOWED_SIDECAR_CONSUMERS = [
    "narrative_context",
    "catalyst_detection",
    "follow_up_data_need",
    "report_safe_sidecar_display",
    "forensic_context",
]
FORBIDDEN_SIDECAR_CONSUMERS = [
    "market_price_truth",
    "macro_print_truth",
    "exact_source_clearance",
    "dqr_override",
    "direct_trade_signal",
    "broker_execution_input",
]

def _utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def _sha256_bytes(raw_bytes):
    return hashlib.sha256(raw_bytes).hexdigest()

def _safe_json_bytes(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def _load_state_json(filename):
    path = os.path.join(STATE_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, []
    except FileNotFoundError:
        return None, [f"{filename}_missing_fail_closed"]
    except Exception as exc:
        return None, [f"{filename}_unreadable_fail_closed:{type(exc).__name__}"]

def _manifest_summary():
    data, warnings = _load_state_json("InputStateManifest.json")
    if not isinstance(data, dict):
        return {
            "manifest_id": "missing_input_state_manifest_fail_closed",
            "input_state_manifest_status": "missing_fail_closed",
            "warnings": warnings,
        }
    raw = _safe_json_bytes(data)
    digest = _sha256_bytes(raw)
    return {
        "manifest_id": data.get("manifest_id") or data.get("current_state_mutated_by") or f"InputStateManifest:{digest[:16]}",
        "input_state_manifest_status": data.get("internal_alpha_status") or "present_no_clearance",
        "input_state_manifest_sha256": digest,
        "warnings": warnings,
    }

def _dqr_summary():
    data, warnings = _load_state_json("DataQualityReport.json")
    if not isinstance(data, dict):
        return {"dqr_status": "BLOCKED_FAIL_CLOSED", "warnings": warnings}
    status = data.get("overall_status")
    if not status:
        status = "BLOCKED" if data.get("critical_missing_metrics") else "UNKNOWN_FAIL_CLOSED"
        warnings.append("DataQualityReport.overall_status_missing_fail_closed")
    return {
        "dqr_status": str(status).upper(),
        "dqr_critical_missing_metrics": data.get("critical_missing_metrics", []),
        "dqr_reporting_allowed": data.get("reporting_allowed", False),
        "dqr_regime_synthesis_allowed": data.get("regime_synthesis_allowed", False),
        "dqr_allocation_allowed": data.get("allocation_allowed", False),
        "dqr_execution_allowed": data.get("execution_allowed", False),
        "warnings": warnings,
    }

def _source_health_summary():
    data, warnings = _load_state_json("SourceHealth.json")
    if not isinstance(data, dict):
        return {
            "source_quality_status": "unknown_fail_closed",
            "source_health_summary": {"status": "missing_fail_closed"},
            "warnings": warnings,
        }
    status = data.get("overall_status") or data.get("status") or "present_no_step1_clearance"
    return {
        "source_quality_status": status,
        "source_health_summary": {
            "status": status,
            "source_count": len(data.get("sources", [])) if isinstance(data.get("sources"), list) else None,
            "generated_at_utc": data.get("generated_at_utc"),
        },
        "warnings": warnings,
    }

def build_headline_sidecar_context():
    manifest = _manifest_summary()
    dqr = _dqr_summary()
    source_health = _source_health_summary()
    warnings = []
    warnings.extend(manifest.pop("warnings", []))
    warnings.extend(dqr.pop("warnings", []))
    warnings.extend(source_health.pop("warnings", []))
    warnings.append("headline_sidecar_evidence_only_no_numeric_truth")
    warnings.append("dqr_ia_exact_current_canonical_apply_unchanged")
    return {
        **manifest,
        **dqr,
        **source_health,
        "data_quality_warnings": warnings,
        "headline_sidecar_only": True,
        "candidate_only": True,
        "numeric_truth_authority": False,
        "forecast_readiness_authority": False,
        "dqr_clearance_authority": False,
        "current_canonical_apply": False,
        "allowed_consumers": ALLOWED_SIDECAR_CONSUMERS,
        "forbidden_consumers": FORBIDDEN_SIDECAR_CONSUMERS,
    }

def archive_raw_payload(payload, source_url=""):
    raw_bytes = _safe_json_bytes(payload)
    digest = _sha256_bytes(raw_bytes)
    os.makedirs(RAW_ARCHIVE_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(RAW_ARCHIVE_DIR, f"step1_x_cdp_raw_{stamp}_{digest[:16]}.json")
    with open(path, "wb") as f:
        f.write(raw_bytes)
    return {
        "raw_payload_ref": os.path.relpath(path, ".").replace(os.sep, "/"),
        "raw_payload_sha256": digest,
        "raw_payload_byte_size": len(raw_bytes),
        "source_url_or_ref": source_url,
    }

def _sidecar_path_for_timestamp(timestamp):
    date_key = datetime.now(timezone(timedelta(hours=7))).strftime("%Y_%m_%d")
    if isinstance(timestamp, str):
        match = re.search(r"(\d{4})-(\d{2})-(\d{2})", timestamp)
        if match:
            date_key = "_".join(match.groups())
    return os.path.join(SIDECAR_DIR, f"step1_headline_sidecar_{date_key}.jsonl")

def _headline_id(timestamp, text):
    return _sha256_bytes(f"{timestamp}\n{text}".encode("utf-8"))[:24]

def _normalize_headline_text(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()

def _tweet_timestamp(tweet):
    if isinstance(tweet, dict):
        return tweet.get("timestamp") or tweet.get("created_at_gmt7") or tweet.get("created_at_raw") or ""
    return tweet[0] if len(tweet) > 0 else ""

def _tweet_text(tweet):
    if isinstance(tweet, dict):
        return _normalize_headline_text(tweet.get("text") or tweet.get("headline_text"))
    return _normalize_headline_text(tweet[1] if len(tweet) > 1 else "")

def _legacy_tweet_row(tweet):
    return [_tweet_timestamp(tweet), _tweet_text(tweet)]

def _text_sha256(text):
    return _sha256_bytes(_normalize_headline_text(text).encode("utf-8"))

def _dedup_key(tweet):
    if isinstance(tweet, dict) and tweet.get("tweet_id"):
        return f"tweet_id:{tweet['tweet_id']}"
    basis = "\n".join([
        str(tweet.get("author_handle", "unknown")) if isinstance(tweet, dict) else "unknown",
        str(_tweet_timestamp(tweet)),
        _tweet_text(tweet),
    ])
    return f"headline_sha256:{_sha256_bytes(basis.encode('utf-8'))}"

def candidate_catalyst_tags(text):
    text = _normalize_headline_text(text)
    rules = {
        "central_bank": r"\b(Fed|FOMC|Powell|ECB|BOE|BOJ|rate decision|central bank)\b",
        "inflation": r"\b(CPI|PCE|inflation|prices|deflator)\b",
        "labor": r"\b(NFP|payrolls|jobless|claims|unemployment|labor|wages)\b",
        "energy": r"\b(oil|crude|WTI|Brent|OPEC|EIA|gasoline|natgas)\b",
        "geopolitics": r"\b(Trump|Biden|China|Russia|Ukraine|Iran|tariff|sanction|war|ceasefire)\b",
        "fiscal": r"\b(Treasury|deficit|debt|auction|tax|budget|fiscal)\b",
        "risk_off": r"\b(risk[- ]off|selloff|crash|panic|safe haven|flight to quality)\b",
        "volatility": r"\b(VIX|volatility|vol|gamma|options|hedging)\b",
        "growth": r"\b(GDP|PMI|ISM|retail sales|industrial production|growth)\b",
    }
    return [name for name, pattern in rules.items() if re.search(pattern, text, re.IGNORECASE)]

def follow_up_data_need_candidates(tags, text):
    mapping = {
        "central_bank": "official_central_bank_statement_or_calendar",
        "inflation": "official_inflation_release",
        "labor": "official_labor_release",
        "energy": "official_energy_inventory_or_opec_release",
        "fiscal": "official_treasury_or_budget_release",
        "growth": "official_growth_or_pmi_release",
        "volatility": "official_volatility_or_options_source_check",
    }
    needs = [mapping[tag] for tag in tags if tag in mapping]
    if re.search(r"\b(actual|forecast|previous|yield|futures?|price|index|PMI|CPI|PCE)\b", text or "", re.IGNORECASE):
        needs.append("official_numeric_source_required_before_truth_use")
    return sorted(set(needs))

def headline_quality_flags(tweet):
    text = _tweet_text(tweet)
    flags = []
    if isinstance(tweet, dict) and tweet.get("is_retweet"):
        flags.append("retweet")
    if re.fullmatch(r"https?://\S+", text):
        flags.append("url_only_text")
    if re.search(r"\d", text):
        flags.append("numeric_text_not_truth")
    if isinstance(tweet, dict) and tweet.get("is_quote_like"):
        flags.append("quote_or_link_context")
    return flags

def _tweet_sidecar_metadata(tweet):
    text = _tweet_text(tweet)
    tags = candidate_catalyst_tags(text)
    metadata = {
        "tweet_id": None,
        "author_handle": "unknown",
        "tweet_url": None,
        "created_at_raw": None,
        "is_retweet": False,
        "is_quote_like": False,
    }
    if isinstance(tweet, dict):
        metadata.update({key: tweet.get(key, metadata[key]) for key in metadata})
    metadata.update({
        "text_sha256": _text_sha256(text),
        "dedup_key": _dedup_key(tweet),
        "candidate_catalyst_tags": tags,
        "follow_up_data_need_candidates": follow_up_data_need_candidates(tags, text),
        "headline_quality_flags": headline_quality_flags(tweet),
    })
    return metadata

def append_headline_sidecars(tweets, raw_payload_metadata=None):
    if not tweets:
        return 0
    context = build_headline_sidecar_context()
    raw_meta = raw_payload_metadata or {
        "raw_payload_ref": None,
        "raw_payload_sha256": None,
        "raw_payload_byte_size": None,
        "source_url_or_ref": "legacy_or_test_call_without_raw_payload",
    }
    os.makedirs(SIDECAR_DIR, exist_ok=True)
    rows_by_path = {}
    captured_at_utc = _utc_now_iso()
    for tweet in tweets:
        timestamp, text = _tweet_timestamp(tweet), _tweet_text(tweet)
        if not text:
            continue
        row = {
            "schema_version": "step1_headline_catalyst_sidecar_v1",
            "headline_id": _headline_id(timestamp, text),
            "headline_text": text,
            "headline_timestamp": timestamp,
            "source_platform": "x_cdp_list_latest_tweets_timeline",
            "captured_at_utc": captured_at_utc,
            **raw_meta,
            **_tweet_sidecar_metadata(tweet),
            **context,
        }
        rows_by_path.setdefault(_sidecar_path_for_timestamp(timestamp), []).append(row)
    written = 0
    for path, rows in rows_by_path.items():
        with open(path, "a", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
                written += 1
    return written

def convert_to_gmt7(tw_time_str):
    if not tw_time_str: return tw_time_str
    try:
        dt = datetime.strptime(tw_time_str, "%a %b %d %H:%M:%S %z %Y")
        dt_gmt7 = dt.astimezone(timezone(timedelta(hours=7)))
        return f"{dt_gmt7.strftime('%Y-%m-%d %H:%M:%S')} GMT+7"
    except Exception:
        return tw_time_str

def get_current_gmt7():
    dt_gmt7 = datetime.now(timezone(timedelta(hours=7)))
    return f"{dt_gmt7.strftime('%Y-%m-%d %H:%M:%S')} GMT+7"

def find_screen_name(node):
    if isinstance(node, dict):
        if 'screen_name' in node: return node['screen_name']
        for k, v in node.items():
            if k in ('mentioned_users', 'user_mentions'): continue
            res = find_screen_name(v)
            if res: return res
    elif isinstance(node, list):
        for item in node:
            res = find_screen_name(item)
            if res: return res
    return None

def recursive_tweet_extractor(obj):
    tweets = []
    if isinstance(obj, dict):
        if 'legacy' in obj and 'full_text' in obj['legacy']:
            try:
                author_handle = "unknown"
                core_data = obj.get('core', {})
                found_handle = find_screen_name(core_data)
                if found_handle:
                    author_handle = found_handle
                legacy = obj['legacy']
                text = _normalize_headline_text(legacy.get('full_text', ''))
                if author_handle == "unknown":
                    match = re.search(r"^RT @(\w+):", text)
                    if match: author_handle = match.group(1)
                tweet_id = legacy.get('id_str')
                if tweet_id and text:
                    tweets.append({
                        "timestamp": convert_to_gmt7(legacy.get('created_at')),
                        "text": text,
                        "tweet_id": str(tweet_id),
                        "author_handle": author_handle,
                        "tweet_url": None if author_handle == "unknown" else f"https://x.com/{author_handle}/status/{tweet_id}",
                        "created_at_raw": legacy.get('created_at'),
                        "is_retweet": text.startswith("RT @"),
                        "is_quote_like": "https://t.co/" in text,
                    })
            except Exception: pass
        for key, value in obj.items(): tweets.extend(recursive_tweet_extractor(value))
    elif isinstance(obj, list):
        for item in obj: tweets.extend(recursive_tweet_extractor(item))
    return tweets

new_data_received_recently = False

def save_data(new_tweets, raw_payload_metadata=None):
    global new_data_received_recently
    
    # 1. Process for ALL_DATA file
    all_data_json = get_current_output_filename()
    all_data_md = all_data_json.replace('.json', '.md')
    existing_all_data = []
    
    if os.path.exists(all_data_json):
        try:
            with open(all_data_json, 'r', encoding='utf-8') as f: existing_all_data = json.load(f)
            if existing_all_data and isinstance(existing_all_data[0], dict):
                existing_all_data = [[d.get('timestamp', ''), d.get('text_content', '')] for d in existing_all_data]
        except json.JSONDecodeError: pass
    
    existing_texts_all = {t[1] for t in existing_all_data if len(t) > 1 and t[1]}
    added_count = 0
    added_tweets = []
    
    for tweet in new_tweets:
        text = _tweet_text(tweet)
        if text and text not in existing_texts_all:
            legacy_row = _legacy_tweet_row(tweet)
            existing_all_data.append(legacy_row)
            existing_texts_all.add(text)
            added_tweets.append(tweet)
            added_count += 1
            
    if added_count > 0:
        existing_all_data.sort(key=lambda x: x[0] if len(x) > 0 else '', reverse=True)
        
        with open(all_data_json, 'w', encoding='utf-8') as f: json.dump(existing_all_data, f, ensure_ascii=False, separators=(',', ':'))
        
        with open(all_data_md, 'w', encoding='utf-8') as f:
            f.write("# Capital Chronicle Headlines (ALL DATA BATCH)\n\n")
            for t in existing_all_data:
                time_str = t[0] if len(t) > 0 else ""
                text_str = t[1].replace('\n', ' ') if len(t) > 1 and t[1] else ""
                f.write(f"- **[{time_str}]** {text_str}\n\n")
                
        print(f"[{datetime.now(timezone(timedelta(hours=7))).strftime('%H:%M:%S')}] Fetched {added_count} new headlines. Total saved in ALL_DATA: {len(existing_all_data)}")
        sidecar_count = append_headline_sidecars(added_tweets, raw_payload_metadata)
        print(f"[{datetime.now(timezone(timedelta(hours=7))).strftime('%H:%M:%S')}] Wrote {sidecar_count} Step1 headline sidecar rows.")
        
    # 2. Process for Daily files
    grouped_tweets = {}
    for tweet in new_tweets:
        if not _tweet_text(tweet): continue
        time_str = _tweet_timestamp(tweet)
        
        now = datetime.now(timezone(timedelta(hours=7)))
        effective_date = now - timedelta(days=1) if now.hour < 4 else now
        filename = os.path.join(DATA_DIR, f"capital_chronicle_{effective_date.strftime('%Y_%m_%d')}.json")
        
        try:
            parts = time_str.split()
            date_str = None
            if len(parts) >= 2:
                if '-' in parts[0] and len(parts[0].split('-')) == 3:
                    date_str = parts[0]
                elif '-' in parts[1] and len(parts[1].split('-')) == 3:
                    date_str = parts[1]
            
            if date_str:
                date_parts = date_str.split('-')
                if len(date_parts) == 3:
                    filename = os.path.join(DATA_DIR, f"capital_chronicle_{date_parts[0]}_{date_parts[1]}_{date_parts[2]}.json")
        except Exception:
            pass
            
        if filename not in grouped_tweets:
            grouped_tweets[filename] = []
        grouped_tweets[filename].append(tweet)
        
    total_daily_added = 0
    for json_file, tweets_group in grouped_tweets.items():
        md_file = json_file.replace('.json', '.md')
        existing_data = []
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f: existing_data = json.load(f)
                if existing_data and isinstance(existing_data[0], dict):
                    existing_data = [[d.get('timestamp', ''), d.get('text_content', '')] for d in existing_data]
            except json.JSONDecodeError: pass
            
        existing_texts = {t[1] for t in existing_data if len(t) > 1 and t[1]}
        daily_added = 0
        for tweet in tweets_group:
            text = _tweet_text(tweet)
            if text and text not in existing_texts:
                existing_data.append(_legacy_tweet_row(tweet))
                existing_texts.add(text)
                daily_added += 1
                total_daily_added += 1
                
        if daily_added > 0:
            existing_data.sort(key=lambda x: x[0] if len(x) > 0 else '', reverse=True)
            with open(json_file, 'w', encoding='utf-8') as f: json.dump(existing_data, f, ensure_ascii=False, separators=(',', ':'))
            
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(f"# Capital Chronicle Headlines ({os.path.basename(json_file)})\n\n")
                for t in existing_data:
                    time_str = t[0] if len(t) > 0 else ""
                    text_str = t[1].replace('\n', ' ') if len(t) > 1 and t[1] else ""
                    f.write(f"- **[{time_str}]** {text_str}\n\n")

    if total_daily_added > 0:
        print(f"[{datetime.now(timezone(timedelta(hours=7))).strftime('%H:%M:%S')}] Wrote {total_daily_added} new headlines to daily files.")

    # Flag that we got new data if EITHER file type received updates
    if added_count > 0 or total_daily_added > 0:
        new_data_received_recently = True

async def intercept_handler(response):
    if TARGET_URL_KEYWORD in response.url and response.status == 200:
        try:
            data = await response.json()
            raw_payload_metadata = archive_raw_payload(data, response.url)
            extracted_tweets = recursive_tweet_extractor(data)
            if extracted_tweets: save_data(extracted_tweets, raw_payload_metadata)
        except Exception as e:
            pass

TARGET_LIST_URL = "https://x.com/i/lists/1843870469143048642"

async def run_data_ingestion():
    global new_data_received_recently
    print("[SYSTEM] Connecting to CDP localhost:9222 for Data Ingestion...")
    start_time = datetime.now()
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = next((p for p in context.pages if "x.com" in p.url or "twitter.com" in p.url), None)
        
        if not page:
            print("[SYSTEM] X tab not found. Opening new tab...")
            page = await context.new_page()
            
        # Attach listener BEFORE any navigation or reload to catch the very first batch of newest tweets
        page.on("response", intercept_handler)
            
        if "1843870469143048642" not in page.url:
            print(f"[SYSTEM] Redirecting to target list: {TARGET_LIST_URL}")
            await page.goto(TARGET_LIST_URL)
            await page.wait_for_timeout(3000)
            
        print(f"[SYSTEM] Attached to: {page.url}. Refreshing to ensure clean state...")
        await page.reload()
        await page.wait_for_timeout(4000)
        
        # --- PHASE 1: BATCH HISTORY FETCH ---
        print(f"[SYSTEM] PHASE 1: Historical Batch Fetch...")
        print(f"[SYSTEM] Aggressively scrolling to fetch missing history.")
        empty_scrolls = 0
        
        while empty_scrolls < MAX_EMPTY_SCROLLS:
            new_data_received_recently = False
            
            try:
                retry_btn = page.locator("div[role='button']", has_text=re.compile(r"Retry", re.IGNORECASE)).locator("visible=true").first
                if await retry_btn.count() > 0:
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    await retry_btn.click()
                    print(f"[{datetime.now(timezone(timedelta(hours=7))).strftime('%H:%M:%S')}] [BATCH] Clicked Retry button.")
                    await asyncio.sleep(random.uniform(2.5, 4.0))
                    continue
            except PlaywrightTimeoutError: pass

            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(random.uniform(3.5, 5.5))
            
            if new_data_received_recently:
                empty_scrolls = 0
            else:
                empty_scrolls += 1
                print(f"[SYSTEM] No new data found. Empty scrolls: {empty_scrolls}/{MAX_EMPTY_SCROLLS}")
                await page.evaluate("window.scrollBy(0, -800)")
                await asyncio.sleep(1.0)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                
        print(f"[SYSTEM] Reached the bottom or Twitter limits for Phase 1.")
        
        # --- PHASE 2: CONTINUOUS STREAM ---
        print(f"[SYSTEM] PHASE 2: Switching to Continuous Stream Mode...")
        # Reset scroll to top to monitor new tweets naturally
        await page.evaluate("window.scrollTo(0, 0)")
        
        last_reload_time = datetime.now()
        reload_interval = random.uniform(1800.0, 2700.0)
        
        while True:
            if (datetime.now() - start_time).total_seconds() / 3600 > MAX_UPTIME_HOURS:
                print("[SYSTEM] Memory refresh. Reloading...")
                await page.reload()
                start_time = datetime.now()
                last_reload_time = datetime.now()
                await asyncio.sleep(10)
                continue
                
            if (datetime.now() - last_reload_time).total_seconds() > reload_interval:
                dt_str = datetime.now(timezone(timedelta(hours=7))).strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{dt_str} GMT+7] [NUDGE] Hard reloading page to force fetch new posts...")
                await page.reload()
                last_reload_time = datetime.now()
                reload_interval = random.uniform(1800.0, 2700.0)
                await asyncio.sleep(random.uniform(4.0, 7.0))
                continue
                
            try:
                await asyncio.sleep(random.uniform(3.5, 8.2))
                
                retry_btn = page.locator("div[role='button']", has_text=re.compile(r"Retry", re.IGNORECASE)).locator("visible=true").first
                if await retry_btn.count() > 0:
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    await retry_btn.click()
                    print(f"[{datetime.now(timezone(timedelta(hours=7))).strftime('%H:%M:%S')}] [NUDGE] Clicked Retry button.")
                    continue
                    
                btn = page.locator("div[role='button']", has_text=re.compile(r"(show.*post|post.*)", re.IGNORECASE)).locator("visible=true").first
                if await btn.count() > 0:
                    await asyncio.sleep(random.uniform(0.5, 2.1))
                    await btn.click()
                    print(f"[{datetime.now(timezone(timedelta(hours=7))).strftime('%H:%M:%S')}] [NUDGE] Clicked 'Show new posts'.")
                elif random.random() > 0.6:
                    await page.evaluate("window.scrollTo(0, 0)")
                    await asyncio.sleep(1.0)
                    await page.evaluate("window.scrollBy(0, 300)")
            except PlaywrightTimeoutError: pass

async def main():
    while True:
        try: 
            await run_data_ingestion()
        except Exception as e:
            print(f"[ERROR] Connection lost ({e}). Retrying in 30s...")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
