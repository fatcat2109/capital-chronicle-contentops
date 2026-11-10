"""Decision 113: source-bound plan pages, through the existing publication owner.

Main's sealed run is read, never changed. A native writer supplies structured
public paragraphs. Code verifies their numbers, rights and exact plan binding,
then renders them; it does not invent an explanation or a missing scenario.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
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
RIGHTS = {"CAPITAL_CHRONICLE_ORIGINAL_ANALYSIS", "PUBLIC_DOMAIN_OFFICIAL_FACT", "SINGLE_ATTRIBUTED_FACT"}
_PRIVATE = re.compile(
    r"\b(?:demo|mt[45]|exness[\w-]*|metatrader|account\s+(?:id|number|balance|equity)|"
    r"position\s+siz(?:e|ing)|risk\s+(?:allocation|per trade)|(?:our|my)\s+(?:balance|equity|capital)|"
    r"ticket(?:\s+id)?|p\s*&\s*l|realised profit|realized profit|lot\s+size|HALF_PLAN_RISK)\b|"
    r"\b\d+(?:\.\d+)?\s*(?:standard\s+|mini\s+|micro\s+)?lots?\b|"
    r"\b(?:279805139|279779602)\b", re.I)
_MONEY = re.compile(r"\b(?:balance|equity|capital|allocation|size|sizing|risk budget|profit|loss)\b.{0,35}"
                    r"(?:[$€£]\s*\d|\d[\d,.]*\s*(?:USD|EUR|dollars|lots|%))", re.I)
_MODELS = re.compile(r"\b(?:GPT(?:[- .]?\d[\w.-]*)?|ChatGPT|Claude|Opus|Gemini|Luna|Sol\s*6|Antigravity|"
                     r"AI[- ](?:run|native|powered|driven)|(?:run|written|generated|operated)\s+by\s+AI)\b", re.I)
_X = re.compile(r"(?:https?://(?:www\.)?(?:x|twitter)\.com/|JIM_X_LIST|PRIVATE_X_LIST|X[-_ ]list)", re.I)
_SECRET = re.compile(r"(?:sk-[A-Za-z0-9]{16,}|access[_ -]?token\s*[:=]|api[_ -]?key\s*[:=]|password\s*[:=])", re.I)
_NUM = re.compile(r"(?<![\w.])[+−-]?\d+(?:,\d{3})*(?:\.\d+)?%?(?![\w.])")


def _numbers(text):
    # A sign and a percentage are material. A scalar probability of 55 can
    # support '55%' but never a made-up complement or a changed magnitude.
    return {str(Decimal(m.group().replace(',', '').replace('−', '-').rstrip('%')))
            for m in _NUM.finditer(str(text))}


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
    names = ["role-pack.json", "role-evidence.json", "critic-note.json", "integrated-owner-record.json",
             "plan-geometry.json", "options-context.json", "final-decision-freeze.json", "desktop-manual-result.json"]
    names += (["analysis-native.json"] if (folder / "analysis-native.json").is_file()
              else ["primary-native.json", "critical-native.json", "owner-native.json"])
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
    return {"folder": folder, "documents": documents, "manifest": manifest, "freeze": freeze}


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
    from .preview_link_guard_v1 import find_forbidden_link
    if find_forbidden_link(text):
        raise ValueError("PREVIEW_HOST_LINK_FORBIDDEN")
    require_public_time(text)
    return {"status": "PASS", "sha256": sha256(text.encode()).hexdigest()}


def _source_text(run, ref):
    name, pointer = ref["file"], ref["pointer"]
    if name not in run["documents"]:
        raise ValueError("PLAN_ANALYSIS_SOURCE_FILE_NOT_BOUND")
    # Raw accounts, execution packets and bulk vendor series are never public
    # sources. Main's original analytical prose and official single facts are.
    if re.search(r"(?:account|portfolio_state|cost_inputs|cost_summary|execution|risk_allocation)", pointer, re.I):
        raise ValueError("PLAN_ANALYSIS_PRIVATE_SOURCE_POINTER")
    value = _pointer(run["documents"][name], pointer)
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        raise ValueError("PLAN_ANALYSIS_SCALAR_SOURCE_REQUIRED")
    if ref.get("transform") == "ET":
        return public_timestamp(value)
    if ref.get("transform"):
        raise ValueError("PLAN_ANALYSIS_SOURCE_TRANSFORM_INVALID")
    return str(value)


def validate_manuscript(plan, manuscript, run):
    if (manuscript.get("plan_id") != plan["plan_id"]
            or manuscript.get("registration_hash") != plan["registration_hash"]):
        raise ValueError("PLAN_ANALYSIS_EXACT_PLAN_REQUIRED")
    if set(manuscript.get("sections", {})) != {key for key, _ in SECTIONS}:
        raise ValueError("PLAN_ANALYSIS_ALL_SEVEN_SECTIONS_REQUIRED")
    bound = []
    for key, _ in SECTIONS:
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
                          private_texts=manuscript.get("private_x_texts", []))
            source = "\n".join(_source_text(run, ref) for ref in refs)
            if _numbers(text) - _numbers(source):
                raise ValueError("PLAN_ANALYSIS_UNBOUND_NUMBER:" + key + ":" + str(index))
            bound.append({"section": key, "paragraph": index, "public_sha256": sha256(text.encode()).hexdigest(),
                          "numbers": sorted(_numbers(text)), "refs": refs})
        public_filter(section["summary"])
        if _numbers(section["summary"]) - _numbers(" ".join(p["text"] for p in section["paragraphs"])):
            raise ValueError("PLAN_ANALYSIS_UNBOUND_SUMMARY_NUMBER:" + key)
    for field in ("title", "subtitle", "introduction"):
        public_filter(manuscript[field])
        if _numbers(manuscript[field]) - _numbers(" ".join(p["text"] for s in manuscript["sections"].values() for p in s["paragraphs"])):
            raise ValueError("PLAN_ANALYSIS_UNBOUND_HEADING_NUMBER")
    return bound


def render(plan, manuscript, *, output_dir, run_root=RUN_ROOT):
    run = load_run(plan, run_root=run_root)
    bindings = validate_manuscript(plan, manuscript, run)
    freeze = run["freeze"]
    timestamp = public_timestamp(freeze["frozen_at_utc"])
    audit = f"The view was fixed at {timestamp}. Analysis fingerprint: {freeze['immutable_hash']}."
    paragraphs = [manuscript["introduction"]]
    for key, title in SECTIONS:
        paragraphs += ["## " + title, *[p["text"] for p in manuscript["sections"][key]["paragraphs"]]]
    paragraphs += [audit, PUBLIC_NOTICE, CONFLICTS_NOTICE]
    body = "\n\n".join(paragraphs)
    public_filter(body)
    payload = {"title": manuscript["title"], "subtitle": manuscript["subtitle"], "body_markdown": body}
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "article.md").write_text("# " + payload["title"] + "\n\n" + body, encoding="utf-8")
    html = '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
    html += '<style>body{font:18px/1.65 Georgia,serif;max-width:760px;margin:36px auto;padding:0 22px;color:#18252b}h1{line-height:1.2}h2{font:600 24px/1.3 system-ui;margin-top:2em}p{overflow-wrap:anywhere}</style>'
    html += '<h1>' + escape(payload['title']) + '</h1><p>' + escape(payload['subtitle']) + '</p>'
    html += ''.join('<h2>' + escape(p[3:]) + '</h2>' if p.startswith('## ') else '<p>' + escape(p) + '</p>' for p in paragraphs)
    (folder / "article.html").write_text(html, encoding="utf-8")
    packet = {"schema_version": "contentops.plan_analysis_page.v1", "plan_id": plan["plan_id"],
              "registration_hash": plan["registration_hash"], "run_id": plan["run_id"],
              "analysis_result_hash": plan["analysis_result_hash"], "native_payload": payload,
              "summary": {k: manuscript["sections"][k]["summary"] for k, _ in SECTIONS},
              "source_manifest": run["manifest"], "numeric_bindings": bindings,
              "freeze": {k: freeze[k] for k in ("frozen_at_utc", "immutable_hash")},
              "authorship": manuscript.get("authorship", {}), "manuscript": manuscript, "run_root": str(Path(run_root)),
              "source_plan": plan, "media_assets": [], "output_dir": str(folder.resolve())}
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
        return held
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


def validate_plan(store, work_item_id, plan):
    row = store.get_outbox_message(work_item_id)
    packet = json.loads(row["payload"]) if row else {}
    if packet.get("page_id") != work_item_id or packet.get("plan") != plan:
        raise ValueError("PLAN_ANALYSIS_EXACT_STORED_PAGE_REQUIRED")
    run = load_run(packet["source_plan"], run_root=Path(packet["run_root"]))
    if run["manifest"] != packet["source_manifest"]:
        raise ValueError("PLAN_ANALYSIS_SOURCE_BYTES_CHANGED")
    validate_manuscript(packet["source_plan"], packet["manuscript"], run)
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


def continue_page(store, packet, *, invocation_id, rollout, command="resume", request_hash=None, response=None):
    from .native_desktop_publication_v1 import live_publication_policy
    from .native_neo_executor_v1 import bind_native_neo_coordinator, NativeNeoInputRequired
    from .llm_operator_control_v1 import assert_llm_operator_execution_enabled
    live_publication_policy(rollout)
    assert_llm_operator_execution_enabled()
    if Path(store.db_path).resolve() != Path(rollout["store_path"]).resolve():
        raise ValueError("PLAN_ANALYSIS_ROLLOUT_STORE_MISMATCH")
    coordinator, executor = bind_native_neo_coordinator(store, operation_id=packet["page_id"],
        output_dir=packet["output_dir"], native_invocation_id=invocation_id, allow_publish=True)
    coordinator.allow_prior_confirmed_distribution = True
    coordinator.recovery_scope = {"work_item_id": packet["page_id"], "plan": packet["plan"], "exact_work_item_only": True}
    if command in {"begin", "submit"}:
        request = (executor._get(request_hash, "request") or {}).get("request", {})
        if request.get("work_item_id") not in {packet["page_id"], "native-neo-operation-" + sha256_of(packet["page_id"])}:
            raise ValueError("PLAN_ANALYSIS_TOOL_REQUEST_MISMATCH")
        return executor.begin(request_hash) if command == "begin" else executor.submit(request_hash, response)
    try:
        result = coordinator.publish_plan(packet["page_id"], packet["plan"])
    except NativeNeoInputRequired as pending:
        return {"state": "NATIVE_NEO_TOOL_PENDING", "native_tool_request": pending.request}
    return {"publication": result, **page_status(store, packet), "pending_requests": executor.pending()}
