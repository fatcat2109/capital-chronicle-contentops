"""Decision 121: the live coordinator consumes the restored article transport."""
from datetime import datetime, timezone
import json

import pytest

from live_contentops import neo_destination_handoff_v1 as handoff
from live_contentops import neo_endpoint_executor_v1 as endpoint
from live_contentops.native_neo_executor_v1 import bind_native_neo_coordinator
from test_publication_coordinator_v1 import _coordinator, _plan, _quality_plan, _set_mode


class ArticleBrowser:
    """Controlled Neo interface, with the real coordinator/executor/driver above it."""
    def __init__(self, destination, fault=None):
        self.destination, self.fault = destination, fault
        self.calls, self.posts, self.composer = [], [], []

    def initialize(self):
        self.calls.append("initialize")

    def open(self, destination, url):
        assert destination == self.destination
        self.url = url
        return 1

    def snapshot(self, page):
        wording = "Your account has been restricted" if self.fault == "restriction" else 'heading "Capital Chronicle"'
        if self.fault == "checkpoint":
            self.url = "https://www.linkedin.com/checkpoint/challenge/"
            wording = "Confirm your identity"
        return {"url": self.url, "text": wording, "refs": [
            {"role": "button", "name": "Start a post", "ref": "start"},
            {"role": "textbox", "name": "Text editor for creating content", "ref": "editor"},
            {"role": "button", "name": "Bật mí về video tiếp theo của bạn", "ref": "youtube-editor"},
            {"role": "textbox", "name": "CC454 article text", "ref": "youtube-text"},
            {"role": "button", "name": "Add media", "ref": "add-media"},
            {"role": "button", "name": "Thêm hình ảnh", "ref": "add-image"},
            {"role": "button", "name": "Next", "ref": "next"},
            {"role": "button", "name": "CC454 article image", "ref": "image"}]}

    def act(self, page, kind, **kwargs):
        self.calls.append((kind, kwargs))
        if kind == "click" and kwargs.get("ref") in {"add-media", "add-image"}:
            assert getattr(self, "intercepting", False), "A native file chooser must never be opened"
        if kind == "fill":
            self.composer = [kwargs["value"]]
            if self.fault in {"normalized_fill", "changed_fill"}:
                self.composer = [kwargs["value"].replace(" ", "\n\n") + (" changed" if self.fault == "changed_fill" else "")]
                raise endpoint.NeoEndpointError("NEO_FIELD_NORMALIZED_OR_REJECTED_ACT")

    def wait(self, page, selector):
        pass

    def wait_text(self, page, text):
        self.owner_controls_ready = text == "Start a post"

    def call(self, name, args):
        self.calls.append((name, args))
        if name == "upload":
            assert self.intercepting
        if name == "navigate":
            self.url = args["url"]

    def verify_link(self, short, canonical):
        return self.fault != "wrong_link"

    def run(self, page, phase, **kwargs):
        self.calls.append(phase)
        if phase == "article_restriction":
            return {"verification_required": self.fault == "external_links",
                "platform_wording": "Complete one-time verification to make external links clickable"}
        if phase == "article_identity":
            correct = self.fault != "account" and (self.fault != "delayed_owner" or getattr(self, "owner_controls_ready", False))
            return {"authenticated": correct, "observed_identity": handoff.IDENTITIES[self.destination] if correct else None,
                "observed_stable_id": "143198922", "observed_at_utc": datetime.now(timezone.utc).isoformat()}
        if phase == "article_editor":
            return {"ready": True}
        if phase == "article_composer":
            return {"texts": self.composer}
        if phase == "article_intercept_upload":
            self.intercepting = self.fault != "interception"
            return {"installed": self.fault != "interception"}
        if phase == "article_upload_restore":
            self.intercepting = False
            return {"restored": True}
        if phase == "article_publish":
            if self.fault == "composer":
                return {"status": "FAILED_BEFORE_WRITE", "definite_no_write": True,
                    "stage": "BEFORE_PUBLISH_CLICK", "reason_code": "NEO_COMPOSER_PAYLOAD_MISMATCH"}
            assert [" ".join(t.split()) for t in kwargs["posts"]] == [" ".join(t.split()) for t in self.composer]
            company = self.destination == "linkedin_company"
            self.posts = [{"public_object_id": "urn:li:activity:123" if company else "UgArticle",
                "public_object_url": "https://www.linkedin.com/feed/update/urn:li:activity:123/" if company else "https://www.youtube.com/post/UgArticle",
                "observed_text": self.composer[0], "observed_identity": handoff.IDENTITIES[self.destination],
                "links": [], "public_image_urls": []}]
            if self.fault == "lost_return":
                self.fault = None
                raise endpoint.NeoEndpointError("LOST_CLICK_RETURN")
            return {"status": "CLICKED", "dispatched_at_utc": datetime.now(timezone.utc).isoformat(),
                "pre_click_posts": list(self.composer)}
        if phase == "article_readback":
            return {"posts": self.posts}
        raise AssertionError(phase)


