"""CC-143: a frozen index of confirmed articles, using the existing outbox/publisher.

The renderer copies public titles and links only. It authors no analysis. The
existing host tick prepares due work; a native conversation performs Neo actions.
No timer, email provider, store, publication or authentication owner is added.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.destination_transport_registry_v1 import REGISTRY_VERSION, registration_for_destination
from live_contentops.event_article_guard_v1 import PUBLIC_NOTICE
from live_contentops.published_content_v1 import read_records, utc

DESTINATION = "internal:substack-daily-digest"
WEB_ONLY = "WEB_ONLY"
EMAIL_DIGEST = "DAILY_EMAIL_DIGEST"
BANGKOK = timezone(timedelta(hours=7))


def delivery_policy(mode):
    if mode not in {WEB_ONLY, EMAIL_DIGEST}:
        raise ValueError("SUBSTACK_DELIVERY_MODE_INVALID")
    return {"authority": "JIM_DECISION_42", "mode": mode,
            "web_publish_enabled": True, "email_send_enabled": mode == EMAIL_DIGEST,
            "before_publish": "Inspect the visible delivery controls. Set and verify the email choice before the final Publish button; stop before writing if it cannot be verified.",
            "return_fields": ["delivery_observation.email_send_enabled", "delivery_observation.web_publish_enabled", "delivery_observation.evidence_ref"],
            "code_policy": "JIM_DECISION_54_WAIT_ON_UNTOUCHED_CODE_TAB",
            "duplicate_policy": "Reuse this operation's existing draft/post; read back before any retry. Never create a second draft."}


def packets(store):
    # Never hydrate unrelated historical media payloads on the cheap host tick.
    with store.get_read_only_connection() as conn:
        return [json.loads(r[0]) for r in conn.execute(
            "SELECT payload FROM outbox_messages WHERE destination=? ORDER BY created_at,message_id",
            (DESTINATION,))]


def validate_digest_plan(store, work_item_id, plan):
    row = store.get_outbox_message("substack-digest-" + work_item_id)
    packet = json.loads(row["payload"]) if row else {}
    if (packet.get("digest_id") != work_item_id or packet.get("plan") != plan
            or plan.get("daily_digest") != work_item_id):
        raise ValueError("EXACT_FROZEN_DAILY_DIGEST_REQUIRED")
    return packet


def delivery_mode_for_plan(store, work_item_id, plan):
    if plan.get("daily_digest"):
        validate_digest_plan(store, work_item_id, plan)
        return EMAIL_DIGEST
    # No caller can turn an ordinary article into a per-post email blast.
    return WEB_ONLY


def validate_digest_intent(store, intent):
    row = store.get_outbox_message("substack-digest-" + str(intent.get("daily_digest")))
    packet = json.loads(row["payload"]) if row else {}
    plan = packet.get("plan", {})
    if (intent.get("work_item_id") != packet.get("digest_id")
            or intent.get("plan_hash") != plan.get("plan_hash")
            or intent.get("native_payload") != packet.get("native_payload")
            or intent.get("media_assets", []) != packet.get("media_assets", [])
            or intent.get("destination_plan") != {**plan.get("destinations", [{}])[0],
                                                   "substack_delivery_mode": EMAIL_DIGEST}):
        raise ValueError("EXACT_FROZEN_DAILY_DIGEST_INTENT_REQUIRED")
    return packet


def digest_status(store, packet):
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    ids = DurablePublicationCoordinator._ids(packet["digest_id"], packet["plan"]["plan_hash"], "substack")
    dispatch = store.get_platform_dispatch(ids["dispatch_id"]) or {}
    reconciled = any(r["reconciliation_id"] == ids["reconciliation_id"] and r["status"] == "RECONCILED_CONFIRMED"
                     for r in store.get_reconciliations_for_work_item(packet["digest_id"]))
    web_confirmed = reconciled and DurablePublicationCoordinator._confirmed_public_object(
        {**dispatch, "reconciliation_status": "RECONCILED_CONFIRMED"}, destination="substack")
    # A public page proves web publication, not subscriber email delivery.
    email_confirmed = False
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor
    observer = NativeNeoExecutor(store, operation_id=packet["digest_id"], output_dir=".",
                                 native_invocation_id="status-read-only")
    with store.get_read_only_connection() as conn:
        rows = conn.execute("SELECT payload FROM outbox_messages WHERE destination=? AND work_item_id=?",
                            ("internal:native-neo-tool", packet["digest_id"])).fetchall()
    for row in rows:
        request = json.loads(row[0]).get("request", {})
        if request.get("action") != "READBACK" or request.get("destination") != "substack":
            continue
        returned = observer._get(request["request_sha256"], "response") or {}
        result = returned.get("result", {})
        email_confirmed |= (result.get("email_delivery_confirmed") is True
            and bool(result.get("email_delivery_evidence_ref"))
            and result.get("observed_identity") == "capitalchronicle.substack.com"
            and result.get("public_object_id") == dispatch.get("public_object_id")
            and result.get("public_object_url") == dispatch.get("public_object_url")
            and bool(result.get("native_tool_observation")))
    confirmed = bool(web_confirmed and email_confirmed)
    return {"digest_id": packet["digest_id"], "confirmed": confirmed,
            "web_confirmed": bool(web_confirmed), "email_confirmed": email_confirmed,
            "state": "CONFIRMED" if confirmed else "WEB_CONFIRMED_EMAIL_READBACK_REQUIRED" if web_confirmed
                     else dispatch.get("status", "PREPARED_NATIVE_INPUT_REQUIRED"),
            "public_object_id": dispatch.get("public_object_id"), "public_object_url": dispatch.get("public_object_url")}


def _link_title(title):
    # Escape Markdown syntax without changing the reader-visible source title.
    return title.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]").replace("\n", " ")


def day_label(day):
    """Reader date without a zero-padded day: "November 3, 2026"."""
    return f"{day:%B} {day.day}, {day.year}"


def _plain(text):
    return " ".join(str(text or "").replace("\n", " ").split())


def substack_subtitle(text):
    """The native editor accepts 200 characters; full titles stay in the body."""
    text = _plain(text)
    return text if len(text) <= 200 else text[:197].rsplit(" ", 1)[0] + "..."


def _utc_text(value):
    return utc(str(value).replace("Z", "+00:00")).isoformat()


def live_canonicals(store):
    """Confirmed Substack articles in the store, with title and standfirst.

    The feed (CC-135) omits a live article whose canonical readback was held
    content-incomplete after a credit edit (the 3 Nov midterm preview), so the
    digest also reads the store's confirmed canonical dispatches.
    """
    from pathlib import Path
    rows = []
    with store.get_read_only_connection() as conn:
        found = conn.execute(
            "SELECT d.public_object_id, d.public_object_url, d.dispatched_at, m.work_item_id, m.payload "
            "FROM platform_dispatches d JOIN outbox_messages m ON m.message_id=d.message_id "
            "WHERE d.platform='substack' AND d.status='DISPATCH_CONFIRMED' AND d.public_object_url IS NOT NULL "
            "ORDER BY d.dispatched_at").fetchall()
        for public_id, url, dispatched_at, work_item_id, payload in found:
            intent = json.loads(payload)
            if intent.get("daily_digest") or not intent.get("output_dir"):
                continue
            manifest = Path(intent["output_dir"]) / "article_manifest_v1.json"
            if not manifest.is_file():
                continue
            article = json.loads(manifest.read_bytes())
            published = None
            for (data,) in conn.execute("SELECT readback_data FROM readbacks WHERE dispatch_id IN "
                    "(SELECT dispatch_id FROM platform_dispatches WHERE message_id IN "
                    "(SELECT message_id FROM outbox_messages WHERE work_item_id=?) AND platform='substack') "
                    "ORDER BY read_at", (work_item_id,)):
                observed = (json.loads(data).get("readback") or {}).get("observed_published_at_utc")
                if observed:
                    published = observed
                    break
            rows.append({"content_id": "substack:" + str(public_id), "url": url,
                         "title": _plain(article.get("title")),
                         "standfirst": _plain(article.get("dek") or article.get("subtitle")),
                         "published_at_utc": published or dispatched_at})
    return [r for r in rows if r["title"]]


def _titles_card(day, articles, *, output_dir, evidence_sha256):
    """A card naming the day's pieces, in the CC-245 site design, not an empty "N articles" card."""
    from live_contentops.fact_card_design_v1 import CardSpec, DESIGN, render_fact_card
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _sha256_file
    binding = {"digest_day": day.isoformat(), "titles": [a["title"] for a in articles],
               "accepted_evidence_sha256": evidence_sha256, "design": DESIGN}
    path = Path(output_dir) / ("digest-card-" + sha256_of(binding)[:20] + ".png")
    path.parent.mkdir(parents=True, exist_ok=True)
    label = day_label(day)
    facts = [("Edition", label), *(("", a["title"]) for a in articles[:5])]
    if len(articles) > 5:
        facts.append(("", f"and {len(articles) - 5} more"))
    render_fact_card(path, CardSpec(title="Capital Chronicle daily digest", facts=facts, kicker="Daily digest",
        key_label="Edition", key_value=label, source_line="Capital Chronicle's own articles",
        dated_line="Capital Chronicle · " + label))
    title = "Capital Chronicle daily digest, " + label
    return {"asset_id": "digest-card-" + sha256_of(binding)[:20], "path": str(path.resolve()),
            "sha256": _sha256_file(path), "width": 1600, "height": 900, "modality": "source_backed_chart",
            "visual_type": "DIGEST_TITLES_CARD", "digest_card_binding": binding, "quantitative_chart": False,
            "caption": title, "alt_text": title + ": " + "; ".join(a["title"] for a in articles),
            "placement_after": "lead", "rights_status": "OWNED_ORIGINAL",
            "rights": "Capital Chronicle original publication index and layout"}


