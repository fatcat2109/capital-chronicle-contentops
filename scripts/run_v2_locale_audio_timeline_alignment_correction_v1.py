from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from video.locale_activation_hardening_v1.timeline_correction import (  # noqa: E402
    run_bounded_correction,
)


DEFAULT_TRANSLATIONS = (
    REPO / "video" / "locale_activation_hardening_v1" / "us_retail_locales_v1.json"
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Realign the accepted Task-2 Vietnamese audio without TTS or picture rerender."
    )
    parser.add_argument("--source-job-root", type=Path, required=True)
    parser.add_argument("--prior-proof-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--translations", type=Path, default=DEFAULT_TRANSLATIONS)
    args = parser.parse_args()
    receipt = run_bounded_correction(
        source_job_root=args.source_job_root,
        translations_path=args.translations,
        prior_proof_root=args.prior_proof_root,
        output_root=args.output_root,
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
