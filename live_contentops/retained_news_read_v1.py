"""Small private News view of the existing owner projection; no runtime or store owner.

Request parameters select identities, never paths. Main supplies its existing trusted
SessionAdapter.resolve convention; this module provides no identity provider or listener.
The portable producer artifact is private input, never a directly served public file.
"""
from __future__ import annotations

import base64
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from stat import FILE_ATTRIBUTE_REPARSE_POINT
from types import SimpleNamespace
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "docs/automation/CONTENTOPS_V1_RELEASE_CONVERGENCE_V1"
ARTIFACT_PATH = RELEASE / "main-news/selected-edition.json"
SELECTION_PATH = RELEASE / "data-journalism/edition/workspace.json"
PROFILE_PATH = ROOT / "config/native_desktop_operator_profile_v1.json"
ROLLOUT_PATH = ROOT / "config/native_desktop_rollout_v1.json"
SCHEMA = "contentops.cc_report_editorial_workspace.v1"
VIEW = "contentops.retained_news.private_preview.v1"
SCOPE = "subscriber:read:private-preview"
IDENTITY = re.compile(r"[a-f0-9]{64}\Z")
ASSET_ID = re.compile(r"[a-z][a-z0-9_-]{2,100}\Z")

# Field paths are the existing Goal35 report_workspace_projection read contract.
# Do not replace this with dict(item)/recursive key stripping: absent fields stay absent.
ARTICLE_FIELDS = ("title", "dek", "substack_body_markdown", "display_date", "source_date_notice",
                  "search_title", "meta_description", "search_freshness_class", "canonical_slug_candidate",
                  "topics", "entities", "primary_reader_question", "secondary_reader_questions",
                  "reader_first_version", "resolved_article_mode")
SOURCE_FIELDS = ("source_id", "document_id", "publisher", "url", "published_at_source",
                 "published_at_utc", "source_authority_class", "report_truth_only",
                 "canonical_content_sha256", "retrieval_method", "source_use_basis")
RIGHTS_FIELDS = ("scope", "INTERNAL_ANALYSIS_ALLOWED", "public_expression_reuse_allowed",
                "images_logos_exhibits_reuse_allowed", "attribution_required", "permitted_consumers", "policy_url")
MEDIA_FIELDS = ("asset_id", "sha256", "modality", "caption", "reader_caption", "alt_text", "attribution",
                "reader_credit", "source_page_url", "width", "height", "placement_after", "creator_publisher",
                "depicted_date", "license_name", "license_url", "rights_status", "underlying_source_rights_status",
                "source_reuse_basis", "changes_description", "context_only", "corroborates_article_facts", "support_caption")
EPISTEMIC_FIELDS = ("reader_visible_epistemic_label", "event_confirmation_state", "evidence_basis",
                    "source_multiplicity", "origin_character", "primary_reporting_publisher", "report_truth_supported",
                    "event_truth_supported", "analysis_must_be_conditional", "underlying_event_may_be_stated_as_confirmed")
PERMITTED_FACT_SCOPES = {"ATTRIBUTED_ORIGINAL_FACTS_ONLY_INDEPENDENT_PUBLIC_PARAPHRASE",
                         "ATTRIBUTED_REPORTED_FACTS_ONLY_INDEPENDENT_PUBLIC_PARAPHRASE"}
HEADERS = {"Cache-Control": "private, no-store, max-age=0", "X-Content-Type-Options": "nosniff",
           "Referrer-Policy": "no-referrer"}


def _pick(value, fields):
    return {key: deepcopy(value[key]) for key in fields if key in value}


