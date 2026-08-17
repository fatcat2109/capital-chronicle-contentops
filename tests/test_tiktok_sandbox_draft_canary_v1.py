from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from live_contentops import tiktok_local_desktop_oauth_pkce_v1 as oauth
from live_contentops import tiktok_sandbox_draft_canary_v1 as canary
from live_contentops import tiktok_secure_refresh_store_readonly_preflight_v1 as secure
from scripts import run_tiktok_sandbox_draft_canary_v1 as cli


RAW_OPEN_ID = "TEST-ONLY-RAW-OPEN-ID-DO-NOT-SERIALIZE"
ACCESS_TOKEN = "TEST-ONLY-ACCESS-TOKEN-DO-NOT-SERIALIZE"
OLD_REFRESH = "TEST-ONLY-OLD-REFRESH-TOKEN-DO-NOT-SERIALIZE"
NEW_REFRESH = "TEST-ONLY-NEW-REFRESH-TOKEN-DO-NOT-SERIALIZE"
CLIENT_KEY = "TEST-ONLY-CLIENT-KEY-DO-NOT-SERIALIZE"
CLIENT_SECRET = "TEST-ONLY-CLIENT-SECRET-DO-NOT-SERIALIZE"
UPLOAD_URL = (
    "https://open-upload.tiktokapis.com/video/"
    "?upload_id=fake&upload_token=TEST-ONLY-UPLOAD-TOKEN"
)
EXACT_MEDIA_SHA256 = (
    "1a2bddc40a2db7b019ddd5d7a5f7349182621b6e1ae273bbdd58a7393165c810"
)
EXACT_ATTEMPT_ID = (
    "ttcanary_b9c7a9b18d7ed326d556ba53d75fd0f2f8bb7218558f031dc7e703abf092d27a"
)
TRUNCATED_ATTEMPT_ID = (
    "ttcanary_b9c7a9b18d7ed326d556ba53d75fd0f2f8bb7218558f031dc7e703abf092d"
)


class FakeCredentialBackend:
    def __init__(self) -> None:
        self.records: dict[str, secure.CredentialRecord] = {}
        self.read_calls = 0
        self.write_calls = 0

    def read(self, target: str) -> secure.CredentialRecord | None:
        self.read_calls += 1
        return self.records.get(target)

    def write(self, target: str, *, username: str, secret: str) -> None:
        self.write_calls += 1
        self.records[target] = secure.CredentialRecord(
            username=username, secret=secret
        )

    def delete(self, target: str) -> None:
        self.records.pop(target, None)