@pytest.fixture(autouse=True)
def local_controls(tmp_path, monkeypatch):
    control = tmp_path / "suspended_routes.json"
    control.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(handoff, "SUSPENDED_ROUTES_FILE", control)
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled", lambda: None)
    # The source/compiler is covered by the native publication suite. These
    # transport tests supply its already-approved output at the same data seam.
    from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
    original_inputs = pipeline._durable_intent_inputs
    def source_inputs(intent):
        if intent.get("output_dir"):
            return original_inputs(intent)
        payload = intent.get("native_payload") or {"text": intent["payload"]}
        return {"output_dir": tmp_path, "article": {}, "media_assets": intent.get("media_assets") or [],
            "payloads": {d: payload for d in ("youtube", "linkedin_company")},
            "canonical_url": intent.get("canonical_url"), "local_media": "", "public_image_url": ""}
    monkeypatch.setattr("live_contentops._eight_platform_substack_first_pipeline_impl_v1._durable_intent_inputs", source_inputs)


def article(tmp_path, destination, fault=None, *, automatic_articles_only=False):
    store, _, seed = _coordinator(tmp_path)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    plan = _quality_plan() if destination == "linkedin_company" else _plan(destination)
    row = next(r for r in seed.register_plan("work-1", plan)["registered"] if r["destination"] == destination)
    client = ArticleBrowser(destination, fault)
    coordinator, executor = bind_native_neo_coordinator(store, operation_id="work-1", output_dir=tmp_path / "native",
        native_invocation_id="controlled", allow_publish=True, automatic=not automatic_articles_only,
        automatic_articles=automatic_articles_only, endpoint_client=client)
    message = store.get_outbox_message(row["message_id"])
    return store, coordinator, executor, client, message, row


@pytest.mark.parametrize("destination", ["linkedin_company", "youtube"])
@pytest.mark.parametrize("case", ["closed", "unknown", "public_identity", "fresh", "other_failure"])
def test_restored_route_keeps_only_its_exact_prior_policy_no_write_closed(destination, case):
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator

    row = {"status": "DEFINITE_NO_WRITE", "dispatch_recorded": True,
           "reconciliation_status": "YOUTUBE_NON_API_AUTOMATION_PROHIBITED" if destination == "youtube"
                                    else "LINKEDIN_NON_API_AUTOMATION_PROHIBITED",
           "public_object_id": None, "public_object_url": None}
    if case == "unknown":
        row["status"] = "UNKNOWN_WRITE"
    elif case == "public_identity":
        row["public_object_id"] = "existing-public-object"
    elif case == "fresh":
        row.update(status="NOT_DISPATCHED", dispatch_recorded=False, reconciliation_status=None)
    elif case == "other_failure":
        row["reconciliation_status"] = "NEO_COMPOSER_PAYLOAD_MISMATCH"
    outcomes = {destination: row, "substack": {"status": "DISPATCH_CONFIRMED",
        "reconciliation_status": "RECONCILED_CONFIRMED", "public_object_id": "canonical",
        "public_object_url": "https://capitalchronicle.substack.com/p/controlled-history"}}
    before = json.dumps(outcomes, sort_keys=True)
    result = DurablePublicationCoordinator.publication_totals(outcomes)
    recovery = result["recovery_required_destinations"] + result.get("additional_recovery_required_destinations", [])
    assert (destination not in recovery) is (case == "closed")
    assert result["closed_no_write_destinations"] == ([destination] if case == "closed" else [])
    assert result["unknown_write_count"] == int(case == "unknown")
    assert result.get("additional_destinations", {}).get(destination) == row if destination == "linkedin_company" or case == "closed" else True
    assert json.dumps(outcomes, sort_keys=True) == before


