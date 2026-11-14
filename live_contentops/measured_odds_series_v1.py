"""CC-536: source-bound research pieces through the existing article publisher.

No bars, returns or probabilities are calculated here. Main supplies every value.
The commissioned method series has dated samples, not a current-market cutoff or
an invented scenario set. Public writes still belong to DurablePublicationCoordinator.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import subprocess

from .capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from .event_article_guard_v1 import PUBLIC_NOTICE, CONFLICTS_NOTICE

POLICY = "CC536_MEASURED_ODDS_SERIES_V1"
DESTINATION = "internal:measured-odds-piece"
NUMBER = re.compile(r"(?<![\w.])[+−-]?\d+(?:,\d{3})*(?:\.\d+)?%?")
TEXT_FIELDS = ("title", "subtitle", "dek", "social_hook", "social_summary", "substack_body_markdown")
FX = {"EURUSD", "USDJPY"}
MAIN_SOURCE_REPO = Path(r"A:\Capital Chronicle\Worktrees\codex-data-backlog")


def _read(path):
    return json.loads(Path(path).read_bytes())


def pointer(value, path):
    for part in path.strip("/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def sources(root):
    root = Path(root)
    manifest = _read(root / "manifest.json")
    if not re.fullmatch(r"live-[\w-]+", manifest["live_tag"]) or not re.fullmatch(r"[0-9a-f]{40}", manifest["main_commit"]):
        raise ValueError("ODDS_MAIN_LIVE_TAG_REQUIRED")
    values = {}
    for name, spec in manifest["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("ODDS_SOURCE_PATH_INVALID")
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != spec["sha256"]:
            raise ValueError("ODDS_SOURCE_BYTES_CHANGED:" + name)
        blob = __import__("hashlib").sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if blob != spec["git_blob"]:
            raise ValueError("ODDS_MAIN_BLOB_CHANGED:" + name)
        values[name] = json.loads(raw) if name.endswith(".json") else raw.decode("utf-8-sig")
    table = values["desk_odds_v1.json"]
    if table.get("schema") != "DeskOddsTableV1" or table["content_hash"] != manifest["table_hash"]:
        raise ValueError("ODDS_TABLE_HASH_CHANGED")
    if table.get("audit", {}).get("item") != "CC-521":
        raise ValueError("ODDS_CC521_AUDIT_REQUIRED")
    return manifest, values


def verify_main_snapshot(root, *, repo=MAIN_SOURCE_REPO):
    """Verify the pinned Main tag and blobs without touching its live checkout."""
    manifest, _ = sources(root)
    actual = subprocess.check_output(["git","-C",str(repo),"rev-parse",manifest["live_tag"]+"^{commit}"],text=True).strip()
    if actual != manifest["main_commit"]:
        raise ValueError("ODDS_MAIN_LIVE_TAG_CHANGED")
    specs = list(manifest["files"].values())
    refs = "\n".join(actual+":"+s["main_path"] for s in specs)+"\n"
    blobs = subprocess.check_output(["git","-C",str(repo),"cat-file","--batch-check=%(objectname)"],input=refs,text=True).splitlines()
    if blobs != [s["git_blob"] for s in specs]:
        raise ValueError("ODDS_SNAPSHOT_NOT_FROM_MAIN_LIVE_TAG")
    return {"live_tag":manifest["live_tag"],"commit":actual,"table_hash":manifest["table_hash"],"blobs_verified":len(blobs)}


def _numbers(text, table_hash):
    # The required fingerprint identifies the table; it is not a numerical claim.
    text = str(text).replace(table_hash, " " * len(table_hash))
    text = re.sub(r"\bS&P 500\b", lambda m: " " * len(m[0]), text)
    return list(NUMBER.finditer(text))


def number_report(piece, root):
    """List each printed numeric occurrence and its exact Main value and side.

    A coincidentally equal number elsewhere is insufficient: the author's full
    span must match and its source pointer is restricted to the intended row.
    """
    manifest, held = sources(root)
    table_hash = manifest["table_hash"]
    if piece["table_hash"] != table_hash:
        raise ValueError("ODDS_PIECE_TABLE_MISMATCH")
    reports, covered = [], {}
    for claim in piece.get("number_bindings", []):
        field, span = claim["field"], claim["span"]
        text = piece["article"][field]
        if text.count(span) != 1:
            raise ValueError("ODDS_EXACT_PUBLIC_SPAN_REQUIRED:" + span)
        file, path = claim["file"], claim["pointer"]
        if file == "desk_odds_v1.json":
            if not path.startswith(("/behaviours/", "/markets/", "/audit/", "/how_measured", "/what_this_is", "/by_market/", "/construction/", "/half_split_date")):
                raise ValueError("ODDS_PUBLIC_DERIVED_FIELD_REQUIRED")
            market = path.split("/")[2] if path.startswith(("/by_market/", "/markets/")) else None
            if market in FX and path.startswith("/by_market/") and not manifest.get("fx_repair_live"):
                raise ValueError("ODDS_FX_CLOSE_REPAIR_NOT_LIVE:" + market)
            if path.startswith("/by_market/"):
                behaviour = pointer(held[file], "/".join(path.split("/")[:4]))[0]
                if behaviour in held["desk_odds_sides_v1.json"]["two_sided_behaviours"]:
                    if claim.get("side") or re.search(r"\b(?:long|short)\b", span, re.I):
                        raise ValueError("ODDS_ONE_SIDE_REQUIRES_SIDE_FILE")
                    if "both sides together" not in span.casefold():
                        raise ValueError("ODDS_POOLED_LABEL_REQUIRED")
            if path.startswith("/construction/") and "both sides together" not in span.casefold():
                raise ValueError("ODDS_CONSTRUCTION_POOLED_LABEL_REQUIRED")
        elif file == "desk_odds_sides_v1.json":
            prefix = "/tables/" + table_hash + "/markets/"
            if not path.startswith(prefix):
                raise ValueError("ODDS_SIDE_TABLE_HASH_REQUIRED")
            rest = path[len(prefix):].split("/")
            if rest[0] in FX and not manifest.get("fx_repair_live"):
                raise ValueError("ODDS_FX_CLOSE_REPAIR_NOT_LIVE:" + rest[0])
            if "/sides/" in path and (not claim.get("side") or "/" + claim["side"] + "/" not in path):
                raise ValueError("ODDS_EXACT_SIDE_REQUIRED")
        elif file not in {"README.md", "AUDIT.md", "desk_odds_v1.py"} or path != "/":
            raise ValueError("ODDS_NUMERIC_SOURCE_NOT_ADMITTED")
        value = held[file] if path == "/" else pointer(held[file], path)
        source = str(value)
        start = text.index(span)
        source_excerpt = claim.get("source_excerpt")
        if source_excerpt is not None:
            if source_excerpt not in source:
                raise ValueError("ODDS_SOURCE_EXCERPT_CHANGED")
            source = source_excerpt
        for match in _numbers(span, table_hash):
            token = match.group()
            if not re.search(r"(?<![\d.])" + re.escape(token) + r"(?![\d.])", source):
                raise ValueError("ODDS_NUMBER_DIFFERS_FROM_SOURCE:" + token)
            covered.setdefault(field, set()).add(start + match.start())
            reports.append({"field":field, "public_span":span, "number":token,
                "file":file, "pointer":path, "table_value":value if not isinstance(value, str) else source,
                "side":claim.get("side"), "table_hash":table_hash})
    for field in TEXT_FIELDS:
        text = piece["article"].get(field, "")
        # Use original offsets, excluding fingerprint and the market's proper name.
        ignored = [(m.start(), m.end()) for m in re.finditer(re.escape(table_hash) + r"|S&P 500", text)]
        for match in NUMBER.finditer(text):
            if any(a <= match.start() < b for a,b in ignored):
                continue
            if match.start() not in covered.get(field, set()):
                raise ValueError("ODDS_UNBOUND_PUBLIC_NUMBER:" + field + ":" + match.group())
    return reports


def validate_piece(piece, root):
    if piece.get("policy") != POLICY or piece.get("piece") not in range(1, 8):
        raise ValueError("ODDS_SERIES_PIECE_REQUIRED")
    rows = number_report(piece, root)
    article = piece["article"]
    body = article["substack_body_markdown"]
    if not body.startswith("We ") or "So what:" not in body:
        raise ValueError("ODDS_READER_CALL_AND_SO_WHAT_REQUIRED")
    if PUBLIC_NOTICE not in body or CONFLICTS_NOTICE not in body:
        raise ValueError("ODDS_PUBLIC_NOTICES_REQUIRED")
    if piece["table_hash"] not in body:
        raise ValueError("ODDS_PUBLIC_TABLE_HASH_REQUIRED")
    if (article.get("reader_article_contract") or {}).get("policy") != "CC403_READER_ARTICLE_V1":
        raise ValueError("ODDS_READER_CONTRACT_REQUIRED")
    from .plan_analysis_pages_v1 import public_filter
    from .reader_article_contract_v1 import sentences, words
    for field in TEXT_FIELDS:
        public_filter(article.get(field, ""))
        for sentence in sentences(article.get(field, "")):
            if len(words(sentence)) > 22:
                raise ValueError("ODDS_VOICE_SENTENCE_TOO_LONG:" + sentence)
    if piece["piece"] == 1:
        required = ("both sides together", "euro and yen", "always long", "54", "2016", "2026")
        if any(word not in body.casefold() for word in required):
            raise ValueError("ODDS_METHOD_LIMITS_REQUIRED")
    if piece["piece"] in {4,5,6} and "both sides together" not in body.casefold():
        raise ValueError("ODDS_CONSTRUCTION_POOLED_LABEL_REQUIRED")
    return rows


def validate_plan(store, work_item_id, plan):
    row = store.get_outbox_message(work_item_id)
    if not row or row["destination"] != DESTINATION:
        raise ValueError("ODDS_REGISTERED_PIECE_REQUIRED")
    packet = json.loads(row["payload"])
    if packet["plan"] != plan or plan.get("measured_odds_piece") != work_item_id:
        raise ValueError("ODDS_REGISTERED_PLAN_CHANGED")
    validate_piece(packet["piece"], packet["source_root"])
    for file, digest in packet["artifacts"].items():
        if sha256((Path(packet["output_dir"]) / file).read_bytes()).hexdigest() != digest:
            raise ValueError("ODDS_REGISTERED_ARTIFACT_CHANGED:" + file)
    return packet


def before_write(coordinator, intent, destination):
    stored = coordinator.store.get_outbox_message(intent["measured_odds_piece"])
    packet = json.loads(stored["payload"]) if stored else {}
    if (packet.get("identity") != intent["work_item_id"]
            or packet.get("plan", {}).get("plan_hash") != intent["plan_hash"]):
        raise ValueError("ODDS_INTENT_BINDING_CHANGED")
    packet = validate_plan(coordinator.store, intent["work_item_id"], packet["plan"])
    assets = packet["media_assets"]
    for asset in assets:
        raw = Path(asset["path"]).read_bytes()
        if sha256(raw).hexdigest() != asset["sha256"]:
            raise ValueError("ODDS_CHART_BYTES_CHANGED")
    from .article_publication_quality_v1 import image_register, piece_id
    # It consumes the normal two-article daily budget, including the method page.
    return image_register(coordinator).reserve(piece_id=piece_id(coordinator.store,intent), assets=assets,
        lead_asset_id=assets[0]["asset_id"], now=coordinator._clock(),
        canonical_url=intent.get("canonical_url"), enforce_cap=destination=="substack")


def compile_payloads(article, canonical_url, media_asset_ids):
    """Format the writer's complete summary; never derive a market scenario."""
    notices = PUBLIC_NOTICE + "\n" + CONFLICTS_NOTICE
    summary = article["social_summary"]
    link = "Full analysis: " + canonical_url
    long = summary + "\n\n" + link + "\n\n" + notices
    media = list(media_asset_ids)
    limits={"telegram":4096,"discord":2000,"linkedin":3000,"facebook_page":63206,
            "instagram_business":2200,"youtube":1000}
    payloads={}
    for destination,limit in limits.items():
        if len(long)>limit:
            raise ValueError("ODDS_AUTHORED_SUMMARY_TOO_LONG:"+destination)
        payloads[destination]={"format":"measured_odds_summary","text":long,
            "platform_limit":limit,"hard_truncation_used":False,"media_asset_ids":media}
    for destination,limit in (("x",280),("threads",500)):
        paragraphs=[article["social_hook"],link+"\n\n"+notices,*summary.split("\n\n")]
        if any(len(p)>limit for p in paragraphs):
            raise ValueError("ODDS_AUTHORED_THREAD_PASSAGE_TOO_LONG:"+destination)
        posts=[{"order":i,"role":"root" if i==0 else "reply","text":text,
                "media_asset_ids":media if i==0 else []} for i,text in enumerate(paragraphs)]
        payloads[destination]={"format":"thread","posts":posts,"root_text":posts[0]["text"],
            "reply_texts":[p["text"] for p in posts[1:]],"full_text":"\n\n".join(paragraphs),
            "platform_limit":limit,"hard_truncation_used":False,"media_asset_ids":media}
    return payloads


