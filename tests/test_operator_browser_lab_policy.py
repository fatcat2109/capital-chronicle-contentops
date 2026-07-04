from pathlib import Path
from unittest.mock import MagicMock, patch
from live_contentops import operator_browser_lab as lab


def test_probe_cdp_reports_boolean_liveness():
    response = MagicMock()
    response.__enter__.return_value = response
    response.__exit__.return_value = None
    with patch("urllib.request.urlopen", return_value=response), patch("json.load", return_value={"Browser": "Edg", "webSocketDebuggerUrl": "ws://127.0.0.1"}):
        result = lab.probe_cdp(9222)
    assert result == {"cdp_alive": True, "browser_present": True, "websocket_present": True}


def test_default_profile_path_outside_repo():
    repo = Path(r"A:\Capital Chronicle\tools\cc-live-contentops")
    profile = lab.get_default_profile_root()
    assert not lab.is_path_inside(profile, repo)
    policy = lab.validate_profile_policy(profile, repo)
    assert policy["profile_inside_repo"] is False
    assert policy["profile_path_persistable_in_git"] is False


def test_cdp_default_port_and_override():
    assert lab.resolve_cdp_port({}) == 9222
    assert lab.resolve_cdp_port({lab.CDP_PORT_ENV_KEY: "9333"}) == 9333


