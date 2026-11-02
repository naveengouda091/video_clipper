import argparse
import os
import re
import sys
from typing import Optional

from core.ffmpeg_locator import get_ffmpeg_path
from core.splitter import VideoSplitter
from core.video_info import extract_video_info, format_seconds


def parse_time_input(val: str) -> float:
    """
    Parses flexible duration strings:
    '60' -> 60.0
    '60s' -> 60.0
    '1m' -> 60.0
    '1.5m' -> 90.0
    '1m30s' -> 90.0
    '01:30' -> 90.0
    '01:00:00' -> 3600.0
    """
    val = val.strip().lower()

    # Colon format: HH:MM:SS or MM:SS
    if ":" in val:
        parts = val.split(":")
        if len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])

    # Format like 1m30s, 2m, 45s
    match_ms = re.match(r"^(?:(\d+(?:\.\d+)?)m)?\s*(?:(\d+(?:\.\d+)?)s)?$", val)
    if match_ms and (match_ms.group(1) or match_ms.group(2)):
        minutes = float(match_ms.group(1)) if match_ms.group(1) else 0.0
        seconds = float(match_ms.group(2)) if match_ms.group(2) else 0.0
        return minutes * 60.0 + seconds

    # Plain float
    try:
        return float(val)
    except ValueError:
        raise ValueError(
            f"Cannot parse duration '{val}'. Use e.g. '60', '1m', '1m30s', or '01:00'."
        )


def main():
    parser = argparse.ArgumentParser(
        description="Clipper CLI - Lossless Video Splitter (1 min, custom min, or parts)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py video.mp4                        # Split into 1-minute lossless clips
  python cli.py video.mp4 -d 30s                 # Split into 30-second clips
  python cli.py video.mp4 -d 2m -o ./clips/      # Split into 2-minute clips in ./clips/
  python cli.py video.mp4 --parts 4              # Split into 4 equal segments
  python cli.py video.mp4 --mode accurate        # Frame-accurate cut (visually lossless)
  python cli.py video.mp4 --info                 # Print video details only
        """
    )
    parser.add_argument("input", help="Path to input video file")
    parser.add_argument(
        "-d", "--duration",
        default="60s",
        help="Target clip duration (e.g. '60s', '1m', '90', '1m30s', '01:00'). Default: 60s"
    )
    parser.add_argument(
        "-p", "--parts",
        type=int,
        default=None,
        help="Split into N equal parts instead of fixed duration"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output directory (default: '<video_name>_clips')"
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["lossless", "accurate"],
        default="lossless",
        help="Cutting mode: 'lossless' (zero quality loss, instant) or 'accurate' (frame-exact re-encode)"
    )
    parser.add_argument(
        "--naming",
        choices=["number", "prefix"],
        default="number",
        help="Naming pattern: 'number' (001.mp4, 002.mp4... [default]) or 'prefix' (video_001.mp4...)"
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help="Custom prefix for output filenames (overrides number-only naming)"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show video info only and exit"
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open destination folder after completion"
    )

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: Input video not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        ffmpeg_exe = get_ffmpeg_path()
    except Exception as e:
        print(f"Error finding FFmpeg: {e}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print(" 🎬 CLIPPER - LOSSLESS VIDEO CUTTER")
    print("=" * 60)

    try:
        info = extract_video_info(args.input)
    except Exception as e:
        print(f"Error probing video: {e}", file=sys.stderr)
        sys.exit(1)

    print(f" Source File  : {info.file_name}")
    print(f" Duration     : {info.duration_str} ({info.duration_seconds:.2f}s)")
    print(f" Resolution   : {info.resolution} @ {info.fps:.2f} fps")
    print(f" Codecs       : Video: {info.video_codec} | Audio: {info.audio_codec}")
    print(f" File Size    : {info.size_str}")
    print(f" Mode         : {args.mode.upper()} {'(Zero quality loss, stream copy)' if args.mode == 'lossless' else '(Frame-accurate visually lossless)'}")
    print("=" * 60)

    if args.info:
        sys.exit(0)

    duration_sec: Optional[float] = None
    if not args.parts:
        try:
            duration_sec = parse_time_input(args.duration)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    splitter = VideoSplitter()

    def on_progress(p):
        bar_len = 30
        filled = int(bar_len * (p.percentage / 100.0))
        bar = "█" * filled + "░" * (bar_len - filled)
        sys.stdout.write(f"\r[{bar}] {p.percentage:5.1f}% | {p.message}")
        sys.stdout.flush()

    try:
        clips = splitter.split_video(
            input_file=args.input,
            output_dir=args.output,
            segment_duration_sec=duration_sec,
            num_parts=args.parts,
            mode=args.mode,
            prefix=args.prefix,
            naming_format="number_only" if args.naming == "number" and not args.prefix else "prefix_number",
            progress_cb=on_progress
        )
        print("\n")
        print("=" * 60)
        print(f"✨ Successfully generated {len(clips)} clip(s)!")
        out_folder = os.path.dirname(clips[0]) if clips else args.output
        print(f"📁 Destination: {out_folder}")
        print("=" * 60)

        if args.open and out_folder:
            if sys.platform == "win32":
                os.startfile(out_folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", out_folder])
            else:
                subprocess.Popen(["xdg-open", out_folder])

    except KeyboardInterrupt:
        splitter.cancel()
        print("\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nFailed to split video: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
