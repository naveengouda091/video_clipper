import os
import re
import subprocess
from dataclasses import dataclass
from typing import Optional
from core.ffmpeg_locator import get_ffmpeg_path


@dataclass
class VideoInfo:
    file_path: str
    file_name: str
    duration_seconds: float
    duration_str: str
    resolution: str
    width: int
    height: int
    video_codec: str
    audio_codec: str
    fps: float
    bitrate_str: str
    size_bytes: int
    size_str: str

    def to_dict(self):
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "duration_seconds": self.duration_seconds,
            "duration_str": self.duration_str,
            "resolution": self.resolution,
            "width": self.width,
            "height": self.height,
            "video_codec": self.video_codec,
            "audio_codec": self.audio_codec,
            "fps": self.fps,
            "bitrate_str": self.bitrate_str,
            "size_bytes": self.size_bytes,
            "size_str": self.size_str,
        }


def format_seconds(seconds: float) -> str:
    """Formats seconds into HH:MM:SS or MM:SS."""
    total_sec = max(0, int(seconds))
    hrs = total_sec // 3600
    mins = (total_sec % 3600) // 60
    secs = total_sec % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def format_bytes(num_bytes: int) -> str:
    """Formats file size into human-readable B, KB, MB, GB."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def parse_duration_to_seconds(time_str: str) -> float:
    """Parses 'HH:MM:SS.xx' or 'MM:SS' into float seconds."""
    parts = time_str.strip().split(":")
    if len(parts) == 3:
        h, m, s = parts
        return float(h) * 3600 + float(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return float(m) * 60 + float(s)
    elif len(parts) == 1:
        return float(parts[0])
    return 0.0


def extract_video_info(file_path: str) -> VideoInfo:
    """
    Inspects a video file using FFmpeg and extracts its duration,
    resolution, codecs, bitrate, fps, and file size.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    ffmpeg_exe = get_ffmpeg_path()

    cmd = [ffmpeg_exe, "-hide_banner", "-i", file_path]
    res = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        text=True,
        errors="replace"
    )
    output = res.stderr

    # Duration and bitrate extraction
    # Duration: 00:05:23.45, start: 0.000000, bitrate: 1250 kb/s
    dur_match = re.search(r"Duration:\s*(\d+:\d+:\d+(?:\.\d+)?)", output)
    duration_sec = 0.0
    duration_str = "00:00"
    if dur_match:
        raw_dur = dur_match.group(1)
        duration_sec = parse_duration_to_seconds(raw_dur)
        duration_str = format_seconds(duration_sec)

    bitrate_match = re.search(r"bitrate:\s*(\d+\s*kb/s)", output)
    bitrate_str = bitrate_match.group(1) if bitrate_match else "N/A"

    # Video stream extraction
    # Stream #0:0[0x1]: Video: h264 (...), yuv420p, 1920x1080 [...], 30 fps
    video_codec = "N/A"
    resolution = "N/A"
    width = 0
    height = 0
    fps = 0.0

    video_match = re.search(
        r"Stream.*Video:\s*([a-zA-Z0-9_\-]+).*?,\s*(\d{2,5})x(\d{2,5})",
        output
    )
    if video_match:
        video_codec = video_match.group(1)
        width = int(video_match.group(2))
        height = int(video_match.group(3))
        resolution = f"{width}x{height}"

    fps_match = re.search(r"(\d+(?:\.\d+)?)\s*fps", output)
    if fps_match:
        fps = float(fps_match.group(1))

    # Audio stream extraction
    # Stream #0:1: Audio: aac (LC)...
    audio_codec = "N/A"
    audio_match = re.search(r"Stream.*Audio:\s*([a-zA-Z0-9_\-]+)", output)
    if audio_match:
        audio_codec = audio_match.group(1)

    return VideoInfo(
        file_path=os.path.abspath(file_path),
        file_name=file_name,
        duration_seconds=duration_sec,
        duration_str=duration_str,
        resolution=resolution,
        width=width,
        height=height,
        video_codec=video_codec,
        audio_codec=audio_codec,
        fps=fps,
        bitrate_str=bitrate_str,
        size_bytes=file_size,
        size_str=format_bytes(file_size)
    )