@pytest.mark.parametrize("destination", ["linkedin_company", "youtube"])
@pytest.mark.parametrize("automatic_articles_only", [False, True])
def test_article_coordinator_posts_and_reads_exact_public_object_once(tmp_path, destination, automatic_articles_only):
    store, c, executor, browser, message, row = article(tmp_path, destination,
        automatic_articles_only=automatic_articles_only)
    result = c._dispatch_message(message, canonical_url="https://capitalchronicle.substack.com/p/test")
    assert result["status"] == "DISPATCH_CONFIRMED", result
    assert result["reconciliation_status"] == "RECONCILED_CONFIRMED", result
    assert result["public_object_url"] == browser.posts[0]["public_object_url"]
    c._dispatch_message(message, canonical_url="https://capitalchronicle.substack.com/p/test")
    assert browser.calls.count("article_publish") == 1
    assert executor.pending() == []


@pytest.mark.parametrize("destination", ["linkedin_company", "youtube"])
@pytest.mark.parametrize("fault", ["account", "composer", "restriction", "checkpoint"])
def test_refusal_never_clicks_and_platform_objection_suspends_only_that_route(tmp_path, destination, fault):
    store, c, executor, browser, message, row = article(tmp_path, destination, fault)
    before = dict(store.get_operating_control())
    result = c._dispatch_message(message, canonical_url="https://capitalchronicle.substack.com/p/test")
    assert result["status"] in {"DEFINITE_NO_WRITE", "RECONCILED_ABSENT_SAFE_TO_RETRY"}, result
    assert not browser.posts
    assert store.get_operating_control() == before
    routes = handoff.suspended_routes()
    if fault in {"restriction", "checkpoint"}:
        assert set(routes) == {destination}
        assert "article_publish" not in browser.calls
        response = next(json.loads(r["payload"])["result"] for r in store.list_outbox_messages(destination="internal:native-neo-tool")
            if "result" in json.loads(r["payload"]))
        assert response["platform_wording"] in {"Your account has been restricted", "Confirm your identity"}
    else:
        assert routes == {}
    assert handoff._prohibited_write("x") is None
    assert handoff._prohibited_write("substack") is None


def test_cc536_youtube_existing_editor_does_not_depend_on_rotating_prompt(tmp_path, monkeypatch):
    store, c, executor, browser, message, row = article(tmp_path, "youtube")
    snapshot = browser.snapshot
    def rotated(page):
        value = snapshot(page)
        value["refs"] = [r for r in value["refs"] if r["ref"] != "youtube-editor"]
        return value
    monkeypatch.setattr(browser, "snapshot", rotated)
    result = c._dispatch_message(message, canonical_url="https://capitalchronicle.substack.com/p/test")
    assert result["reconciliation_status"] == "RECONCILED_CONFIRMED"
    assert browser.calls.count("article_publish") == 1


def test_cc536_company_identity_waits_for_its_hydrated_owner_controls(tmp_path):
    store, c, executor, browser, message, row = article(tmp_path, "linkedin_company", "delayed_owner")
    result = c._dispatch_message(message, canonical_url="https://capitalchronicle.substack.com/p/test")
    assert result["reconciliation_status"] == "RECONCILED_CONFIRMED"
    assert browser.calls.count("article_publish") == 1


@pytest.mark.parametrize("case,absent", [("loaded", True), ("empty", False), ("partial", False), ("wrong_account", False)])
def test_cc536_company_absence_requires_loaded_own_feed_without_a_partial_target(case, absent):
    browser = ArticleBrowser("linkedin_company", "account" if case == "wrong_account" else None)
    url = "https://www.linkedin.com/company/143198922/admin/page-posts/published/"
    browser.open("linkedin_company", url)
    text = "The complete approved article starts with its bound research call and all its limits.\n\nMore exact copy."
    browser.posts = [] if case == "empty" else [{"public_object_id":"urn:li:activity:old", "public_object_url":"https://www.linkedin.com/feed/update/urn:li:activity:old/",
        "observed_identity":"linkedin:company:143198922", "observed_text":text[:70] if case == "partial" else "An older unrelated article.", "links":[]}]
    result = endpoint.NeoBrowserDriver(browser).article_readback({"destination":"linkedin_company",
        "expected_identity":"linkedin:company:143198922", "entry_url":url, "native_payload":{"text":text}}, 1)
    assert bool(result.get("target_post_absent")) is absent
    assert "article_publish" not in browser.calls


