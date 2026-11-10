"""Run the official OTS client on Windows; inspect proofs without printing bytes.

Use the isolated interpreter installed from requirements-opentimestamps.txt.
No wallet, Bitcoin configuration, credentials or account is opened by this shim.
"""
from __future__ import annotations

import ctypes.util
from hashlib import sha256
import json
import os
from pathlib import Path
import sys


def windows_crypto():
    # python-bitcoinlib asks for libssl although its EC functions live in
    # libcrypto. PATH may resolve an incompatible DLL. Use CPython's own DLL.
    if os.name == "nt":
        crypto = Path(sys.base_prefix) / "DLLs" / "libcrypto-3.dll"
        if crypto.is_file():
            find = ctypes.util.find_library
            ctypes.util.find_library = lambda name: (
                str(crypto) if name in {"ssl.35", "ssl", "libeay32"} else find(name))


def inspect_proof(source, proof):
    from opentimestamps.core.serialize import StreamDeserializationContext
    from opentimestamps.core.timestamp import DetachedTimestampFile
    from opentimestamps.core.notary import BitcoinBlockHeaderAttestation, PendingAttestation
    from opentimestamps.core.op import OpSHA256

    with Path(proof).open("rb") as stream:
        ctx = StreamDeserializationContext(stream)
        detached = DetachedTimestampFile.deserialize(ctx)
        ctx.assert_eof()
    digest = sha256(Path(source).read_bytes()).hexdigest()
    if not isinstance(detached.file_hash_op, OpSHA256) or detached.file_digest.hex() != digest:
        raise ValueError("OTS_PROOF_FILE_DIGEST_MISMATCH")
    calendars, blocks = [], []
    for msg, attestation in detached.timestamp.all_attestations():
        if isinstance(attestation, PendingAttestation):
            calendars.append(attestation.uri)
        elif isinstance(attestation, BitcoinBlockHeaderAttestation):
            blocks.append({"height": attestation.height, "merkle_root": msg[::-1].hex()})
    if not calendars and not blocks:
        raise ValueError("OTS_PROOF_HAS_NO_SUPPORTED_ATTESTATION")
    return {"file_sha256": digest, "file_matches": True,
            "calendars": sorted(set(calendars)), "bitcoin_attestations": blocks,
            "bitcoin_verified": False,
            "status": "BITCOIN_ATTESTATION_PRESENT" if blocks else "CALENDAR_PENDING"}


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "inspect":
        print(json.dumps(inspect_proof(sys.argv[2], sys.argv[3]), sort_keys=True))
        return 0
    windows_crypto()
    from otsclient.ots import main as official_main
    return official_main()


if __name__ == "__main__":
    raise SystemExit(main())
