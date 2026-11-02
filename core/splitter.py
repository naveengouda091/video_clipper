import json
import math
import os
import subprocess
import threading
from typing import Callable, List, Optional, Tuple

from core.ffmpeg_locator import get_ffmpeg_path
from core.video_info import VideoInfo, extract_video_info, format_seconds


class SplitProgress:
    def __init__(
        self,
        current_part: int,
        total_parts: int,
        output_file: str,
        start_time_sec: float,
        end_time_sec: float,
        percentage: float,
        message: str
    ):
        self.current_part = current_part
        self.total_parts = total_parts
        self.output_file = output_file
        self.start_time_sec = start_time_sec
        self.end_time_sec = end_time_sec
        self.percentage = percentage
        self.message = message


def sanitize_filename(name: str) -> str:
    """Removes or replaces invalid characters for Windows/OS filenames."""
    invalid_chars = '<>:"/\\|?*'
    for ch in invalid_chars:
        name = name.replace(ch, "_")
    return name.strip()


def calculate_segments(
    total_duration: float,
    segment_duration: Optional[float] = None,
    num_parts: Optional[int] = None
) -> List[Tuple[float, float]]:
    """
    Computes a list of (start_sec, end_sec) tuples based on total duration
    and either a target segment duration or target number of parts.
    """
    if total_duration <= 0:
        return []

    segments: List[Tuple[float, float]] = []

    if num_parts and num_parts > 0:
        part_len = total_duration / num_parts
        for i in range(num_parts):
            s = i * part_len
            e = min(total_duration, (i + 1) * part_len)
            segments.append((s, e))
    elif segment_duration and segment_duration > 0:
        cur = 0.0
        while cur < total_duration:
            nxt = min(total_duration, cur + segment_duration)
            segments.append((cur, nxt))
            cur = nxt
    else:
        segments.append((0.0, total_duration))

    return segments