def _utc(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("UTC_REQUIRED")
    return parsed


def _url(value):
    parsed = urlsplit(value or "")
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password


def _source(document):
    constraints = document.get("source_reuse_constraints") or {}
    citation_only = document.get("source_use_basis") == "GOVERNED_RELAY_CITATION_METADATA_ONLY"
    if not constraints and document.get("report_truth_only") is True:
        digest = document.get("canonical_content_sha256") or ""
        exact_relay = (document.get("retrieval_method") == "EXACT_GOVERNED_CANONICAL_X_RELAY_SIDECAR"
            and document.get("source_authority_class") == "trusted_professional_feed_relay"
            and document.get("document_id") == "trusted-relay-" + digest[:20]
            and bool(IDENTITY.fullmatch(digest))
            and (document.get("url") or "").startswith("https://x.com/")
            and _url(document.get("url")))
        text = document.get("canonical_content_text")
        if exact_relay and (citation_only or isinstance(text, str)
                and hashlib.sha256(text.encode()).hexdigest() == digest):
            # Citation metadata and our independently authored article are readable.
            # No relay text, source-expression right or new eligibility is exported.
            return {**_pick(document, SOURCE_FIELDS),
                    "source_use_basis": "GOVERNED_RELAY_CITATION_METADATA_ONLY",
                    "publication_precision": "AS_SUPPLIED",
                    "observation_time_utc": document.get("observation_time_utc")}
    if (constraints.get("scope") not in PERMITTED_FACT_SCOPES
            or constraints.get("INTERNAL_ANALYSIS_ALLOWED") is not True
            or "narrative_context" not in constraints.get("permitted_consumers", [])
            or not _url(document.get("url"))):
        raise ValueError("SOURCE_USE_PERMISSION_NOT_ADMITTED")
    source = _pick(document, SOURCE_FIELDS)
    date = source.get("published_at_source")
    # A normalized midnight in evidence is not a supplied release time.
    source["publication_precision"] = "DATE_ONLY" if date and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) else "AS_SUPPLIED"
    if source["publication_precision"] == "DATE_ONLY":
        source["published_at_utc"] = None
    source["observation_time_utc"] = document.get("observation_time_utc")
    source["source_reuse_constraints"] = _pick(constraints, RIGHTS_FIELDS)
    terms = constraints.get("data_terms") or {}
    if terms:
        source["source_reuse_constraints"]["data_terms"] = _pick(terms, (
            "url", "required_attribution", "endorsement_granted", "independent_modification_label_required"))
    return source


def _media_permission(asset):
    if asset.get("modality") == "source_backed_chart":
        if asset.get("underlying_source_rights_status") != "attributed_facts_independent_chart":
            raise ValueError("MEDIA_USE_PERMISSION_NOT_ADMITTED")
    elif asset.get("modality") == "documentary_photo":
        if (asset.get("rights_status") not in {"OPEN_LICENSED", "PUBLIC_DOMAIN"}
                or not asset.get("source_reuse_basis")):
            raise ValueError("MEDIA_USE_PERMISSION_NOT_ADMITTED")
    else:
        raise ValueError("MEDIA_USE_PERMISSION_NOT_ADMITTED")


def _media(asset, *, embed_original=False):
    _media_permission(asset)
    safe = _pick(asset, MEDIA_FIELDS)
    safe["source_links"] = [_pick(link, ("document_id", "label", "url")) for link in asset.get("source_links", [])]
    if not _url(safe.get("source_page_url")) or any(not _url(s["url"]) for s in safe["source_links"]):
        raise ValueError("MEDIA_SOURCE_REQUIRED")
    if table := asset.get("reader_table"):
        safe["reader_table"] = {**_pick(table, ("caption", "unit", "columns", "notes")),
                                "rows": [_pick(row, ("label", "values")) for row in table["rows"]]}
    packet = asset.get("editorial_data_packet") or {}
    safe["data_context"] = {**_pick(packet, ("unit", "subtitle", "comparability_limits")),
        "source_periods": list(dict.fromkeys(i["prepared_period"] for s in packet.get("series", [])
            for point in s["points"] for i in point.get("inputs", []) if i.get("prepared_period")))}
    # Only the producer uses its already inspected owner path. No path is serialized.
    from live_contentops.native_desktop_workspace_v1 import resolve_workspace_path
    path = resolve_workspace_path(asset["path"])
    if path.stat().st_size > 20_000_000:
        raise ValueError("MEDIA_TOO_LARGE")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != asset["sha256"]:
        raise ValueError("MEDIA_BYTES_CHANGED")
    mime = "image/png" if raw.startswith(b"\x89PNG\r\n\x1a\n") else "image/jpeg" if raw.startswith(b"\xff\xd8\xff") else None
    if not mime:
        raise ValueError("MEDIA_FORMAT_UNSUPPORTED")
    safe["content_type"] = mime
    if asset["modality"] == "documentary_photo":
        # Reuse the owner's already generated display derivative. Original photo
        # bytes stay in the existing portable edition, selected only by exact ID.
        prefix, encoded = asset["preview_data_url"].split(",", 1)
        preview = base64.b64decode(encoded, validate=True)
        safe.update(preview_content_type=prefix.removeprefix("data:").removesuffix(";base64"),
                    preview_content_base64=encoded, preview_sha256=hashlib.sha256(preview).hexdigest())
        if embed_original:
            # Current admitted runtime photos have no entry in the historical
            # portable map. Embed the same verified public original, never its path.
            safe["content_base64"] = base64.b64encode(raw).decode("ascii")
    else:
        safe["content_base64"] = base64.b64encode(raw).decode("ascii")
    return safe


