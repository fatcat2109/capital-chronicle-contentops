from pathlib import Path

from live_contentops.source_chart_short_video_v1 import build_chart_sequence_command


def test_chart_sequence_command_uses_only_supplied_chart_paths(tmp_path: Path):
    charts = []
    for index in range(3):
        path = tmp_path / f"chart_{index}.png"
        path.write_bytes(b"chart")
        charts.append(path)
    output = tmp_path / "short.mp4"
    command = build_chart_sequence_command(
        ffmpeg_binary="ffmpeg",
        chart_paths=charts,
        output_path=output,
    )
    joined = " ".join(command)
    assert "concat=n=3" in joined
    assert "color=white" in joined
    assert "drawtext" not in joined
    assert all(str(path.resolve()) in command for path in charts)
    assert str(output.resolve()) == command[-1]
