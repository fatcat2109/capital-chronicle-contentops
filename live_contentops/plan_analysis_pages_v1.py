"""Decision 113: source-bound plan pages, through the existing publication owner.

Main's sealed run is read, never changed. A native writer supplies structured
public paragraphs. Code verifies their numbers, rights and exact plan binding,
then renders them; it does not invent an explanation or a missing scenario.
"""
from __future__ import annotations

from decimal import Decimal
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re

from . import plan_status_posts_v1 as posts
from .capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from .event_article_guard_v1 import PUBLIC_NOTICE, CONFLICTS_NOTICE
from .public_time_v1 import public_timestamp, require_public_time

DESTINATION = "internal:plan-analysis-page"
RUN_ROOT = Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-research\daily-research-portfolio-279805139")
SECTIONS = (
    ("macro", "Macro: the drivers, rates and the dollar"),
    ("fundamental", "Fundamental: the asset's own economics"),
    ("technical", "Technical: structure, momentum and the plan's levels"),
    ("geopolitical", "Geopolitical: events and transmission"),
    ("priced_in", "What is priced in"),
    ("scenarios", "Scenarios: base, upside and downside"),
    ("desk_process", "How the desk reached its view"),
)

READER_SECTIONS = (
    ("priced_in", "What is priced in"), ("positioning", "Positioning"),
    ("fear", "Fear"), ("technical", "Structure"), ("story", "The story"),
    ("macro", "Macro"), ("scenarios", "The scenarios"), ("plan", "The plan"),
    ("invalidation", "What would change our mind"),
)


def sections_for(manuscript):
    return READER_SECTIONS if manuscript.get("reader_contract") == "CC466_V1" else SECTIONS
RIGHTS = {"CAPITAL_CHRONICLE_ORIGINAL_ANALYSIS", "PUBLIC_DOMAIN_OFFICIAL_FACT", "SINGLE_ATTRIBUTED_FACT"}
_PRIVATE = re.compile(
    r"\b(?:demo|mt[45]|exness[\w-]*|metatrader|account\s+(?:id|number|balance|equity)|"
    r"model[\s-]+positions?|position\s+siz(?:e|ing)|risk\s+(?:allocation|per trade)|(?:our|my)\s+(?:balance|equity|capital)|"
    r"ticket(?:\s+id)?|p\s*&\s*l|realised profit|realized profit|lot\s+size|HALF_PLAN_RISK)\b|"
    r"\b\d+(?:\.\d+)?\s*(?:standard\s+|mini\s+|micro\s+)?lots?\b|"
    r"\b(?:279805139|279779602)\b", re.I)
_MONEY = re.compile(r"\b(?:balance|equity|capital|allocation|size|sizing|risk budget|profit|loss)\b.{0,35}"
                    r"(?:[$€£]\s*\d|\d[\d,.]*\s*(?:USD|EUR|dollars|lots|%))", re.I)
_MODELS = re.compile(r"\b(?:GPT(?:[- .]?\d[\w.-]*)?|ChatGPT|Claude|Opus|Gemini|Luna|Sol\s*6|Antigravity|"
                     r"AI[- ](?:run|native|powered|driven)|(?:run|written|generated|operated|powered)\s+by\s+AI|"
                     r"(?:our|the)\s+(?:AI|artificial intelligence)\s+(?:desk|analysts?|team))\b", re.I)
_X = re.compile(r"(?:https?://(?:www\.)?(?:x|twitter)\.com/|JIM_X_LIST|PRIVATE_X_LIST|X[-_ ]list)", re.I)
_SECRET = re.compile(r"(?:sk-[A-Za-z0-9]{16,}|access[_ -]?token\s*[:=]|api[_ -]?key\s*[:=]|password\s*[:=])", re.I)
_NUM = re.compile(r"(?<![\w.])[+−-]?\d+(?:,\d{3})*(?:\.\d+)?%?(?!\w|\.\d)")


def _numbers(text):
    # A sign and a percentage are material. A scalar probability of 55 can
    # support '55%' but never a made-up complement or a changed magnitude.
    from .event_article_guard_v1 import NAMED_NUMBER
    text = str(text)
    # A stated decline and a signed negative are the same sourced magnitude.
    # An unsigned rise never gains that equivalence.
    text = re.sub(r"\b(?:down|fell|declined|dropped|lost)\s+(\d+(?:\.\d+)?%)", r"-\1", text, flags=re.I)
    text = re.sub(r"\b(\d+(?:\.\d+)?%)\s+(?:decline|fall|drop|decrease)\b", r"-\1", text, flags=re.I)
    values = {format(Decimal(m.group().replace(',', '').replace('−', '-').rstrip('%')).normalize(), 'f')
              for m in _NUM.finditer(NAMED_NUMBER.sub('', text))}
    values.update(re.findall(r"\b(?:SMA|ATR|M|H)(\d+)\b", text))
    return values


def _pointer(value, pointer):
    for part in pointer.strip('/').split('/') if pointer else []:
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def load_run(plan, *, run_root=RUN_ROOT):
    run_id = plan.get("run_id")
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("PLAN_ANALYSIS_RUN_ID_INVALID")
    folder = next((Path(run_root) / kind / run_id for kind in ("requests", "shocks")
                   if (Path(run_root) / kind / run_id / "role-pack.json").is_file()), None)
    if folder is None:
        raise ValueError("PLAN_ANALYSIS_RUN_NOT_FOUND")
    names = ["role-pack.json", "role-evidence.json", "integrated-owner-record.json",
             "plan-geometry.json", "options-context.json", "final-decision-freeze.json", "desktop-manual-result.json"]
    names += (["analysis-native.json"] if (folder / "analysis-native.json").is_file()
              else ["primary-native.json", "critical-native.json", "owner-native.json"])
    names += [name for name in ("critic-note.json", "market-context.json", "shock-pack.json") if (folder / name).is_file()]
    documents, manifest = {}, {}
    for name in names:
        raw = (folder / name).read_bytes()
        documents[name] = json.loads(raw)
        manifest[name] = {"path": str(folder / name), "sha256": sha256(raw).hexdigest(), "bytes": len(raw)}
    if sha256_of(documents["desktop-manual-result.json"]) != plan.get("analysis_result_hash"):
        raise ValueError("PLAN_ANALYSIS_RESULT_HASH_MISMATCH")
    freeze = documents["final-decision-freeze.json"]
    if freeze.get("qualitative_result_hash") != plan.get("analysis_result_hash"):
        raise ValueError("PLAN_ANALYSIS_FREEZE_RESULT_MISMATCH")
    return {"folder": folder, "documents": documents, "manifest": manifest, "freeze": freeze,
            "source_plan": plan}


def public_filter(text, *, rights="CAPITAL_CHRONICLE_ORIGINAL_ANALYSIS", source_name="Capital Chronicle",
                  source_locator="", private_texts=()):
    """The same code is called at render, registration and the final write boundary."""
    if rights not in RIGHTS:
        raise ValueError("PLAN_ANALYSIS_PUBLIC_REDISTRIBUTION_NOT_LICENSED")
    if not source_name or _X.search(source_locator) or _X.search(text):
        raise ValueError("PLAN_ANALYSIS_PRIVATE_X_LIST_FORBIDDEN")
    normal = " ".join(text.casefold().split())
    for private in private_texts:
        line = " ".join(str(private).casefold().split())
        if len(line) >= 24 and line in normal:
            raise ValueError("PLAN_ANALYSIS_PRIVATE_X_LIST_FORBIDDEN")
    if _PRIVATE.search(text) or _MONEY.search(text):
        raise ValueError("PLAN_ANALYSIS_PRIVATE_ACCOUNT_OR_SIZE_FORBIDDEN")
    if _MODELS.search(text):
        raise ValueError("PLAN_ANALYSIS_DESK_AI_LABEL_FORBIDDEN")
    if _SECRET.search(text):
        raise ValueError("PLAN_ANALYSIS_SECRET_FORBIDDEN")
    if re.search(r"\b(?:buy now|sell now|you should (?:buy|sell)|we recommend (?:buying|selling))\b", text, re.I):
        raise ValueError("PLAN_ANALYSIS_RECOMMENDATION_FORBIDDEN")
    from .preview_link_guard_v1 import find_forbidden_link
    if find_forbidden_link(text):
        raise ValueError("PREVIEW_HOST_LINK_FORBIDDEN")
    require_public_time(text)
    return {"status": "PASS", "sha256": sha256(text.encode()).hexdigest()}