class VideoSplitter:
    """
    High-performance video splitter supporting zero quality loss (stream copy)
    and frame-accurate cutting.
    """

    def __init__(self):
        self._current_process: Optional[subprocess.Popen] = None
        self._cancel_requested = False
        self._lock = threading.Lock()

    def cancel(self):
        """Cancels an in-progress splitting operation immediately."""
        with self._lock:
            self._cancel_requested = True
            if self._current_process and self._current_process.poll() is None:
                try:
                    self._current_process.terminate()
                except Exception:
                    pass

    def reset(self):
        with self._lock:
            self._cancel_requested = False
            self._current_process = None

    def split_video(
        self,
        input_file: str,
        output_dir: Optional[str] = None,
        segment_duration_sec: Optional[float] = None,
        num_parts: Optional[int] = None,
        custom_ranges: Optional[List[Tuple[float, float]]] = None,
        mode: str = "lossless",  # "lossless" or "accurate"
        prefix: Optional[str] = None,
        naming_format: str = "number_only",  # "number_only" (001, 002...) or "prefix_number" (name_001...)
        progress_cb: Optional[Callable[[SplitProgress], None]] = None
    ) -> List[str]:
        """
        Splits a video file into multiple parts.

        :param input_file: Path to source video file
        :param output_dir: Destination folder. Defaults to '<VideoName>_clips' next to input
        :param segment_duration_sec: Target length for each clip in seconds (e.g. 60.0 for 1 min)
        :param num_parts: Alternatively, split into N equal parts
        :param custom_ranges: Optional list of explicit [(start_sec, end_sec), ...] ranges
        :param mode: "lossless" (stream copy, 100% original quality, ultra-fast) or
                     "accurate" (frame-exact visually lossless re-encode)
        :param prefix: Optional output filename prefix
        :param naming_format: "number_only" (e.g. 001.mp4, 002.mp4) or "prefix_number" (e.g. video_001.mp4)
        :param progress_cb: Optional callback receiving SplitProgress objects
        :return: List of generated output file paths
        """
        self.reset()
        ffmpeg_exe = get_ffmpeg_path()
        video_info = extract_video_info(input_file)

        base_name, ext = os.path.splitext(os.path.basename(input_file))
        clean_base = sanitize_filename(prefix or base_name)

        if not output_dir:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(input_file)), f"{clean_base}_clips")
        os.makedirs(output_dir, exist_ok=True)

        # Determine segment ranges
        if custom_ranges:
            segments = custom_ranges
        else:
            segments = calculate_segments(
                total_duration=video_info.duration_seconds,
                segment_duration=segment_duration_sec,
                num_parts=num_parts
            )

        if not segments:
            raise ValueError("No segments generated. Video duration might be 0.")

        total_segments = len(segments)
        output_files: List[str] = []
        manifest_entries = []

        for idx, (start_sec, end_sec) in enumerate(segments, 1):
            with self._lock:
                if self._cancel_requested:
                    break

            part_num_str = f"{idx:03d}"
            if naming_format == "prefix_number" or (prefix and naming_format != "number_only"):
                part_filename = f"{clean_base}_{part_num_str}{ext}"
            else:
                part_filename = f"{part_num_str}{ext}"
            part_path = os.path.join(output_dir, part_filename)

            # Format start & duration for ffmpeg
            # Using -ss {start} -to {end} -i ...
            start_str = f"{start_sec:.3f}"
            end_str = f"{end_sec:.3f}"
            duration = end_sec - start_sec

            if mode == "lossless":
                # -c copy copies packets losslessly without decoding or re-encoding.
                # -avoid_negative_ts make_zero shifts timestamps cleanly.
                # -map 0 retains all audio, video, subtitle streams.
                cmd = [
                    ffmpeg_exe,
                    "-y",
                    "-ss", start_str,
                    "-to", end_str,
                    "-i", input_file,
                    "-c", "copy",
                    "-map", "0",
                    "-avoid_negative_ts", "make_zero",
                    part_path
                ]
            else:
                # Frame-accurate mode: visually lossless re-encode
                cmd = [
                    ffmpeg_exe,
                    "-y",
                    "-ss", start_str,
                    "-to", end_str,
                    "-i", input_file,
                    "-c:v", "libx264",
                    "-crf", "17",
                    "-preset", "veryfast",
                    "-c:a", "copy",
                    "-avoid_negative_ts", "make_zero",
                    part_path
                ]

            if progress_cb:
                pct = ((idx - 1) / total_segments) * 100.0
                msg = f"Clipping part {idx}/{total_segments} ({format_seconds(start_sec)} -> {format_seconds(end_sec)})..."
                progress_cb(SplitProgress(
                    current_part=idx,
                    total_parts=total_segments,
                    output_file=part_path,
                    start_time_sec=start_sec,
                    end_time_sec=end_sec,
                    percentage=pct,
                    message=msg
                ))

            with self._lock:
                if self._cancel_requested:
                    break
                self._current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    text=True
                )

            stdout, stderr = self._current_process.communicate()
            ret_code = self._current_process.returncode

            with self._lock:
                if self._cancel_requested:
                    # Clean up partially written file
                    if os.path.exists(part_path):
                        try:
                            os.remove(part_path)
                        except Exception:
                            pass
                    break

            if ret_code != 0:
                raise RuntimeError(
                    f"FFmpeg failed while generating part {idx} ({part_filename}):\n{stderr}"
                )

            if os.path.isfile(part_path):
                output_files.append(part_path)
                file_sz = os.path.getsize(part_path)
                manifest_entries.append({
                    "part": idx,
                    "filename": part_filename,
                    "file_path": part_path,
                    "start_sec": start_sec,
                    "end_sec": end_sec,
                    "duration_sec": duration,
                    "start_timestamp": format_seconds(start_sec),
                    "end_timestamp": format_seconds(end_sec),
                    "duration_timestamp": format_seconds(duration),
                    "size_bytes": file_sz
                })

        # Final progress update
        if progress_cb:
            with self._lock:
                cancelled = self._cancel_requested
            if cancelled:
                progress_cb(SplitProgress(
                    current_part=len(output_files),
                    total_parts=total_segments,
                    output_file="",
                    start_time_sec=0,
                    end_time_sec=0,
                    percentage=0,
                    message="Cancelled by user."
                ))
            else:
                progress_cb(SplitProgress(
                    current_part=total_segments,
                    total_parts=total_segments,
                    output_file=output_files[-1] if output_files else "",
                    start_time_sec=0,
                    end_time_sec=video_info.duration_seconds,
                    percentage=100.0,
                    message=f"Complete! Generated {len(output_files)} clips in {output_dir}"
                ))

        # Write manifest summary JSON into the output folder
        if output_files:
            manifest_path = os.path.join(output_dir, "manifest.json")
            try:
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "source_video": video_info.to_dict(),
                        "mode": mode,
                        "total_clips": len(output_files),
                        "clips": manifest_entries
                    }, f, indent=2)
            except Exception:
                pass

        return output_files