def prepare_daily_digest(store, feed_path, *, now=None):
    """Freeze once per 19:00 GMT+7 cutoff; resume an unsent draft before a new day.

    Cutoffs cover the preceding 24 hours, so a post after 19:00 is included in the
    following digest. Already allocated identities/URLs are never selected again.
    There is no two-hour timeout/retry: decision 54 supersedes that older rule.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("EXPLICIT_DIGEST_CLOCK_REQUIRED")
    local = now.astimezone(BANGKOK)
    day = local.date() if local.time() >= time(19) else local.date() - timedelta(days=1)
    end = datetime.combine(day, time(19), BANGKOK).astimezone(timezone.utc)
    start = end - timedelta(days=1)
    digest_id = "cc143-digest-" + day.isoformat()
    from uuid import uuid4
    owner = "digest-prepare-" + uuid4().hex
    lease = store.acquire_lease(DESTINATION, owner, ttl_seconds=60)
    try:
        prior = sorted(packets(store), key=lambda p: p["cutoff_utc"])
        for packet in prior:
            status = digest_status(store, packet)
            # A live digest page is done for sequencing. Its email readback stays
            # recorded, but it never holds the next day's digest (4 Nov: the 3 Nov
            # digest's unobservable email would have held every later one).
            if not (status["confirmed"] or status["web_confirmed"]) or packet["digest_id"] == digest_id:
                return {**status, "packet": packet, "public_write_performed": False}
        if prior:
            # Delayed code entry or a late confirmed-feed append must not lose
            # articles between digests. Already allocated IDs/URLs are excluded.
            start = utc(prior[0]["plan"]["publication_window"]["start_utc"])
        used_ids = {a["content_id"] for p in prior for a in p["articles"]}
        used_urls = {a["url"] for p in prior for a in p["articles"]}
        candidates = []
        feed_rows = read_records(feed_path) if feed_path and Path(feed_path).is_file() else []
        for row in feed_rows:
            if utc(row["recorded_at_utc"]) <= now:
                candidates.append({"content_id": row["content_id"], "title": row["title"],
                    "standfirst": row["standfirst"], "published_at_utc": row["published_at_utc"],
                    "url": next(o["url"] for o in row["outlets"] if o["name"] == "substack")})
        # A live Substack article the feed lacks is still the day's piece.
        candidates.extend(live_canonicals(store))
        articles = []
        for row in sorted(candidates, key=lambda r: (utc(_utc_text(r["published_at_utc"])), r["content_id"])):
            if (start < utc(_utc_text(row["published_at_utc"])) <= end
                    and row["content_id"] not in used_ids and row["url"] not in used_urls):
                articles.append({"content_id": row["content_id"], "title": row["title"],
                    "standfirst": row.get("standfirst") or "",
                    "published_at_utc": _utc_text(row["published_at_utc"]), "url": row["url"]})
                articles[-1]["content_sha256"] = sha256_of({k: articles[-1][k] for k in ("content_id", "title", "url")})
                used_ids.add(row["content_id"])
                used_urls.add(row["url"])
        if not articles:
            return {"digest_id": digest_id, "state": "NO_CONFIRMED_ARTICLES", "public_write_performed": False}
        titles = "; ".join(a["title"] for a in articles)
        subtitle = substack_subtitle(titles)
        entries = [f'**[{_link_title(a["title"])}]({a["url"]})**' + (f'\n\n{a["standfirst"]}' if a["standfirst"] else "")
                   for a in articles]
        payload = {"title": "Capital Chronicle daily digest — " + day_label(day),
                   "subtitle": subtitle,
                   "body_markdown": "\n\n".join([*entries, PUBLIC_NOTICE])}
        card = _titles_card(day, articles,
            output_dir=Path(store.db_path).parent / "daily_app_outputs" / "owner-manual" / digest_id / "media",
            evidence_sha256=sha256_of(articles))
        registration = registration_for_destination("substack")
        body = payload["body_markdown"]
        plan = {"schema_version": "contentops.publication_plan.v1", "daily_digest": digest_id,
                "story_identity": digest_id, "article_identity": digest_id, "package_identity": digest_id,
                "transport_registry_version": REGISTRY_VERSION, "policy_mode_version": "AUTONOMOUS_DEFAULT:JIM_DECISION_42",
                "publication_window": {"window_identity": digest_id, "start_utc": start.isoformat(), "cutoff_utc": end.isoformat()},
                "source_provenance_binding_preserved": True,
                "accepted_evidence_ids": [a["content_id"] for a in articles], "accepted_evidence_sha256": sha256_of(articles),
                "destinations": [{"destination": "substack", "surface": registration.surface,
                    "transport_type": registration.transport_type, "payload": body,
                    "payload_hash": sha256(body.encode()).hexdigest(), "readiness_state": "READINESS_UNKNOWN"}]}
        plan["plan_hash"] = sha256_of(plan)
        packet = {"schema_version": "contentops.substack_daily_digest.v1", "digest_id": digest_id,
                  "cutoff_utc": end.isoformat(), "prepared_at_utc": now.astimezone(timezone.utc).isoformat(),
                  "articles": articles, "native_payload": payload, "media_assets": [card], "plan": plan}
        store.create_work_item(story_id=digest_id, work_item_id=digest_id,
                               title=payload["title"], target_surface="SUBSTACK_ARTICLE")
        store.register_outbox_message(message_id="substack-digest-" + digest_id, work_item_id=digest_id,
            destination=DESTINATION, payload=canonical_bytes(packet).decode(), status="EDITORIAL_INTERNAL")
        return {**digest_status(store, packet), "packet": packet, "public_write_performed": False}
    finally:
        store.release_lease(lease["lease_id"], owner, lease["fencing_token"])


def production_digest_housekeeping(store, *, now=None):
    """Called by the existing host tick, with no schedule or browser action."""
    from pathlib import Path
    from live_contentops.published_content_v1 import DEFAULT_FEED, PRODUCTION_STORE
    if Path(store.db_path).resolve() != PRODUCTION_STORE.resolve():
        return {"state": "NOT_PRODUCTION_STORE", "public_write_performed": False}
    if store.get_operating_control()["operating_mode"] != "AUTONOMOUS_DEFAULT":
        return {"state": "PUBLICATION_OPERATING_MODE_BLOCKED", "public_write_performed": False}
    if not DEFAULT_FEED.is_file():
        return {"state": "CONFIRMED_PUBLICATION_FEED_MISSING", "public_write_performed": False}
    result = prepare_daily_digest(store, DEFAULT_FEED, now=now)
    summary = {k: v for k, v in result.items() if k != "packet"}
    if result.get("packet") and not result.get("confirmed"):
        summary["native_continuation"] = {
            "command": "digest-resume",
            "arguments": ["--rollout", "config/native_desktop_rollout_v1.json",
                          "--native-invocation-id", "<actual-active-invocation>"],
            "instruction": "Continue this exact due digest through the existing Neo begin/submit loop before preparing another digest. Preserve any code tab and never read a mailbox or enter a code.",
        }
    return summary


def continue_daily_digest(store, packet, *, output_dir, invocation_id, rollout, command="resume",
                          request_hash=None, response=None):
    """Use the same native Neo begin/submit loop and sole coordinator as articles."""
    from pathlib import Path
    from live_contentops.native_desktop_publication_v1 import live_publication_policy
    from live_contentops.native_neo_executor_v1 import bind_native_neo_coordinator, NativeNeoInputRequired
    from live_contentops.llm_operator_control_v1 import assert_llm_operator_execution_enabled
    live_publication_policy(rollout)
    if Path(store.db_path).resolve() != Path(rollout["store_path"]).resolve():
        raise ValueError("EXACT_DIGEST_ROLLOUT_STORE_REQUIRED")
    assert_llm_operator_execution_enabled()
    if store.get_operating_control()["operating_mode"] != "AUTONOMOUS_DEFAULT":
        raise ValueError("PUBLICATION_OPERATING_MODE_BLOCKED")
    plan = packet["plan"]
    validate_digest_plan(store, packet["digest_id"], plan)
    coordinator, executor = bind_native_neo_coordinator(store, operation_id=packet["digest_id"],
        output_dir=output_dir, native_invocation_id=invocation_id, allow_publish=True)
    # Match the ordinary live article owner: a different, confirmed article's
    # unfinished social delivery cannot hold this exact digest's Substack send.
    # The coordinator still keeps unknown canonical and same-object writes local.
    coordinator.allow_prior_confirmed_distribution = True
    coordinator.recovery_scope = {"work_item_id": packet["digest_id"], "plan": plan}
    if command in {"begin", "submit"}:
        request = (executor._get(request_hash, "request") or {}).get("request", {})
        if request.get("work_item_id") not in {packet["digest_id"],
                "native-neo-operation-" + sha256_of(packet["digest_id"])}:
            raise ValueError("EXACT_DIGEST_TOOL_REQUEST_REQUIRED")
        return executor.begin(request_hash) if command == "begin" else executor.submit(request_hash, response)
    try:
        status = digest_status(store, packet)
        if status["web_confirmed"] and not status["email_confirmed"]:
            ids = coordinator._ids(packet["digest_id"], plan["plan_hash"], "substack")
            result = coordinator.readback_existing_dispatch(ids["dispatch_id"])
            return {"publication": result, **digest_status(store, packet), "pending_requests": executor.pending()}
        result = coordinator.publish_plan(packet["digest_id"], plan)
    except NativeNeoInputRequired as pending:
        return {"state": "NATIVE_NEO_TOOL_PENDING", "native_tool_request": pending.request}
    return {"publication": result, **digest_status(store, packet),
            "pending_requests": executor.pending()}