def _source_text(run, ref):
    name, pointer = ref["file"], ref["pointer"]
    if name == "plan-export":
        document = run["source_plan"]
    elif name in run["documents"]:
        document = run["documents"][name]
    else:
        raise ValueError("PLAN_ANALYSIS_SOURCE_FILE_NOT_BOUND")
    # Raw accounts, execution packets and bulk vendor series are never public
    # sources. Main's original analytical prose and official single facts are.
    if re.search(r"(?:account|portfolio_state|cost_inputs|cost_summary|execution|risk_allocation)", pointer, re.I):
        raise ValueError("PLAN_ANALYSIS_PRIVATE_SOURCE_POINTER")
    value = _pointer(document, pointer)
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        raise ValueError("PLAN_ANALYSIS_SCALAR_SOURCE_REQUIRED")
    if ref.get("transform") == "ET":
        return public_timestamp(value)
    if ref.get("transform") == "ET12":
        from .plan_reader_copy_v1 import et
        return et(value)
    if ref.get("transform") == "TIMEFRAME_WORDS":
        return re.sub(r"\bM(\d+)\b", r"\1-minute", str(value))
    if ref.get("transform"):
        raise ValueError("PLAN_ANALYSIS_SOURCE_TRANSFORM_INVALID")
    return str(value)


def validate_manuscript(plan, manuscript, run):
    if (manuscript.get("plan_id") != plan["plan_id"]
            or manuscript.get("registration_hash") != plan["registration_hash"]):
        raise ValueError("PLAN_ANALYSIS_EXACT_PLAN_REQUIRED")
    sections = sections_for(manuscript)
    if set(manuscript.get("sections", {})) != {key for key, _ in sections}:
        raise ValueError("PLAN_ANALYSIS_ALL_SEVEN_SECTIONS_REQUIRED")
    private_texts = []
    for name in ("market-context.json", "shock-pack.json"):
        document = run["documents"].get(name, {})
        items = document.get("items", []) if name == "market-context.json" else document.get("headlines", {}).get("rows", [])
        for item in items:
            if not isinstance(item, dict):
                continue
            if name == "shock-pack.json" or _X.search(json.dumps(item)):
                private_texts.extend(item[k] for k in ("headline", "text", "body", "title") if isinstance(item.get(k), str))
    bound = []
    for key, _ in sections:
        section = manuscript["sections"][key]
        if not section.get("paragraphs") or not section.get("summary"):
            raise ValueError("PLAN_ANALYSIS_SECTION_EMPTY:" + key)
        for index, paragraph in enumerate(section["paragraphs"]):
            text = paragraph["text"]
            refs = paragraph.get("refs") or []
            if not refs:
                raise ValueError("PLAN_ANALYSIS_PARAGRAPH_SOURCES_REQUIRED")
            public_filter(text, rights=paragraph.get("rights", ""),
                          source_name=paragraph.get("source_name", ""),
                          source_locator=paragraph.get("source_locator", ""),
                          private_texts=private_texts)
            source = "\n".join(_source_text(run, ref) for ref in refs)
            if _numbers(text) - _numbers(source):
                raise ValueError("PLAN_ANALYSIS_UNBOUND_NUMBER:" + key + ":" + str(index))
            bound.append({"section": key, "paragraph": index, "public_sha256": sha256(text.encode()).hexdigest(),
                          "numbers": sorted(_numbers(text)), "refs": refs})
        public_filter(section["summary"], private_texts=private_texts)
        if _numbers(section["summary"]) - _numbers(" ".join(p["text"] for p in section["paragraphs"])):
            raise ValueError("PLAN_ANALYSIS_UNBOUND_SUMMARY_NUMBER:" + key)
    for field in ("title", "subtitle", "introduction"):
        public_filter(manuscript[field], private_texts=private_texts)
        if _numbers(manuscript[field]) - _numbers(" ".join(p["text"] for s in manuscript["sections"].values() for p in s["paragraphs"])):
            raise ValueError("PLAN_ANALYSIS_UNBOUND_HEADING_NUMBER")
    return bound


def _owner_candidate(plan, run):
    documents = run["documents"]
    owner = documents.get("analysis-native.json", {}).get("native_synthesis") or documents["owner-native.json"]
    owner = owner.get("native_synthesis") or owner
    cid = {"XAUUSD": "cand_macro_gold", "USOIL": "cand_macro_wti", "US500": "cand_macro_spx",
           "BTCUSD": "cand_macro_btcusd", "EURUSD": "cand_macro_eurusd", "USDJPY": "cand_macro_usdjpy"}.get(plan["asset_id"])
    index = next(i for i,c in enumerate(owner["candidates"]) if c["candidate_id"] == cid)
    combined = "analysis-native.json" in documents
    return owner["candidates"][index], ("analysis-native.json" if combined else "owner-native.json"), ("/native_synthesis" if combined else "") + f"/candidates/{index}"


def _public_geometry(plan, run):
    if not plan.get("zone"):
        return [], []
    candidate, filename, pointer = _owner_candidate(plan, run)
    lines, bindings = [], []
    for key in ("pullback", "breakout"):
        leg = (candidate.get("directional_entries") or {}).get(key, {})
        bounds = leg.get("entry_bounds") or {}
        fields = (bounds.get("minimum"), bounds.get("maximum"), leg.get("stop_level"), leg.get("target_level"))
        if any(v is None for v in fields):
            lines.append(key.capitalize() + " geometry was not fully priced in the original record; no missing level has been inferred.")
            continue
        low, high, stop, target = map(posts._level, fields)
        text = f"Original {key} condition: price reaches {low}–{high}. Invalidation level: {stop}. Capital Chronicle model objective: {target}."
        public_filter(text)
        lines.append(text)
        refs = [{"file": filename, "pointer": pointer + f"/directional_entries/{key}/" + path}
                for path in ("entry_bounds/minimum", "entry_bounds/maximum", "stop_level", "target_level")]
        bindings.append({"section": "technical", "paragraph": "structured_" + key,
                         "public_sha256": sha256(text.encode()).hexdigest(), "numbers": sorted(_numbers(text)), "refs": refs})
    return lines, bindings


def _card(plan, run, folder, manuscript):
    """One new owned diagram of this run's levels; no later price history."""
    from .publication_image_contract_v1 import EFFECTIVE_FROM
    if posts._utc(run["freeze"]["frozen_at_utc"]) >= EFFECTIVE_FROM:
        row = {"key": "plan-analysis-" + plan["plan_id"], "symbol": plan["asset_id"],
               "at_utc": run["freeze"]["frozen_at_utc"],
               "instrument_title": manuscript["title"],
               "levels": posts._display_plan(posts._built_plan(plan))}
        return posts._post_image(row, folder)[0]
    from .plan_analysis_media_v1 import render as render_card
    candidate, _, _ = _owner_candidate(plan, run)
    return render_card(plan,candidate,folder / 'media',frozen_at=run['freeze']['frozen_at_utc'])


def _assemble(plan, manuscript, run):
    freeze = run["freeze"]
    timestamp = public_timestamp(freeze["frozen_at_utc"])
    cutoff = public_timestamp(freeze.get("decision_cutoff_utc", freeze["frozen_at_utc"]))
    audit = f"Evidence cutoff: {cutoff}. The view was fixed at {timestamp}. Analysis fingerprint: {freeze['immutable_hash']}."
    reader = manuscript.get("reader_contract") == "CC466_V1"
    geometry, geometry_bindings = ([], []) if reader else _public_geometry(plan, run)
    paragraphs = [manuscript["introduction"]]
    for key, title in sections_for(manuscript):
        paragraphs += ["## " + title, *[p["text"] for p in manuscript["sections"][key]["paragraphs"]]]
        if key == "technical":
            paragraphs += geometry
    if reader:
        from .plan_reader_copy_v1 import page_footer, check_text
        paragraphs += page_footer(plan, freeze, legacy=manuscript.get("reader_revision", 1) < 2)
    else:
        paragraphs += [audit]
    paragraphs += [PUBLIC_NOTICE, CONFLICTS_NOTICE]
    body = "\n\n".join(paragraphs)
    public_filter(body)
    if reader:
        check_text(body, source="\n".join(_source_text(run, ref) for section in manuscript["sections"].values()
            for paragraph in section["paragraphs"] for ref in paragraph["refs"]),
            check_numbers=False, prose=False)
    payload = {"title": manuscript["title"], "subtitle": manuscript["subtitle"], "body_markdown": body}
    return payload, paragraphs, geometry_bindings


