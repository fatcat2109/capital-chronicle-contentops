"""Record only the five exact owner deletions independently observed in Neo."""
from pathlib import Path
import sys, json
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
s = ContentOpsDurableStore(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3", auto_migrate=False)
co = DurablePublicationCoordinator(store=s, transport_runtime=None)
items = [
    ("dispatch_d01bbafa38b1b14dba9ee60b7ef9f93b", "instagram_business", "18140916916727008", "deletions-first.json", "Instagram exact old URL: Sorry, this page is not available"),
    ("dispatch_56e1e68f8f3bbf42a84bd2490826da2c", "instagram_business", "18175737499394152", "deletions-first.json", "Instagram exact old URL: Sorry, this page is not available"),
    ("dispatch_9c4df1abf9421b1e987136fbad3b160a", "facebook_page", "106091951705748_1444133184571764", "deletions-second.json", "Exact Facebook post explicitly marked Only you can see posts in your Trash"),
    ("dispatch_6f08856c1f557ccba894a0c58e6e633d", "telegram", "75", "deletions-second.json", "Exact Telegram widget: Post not found"),
    ("dispatch_e2266182add291a84aa8feb637643c3a", "youtube", "UgkxpL7C_qPEDgq4_M3esrHD9Hpfseas5Fu_", "deletions-second.json", "Exact YouTube post: Trang này không có sẵn. Mong bạn thông cảm."),
]
out = []
for did, destination, oid, ref, basis in items:
    if s.get_platform_dispatch(did)["status"] == "EXTERNAL_REMOVAL_REPORTED_NO_RETRY":
        out.append({"dispatch_id": did, "status": "ALREADY_RECORDED"})
    else:
        out.append(co.reconcile_owner_removed_object(did, disposition="EXTERNAL_REMOVAL_REPORTED_NO_RETRY", observation={
            "destination": destination, "public_object_id": oid, "authority_ref": "Jim, 4 Nov ~21:05 GMT+7, via Ops",
            "observation_ref": str(Path(__file__).resolve().parent / ref), "observed_at_utc": "2026-11-04T15:54:30Z",
            "observation_basis": basis, "exact_object_absence_verified": True}))
    (Path(__file__).resolve().parent / "owner-removals.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(did, out[-1]["status"], flush=True)
