"""Read-only probe registry for Batch B.

Network probes require explicit calls and credentials supplied by caller. No import-time env reads.
No write endpoints, no retry, one request per endpoint family by default.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .credential_redaction_policy import REDACTION_POLICY_ID, redact_text

TASK_LABEL = "TASK_CONTENTOPS_MULTI_PLATFORM_LIVE_FOUNDATION_BATCH_B_OPERATOR_SETUP_TELEGRAM_READONLY_PROOF_AND_PROBE_HARDENING_V0"
WRITE_ENDPOINT_DENYLIST = (
    "sendMessage", "sendPhoto", "sendDocument", "sendMediaGroup", "sendRichMessage",
    "sendRichMessageDraft", "statuses/update", "tweets", "ugcPosts", "videos", "upload",
    "publish", "media_publish", "feed", "insert", "create", "post",
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
    allowed_query_keys: tuple[str, ...] = ()


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


_ALLOWED_PLANS: tuple[ProbePlan, ...] = (
    ProbePlan("telegram_remote_operator", "telegram_bot_identity", "GET", "https", "api.telegram.org", "/bot<redacted>/getMe", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked"),
    ProbePlan("telegram_channel_destination", "telegram_channel_read", "GET", "https", "api.telegram.org", "/bot<redacted>/getChat", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked", ("chat_id",)),
    ProbePlan("x_profile", "x_user_identity", "GET", "https", "api.x.com", "/2/users/me", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked"),
    ProbePlan("linkedin_member_profile", "linkedin_member_identity", "GET", "https", "api.linkedin.com", "/v2/userinfo", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked"),
    ProbePlan("linkedin_organization_page", "linkedin_org_acl", "GET", "https", "api.linkedin.com", "/v2/organizationalEntityAcls", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked", ("q", "role", "projection")),
    ProbePlan("facebook_page", "meta_page_identity", "GET", "https", "graph.facebook.com", "/v20.0/<page-id>", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked", ("fields",)),
    ProbePlan("instagram_professional_account", "instagram_account_identity", "GET", "https", "graph.facebook.com", "/v20.0/<ig-account-id>", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked", ("fields",)),
    ProbePlan("threads_profile", "threads_user_identity", "GET", "https", "graph.threads.net", "/v1.0/me", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked", ("fields",)),
    ProbePlan("tiktok_account", "tiktok_user_info", "GET", "https", "open.tiktokapis.com", "/v2/user/info/", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked", ("fields",)),
    ProbePlan("youtube_channel", "youtube_channel_identity", "GET", "https", "www.googleapis.com", "/youtube/v3/channels", 10, "redirect_disabled_fail_closed", 1, False, False, "official_docs_checked", ("part", "mine", "id")),
    ProbePlan("substack_newsletter", "substack_publication_url_format", "LOCAL", "none", "local", "publication_url_format", 0, "no_network", 0, False, False, "docs_unverified"),
)


_ALLOWED_BY_FAMILY = {plan.endpoint_family: plan for plan in _ALLOWED_PLANS}


def build_probe_plans() -> tuple[ProbePlan, ...]:
    return _ALLOWED_PLANS


def _deny_write_endpoint(path_or_name: str) -> None:
    lowered = path_or_name.lower()
    for denied in WRITE_ENDPOINT_DENYLIST:
        if denied.lower() in lowered:
            raise ValueError("write_endpoint_blocked_by_batch_b_policy")


def _assert_probe_invariants(plan: ProbePlan) -> None:
    allowed = _ALLOWED_BY_FAMILY.get(plan.endpoint_family)
    if allowed != plan:
        raise ValueError("probe_plan_not_in_batch_b_allowlist")
    _deny_write_endpoint(plan.path)
    if plan.method not in {"GET", "LOCAL"}:
        raise ValueError("probe_method_not_read_only")
    if plan.method == "GET" and plan.request_budget != 1:
        raise ValueError("request_budget_must_be_one_for_batch_b")
    if plan.method == "LOCAL" and plan.request_budget != 0:
        raise ValueError("local_probe_budget_must_be_zero")
    if plan.auto_retry:
        raise ValueError("auto_retry_forbidden_for_batch_b")
    if plan.raw_response_persisted:
        raise ValueError("raw_response_persistence_forbidden")
    if plan.method == "GET" and plan.redirect_policy != "redirect_disabled_fail_closed":
        raise ValueError("redirect_policy_must_fail_closed")


def classify_missing_credentials(platform_id: str, endpoint_family: str, plan: ProbePlan, reasons: tuple[str, ...]) -> ProbeResult:
    return ProbeResult(platform_id, endpoint_family, plan.method, plan.scheme, plan.host, plan.path, 0, plan.timeout_seconds, plan.redirect_policy, plan.auto_retry, plan.raw_response_persisted, "blocked_not_attempted", REDACTION_POLICY_ID, reasons)


def build_blocked_probe_report(reasons_by_platform: Mapping[str, tuple[str, ...]] | None = None) -> dict[str, Any]:
    reasons_by_platform = reasons_by_platform or {}
    results = []
    for plan in build_probe_plans():
        _assert_probe_invariants(plan)
        reasons = reasons_by_platform.get(plan.platform_id, ("credential_or_scope_not_verified", "batch_b_live_write_forbidden"))
        results.append(asdict(classify_missing_credentials(plan.platform_id, plan.endpoint_family, plan, reasons)))
    return {"task_label": TASK_LABEL, "raw_response_persisted": False, "auto_retry": False, "results": results}


def _actual_path_matches_template(actual_path: str, template_path: str) -> bool:
    if template_path.startswith("/bot<redacted>/"):
        suffix = template_path.removeprefix("/bot<redacted>")
        if not actual_path.endswith(suffix):
            return False
        token_segment = actual_path[: -len(suffix)] if suffix else actual_path
        return token_segment.startswith("/bot") and len(token_segment) > len("/bot")
    if "<page-id>" in template_path or "<ig-account-id>" in template_path:
        prefix = template_path.split("<", 1)[0]
        return actual_path.startswith(prefix) and len(actual_path) > len(prefix)
    return actual_path == template_path


def _validate_probe_url(plan: ProbePlan, url: str) -> tuple[bool, tuple[str, ...]]:
    parsed = urlparse(url)
    reasons: list[str] = []
    if parsed.scheme != plan.scheme:
        reasons.append("final_scheme_mismatch")
    if parsed.netloc != plan.host:
        reasons.append("final_host_mismatch")
    if not _actual_path_matches_template(parsed.path, plan.path):
        reasons.append("final_path_mismatch")
    query_keys = tuple(sorted(parse_qs(parsed.query, keep_blank_values=True).keys()))
    unexpected = [key for key in query_keys if key not in plan.allowed_query_keys]
    if unexpected:
        reasons.append("query_key_not_allowlisted")
    if parsed.fragment:
        reasons.append("url_fragment_forbidden")
    return not reasons, tuple(reasons)


def run_http_get_probe(plan: ProbePlan, url: str, headers: Mapping[str, str]) -> ProbeResult:
    _assert_probe_invariants(plan)
    ok, reasons = _validate_probe_url(plan, url)
    if not ok:
        return classify_missing_credentials(plan.platform_id, plan.endpoint_family, plan, reasons)
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