def render(plan, manuscript, *, output_dir, run_root=RUN_ROOT):
    run = load_run(plan, run_root=run_root)
    bindings = validate_manuscript(plan, manuscript, run)
    freeze = run["freeze"]
    payload, paragraphs, geometry_bindings = _assemble(plan, manuscript, run)
    bindings += geometry_bindings
    body = payload["body_markdown"]
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    card = _card(plan, run, folder, manuscript) if plan.get("asset_id") in posts.MARKETS and plan.get("zone") else None
    if card and manuscript.get("reader_contract") == "CC466_V1":
        card = {**card, "article_inclusion": True, "canonical_article_media": True,
                "placement_after": manuscript["introduction"], "article_section": "introduction",
                "canonical_article_section_association": "introduction"}
    (folder / "article.md").write_text("# " + payload["title"] + "\n\n" + body, encoding="utf-8")
    html = '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
    html += '<style>body{font:18px/1.65 Georgia,serif;max-width:760px;margin:36px auto;padding:0 22px;color:#18252b}h1{line-height:1.2}h2{font:600 24px/1.3 system-ui;margin-top:2em}p{overflow-wrap:anywhere}</style>'
    html += '<h1>' + escape(payload['title']) + '</h1><p>' + escape(payload['subtitle']) + '</p>'
    for index, paragraph in enumerate(paragraphs):
        html += '<h2>' + escape(paragraph[3:]) + '</h2>' if paragraph.startswith('## ') else '<p>' + escape(paragraph).replace('\n','<br>') + '</p>'
        if index == 0 and card:
            html += '<figure style="margin:24px 0"><img style="width:100%;height:auto" src="' + escape(Path(card['path']).as_uri()) + '" alt="' + escape(card['alt_text']) + '"><figcaption>' + escape(card['caption']) + '</figcaption></figure>'
    (folder / "article.html").write_text(html, encoding="utf-8")
    packet = {"schema_version": "contentops.plan_analysis_page.v1", "plan_id": plan["plan_id"],
              "registration_hash": plan["registration_hash"], "run_id": plan["run_id"],
              "analysis_result_hash": plan["analysis_result_hash"], "native_payload": payload,
               "summary": {k: manuscript["sections"][k]["summary"] for k, _ in sections_for(manuscript)},
              "source_manifest": run["manifest"], "numeric_bindings": bindings,
              "freeze": {k: freeze[k] for k in ("frozen_at_utc", "immutable_hash")},
              "authorship": manuscript.get("authorship", {}), "manuscript": manuscript, "run_root": str(Path(run_root)),
              "source_plan": plan, "media_assets": [card] if card else [], "output_dir": str(folder.resolve())}
    article = {"title": payload["title"], "body": body, "market_asset": plan.get("asset_id")}
    state = folder / "tradingview_capture_v1.json"
    if state.is_file():
        from .publication_image_contract_v1 import POLICY
        capture_state = json.loads(state.read_bytes())
        article.update(publication_image_contract=POLICY,
            tradingview_capture_state_path=str(state.resolve()), tradingview_capture_key=capture_state["key"],
            tradingview_text_fallback=capture_state.get("status") == "TEXT_ONLY")
    (folder / "run_context_v1.json").write_bytes(canonical_bytes({"article": article,
        "selection": {}, "media": {"assets": packet["media_assets"]}}))
    (folder / "page.json").write_bytes(canonical_bytes(packet))
    return packet


def register_page(store, packet):
    from .destination_transport_registry_v1 import REGISTRY_VERSION, registration_for_destination
    identity = "plan-analysis-" + packet["plan_id"]
    previous = store.get_outbox_message(identity)
    if previous:
        held = json.loads(previous["payload"])
        if held["registration_hash"] != packet["registration_hash"] or held["native_payload"] != packet["native_payload"]:
            raise ValueError("PLAN_ANALYSIS_EXISTING_PAGE_CHANGED")
        if held.get("media_assets") == packet.get("media_assets"):
            return held
        return replace_unpublished_media(store,held,packet)
    body = packet["native_payload"]["body_markdown"]
    registration = registration_for_destination("substack")
    plan = {"schema_version": "contentops.publication_plan.v1", "plan_analysis_page": identity,
            "story_identity": identity, "article_identity": identity, "package_identity": identity,
            "output_dir": packet["output_dir"], "transport_registry_version": REGISTRY_VERSION,
            "policy_mode_version": "AUTONOMOUS_DEFAULT:JIM_DECISION_113",
            "publication_window": {"window_identity": identity},
            "destinations": [{"destination": "substack", "surface": registration.surface,
                              "transport_type": registration.transport_type, "payload": body,
                              "payload_hash": sha256(body.encode()).hexdigest()}]}
    plan["plan_hash"] = sha256_of(plan)
    value = {**packet, "page_id": identity, "plan": plan}
    store.create_work_item(story_id=identity, work_item_id=identity, title=packet["native_payload"]["title"], target_surface="SUBSTACK_ARTICLE")
    store.register_outbox_message(message_id=identity, work_item_id=identity, destination=DESTINATION,
                                 payload=canonical_bytes(value).decode(), status="EDITORIAL_INTERNAL")
    return value


def replace_unpublished_media(store, held, packet):
    """Keep the same page/text while correcting media before any native send.

    A prior local failed attempt first needs exact absence reconciliation. Old
    packets/intents remain retained; a revised media hash gets its own dispatch.
    """
    if held["native_payload"]!=packet["native_payload"] or held["registration_hash"]!=packet["registration_hash"]:
        raise ValueError("PLAN_ANALYSIS_EXISTING_PAGE_CHANGED")
    for row in store.list_outbox_messages(work_item_id=held["page_id"]):
        if row["destination"]=="internal:native-neo-tool":
            if json.loads(row["payload"]).get("request",{}).get("action") in {"PUBLISH","EDIT_EXISTING"}:
                raise ValueError("PLAN_ANALYSIS_MEDIA_REVISION_NATIVE_WRITE_ALREADY_ISSUED")
        if row["destination"]=="substack":
            with store.get_read_only_connection() as conn:
                dispatch=conn.execute("SELECT status FROM platform_dispatches WHERE message_id=?",(row["message_id"],)).fetchone()
            if dispatch and dispatch["status"] not in {"DEFINITE_NO_WRITE","RECONCILED_ABSENT_SAFE_TO_RETRY"}:
                raise ValueError("PLAN_ANALYSIS_MEDIA_REVISION_READBACK_REQUIRED")
    plan={**held["plan"],"analysis_media_sha256":[a["sha256"] for a in packet.get("media_assets",[])]}
    plan.pop("plan_hash",None);plan["plan_hash"]=sha256_of(plan)
    revised={**packet,"page_id":held["page_id"],"plan":plan}
    store.register_outbox_message(message_id=held["page_id"]+"-prior-media-"+held["plan"]["plan_hash"],
        work_item_id=held["page_id"],destination="internal:plan-analysis-revision",
        payload=canonical_bytes(held).decode(),status="EDITORIAL_INTERNAL")
    store.finalize_outbox_payload_before_dispatch(message_id=held["page_id"],payload=canonical_bytes(revised).decode(),status="EDITORIAL_INTERNAL")
    for row in store.list_outbox_messages(work_item_id=held["page_id"],destination="substack"):
        intent=json.loads(row["payload"])
        if intent.get("plan_hash")!=plan["plan_hash"]:
            store.set_outbox_status(row["message_id"],"SUPERSEDED_UNSENT_MEDIA_REVISION")
    return revised


