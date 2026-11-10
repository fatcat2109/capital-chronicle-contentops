"""CC-406: a native-written morning note, consumed by the installed CC-418 desk.

The existing editorial outbox owns requests and returns. Files are the desk's
product input, not a publisher, schedule or second coordination store.
"""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from uuid import uuid4
from zoneinfo import ZoneInfo

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.main_report_projection_source_v1 import NATIVE_MAIN_REPORT_ROOT, verify_projection
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DesktopInputRequired
from live_contentops.reader_article_contract_v1 import numbers
from tools.product.desk_record_projection_v1 import public_text_problems

ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\gold-notes")
LOCAL = ZoneInfo("Asia/Bangkok")
ET = ZoneInfo("America/New_York")
FIRST_MORNING = date(2026, 11, 13)
NOTICE = "Bản tin chỉ đưa ra phân tích thuần túy, không tư vấn tài chính hay khuyến nghị."
SCHEMA = "contentops.vietnamese_gold_note.v1"
MARKETS = {
    "XAUUSD": ("gold", "xauusd"), "US500": ("spx", "us500"),
    "EURUSD": ("eurusd",), "USDJPY": ("usdjpy",),
    "USOIL": ("wti", "usoil"), "BTCUSD": ("btcusd", "bitcoin"),
}
PROMPT = """CC-406. Write a short Vietnamese general-analysis gold note for Jim's
own community. This is separate from the Capital Chronicle brand: do not name the
brand. Read the Main gold view AND all six market rows. They are dated analysis,
not independently verified current prices. Use only the supplied official facts
for factual numbers; name their official publisher naturally. Explain the gold
mechanism, one countercase and the evidence that would change the view. No personal
advice, entry instructions, account facts, targets or invented probabilities.
At most 150 whitespace-separated words INCLUDING the title and exact final notice.
Use Vietnamese decimal points exactly as supplied. If a public time is useful,
convert it to ET. Keep internal ids, source markers and workflow labels out of copy.
The separate PNG charts the supplied official observations, with source/period/unit.
Return JSON {"text": "...", "fact_ids": ["..."]}; list every fact used. The exact
last line is: """ + NOTICE


def utc(value):
    stamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("GOLD_NOTE_EXPLICIT_CLOCK_REQUIRED")
    return stamp.astimezone(timezone.utc)


def _json(path):
    return json.loads(Path(path).read_bytes())


def _atomic(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    temporary.write_bytes(raw)
    os.replace(temporary, path)


def _latest_report(root, now):
    """Order by the original capture, never by a refreshed file's mtime."""
    reports = []
    for path in Path(root).glob("*/owner-native.json"):
        capture = path.with_name("capture.json")
        if path.stat().st_size > 1_000_000 or not capture.is_file():
            continue
        try:
            clock = utc(_json(capture)["known_at_utc"])
            if clock <= now and _json(path).get("candidates"):
                reports.append((clock, path))
        except (KeyError, TypeError, ValueError):
            continue
    if not reports:
        raise ValueError("GOLD_NOTE_MAIN_DAILY_REPORT_ABSENT")
    return max(reports, key=lambda row: (row[0], str(row[1])))[1]


def _official_cpi(report_path, cutoff):
    """Reuse the newest held official release known by Main's capture."""
    paths = [report_path.with_name("role-evidence.json"),
             *sorted(report_path.parent.parent.glob("*/role-evidence.json"))]
    options = []
    for path in dict.fromkeys(paths):
        if not path.is_file():
            continue
        raw = path.read_bytes()
        evidence = json.loads(raw)
        rows = evidence if isinstance(evidence, list) else evidence.get("rows", [])
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("content"), dict):
                continue
            content = row["content"]
            rights = row.get("rights_state") or {}
            rights = rights.get("rights_state") if isinstance(rights, dict) else rights
            if (content.get("source_url") == "https://www.bls.gov/news.release/cpi.nr0.htm"
                    and rights == "PUBLIC_DOMAIN_ATTRIBUTION_REQUIRED" and content.get("official_text")
                    and row.get("known_at_utc") and utc(row["known_at_utc"]) <= cutoff):
                options.append((row, {"path": str(path), "sha256": sha256(raw).hexdigest()}))
    if not options:
        raise ValueError("GOLD_NOTE_HELD_OFFICIAL_CPI_RELEASE_ABSENT")
    return max(options, key=lambda option: utc(option[0]["known_at_utc"]))


