"""Read-only probe registry for Batch A.

Network probes require explicit calls and credentials supplied by caller. No import-time env reads.
No write endpoints, no retry, one request per endpoint family by default.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
import json

from .credential_redaction_policy import REDACTION_POLICY_ID, redact_text

TASK_LABEL = "TASK_CONTENTOPS_MULTI_PLATFORM_LIVE_FOUNDATION_BATCH_A_DOCS_CREDENTIALS_BINDINGS_AND_READONLY_PROBES_V0"
WRITE_ENDPOINT_DENYLIST = (
    "sendMessage", "sendPhoto", "sendDocument", "statuses/update", "tweets", "ugcPosts",
    "videos", "upload", "publish", "media_publish", "feed",
)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


@dataclass(frozen=True)
class ProbePlan:
    platform_id: str
    endpoint_family: str
    method: str
    scheme: str
    host: str
    path: str
    timeout_seconds: int
    redirect_policy: str
    request_budget: int
    auto_retry: bool
    raw_response_persisted: bool
    docs_status_required: str


@dataclass(frozen=True)
class ProbeResult:
    platform_id: str
    endpoint_family: str
    method: str
    scheme: str
    host: str
    path: str
    request_count: int
    timeout_seconds: int
    redirect_policy: str
    auto_retry: bool
    raw_response_persisted: bool
    result_classification: str
    redaction_policy_id: str
    blocked_reasons: tuple[str, ...]


def build_probe_plans() -> tuple[ProbePlan, ...]:
    return (
        ProbePlan("telegram_remote_operator", "telegram_bot_identity", "GET", "https", "api.telegram.org", "/bot<redacted>/getMe", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked"),
        ProbePlan("telegram_channel_destination", "telegram_channel_read", "GET", "https", "api.telegram.org", "/bot<redacted>/getChat", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked"),
        ProbePlan("x_profile", "x_user_identity", "GET", "https", "api.x.com", "/2/users/me", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked"),
        ProbePlan("linkedin_member_profile", "linkedin_member_identity", "GET", "https", "api.linkedin.com", "/v2/userinfo", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked"),
        ProbePlan("linkedin_organization_page", "linkedin_org_acl", "GET", "https", "api.linkedin.com", "/v2/organizationalEntityAcls", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked"),
        ProbePlan("facebook_page", "meta_page_identity", "GET", "https", "graph.facebook.com", "/v20.0/<page-id>", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked"),
        ProbePlan("instagram_professional_account", "instagram_account_identity", "GET", "https", "graph.facebook.com", "/v20.0/<ig-account-id>", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked"),
        ProbePlan("threads_profile", "threads_user_identity", "GET", "https", "graph.threads.net", "/v1.0/me", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked"),
        ProbePlan("tiktok_account", "tiktok_user_info", "GET", "https", "open.tiktokapis.com", "/v2/user/info/", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked"),
        ProbePlan("youtube_channel", "youtube_channel_identity", "GET", "https", "www.googleapis.com", "/youtube/v3/channels", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked"),
        ProbePlan("substack_newsletter", "substack_publication_url_format", "LOCAL", "none", "local", "publication_url_format", 0, "no_network", 0, False, False, "docs_unverified"),
    )


def _deny_write_endpoint(path_or_name: str) -> None:
    lowered = path_or_name.lower()
    for denied in WRITE_ENDPOINT_DENYLIST:
        if denied.lower() in lowered:
            raise ValueError("write_endpoint_blocked_by_batch_a_policy")


def classify_missing_credentials(platform_id: str, endpoint_family: str, plan: ProbePlan, reasons: tuple[str, ...]) -> ProbeResult:
    return ProbeResult(platform_id, endpoint_family, plan.method, plan.scheme, plan.host, plan.path, 0, plan.timeout_seconds, plan.redirect_policy, plan.auto_retry, plan.raw_response_persisted, "blocked_not_attempted", REDACTION_POLICY_ID, reasons)


def build_blocked_probe_report(reasons_by_platform: Mapping[str, tuple[str, ...]] | None = None) -> dict[str, Any]:
    reasons_by_platform = reasons_by_platform or {}
    results = []
    for plan in build_probe_plans():
        _deny_write_endpoint(plan.path)
        reasons = reasons_by_platform.get(plan.platform_id, ("credential_or_scope_not_verified", "batch_a_live_write_forbidden"))
        results.append(asdict(classify_missing_credentials(plan.platform_id, plan.endpoint_family, plan, reasons)))
    return {"task_label": TASK_LABEL, "raw_response_persisted": False, "auto_retry": False, "results": results}


def run_http_get_probe(plan: ProbePlan, url: str, headers: Mapping[str, str]) -> ProbeResult:
    _deny_write_endpoint(plan.path)
    if plan.request_budget != 1:
        raise ValueError("request_budget_must_be_one_for_batch_a")
    parsed = urlparse(url)
    if parsed.scheme != plan.scheme or parsed.netloc != plan.host:
        return classify_missing_credentials(plan.platform_id, plan.endpoint_family, plan, ("final_host_or_scheme_mismatch",))
    request = Request(url, headers=dict(headers), method="GET")
    opener = build_opener(NoRedirect)
    try:
        with opener.open(request, timeout=plan.timeout_seconds) as response:
            status = getattr(response, "status", None)
            classification = "read_only_probe_pass" if status and 200 <= int(status) < 300 else "read_only_probe_non_2xx"
    except HTTPError as exc:
        classification = "read_only_probe_http_error_redacted_" + str(exc.code)
    except (URLError, TimeoutError, OSError) as exc:
        classification = "read_only_probe_transport_error_redacted:" + redact_text(exc.__class__.__name__)
    return ProbeResult(plan.platform_id, plan.endpoint_family, plan.method, plan.scheme, plan.host, plan.path, 1, plan.timeout_seconds, plan.redirect_policy, False, False, classification, REDACTION_POLICY_ID, ())
