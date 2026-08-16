"""Versioned Final Daily App destination/surface transport and readiness authority.

This module distinguishes platform from surface, permits exactly one write transport per
surface, and performs only bounded read-only identity probes.  It never prints or persists
tokens, webhook URLs, cookies, browser storage, authorization headers, or raw responses.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

from live_contentops.browser_interaction_budget_v1 import (
    BROWSER_INTERACTION_BUDGET_V1,
    browser_activity,
    record_browser_interaction_event,
)


REGISTRY_VERSION = "contentops.destination_transport_registry.v2"
IDENTITY_AUTHORITY_VERSION = "contentops.destination_identity_authority.v2"
V1_QUALITY_PROBATION_POLICY_ID = "QUALITY_PROBATION_FOUR_WINDOW_V1"
PUBLISHING_CDP_PORT = 9223
INGESTION_ONLY_CDP_PORT = 9222

READY_AUTHENTICATED = "READY_AUTHENTICATED"
READY_NON_BROWSER_BINDING = "READY_NON_BROWSER_BINDING"
READY_OFFICIAL_MEMBER_API = "READY_OFFICIAL_MEMBER_API"
READY_STATES = frozenset({
    READY_AUTHENTICATED, READY_NON_BROWSER_BINDING, READY_OFFICIAL_MEMBER_API,
})
READINESS_STATES = frozenset({
    *READY_STATES,
    "REAUTH_REQUIRED",
    "AUTH_INVALID",
    "IDENTITY_MISMATCH",
    "PERMISSION_MISSING",
    "SESSION_UNAVAILABLE",
    "TRANSPORT_UNAVAILABLE",
    "TRANSIENT_DEGRADED",
    "CAPABILITY_UNSUPPORTED",
    "TOKEN_EXPIRING",
    "AUTH_UNAVAILABLE",
    "LAST_VERIFIED_READY",
    "STALE_NEEDS_JIT_VERIFICATION",
})


@dataclass(frozen=True)
class SurfaceTransport:
    surface: str
    platform: str
    transport_type: str
    adapter: str
    destination_key: str
    expected_identity: str
    publishing_port: Optional[int] = None
    tier1_write_enabled: bool = True
    canonical_url_dependency: Optional[str] = None
    expected_identity_kind: str = "PUBLIC_IDENTITY"
    expected_stable_id: Optional[str] = None
    expected_public_handle: Optional[str] = None
    expected_domain: Optional[str] = None


_SURFACES = (
    SurfaceTransport(
        "SUBSTACK_ARTICLE", "substack", "EDGE_CDP",
        "edge_cdp_publishing_adapter_v1.publish_substack_article_via_edge",
        "substack", "capitalchronicle.substack.com", PUBLISHING_CDP_PORT,
        expected_identity_kind="DOMAIN",
        expected_domain="capitalchronicle.substack.com",
    ),
    SurfaceTransport(
        "X_POST", "x", "EDGE_CDP", "edge_cdp_publishing_adapter_v1.publish_x_post_via_edge",
        "x", "@Capitalnicle", PUBLISHING_CDP_PORT, canonical_url_dependency="SUBSTACK_ARTICLE",
        expected_identity_kind="PUBLIC_HANDLE", expected_public_handle="@Capitalnicle",
    ),
    SurfaceTransport(
        "X_THREAD", "x", "EDGE_CDP", "edge_cdp_publishing_adapter_v1.publish_x_post_via_edge+publish_x_reply_via_edge",
        "x", "@Capitalnicle", PUBLISHING_CDP_PORT, canonical_url_dependency="SUBSTACK_ARTICLE",
        expected_identity_kind="PUBLIC_HANDLE", expected_public_handle="@Capitalnicle",
    ),
    SurfaceTransport(
        "LINKEDIN_POST", "linkedin", "OFFICIAL_MEMBER_API",
        "linkedin_official_member_api_v1.LinkedInOfficialMemberApiTransportV1",
        "linkedin", "linkedin:jimcc",
        canonical_url_dependency="SUBSTACK_ARTICLE",
        expected_identity_kind="PUBLIC_IDENTITY", expected_public_handle="linkedin:jimcc",
    ),
    SurfaceTransport(
        "YOUTUBE_COMMUNITY_POST", "youtube", "EDGE_CDP",
        "edge_cdp_publishing_adapter_v1.publish_youtube_community_post_via_edge",
        "youtube", "@CapitalChronicleYouTube", PUBLISHING_CDP_PORT,
        canonical_url_dependency="SUBSTACK_ARTICLE",
        expected_identity_kind="PUBLIC_HANDLE",
        expected_public_handle="@CapitalChronicleYouTube",
    ),
    SurfaceTransport(
        "TELEGRAM_CHANNEL_POST", "telegram", "BOT_API", "telegram_live_adapter_v6.execute_telegram_photo",
        "telegram", "@CapitalChronicle", canonical_url_dependency="SUBSTACK_ARTICLE",
        expected_identity_kind="PUBLIC_HANDLE", expected_public_handle="@CapitalChronicle",
    ),
    SurfaceTransport(
        "DISCORD_ANNOUNCEMENT", "discord", "WEBHOOK_API", "discord_live_adapter_v6.execute_discord_post",
        "discord", "discord_channel:1519311669216673802", canonical_url_dependency="SUBSTACK_ARTICLE",
        expected_identity_kind="STABLE_ID", expected_stable_id="1519311669216673802",
    ),
    SurfaceTransport(
        "FACEBOOK_PAGE_POST", "facebook_page", "META_GRAPH_API", "facebook_page_adapter_v6.execute_facebook_photo",
        "facebook_page", "Capital Chronicle", canonical_url_dependency="SUBSTACK_ARTICLE",
        expected_identity_kind="STABLE_ID",
        expected_stable_id="106091951705748",
    ),
    SurfaceTransport(
        "INSTAGRAM_BUSINESS_POST", "instagram_business", "META_GRAPH_API", "instagram_adapter_v6.execute_instagram_post",
        "instagram_business", "official.capitalchronicle", canonical_url_dependency="SUBSTACK_ARTICLE",
        expected_identity_kind="PUBLIC_HANDLE", expected_public_handle="official.capitalchronicle",
    ),
    SurfaceTransport(
        "THREADS_POST", "threads", "THREADS_API", "threads_adapter_v6.execute_threads_post",
        "threads", "official.capitalchronicle", canonical_url_dependency="SUBSTACK_ARTICLE",
        expected_identity_kind="PUBLIC_HANDLE", expected_public_handle="official.capitalchronicle",
    ),
    # Future video surfaces stay explicit and cannot be mistaken for the Tier-1 Community post.
    SurfaceTransport(
        "YOUTUBE_VIDEO", "youtube", "YOUTUBE_DATA_API", "future:youtube.videos.insert",
        "youtube_video", "@CapitalChronicleYouTube", tier1_write_enabled=False,
        expected_identity_kind="PUBLIC_HANDLE", expected_public_handle="@CapitalChronicleYouTube",
    ),
    SurfaceTransport(
        "YOUTUBE_SHORT", "youtube", "YOUTUBE_DATA_API", "future:youtube.videos.insert",
        "youtube_short", "@CapitalChronicleYouTube", tier1_write_enabled=False,
        expected_identity_kind="PUBLIC_HANDLE", expected_public_handle="@CapitalChronicleYouTube",
    ),
)

SURFACE_REGISTRY = {row.surface: row for row in _SURFACES}
TIER1_SURFACES = (
    "SUBSTACK_ARTICLE", "X_THREAD", "LINKEDIN_POST", "YOUTUBE_COMMUNITY_POST",
    "TELEGRAM_CHANNEL_POST", "DISCORD_ANNOUNCEMENT", "FACEBOOK_PAGE_POST",
    "INSTAGRAM_BUSINESS_POST", "THREADS_POST",
)
DESTINATION_TO_SURFACE = {
    "substack": "SUBSTACK_ARTICLE",
    "x": "X_THREAD",
    "linkedin": "LINKEDIN_POST",
    "youtube": "YOUTUBE_COMMUNITY_POST",
    "telegram": "TELEGRAM_CHANNEL_POST",
    "discord": "DISCORD_ANNOUNCEMENT",
    "facebook_page": "FACEBOOK_PAGE_POST",
    "instagram_business": "INSTAGRAM_BUSINESS_POST",
    "threads": "THREADS_POST",
}

# Quality-probation V1 is one canonical article plus these exact eight derivative
# surfaces. YouTube here means Community; video/Short surfaces remain V2-only.
V1_REQUIRED_DERIVATIVE_DESTINATIONS = (
    "telegram",
    "x",
    "discord",
    "linkedin",
    "facebook_page",
    "instagram_business",
    "threads",
    "youtube",
)
V1_REQUIRED_PUBLICATION_DESTINATIONS = (
    "substack",
    *V1_REQUIRED_DERIVATIVE_DESTINATIONS,
)


def canonical_transport_registry() -> dict[str, Any]:
    rows = [asdict(SURFACE_REGISTRY[surface]) for surface in sorted(SURFACE_REGISTRY)]
    return {
        "schema_version": REGISTRY_VERSION,
        "registry_version": REGISTRY_VERSION,
        "identity_authority_version": IDENTITY_AUTHORITY_VERSION,
        "surfaces": rows,
        "tier1_surfaces": list(TIER1_SURFACES),
        "v1_required_publication_destinations": list(
            V1_REQUIRED_PUBLICATION_DESTINATIONS
        ),
        "publishing_cdp_port": PUBLISHING_CDP_PORT,
        "ingestion_only_cdp_port": INGESTION_ONLY_CDP_PORT,
        "chrome_publishing_allowed": False,
        "silent_transport_fallback_allowed": False,
        "runtime_binding_is_identity_authority": False,
        "youtube_community_is_video_surface": False,
        "linkedin_edge_cdp_probe_allowed": False,
        "linkedin_runtime_state": "OFFICIAL_MEMBER_API_LOCAL_AUTH_METADATA",
    }


def registration_for_destination(destination: str) -> SurfaceTransport:
    surface = DESTINATION_TO_SURFACE.get(str(destination))
    if not surface:
        raise ValueError(f"destination_transport_unregistered:{destination}")
    return SURFACE_REGISTRY[surface]


def validate_registry() -> None:
    if len(SURFACE_REGISTRY) != len(_SURFACES):
        raise RuntimeError("duplicate_surface_transport_registration")
    if set(TIER1_SURFACES) - set(SURFACE_REGISTRY):
        raise RuntimeError("tier1_surface_transport_missing")
    if set(V1_REQUIRED_PUBLICATION_DESTINATIONS) != set(DESTINATION_TO_SURFACE):
        raise RuntimeError("v1_required_publication_destination_mismatch")
    for surface in TIER1_SURFACES:
        row = SURFACE_REGISTRY[surface]
        if not any((row.expected_stable_id, row.expected_public_handle, row.expected_domain)):
            raise RuntimeError(f"owner_identity_pin_missing:{surface}")
        if row.transport_type == "EDGE_CDP" and row.publishing_port != PUBLISHING_CDP_PORT:
            raise RuntimeError(f"edge_surface_not_locked_to_9223:{surface}")
    if SURFACE_REGISTRY["YOUTUBE_COMMUNITY_POST"].transport_type != "EDGE_CDP":
        raise RuntimeError("youtube_community_transport_must_be_edge_cdp")
    if SURFACE_REGISTRY["YOUTUBE_VIDEO"].tier1_write_enabled:
        raise RuntimeError("youtube_video_must_not_be_tier1_write_enabled")


class _ProbeHTTPError(RuntimeError):
    def __init__(self, status_code: Optional[int], error_class: str) -> None:
        self.status_code = status_code
        self.error_class = error_class
        super().__init__(error_class)


def _json_get(url: str, *, timeout_seconds: float = 8.0) -> Mapping[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "CapitalChronicle-ContentOps/1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read(512 * 1024)
    except urllib.error.HTTPError as exc:
        raise _ProbeHTTPError(int(exc.code), "HTTPError") from None
    except Exception as exc:  # URLs/credentials are intentionally excluded from the error.
        raise _ProbeHTTPError(None, type(exc).__name__) from None
    try:
        decoded = json.loads(raw)
    except Exception:
        raise _ProbeHTTPError(None, "MalformedJSON") from None
    if not isinstance(decoded, Mapping):
        raise _ProbeHTTPError(None, "NonMappingJSON")
    return decoded


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalized_identity(value: Any) -> str:
    return " ".join(str(value or "").strip().split()).casefold()


def _normalized_handle(value: Any) -> str:
    return _normalized_identity(value).lstrip("@")


def _normalized_domain(value: Any) -> str:
    raw = str(value or "").strip()
    if "://" in raw:
        raw = urllib.parse.urlparse(raw).netloc
    return raw.rstrip(".").casefold()


def _identity_pin_match(
    registration: SurfaceTransport,
    *,
    observed_stable_id: Any = None,
    observed_public_handle: Any = None,
    observed_domain: Any = None,
) -> tuple[bool, dict[str, bool]]:
    """Match provider/browser observations only against repository-owned identity pins."""
    checks: dict[str, bool] = {}
    if registration.expected_stable_id is not None:
        checks["stable_id_match"] = (
            bool(str(observed_stable_id or ""))
            and str(observed_stable_id) == registration.expected_stable_id
        )
    if registration.expected_public_handle is not None:
        checks["public_handle_match"] = (
            bool(str(observed_public_handle or ""))
            and _normalized_handle(observed_public_handle)
            == _normalized_handle(registration.expected_public_handle)
        )
    if registration.expected_domain is not None:
        checks["domain_match"] = (
            bool(str(observed_domain or ""))
            and _normalized_domain(observed_domain)
            == _normalized_domain(registration.expected_domain)
        )
    # Registry validation guarantees at least one independent owner pin. Missing or
    # mismatched observations therefore fail closed; request/env bindings are not inputs.
    return bool(checks) and all(checks.values()), checks


def _base_row(registration: SurfaceTransport, *, state: str, identity: Optional[str],
              identity_match: bool, probe_kind: str, detail: Mapping[str, Any]) -> dict[str, Any]:
    if state not in READINESS_STATES:
        raise ValueError(f"readiness_state_invalid:{state}")
    return {
        "surface": registration.surface,
        "platform": registration.platform,
        "transport_registry_version": REGISTRY_VERSION,
        "identity_authority_version": IDENTITY_AUTHORITY_VERSION,
        "transport_type": registration.transport_type,
        "readiness_state": state,
        "destination_identity": identity,
        "identity_match": bool(identity_match),
        "write_eligible": state in READY_STATES,
        "probe_kind": probe_kind,
        "probed_at_utc": _now_iso(),
        "sanitized_detail": dict(detail),
    }


def _error_state(error: _ProbeHTTPError) -> str:
    if error.status_code == 400:
        return "AUTH_INVALID"
    if error.status_code == 401:
        return "AUTH_INVALID"
    if error.status_code == 403:
        return "PERMISSION_MISSING"
    return "TRANSIENT_DEGRADED"


class DestinationReadinessManager:
    """Passive idle readiness plus exact destination-only JIT verification."""

    def __init__(self, *, store: Any = None, env: Mapping[str, str] | None = None,
                 edge_runtime_ensurer: Any = None, linkedin_auth_root: Any = None,
                 linkedin_transport: Any = None) -> None:
        validate_registry()
        self.store = store
        self.env = os.environ if env is None else env
        self.edge_runtime_ensurer = edge_runtime_ensurer
        self.linkedin_auth_root = linkedin_auth_root
        self.linkedin_transport = linkedin_transport

    def _linkedin_probe(self, registration: SurfaceTransport) -> dict[str, Any]:
        """Use secure local auth metadata only; never navigate or poll linkedin.com."""
        if self.linkedin_transport is None:
            from live_contentops.linkedin_official_member_api_v1 import (
                DEFAULT_AUTH_ROOT,
                LinkedInOfficialMemberApiTransportV1,
            )
            self.linkedin_transport = LinkedInOfficialMemberApiTransportV1(
                auth_root=self.linkedin_auth_root or DEFAULT_AUTH_ROOT
            )
        result = dict(self.linkedin_transport.readiness())
        official_state = str(result.get("state") or "AUTH_UNAVAILABLE")
        state = {
            "READY_OFFICIAL_MEMBER_API": READY_NON_BROWSER_BINDING,
            "TOKEN_EXPIRING": "TRANSIENT_DEGRADED",
            "REAUTH_REQUIRED": "REAUTH_REQUIRED",
            "AUTH_UNAVAILABLE": "SESSION_UNAVAILABLE",
        }.get(official_state, "SESSION_UNAVAILABLE")
        authenticated = bool(result.get("authenticated"))
        return _base_row(
            registration,
            state=state,
            identity=str(result.get("safe_identity") or "") or None,
            identity_match=authenticated,
            probe_kind="OFFICIAL_MEMBER_API_LOCAL_AUTH_METADATA",
            detail={
                "authenticated": authenticated,
                "official_api_state": official_state,
                "expiry_at_utc": result.get("expiry_at_utc"),
                "days_remaining": result.get("days_remaining"),
                "readback_capability": result.get("readback_capability"),
                "secure_store_binding": result.get("secure_store_binding"),
                "cdp_navigation_performed": False,
                "network_probe_performed": False,
            },
        )

    def _browser_probe(self, registration: SurfaceTransport) -> dict[str, Any]:
        from live_contentops.edge_cdp_publishing_adapter_v1 import (
            probe_authenticated_platform_session,
            probe_youtube_community_surface_via_edge,
        )
        from live_contentops.publishing_profile_registry_v1 import browser_doctor

        doctor = browser_doctor(env=self.env)
        recovery_status = None
        if (
            doctor.get("status") != "READY_TO_ATTACH"
            and callable(self.edge_runtime_ensurer)
        ):
            try:
                # Launch a blank canonical window only. The exact destination probe below owns
                # the sole platform navigation for this attempt.
                try:
                    recovered = dict(self.edge_runtime_ensurer(urls=()) or {})
                except TypeError:
                    recovered = dict(self.edge_runtime_ensurer() or {})
                recovery_status = str(recovered.get("status") or "UNKNOWN")
                doctor = browser_doctor(env=self.env)
            except Exception as exc:
                recovery_status = f"FAILED:{type(exc).__name__}"
        if doctor.get("status") != "READY_TO_ATTACH" or doctor.get("recommended_cdp_port") != PUBLISHING_CDP_PORT:
            return _base_row(
                registration, state="TRANSPORT_UNAVAILABLE", identity=None,
                identity_match=False, probe_kind="EDGE_CDP_IDENTITY",
                detail={"edge_runtime_status": str(doctor.get("status") or "UNAVAILABLE"),
                        "edge_recovery_status": recovery_status},
            )
        try:
            observed = probe_authenticated_platform_session(
                PUBLISHING_CDP_PORT, registration.destination_key
            )
            if registration.surface == "YOUTUBE_COMMUNITY_POST":
                community = probe_youtube_community_surface_via_edge(
                    cdp_port=PUBLISHING_CDP_PORT,
                    expected_handle=str(registration.expected_public_handle),
                )
                authenticated = bool(observed.get("authenticated"))
                active_channel_id = str(observed.get("destination_stable_id") or "")
                canonical_channel_id = str(community.get("canonical_channel_id") or "")
                handle_match = bool(community.get("channel_identity_verified"))
                stable_route_match = bool(
                    active_channel_id
                    and canonical_channel_id
                    and active_channel_id == canonical_channel_id
                )
                identity_match = handle_match and stable_route_match
                identity = str(observed.get("destination_identity") or "") or None
                if identity_match:
                    identity = registration.expected_public_handle
                pin_checks = {
                    "public_handle_match": handle_match,
                    "authenticated_channel_matches_pinned_handle_route": stable_route_match,
                }
            else:
                authenticated = bool(observed.get("authenticated"))
                identity = str(observed.get("destination_identity") or "") or None
                if registration.surface == "SUBSTACK_ARTICLE":
                    observed_domain = str(observed.get("page_domain") or "")
                    identity_match, pin_checks = _identity_pin_match(
                        registration, observed_domain=observed_domain,
                    )
                    identity = observed_domain or identity
                else:
                    identity_match, pin_checks = _identity_pin_match(
                        registration, observed_public_handle=identity,
                    )
            if not authenticated:
                state = "REAUTH_REQUIRED"
            elif not identity_match:
                state = "IDENTITY_MISMATCH"
            else:
                state = READY_AUTHENTICATED
            return _base_row(
                registration, state=state, identity=identity, identity_match=identity_match,
                probe_kind="EDGE_CDP_IDENTITY",
                detail={
                    "edge_runtime_status": "READY_TO_ATTACH",
                    "edge_recovery_status": recovery_status,
                    "authenticated": authenticated,
                    "login_control_detected": bool(observed.get("login_control_detected")),
                    "owner_pin_match": pin_checks,
                },
            )
        except Exception as exc:
            return _base_row(
                registration, state="TRANSIENT_DEGRADED", identity=None,
                identity_match=False, probe_kind="EDGE_CDP_IDENTITY",
                detail={"error_class": type(exc).__name__},
            )

    def _telegram_probe(self, registration: SurfaceTransport) -> dict[str, Any]:
        token = str(self.env.get("TELEGRAM_BOT_TOKEN") or self.env.get("TEST_TELEGRAM_BOT_TOKEN") or "")
        chat_id = str(self.env.get("TELEGRAM_TARGET_CHAT_ID") or self.env.get("TELEGRAM_CHAT_ID") or self.env.get("TELEGRAM_CHANNEL_ID") or self.env.get("TEST_TELEGRAM_CHANNEL") or "")
        if not token or not chat_id:
            return _base_row(registration, state="SESSION_UNAVAILABLE", identity=None,
                             identity_match=False, probe_kind="TELEGRAM_BOT_API_IDENTITY",
                             detail={"binding_configured": False})
        try:
            bot = _json_get(f"https://api.telegram.org/bot{token}/getMe")
            chat = _json_get(
                f"https://api.telegram.org/bot{token}/getChat?chat_id={urllib.parse.quote(chat_id)}"
            )
            bot_ok = bot.get("ok") is True
            chat_result = chat.get("result") if isinstance(chat.get("result"), Mapping) else {}
            observed_handle = (
                "@" + str(chat_result.get("username") or "")
                if chat_result.get("username") else None
            )
            observed_id = str(chat_result.get("id") or "") or None
            pin_match, pin_checks = _identity_pin_match(
                registration,
                observed_stable_id=observed_id,
                observed_public_handle=observed_handle,
            )
            identity_match = bot_ok and bool(chat_result) and pin_match
            state = READY_NON_BROWSER_BINDING if identity_match else "IDENTITY_MISMATCH"
            return _base_row(registration, state=state, identity=observed_handle or observed_id,
                             identity_match=identity_match, probe_kind="TELEGRAM_BOT_API_IDENTITY",
                             detail={"bot_identity_verified": bot_ok,
                                     "chat_access_verified": bool(chat_result),
                                     "owner_pin_match": pin_checks})
        except _ProbeHTTPError as exc:
            return _base_row(registration, state=_error_state(exc), identity=None,
                             identity_match=False, probe_kind="TELEGRAM_BOT_API_IDENTITY",
                             detail={"error_class": exc.error_class, "http_status": exc.status_code})

    def _discord_probe(self, registration: SurfaceTransport) -> dict[str, Any]:
        webhook = str(
            self.env.get("DISCORD_ANNOUNCEMENTS_WEBHOOK_URL")
            or self.env.get("DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK")
            or self.env.get("DISCORD_WEBHOOK_URL")
            or ""
        )
        if not webhook:
            return _base_row(registration, state="SESSION_UNAVAILABLE", identity=None,
                             identity_match=False, probe_kind="DISCORD_WEBHOOK_IDENTITY",
                             detail={"binding_configured": False})
        try:
            data = _json_get(webhook)
            channel_id = str(data.get("channel_id") or "")
            identity_match, pin_checks = _identity_pin_match(
                registration, observed_stable_id=channel_id,
            )
            state = READY_NON_BROWSER_BINDING if identity_match else "IDENTITY_MISMATCH"
            return _base_row(registration, state=state,
                             identity=f"discord_channel:{channel_id}" if channel_id else None,
                             identity_match=identity_match, probe_kind="DISCORD_WEBHOOK_IDENTITY",
                             detail={"webhook_identity_verified": bool(data.get("id")),
                                     "channel_identity_verified": identity_match,
                                     "owner_pin_match": pin_checks})
        except _ProbeHTTPError as exc:
            return _base_row(registration, state=_error_state(exc), identity=None,
                             identity_match=False, probe_kind="DISCORD_WEBHOOK_IDENTITY",
                             detail={"error_class": exc.error_class, "http_status": exc.status_code})

    def _graph_probe(self, registration: SurfaceTransport) -> dict[str, Any]:
        if registration.surface == "FACEBOOK_PAGE_POST":
            object_id = str(self.env.get("FACEBOOK_PAGE_ID") or "")
            token = str(self.env.get("FACEBOOK_PAGE_ACCESS_TOKEN") or self.env.get("META_ACCESS_TOKEN") or "")
            fields = "id,name"
        elif registration.surface == "INSTAGRAM_BUSINESS_POST":
            object_id = str(self.env.get("INSTAGRAM_BUSINESS_ACCOUNT_ID") or self.env.get("INSTAGRAM_IG_ID") or "")
            token = str(self.env.get("INSTAGRAM_ACCESS_TOKEN") or self.env.get("META_ACCESS_TOKEN") or "")
            fields = "id,username"
        else:
            object_id = str(self.env.get("THREADS_USER_ID") or "")
            token = str(self.env.get("THREADS_USER_ACCESS_TOKEN") or self.env.get("THREADS_ACCESS_TOKEN") or "")
            fields = "id,username"
        if not object_id or not token:
            return _base_row(registration, state="SESSION_UNAVAILABLE", identity=None,
                             identity_match=False, probe_kind="OFFICIAL_API_IDENTITY",
                             detail={"binding_configured": False})
        if registration.surface == "THREADS_POST":
            from live_contentops.threads_adapter_v6 import THREADS_GRAPH_VERSION as graph_version
            host = "graph.threads.net"
        else:
            from live_contentops.facebook_page_adapter_v6 import GRAPH_VERSION as graph_version
            host = "graph.facebook.com"
        url = f"https://{host}/{graph_version}/{urllib.parse.quote(object_id)}?fields={fields}&access_token={urllib.parse.quote(token)}"
        try:
            data = _json_get(url)
            observed_id = str(data.get("id") or "")
            display = str(data.get("username") or data.get("name") or observed_id)
            identity_match, pin_checks = _identity_pin_match(
                registration,
                observed_stable_id=observed_id,
                observed_public_handle=display,
            )
            state = READY_NON_BROWSER_BINDING if identity_match else "IDENTITY_MISMATCH"
            return _base_row(registration, state=state, identity=display or None,
                             identity_match=identity_match, probe_kind="OFFICIAL_API_IDENTITY",
                             detail={"object_id_matches_owner_pin": pin_checks.get("stable_id_match"),
                                     "identity_field_present": bool(display),
                                     "owner_pin_match": pin_checks})
        except _ProbeHTTPError as exc:
            return _base_row(registration, state=_error_state(exc), identity=None,
                             identity_match=False, probe_kind="OFFICIAL_API_IDENTITY",
                             detail={"error_class": exc.error_class, "http_status": exc.status_code})

    def probe_surface(self, surface: str) -> dict[str, Any]:
        """Active exact-surface verification. Never call this from idle/global refresh."""
        registration = SURFACE_REGISTRY[surface]
        if registration.surface == "LINKEDIN_POST":
            return self._linkedin_probe(registration)
        if not registration.tier1_write_enabled:
            return _base_row(registration, state="CAPABILITY_UNSUPPORTED", identity=None,
                             identity_match=False, probe_kind="REGISTRY_CAPABILITY",
                             detail={"tier1_write_enabled": False})
        if registration.transport_type == "EDGE_CDP":
            return self._browser_probe(registration)
        if registration.surface == "TELEGRAM_CHANNEL_POST":
            return self._telegram_probe(registration)
        if registration.surface == "DISCORD_ANNOUNCEMENT":
            return self._discord_probe(registration)
        return self._graph_probe(registration)

    def _persist(self, row: Mapping[str, Any], *, persist: bool) -> dict[str, Any]:
        result = dict(row)
        if persist and self.store is not None:
            self.store.upsert_destination_readiness(row=result)
        return result

    def _previous_readiness(self, surface: str) -> dict[str, Any]:
        if self.store is None:
            return {}
        return next(
            (dict(row) for row in self.store.list_destination_readiness() if row["surface"] == surface),
            {},
        )

    def passive_surface(self, surface: str, *, persist: bool = True) -> dict[str, Any]:
        """Local/process/cached-metadata readiness only; never opens or navigates a page."""

        registration = SURFACE_REGISTRY[surface]
        previous = self._previous_readiness(surface)
        previous_detail = previous.get("sanitized_detail") or previous.get("sanitized_detail_json")
        if isinstance(previous_detail, str):
            try:
                previous_detail = json.loads(previous_detail)
            except (TypeError, ValueError):
                previous_detail = {}
        previous_detail = dict(previous_detail) if isinstance(previous_detail, Mapping) else {}
        previous_kind = str(previous.get("probe_kind") or "")
        last_active_proof = (
            previous_detail.get("last_active_proof_at_utc")
            if previous_kind == "PASSIVE_LOCAL_AND_CACHED_METADATA"
            else previous.get("probed_at_utc")
        )
        previous_state = str(previous.get("readiness_state") or "")
        prior_jit_attempt_identity = previous_detail.get("jit_attempt_identity")

        if registration.surface == "LINKEDIN_POST":
            # This implementation reads DPAPI-backed metadata/expiry only and performs no
            # provider call or CDP navigation.
            row = self._linkedin_probe(registration)
            if prior_jit_attempt_identity:
                row["sanitized_detail"]["jit_attempt_identity"] = prior_jit_attempt_identity
            return self._persist(row, persist=persist)

        if registration.transport_type == "EDGE_CDP":
            from live_contentops.publishing_profile_registry_v1 import browser_doctor

            doctor = browser_doctor(env=self.env)
            transport_available = bool(
                doctor.get("status") == "READY_TO_ATTACH"
                and doctor.get("recommended_cdp_port") == PUBLISHING_CDP_PORT
            )
            if previous_state in {"REAUTH_REQUIRED", "AUTH_INVALID", "IDENTITY_MISMATCH"}:
                state = previous_state
            elif not transport_available:
                state = "TRANSPORT_UNAVAILABLE"
            elif last_active_proof:
                state = "LAST_VERIFIED_READY"
            else:
                state = "STALE_NEEDS_JIT_VERIFICATION"
            return self._persist(_base_row(
                registration,
                state=state,
                identity=str(previous.get("destination_identity") or "") or None,
                identity_match=False,
                probe_kind="PASSIVE_LOCAL_AND_CACHED_METADATA",
                detail={
                    "edge_process_profile_cdp_available": transport_available,
                    "last_active_proof_at_utc": last_active_proof,
                    "active_probe_performed": False,
                    "navigation_performed": False,
                    "jit_attempt_identity": prior_jit_attempt_identity,
                },
            ), persist=persist)

        binding_configured = False
        if registration.surface == "TELEGRAM_CHANNEL_POST":
            binding_configured = bool(
                self.env.get("TELEGRAM_BOT_TOKEN")
                and (self.env.get("TELEGRAM_TARGET_CHAT_ID") or self.env.get("TELEGRAM_CHAT_ID") or self.env.get("TELEGRAM_CHANNEL_ID"))
            )
        elif registration.surface == "DISCORD_ANNOUNCEMENT":
            binding_configured = bool(
                self.env.get("DISCORD_ANNOUNCEMENTS_WEBHOOK_URL")
                or self.env.get("DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK")
                or self.env.get("DISCORD_WEBHOOK_URL")
            )
        elif registration.surface == "FACEBOOK_PAGE_POST":
            binding_configured = bool(
                self.env.get("FACEBOOK_PAGE_ID")
                and (self.env.get("FACEBOOK_PAGE_ACCESS_TOKEN") or self.env.get("META_ACCESS_TOKEN"))
            )
        elif registration.surface == "INSTAGRAM_BUSINESS_POST":
            binding_configured = bool(
                (self.env.get("INSTAGRAM_BUSINESS_ACCOUNT_ID") or self.env.get("INSTAGRAM_IG_ID"))
                and (self.env.get("INSTAGRAM_ACCESS_TOKEN") or self.env.get("META_ACCESS_TOKEN"))
            )
        elif registration.surface == "THREADS_POST":
            binding_configured = bool(
                self.env.get("THREADS_USER_ID")
                and (self.env.get("THREADS_USER_ACCESS_TOKEN") or self.env.get("THREADS_ACCESS_TOKEN"))
            )
        state = (
            "LAST_VERIFIED_READY" if binding_configured and last_active_proof
            else "STALE_NEEDS_JIT_VERIFICATION" if binding_configured
            else "TRANSPORT_UNAVAILABLE"
        )
        return self._persist(_base_row(
            registration,
            state=state,
            identity=str(previous.get("destination_identity") or "") or None,
            identity_match=False,
            probe_kind="PASSIVE_LOCAL_AND_CACHED_METADATA",
            detail={
                "binding_configured": binding_configured,
                "last_active_proof_at_utc": last_active_proof,
                "network_probe_performed": False,
                "jit_attempt_identity": prior_jit_attempt_identity,
            },
        ), persist=persist)

    def cached_failed_jit_attempt(
        self, destination: str, *, attempt_identity: str
    ) -> dict[str, Any] | None:
        """Return a local failed JIT result already consumed by this exact durable intent."""

        previous = self._previous_readiness(registration_for_destination(destination).surface)
        detail: Any = previous.get("sanitized_detail") or previous.get("sanitized_detail_json")
        if isinstance(detail, str):
            try:
                detail = json.loads(detail)
            except (TypeError, ValueError):
                detail = {}
        detail = dict(detail) if isinstance(detail, Mapping) else {}
        state = str(previous.get("readiness_state") or "")
        if detail.get("jit_attempt_identity") == str(attempt_identity) and state not in READY_STATES:
            return dict(previous)
        return None

    def verify_destination_jit(
        self,
        destination: str,
        *,
        reason: str,
        persist: bool = True,
        attempt_identity: str | None = None,
    ) -> dict[str, Any]:
        """Perform at most one active probe for the exact destination attempt."""

        if reason not in {"PUBLICATION", "MANUAL_DESTINATION_VERIFICATION"}:
            raise ValueError("jit_destination_probe_reason_not_authorized")
        registration = registration_for_destination(destination)
        if registration.transport_type == "EDGE_CDP":
            record_browser_interaction_event(
                "active_probe", reason=f"{reason}_JIT_READINESS", destination=destination
            )
            activity_state = "PUBLICATION_ACTIVE" if reason == "PUBLICATION" else "RECONCILIATION_ACTIVE"
            with browser_activity(
                activity_state,
                reason=f"{reason}_JIT_READINESS",
                destination=destination,
            ):
                row = self.probe_surface(registration.surface)
        else:
            row = self.probe_surface(registration.surface)
        if attempt_identity:
            row["sanitized_detail"] = {
                **dict(row.get("sanitized_detail") or {}),
                "jit_attempt_identity": str(attempt_identity),
            }
        return self._persist(row, persist=persist)

    def ensure_destination_runtime_for_readback(self, destination: str) -> dict[str, Any]:
        """Ensure Edge only for exact browser readback; do not perform an auth/global probe."""

        registration = registration_for_destination(destination)
        if registration.transport_type != "EDGE_CDP":
            return {"status": "NON_BROWSER_DESTINATION", "external_probe_performed": False}
        if not callable(self.edge_runtime_ensurer):
            return {"status": "TRANSPORT_UNAVAILABLE", "external_probe_performed": False}
        try:
            recovered = dict(self.edge_runtime_ensurer(urls=()) or {})
        except TypeError:
            recovered = dict(self.edge_runtime_ensurer() or {})
        return {
            "status": str(recovered.get("status") or "TRANSPORT_UNAVAILABLE"),
            "external_probe_performed": False,
            "destination": destination,
        }

    def probe_all(self, *, surfaces: Sequence[str] = TIER1_SURFACES,
                   persist: bool = True) -> dict[str, Any]:
        """Compatibility name for a passive snapshot; global active social probing is forbidden."""
        if BROWSER_INTERACTION_BUDGET_V1.edge_global_social_probe_allowed:
            raise RuntimeError("browser_budget_invalid_global_social_probe_enabled")
        rows = {surface: self.passive_surface(surface, persist=persist) for surface in surfaces}
        return {
            "schema_version": "contentops.destination_readiness_matrix.v1",
            "transport_registry_version": REGISTRY_VERSION,
            "identity_authority_version": IDENTITY_AUTHORITY_VERSION,
            "surfaces": rows,
            "ready_surfaces": sorted(
                surface for surface, row in rows.items() if row["readiness_state"] in READY_STATES
            ),
            "public_write_performed": False,
            "secret_values_exposed": False,
            "active_browser_probe_performed": False,
            "external_provider_health_poll_performed": False,
        }


validate_registry()