def test_cc536_youtube_external_link_verification_stops_only_its_route(tmp_path):
    store, c, executor, browser, message, row = article(tmp_path, "youtube", "external_links")
    result = c._dispatch_message(message, canonical_url="https://capitalchronicle.substack.com/p/test")
    assert result["status"] in {"DEFINITE_NO_WRITE", "RECONCILED_ABSENT_SAFE_TO_RETRY"}
    assert "article_publish" not in browser.calls
    assert handoff.suspended_routes() == {"youtube": "YOUTUBE_EXTERNAL_LINK_VERIFICATION_REQUIRED"}
    response = next(json.loads(r["payload"])["result"] for r in store.list_outbox_messages(destination="internal:native-neo-tool")
        if "result" in json.loads(r["payload"]))
    assert response["platform_wording"] == "Complete one-time verification to make external links clickable"


@pytest.mark.parametrize("fault,confirmed", [("normalized_fill", True), ("changed_fill", False)])
@pytest.mark.parametrize("destination", ["youtube", "linkedin_company"])
def test_cc536_youtube_fill_accepts_only_observed_whitespace_changes(tmp_path, fault, confirmed, destination):
    store, c, executor, browser, message, row = article(tmp_path, destination, fault)
    result = c._dispatch_message(message, canonical_url="https://capitalchronicle.substack.com/p/test")
    assert (result.get("reconciliation_status") == "RECONCILED_CONFIRMED") is confirmed
    assert bool(browser.posts) is confirmed
    assert browser.calls.count("article_publish") == int(confirmed)


@pytest.mark.parametrize("visible", [False, True])
def test_cc536_youtube_dom_editor_excludes_hidden_composer(visible):
    import subprocess
    from pathlib import Path
    source = (Path(endpoint.__file__).with_name("neo_endpoint_steps_v1.js")).read_text(encoding="utf-8")
    script = """
const visible=JSON.parse(process.argv[1]);
const field={getClientRects:()=>visible?[{}]:[],setAttribute:()=>{},getAttribute:()=> 'A rotating prompt'};
global.document={querySelector:()=>field,querySelectorAll:()=>[field]};
global.getComputedStyle=()=>({visibility:'visible'});
const page={evaluateInPage:async fn=>({value:fn()})};
const source=JSON.parse(process.argv[2]);
(async()=>{const fn=new (Object.getPrototypeOf(async function(){}).constructor)('page','input',source);
console.log(JSON.stringify(await fn(page,{phase:'article_editor'})));})();
"""
    raw = subprocess.check_output(["node", "-e", script, json.dumps(visible), json.dumps(source)], text=True, timeout=5)
    result = json.loads(raw)
    assert result["ready"] is visible
    if not visible:
        assert result["prompt"] == "A rotating prompt"


@pytest.mark.parametrize("destination", ["linkedin_company", "youtube"])
def test_lost_article_click_return_is_readback_only(tmp_path, destination):
    store, c, _, browser, message, row = article(tmp_path, destination, "lost_return")
    first = c._dispatch_message(message, canonical_url="https://capitalchronicle.substack.com/p/test")
    assert first["status"] in {"UNKNOWN_WRITE", "DISPATCH_CONFIRMED"}, first
    assert browser.calls.count("article_publish") == 1
    browser.calls.clear()
    second = c._dispatch_message(message, canonical_url="https://capitalchronicle.substack.com/p/test")
    assert second["reconciliation_status"] == "RECONCILED_CONFIRMED", second
    assert "article_publish" not in browser.calls


def test_suspension_preserves_other_platforms_and_optional_premium_is_not_a_checkpoint(tmp_path):
    handoff.SUSPENDED_ROUTES_FILE.write_text(json.dumps({"substack_notes": "EXISTING_CAUSE"}), encoding="utf-8")
    handoff.suspend_route("youtube", "YOUTUBE_PLATFORM_RESTRICTION")
    assert handoff.suspended_routes() == {"substack_notes": "EXISTING_CAUSE", "youtube": "YOUTUBE_PLATFORM_RESTRICTION"}
    client = ArticleBrowser("linkedin_company")
    client.url = handoff.ROOTS["linkedin_company"]
    original = client.snapshot
    client.snapshot = lambda page: {**original(page), "text": "Verify with Premium"}
    assert endpoint.NeoBrowserDriver(client).article_guard({"destination": "linkedin_company"}, 1) is None


