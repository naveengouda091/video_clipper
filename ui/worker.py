from typing import List, Optional
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from core.splitter import SplitProgress, VideoSplitter
from core.video_info import VideoInfo, extract_video_info


class VideoInfoWorker(QThread):
    """Asynchronously extracts metadata for a selected video file."""
    info_ready = pyqtSignal(VideoInfo)
    error = pyqtSignal(str)

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            info = extract_video_info(self.file_path)
            self.info_ready.emit(info)
        except Exception as e:
            self.error.emit(str(e))


class VideoSplitWorker(QThread):
    """Asynchronously splits a video using VideoSplitter in a background thread."""
    progress = pyqtSignal(SplitProgress)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(
        self,
        input_file: str,
        output_dir: Optional[str] = None,
        segment_duration_sec: Optional[float] = None,
        num_parts: Optional[int] = None,
        mode: str = "lossless",
        prefix: Optional[str] = None
    ):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir
        self.segment_duration_sec = segment_duration_sec
        self.num_parts = num_parts
        self.mode = mode
        self.prefix = prefix
        self.splitter = VideoSplitter()

    def cancel(self):
        self.splitter.cancel()

    def run(self):
        try:
            output_clips = self.splitter.split_video(
                input_file=self.input_file,
                output_dir=self.output_dir,
                segment_duration_sec=self.segment_duration_sec,
                num_parts=self.num_parts,
                mode=self.mode,
                prefix=self.prefix,
                progress_cb=lambda p: self.progress.emit(p)
            )
            if self.splitter._cancel_requested:
                self.cancelled.emit()
            else:
                self.finished.emit(output_clips)
        except Exception as e:
            self.error.emit(str(e))