def source_context(*, now, report_root=NATIVE_MAIN_REPORT_ROOT):
    """Reuse the exact public-span adapter. No execution row enters native input."""
    path = _latest_report(report_root, now)
    raw = path.read_bytes()
    report = json.loads(raw)
    digest = sha256(raw).hexdigest()
    capture = path.with_name("capture.json")
    capture_raw = capture.read_bytes()
    cutoff = utc(json.loads(capture_raw)["known_at_utc"])
    known = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    if known > now:
        raise ValueError("GOLD_NOTE_REPORT_AFTER_OBSERVATION")
    table, passages = [], []
    for asset, aliases in MARKETS.items():
        match = next(((i, c) for i, c in enumerate(report["candidates"])
                      if any(c.get("candidate_id", "").casefold().endswith("_" + alias) for alias in aliases)), None)
        if match is None:
            table.append({"asset": asset, "view": None, "cause": "MAIN_MARKET_VIEW_ABSENT"})
            continue
        i, candidate = match
        text = candidate.get("rationale", "")
        end = text.find("\nPriced:")
        first = text[:end] if end >= 0 else text.split("\n", 1)[0]
        # Main sometimes puts private plan/cost prose after the opening view.
        first = re.split(r"\b(?:Mechanism:|Plan:|Cost line:|Desk outcome:)", first)[0].strip()
        if not first or len(first) > 1800:
            raise ValueError("GOLD_NOTE_MAIN_VIEW_SPAN_INVALID:" + asset)
        passages.append({"source_path": str(path), "source_sha256": digest,
            "source_json_pointer": f"/candidates/{i}/rationale",
            "fragments": [{"start": 0, "end": len(first)}]})
        table.append({"asset": asset, "view": first, "source_json_pointer": f"/candidates/{i}/rationale"})
    gold = next(row for row in table if row["asset"] == "XAUUSD")
    if not gold["view"]:
        raise ValueError("GOLD_NOTE_MAIN_GOLD_VIEW_ABSENT")
    spec = {"authority_ref": "JIM_DECISION_89", "source_url": "urn:cc-public-report:gold-note:" + digest,
        "headline_id": "cc406-main-" + digest, "headline_text": "Main daily gold and six-market views",
        "known_at_utc": known.isoformat(), "revision_at_utc": now.isoformat(), "passages": passages}
    verified = verify_projection(spec)
    # Main already holds the official release. Retain only two exact BLS spans,
    # not the full evidence file or its private neighbouring rows.
    official, evidence_binding = _official_cpi(path, cutoff)
    content = official["content"]
    text = content["official_text"]
    patterns = [
        ("headline", "CPI chung", r"The Consumer Price Index for All Urban Consumers \(CPI-U\) (?:increased|rose) ([\d.]+) percent"),
        ("core", "CPI lõi", r"The index for all items less food and energy (?:increased|rose) ([\d.]+) percent"),
    ]
    facts = []
    main_summary = " ".join(row.get("text", "") for row in report.get("summary", []) if isinstance(row, dict))
    main_patterns = {"headline": r"\b(?:CPI-U|headline CPI|CPI)\s+\+?(\d+(?:\.\d+)?)%",
                     "core": r"\bcore(?: CPI)?\s+\+?(\d+(?:\.\d+)?)%"}
    for identity, label, pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            raise ValueError("GOLD_NOTE_OFFICIAL_CPI_FIELD_ABSENT:" + identity)
        main_value = re.search(main_patterns[identity], main_summary, re.I)
        if main_value and float(main_value[1]) != float(match[1]):
            raise ValueError("GOLD_NOTE_OFFICIAL_NUMBER_DIFFERS_FROM_MAIN:" + identity)
        value = float(match[1])
        facts.append({"fact_id": identity, "label": label, "value": value, "display": match[1] + "%",
            "unit": "percent_month_on_month_seasonally_adjusted", "period": content["reference_period"],
            "publisher": "U.S. Bureau of Labor Statistics (BLS)", "source_url": content["source_url"],
            "known_at_utc": official["known_at_utc"], "rights_class": "PUBLIC_DOMAIN_ATTRIBUTION_REQUIRED",
            "source_excerpt": match[0], "source_span": [match.start(), match.end()],
            "source_row_key": official["key"], "official_text_sha256": sha256(text.encode()).hexdigest()})
    context = {"schema_version": SCHEMA, "data_cutoff_utc": cutoff.isoformat(),
        "source_age_seconds": (now - cutoff).total_seconds(), "observed_at_utc": now.isoformat(),
        "main_source": {"path": str(path), "sha256": digest, "projection_sha256": sha256_of(verified),
            "known_at_utc": known.isoformat(), "capture_path": str(capture), "capture_sha256": sha256(capture_raw).hexdigest()},
        "gold_view": gold, "six_market_table": table, "official_facts": facts,
        "official_evidence": evidence_binding,
        "public_date_et": cutoff.astimezone(ET).date().isoformat(),
        "notice": NOTICE, "chart": {"kind": "bar", "series": "BLS CPI monthly change", "fact_ids": ["headline", "core"]}}
    context["source_pack_sha256"] = sha256_of(context)
    return context


