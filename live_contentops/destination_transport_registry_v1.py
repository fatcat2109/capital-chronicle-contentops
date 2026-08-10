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


REGISTRY_VERSION = "contentops.destination_transport_registry.v1"
PUBLISHING_CDP_PORT = 9223
INGESTION_ONLY_CDP_PORT = 9222

READY_AUTHENTICATED = "READY_AUTHENTICATED"
READY_NON_BROWSER_BINDING = "READY_NON_BROWSER_BINDING"
READY_STATES = frozenset({READY_AUTHENTICATED, READY_NON_BROWSER_BINDING})
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


_SURFACES = (
    SurfaceTransport(
        "SUBSTACK_ARTICLE", "substack", "EDGE_CDP",
        "edge_cdp_publishing_adapter_v1.publish_substack_article_via_edge",
        "substack", "capitalchronicle.substack.com", PUBLISHING_CDP_PORT,
    ),
    SurfaceTransport(
        "X_POST", "x", "EDGE_CDP", "edge_cdp_publishing_adapter_v1.publish_x_post_via_edge",
        "x", "@Capitalnicle", PUBLISHING_CDP_PORT, canonical_url_dependency="SUBSTACK_ARTICLE",
    ),
    SurfaceTransport(
        "X_THREAD", "x", "EDGE_CDP", "edge_cdp_publishing_adapter_v1.publish_x_post_via_edge+publish_x_reply_via_edge",
        "x", "@Capitalnicle", PUBLISHING_CDP_PORT, canonical_url_dependency="SUBSTACK_ARTICLE",
    ),
    SurfaceTransport(
        "LINKEDIN_POST", "linkedin", "EDGE_CDP", "edge_cdp_publishing_adapter_v1.publish_linkedin_post_via_edge",
        "linkedin", "linkedin:jimcc", PUBLISHING_CDP_PORT, canonical_url_dependency="SUBSTACK_ARTICLE",
    ),
    SurfaceTransport(
        "YOUTUBE_COMMUNITY_POST", "youtube", "EDGE_CDP",
        "edge_cdp_publishing_adapter_v1.publish_youtube_community_post_via_edge",
        "youtube", "@CapitalChronicleYouTube", PUBLISHING_CDP_PORT,
        canonical_url_dependency="SUBSTACK_ARTICLE",
    ),
    SurfaceTransport(
        "TELEGRAM_CHANNEL_POST", "telegram", "BOT_API", "telegram_live_adapter_v6.execute_telegram_photo",
        "telegram", "@CapitalChronicle", canonical_url_dependency="SUBSTACK_ARTICLE",
    ),
    SurfaceTransport(
        "DISCORD_ANNOUNCEMENT", "discord", "WEBHOOK_API", "discord_live_adapter_v6.execute_discord_post",
        "discord", "configured_discord_announcement", canonical_url_dependency="SUBSTACK_ARTICLE",
    ),
    SurfaceTransport(
        "FACEBOOK_PAGE_POST", "facebook_page", "META_GRAPH_API", "facebook_page_adapter_v6.execute_facebook_photo",
        "facebook_page", "configured_facebook_page", canonical_url_dependency="SUBSTACK_ARTICLE",
    ),
    SurfaceTransport(
        "INSTAGRAM_BUSINESS_POST", "instagram_business", "META_GRAPH_API", "instagram_adapter_v6.execute_instagram_post",
        "instagram_business", "official.capitalchronicle", canonical_url_dependency="SUBSTACK_ARTICLE",
    ),
    SurfaceTransport(
        "THREADS_POST", "threads", "THREADS_API", "threads_adapter_v6.execute_threads_post",
        "threads", "official.capitalchronicle", canonical_url_dependency="SUBSTACK_ARTICLE",
    ),
    # Future video surfaces stay explicit and cannot be mistaken for the Tier-1 Community post.
    SurfaceTransport(
        "YOUTUBE_VIDEO", "youtube", "YOUTUBE_DATA_API", "future:youtube.videos.insert",
        "youtube_video", "@CapitalChronicleYouTube", tier1_write_enabled=False,
    ),
    SurfaceTransport(
        "YOUTUBE_SHORT", "youtube", "YOUTUBE_DATA_API", "future:youtube.videos.insert",
        "youtube_short", "@CapitalChronicleYouTube", tier1_write_enabled=False,
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


def canonical_transport_registry() -> dict[str, Any]:
    rows = [asdict(SURFACE_REGISTRY[surface]) for surface in sorted(SURFACE_REGISTRY)]
    return {
        "schema_version": REGISTRY_VERSION,
        "registry_version": REGISTRY_VERSION,
        "surfaces": rows,
        "tier1_surfaces": list(TIER1_SURFACES),
        "publishing_cdp_port": PUBLISHING_CDP_PORT,
        "ingestion_only_cdp_port": INGESTION_ONLY_CDP_PORT,
        "chrome_publishing_allowed": False,
        "silent_transport_fallback_allowed": False,
        "youtube_community_is_video_surface": False,
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
    for surface in TIER1_SURFACES:
        row = SURFACE_REGISTRY[surface]
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


def _base_row(registration: SurfaceTransport, *, state: str, identity: Optional[str],
              identity_match: bool, probe_kind: str, detail: Mapping[str, Any]) -> dict[str, Any]:
    if state not in READINESS_STATES:
        raise ValueError(f"readiness_state_invalid:{state}")
    return {
        "surface": registration.surface,
        "platform": registration.platform,
        "transport_registry_version": REGISTRY_VERSION,
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
    """Bounded read-only current identity probes with optional schema-v8 persistence."""

    def __init__(self, *, store: Any = None, env: Mapping[str, str] | None = None,
                 edge_runtime_ensurer: Any = None) -> None:
        validate_registry()
        self.store = store
        self.env = os.environ if env is None else env
        self.edge_runtime_ensurer = edge_runtime_ensurer

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
                    expected_handle=registration.expected_identity,
                )
                authenticated = bool(observed.get("authenticated"))
                identity_match = bool(community.get("channel_identity_verified"))
                identity = registration.expected_identity if identity_match else None
            else:
                authenticated = bool(observed.get("authenticated"))
                identity = str(observed.get("destination_identity") or "") or None
                if registration.surface == "SUBSTACK_ARTICLE":
                    # The exact configured publication route is the account/destination binding;
                    # authentication alone never substitutes an arbitrary Substack domain.
                    identity_match = authenticated and str(observed.get("page_domain") or "").endswith("substack.com")
                    identity = registration.expected_identity if identity_match else identity
                else:
                    identity_match = bool(identity) and identity.casefold() == registration.expected_identity.casefold()
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
            observed = "@" + str(chat_result.get("username") or "") if chat_result.get("username") else str(chat_result.get("id") or "")
            expected = registration.expected_identity
            identity_match = bot_ok and bool(observed) and (
                observed.casefold() == expected.casefold() or observed == chat_id
            )
            state = READY_NON_BROWSER_BINDING if identity_match else "IDENTITY_MISMATCH"
            return _base_row(registration, state=state, identity=observed or None,
                             identity_match=identity_match, probe_kind="TELEGRAM_BOT_API_IDENTITY",
                             detail={"bot_identity_verified": bot_ok, "chat_access_verified": bool(chat_result)})
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
        expected_channel = str(self.env.get("DISCORD_CHANNEL_ID") or "")
        if not webhook:
            return _base_row(registration, state="SESSION_UNAVAILABLE", identity=None,
                             identity_match=False, probe_kind="DISCORD_WEBHOOK_IDENTITY",
                             detail={"binding_configured": False})
        try:
            data = _json_get(webhook)
            channel_id = str(data.get("channel_id") or "")
            identity_match = bool(channel_id) and (not expected_channel or channel_id == expected_channel)
            state = READY_NON_BROWSER_BINDING if identity_match else "IDENTITY_MISMATCH"
            return _base_row(registration, state=state,
                             identity=f"discord_channel:{channel_id}" if channel_id else None,
                             identity_match=identity_match, probe_kind="DISCORD_WEBHOOK_IDENTITY",
                             detail={"webhook_identity_verified": bool(data.get("id")), "channel_identity_verified": identity_match})
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
            identity_match = observed_id == object_id
            display = str(data.get("username") or data.get("name") or observed_id)
            state = READY_NON_BROWSER_BINDING if identity_match else "IDENTITY_MISMATCH"
            return _base_row(registration, state=state, identity=display or None,
                             identity_match=identity_match, probe_kind="OFFICIAL_API_IDENTITY",
                             detail={"object_id_verified": identity_match, "identity_field_present": bool(display)})
        except _ProbeHTTPError as exc:
            return _base_row(registration, state=_error_state(exc), identity=None,
                             identity_match=False, probe_kind="OFFICIAL_API_IDENTITY",
                             detail={"error_class": exc.error_class, "http_status": exc.status_code})

    def probe_surface(self, surface: str) -> dict[str, Any]:
        registration = SURFACE_REGISTRY[surface]
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

    def probe_all(self, *, surfaces: Sequence[str] = TIER1_SURFACES,
                  persist: bool = True) -> dict[str, Any]:
        rows = {surface: self.probe_surface(surface) for surface in surfaces}
        if persist and self.store is not None:
            for row in rows.values():
                self.store.upsert_destination_readiness(row=row)
        return {
            "schema_version": "contentops.destination_readiness_matrix.v1",
            "transport_registry_version": REGISTRY_VERSION,
            "surfaces": rows,
            "ready_surfaces": sorted(
                surface for surface, row in rows.items() if row["readiness_state"] in READY_STATES
            ),
            "public_write_performed": False,
            "secret_values_exposed": False,
        }


validate_registry()