def test_browser_command_never_includes_secrets():
    cmd = lab.build_browser_command("chrome.exe", Path(r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"), 9222, "telegram")
    joined = "\n".join(cmd).lower()
    assert "bot_token" not in joined
    assert "client_secret" not in joined
    assert "access_token" not in joined
    assert "cookie" not in joined
    assert "--new-window" in cmd
    assert "https://core.telegram.org/bots/api" in cmd


def test_policy_forbids_browser_state_dumps_and_publish_actions():
    policy = lab.SAFE_POLICY
    assert policy["cookie_dump_allowed"] is False
    assert policy["localStorage_dump_allowed"] is False
    assert policy["sessionStorage_dump_allowed"] is False
    assert policy["dom_dump_allowed"] is False
    assert policy["platform_write_allowed"] is False
    assert policy["post_publish_upload_allowed"] is False
    assert policy["scheduler_allowed"] is False
    assert policy["autonomous_replies_or_dms_allowed"] is False



def test_all_docs_contains_official_portals():
    urls = lab.urls_for_platform("all-docs")
    assert "https://developer.x.com/" in urls
    assert "https://www.linkedin.com/developers/" in urls
    assert "https://developers.facebook.com/" in urls
    assert "https://developers.tiktok.com/" in urls
    assert "https://console.cloud.google.com/" in urls
    assert "https://substack.com/" in urls


def test_guard_x_cdp_requires_dry_run(capsys):
    code = lab.main(["guard-x-cdp", "--cdp-port", "9222"])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    assert payload["live_click_allowed"] is False


def test_guard_x_cdp_blocks_antigravity_without_launch(capsys):
    code = lab.main([
        "guard-x-cdp",
        "--dry-run",
        "--cdp-port",
        "9222",
        "--command-line",
        r"chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\Users\bullw\.gemini\antigravity-browser-profile",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 2
    assert payload["operator_browser_lab_command"] == "guard-x-cdp"
    assert payload["profile_guard_status"] == "antigravity_profile_blocked"
    assert payload["blocked_before_live_click"] is True
    assert payload["live_click_performed"] is False


def test_prelive_x_post_requires_dry_run(capsys):
    code = lab.main(["prelive-x-post", "--payload-text", "Capital Chronicle educational briefing."])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    assert payload["live_click_allowed"] is False


def test_prelive_x_post_ready_without_browser_probe_or_click(capsys):
    code = lab.main([
        "prelive-x-post",
        "--dry-run",
        "--payload-text",
        "Capital Chronicle educational briefing: supervised pre-live X payload validation.",
        "--cdp-port",
        "9223",
        "--command-line",
        r"msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 0
    assert payload["operator_browser_lab_command"] == "prelive-x-post"
    assert payload["ready_for_operator_review"] is True
    assert payload["browser_or_cdp_probe_performed"] is False
    assert payload["live_click_performed"] is False


def test_gate_x_live_click_requires_dry_run(capsys):
    code = lab.main([
        "gate-x-live-click",
        "--payload-text",
        "Capital Chronicle educational briefing.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    assert payload["live_click_allowed"] is False


def test_gate_x_live_click_ready_without_browser_probe_or_click(capsys):
    code = lab.main([
        "gate-x-live-click",
        "--dry-run",
        "--payload-text",
        "Capital Chronicle educational briefing: supervised pre-live X payload validation.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
        "--cdp-port",
        "9223",
        "--command-line",
        r"msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 0
    assert payload["operator_browser_lab_command"] == "gate-x-live-click"
    assert payload["future_live_click_eligible_after_separate_live_task"] is True
    assert payload["live_click_allowed"] is False
    assert payload["browser_or_cdp_probe_performed"] is False
    assert payload["live_click_performed"] is False


def test_authorize_x_live_click_requires_dry_run(capsys):
    code = lab.main([
        "authorize-x-live-click",
        "--payload-text",
        "Capital Chronicle educational briefing.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    assert payload["live_click_allowed"] is False


def test_authorize_x_live_click_ready_without_browser_probe_or_click(capsys):
    code = lab.main([
        "authorize-x-live-click",
        "--dry-run",
        "--payload-text",
        "Capital Chronicle educational briefing: supervised pre-live X payload validation.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
        "--cdp-port",
        "9223",
        "--command-line",
        r"msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 0
    assert payload["operator_browser_lab_command"] == "authorize-x-live-click"
    assert payload["ready_for_exact_separate_live_task"] is True
    assert payload["separate_exact_live_task_required"] is True
    assert payload["live_click_allowed"] is False
    assert payload["browser_or_cdp_probe_performed"] is False
    assert payload["live_click_performed"] is False
    assert payload["public_url_capture_performed"] is False



def test_rehearse_x_pre_click_requires_dry_run(capsys):
    code = lab.main([
        "rehearse-x-pre-click",
        "--payload-text",
        "Capital Chronicle educational briefing.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    assert payload["live_click_allowed"] is False


def test_rehearse_x_pre_click_ready_without_browser_probe_or_click(capsys):
    code = lab.main([
        "rehearse-x-pre-click",
        "--dry-run",
        "--payload-text",
        "Capital Chronicle educational briefing: supervised pre-live X payload validation.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
        "--cdp-port",
        "9223",
        "--command-line",
        r"msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 0
    assert payload["operator_browser_lab_command"] == "rehearse-x-pre-click"
    assert payload["ready_for_separate_exact_live_task"] is True
    assert payload["separate_exact_live_task_required"] is True
    assert payload["live_click_allowed"] is False
    assert payload["browser_or_cdp_probe_performed"] is False
    assert payload["live_click_performed"] is False
    assert payload["public_url_capture_performed"] is False


def test_authorization_request_x_live_click_requires_dry_run(capsys):
    code = lab.main([
        "authorization-request-x-live-click",
        "--payload-text",
        "Capital Chronicle educational briefing.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    assert payload["live_click_allowed"] is False


def test_authorization_request_x_live_click_ready_without_browser_probe_or_click(capsys):
    code = lab.main([
        "authorization-request-x-live-click",
        "--dry-run",
        "--payload-text",
        "Capital Chronicle educational briefing: supervised pre-live X payload validation.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
        "--cdp-port",
        "9223",
        "--command-line",
        r"msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 0
    assert payload["operator_browser_lab_command"] == "authorization-request-x-live-click"
    assert payload["ready_for_operator_review"] is True
    assert payload["future_exact_live_task_required"] is True
    assert payload["explicit_future_live_scope_required"] is True
    assert payload["live_click_allowed_now"] is False
    assert payload["live_click_allowed"] is False
    assert payload["browser_or_cdp_probe_performed"] is False
    assert payload["live_click_performed"] is False
    assert payload["public_url_capture_performed"] is False


def test_scope_decision_x_live_click_requires_dry_run(capsys):
    code = lab.main([
        "scope-decision-x-live-click",
        "--payload-text",
        "Capital Chronicle educational briefing.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
        "--scope-decision",
        "approve_future_scope",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    assert payload["live_click_allowed"] is False


def test_scope_decision_x_live_click_approves_future_scope_without_probe_or_click(capsys):
    code = lab.main([
        "scope-decision-x-live-click",
        "--dry-run",
        "--payload-text",
        "Capital Chronicle educational briefing: supervised pre-live X payload validation.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
        "--scope-decision",
        "approve_future_scope",
        "--cdp-port",
        "9223",
        "--command-line",
        r"msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 0
    assert payload["operator_browser_lab_command"] == "scope-decision-x-live-click"
    assert payload["scope_decision_status"] == "APPROVED_FOR_FUTURE_EXACT_LIVE_TASK"
    assert payload["future_exact_live_task_eligible_for_consideration"] is True
    assert payload["explicit_future_live_authorization_still_required"] is True
    assert payload["live_click_allowed_now"] is False
    assert payload["live_click_allowed"] is False
    assert payload["browser_or_cdp_probe_performed"] is False
    assert payload["live_click_performed"] is False
    assert payload["public_url_capture_performed"] is False


def test_execution_prep_x_live_click_requires_dry_run(capsys):
    code = lab.main([
        "execution-prep-x-live-click",
        "--payload-text",
        "Capital Chronicle educational briefing.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
        "--scope-decision",
        "approve_future_scope",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    assert payload["live_click_allowed"] is False


def test_execution_prep_x_live_click_ready_without_probe_or_click(capsys):
    code = lab.main([
        "execution-prep-x-live-click",
        "--dry-run",
        "--payload-text",
        "Capital Chronicle educational briefing: supervised pre-live X payload validation.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
        "--scope-decision",
        "approve_future_scope",
        "--cdp-port",
        "9223",
        "--command-line",
        r"msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 0
    assert payload["operator_browser_lab_command"] == "execution-prep-x-live-click"
    assert payload["execution_prep_status"] == "READY_FOR_EXACT_LIVE_EXECUTION_AUTHORIZATION_TASK"
    assert payload["ready_for_exact_live_execution_authorization_task"] is True
    assert payload["exact_live_authorization_task_required"] is True
    assert payload["live_click_allowed_now"] is False
    assert payload["live_click_allowed"] is False
    assert payload["browser_or_cdp_probe_performed"] is False
    assert payload["live_click_performed"] is False
    assert payload["public_url_capture_performed"] is False



def test_exact_authorize_x_live_click_requires_dry_run(capsys):
    code = lab.main([
        "exact-authorize-x-live-click",
        "--payload-text",
        "Capital Chronicle educational briefing.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
        "--scope-decision",
        "approve_future_scope",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    assert payload["live_click_performed"] is False


def test_exact_authorize_x_live_click_authorizes_scope_without_probe_or_click(capsys):
    code = lab.main([
        "exact-authorize-x-live-click",
        "--dry-run",
        "--payload-text",
        "Capital Chronicle educational briefing: supervised pre-live X payload validation.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
        "--scope-decision",
        "approve_future_scope",
        "--cdp-port",
        "9223",
        "--command-line",
        r"msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 0
    assert payload["operator_browser_lab_command"] == "exact-authorize-x-live-click"
    assert payload["authorization_status"] == "EXACT_LIVE_CLICK_AUTHORIZED_FOR_ONE_OPERATOR_SUPERVISED_CLICK"
    assert payload["exact_live_click_authorized_for_one_operator_supervised_click"] is True
    assert payload["authorization_scope"] == "one_payload_one_account_one_destination_one_x_post_click"
    assert payload["browser_or_cdp_probe_performed"] is False
    assert payload["live_click_performed"] is False
    assert payload["public_url_capture_performed"] is False


def test_execute_x_live_click_requires_dry_run(capsys):
    code = lab.main([
        "execute-x-live-click",
        "--payload-text",
        "Capital Chronicle educational briefing: supervised pre-live X payload validation.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
        "--scope-decision",
        "approve_future_scope",
        "--captured-public-x-url",
        "https://x.com/capitalchronicle/status/1234567890123456789",
        "--operator-confirmed-payload-hash",
        "0" * 64,
        "--operator-confirmed-account-destination",
        "@capitalchronicle on X",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    assert payload["live_click_performed"] is False


def test_execute_x_live_click_records_operator_outcome_without_probe_or_session_read(capsys):
    auth_code = lab.main([
        "exact-authorize-x-live-click",
        "--dry-run",
        "--payload-text",
        "Capital Chronicle educational briefing: supervised pre-live X payload validation.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
        "--scope-decision",
        "approve_future_scope",
        "--cdp-port",
        "9223",
        "--command-line",
        r"msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main",
    ])
    auth_payload = __import__("json").loads(capsys.readouterr().out)
    assert auth_code == 0

    code = lab.main([
        "execute-x-live-click",
        "--dry-run",
        "--payload-text",
        "Capital Chronicle educational briefing: supervised pre-live X payload validation.",
        "--operator-go-phrase",
        "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY",
        "--scope-decision",
        "approve_future_scope",
        "--cdp-port",
        "9223",
        "--command-line",
        r"msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main",
        "--operator-confirmed-click-performed",
        "--captured-public-x-url",
        "https://x.com/capitalchronicle/status/1234567890123456789",
        "--operator-confirmed-payload-hash",
        auth_payload["payload_hash"],
        "--operator-confirmed-account-destination",
        "@capitalchronicle on X",
        "--operator-confirmed-kill-switch-available-before-click",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 0
    assert payload["operator_browser_lab_command"] == "execute-x-live-click"
    assert payload["execution_status"] == "EXECUTED_WITH_CAPTURED_PUBLIC_URL"
    assert payload["live_click_performed"] is True
    assert payload["public_url_capture_performed"] is True
    assert payload["publication_registry_record_appended"] is False
    assert payload["browser_or_cdp_probe_performed"] is False
    assert payload["cookie_read_performed"] is False
    assert payload["session_storage_read_performed"] is False
    assert payload["x_api_used"] is False


def test_audit_publication_registry_reports_local_readback_without_probe(capsys, tmp_path):
    target = tmp_path / "registry.jsonl"
    code = lab.main(["audit-publication-registry", "--registry-path", str(target)])
    payload = __import__("json").loads(capsys.readouterr().out)
    assert code == 0
    assert payload["operator_browser_lab_command"] == "audit-publication-registry"
    assert payload["row_count"] == 0
    assert payload["duplicate_natural_key_count"] == 0
    assert payload["browser_or_cdp_probe_performed"] is False
    assert payload["public_url_fetch_made"] is False
    assert payload["x_api_used"] is False
