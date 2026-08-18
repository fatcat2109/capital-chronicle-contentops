"""Build the governed four-locale V2 proof from one accepted English picture master."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from video.locale_activation_hardening_v1.factory import activate_locales  # noqa: E402


DEFAULT_TRANSLATIONS = (
    REPO / "video" / "locale_activation_hardening_v1" / "us_retail_locales_v1.json"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-job-root", type=Path, required=True)
    parser.add_argument("--translations", type=Path, default=DEFAULT_TRANSLATIONS)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--kokoro-model", type=Path, required=True)
    parser.add_argument("--kokoro-voices", type=Path, required=True)
    args = parser.parse_args()
    result = activate_locales(
        source_job_root=args.source_job_root,
        translations_path=args.translations,
        output_root=args.output_root,
        kokoro_model=args.kokoro_model,
        kokoro_voices=args.kokoro_voices,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