def validate_note(output, context):
    text = output.get("text", "")
    if not isinstance(text, str) or not text.strip() or len(text.split()) > 150:
        raise ValueError("GOLD_NOTE_150_WORD_LIMIT_OR_TEXT_INVALID")
    if not text.rstrip().endswith(NOTICE) or text.count(NOTICE) != 1:
        raise ValueError("GOLD_NOTE_EXACT_FINAL_NOTICE_REQUIRED")
    if re.search(r"capital\s*chronicle|\[\[SOURCE:|https?://|GMT|UTC|Bangkok|DEMO|MT5", text, re.I):
        raise ValueError("GOLD_NOTE_BRAND_INTERNAL_LABEL_OR_PUBLIC_TIME_INVALID")
    if public_text_problems(text) or re.search(r"(?:hãy|nên)\s+(?:mua|bán)|vào lệnh|chốt lời|dừng lỗ", text, re.I):
        raise ValueError("GOLD_NOTE_PRIVATE_DETAIL_OR_PERSONAL_ADVICE")
    facts = {row["fact_id"]: row for row in context["official_facts"]}
    ids = output.get("fact_ids")
    if not isinstance(ids, list) or not ids or any(identity not in facts for identity in ids):
        raise ValueError("GOLD_NOTE_EXACT_OFFICIAL_FACT_BINDINGS_REQUIRED")
    if "BLS" not in text:
        raise ValueError("GOLD_NOTE_OFFICIAL_ATTRIBUTION_REQUIRED")
    allowed = numbers(" ".join(facts[identity]["display"] for identity in ids))
    # Dates may be used as dated context; no new price, probability or forecast.
    allowed |= numbers(context["public_date_et"])
    for row in context["official_facts"]:
        allowed |= numbers(str(row["period"]).replace("-M", "-"))
    if numbers(text) - allowed:
        raise ValueError("GOLD_NOTE_NUMBER_NOT_IN_BOUND_OFFICIAL_SOURCE")
    return output


def _turn(store, output_root, day):
    from live_contentops.durable_operational_store_v1 import WorkItemNotFoundError
    run_id = "cc406-gold-note-" + day.isoformat()
    work = "cc-opportunity-" + sha256_of(run_id)
    try:
        store.get_work_item(work)
    except WorkItemNotFoundError:
        store.create_work_item(story_id=work, work_item_id=work, title="Vietnamese gold note " + day.isoformat(),
                               target_surface="CONTENTOPS_EDITORIAL_ONLY")
    return NativeDesktopTurn(store, run_id=run_id, output_dir=Path(output_root) / "owner-manual" / run_id)


