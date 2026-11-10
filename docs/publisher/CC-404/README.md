# CC-404: verifiable event pack

Code is built and tested. Completion still needs PPI's issued freeze and the
three public-stage readbacks. The current outside publication cause is
`SUBSTACK_ACCOUNT_SUSPENDED_IMPERSONATION`: a fresh read-only browser check
confirmed the suspension. Production retains `KILL_SWITCH`, version 41.
See [external-readbacks.json](external-readbacks.json); integration and the
installed consumer are recorded in [FINAL.json](FINAL.json).

The event attach command now retains Main's exact public file and stamps its
SHA-256 with the official OpenTimestamps client. The binary `.ots` proof and the
first proof stay beside the retained file. The existing plan-status minute entry
checks at most one due proof, at six-hour intervals; no schedule is added or changed.
Dry runs perform no timestamp or publication writes.

The fresh remote default `5be8fc63317be06d8319f3dd51ac4137a107cbb5` is an
ancestor of Publisher's operating HEAD
`6f7e4003a14ac679dcf199c69376aae75f252409`, 834 commits behind it. This branch
starts at that operating HEAD so the existing live consumers and earlier work
are preserved. The three user-named uncommitted files are excluded.

Install the bounded client in its dedicated environment:

```powershell
python -m venv 'A:\Capital Chronicle\Runtime\ContentOps\tools\opentimestamps-client'
& 'A:\Capital Chronicle\Runtime\ContentOps\tools\opentimestamps-client\Scripts\python.exe' -m pip install -r requirements-opentimestamps.txt
```

`scripts/opentimestamps_client.py` runs the official client with CPython's
Windows crypto DLL. It also inspects a proof's hash and attestations without
printing binary data. Automated stamp and upgrade calls use `--no-bitcoin` and
`--no-cache`: they open no wallet, Bitcoin configuration or credentials.

Attach a new freeze through the existing consumer:

```powershell
python scripts/event_public_record.py --attach-freeze EVENT_ID --freeze-file PUBLIC_JSON --freeze-sha256 EXACT_MAIN_SHA256
```

`--stamp-freeze EVENT_ID` stamps without opening the production store.
`--upgrade-timestamp` makes one bounded upgrade attempt. The source bytes are
never reserialized. Calendar acceptance, an included Bitcoin attestation, and
independent Bitcoin verification are distinct states. Neither a local clock nor
`--no-bitcoin` verification is reported as Bitcoin confirmation.

The preview/review transport includes the exact public JSON and available proof
inside the article's own media folder. Its readback requires actual downloaded
bytes, hashes and the same public object. Upgrading a local proof does not edit
an issued post; a later review can carry the upgraded proof.

The network smoke uses the already-issued 6 November NFP public file. Its new
submission was observed on 11 November at 01:34 GMT+7, after that release. This
cannot establish that NFP's file was independently timestamped before release.
The first returned proof is `CALENDAR_PENDING`; Bitcoin verification is false.
The proof and exact public source are in this item's media folder.

The final focused tests cover 476 distinct cases across the recorded runs:
[event-tests.xml](event-tests.xml), [reader-event-tests.xml](reader-event-tests.xml),
[publication-regression.xml](publication-regression.xml) and
[stamp-tests.xml](stamp-tests.xml). The 272-case publication regression includes
the real coordinator, native Neo executor and canonical entrypoint. Full PPI
acceptance still requires the 13 November source freeze, Bitcoin confirmation,
independent CLI/site verification and actual preview/arrival/review readbacks.
The prior run's observed Substack suspension and publication halt are preserved.

The three structured stages now assemble without editorial model calls. The
preview leads with the conditional call in first person, retaining all five
Main fields. An exact legacy wording remains accepted. A preview/hash post is
immutable through the coordinator's presentation, restoration and attribution
edit paths. Its JSON/proof downloads are pinned on first assembly; a later local
proof upgrade cannot change an issued post's expected attachments.

