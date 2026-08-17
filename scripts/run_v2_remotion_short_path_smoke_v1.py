"""Run one tiny non-creative Remotion smoke through the canonical short browser path."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from video.unattended_core_factory_v1.creative import materialize_source
from video.unattended_core_factory_v1.media import (
    artifact,
    browser_launch_layout,
    prepare_project,
    probe_media,
    render_project,
    resolve_remotion_browser_executable,
)


SMOKE_SOURCE = {
    "src/index.tsx": (
        "import {registerRoot} from 'remotion';\n"
        "import {Root} from './Root';\n"
        "registerRoot(Root);"
    ),
    "src/Root.tsx": (
        "import React from 'react';\n"
        "import {Composition} from 'remotion';\n"
        "import {Short} from './Short';\n"
        "export const Root: React.FC = () => <Composition "
        "id='V2RenderSmoke' component={Short} durationInFrames={30} "
        "fps={30} width={320} height={568}/>;"
    ),
    "src/Short.tsx": (
        "import React from 'react';\n"
        "import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';\n"
        "export const Short: React.FC = () => {\n"
        "  const frame = useCurrentFrame();\n"
        "  const x = interpolate(frame, [0, 29], [24, 272]);\n"
        "  return <AbsoluteFill style={{backgroundColor: '#071116'}}>"
        "<div style={{position: 'absolute', top: 260, left: x, width: 24, "
        "height: 24, borderRadius: 12, backgroundColor: '#6ed8cf'}}/>"
        "</AbsoluteFill>;\n"
        "};"
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--dependency-root", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    args = parser.parse_args()

    runtime = args.runtime_root.resolve()
    project = runtime / "p"
    output = runtime / "remotion_browser_smoke.mp4"
    receipt_path = runtime / "remotion_browser_smoke_receipt.json"
    materialize_source(SMOKE_SOURCE, project)
    scaffold = prepare_project(
        project_root=project,
        scaffold_root=REPO / "video" / "unattended_core_factory_v1" / "scaffold",
        dependency_root=args.dependency_root.resolve(),
        asset_root=args.asset_root.resolve(),
    )
    browser = resolve_remotion_browser_executable(args.dependency_root)
    render = render_project(
        project_root=project,
        output=output,
        crf=28,
        browser_executable=browser,
        public_root=args.asset_root.resolve(),
        composition_id="V2RenderSmoke",
        concurrency=1,
    )
    probe = probe_media(output)
    video = next(
        (stream for stream in probe.get("streams", []) if stream.get("codec_type") == "video"),
        None,
    )
    if not video:
        raise RuntimeError("smoke_video_stream_missing")
    if (int(video.get("width", 0)), int(video.get("height", 0))) != (320, 568):
        raise RuntimeError("smoke_dimensions_invalid")
    if str(video.get("r_frame_rate")) != "30/1":
        raise RuntimeError("smoke_fps_invalid")
    receipt = {
        "schema": "contentops.v2.remotion_short_path_smoke.v1",
        "result": "PASS_NON_CREATIVE_REMOTION_BROWSER_SMOKE",
        "creative_proof_consumed": False,
        "creative_reasoning_used": False,
        "parent_reasoning_effort": "high",
        "scaffold": scaffold,
        "browser_launch_layout": browser_launch_layout(project, args.dependency_root),
        "render": render,
        "media": artifact(output),
        "probe": probe,
        "public_write_authority": False,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({**receipt, "receipt": artifact(receipt_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
