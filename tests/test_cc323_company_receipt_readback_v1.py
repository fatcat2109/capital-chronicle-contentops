"""A real LinkedIn company receipt shape reaches exact-object reconciliation."""
import pytest

from live_contentops.neo_destination_handoff_v1 import IDENTITIES, NeoDestinationHandoff


@pytest.mark.parametrize("query,identity,object_id,text,verified", [
    ("?actorCompanyId=143198922", IDENTITIES["linkedin_company"], "urn:li:share:7524330971534508032", "Exact reviewed article copy.", True),
    ("", IDENTITIES["linkedin_company"], "urn:li:share:7524330971534508032", "Exact reviewed article copy.", True),
    ("?actorCompanyId=999", IDENTITIES["linkedin_company"], "urn:li:share:7524330971534508032", "Exact reviewed article copy.", False),
    ("?actorCompanyId=143198922&redirect=https://example.com", IDENTITIES["linkedin_company"], "urn:li:share:7524330971534508032", "Exact reviewed article copy.", False),
    ("?actorCompanyId=143198922&actorCompanyId=999", IDENTITIES["linkedin_company"], "urn:li:share:7524330971534508032", "Exact reviewed article copy.", False),
    ("?actorCompanyId=143198922", "other-company", "urn:li:share:7524330971534508032", "Exact reviewed article copy.", False),
    ("?actorCompanyId=143198922", IDENTITIES["linkedin_company"], "urn:li:share:999", "Exact reviewed article copy.", False),
    ("?actorCompanyId=143198922", IDENTITIES["linkedin_company"], "urn:li:share:7524330971534508032", "Different copy.", False),
])
def test_company_receipt_reconciles_only_its_bound_account_object_and_copy(query, identity, object_id, text, verified):
    expected_id = "urn:li:share:7524330971534508032"
    url = "https://www.linkedin.com/feed/update/" + expected_id + query
    intent = {"work_item_id": "article", "plan_hash": "plan", "payload": "Exact reviewed article copy.",
              "destination_plan": {"surface": "POST", "payload_hash": "hash"}}
    completed = []

    class ObservedReturn:
        def __call__(self, request):
            return {"request_sha256": request["request_sha256"], "status": "SUCCESS", "content_verified": True,
                    "observed_identity": identity, "public_object_id": object_id,
                    "public_object_url": url, "observed_text": text}

        def complete_readback_request(self, request):
            completed.append(request["request_sha256"])

    result = NeoDestinationHandoff(native_executor=ObservedReturn()).readback(
        destination="linkedin_company", intent=intent, public_object_id=expected_id, public_object_url=url)
    assert result["verified"] is verified
    assert bool(completed) is verified


def test_company_actor_query_cannot_validate_a_personal_post():
    from live_contentops.neo_destination_handoff_v1 import _public_url
    assert not _public_url("linkedin", "https://www.linkedin.com/feed/update/urn:li:activity:7524328966573469696?actorCompanyId=143198922")