The arrival uses Main's explicit matched branch indices and plan IDs. Its print
must occur in the hash-bound official capture. The status export must recognise
each armed plan. A native publish action rechecks the 15-minute arrival window.
The release card shows the actual print. The review card shows its scored count.

The review joins every public ledger call whose exact source-plan hash appears
in the frozen file. A caller cannot narrow the population with an ID list.
Main's scored rows supply results; untriggered and unresolved calls survive.
The review reads current public ledger and score exports, while the preview
keeps its original ledger snapshot. Neither stage rewrites Main's public bytes.
The downloadable ledger, its hash and chain tip enter the existing publication
transport. Its snapshot clock is shown separately from the event freeze clock.

The existing `CapitalChronicle-PlanStatusPosts-V1` task runs
`pythonw.exe -B scripts/plan_status_posts.py --publish` from
`A:\Capital Chronicle\ContentOps`. One pass assembles or resumes one due event.
It uses the existing preparation rows, outbox and sole coordinator. Confirmed
canonical readback precedes its seven registered derivatives. Repeated passes
do not resend confirmed posts; uncertain writes stay in readback/reconciliation.
Fresh native newsroom input recognises the reserved event stage and does not
author a duplicate. Already-issued native requests keep their original route.

An arrival is attached with one existing-CLI action:

```powershell
python scripts/event_public_record.py --attach-arrival EVENT_ID --arrival-file MAIN_PUBLIC_ARRIVAL_JSON --arrival-sha256 EXACT_MAIN_SHA256
```

Main's public arrival object has exactly these fields:

```json
{
  "schema_version": "contentops.event_arrival.public.v1",
  "event_id": "EVENT_ID",
  "event_time_utc": "RELEASE_INSTANT",
  "known_at_utc": "OBSERVED_RELEASE_INSTANT",
  "frozen_sha256": "EXACT_FREEZE_SHA256",
  "matched_branches": [0],
  "armed_plan_ids": [],
  "print": {
    "display": "EXACT_PRINT",
    "label": "MEASURE",
    "publisher": "OFFICIAL_PUBLISHER",
    "source_url": "https://OFFICIAL_RELEASE",
    "source": {"path": "RETAINED_OFFICIAL_CAPTURE", "sha256": "EXACT_CAPTURE_SHA256"},
    "excerpt": "EXACT_CAPTURE_EXCERPT_CONTAINING_PRINT",
    "rights_class": "BLS_US_FEDERAL_PUBLIC_DOMAIN_TEXT"
  }
}
```

Branch indices are zero-based. An empty branch list explicitly means none
matched. `US_FEDERAL_PUBLIC_DOMAIN` is also accepted for the release text.
Main supplies the matches and armed-plan identities; Publisher does not infer
them from prose or account state. No PPI arrival can exist before its release.

For a prepared source packet, `--event-pack preview|arrival|review --pack-inputs
FILE` assembles the structured stage. `--resume-pack ID` continues its existing
coordinator. `--pack-command begin|submit|readback` handles exact native requests;
pass the actual invocation ID and request hash. No other chat is messaged.

The [rendered NFP example](rendered-final/event-pack-bls-emsit-20261106-preview/article.html)
uses only the retained NFP public map at its original source cutoff. Its new
render clock is separate. The image was visually inspected for legibility,
source meaning and clipping; [render-evidence.json](render-evidence.json)
binds its binary bytes. It is not a new post or PPI acceptance evidence.

Prepared outside actions: Ops Product resolves the existing Substack suspension
through its owner appeal route. Ops Live issues PPI's public freeze and explicit
arrival record. After access returns, resume the existing event identities;
do not repost uncertain objects or clear the halt as part of this item.

Official references: [OpenTimestamps](https://opentimestamps.org/) and the
[client's verification instructions](https://github.com/opentimestamps/opentimestamps-client).
Launch readback: `gpt-6.1-sol/max`, `CONFIGURED_NOT_OBSERVED`. No editorial model
call has been made in this deterministic sub-step.