def build_news_projection(workspace, *, exported_at_utc, embedded_photo_operations=()):
    """Allowlisted view over the admitted, selected existing owner edition."""
    _utc(exported_at_utc)
    group = workspace["owner_edition"]
    by_run = {item["run_id"]: item for item in workspace["native_edition"]}
    items = []
    for run in group["operation_ids"]:
        item = by_run.get(run)
        if item is None:
            items.append({"run_id": run, "article_identity": None, "availability": "LOCAL_CONTENT_MISSING"})
            continue
        identity = item["article_identity"]
        entry = {"run_id": run, "article_identity": identity,
                 "article_revision": (item.get("review") or {}).get("package_revision")}
        if not IDENTITY.fullmatch(identity):
            raise ValueError("ARTICLE_IDENTITY_REQUIRED")
        try:
            if ((item.get("review") or {}).get("decision") != "KEEP" or item.get("prepared_state")
                    or (item.get("source_review") or {}).get("invalidates_prepared_review")):
                raise ValueError("CURRENT_REVIEW_UNAVAILABLE")
            sources = [_source(document) for document in item.get("evidence", [])]
            if not sources:
                raise ValueError("SOURCE_USE_PERMISSION_NOT_ADMITTED")
            media = [_media(asset, embed_original=run in embedded_photo_operations) for asset in item.get("media_assets", [])]
        except (ValueError, OSError) as exc:
            # An unqualified record must not leak prose, source URLs, tables or images.
            entry.update(availability="CONTENT_RESTRICTED" if isinstance(exc, ValueError) else "LOCAL_CONTENT_MISSING",
                         reason=str(exc) if isinstance(exc, ValueError) else "RETAINED_MEDIA_UNAVAILABLE")
            items.append(entry)
            continue
        publication = item.get("publication") or {}
        destinations = [_pick(d, ("destination", "status", "reconciliation_status")) for d in publication.get("destinations", [])]
        canonical_record = next((d for d in publication.get("destinations", [])
            if d["destination"] == "substack" and d.get("reconciliation_status") == "RECONCILED_CONFIRMED"
            and _url(d.get("public_object_url")) and "pending-publication" not in d["public_object_url"]), None)
        canonical = canonical_record["public_object_url"] if canonical_record else None
        execution = item.get("editorial_execution") or {}
        models = [_pick(o, ("role", "stage", "model", "reasoning_effort")) for o in execution.get("observations", [])]
        entry.update(availability="AVAILABLE", article=_pick(item["article"], ARTICLE_FIELDS),
            evidence=sources, media_assets=media, review=_pick(item["review"], ("decision",)),
            publication={"state": publication.get("state", "UNKNOWN"), "destinations": destinations,
                         "canonical_url": canonical,
                         "canonical_public_object_id": canonical_record.get("public_object_id") if canonical_record else None,
                         "publication_at_utc": publication.get("published_at_utc") if canonical else None},
            clocks={"evidence_cutoff_utc": item.get("source_cutoff_utc"), "retained_at_utc": item.get("retained_at_utc"),
                    "analysis_at_utc": item["article"].get("analysis_at_utc"), "current_market_refresh_verified": False},
            epistemic_state=_pick(item.get("epistemic_state") or {}, EPISTEMIC_FIELDS),
            editorial_execution={"observed_models": models, "attribution": "SAVED_NATIVE_OBSERVATION_NOT_A_NEW_INVOCATION"},
            use_permission={"scope": "PRIVATE_PREVIEW_ONLY", "public_release_authorized_by_export": False,
                            "source_expression_reuse_authorized": False})
        items.append(entry)
    return {"schema_version": SCHEMA, "consumer_view": VIEW, "exported_at_utc": exported_at_utc,
            "owner_edition": _pick(group, ("edition_id", "title", "operation_ids")), "native_edition": items,
            "scope": "PRIVATE_PREVIEW_ONLY", "public_write_performed": False}