def confirmed_method_page(store):
    """Shared read-only reference for new plan posts and CC-537's daily board."""
    identity = "cc536-measured-odds-1"
    row = store.get_outbox_message(identity)
    if not row or row["destination"] != DESTINATION:
        return None
    packet = json.loads(row["payload"])
    from .publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
    ids = Coordinator._ids(identity, packet["plan"]["plan_hash"], "substack")
    dispatch = store.get_platform_dispatch(ids["dispatch_id"]) or {}
    reconciled = any(r["reconciliation_id"] == ids["reconciliation_id"] and r["status"] == "RECONCILED_CONFIRMED"
                     for r in store.get_reconciliations_for_work_item(identity))
    url = dispatch.get("public_object_url", "")
    if (dispatch.get("status") != "DISPATCH_CONFIRMED" or not reconciled
            or not re.fullmatch(r"https://capitalchronicle\.substack\.com/p/[a-z0-9-]+", url)):
        return None
    return {"identity":identity,"plan_hash":packet["plan"]["plan_hash"],"canonical_url":url,
            "table_hash":packet["piece"]["table_hash"]}


def add_method_link(payload, reference):
    if not reference:
        return payload
    url = reference["canonical_url"]
    if not re.fullmatch(r"https://capitalchronicle\.substack\.com/p/[a-z0-9-]+", url):
        raise ValueError("ODDS_CONFIRMED_METHOD_URL_REQUIRED")
    result = deepcopy(payload)
    line = "How we measure historical odds: " + url
    if result.get("posts"):
        posts = result["posts"]
        posts.append({"text":line,"media_asset_ids":[],"order":len(posts),"role":"reply"})
        result["reply_texts"] = [p["text"] for p in posts[1:]]
        result["full_text"] = "\n\n".join(p["text"] for p in posts)
    else:
        for key in ("text", "full_text"):
            if result.get(key):
                result[key] += "\n\n" + line
    return result