def prepare(store, *, output_root, now=None, day=None, report_root=NATIVE_MAIN_REPORT_ROOT, notes_root=ROOT):
    now = now or datetime.now(timezone.utc)
    day = day or now.astimezone(LOCAL).date()
    if day > now.astimezone(LOCAL).date():
        raise ValueError("GOLD_NOTE_FUTURE_DAY_FORBIDDEN")
    if day.weekday() >= 5:
        return {"state": "NO_TRADING_DAY_NOTE_DUE", "day": day.isoformat()}
    metadata = Path(notes_root) / (day.isoformat() + ".json")
    if metadata.is_file():
        return status(notes_root=notes_root, day=day)
    turn = _turn(store, output_root, day)
    frozen = turn.frozen_request("gold-note")
    context = frozen["governed_input"] if frozen else source_context(now=now, report_root=report_root)
    prompt = frozen["prompt"] if frozen else PROMPT + "\nGOVERNED_INPUT:\n" + canonical_bytes(context).decode()
    try:
        output, telemetry = turn(logical_invocation_id=turn.run_id + ":gold-note", governed_input=context,
            prompt=prompt, validator=lambda raw: (True, None, validate_note(json.loads(raw), context), None))
    except DesktopInputRequired as pending:
        return {"state": "GOLD_NOTE_NATIVE_INPUT_REQUIRED", "day": day.isoformat(),
            "stage": "gold-note", "request_path": pending.request["request_path"],
            "request_sha256": pending.request["request_sha256"], "requested_model": "gpt-6.1-sol",
            "requested_reasoning_effort": "max", "public_write_performed": False,
            "next_command": {"command": "gold-note-submit", "note_date": day.isoformat(),
                "response": "<authored-response.json>", "rollout": "<same applied rollout>"},
            "continuation_required": "Read the exact request, write in this native MAX context, gold-note-submit, inspect its PNG, then gold-note-accept; do not end with an executable pending note."}
    validate_note(output, context)
    preview = turn.root / "gold-note"
    _atomic(preview.with_suffix(".md"), (output["text"].strip() + "\n").encode())
    chart = render_chart(context, preview.with_suffix(".png"))
    return {"state": "GOLD_NOTE_RENDER_REVIEW_REQUIRED", "day": day.isoformat(),
        "text_path": str(preview.with_suffix(".md")), "text_sha256": sha256(preview.with_suffix(".md").read_bytes()).hexdigest(),
        "chart_path": str(preview.with_suffix(".png")), "chart_sha256": chart,
        "word_count": len(output["text"].split()), "source_pack_sha256": context["source_pack_sha256"],
        "telemetry": telemetry, "public_write_performed": False,
        "next_command": {"command": "gold-note-accept", "note_date": day.isoformat(),
            "response": "<exact render review.json>", "rollout": "<same applied rollout>"},
        "continuation_required": "Inspect the exact PNG and note in the writing context, save the review with text_sha256, chart_sha256, accepted and findings, then gold-note-accept in this same turn."}