class FakeTokenTransport:
    def __init__(
        self,
        *,
        open_id: str = RAW_OPEN_ID,
        scopes: tuple[str, ...] = oauth.REQUIRED_SCOPES,
    ) -> None:
        self.open_id = open_id
        self.scopes = scopes
        self.calls = 0

    def post_form(
        self,
        endpoint: str,
        form: Mapping[str, str],
        *,
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        self.calls += 1
        assert endpoint == oauth.TOKEN_ENDPOINT
        assert form["refresh_token"] == OLD_REFRESH
        return {
            "access_token": ACCESS_TOKEN,
            "refresh_token": NEW_REFRESH,
            "open_id": self.open_id,
            "scope": " ".join(self.scopes),
            "expires_in": 86400,
            "refresh_expires_in": 31536000,
            "token_type": "Bearer",
        }


class FakeUserInfoTransport:
    def __init__(self, open_id: str = RAW_OPEN_ID) -> None:
        self.open_id = open_id
        self.calls = 0

    def get_user_info(
        self,
        endpoint: str,
        *,
        fields: tuple[str, ...],
        access_token: str,
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        self.calls += 1
        assert endpoint == secure.USER_INFO_ENDPOINT
        assert fields == secure.USER_INFO_FIELDS
        assert access_token == ACCESS_TOKEN
        return {
            "data": {
                "user": {
                    "open_id": self.open_id,
                    "display_name": "Fake TikTok User",
                }
            },
            "error": {"code": "ok", "message": "", "log_id": "fake"},
        }


class DirectFakeSecurityProvider:
    def __init__(
        self,
        *,
        error: str | None = None,
        scopes_satisfied: bool = True,
    ) -> None:
        self.error = error
        self.scopes_satisfied = scopes_satisfied
        self.calls = 0

    def refresh_and_preflight(self) -> canary.CanarySecurityContext:
        self.calls += 1
        if self.error:
            raise secure.TikTokSecureSessionError(self.error)
        return canary.CanarySecurityContext(
            access_token=ACCESS_TOKEN,
            oauth_refresh_success=True,
            identity_preflight_success=True,
            required_scopes_satisfied=self.scopes_satisfied,
            refresh_token_rotation_persisted=True,
        )


class FakeCanaryTransport:
    def __init__(
        self,
        *,
        statuses: list[Mapping[str, Any]] | None = None,
        ambiguous_init: bool = False,
        ambiguous_upload: bool = False,
        init_failure: bool = False,
        upload_failure: bool = False,
        status_failure: bool = False,
    ) -> None:
        self.statuses = list(
            statuses
            if statuses is not None
            else [
                {"status": "PROCESSING_UPLOAD", "uploaded_bytes": 22},
                {"status": "SEND_TO_USER_INBOX", "uploaded_bytes": 22},
            ]
        )
        self.ambiguous_init = ambiguous_init
        self.ambiguous_upload = ambiguous_upload
        self.init_failure = init_failure
        self.upload_failure = upload_failure
        self.status_failure = status_failure
        self.init_calls = 0
        self.upload_calls = 0
        self.status_calls = 0
        self.operations: list[str] = []

    def initialize_draft(
        self, *, access_token: str, source_info: Mapping[str, Any]
    ) -> canary.ProviderInitResult:
        self.init_calls += 1
        self.operations.append("POST_INBOX_INIT")
        assert access_token == ACCESS_TOKEN
        assert source_info["source"] == "FILE_UPLOAD"
        if self.ambiguous_init:
            raise canary.ProviderCallError(
                "AMBIGUOUS_INIT_FOR_TEST", ambiguous=True
            )
        if self.init_failure:
            raise canary.ProviderCallError("INIT_FAILED_FOR_TEST", ambiguous=False)
        return canary.ProviderInitResult(
            publish_id="v_inbox_file~v2.fake", upload_url=UPLOAD_URL
        )

    def upload_chunk(
        self,
        *,
        upload_url: str,
        chunk: bytes,
        byte_range: canary.ChunkRange,
        final_chunk: bool,
    ) -> None:
        self.upload_calls += 1
        self.operations.append("PUT_UPLOAD_URL")
        assert upload_url == UPLOAD_URL
        assert len(chunk) == byte_range.length
        assert final_chunk is True
        if self.ambiguous_upload:
            raise canary.ProviderCallError(
                "AMBIGUOUS_UPLOAD_FOR_TEST", ambiguous=True
            )
        if self.upload_failure:
            raise canary.ProviderCallError(
                "UPLOAD_FAILED_FOR_TEST", ambiguous=False
            )

    def fetch_status(
        self, *, access_token: str, publish_id: str
    ) -> Mapping[str, Any]:
        self.status_calls += 1
        self.operations.append("POST_STATUS_FETCH")
        assert access_token == ACCESS_TOKEN
        assert publish_id == "v_inbox_file~v2.fake"
        if self.status_failure:
            raise canary.ProviderCallError("STATUS_FAILED_FOR_TEST", ambiguous=False)
        if self.statuses:
            return self.statuses.pop(0)
        return {"status": "PROCESSING_UPLOAD", "uploaded_bytes": 22}


class FakeHttpResponse:
    def __init__(self, status: int, payload: Mapping[str, Any] | None = None) -> None:
        self.status = status
        self._raw = (
            json.dumps(dict(payload)).encode("utf-8") if payload is not None else b""
        )

    def __enter__(self) -> FakeHttpResponse:
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def getcode(self) -> int:
        return self.status

    def read(self) -> bytes:
        return self._raw


def _probe(_path: Path) -> Mapping[str, Any]:
    return {
        "container": "mov,mp4,m4a,3gp,3g2,mj2",
        "codec": "h264",
        "width": 1080,
        "height": 1920,
        "fps": 30.0,
        "duration_seconds": 58.0,
    }


def _fixture_resolver(
    tmp_path: Path, *, corrupt_media: bool = False
) -> canary.AcceptedShortPackageResolver:
    tmp_path.mkdir(parents=True, exist_ok=True)
    media = tmp_path / "accepted_short.mp4"
    media.write_bytes(b"fake-mp4-bytes-for-canary")
    digest = hashlib.sha256(media.read_bytes()).hexdigest()
    manifest = tmp_path / "accepted_short.package.json"
    package = {
        "schema": "contentops.v2.platform_neutral_publication_package.v1",
        "source_story_id": "fixture",
        "source_film_id": "fixture_v1",
        "format": "SHORT_9_16",
        "language": "en",
        "artifacts": {
            "clean_video": {
                "path": str(media),
                "sha256": digest,
                "size_bytes": media.stat().st_size,
            },
            "audio": {"path": "fake.wav", "sha256": "a" * 64},
            "caption_srt": {"path": "fake.srt", "sha256": "b" * 64},
            "caption_vtt": {"path": "fake.vtt", "sha256": "c" * 64},
        },
        "metadata": {"title": "Fixture", "description": "Fixture description"},
        "rights_provenance_refs": [],
        "factual_evidence_refs": [],
        "intended_future_surfaces": ["TIKTOK"],
        "generation_version": "fixture_v1",
        "hard_boundaries": {
            "video_public_write_authority": False,
            "v1_mutation_authority": False,
            "scheduler_mutation_authority": False,
            "allow_4k": False,
        },
        "package_id": canary.EXACT_PACKAGE_ID,
        "transport": None,
        "publication_state": "PACKAGE_ONLY_ZERO_PUBLIC_WRITE",
    }
    manifest.write_text(json.dumps(package), encoding="utf-8")
    if corrupt_media:
        media.write_bytes(b"changed-after-manifest")
    return canary.AcceptedShortPackageResolver(manifest)


def _executor(
    tmp_path: Path,
    *,
    security: Any | None = None,
    transport: FakeCanaryTransport | None = None,
    corrupt_media: bool = False,
    poll_count: int = 5,
) -> tuple[
    canary.TikTokSandboxDraftCanaryExecutor,
    DirectFakeSecurityProvider,
    FakeCanaryTransport,
    canary.CanaryJournal,
]:
    active_security = security or DirectFakeSecurityProvider()
    active_transport = transport or FakeCanaryTransport()
    journal = canary.CanaryJournal(tmp_path / "journal")
    executor = canary.TikTokSandboxDraftCanaryExecutor(
        resolver=_fixture_resolver(tmp_path, corrupt_media=corrupt_media),
        secure_session_provider=active_security,
        transport=active_transport,
        journal=journal,
        media_probe=_probe,
        poll_schedule_seconds=(0.0,) * poll_count,
        sleeper=lambda _seconds: None,
    )
    return executor, active_security, active_transport, journal


def _attempt_id(executor: canary.TikTokSandboxDraftCanaryExecutor) -> str:
    return executor.expected_attempt()[1]


def test_exact_production_attempt_id_has_full_64_hex_suffix() -> None:
    attempt_id = canary.deterministic_canary_attempt_id(
        package_id=canary.EXACT_PACKAGE_ID,
        media_sha256=EXACT_MEDIA_SHA256,
    )
    suffix = attempt_id.removeprefix("ttcanary_")
    assert attempt_id == EXACT_ATTEMPT_ID
    assert len(suffix) == 64
    assert set(suffix) <= set("0123456789abcdef")


def test_fake_e2e_refresh_rotation_identity_upload_and_draft_delivery(
    tmp_path: Path,
) -> None:
    backend = FakeCredentialBackend()
    backend.records[secure.CREDENTIAL_TARGET] = secure.CredentialRecord(
        username=RAW_OPEN_ID, secret=OLD_REFRESH
    )
    store = secure.TikTokRefreshCredentialStore(backend)
    token_transport = FakeTokenTransport()
    user_info = FakeUserInfoTransport()
    security = canary.AcceptedSecureSessionProvider(
        store=store,
        token_transport=token_transport,
        user_info_transport=user_info,
        env={
            oauth.CLIENT_KEY_ENV: CLIENT_KEY,
            oauth.CLIENT_SECRET_ENV: CLIENT_SECRET,
        },
    )
    transport = FakeCanaryTransport()
    executor, _, _, journal = _executor(
        tmp_path, security=security, transport=transport
    )

    receipt = executor.run(authorized_attempt_id=_attempt_id(executor))

    assert receipt["result"] == "DRAFT_DELIVERY_CONFIRMED"
    assert receipt["logical_draft_delivery_attempts"] == 1
    assert receipt["mutation_http_calls"] == 2
    assert receipt["status_readback_calls"] == 2
    assert receipt["draft_delivery_confirmed"] is True
    assert receipt["creator_finalization_required"] is True
    assert receipt["creator_finalization_observed"] is False
    assert receipt["public_post_confirmed"] is False
    assert receipt["refresh_token_rotation_persisted"] is True
    assert receipt["access_token_persisted"] is False
    assert receipt["public_writes"] == 0
    assert token_transport.calls == 1
    assert user_info.calls == 1
    assert backend.records[secure.CREDENTIAL_TARGET].secret == NEW_REFRESH
    assert transport.init_calls == 1
    assert transport.upload_calls == 1
    assert transport.operations == [
        "POST_INBOX_INIT",
        "PUT_UPLOAD_URL",
        "POST_STATUS_FETCH",
        "POST_STATUS_FETCH",
    ]
    assert all("DIRECT_POST" not in operation for operation in transport.operations)
    assert all("VIDEO_QUERY" not in operation for operation in transport.operations)
    assert all("VIDEO_PUBLISH" not in operation for operation in transport.operations)
    assert all("CREATOR_FINALIZATION" not in operation for operation in transport.operations)
    serialized = json.dumps(receipt, sort_keys=True)
    journal_text = journal.path_for(receipt["attempt_id"]).read_text(encoding="utf-8")
    for secret_value in (
        CLIENT_KEY,
        CLIENT_SECRET,
        ACCESS_TOKEN,
        OLD_REFRESH,
        NEW_REFRESH,
        RAW_OPEN_ID,
        UPLOAD_URL,
        "TEST-ONLY-UPLOAD-TOKEN",
        "Authorization",
    ):
        assert secret_value not in serialized
        assert secret_value not in journal_text


@pytest.mark.parametrize(
    ("security", "expected"),
    [
        (
            DirectFakeSecurityProvider(error="IDENTITY_OPEN_ID_MISMATCH"),
            "IDENTITY_OPEN_ID_MISMATCH",
        ),
        (
            DirectFakeSecurityProvider(scopes_satisfied=False),
            "SECURE_IDENTITY_PREFLIGHT_FAILED",
        ),
    ],
)
def test_identity_or_scope_failure_blocks_all_mutations(
    tmp_path: Path, security: DirectFakeSecurityProvider, expected: str
) -> None:
    executor, _, transport, _ = _executor(tmp_path, security=security)
    receipt = executor.run(authorized_attempt_id=_attempt_id(executor))
    assert receipt["result"] == expected
    assert receipt["logical_draft_delivery_attempts"] == 0
    assert receipt["mutation_http_calls"] == 0
    assert transport.init_calls == 0
    assert transport.upload_calls == 0
    assert transport.status_calls == 0


def test_wrong_attempt_id_makes_zero_external_calls(tmp_path: Path) -> None:
    executor, security, transport, journal = _executor(tmp_path)
    receipt = executor.run(authorized_attempt_id="ttcanary_wrong")
    assert receipt["result"] == "OWNER_AUTHORIZED_ATTEMPT_ID_MISMATCH"
    assert security.calls == 0
    assert transport.operations == []
    assert not journal.root.exists()


def test_cli_without_exact_flag_constructs_no_external_dependency(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def forbidden() -> None:
        raise AssertionError("external dependency must not be constructed")

    monkeypatch.setattr(cli, "TikTokRefreshCredentialStore", forbidden)
    assert cli.main([]) == 2
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["result"] == "EXACT_CANARY_EXECUTION_FLAG_REQUIRED"
    assert receipt["logical_draft_delivery_attempts"] == 0
    assert receipt["mutation_http_calls"] == 0


def test_cli_wrong_attempt_constructs_no_credential_dependency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def forbidden() -> None:
        raise AssertionError("credential dependency must not be constructed")

    monkeypatch.setattr(cli, "TikTokRefreshCredentialStore", forbidden)
    resolver = _fixture_resolver(tmp_path)
    monkeypatch.setattr(cli, "AcceptedShortPackageResolver", lambda: resolver)
    result = cli.main(
        [
            "--run-exact-tiktok-sandbox-draft-canary",
            "--authorized-attempt-id",
            "ttcanary_wrong",
        ]
    )
    assert result == 2
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["result"] == "OWNER_AUTHORIZED_ATTEMPT_ID_MISMATCH"
    assert receipt["mutation_http_calls"] == 0


def test_cli_truncated_authority_id_constructs_no_external_dependency(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dependency_constructions: list[str] = []

    class ExactAuthorityResolver:
        def describe_authority(self) -> canary.PackageAuthority:
            return canary.PackageAuthority(
                package_id=canary.EXACT_PACKAGE_ID,
                media_path=Path("unused-exact-authority.mp4"),
                media_sha256=EXACT_MEDIA_SHA256,
                manifest_size_bytes=22_101_311,
            )

    def forbidden_dependency(*_args: object, **_kwargs: object) -> None:
        dependency_constructions.append("forbidden")
        raise AssertionError("external dependency must not be constructed")

    monkeypatch.setattr(cli, "AcceptedShortPackageResolver", ExactAuthorityResolver)
    monkeypatch.setattr(cli, "TikTokRefreshCredentialStore", forbidden_dependency)
    monkeypatch.setattr(cli, "UrllibFormTokenTransport", forbidden_dependency)
    monkeypatch.setattr(cli, "UrllibUserInfoTransport", forbidden_dependency)
    monkeypatch.setattr(cli, "UrllibTikTokCanaryTransport", forbidden_dependency)

    result = cli.main(
        [
            "--run-exact-tiktok-sandbox-draft-canary",
            "--authorized-attempt-id",
            TRUNCATED_ATTEMPT_ID,
        ]
    )

    assert result == 2
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["result"] == "OWNER_AUTHORIZED_ATTEMPT_ID_MISMATCH"
    assert receipt["attempt_id"] == EXACT_ATTEMPT_ID
    assert receipt["logical_draft_delivery_attempts"] == 0
    assert receipt["mutation_http_calls"] == 0
    assert receipt["status_readback_calls"] == 0
    assert dependency_constructions == []


def test_package_hash_failure_blocks_mutation(tmp_path: Path) -> None:
    executor, security, transport, journal = _executor(
        tmp_path, corrupt_media=True
    )
    receipt = executor.run(authorized_attempt_id=_attempt_id(executor))
    assert receipt["result"] in {"MEDIA_SIZE_MISMATCH", "MEDIA_HASH_MISMATCH"}
    assert security.calls == 1
    assert transport.operations == []
    assert not journal.root.exists()


def test_ambiguous_init_is_unknown_write_and_never_retried(tmp_path: Path) -> None:
    transport = FakeCanaryTransport(ambiguous_init=True)
    executor, _, _, journal = _executor(tmp_path, transport=transport)
    receipt = executor.run(authorized_attempt_id=_attempt_id(executor))
    assert receipt["result"] == "AMBIGUOUS_INIT_FOR_TEST"
    assert receipt["unknown_write"] is True
    assert transport.init_calls == 1
    assert transport.upload_calls == 0
    assert transport.status_calls == 0
    data = journal.load(receipt["attempt_id"])
    assert data is not None and data["state"] == "UNKNOWN_WRITE"
    assert data["publish_id"] is None
    security_calls = executor._secure_session_provider.calls  # noqa: SLF001
    second = executor.run(authorized_attempt_id=receipt["attempt_id"])
    assert second["result"] == "EXISTING_ATTEMPT_PREVENTS_DUPLICATE_CANARY"
    assert executor._secure_session_provider.calls == security_calls  # noqa: SLF001
    assert transport.init_calls == 1


def test_ambiguous_transfer_reconciles_by_readback_without_second_put(
    tmp_path: Path,
) -> None:
    transport = FakeCanaryTransport(
        ambiguous_upload=True,
        statuses=[
            {"status": "PROCESSING_UPLOAD", "uploaded_bytes": 25},
            {"status": "SEND_TO_USER_INBOX", "uploaded_bytes": 25},
        ],
    )
    executor, _, _, _ = _executor(tmp_path, transport=transport)
    receipt = executor.run(authorized_attempt_id=_attempt_id(executor))
    assert receipt["result"] == "DRAFT_DELIVERY_CONFIRMED"
    assert receipt["unknown_write"] is False
    assert transport.init_calls == 1
    assert transport.upload_calls == 1
    assert transport.status_calls == 2


def test_unresolved_ambiguous_transfer_remains_unknown_write(tmp_path: Path) -> None:
    transport = FakeCanaryTransport(
        ambiguous_upload=True,
        statuses=[{"status": "PROCESSING_UPLOAD", "uploaded_bytes": 10}] * 3,
    )
    executor, _, _, journal = _executor(
        tmp_path, transport=transport, poll_count=3
    )
    receipt = executor.run(authorized_attempt_id=_attempt_id(executor))
    assert receipt["result"] == "UNRESOLVED_AMBIGUOUS_TRANSFER"
    assert receipt["unknown_write"] is True
    assert transport.upload_calls == 1
    assert transport.status_calls == 3
    assert journal.load(receipt["attempt_id"])["state"] == "UNKNOWN_WRITE"


def test_provider_failed_and_poll_timeout_never_reupload(tmp_path: Path) -> None:
    failed_transport = FakeCanaryTransport(statuses=[{"status": "FAILED"}])
    executor, _, _, _ = _executor(tmp_path / "failed", transport=failed_transport)
    failed = executor.run(authorized_attempt_id=_attempt_id(executor))
    assert failed["result"] == "PROVIDER_REPORTED_FAILED"
    assert failed_transport.upload_calls == 1

    timeout_transport = FakeCanaryTransport(
        statuses=[{"status": "PROCESSING_UPLOAD", "uploaded_bytes": 25}] * 2
    )
    executor, _, _, _ = _executor(
        tmp_path / "timeout", transport=timeout_transport, poll_count=2
    )
    timed_out = executor.run(authorized_attempt_id=_attempt_id(executor))
    assert timed_out["result"] == "STATUS_POLLING_TIMEOUT_NO_REUPLOAD"
    assert timed_out["unknown_write"] is True
    assert timeout_transport.upload_calls == 1


def test_existing_terminal_journal_prevents_duplicate_before_credentials(
    tmp_path: Path,
) -> None:
    executor, security, transport, _ = _executor(tmp_path)
    attempt_id = _attempt_id(executor)
    first = executor.run(authorized_attempt_id=attempt_id)
    assert first["result"] == "DRAFT_DELIVERY_CONFIRMED"
    security_calls = security.calls
    init_calls = transport.init_calls
    second = executor.run(authorized_attempt_id=attempt_id)
    assert second["result"] == "EXISTING_ATTEMPT_ALREADY_TERMINAL"
    assert security.calls == security_calls
    assert transport.init_calls == init_calls


def test_readback_only_resume_cannot_initialize_or_transfer(tmp_path: Path) -> None:
    executor, security, transport, journal = _executor(
        tmp_path,
        transport=FakeCanaryTransport(
            statuses=[{"status": "SEND_TO_USER_INBOX", "uploaded_bytes": 25}]
        ),
    )
    authority, attempt_id = executor.expected_attempt()
    prepared = executor._resolver.validate_media(authority, probe=_probe)  # noqa: SLF001
    data = journal.create_intent(prepared, attempt_id)
    journal.update(
        data,
        state="UNKNOWN_WRITE",
        publish_id="v_inbox_file~v2.fake",
        terminal_classification="AMBIGUOUS_UPLOAD_FOR_TEST",
    )
    receipt = executor.run(
        authorized_attempt_id=attempt_id,
        readback_only=True,
    )
    assert receipt["result"] == "DRAFT_DELIVERY_CONFIRMED"
    assert receipt["logical_draft_delivery_attempts"] == 1
    assert security.calls == 1
    assert transport.init_calls == 0
    assert transport.upload_calls == 0
    assert transport.status_calls == 1


def test_chunk_contract_uses_one_actual_chunk_for_accepted_size() -> None:
    chunks = canary.build_chunk_plan(22_101_311)
    assert len(chunks) == 1
    assert chunks[0] == canary.ChunkRange(0, 22_101_310, 22_101_311)
    multi = canary.build_chunk_plan(130_000_001)
    assert len(multi) >= 2
    assert sum(chunk.length for chunk in multi) == 130_000_001
    assert all(
        canary.MIN_CHUNK_BYTES <= chunk.length <= canary.MAX_FINAL_CHUNK_BYTES
        for chunk in multi
    )


def test_live_capable_transport_uses_only_exact_upload_draft_contract() -> None:
    requests: list[Any] = []

    def opener(request: Any, *, timeout: float) -> FakeHttpResponse:
        requests.append(request)
        assert timeout == 30.0
        if request.full_url == canary.INIT_ENDPOINT:
            return FakeHttpResponse(
                200,
                {
                    "data": {
                        "publish_id": "v_inbox_file~v2.fake",
                        "upload_url": UPLOAD_URL,
                    },
                    "error": {"code": "ok", "message": "", "log_id": "fake"},
                },
            )
        if request.full_url == UPLOAD_URL:
            return FakeHttpResponse(201)
        if request.full_url == canary.STATUS_ENDPOINT:
            return FakeHttpResponse(
                200,
                {
                    "data": {"status": "SEND_TO_USER_INBOX", "uploaded_bytes": 4},
                    "error": {"code": "ok", "message": "", "log_id": "fake"},
                },
            )
        raise AssertionError("unexpected endpoint")

    transport = canary.UrllibTikTokCanaryTransport(opener=opener)
    init = transport.initialize_draft(
        access_token=ACCESS_TOKEN,
        source_info={
            "source": "FILE_UPLOAD",
            "video_size": 4,
            "chunk_size": 4,
            "total_chunk_count": 1,
        },
    )
    byte_range = canary.ChunkRange(0, 3, 4)
    transport.upload_chunk(
        upload_url=init.upload_url,
        chunk=b"MP4!",
        byte_range=byte_range,
        final_chunk=True,
    )
    status = transport.fetch_status(
        access_token=ACCESS_TOKEN, publish_id=init.publish_id
    )

    assert status["status"] == "SEND_TO_USER_INBOX"
    assert [request.get_method() for request in requests] == ["POST", "PUT", "POST"]
    init_body = json.loads(requests[0].data)
    assert init_body == {
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": 4,
            "chunk_size": 4,
            "total_chunk_count": 1,
        }
    }
    upload_headers = {key.casefold(): value for key, value in requests[1].header_items()}
    assert upload_headers["content-type"] == "video/mp4"
    assert upload_headers["content-length"] == "4"
    assert upload_headers["content-range"] == "bytes 0-3/4"
    assert json.loads(requests[2].data) == {"publish_id": "v_inbox_file~v2.fake"}
    all_urls = [request.full_url for request in requests]
    assert not any("/v2/post/publish/video/init/" in url for url in all_urls)
    assert not any("/v2/video/query/" in url for url in all_urls)


def test_publish_complete_without_public_id_does_not_confirm_public_post(
    tmp_path: Path,
) -> None:
    transport = FakeCanaryTransport(
        statuses=[
            {"status": "PUBLISH_COMPLETE", "publicaly_available_post_id": []}
        ]
    )
    executor, _, _, journal = _executor(tmp_path, transport=transport)
    receipt = executor.run(authorized_attempt_id=_attempt_id(executor))
    assert receipt["result"] == "UNEXPECTED_PUBLISH_COMPLETE"
    assert receipt["draft_delivery_confirmed"] is False
    assert receipt["creator_finalization_observed"] is True
    assert receipt["public_post_confirmed"] is False
    assert receipt["public_writes"] == 0
    assert transport.operations == [
        "POST_INBOX_INIT",
        "PUT_UPLOAD_URL",
        "POST_STATUS_FETCH",
    ]
    assert transport.upload_calls == 1
    assert all("VIDEO_QUERY" not in operation for operation in transport.operations)
    journal_text = journal.path_for(receipt["attempt_id"]).read_text(encoding="utf-8")
    assert "publicaly_available_post_id" not in journal_text


def test_publish_complete_with_public_id_confirms_boolean_without_serializing_id(
    tmp_path: Path,
) -> None:
    public_post_id = 739_123_456_789_012_345
    transport = FakeCanaryTransport(
        statuses=[
            {
                "status": "PUBLISH_COMPLETE",
                "publicaly_available_post_id": [public_post_id],
            }
        ]
    )
    executor, _, _, journal = _executor(tmp_path, transport=transport)
    receipt = executor.run(authorized_attempt_id=_attempt_id(executor))
    assert receipt["result"] == "UNEXPECTED_PUBLISH_COMPLETE"
    assert receipt["draft_delivery_confirmed"] is False
    assert receipt["creator_finalization_observed"] is True
    assert receipt["public_post_confirmed"] is True
    assert receipt["public_writes"] == 0
    assert transport.operations == [
        "POST_INBOX_INIT",
        "PUT_UPLOAD_URL",
        "POST_STATUS_FETCH",
    ]
    serialized_receipt = json.dumps(receipt, sort_keys=True)
    journal_text = journal.path_for(receipt["attempt_id"]).read_text(encoding="utf-8")
    assert str(public_post_id) not in serialized_receipt
    assert str(public_post_id) not in journal_text
    assert "publicaly_available_post_id" not in serialized_receipt
    assert "publicaly_available_post_id" not in journal_text
    assert all("VIDEO_QUERY" not in operation for operation in transport.operations)
