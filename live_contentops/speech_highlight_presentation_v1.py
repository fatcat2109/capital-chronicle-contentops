"""Small phone presentation compiler for reviewed successor relay edits."""

from __future__ import annotations
import math
import shutil
from live_contentops import speech_highlight_relay_v1 as relay


def validate_presentation(plan, duration):
    if (
        plan.get("style") != "SOURCE_CENTRAL_PHONE_V1"
        or not plan.get("framing_reason")
        or not plan.get("source_evidence_preserved")
    ):
        raise relay.SpeechRelayError(
            "Explicit source-preserving phone presentation required"
        )
    end = 0
    for shot in plan.get("shots", []):
        a, b = shot["start_seconds"], shot["end_seconds"]
        if (
            not all(
                isinstance(n, (int, float))
                and not isinstance(n, bool)
                and math.isfinite(n)
                for n in (a, b)
            )
            or a != end
            or not a < b <= duration
            or shot.get("framing") not in {"SPEAKER_CENTER", "FULL_SOURCE"}
        ):
            raise relay.SpeechRelayError(
                "Continuous source-picture framing plan required"
            )
        end = b
    if end != duration:
        raise relay.SpeechRelayError("Framing must cover the whole unchanged cut")


def render(clip, target, source, meaning, duration, plan, cues):
    validate_presentation(plan, duration)
    executable = shutil.which("ffmpeg")
    if not executable:
        raise relay.SpeechRelayError("ffmpeg required")
    probe = relay.probe_media(clip)
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    width, height = video["width"], video["height"]
    bold, regular = relay._font(True), relay._font()
    directory = target.parent
    texts = {
        "hook": (meaning["headline"], 54, 920, 2, True),
        "credit": (
            f"{source['speaker']['name']} | {source['event_date']}",
            32,
            940,
            2,
            True,
        ),
        "publisher": (f"Source: {source['publisher']}", 23, 940, 2, False),
        "context": (" ".join(meaning["context"].split()), 35, 920, 3, False),
    }
    for i, cue in enumerate(cues or []):
        texts[f"cue{i}"] = (cue.text, 48, 910, 3, True)
    for name, (text, size, w, lines, is_bold) in texts.items():
        # This FFmpeg build treats CRLF as two breaks. Keep the measured LF layout.
        (directory / f"phone_{name}.txt").write_bytes(
            relay._wrapped(text, bold if is_bold else regular, size, w, lines).encode(
                "utf-8"
            )
        )
    fonts = {
        True: bold.as_posix().replace(":", "\\:"),
        False: regular.as_posix().replace(":", "\\:"),
    }

    def draw(name, y, size, is_bold=False, color="white", enable=""):
        return f"drawtext=textfile=phone_{name}.txt:expansion=none:fontfile='{fonts[is_bold]}':fontsize={size}:fontcolor={color}:line_spacing=8:x=70:y={y}{enable}"

    # Picture uses explicit shot-aware framing, never a blind crop of a room-wide cut.
    n = len(plan["shots"])
    filters = (
        [f"[0:v]split={n}" + "".join(f"[s{i}]" for i in range(n))]
        if n > 1
        else ["[0:v]null[s0]"]
    )
    for i, shot in enumerate(plan["shots"]):
        crop = ""
        if shot["framing"] == "SPEAKER_CENTER":
            cropwidth = int(width * 0.625) // 2 * 2
            crop = f"crop={cropwidth}:{height}:{(width - cropwidth) // 2}:0,"
        filters.append(
            f"[s{i}]trim=start={shot['start_seconds']:.6f}:end={shot['end_seconds']:.6f},setpts=PTS-STARTPTS,{crop}scale=1080:1040:force_original_aspect_ratio=decrease,pad=1080:1040:(ow-iw)/2:(oh-ih)/2:color=0x0b1420,setsar=1[v{i}]"
        )
    filters.append(
        "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[picture]"
    )
    filters.extend(
        [
            f"color=c=0x0b1420:s=1080x1920:r=30:d={duration:.6f}[bg]",
            "[bg][picture]overlay=0:260,"
            + f"drawtext=text='CAPITAL CHRONICLE | DATED REMARKS':fontfile='{fonts[True]}':fontsize=25:fontcolor=0xf2bc66:x=70:y=64,"
            + f"{draw('hook', 122, 54, True)},{draw('credit', 1330, 32, True)},"
            + "drawbox=x=45:y=1415:w=970:h=190:color=0x142638:t=fill,"
            + f"{draw('context', 1645, 35)},{draw('publisher', 1802, 23, color='0xb6c7d8')},"
            + f"drawtext=text='PRIVATE REVIEW | AUDIO UNVERIFIED':fontfile='{fonts[True]}':fontsize=24:fontcolor=0xf2bc66:x=70:y=1875[base]",
        ]
    )
    last = "base"
    for i, cue in enumerate(cues or []):
        enable = f":enable='gte(t,{cue.start_seconds:.6f})*lt(t,{cue.end_seconds:.6f})'"
        filters.append(
            f"[{last}]{draw(f'cue{i}', 1440, 48, True, '0xffe0a6', enable)}[c{i}]"
        )
        last = f"c{i}"
    relay._run_local(
        [
            executable,
            "-v",
            "error",
            "-nostdin",
            "-n",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(clip),
            "-filter_complex",
            ";".join(filters),
            "-map",
            f"[{last}]",
            "-map",
            "0:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",
            "-t",
            f"{duration:.6f}",
            "-movflags",
            "+faststart",
            target.name,
        ],
        cwd=directory,
    )
