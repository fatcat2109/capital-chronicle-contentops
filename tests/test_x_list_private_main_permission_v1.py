"""Controlled owner-grant/capture fixtures; actual grant and cadence need runtime evidence."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import urlencode

import pytest

from live_contentops.contentops_source_research_v1 import XListPrivateMainPermission
from live_contentops.contentops_main_headline_projection_v1 import MainHeadlineExporter, project_headline
from live_contentops.contentops_main_intake_export_v1 import export_after_intake
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

CUTOFF = "2026-10-29T07:00:00Z"


def setup_profile(tmp_path, count=1):
    profile = json.loads((Path(__file__).parents[1]/"config/x_list_private_main_permission_v1.json").read_bytes())
    authority = tmp_path/"owner-authority.md"
    authority.write_text("CONTROLLED NOT REAL AUTHORITY " + profile["grant_id"], encoding="utf-8")
    profile.update(authority_file=str(authority), authority_file_sha256=sha256(authority.read_bytes()).hexdigest())
    profile_path = tmp_path/"profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    raw_root = tmp_path/"raw_archive/headline_cdp"
    raw_root.mkdir(parents=True)
    tweets = [{"tweet_id":str(100000+i), "author_handle":"FixtureOwner", "text":f"Controlled report {i}",
        "timestamp":"2026-10-26 09:00:00 GMT+7"} for i in range(count)]
    raw = raw_root/"source.json"
    raw.write_text(json.dumps({"tweets":tweets}), encoding="utf-8")
    digest = sha256(raw.read_bytes()).hexdigest()
    route = "https://x.com/i/api/graphql/fixture/ListLatestTweetsTimeline?" + urlencode({
        "variables":json.dumps({"listId":"1843870469143048642"})})
    rows = [{"schema_version":"step1_headline_catalyst_sidecar_v1", "headline_id":"fixture-"+t["tweet_id"],
        "headline_text":t["text"], "text_sha256":sha256(t["text"].encode()).hexdigest(),
        "tweet_id":t["tweet_id"], "author_handle":t["author_handle"],
        "tweet_url":"https://x.com/FixtureOwner/status/"+t["tweet_id"],
        "source_platform":"x_cdp_list_latest_tweets_timeline", "source_url_or_ref":route,
        "raw_payload_ref":str(raw.relative_to(tmp_path)), "raw_payload_sha256":digest,
        "headline_timestamp":"2026-10-26 09:00:00 GMT+7", "captured_at_utc":"2026-10-26T02:01:00Z"} for t in tweets]
    options = {"profile_path":profile_path,"capture_root":raw_root,"repository_root":tmp_path,
        "extractor":lambda payload:payload["tweets"]}
    return XListPrivateMainPermission(**options), rows, options


def projected(profile, row):
    return project_headline(row, cutoff_utc=CUTOFF, locator={}, permission_resolver=profile.permission_for)


def test_record_inherits_private_owner_authority_with_source_clocks_and_prohibitions(tmp_path):
    profile, rows, _ = setup_profile(tmp_path)
    value, reason = projected(profile, rows[0])
    assert reason is None
    assert value["rights_state"]["grant_id"] == XListPrivateMainPermission.GRANT_ID
    assert value["rights_state"]["external_licence"] is False
    assert value["rights_state"]["prohibitions"] == sorted(profile.PROHIBITIONS)
    assert value["allowed_consumers"] == ["internal_research", "narrative_context"]
    for key in ("public_republication_authority", "numeric_authority_granted", "underlying_event_truth_granted"):
        assert value[key] is False
    for key in ("public_republication_authority", "subscriber_redistribution_allowed", "model_training_allowed", "third_party_sharing_allowed"):
        assert value["rights_state"][key] is False
    assert value["known_at_utc"] == value["captured_at_utc"] == rows[0]["captured_at_utc"]
    assert value["headline_timestamp"] == "2026-10-26T02:00:00Z"
    assert value["published_at_source"] == rows[0]["headline_timestamp"]
    assert value["permission_known_at_utc"] == profile.profile["authority_observed_at_utc"]
    binding = value["private_source_profile_permission"]["record_binding"]
    assert binding["content_sha256"] == rows[0]["text_sha256"]
    assert binding["source_capture_sha256"] == rows[0]["raw_payload_sha256"]
    assert binding["post_id"] == rows[0]["tweet_id"]


@pytest.mark.parametrize("change,cause", [
    ({"captured_at_utc":"2026-10-25T16:59:59Z"}, "PRIVATE_MAIN_CAPTURE_BEFORE_GRANT_COHORT"),
    ({"captured_at_utc":None}, "HEADLINE_CLOCK_UNAVAILABLE"),
    ({"headline_timestamp":None}, "HEADLINE_CLOCK_UNAVAILABLE"),
    ({"headline_timestamp":"2026-10-26T02:00:01Z"}, "HEADLINE_SOURCE_PUBLICATION_CLOCK_MISMATCH"),
    ({"author_handle":"unknown"}, "HEADLINE_SOURCE_IDENTITY_UNAVAILABLE"),
    ({"tweet_id":"999"}, "HEADLINE_SOURCE_IDENTITY_UNAVAILABLE"),
    ({"source_url_or_ref":"https://x.com/i/api/graphql/other/UserTweets"}, "PRIVATE_MAIN_ACQUISITION_ROUTE_NOT_COVERED"),
    ({"source_platform":"NEW_FETCHER"}, "PRIVATE_MAIN_ACQUISITION_ROUTE_NOT_COVERED"),
    ({"text_sha256":"b"*64}, "HEADLINE_TEXT_HASH_MISMATCH"),
    ({"raw_payload_sha256":"b"*64}, "PRIVATE_MAIN_SOURCE_CAPTURE_HASH_MISMATCH"),
    ({"is_deleted":True}, "SOURCE_REMOVAL_OR_TAKEDOWN"),
    ({"takedown":True}, "SOURCE_REMOVAL_OR_TAKEDOWN"),
])
def test_missing_or_uncovered_inputs_do_not_gain_private_permission(tmp_path, change, cause):
    profile, rows, _ = setup_profile(tmp_path)
    value, reason = projected(profile, {**rows[0], **change})
    assert value is None and reason == cause


def test_actual_post_id_can_supply_locator_but_no_identity_is_invented(tmp_path):
    profile, rows, _ = setup_profile(tmp_path)
    value, reason = projected(profile, {**rows[0], "tweet_url":None})
    assert reason is None and value["source_url"].endswith(rows[0]["tweet_id"])
    assert value["private_source_profile_permission"]["record_binding"]["post_url_basis"] == "DERIVED_FROM_RETAINED_POST_ID_AND_AUTHOR"
    value, reason = projected(profile, {**rows[0], "tweet_url":None, "tweet_id":None})
    assert value is None and reason == "HEADLINE_SOURCE_IDENTITY_UNAVAILABLE"


def test_new_source_profile_revisits_500_row_rights_gaps_without_public_grant(tmp_path):
    profile, rows, _ = setup_profile(tmp_path, 610)
    source = tmp_path/"step1_headline_sidecar_2026_10_26.jsonl"
    raw = "".join(json.dumps(row)+"\n" for row in rows).encode()
    source.write_bytes(raw)
    store = ContentOpsDurableStore(tmp_path/"state.sqlite3")
    options = {"paths":[source], "output_root":tmp_path/"governed"}
    old = export_after_intake(store, cutoff_utc=CUTOFF, intake_identity="same-intake", **options)
    assert old["eligible_rows"] == 0 and old["source_rows_scanned"] == 610
    permitted = export_after_intake(store, cutoff_utc=CUTOFF, intake_identity="same-intake", private_profile=profile, **options)
    assert permitted["eligible_rows"] == permitted["source_rows_scanned"] == 610
    assert permitted["pages"] == 2 and not permitted["continuation_required"]
    assert source.read_bytes() == raw
    ordinary = MainHeadlineExporter(store).export(batch_id="public-unchanged", paths=[source], cutoff_utc=CUTOFF)
    assert ordinary["eligible_rows"] == 0
    with pytest.raises(ValueError, match="NOT_PUBLIC_EDITORIAL_AUTHORITY"):
        MainHeadlineExporter(store, private_profile=profile).export(batch_id="wrong-consumer", paths=[source], cutoff_utc=CUTOFF)


def test_coverage_uses_capture_clock_across_old_named_files_and_over_16_files(tmp_path):
    profile, rows, _ = setup_profile(tmp_path, 18)
    sources = []
    for index, row in enumerate(rows):
        path = tmp_path/f"step1_headline_sidecar_2026_01_{index+1:02d}.jsonl"
        path.write_text(json.dumps(row)+"\n", encoding="utf-8")
        sources.append(path)
    store = ContentOpsDurableStore(tmp_path/"state.sqlite3")
    value = export_after_intake(store, cutoff_utc=CUTOFF, intake_identity="old-name-capture", paths=sources,
        private_profile=profile, output_root=tmp_path/"governed")
    assert value["eligible_rows"] == value["source_rows_scanned"] == 18
    assert value["pages"] == 2 and not value["continuation_required"]


def test_profile_withdrawal_removes_private_rows_and_cannot_expand_consumers(tmp_path):
    profile, rows, options = setup_profile(tmp_path)
    source = tmp_path/"source.jsonl"
    source.write_text(json.dumps(rows[0])+"\n", encoding="utf-8")
    store = ContentOpsDurableStore(tmp_path/"state.sqlite3")
    kwargs = {"paths":[source], "output_root":tmp_path/"governed"}
    assert export_after_intake(store, cutoff_utc=CUTOFF, intake_identity="first", private_profile=profile, **kwargs)["eligible_rows"] == 1
    changed = deepcopy(profile.profile)
    changed["status"] = "WITHDRAWN"
    Path(options["profile_path"]).write_text(json.dumps(changed), encoding="utf-8")
    withdrawn = XListPrivateMainPermission(**options)
    assert export_after_intake(store, cutoff_utc=CUTOFF, intake_identity="withdrawn", private_profile=withdrawn, **kwargs)["eligible_rows"] == 0
    changed["permitted_consumers"].append("public_editorial")
    Path(options["profile_path"]).write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="SCOPE_INVALID"):
        XListPrivateMainPermission(**options)


def test_later_takedown_removes_the_exact_post_from_cumulative_view(tmp_path):
    profile, rows, _ = setup_profile(tmp_path)
    source = tmp_path/"source.jsonl"
    source.write_text(json.dumps(rows[0])+"\n", encoding="utf-8")
    store = ContentOpsDurableStore(tmp_path/"state.sqlite3")
    kwargs = {"paths":[source], "output_root":tmp_path/"governed", "private_profile":profile}
    assert export_after_intake(store, cutoff_utc=CUTOFF, intake_identity="first", **kwargs)["x_rows"] == 1
    with source.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({**rows[0], "takedown":True})+"\n")
    result = export_after_intake(store, cutoff_utc=CUTOFF, intake_identity="takedown", **kwargs)
    assert result["x_rows"] == 0 and result["gap_causes"]["SOURCE_REMOVAL_OR_TAKEDOWN"] == 1
