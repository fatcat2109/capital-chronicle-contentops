# CC-404: verifiable event pack

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

The initial targeted result is [stamp-tests.xml](stamp-tests.xml). Full PPI
acceptance still requires the 13 November source freeze, Bitcoin confirmation,
independent CLI/site verification and actual preview/arrival/review readbacks.
The prior run's observed Substack suspension and publication halt are preserved.

Official references: [OpenTimestamps](https://opentimestamps.org/) and the
[client's verification instructions](https://github.com/opentimestamps/opentimestamps-client).
Launch readback: `gpt-6.1-sol/max`, `CONFIGURED_NOT_OBSERVED`. No editorial model
call has been made in this deterministic sub-step.