def _selected_runtime_projection(store_path, operation_ids):
    """Read only the selected missing operations from the already configured live owner."""
    import sqlite3
    from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    work = list(dict.fromkeys([*operation_ids, *("cc-opportunity-" + sha256_of(r) for r in operation_ids)]))
    placeholders = ",".join("?" for _ in work)
    with sqlite3.connect(Path(store_path).resolve().as_uri() + "?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        conn.execute("BEGIN")
        outbox = [dict(r) for r in conn.execute(
            "SELECT * FROM outbox_messages WHERE work_item_id IN (" + placeholders + ") ORDER BY rowid", work)]
        reviews = [dict(r) for r in conn.execute(
            "SELECT * FROM review_records WHERE work_item_id IN (" + placeholders + ") ORDER BY rowid", work)]
        dispatches = [dict(r) for r in conn.execute(
            "SELECT d.* FROM platform_dispatches d JOIN outbox_messages o ON o.message_id=d.message_id "
            "WHERE o.work_item_id IN (" + placeholders + ") ORDER BY d.rowid", work)]
        reconciliations = [dict(r) for r in conn.execute(
            "SELECT * FROM reconciliations WHERE work_item_id IN (" + placeholders + ") ORDER BY rowid", work)]
    return report_workspace_projection(outbox, review_records=reviews, dispatches=dispatches,
                                      reconciliations=reconciliations, readiness=[])


def export_selected_news():
    """Fixed trusted producer operation: read the existing SQLite in query-only mode."""
    import sqlite3
    from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
    profile = json.loads(PROFILE_PATH.read_bytes())
    selection = json.loads(SELECTION_PATH.read_bytes())["owner_edition"]
    with sqlite3.connect(Path(profile["store_path"]).resolve().as_uri() + "?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        conn.execute("BEGIN")
        values = {table: [dict(row) for row in conn.execute("SELECT * FROM " + table + " ORDER BY rowid")]
                  for table in ("outbox_messages", "review_records", "platform_dispatches", "reconciliations", "destination_readiness")}
    projection = report_workspace_projection(values["outbox_messages"], review_records=values["review_records"],
        dispatches=values["platform_dispatches"], reconciliations=values["reconciliations"], readiness=values["destination_readiness"])
    missing = [r for r in selection["operation_ids"]
               if r not in {i["run_id"] for i in projection["native_edition"]}]
    if missing and ROLLOUT_PATH.is_file():
        rollout = json.loads(ROLLOUT_PATH.read_bytes())
        live_store = rollout.get("store_path")
        if live_store and Path(live_store).resolve() != Path(profile["store_path"]).resolve() and Path(live_store).is_file():
            current = _selected_runtime_projection(live_store, missing)
            projection["native_edition"].extend(i for i in current["native_edition"] if i["run_id"] in missing)
    # Do not let a newer unrelated owner pointer change the configured selected edition.
    projection["owner_edition"] = selection
    artifact = build_news_projection(projection, exported_at_utc=datetime.now(timezone.utc).isoformat(),
                                     embedded_photo_operations=missing)
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    return {"state": "PRODUCER_DELIVERED", "edition_id": selection["edition_id"],
            "articles": len(artifact["native_edition"]), "available": sum(i["availability"] == "AVAILABLE" for i in artifact["native_edition"]),
            "main_adoption": "NOT_VERIFIED", "public_write_performed": False}


def _artifact():
    # Validate one fixed local file at reader admission. Never follow an endpoint path.
    for path in (ARTIFACT_PATH.parent, ARTIFACT_PATH):
        info = path.lstat()
        if path.is_symlink() or getattr(info, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError("CONTENT_INTEGRITY")
    if ARTIFACT_PATH.stat().st_size > 40_000_000:
        raise ValueError("CONTENT_INTEGRITY")
    def unique(pairs):
        result = {}
        for key, data in pairs:
            if key in result:
                raise ValueError("CONTENT_INTEGRITY")
            result[key] = data
        return result
    value = json.loads(ARTIFACT_PATH.read_bytes(), object_pairs_hook=unique)
    if value.get("schema_version") != SCHEMA or value.get("consumer_view") != VIEW or value.get("scope") != "PRIVATE_PREVIEW_ONLY":
        raise ValueError("CONTENT_INTEGRITY")
    _validate_shape(value)
    return value


def _keys(value, allowed):
    if not isinstance(value, dict) or set(value) - set(allowed):
        raise ValueError("CONTENT_INTEGRITY")


def _leaves(value):
    """These allowlisted fields are scalars/lists, never nested private objects."""
    if isinstance(value, dict):
        valid = all(not isinstance(v, dict) and _leaves(v) for v in value.values())
    elif isinstance(value, list):
        valid = all(not isinstance(v, dict) and _leaves(v) for v in value)
    else:
        valid = value is None or type(value) in (str, bool, int) or type(value) is float and math.isfinite(value)
    if not valid:
        raise ValueError("CONTENT_INTEGRITY")
    return True


def _validate_shape(value):
    """Admission checks the documented allowlist; extra private fields fail closed."""
    _keys(value, ("schema_version", "consumer_view", "exported_at_utc", "owner_edition", "native_edition", "scope", "public_write_performed"))
    _keys(value["owner_edition"], ("edition_id", "title", "operation_ids"))
    identities, runs = set(), set()
    for item in value["native_edition"]:
        _keys(item, ("run_id", "article_identity", "article_revision", "availability", "reason", "article", "evidence", "media_assets", "review",
                     "publication", "clocks", "epistemic_state", "editorial_execution", "use_permission"))
        if item.get("article_revision") is not None and not IDENTITY.fullmatch(item["article_revision"]):
            raise ValueError("CONTENT_INTEGRITY")
        if item["run_id"] in runs or item["run_id"] not in value["owner_edition"]["operation_ids"]:
            raise ValueError("CONTENT_INTEGRITY")
        runs.add(item["run_id"])
        if item["article_identity"] is not None:
            if not IDENTITY.fullmatch(item["article_identity"]) or item["article_identity"] in identities:
                raise ValueError("CONTENT_INTEGRITY")
            identities.add(item["article_identity"])
        if item["availability"] not in {"AVAILABLE", "CONTENT_RESTRICTED", "LOCAL_CONTENT_MISSING"}:
            raise ValueError("CONTENT_INTEGRITY")
        if item["availability"] != "AVAILABLE":
            _keys(item, ("run_id", "article_identity", "article_revision", "availability", "reason"))
            continue
        _keys(item["article"], ARTICLE_FIELDS)
        _leaves(item["article"])
        for name in ("title", "dek", "substack_body_markdown"):
            if not isinstance(item["article"][name], str) or not item["article"][name].strip():
                raise ValueError("CONTENT_INTEGRITY")
        _keys(item["review"], ("decision",))
        _keys(item["publication"], ("state", "destinations", "canonical_url", "canonical_public_object_id", "publication_at_utc"))
        canonical_id = item["publication"].get("canonical_public_object_id")
        if canonical_id is not None and (not isinstance(canonical_id, str)
                or not re.fullmatch(r"[1-9][0-9]{0,31}", canonical_id)
                or not _url(item["publication"].get("canonical_url"))
                or not any(d.get("destination") == "substack" and d.get("reconciliation_status") == "RECONCILED_CONFIRMED"
                           for d in item["publication"]["destinations"])):
            raise ValueError("CONTENT_INTEGRITY")
        for destination in item["publication"]["destinations"]:
            _keys(destination, ("destination", "status", "reconciliation_status"))
        _keys(item["clocks"], ("evidence_cutoff_utc", "retained_at_utc", "analysis_at_utc", "current_market_refresh_verified"))
        _keys(item["epistemic_state"], EPISTEMIC_FIELDS)
        _keys(item["editorial_execution"], ("observed_models", "attribution"))
        for model in item["editorial_execution"]["observed_models"]:
            _keys(model, ("role", "stage", "model", "reasoning_effort"))
        _keys(item["use_permission"], ("scope", "public_release_authorized_by_export", "source_expression_reuse_authorized"))
        if (item["use_permission"]["scope"] != "PRIVATE_PREVIEW_ONLY"
                or item["use_permission"]["public_release_authorized_by_export"]
                or item["use_permission"]["source_expression_reuse_authorized"]
                or item["review"]["decision"] != "KEEP"):
            raise ValueError("CONTENT_INTEGRITY")
        for source in item["evidence"]:
            _keys(source, (*SOURCE_FIELDS, "publication_precision", "observation_time_utc", "source_reuse_constraints"))
            _keys(source.get("source_reuse_constraints", {}), (*RIGHTS_FIELDS, "data_terms"))
            _keys(source.get("source_reuse_constraints", {}).get("data_terms", {}),
                  ("url", "required_attribution", "endorsement_granted", "independent_modification_label_required"))
            _source(source)
        for asset in item["media_assets"]:
            _media_permission(asset)
            _keys(asset, (*MEDIA_FIELDS, "source_links", "reader_table", "data_context", "content_type", "content_base64",
                          "preview_content_base64", "preview_content_type", "preview_sha256"))
            if not ASSET_ID.fullmatch(asset["asset_id"]):
                raise ValueError("CONTENT_INTEGRITY")
            if (asset["content_type"] not in {"image/png", "image/jpeg"}
                    or asset.get("preview_content_type", "image/jpeg") not in {"image/png", "image/jpeg"}):
                raise ValueError("CONTENT_INTEGRITY")
            for link in asset["source_links"]:
                _keys(link, ("document_id", "label", "url"))
            _keys(asset["data_context"], ("unit", "subtitle", "comparability_limits", "source_periods"))
            if table := asset.get("reader_table"):
                _keys(table, ("caption", "unit", "columns", "notes", "rows"))
                for row in table["rows"]:
                    _keys(row, ("label", "values"))
    if runs != set(value["owner_edition"]["operation_ids"]):
        raise ValueError("CONTENT_INTEGRITY")


class RetainedNewsReader:
    """In-process adapter: the trusted host supplies Main's SessionAdapter convention.

    Construction opens no listener or store. Auth is checked separately on every
    article, asset and table request; neither request dictionaries nor flags grant access.
    """
    def __init__(self, session_adapter, *, clock=None):
        self._adapter = session_adapter
        self._clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
        self._snapshot = None
        self._assets = {}

    def _error(self, state, status):
        return {"status": status, "headers": dict(HEADERS), "body": {"state": state}}

    def read(self, article_identity, opaque_session):
        if not isinstance(article_identity, str) or not IDENTITY.fullmatch(article_identity):
            return self._error("UNSUPPORTED_SELECTION", 400)
        if not isinstance(opaque_session, str) or not 1 <= len(opaque_session) <= 512:
            return self._error("ACCESS_DENIED", 403)
        try:
            now = self._clock()
            grant = self._adapter.resolve(opaque_session, read_at_utc=now)
            if (not grant or isinstance(grant, dict) or grant.status != "ACTIVE"
                    or type(grant.scopes) is not tuple or SCOPE not in grant.scopes
                    or type(grant.record_ids) is not tuple or article_identity not in grant.record_ids
                    or not _utc(grant.not_before_utc) <= _utc(grant.verified_at_utc) <= _utc(now) < _utc(grant.expires_at_utc)):
                return self._error("ACCESS_DENIED", 403)
        except Exception:
            # A failing trusted adapter is never an authorization bypass.
            return self._error("ACCESS_DENIED", 403)
        try:
            if self._snapshot is None:
                self._snapshot = _artifact()
        except OSError:
            return self._error("LOCAL_CONTENT_MISSING", 503)
        except (ValueError, KeyError, TypeError, AttributeError, IndexError):
            return self._error("CONTENT_INTEGRITY", 409)
        matches = [i for i in self._snapshot["native_edition"] if i["article_identity"] == article_identity]
        if len(matches) != 1:
            return self._error("ARTICLE_NOT_IN_SELECTED_EDITION", 404)
        item = matches[0]
        if item["availability"] != "AVAILABLE":
            return self._error(item["availability"], 403 if item["availability"] == "CONTENT_RESTRICTED" else 503)
        safe = deepcopy(item)
        for asset in safe["media_assets"]:
            asset.pop("content_base64", None)
            asset.pop("preview_content_base64", None)
        return {"status": 200, "headers": dict(HEADERS), "body": {"schema_version": SCHEMA, "consumer_view": VIEW,
            "edition_id": self._snapshot["owner_edition"]["edition_id"], "exported_at_utc": self._snapshot["exported_at_utc"],
            "scope": "PRIVATE_PREVIEW_ONLY", "story": safe}}

    def read_asset(self, article_identity, asset_id, opaque_session):
        response = self.read(article_identity, opaque_session)
        if response["status"] != 200:
            return response
        if not isinstance(asset_id, str) or not ASSET_ID.fullmatch(asset_id):
            return self._error("UNSUPPORTED_SELECTION", 400)
        item = next(i for i in self._snapshot["native_edition"] if i["article_identity"] == article_identity)
        matches = [a for a in item["media_assets"] if a["asset_id"] == asset_id]
        if len(matches) != 1:
            return self._error("ASSET_NOT_IN_SELECTED_STORY", 404)
        asset = matches[0]
        try:
            cache_key = (article_identity, asset_id)
            if cache_key not in self._assets:
                if "content_base64" in asset:
                    raw = base64.b64decode(asset["content_base64"], validate=True)
                else:
                    # Only the trusted configured edition maps IDs to originals.
                    # Request values never participate in a filesystem join.
                    portable = json.loads(SELECTION_PATH.read_bytes())
                    story = next(c for c in portable["native_edition"] if c["article_identity"] == article_identity)
                    original = next(a for a in story["media_assets"] if a["asset_id"] == asset_id and a["sha256"] == asset["sha256"])
                    path = ROOT / original["path"]
                    media_root = SELECTION_PATH.parent
                    if not path.resolve().is_relative_to(media_root.resolve()):
                        raise ValueError("CONTENT_INTEGRITY")
                    for part in (path, *path.parents):
                        if part == media_root.parent:
                            break
                        info = part.lstat()
                        if part.is_symlink() or getattr(info, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT:
                            raise ValueError("CONTENT_INTEGRITY")
                    raw = path.read_bytes()
                if hashlib.sha256(raw).hexdigest() != asset["sha256"]:
                    raise ValueError("CONTENT_INTEGRITY")
                self._assets[cache_key] = raw
            raw = self._assets[cache_key]
        except OSError:
            return self._error("LOCAL_CONTENT_MISSING", 503)
        except (ValueError, KeyError, StopIteration, TypeError):
            return self._error("CONTENT_INTEGRITY", 409)
        return {"status": 200, "headers": {**HEADERS, "Content-Type": asset["content_type"]}, "body": raw}

    def read_table(self, article_identity, asset_id, opaque_session):
        response = self.read(article_identity, opaque_session)
        if response["status"] != 200:
            return response
        if not isinstance(asset_id, str) or not ASSET_ID.fullmatch(asset_id):
            return self._error("UNSUPPORTED_SELECTION", 400)
        table = next((a.get("reader_table") for a in response["body"]["story"]["media_assets"] if a["asset_id"] == asset_id), None)
        return {"status": 200, "headers": dict(HEADERS), "body": table} if table else self._error("TABLE_NOT_IN_SELECTED_STORY", 404)


def local_owner_read(article_identity, *, asset_id=None):
    """OS-owner CLI inspection, not an HTTP authentication adapter or subscriber grant."""
    class LocalOwner:
        def resolve(self, opaque_session, *, read_at_utc):
            return SimpleNamespace(status="ACTIVE", scopes=(SCOPE,), record_ids=(article_identity,),
                not_before_utc="2020-01-01T00:00:00Z", verified_at_utc=read_at_utc, expires_at_utc="2100-01-01T00:00:00Z")
    reader = RetainedNewsReader(LocalOwner())
    return reader.read_asset(article_identity, asset_id, "LOCAL_OS_OWNER") if asset_id else reader.read(article_identity, "LOCAL_OS_OWNER")
