"""Exact social readbacks feed the coordinator without creating a browser writer."""
import pytest

from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff, IDENTITIES, _public_url
from live_contentops.publication_coordinator_v1 import CanonicalDestinationTransportRuntimeV1


@pytest.mark.parametrize("destination,object_id,url", [
    ("telegram", "74", "https://t.me/CapitalChronicle/74"),
    ("threads", "18145086415612549", "https://www.threads.com/@official.capitalchronicle/post/DfU6w2jHx39"),
])
@pytest.mark.parametrize("fault", [None, "identity", "object", "text", "url"])
def test_social_exact_readback_accepts_observed_object_and_rejects_wrong_content(destination, object_id, url, fault):
    intent = {"work_item_id": "article", "plan_hash": "plan", "payload": "Exact dated article copy.",
              "destination_plan": {"surface": "POST", "payload_hash": "hash"}}
    def observe(request):
        return {"request_sha256": request["request_sha256"], "status": "SUCCESS", "content_verified": True,
                "observed_identity": "other" if fault == "identity" else IDENTITIES[destination],
                "public_object_id": "different" if fault == "object" else object_id,
                "public_object_url": url.replace("CapitalChronicle", "other").replace("official.capitalchronicle", "other") if fault == "url" else url,
                "observed_text": "Different text." if fault == "text" else intent["payload"]}
    result = NeoDestinationHandoff(native_executor=observe).readback(destination=destination, intent=intent,
        public_object_id=object_id, public_object_url=url)
    assert result["verified"] is (fault is None)


@pytest.mark.parametrize("destination", ["telegram", "threads"])
@pytest.mark.parametrize("action", ["PUBLISH", "EDIT_EXISTING"])
def test_social_browser_readback_does_not_replace_api_writes(destination, action):
    with pytest.raises(ValueError, match="SOCIAL_NEO_READBACK_ONLY_API_WRITES_UNCHANGED"):
        NeoDestinationHandoff().request(destination=destination, action=action, intent={})


def test_telegram_unavailable_api_readback_reaches_native_exact_object(monkeypatch):
    from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
    monkeypatch.setattr(pipeline, "_readback_one_destination_from_durable_intent",
                        lambda **kwargs: {"verified": False, "write_absent": False})
    runtime = CanonicalDestinationTransportRuntimeV1()
    calls = []
    class Neo:
        def readback(self, **kwargs):
            calls.append(kwargs)
            return {"verified": True, "public_object_id": kwargs["public_object_id"]}
    runtime._neo_transport = Neo()
    result = runtime.readback(destination="telegram", public_object_id="74",
                              public_object_url="https://t.me/CapitalChronicle/74", intent={})
    assert result["verified"] is True
    assert calls[0]["public_object_id"] == "74"
    assert _public_url("telegram", "https://t.me/CapitalChronicle/74", "75") is False