def register(store, piece_file, output_dir):
    piece_file, output = Path(piece_file), Path(output_dir).resolve()
    piece = _read(piece_file)
    root = piece_file.parent / "source"
    report = validate_piece(piece, root)
    identity = "cc536-measured-odds-" + str(piece["piece"])
    prior = store.get_outbox_message(identity)
    if prior:
        packet = json.loads(prior["payload"])
        if packet["piece"] != piece:
            raise ValueError("ODDS_ISSUED_PIECE_IMMUTABLE")
        return validate_plan(store, identity, packet["plan"])
    verification = verify_main_snapshot(root)
    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(root, output / "source", dirs_exist_ok=True)
    article = deepcopy(piece["article"])
    assets = []
    for spec in piece["media_assets"]:
        source = (piece_file.parent / spec["path"]).resolve()
        if not source.is_relative_to((piece_file.parent / "media").resolve()):
            raise ValueError("ODDS_ITEM_MEDIA_FOLDER_REQUIRED")
        target = output / "media" / source.name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source, target)
        if sha256(target.read_bytes()).hexdigest() != spec["sha256"]:
            raise ValueError("ODDS_CHART_BYTES_CHANGED")
        assets.append({**spec,"path":str(target)})
    if not assets or any(a.get("modality") != "tradingview_chart_snapshot" for a in assets):
        raise ValueError("ODDS_AUTHENTIC_TRADINGVIEW_CHART_REQUIRED")
    from .eight_platform_substack_first_pipeline_v1 import build_native_derivative_payloads
    from .v1_simple_gemini_newsroom_v1 import _build_simple_publication_lifecycle_plan
    pending = "https://capitalchronicle.substack.com/p/pending-publication"
    payloads = build_native_derivative_payloads(article=article, selection={},canonical_url=pending,
                                               media_asset_ids=[a["asset_id"] for a in assets])
    evidence = sha256_of(_read(root / "manifest.json"))
    plan = _build_simple_publication_lifecycle_plan(run_id=identity, output_dir=output,
        selected_candidate={"story_identity":identity}, selected_plan_entry={"article_mode":"EVERGREEN_EXPLAINER"},
        article=article, article_identity=sha256_of(article), native_previews={"packages":payloads},
        qualified_record={"accepted_evidence_ids":[piece["table_hash"]],"accepted_evidence_sha256":evidence},
        epistemic_state={"evidence_basis":"CAPITAL_CHRONICLE_OWN_RESEARCH", "event_confirmation_state":"NOT_EVENT_REPORTING"},
        media_assets=assets)
    plan.update(measured_odds_piece=identity)
    plan.pop("plan_hash",None)
    plan["plan_hash"] = sha256_of(plan)
    (output / "article_manifest_v1.json").write_bytes(canonical_bytes(article))
    (output / "number-report.json").write_bytes(canonical_bytes(report))
    (output / "piece.json").write_bytes(canonical_bytes(piece))
    (output / "native_preview_packages_v1.json").write_bytes(canonical_bytes({"packages":payloads}))
    artifacts = {f:sha256((output/f).read_bytes()).hexdigest() for f in
        ("article_manifest_v1.json","run_context_v1.json","piece.json")}
    artifacts["source/manifest.json"] = sha256((output/"source/manifest.json").read_bytes()).hexdigest()
    packet = {"identity":identity,"piece":piece,"main_verification":verification,"output_dir":str(output),"source_root":str(output/"source"),
              "plan":plan,"media_assets":assets,"artifacts":artifacts}
    store.create_work_item(work_item_id=identity,story_id=identity,title=article["title"],target_surface="MULTI_PLATFORM")
    store.register_outbox_message(message_id=identity,work_item_id=identity,destination=DESTINATION,
        payload=canonical_bytes(packet).decode(),status="EDITORIAL_INTERNAL")
    return packet