def replace_unpublished_copy(store, held, packet):
    """A confirmed pre-click refusal may repair the same retained draft's copy.

    The old request and its exact response remain immutable. A possibly sent
    page always requires its existing readback and cannot enter this function.
    """
    if held["registration_hash"] != packet["registration_hash"] or held["plan_id"] != packet["plan_id"]:
        raise ValueError("PLAN_ANALYSIS_EXACT_PLAN_REQUIRED")
    for row in store.list_outbox_messages(work_item_id=held["page_id"]):
        if row["destination"] != "substack":
            continue
        with store.get_read_only_connection() as conn:
            dispatch=conn.execute("SELECT * FROM platform_dispatches WHERE message_id=?",(row["message_id"],)).fetchone()
        if dispatch and (dispatch["status"] not in {"DEFINITE_NO_WRITE", "RECONCILED_ABSENT_SAFE_TO_RETRY"}
                         or dispatch["public_object_id"] or dispatch["public_object_url"]):
            raise ValueError("PLAN_ANALYSIS_COPY_REVISION_READBACK_REQUIRED")
    store.register_outbox_message(message_id=held["page_id"]+"-prior-copy-"+held["plan"]["plan_hash"],
        work_item_id=held["page_id"],destination="internal:plan-analysis-revision",
        payload=canonical_bytes(held).decode(),status="EDITORIAL_INTERNAL")
    plan={**held["plan"],"analysis_copy_revision":sha256_of(packet["native_payload"])}
    plan["destinations"]=[{**d,"payload":packet["native_payload"]["body_markdown"],
        "payload_hash":sha256(packet["native_payload"]["body_markdown"].encode()).hexdigest()} for d in plan["destinations"]]
    plan.pop("plan_hash",None);plan["plan_hash"]=sha256_of(plan)
    revised={**packet,"page_id":held["page_id"],"plan":plan}
    store.finalize_outbox_payload_before_dispatch(message_id=held["page_id"],
        payload=canonical_bytes(revised).decode(),status="EDITORIAL_INTERNAL")
    return revised


def validate_plan(store, work_item_id, plan):
    row = store.get_outbox_message(work_item_id)
    packet = json.loads(row["payload"]) if row else {}
    if packet.get("page_id") != work_item_id or packet.get("plan") != plan:
        raise ValueError("PLAN_ANALYSIS_EXACT_STORED_PAGE_REQUIRED")
    run = load_run(packet["source_plan"], run_root=Path(packet["run_root"]))
    if run["manifest"] != packet["source_manifest"]:
        raise ValueError("PLAN_ANALYSIS_SOURCE_BYTES_CHANGED")
    validate_manuscript(packet["source_plan"], packet["manuscript"], run)
    expected, _, _ = _assemble(packet["source_plan"], packet["manuscript"], run)
    if expected != packet["native_payload"]:
        raise ValueError("PLAN_ANALYSIS_RENDERED_COPY_CHANGED")
    if packet["summary"] != {k: packet["manuscript"]["sections"][k]["summary"] for k, _ in sections_for(packet["manuscript"])}:
        raise ValueError("PLAN_ANALYSIS_SUMMARY_CHANGED")
    for asset in packet.get("media_assets", []):
        if sha256(Path(asset["path"]).read_bytes()).hexdigest() != asset["sha256"]:
            raise ValueError("PLAN_ANALYSIS_MEDIA_BYTES_CHANGED")
        if asset.get("modality") == "tradingview_chart_snapshot":
            from .tradingview_snapshot_v1 import validate_snapshot_asset
            validate_snapshot_asset(asset, {"market_asset": packet["source_plan"]["asset_id"]})
            if asset.get("plan_overlay"):
                from .tradingview_plan_overlay_v1 import validate as validate_overlay
                validate_overlay(asset, {"key": "plan-analysis-" + packet["plan_id"],
                    "symbol": packet["source_plan"]["asset_id"],
                    "levels": posts._display_plan(posts._built_plan(packet["source_plan"]))})
            continue
        if packet["source_plan"].get("zone"):
            candidate, _, _ = _owner_candidate(packet["source_plan"], run)
            expected = {key:{field:candidate["directional_entries"][key].get(field)
                            for field in ("entry_bounds","stop_level","target_level","structure")}
                        for key in ("pullback","breakout")}
            if (asset.get("provenance_status") != "VERIFIED_CAPITAL_CHRONICLE_PLAN_EXPORT"
                    or (asset.get("chart_spec") or {}).get("legs") != expected):
                raise ValueError("PLAN_ANALYSIS_MEDIA_SOURCE_GEOMETRY_CHANGED")
    public_filter(json.dumps(packet["native_payload"], ensure_ascii=False))
    return packet


def validate_intent(store, intent):
    packet = validate_plan(store, intent["work_item_id"], json.loads(store.get_outbox_message(intent["work_item_id"])["payload"])["plan"])
    if (intent.get("native_payload") != packet["native_payload"] or intent.get("plan_hash") != packet["plan"]["plan_hash"]
            or intent.get("media_assets", []) != packet.get("media_assets", [])
            or intent["destination_plan"].get("substack_delivery_mode") != "WEB_ONLY"):
        raise ValueError("PLAN_ANALYSIS_EXACT_WEB_ONLY_INTENT_REQUIRED")
    return packet


def page_status(store, packet):
    from .publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
    ids = Coordinator._ids(packet["page_id"], packet["plan"]["plan_hash"], "substack")
    dispatch = store.get_platform_dispatch(ids["dispatch_id"]) or {}
    reconciliation = next((r for r in store.get_reconciliations_for_work_item(packet["page_id"])
                           if r["reconciliation_id"] == ids["reconciliation_id"]), {})
    confirmed = dispatch.get("status") == "DISPATCH_CONFIRMED" and reconciliation.get("status") == "RECONCILED_CONFIRMED"
    return {"page_id": packet["page_id"], "plan_id": packet["plan_id"], "confirmed": confirmed,
            "canonical_url": dispatch.get("public_object_url") if confirmed else None,
            "dispatch": dict(dispatch), "reconciliation": dict(reconciliation)}


def confirmed_publication(store, plan):
    row = store.get_outbox_message("plan-analysis-" + plan["plan_id"])
    if not row:
        return None
    packet = json.loads(row["payload"])
    status = page_status(store, packet)
    if not status["confirmed"] or packet["registration_hash"] != plan.get("registration_hash"):
        return None
    return {"plan_id": plan["plan_id"], "registration_hash": packet["registration_hash"],
            "canonical_url": status["canonical_url"], "summary": packet["summary"]}


def continue_page(store, packet, *, invocation_id, rollout, command="resume", request_hash=None, response=None,
                  automatic=False):
    from .native_desktop_publication_v1 import live_publication_policy
    from .native_neo_executor_v1 import bind_native_neo_coordinator, NativeNeoInputRequired
    from .llm_operator_control_v1 import assert_llm_operator_execution_enabled
    live_publication_policy(rollout)
    assert_llm_operator_execution_enabled()
    if Path(store.db_path).resolve() != Path(rollout["store_path"]).resolve():
        raise ValueError("PLAN_ANALYSIS_ROLLOUT_STORE_MISMATCH")
    coordinator, executor = bind_native_neo_coordinator(store, operation_id=packet["page_id"],
        output_dir=packet["output_dir"], native_invocation_id=invocation_id, allow_publish=True, automatic=automatic)
    coordinator.allow_prior_confirmed_distribution = True
    coordinator.recovery_scope = {"work_item_id": packet["page_id"], "plan": packet["plan"], "exact_work_item_only": True}
    if command in {"begin", "submit"}:
        request = (executor._get(request_hash, "request") or {}).get("request", {})
        if request.get("work_item_id") not in {packet["page_id"], "native-neo-operation-" + sha256_of(packet["page_id"])}:
            raise ValueError("PLAN_ANALYSIS_TOOL_REQUEST_MISMATCH")
        try:
            return executor.begin(request_hash) if command == "begin" else executor.submit(request_hash, response)
        except NativeNeoInputRequired as pending:
            return {"state":"NATIVE_NEO_TOOL_PENDING","native_tool_request":pending.request}
    try:
        if command == "readback":
            ids = coordinator._ids(packet["page_id"], packet["plan"]["plan_hash"], "substack")
            result = coordinator.readback_existing_dispatch(ids["dispatch_id"])
        else:
            result = coordinator.publish_plan(packet["page_id"], packet["plan"])
    except NativeNeoInputRequired as pending:
        return {"state": "NATIVE_NEO_TOOL_PENDING", "native_tool_request": pending.request}
    return {"publication": result, **page_status(store, packet), "pending_requests": executor.pending()}