def test_native_article_consumer_keeps_manual_requests_on_its_parent_invocation(tmp_path, monkeypatch):
    from test_native_desktop_publication_v1 import seeded
    from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
    store, binding, rollout, _, _ = seeded(tmp_path, monkeypatch)
    operation = NativeReviewedPublication(store, binding, rollout=rollout,
        native_invocation_id="actual-parent-turn")
    operation._authorize_and_bind()
    assert isinstance(operation.executor, endpoint.EndpointNeoExecutor)
    assert operation.executor.automatic_destinations == {"linkedin_company", "youtube"}
    assert operation.executor.native_invocation_id == operation.native_invocation_id
    assert operation.executor.operation_id == binding["run_id"]
    assert operation.coordinator.store is store


@pytest.mark.parametrize("destination", ["linkedin_company", "youtube"])
@pytest.mark.parametrize("interception_available", [True, False])
def test_article_media_uses_only_intercepted_neo_upload_and_restores_it(tmp_path, destination, interception_available):
    from hashlib import sha256
    store, c, _, browser, message, _ = article(tmp_path, destination,
        None if interception_available else "interception")
    media = tmp_path / "media"
    media.mkdir()
    asset = media / "bound-card.png"
    asset.write_bytes(b"controlled bound transport bytes")
    intent = json.loads(message["payload"])
    intent["native_payload"] = {"text": intent["payload"], "media_asset_ids": ["bound-card"]}
    intent["media_assets"] = [{"asset_id": "bound-card", "path": str(asset),
        "sha256": sha256(asset.read_bytes()).hexdigest()}]
    store.finalize_outbox_payload_before_dispatch(message_id=message["message_id"], payload=json.dumps(intent), status="READY")
    c._dispatch_message(store.get_outbox_message(message["message_id"]),
        canonical_url="https://capitalchronicle.substack.com/p/test")
    uploads = [args for name, args in (call for call in browser.calls if isinstance(call, tuple)) if name == "upload"]
    if interception_available:
        assert uploads == [{"page": 1, "ref": "image", "files": [str(asset)]}]
        assert browser.calls.index("article_intercept_upload") < browser.calls.index("article_upload_restore")
        assert browser.intercepting is False
    else:
        assert uploads == [] and browser.posts == []
        assert not any(isinstance(call, tuple) and call[0] == "click" and call[1].get("ref") in {"add-media", "add-image"}
            for call in browser.calls)


def test_article_only_executor_leaves_other_native_steps_pending_without_endpoint_calls(tmp_path):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired
    store, _, _ = _coordinator(tmp_path)
    browser = ArticleBrowser("youtube")
    _, first = bind_native_neo_coordinator(store, operation_id="work-1", output_dir=tmp_path / "native",
        native_invocation_id="actual-parent-turn", allow_publish=True, automatic_articles=True, endpoint_client=browser)
    request = {"destination": "substack", "action": "VERIFY_IDENTITY", "work_item_id": "work-1",
        "surface": "SUBSTACK_ARTICLE", "expected_identity": handoff.IDENTITIES["substack"]}
    request["request_sha256"] = sha256_of(request)
    with pytest.raises(NativeNeoInputRequired):
        first(request)
    packet = first.begin(request["request_sha256"])
    _, resumed = bind_native_neo_coordinator(store, operation_id="work-1", output_dir=tmp_path / "native",
        native_invocation_id="actual-parent-turn", allow_publish=True, automatic_articles=True, endpoint_client=browser)
    response = {"tool_request_sha256": packet["tool_request_sha256"],
        "tool_observation": {"tool_name": "mcp__browseros_neo__run", "surface": "CODEX_NATIVE_SUBAGENT",
            "native_invocation_id": "actual-parent-turn", "observation_source": "CONTROLLED_TEST",
            "observed_at_utc": datetime.now(timezone.utc).isoformat()},
        "result": {"request_sha256": request["request_sha256"], "status": "SUCCESS",
            "observed_identity": handoff.IDENTITIES["substack"], "authenticated": True}}
    resumed.submit(request["request_sha256"], response)
    assert resumed(request)["authenticated"] is True
    assert browser.calls == []