def render_chart(context, path):
    """Render the exact admitted official values; no interpolation or new data."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    facts = {row["fact_id"]: row for row in context["official_facts"]}
    rows = [facts[identity] for identity in context["chart"]["fact_ids"]]
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 15}):
        fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
        bars = ax.bar([r["label"] for r in rows], [r["value"] for r in rows], color=["#a97522", "#334f68"], width=.5)
        ax.bar_label(bars, labels=[r["display"] for r in rows], padding=7, fontsize=19)
        ax.set_ylim(min(0, min(r["value"] for r in rows) * 1.4), max(.1, max(r["value"] for r in rows) * 1.4))
        ax.set_ylabel("Thay đổi theo tháng (%), đã điều chỉnh mùa vụ")
        period = str(rows[0]["period"]).replace("-M", "-")
        ax.set_title("Lạm phát Mỹ — " + period, loc="left", fontsize=23, pad=24)
        ax.spines[["top", "right"]].set_visible(False)
        ax.yaxis.grid(True, alpha=.2)
        ax.set_axisbelow(True)
        fig.supxlabel("Nguồn: U.S. Bureau of Labor Statistics (BLS)\nCPI lõi loại trừ thực phẩm và năng lượng.", fontsize=12)
        fig.savefig(path, dpi=150)
        plt.close(fig)
    return sha256(Path(path).read_bytes()).hexdigest()


def accept(store, *, output_root, review, now=None, day=None, notes_root=ROOT):
    now = now or datetime.now(timezone.utc)
    day = day or now.astimezone(LOCAL).date()
    if day > now.astimezone(LOCAL).date():
        raise ValueError("GOLD_NOTE_FUTURE_DAY_FORBIDDEN")
    turn = _turn(store, output_root, day)
    request, response = turn.frozen_request("gold-note"), turn._get("gold-note", "response")
    if not request or not response:
        raise ValueError("GOLD_NOTE_NATIVE_RETURN_REQUIRED")
    context = request["governed_input"]
    validate_note(response["output"], context)
    preview = turn.root / "gold-note"
    raw_text, raw_chart = preview.with_suffix(".md").read_bytes(), preview.with_suffix(".png").read_bytes()
    hashes = {"text_sha256": sha256(raw_text).hexdigest(), "chart_sha256": sha256(raw_chart).hexdigest()}
    if any(review.get(k) != v for k, v in hashes.items()) or review.get("accepted") is not True or not review.get("findings"):
        raise ValueError("GOLD_NOTE_EXACT_RENDER_INSPECTION_REQUIRED")
    if raw_text.decode().strip() != response["output"]["text"].strip():
        raise ValueError("GOLD_NOTE_RENDER_TEXT_CHANGED")
    root = Path(notes_root)
    target = root / day.isoformat()
    record = {"schema_version": SCHEMA, "day": day.isoformat(), "prepared_at_utc": now.isoformat(),
        "deadline_utc": datetime.combine(day, time(7, 30), LOCAL).astimezone(timezone.utc).isoformat(),
        "ready_by_0730": now <= datetime.combine(day, time(7, 30), LOCAL),
        "acceptance_morning": day >= FIRST_MORNING, "source_pack_sha256": context["source_pack_sha256"],
        "data_cutoff_utc": context["data_cutoff_utc"], "source_age_seconds_at_delivery": (now - utc(context["data_cutoff_utc"])).total_seconds(),
        "main_source": context["main_source"], "official_evidence": context["official_evidence"],
        "official_facts": context["official_facts"], "six_market_table": context["six_market_table"],
        "native_request_sha256": request["request_sha256"], "native_return_sha256": sha256_of(response),
        "invocation_observation": response["invocation_observation"], "review": review,
        "text_path": str(target.with_suffix(".md")), "chart_path": str(target.with_suffix(".png")),
        "word_count": len(response["output"]["text"].split()), **hashes, "public_write_performed": False}
    meta = target.with_suffix(".json")
    if meta.is_file():
        prior = _json(meta)
        if any(prior.get(k) != v for k, v in hashes.items()):
            raise ValueError("GOLD_NOTE_DATED_OUTPUT_CONFLICT")
        return status(notes_root=root, day=day)
    # The desk selects Markdown; install the reviewed image before that file.
    _atomic(target.with_suffix(".png"), raw_chart)
    _atomic(target.with_suffix(".md"), raw_text)
    _atomic(meta, canonical_bytes(record))
    return status(notes_root=root, day=day)


def status(*, notes_root=ROOT, day=None):
    day = day or datetime.now(LOCAL).date()
    path = Path(notes_root) / (day.isoformat() + ".json")
    if not path.is_file():
        return {"state": "GOLD_NOTE_NOT_PREPARED", "day": day.isoformat(), "first_acceptance_morning": FIRST_MORNING.isoformat()}
    value = _json(path)
    for kind in ("text", "chart"):
        if sha256(Path(value[kind + "_path"]).read_bytes()).hexdigest() != value[kind + "_sha256"]:
            raise ValueError("GOLD_NOTE_DATED_OUTPUT_BYTES_CHANGED")
    return {"state": "GOLD_NOTE_READY_ON_DESK_INPUT", "day": value["day"],
        **{k: value[k] for k in ("text_path", "chart_path", "word_count", "prepared_at_utc", "ready_by_0730", "acceptance_morning")},
        "first_acceptance_morning": FIRST_MORNING.isoformat(), "public_write_performed": False}


def command(rollout, action, *, response=None, day=None, now=None, notes_root=ROOT):
    """One native command in the existing store; no timer and no public transport."""
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    now = now or datetime.now(timezone.utc)
    day = day or now.astimezone(LOCAL).date()
    if day > now.astimezone(LOCAL).date():
        raise ValueError("GOLD_NOTE_FUTURE_DAY_FORBIDDEN")
    if action == "gold-note-status":
        return status(notes_root=notes_root, day=day)
    store = ContentOpsDurableStore(rollout["store_path"], auto_migrate=False)
    output_root = rollout["editorial_output_root"]
    owner = "cc406-" + uuid4().hex
    lease = store.acquire_lease("internal:cc406:" + day.isoformat(), owner, ttl_seconds=60)
    try:
        if action == "gold-note-accept":
            return accept(store, output_root=output_root, review=response or {}, now=now, day=day, notes_root=notes_root)
        if action == "gold-note-submit":
            _turn(store, output_root, day).submit("gold-note", response or {})
        return prepare(store, output_root=output_root, now=now, day=day, notes_root=notes_root)
    finally:
        store.release_lease(lease["lease_id"], owner, lease["fencing_token"])