def structured_summary(packet, destination, canonical_url, authored_summary=None, *, version=1):
    """Use the bound reader contract; preserve the original seven-section dialect."""
    limits = {"telegram": 4096, "discord": 2000, "threads": 500, "facebook_page": 60000,
              "instagram_business": 2200, "x": 10000, "substack_notes": 10000, "linkedin": 3000}
    limit = limits[destination]
    lead = packet["native_payload"]["title"]
    footer = "Full analysis: " + canonical_url + "\n" + PUBLIC_NOTICE + " " + CONFLICTS_NOTICE
    if authored_summary:
        public_filter(authored_summary)
        if _numbers(authored_summary) - _numbers(packet['native_payload']['body_markdown']):
            raise ValueError('PLAN_ANALYSIS_SOCIAL_NUMBER_UNBOUND')
        text=authored_summary+'\n'+footer
        if len(text)>limit:
            raise ValueError('PLAN_ANALYSIS_SUMMARY_LIMIT:'+destination)
        return text
    if packet["manuscript"].get("reader_contract") == "CC466_V1":
        # The nine-section page has no legacy fundamental/geopolitical fields.
        # Reuse its authored summaries, never invent or cut a sentence to fit.
        summary = packet["summary"]
        force_labels = (("macro", "Macro"), ("priced_in", "Priced in"),
            ("positioning", "Positioning"), ("fear", "Fear"), ("story", "Story"),
            ("technical", "Structure"))
        maximum = 3 if destination in {"x", "threads"} else 5
        lines = [label + ": " + summary[key] for key, label in force_labels if summary.get(key)][:maximum]
        scenarios = ["Scenarios: " + summary["scenarios"]] if summary.get("scenarios") else []
        while True:
            text = "\n".join([lead, *lines, *scenarios, footer])
            if len(text) <= limit:
                public_filter(text)
                return text
            if not lines:
                raise ValueError("PLAN_ANALYSIS_SUMMARY_LIMIT:" + destination)
            lines.pop()
    labels = {"macro":"Macro", "fundamental":"Fundamental", "technical":"Technical", "geopolitical":"Geopolitical",
              "priced_in":"Priced in", "scenarios":"Scenarios", "desk_process":"Desk review"}
    summaries = [labels[k] + ": " + packet["summary"][k] for k, _ in SECTIONS]
    if len(lead + '\n' + '\n'.join(summaries) + '\n' + footer) <= limit:
        lines = summaries
        # Add whole source-bound sentences, in section order, without losing
        # their caveat or manufacturing a compressed causal claim.
        for index, (key, _) in enumerate(SECTIONS) if destination != "x" else []:
            for paragraph in packet["manuscript"]["sections"][key]["paragraphs"]:
                detail = paragraph["text"]
                if version == 1:
                    candidate = labels[key] + ": " + detail
                else:
                    if detail in lines[index]:
                        continue
                    previous = lines[index].removeprefix(labels[key] + ": ")
                    candidate = (labels[key] + ": " + detail if previous in detail
                                 else lines[index] + " " + detail)
                proposed = [*lines[:index], candidate, *lines[index+1:]]
                if len(lead+'\n'+'\n'.join(proposed)+'\n'+footer) <= limit and len(candidate)>len(lines[index]):
                    lines = proposed
    else:
        lead = "Original plan: " + packet["source_plan"]["asset_id"]
        budget = limit - len(lead) - len(footer) - 2
        # Threads has little room after the notice and URL. Section names
        # remain explicit; the full page supplies the detailed qualifications.
        if version == 1:
            lines = [posts._excerpt(line, max(0, (budget-6)//7)) for line in summaries]
            lines = [line for line in lines if line]
        else:
            headings = [labels[key] + ": " for key, _ in SECTIONS]
            available = budget - sum(map(len, headings)) - len(headings) + 1
            lines = [heading + posts._excerpt(packet["summary"][key], max(0, available // len(headings)))
                     for heading, (key, _) in zip(headings, SECTIONS)]
    text = lead+'\n'+'\n'.join(lines)+'\n'+footer
    if len(text)>limit:
        raise ValueError("PLAN_ANALYSIS_SUMMARY_LIMIT:"+destination)
    public_filter(text)
    return text


def _link_payload(packet, destination, text, canonical_url, parent, *, discord_delivery=None,
                  discord_thread_parent_id=None):
    payload = {"destination": destination, "text": text, "full_text": text, "media_asset_ids": []}
    if parent:
        payload.update(reply_to_id=str(parent["public_object_id"]), reply_to_url=parent["public_object_url"])
    if destination in {"facebook_page", "instagram_business"}:
        payload["own_call_comment"] = True
    if destination == "substack_notes":
        # Notes is its own link-card post, not a reply to an unrelated Note.
        payload.update(link_card_url=canonical_url)
    if destination == "x":
        body = text.rsplit("\n" + PUBLIC_NOTICE, 1)[0]
        notices = PUBLIC_NOTICE + " " + CONFLICTS_NOTICE
        chunks = posts._x_pack(body, 280, preserve_lines=True) + [notices]
        if any(posts._x_length(chunk) > 280 for chunk in chunks):
            raise ValueError("PLAN_ANALYSIS_X_COPY_TOO_LONG")
        payload.update(text=chunks[0], root_text=chunks[0], full_text="\n\n".join(chunks),
            reply_texts=chunks[1:], posts=[{"text": part, "order": i,
                "role": "root" if i == 0 else "reply", "media_asset_ids": []} for i, part in enumerate(chunks)])
    if destination == "discord":
        if discord_delivery == "channel":
            payload.pop("reply_to_id", None)
            payload.pop("reply_to_url", None)
            payload["discord_channel_post"] = True
        else:
            payload.update(discord_thread_parent_id=str(discord_thread_parent_id or parent["public_object_id"]),
                           discord_thread_name="Full plan analysis")
    return payload


def _analysis_parent(store, original_key, plan_id, destination):
    from .plan_call_cards_v1 import _reference
    parent = _reference(store, original_key, destination)
    if parent:
        return parent
    identity = "plan-analysis-root-" + plan_id + "-" + destination
    row = store.get_outbox_message(identity)
    if not row:
        return None
    value = json.loads(row["payload"])
    if value.get("original_key") != original_key:
        return None
    from .publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
    ids = Coordinator._ids(identity, value["plan"]["plan_hash"], destination)
    dispatch = store.get_platform_dispatch(ids["dispatch_id"]) or {}
    if dispatch.get("status") == "DISPATCH_CONFIRMED" and dispatch.get("public_object_id"):
        return {k: dispatch.get(k) for k in ("public_object_id", "public_object_url", "dispatch_id")}
    return None


def _discord_analysis_thread(store, original, parent):
    """A bot card already lives in its run thread; Discord has no nested threads."""
    from .plan_call_cards_v1 import _reference
    if original.get("kind") == "setup" and not original.get("parent_key"):
        # CC-466's setup is its own root; run_key remains an internal grouping
        # key and does not identify a public count/summary post.
        return str(parent["public_object_id"])
    run_key = original.get("run_key") or original.get("parent_key")
    if not run_key:
        return str(parent["public_object_id"])
    run = _reference(store, run_key, "discord")
    if not run:
        raise ValueError("PLAN_ANALYSIS_RUN_PARENT_NOT_CONFIRMED")
    return str(run["public_object_id"])


def register_link(store, packet, *, original_key, destination, authored_summary=None,
                  original_analysis_root=False, canonical_image_url=None):
    from .plan_call_cards_v1 import _reference
    from .destination_transport_registry_v1 import REGISTRY_VERSION, registration_for_destination
    status = page_status(store, packet)
    if not status["confirmed"]:
        return {"state":"PLAN_ANALYSIS_CANONICAL_NOT_CONFIRMED", "destination":destination}
    if destination not in {"telegram", "discord", "threads", "facebook_page", "instagram_business", "x", "substack_notes"}:
        raise ValueError("PLAN_ANALYSIS_LINK_DESTINATION_INVALID")
    identity = ("plan-analysis-root-" if original_analysis_root else "plan-analysis-link-")+packet["plan_id"]+'-'+destination
    prior = store.get_outbox_message(identity)
    if prior and not authored_summary:
        return json.loads(prior["payload"])
    parent = None if destination == "substack_notes" else _analysis_parent(store, original_key, packet["plan_id"], destination)
    if original_analysis_root:
        # Decision 113 explicitly asks for today's original plan analysis. An
        # unsent legacy setup is not a new live call: publish a dated analysis
        # root through the same coordinator, then attach the requested reply.
        if destination != "threads" or _reference(store, original_key, destination) or parent:
            raise ValueError("PLAN_ANALYSIS_ORIGINAL_ROOT_NOT_REQUIRED")
        if not authored_summary or "original plan" not in authored_summary.casefold():
            raise ValueError("PLAN_ANALYSIS_DATED_ORIGINAL_COPY_REQUIRED")
        if not canonical_image_url or not canonical_image_url.startswith("https://substack-post-media.s3.amazonaws.com/public/images/"):
            raise ValueError("PLAN_ANALYSIS_CANONICAL_IMAGE_REQUIRED")
    elif not parent and destination != "substack_notes":
        return {"state":"PLAN_ANALYSIS_PARENT_NOT_CONFIRMED", "destination":destination, "original_key":original_key}
    original = store.get_outbox_message(original_key) or {}
    original_payload = json.loads(original.get("payload") or "{}")
    discord_delivery = (original_payload.get("discord_delivery")
                        if destination == "discord" else None)
    if destination == "discord" and original_payload.get("state_alert_contract"):
        # CC-543 requires a reply under the alert, never a second channel root.
        # The existing bot transport names missing credentials locally.
        discord_delivery = "bot_thread"
    thread_parent = (_discord_analysis_thread(store, original_payload, parent)
                     if destination == "discord" and discord_delivery != "channel" else None)
    text = structured_summary(packet, destination, status["canonical_url"],authored_summary, version=2)
    payload = _link_payload(packet, destination, text, status["canonical_url"], parent,
                            discord_delivery=discord_delivery, discord_thread_parent_id=thread_parent)
    if original_analysis_root:
        payload.update(media_asset_ids=[packet["media_assets"][0]["asset_id"]], image_url=canonical_image_url)
    registration = registration_for_destination(destination)
    plan = {"schema_version":"contentops.publication_plan.v1", "plan_analysis_link":identity,
            "story_identity":identity, "article_identity":identity, "package_identity":identity,
            "output_dir":packet["output_dir"], "transport_registry_version":REGISTRY_VERSION,
            "policy_mode_version":"AUTONOMOUS_DEFAULT:JIM_DECISION_113", "publication_window":{"window_identity":identity},
            "destinations":[{"destination":destination, "surface":registration.surface, "transport_type":registration.transport_type,
                "payload":payload["full_text"], "payload_hash":sha256(payload["full_text"].encode()).hexdigest(), "canonical_url":status["canonical_url"]}]}
    plan["plan_hash"] = sha256_of(plan)
    value={"link_id":identity, "page_id":packet["page_id"], "plan_id":packet["plan_id"], "original_key":original_key,
           "parent":parent, "destination":destination, "native_payload":payload, "plan":plan, "canonical_url":status["canonical_url"],
           "original_analysis_root":original_analysis_root, "summary_version": 2,
           **({"discord_delivery": discord_delivery} if discord_delivery else {}),
           **({"discord_thread_parent_id": thread_parent} if thread_parent else {}),
           **({'authored_summary':authored_summary} if authored_summary else {})}
    store.create_work_item(story_id=identity,work_item_id=identity,title="Full plan analysis link",target_surface="MULTI_PLATFORM")
    if prior:
        store.finalize_outbox_payload_before_dispatch(message_id=identity,payload=canonical_bytes(value).decode(),status="EDITORIAL_INTERNAL")
    else:
        store.register_outbox_message(message_id=identity,work_item_id=identity,destination=DESTINATION,
                                     payload=canonical_bytes(value).decode(),status="EDITORIAL_INTERNAL")
    return value


def validate_link_plan(store, work_item_id, plan):
    from .plan_call_cards_v1 import _reference
    row=store.get_outbox_message(work_item_id)
    value=json.loads(row["payload"]) if row else {}
    if value.get("link_id")!=work_item_id or value.get("plan")!=plan:
        raise ValueError("PLAN_ANALYSIS_EXACT_LINK_REQUIRED")
    if value.get("kind") == "run":
        return _validate_run_link(store, value)
    packet=json.loads(store.get_outbox_message(value["page_id"])["payload"])
    validate_plan(store,packet["page_id"],packet["plan"])
    if page_status(store,packet)["canonical_url"]!=value["canonical_url"]:
        raise ValueError("PLAN_ANALYSIS_LINK_CANONICAL_CHANGED")
    if value.get("original_analysis_root"):
        if (value["destination"] != "threads" or value.get("parent")
                or _reference(store,value["original_key"],value["destination"])
                or "original plan" not in value.get("authored_summary", "").casefold()):
            raise ValueError("PLAN_ANALYSIS_ORIGINAL_ROOT_CHANGED")
        # The public image must be the exact image observed on the confirmed
        # canonical. A caller cannot substitute a third-party image URL.
        image=value["native_payload"].get("image_url")
        observed=False
        if value["native_payload"].get("media_asset_ids") != [packet["media_assets"][0]["asset_id"]]:
            raise ValueError("PLAN_ANALYSIS_ORIGINAL_ROOT_MEDIA_CHANGED")
        for row in store.list_outbox_messages(work_item_id=packet["page_id"], destination="internal:native-neo-tool"):
            read=json.loads(row["payload"]).get("result",{})
            if (read.get("status")=="SUCCESS" and read.get("public_object_url")==value["canonical_url"]
                    and image in read.get("public_image_urls",[])
                    and packet["media_assets"][0]["sha256"] in read.get("observed_media_sha256",[])
                    and read.get("native_tool_observation")):
                observed=True
        if not observed:
            raise ValueError("PLAN_ANALYSIS_CANONICAL_IMAGE_NOT_OBSERVED")
    elif value["destination"] == "substack_notes":
        if value.get("parent") or value["native_payload"].get("link_card_url") != value["canonical_url"]:
            raise ValueError("PLAN_ANALYSIS_NOTE_LINK_CARD_CHANGED")
    else:
        parent=_analysis_parent(store,value["original_key"],value["plan_id"],value["destination"])
        if not parent or parent!=value["parent"]:
            raise ValueError("PLAN_ANALYSIS_LINK_PARENT_CHANGED")
    expected=structured_summary(packet,value["destination"],value["canonical_url"],value.get('authored_summary'),
                                version=value.get("summary_version", 1))
    thread_parent = value.get("discord_thread_parent_id")
    if thread_parent:
        original = json.loads(store.get_outbox_message(value["original_key"])["payload"])
        if (value["destination"] != "discord" or value.get("discord_delivery") == "channel"
                or thread_parent != _discord_analysis_thread(store, original, value["parent"])):
            raise ValueError("PLAN_ANALYSIS_DISCORD_THREAD_CHANGED")
    expected_payload = _link_payload(packet, value["destination"], expected, value["canonical_url"], value.get("parent"),
                                     discord_delivery=value.get("discord_delivery"), discord_thread_parent_id=thread_parent)
    if value.get("original_analysis_root"):
        expected_payload.update(media_asset_ids=[packet["media_assets"][0]["asset_id"]],
                                image_url=value["native_payload"]["image_url"])
    if value["native_payload"] != expected_payload:
        raise ValueError("PLAN_ANALYSIS_LINK_COPY_CHANGED")
    return value


def validate_link_intent(store, intent):
    value=json.loads(store.get_outbox_message(intent["work_item_id"])["payload"])
    value=validate_link_plan(store,intent["work_item_id"],value["plan"])
    if intent.get("native_payload")!=value["native_payload"] or intent.get("canonical_url")!=value["canonical_url"]:
        raise ValueError("PLAN_ANALYSIS_LINK_INTENT_CHANGED")
    return value


def continue_link(store, value, *, invocation_id="plan-analysis-links-cc435", command="resume",
                  request_hash=None, response=None, automatic_neo=False):
    from .native_neo_executor_v1 import bind_native_neo_coordinator, NativeNeoInputRequired
    coordinator, executor = bind_native_neo_coordinator(store, operation_id=value["link_id"],
        output_dir=Path(value["plan"]["output_dir"]) / value["link_id"] / "native-neo",
        native_invocation_id=invocation_id, allow_publish=True,
        automatic=automatic_neo and command in {"resume", "readback"})
    coordinator.allow_prior_confirmed_distribution=True
    coordinator.recovery_scope={"work_item_id":value["link_id"],"plan":value["plan"],"exact_work_item_only":True}
    try:
        if command in {"begin", "submit"}:
            packet = executor._get(request_hash, "request") or {}
            if packet.get("operation_id") != value["link_id"]:
                raise ValueError("PLAN_ANALYSIS_LINK_TOOL_REQUEST_MISMATCH")
            if command == "begin":
                return executor.begin(request_hash)
            submitted = executor.submit(request_hash, response)
            observed = response.get("result") or {}
            if (packet["request"]["action"] == "PUBLISH" and observed.get("status") == "SUCCESS"
                    and observed.get("public_object_id") and observed.get("public_object_url")):
                submitted["completed_write_reconciliation"] = coordinator.reconcile_completed_native_publish(
                    packet["request"]["dispatch_attempt_identity"], request_hash=request_hash)
            return submitted
        if command == "readback":
            ids = coordinator._ids(value["link_id"], value["plan"]["plan_hash"], value["destination"])
            result = coordinator.readback_existing_dispatch(ids["dispatch_id"])
        elif command == "repair-embed":
            result = repair_discord_empty_embed(coordinator, value, response or {})
        else:
            result = coordinator.publish_plan(value["link_id"], value["plan"])
        return {**result, "pending_requests": executor.pending()}
    except NativeNeoInputRequired as pending:
        return {"state": "NATIVE_NEO_TOOL_PENDING", "native_tool_request": pending.request}


def repair_discord_empty_embed(coordinator, value, evidence):
    """Complete the exact reply rejected by Discord's empty-embed validation.

    Retain its original bytes and failure. A fresh thread read must prove absence;
    an HTTP rejection is not a platform outage or an ambiguous public creation.
    The existing correction audit allows one send for this measured repair.
    """
    store = coordinator.store
    validate_link_plan(store, value["link_id"], value["plan"])
    if value["destination"] != "discord":
        raise ValueError("DISCORD_ANALYSIS_LINK_REQUIRED")
    ids = coordinator._ids(value["link_id"], value["plan"]["plan_hash"], "discord")
    correction = "cc432-discord-empty-embed-v1"
    if coordinator._transport_correction_already_attempted(ids["dispatch_id"], correction):
        return {"status": "CORRECTION_ALREADY_ATTEMPTED_READBACK_ONLY", "publish_called": False}
    message = store.get_outbox_message(ids["message_id"])
    dispatch = store.get_platform_dispatch(ids["dispatch_id"]) or {}
    if not message or dispatch.get("public_object_id") or dispatch.get("public_object_url"):
        return {"status": "EXISTING_DISCORD_OBJECT_READBACK_ONLY", "publish_called": False}
    intent = json.loads(message["payload"])
    validate_link_intent(store, intent)
    if coordinator._message_is_stale(message, intent):
        return {"status": "DERIVATIVE_EXPIRED_STALE_NO_WRITE", "publish_called": False}
    incident_id, _, failure = coordinator._destination_failure_cursor("discord")
    provider = evidence.get("error_response") or {}
    errors = ((provider.get("errors") or {}).get("embeds") or {}).get("0", {})
    errors = (errors.get("description") or {}).get("_errors", [])
    started = posts._utc(failure["attempt_started_at_utc"]) if failure else None
    observed = posts._utc(evidence["timestamp"]) if evidence.get("timestamp") else None
    if (not failure or failure.get("dispatch_id") != ids["dispatch_id"]
            or evidence.get("platform_id") != "discord" or evidence.get("action") != "post"
            or evidence.get("http_status") != 400 or provider.get("code") != 50035
            or not any(e.get("code") == "BASE_TYPE_REQUIRED" for e in errors)
            or not started or not observed or not 0 <= (observed - started).total_seconds() <= 30
            or intent.get("media_assets") or value["native_payload"].get("media_asset_ids")):
        raise ValueError("EXACT_DISCORD_EMPTY_EMBED_REJECTION_REQUIRED")
    readback = coordinator.readback_existing_dispatch(ids["dispatch_id"])
    if readback.get("reconciliation_status") != "RECONCILED_ABSENT_SAFE_TO_RETRY":
        return {**readback, "publish_called": False}
    # Resolve only this measured malformed request, preserving CC-401 for actual
    # provider restrictions, outages, credentials and later ambiguous attempts.
    store.register_incident(incident_id=incident_id + "_local_prewrite_resolved",
        work_item_id=value["link_id"], severity="RESOLVED_LOCAL_REQUEST_VALIDATION",
        description=json.dumps({"cause": "DISCORD_EMPTY_EMBED_CORRECTED", "dispatch_id": ids["dispatch_id"],
            "http_status": 400, "provider_code": 50035, "event_id": evidence.get("event_id"),
            "provider_rejected_creation": True, "fresh_absence_confirmed": True}))
    outcome = coordinator._dispatch_message(message, canonical_url=value["canonical_url"],
        explicit_reconciled_absent_retry=True)
    if outcome.get("publish_called") is True:
        coordinator._record_transport_correction_attempt(ids["dispatch_id"], correction, value["link_id"])
    return {**outcome, "correction_id": correction}


def publish_link(store, value, *, automatic_neo=False):
    return continue_link(store, value, automatic_neo=automatic_neo)


def link_status(store, value):
    from .publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
    ids = Coordinator._ids(value["link_id"], value["plan"]["plan_hash"], value["destination"])
    dispatch = store.get_platform_dispatch(ids["dispatch_id"]) or {}
    message = store.get_outbox_message(ids["message_id"]) or {}
    reconciliation = next((r for r in store.get_reconciliations_for_work_item(value["link_id"])
                           if r["reconciliation_id"] == ids["reconciliation_id"]), {})
    return {"confirmed": dispatch.get("status") == "DISPATCH_CONFIRMED"
                        and reconciliation.get("status") == "RECONCILED_CONFIRMED",
            "status": dispatch.get("status") or message.get("status"), "public_object_id": dispatch.get("public_object_id"),
            "public_object_url": dispatch.get("public_object_url")}


def settle_late_link(store, value, *, now=None):
    """End a late link's automatic work, preserving its exact dispatch/readback."""
    from .plan_call_cards_v1 import SETTLED_POST, SETTLED_COPY, SETTLED_DISPATCHES, _settlement_id
    from .publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
    source = store.get_outbox_message(value["link_id"])
    if not source:
        return None
    cause = "PLAN_ANALYSIS_LINK_OLDER_THAN_24_HOURS"
    status = link_status(store, value)
    if source["status"] == SETTLED_POST:
        return {"status": SETTLED_POST, "cause": cause, "dispatch_status": status["status"]}
    if status["confirmed"] or status["status"] in SETTLED_DISPATCHES:
        return None
    original = store.get_outbox_message(value.get("original_key", ""))
    original_payload = json.loads(original["payload"]) if original else {}
    at = original_payload.get("at_utc") or source["created_at"]
    now = now or datetime.now(timezone.utc)
    if (now - posts._utc(at)).total_seconds() <= posts.LATE_STATE_HOURS * 3600:
        return None
    ids = Coordinator._ids(value["link_id"], value["plan"]["plan_hash"], value["destination"])
    detail = {"key": value["link_id"], "destination": value["destination"], "cause": cause,
        "source_at_utc": at, "dispatch_id": ids["dispatch_id"], "dispatch_status": status["status"],
        "public_object_id": status.get("public_object_id"), "public_object_url": status.get("public_object_url"),
        "automatic_work_closed": True, "public_write_performed": False}
    store.register_incident(incident_id=_settlement_id(value["link_id"], value["destination"]),
        work_item_id=value["link_id"], severity="RECOVERY_AUDIT", description=json.dumps(detail, sort_keys=True))
    if store.get_outbox_message(ids["message_id"]):
        store.set_outbox_status(ids["message_id"], SETTLED_COPY)
    store.set_outbox_status(value["link_id"], SETTLED_POST)
    return {"status": SETTLED_POST, "cause": cause, "dispatch_status": status["status"]}


def _resume_link(store, value, publish, *, automatic_neo=False):
    if not value.get("link_id"):
        return value
    status = link_status(store, value)
    from .plan_call_cards_v1 import SETTLED_DISPATCHES
    if status["confirmed"] or status["status"] in SETTLED_DISPATCHES or not publish:
        return status
    settled = settle_late_link(store, value)
    if settled:
        return settled
    return publish_link(store, value, **({"automatic_neo": True} if automatic_neo else {}))


def _run_link_text(packets, urls):
    from .plan_call_cards_v1 import _run_summary
    analyses = [{"title": p["native_payload"]["title"], "canonical_url": url, "summary": p["summary"]}
                for p, url in zip(packets, urls)]
    notice = PUBLIC_NOTICE + " " + CONFLICTS_NOTICE
    text = _run_summary({"analysis_publications": analyses}, "The original run: full plan analyses",
                        3000 - len(notice) - 2) + "\n\n" + notice
    public_filter(text)
    return text


def register_run_link(store, packets):
    """One official LinkedIn member run post containing every available page."""
    from .destination_transport_registry_v1 import REGISTRY_VERSION, registration_for_destination
    packets = sorted(packets, key=lambda p: p["plan_id"])
    run_ids = {p["source_plan"]["run_id"] for p in packets}
    if not packets or len(run_ids) != 1:
        raise ValueError("PLAN_ANALYSIS_RUN_BINDING_REQUIRED")
    statuses = [page_status(store, p) for p in packets]
    if not all(s["confirmed"] for s in statuses):
        return {"state": "PLAN_ANALYSIS_CANONICAL_NOT_CONFIRMED", "destination": "linkedin"}
    urls = [s["canonical_url"] for s in statuses]
    identity = "plan-analysis-run-" + sha256_of({"run_id": next(iter(run_ids)), "pages": urls})[:32] + "-linkedin"
    prior = store.get_outbox_message(identity)
    if prior:
        return json.loads(prior["payload"])
    text = _run_link_text(packets, urls)
    registration = registration_for_destination("linkedin")
    plan = {"schema_version": "contentops.publication_plan.v1", "plan_analysis_link": identity,
        "story_identity": identity, "article_identity": identity, "package_identity": identity,
        "output_dir": packets[0]["output_dir"], "transport_registry_version": REGISTRY_VERSION,
        "policy_mode_version": "AUTONOMOUS_DEFAULT:CC435", "publication_window": {"window_identity": identity},
        "destinations": [{"destination": "linkedin", "surface": registration.surface,
            "transport_type": registration.transport_type, "payload": text,
            "payload_hash": sha256(text.encode()).hexdigest(), "canonical_url": urls[0]}]}
    plan["plan_hash"] = sha256_of(plan)
    value = {"link_id": identity, "kind": "run", "run_id": next(iter(run_ids)), "destination": "linkedin",
        "page_ids": [p["page_id"] for p in packets], "canonical_urls": urls, "canonical_url": urls[0],
        "native_payload": {"destination": "linkedin", "text": text, "full_text": text, "media_asset_ids": []}, "plan": plan}
    store.create_work_item(story_id=identity, work_item_id=identity, title="Full run analyses", target_surface="MULTI_PLATFORM")
    store.register_outbox_message(message_id=identity, work_item_id=identity, destination=DESTINATION,
        payload=canonical_bytes(value).decode(), status="EDITORIAL_INTERNAL")
    return value


def _validate_run_link(store, value):
    packets = []
    for page_id in value["page_ids"]:
        packet = json.loads(store.get_outbox_message(page_id)["payload"])
        validate_plan(store, page_id, packet["plan"])
        packets.append(packet)
    if value["destination"] != "linkedin" or any(p["source_plan"]["run_id"] != value["run_id"] for p in packets):
        raise ValueError("PLAN_ANALYSIS_RUN_BINDING_CHANGED")
    urls = [page_status(store, p)["canonical_url"] for p in packets]
    if urls != value["canonical_urls"] or value["canonical_url"] != urls[0]:
        raise ValueError("PLAN_ANALYSIS_RUN_CANONICAL_CHANGED")
    expected = {"destination": "linkedin", "text": _run_link_text(packets, urls),
                "full_text": _run_link_text(packets, urls), "media_asset_ids": []}
    if value["native_payload"] != expected or value["plan"]["destinations"][0]["payload"] != expected["text"]:
        raise ValueError("PLAN_ANALYSIS_RUN_COPY_CHANGED")
    return value


def distribute_links(store, *, limit=None, publish=True, automatic_neo=False):
    """The installed status-post run consumes confirmed pages in its own store.

    Frozen links are resumed, not rewritten. A later page in the same Main run
    creates one new complete index snapshot, rather than editing a sent object.
    """
    cards, confirmed_runs = {}, []
    from .plan_call_cards_v1 import _reference
    for row in store.list_outbox_messages(destination=posts.DESTINATION):
        item = json.loads(row["payload"])
        if item.get("kind") == "setup" or item.get("state") == "WAITING":
            cards.setdefault(item.get("plan_id"), row["message_id"])
        if item.get("kind") == "run" and _reference(store, row["message_id"], "linkedin"):
            confirmed_runs.append({a["canonical_url"] for a in item.get("analysis_publications", [])})
    pages, runs, results = [], {}, []
    for row in store.list_outbox_messages(destination=DESTINATION):
        packet = json.loads(row["payload"])
        if row["message_id"] == packet.get("page_id") and page_status(store, packet)["confirmed"]:
            pages.append(packet)
    for packet in pages if limit is None else pages[-limit:]:
        original = cards.get(packet["plan_id"], packet["page_id"])
        for destination in ("telegram", "discord", "threads", "facebook_page", "instagram_business", "x", "substack_notes"):
            try:
                value = register_link(store, packet, original_key=original, destination=destination)
                outcome = _resume_link(store, value, publish, automatic_neo=automatic_neo)
                results.append({"page_id": packet["page_id"], "destination": destination,
                                "link_id": value.get("link_id"), "outcome": outcome})
            except (OSError, ValueError, KeyError, TypeError) as exc:
                results.append({"page_id": packet["page_id"], "destination": destination,
                                "state": "NOT_STARTED", "cause": str(exc)[:200]})
        runs.setdefault(packet["source_plan"]["run_id"], []).append(packet)
    for packets in runs.values():
        try:
            urls = {page_status(store, p)["canonical_url"] for p in packets}
            if any(urls <= confirmed for confirmed in confirmed_runs):
                results.append({"destination": "linkedin", "state": "CONFIRMED_IN_RUN_POST"})
                continue
            value = register_run_link(store, packets)
            outcome = _resume_link(store, value, publish, automatic_neo=automatic_neo)
            results.append({"destination": "linkedin", "link_id": value.get("link_id"), "outcome": outcome})
        except (OSError, ValueError, KeyError, TypeError) as exc:
            results.append({"destination": "linkedin", "state": "NOT_STARTED", "cause": str(exc)[:200]})
    return {"status": "OK", "links": results}


def resume_discord_links(store, *, latest_states, now, limit=5, coordinator_for=None):
    """CC-437: the existing minute consumer also drains registered Discord links.

    Do not change a registered copy or its thread binding. Retire an unattempted
    link after its plan ends; uncertain/identified attempts keep exact recovery.
    """
    from .publication_coordinator_v1 import DurablePublicationCoordinator, CanonicalDestinationTransportRuntimeV1
    from . import plan_status_posts_v1 as posts
    results = []
    candidates = []
    for message in store.list_outbox_messages(destination="discord"):
        if message["status"] != "READY":
            continue
        intent = json.loads(message["payload"])
        key = intent.get("plan_analysis_link")
        if key:
            candidates.append((message, key))
    for message, key in candidates[:limit]:
        try:
            value = json.loads(store.get_outbox_message(key)["payload"])
            plan = value["plan"]
            if coordinator_for is None:
                coordinator = DurablePublicationCoordinator(store=store,
                    transport_runtime=CanonicalDestinationTransportRuntimeV1())
            else:
                coordinator = coordinator_for(key, Path(plan["output_dir"]))
            posts.scope_to_post(coordinator, key, plan)
            ids = coordinator._ids(key, plan["plan_hash"], "discord")
            dispatch = store.get_platform_dispatch(ids["dispatch_id"])
            state = latest_states.get(value["plan_id"])
            original = posts._row_payload(store, value["original_key"])
            until = original.get("time_exit_utc") or (original.get("levels") or {}).get("valid_until_utc")
            ended = state in {"CANCELLED", "INVALIDATED", "EXPIRED", "VIEW_CHANGED", "RESULT"}
            expired = bool(until and now >= posts._utc(until))
            if not dispatch and (ended or expired):
                coordinator._expire_stale_derivative(message, None)
                results.append({"key": key, "status": "DERIVATIVE_EXPIRED_STALE_NO_WRITE",
                    "cause": "PLAN_ALREADY_" + str(state) if ended else "PLAN_VALIDITY_ENDED",
                    "per_destination": {"discord": "DERIVATIVE_EXPIRED_STALE_NO_WRITE"}})
                continue
            if not dispatch and state not in posts.ACTIVE:
                results.append({"key": key, "status": "WAITING", "cause": "CURRENT_PLAN_STATE_NOT_IN_EXPORT"})
                continue
            outcome = coordinator.execute_plan(key, plan)
            per = outcome.get("per_destination") or {}
            state = (per.get("discord") or {}).get("status", "NOT_STARTED")
            results.append({"key": key, "status": state,
                "per_destination": {"discord": state}, "destination_causes": posts.destination_causes(outcome)})
        except (OSError, ValueError, KeyError, TypeError) as exc:
            results.append({"key": key, "status": "NOT_STARTED", "cause": str(exc)[:200]})
    for _, key in candidates[limit:]:
        results.append({"key": key, "status": "WAITING", "cause": "ANALYSIS_LINK_WORK_LIMIT_THIS_RUN"})
    return results