def continue_piece(store, packet, *, invocation_id, rollout, command="resume", request_hash=None, response=None, automatic=False):
    from .native_desktop_publication_v1 import live_publication_policy
    from .native_neo_executor_v1 import bind_native_neo_coordinator, NativeNeoInputRequired
    live_publication_policy(rollout)
    if Path(store.db_path).resolve() != Path(rollout["store_path"]).resolve():
        raise ValueError("ODDS_PRODUCTION_STORE_MISMATCH")
    validate_plan(store, packet["identity"], packet["plan"])
    from .neo_endpoint_executor_v1 import NeoMcpClient
    client = NeoMcpClient(task_name="cc536 measured odds",group_title="codex/cc536-method-page") if automatic else None
    coordinator, executor = bind_native_neo_coordinator(store,operation_id=packet["identity"],
        output_dir=Path(packet["output_dir"])/"native-neo",native_invocation_id=invocation_id,
        allow_publish=True,automatic=automatic,endpoint_client=client)
    coordinator.recovery_scope={"work_item_id":packet["identity"],"plan":packet["plan"],"exact_work_item_only":True}
    try:
        if command in {"begin","submit"}:
            result = executor.begin(request_hash) if command=="begin" else executor.submit(request_hash,response)
        elif command=="status":
            result = {"dispatches":[d for d in store.list_platform_dispatches()
                if (store.get_outbox_message(d["message_id"]) or {}).get("work_item_id")==packet["identity"]]}
        else:
            result=coordinator.publish_plan(packet["identity"],packet["plan"])
    except NativeNeoInputRequired as pending:
        return {"state":"NATIVE_NEO_TOOL_PENDING","native_tool_request":pending.request}
    return {"publication":result,"pending_requests":executor.pending()}


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("check","register","resume","status","begin","submit"))
    parser.add_argument("--piece",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path)
    parser.add_argument("--rollout",type=Path,default=Path("config/native_desktop_rollout_v1.json"))
    parser.add_argument("--invocation-id")
    parser.add_argument("--request-hash")
    parser.add_argument("--response",type=Path)
    parser.add_argument("--result",type=Path,required=True)
    parser.add_argument("--automatic",action="store_true")
    args=parser.parse_args()
    if args.command=="check":
        result={"status":"PASS","numbers":validate_piece(_read(args.piece),args.piece.parent/"source")}
    else:
        from .durable_operational_store_v1 import ContentOpsDurableStore
        rollout=_read(args.rollout);store=ContentOpsDurableStore(rollout["store_path"])
        packet=register(store,args.piece,args.output_dir)
        result=packet if args.command=="register" else continue_piece(store,packet,invocation_id=args.invocation_id,
            rollout=rollout,command=args.command,request_hash=args.request_hash,
            response=_read(args.response) if args.response else None,automatic=args.automatic)
    args.result.parent.mkdir(parents=True,exist_ok=True)
    args.result.write_bytes(canonical_bytes(result))
    print(json.dumps({"result_path":str(args.result),"state":result.get("state",result.get("status","SAVED"))}))


if __name__=="__main__":
    main()
