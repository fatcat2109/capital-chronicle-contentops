"""CC-154: site readback in the existing native outbox, before social dispatch.

The Web lane owns rendering/deployment. A candidate is an export of the reviewed
package, never evidence that the site is live. No Substack identity is invented.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of

POLICY = "SITE_FIRST_V1"
SITE = "https://fatcat2109.github.io/capital-chronicle-preview/"
DESTINATION = "internal:site-publication"
AWAITING_OWNER = "SUBSTACK_DRAFT_AWAITING_OWNER"
PENDING_CODE = "PENDING_JIM_EMAIL_CODE"


def site_url(plan):
    # Stable across retries and independent of the Substack draft/public id.
    return SITE + "articles/" + sha256_of(plan["article_identity"])[:32] + "/"


def request_for_site(work_item_id, plan, native_invocation_id=None):
    request = {
        "action": "READBACK", "destination": "site", "surface": "PUBLIC_ARTICLE_SITE",
        "work_item_id": work_item_id, "plan_hash": plan["plan_hash"],
        "expected_identity": "fatcat2109/capital-chronicle-preview",
        "public_object_url": site_url(plan), "article_identity": plan["article_identity"],
        "article_content_sha256": plan["article_content_sha256"],
        "instructions": "Read the exact live article and its public copy hash. A homepage, deployment receipt, missing article or stale copy is not confirmation. No writes.",
    }
    if native_invocation_id:
        request["native_invocation_id"] = native_invocation_id
    request["request_sha256"] = sha256_of(request)
    return request


def candidate(work_item_id, plan):
    """Reuse the public-copy/rights guard and bind the exact reviewed artifact."""
    from live_contentops.published_content_v1 import article_metadata
    metadata = article_metadata(plan)
    root = Path(plan["output_dir"])
    article = root / "article_manifest_v1.json"
    return {
        "schema_version": "contentops.site_publication_candidate.v1",
        "work_item_id": work_item_id, "plan_hash": plan["plan_hash"],
        "article_identity": plan["article_identity"],
        "article_content_sha256": plan["article_content_sha256"],
        "article_manifest_sha256": sha256(article.read_bytes()).hexdigest(),
        "output_dir": str(root.resolve()), "expected_site_url": site_url(plan),
        "metadata": metadata, "site_publication_confirmed": False,
    }


def confirm_site(store, work_item_id, plan, executor):
    """Only a bound native tool observation can unlock the site's URL."""
    identity = request_for_site(work_item_id, plan)
    request = request_for_site(work_item_id, plan, executor.native_invocation_id)
    result = executor(request)
    observation = result.get("native_tool_observation") or {}
    try:
        observed = datetime.fromisoformat(str(observation.get("observed_at_utc", "")).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("EXACT_LIVE_SITE_ARTICLE_READBACK_REQUIRED") from exc
    if (result.get("verified") is not True or result.get("public_object_url") != site_url(plan)
            or result.get("article_identity") != plan["article_identity"]
            or result.get("article_content_sha256") != plan["article_content_sha256"]
            or result.get("observed_identity") != request["expected_identity"]
            or not result.get("native_tool_return_sha256")
            or observed.tzinfo is None or observed > datetime.now(timezone.utc)):
        raise ValueError("EXACT_LIVE_SITE_ARTICLE_READBACK_REQUIRED")
    value = {"schema_version": "contentops.site_publication_readback.v1",
             "work_item_id": work_item_id, "plan_hash": plan["plan_hash"],
             "request_sha256": identity["request_sha256"], "result": result}
    store.register_outbox_message(message_id="site-readback-" + identity["request_sha256"],
        work_item_id=work_item_id, destination=DESTINATION,
        payload=json.dumps(value, sort_keys=True), status="SITE_READBACK_CONFIRMED")
    return site_url(plan)


def confirmed_site(store, work_item_id, plan):
    request = request_for_site(work_item_id, plan)
    row = store.get_outbox_message("site-readback-" + request["request_sha256"])
    if not row or row["status"] != "SITE_READBACK_CONFIRMED":
        return None
    value = json.loads(row["payload"])
    result = value.get("result") or {}
    if (value.get("request_sha256") != request["request_sha256"]
            or result.get("public_object_url") != site_url(plan)
            or result.get("article_content_sha256") != plan["article_content_sha256"]):
        raise ValueError("SITE_READBACK_IDENTITY_CONFLICT")
    return result["public_object_url"]
