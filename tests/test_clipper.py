import json
import os
import shutil
import subprocess
import unittest

from core.ffmpeg_locator import get_ffmpeg_path
from core.splitter import VideoSplitter, calculate_segments
from core.video_info import extract_video_info, format_seconds, parse_duration_to_seconds
from cli import parse_time_input


class TestClipper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ffmpeg_exe = get_ffmpeg_path()
        cls.test_dir = os.path.abspath("test_tmp_dir")
        os.makedirs(cls.test_dir, exist_ok=True)

        cls.sample_video = os.path.join(cls.test_dir, "sample_test.mp4")
        # Create a 10-second 30fps test video with audio
        cmd = [
            cls.ffmpeg_exe, "-y",
            "-f", "lavfi", "-i", "testsrc=duration=10:size=320x240:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=10",
            "-c:v", "libx264", "-g", "30",
            "-c:a", "aac",
            cls.sample_video
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"FFmpeg failed to create test video: {res.stderr}"

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_ffmpeg_found(self):
        self.assertTrue(os.path.isfile(self.ffmpeg_exe))

    def test_extract_video_info(self):
        info = extract_video_info(self.sample_video)
        self.assertAlmostEqual(info.duration_seconds, 10.0, delta=0.5)
        self.assertEqual(info.resolution, "320x240")
        self.assertEqual(info.fps, 30.0)
        self.assertIn("h264", info.video_codec.lower())
        self.assertIn("aac", info.audio_codec.lower())

    def test_calculate_segments(self):
        # 10s video split into 3s chunks -> [(0,3), (3,6), (6,9), (9,10)]
        segs = calculate_segments(10.0, segment_duration=3.0)
        self.assertEqual(len(segs), 4)
        self.assertEqual(segs[0], (0.0, 3.0))
        self.assertEqual(segs[-1], (9.0, 10.0))

        # Split into 5 equal parts -> 2s each
        segs_parts = calculate_segments(10.0, num_parts=5)
        self.assertEqual(len(segs_parts), 5)
        self.assertEqual(segs_parts[0], (0.0, 2.0))
        self.assertEqual(segs_parts[4], (8.0, 10.0))

    def test_parse_time_input(self):
        self.assertEqual(parse_time_input("60"), 60.0)
        self.assertEqual(parse_time_input("60s"), 60.0)
        self.assertEqual(parse_time_input("1m"), 60.0)
        self.assertEqual(parse_time_input("1.5m"), 90.0)
        self.assertEqual(parse_time_input("1m30s"), 90.0)
        self.assertEqual(parse_time_input("01:30"), 90.0)
        self.assertEqual(parse_time_input("01:00:00"), 3600.0)

    def test_lossless_split(self):
        splitter = VideoSplitter()
        out_dir = os.path.join(self.test_dir, "lossless_clips")
        clips = splitter.split_video(
            input_file=self.sample_video,
            output_dir=out_dir,
            segment_duration_sec=3.0,
            mode="lossless"
        )
        self.assertEqual(len(clips), 4)
        # Verify filenames start with 001, 002, 003, 004
        self.assertEqual(os.path.basename(clips[0]), "001.mp4")
        self.assertEqual(os.path.basename(clips[1]), "002.mp4")
        self.assertEqual(os.path.basename(clips[2]), "003.mp4")
        self.assertEqual(os.path.basename(clips[3]), "004.mp4")

        for clip in clips:
            self.assertTrue(os.path.isfile(clip))
            self.assertGreater(os.path.getsize(clip), 0)

        # Verify manifest.json
        manifest_file = os.path.join(out_dir, "manifest.json")
        self.assertTrue(os.path.isfile(manifest_file))
        with open(manifest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["total_clips"], 4)
            self.assertEqual(len(data["clips"]), 4)


if __name__ == "__main__":
    unittest.main()
