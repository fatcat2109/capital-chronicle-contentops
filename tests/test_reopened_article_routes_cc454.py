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
            {"role": "button", "name": "CC454 article image", "ref": "image"}]}

    def act(self, page, kind, **kwargs):
        self.calls.append((kind, kwargs))
        if kind == "fill":
            self.composer = [kwargs["value"]]

    def wait(self, page, selector):
        pass

    def call(self, name, args):
        self.calls.append((name, args))
        if name == "navigate":
            self.url = args["url"]

    def verify_link(self, short, canonical):
        return self.fault != "wrong_link"

    def run(self, page, phase, **kwargs):
        self.calls.append(phase)
        if phase == "article_identity":
            correct = self.fault != "account"
            return {"authenticated": correct, "observed_identity": handoff.IDENTITIES[self.destination] if correct else None,
                "observed_stable_id": "143198922", "observed_at_utc": datetime.now(timezone.utc).isoformat()}
        if phase == "article_upload":
            return {"ready": True}
        if phase == "article_publish":
            if self.fault == "composer":
                return {"status": "FAILED_BEFORE_WRITE", "definite_no_write": True,
                    "stage": "BEFORE_PUBLISH_CLICK", "reason_code": "NEO_COMPOSER_PAYLOAD_MISMATCH"}
            assert kwargs["posts"] == self.composer
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
    def source_inputs(intent):
        payload = intent.get("native_payload") or {"text": intent["payload"]}
        return {"output_dir": tmp_path, "article": {}, "media_assets": [],
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
