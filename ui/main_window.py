import math
import os
import subprocess
import sys
from typing import Optional

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QColor, QDragEnterEvent, QDropEvent, QFont, QIcon
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.splitter import SplitProgress, calculate_segments
from core.video_info import VideoInfo, format_bytes, format_seconds
from ui.styles import DARK_THEME_QSS
from ui.worker import VideoInfoWorker, VideoSplitWorker


class DropZoneWidget(QFrame):
    """Drop zone for drag-and-drop video file selection."""

    def __init__(self, on_file_selected):
        super().__init__()
        self.on_file_selected = on_file_selected
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        self.icon_label = QLabel("🎬")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 38px; background: transparent;")

        self.main_text = QLabel("Drag & Drop your video file here")
        self.main_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_text.setStyleSheet(
            "font-size: 15px; font-weight: 700; color: #f8fafc; background: transparent;"
        )

        self.sub_text = QLabel("Supports MP4, MKV, MOV, WEBM, AVI, TS")
        self.sub_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_text.setStyleSheet(
            "font-size: 12px; color: #94a3b8; background: transparent;"
        )

        self.browse_btn = QPushButton("📁 Browse File...")
        self.browse_btn.setFixedWidth(160)
        self.browse_btn.clicked.connect(self._browse)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.main_text)
        layout.addWidget(self.sub_text)
        layout.addSpacing(6)
        layout.addWidget(self.browse_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._browse()

    def _browse(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.mkv *.mov *.webm *.avi *.ts *.m4v);;All Files (*.*)"
        )
        if file_path:
            self.on_file_selected(file_path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.isfile(path):
                self.on_file_selected(path)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clipper — Lossless Video Splitter")
        self.resize(840, 800)
        self.setMinimumSize(720, 680)
        self.setStyleSheet(DARK_THEME_QSS)

        self.current_video_info: Optional[VideoInfo] = None
        self.split_worker: Optional[VideoSplitWorker] = None
        self.info_worker: Optional[VideoInfoWorker] = None
        self.selected_preset_sec: float = 60.0  # Default 1 minute
        self.custom_output_dir: Optional[str] = None

        self._build_ui()

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(28, 24, 28, 28)
        self.main_layout.setSpacing(18)

        # 1. Header
        self._build_header()

        # 2. Drop Zone
        self.drop_zone = DropZoneWidget(self._load_video)
        self.main_layout.addWidget(self.drop_zone)

        # 3. Video Metadata Card
        self.meta_card = self._build_meta_card()
        self.meta_card.setVisible(False)
        self.main_layout.addWidget(self.meta_card)

        # 4. Clipping Configuration Card
        self.config_card = self._build_config_card()
        self.main_layout.addWidget(self.config_card)

        # 5. Action & Progress Area
        self._build_action_area()

        # 6. Results Card
        self.results_card = self._build_results_card()
        self.results_card.setVisible(False)
        self.main_layout.addWidget(self.results_card)

        scroll.setWidget(container)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(scroll)

    def _build_header(self):
        header = QFrame()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 8)

        titles_box = QVBoxLayout()
        title = QLabel("✂️ Clipper")
        title.setObjectName("headerTitle")
        sub = QLabel("Lossless video cutter • 100% Quality Preserved • Instant Stream Copy")
        sub.setObjectName("headerSubtitle")

        titles_box.addWidget(title)
        titles_box.addWidget(sub)
        h_layout.addLayout(titles_box)
        h_layout.addStretch()

        self.main_layout.addWidget(header)

    def _build_meta_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("cardFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        title = QLabel("Source Video Details")
        title.setObjectName("sectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self.btn_change_file = QPushButton("Change Video")
        self.btn_change_file.setFixedHeight(28)
        self.btn_change_file.clicked.connect(self.drop_zone._browse)
        header_row.addWidget(self.btn_change_file)
        layout.addLayout(header_row)

        self.lbl_filename = QLabel("Filename: -")
        self.lbl_filename.setStyleSheet("font-size: 14px; font-weight: 700; color: #f8fafc;")
        layout.addWidget(self.lbl_filename)

        # Badges row
        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(10)

        self.badge_duration = QLabel("⏱️ Duration: -")
        self.badge_duration.setObjectName("metaBadge")

        self.badge_resolution = QLabel("📐 Res: -")
        self.badge_resolution.setObjectName("metaBadge")

        self.badge_fps = QLabel("⚡ FPS: -")
        self.badge_fps.setObjectName("metaBadge")

        self.badge_codec = QLabel("🎞️ Codec: -")
        self.badge_codec.setObjectName("metaBadge")

        self.badge_size = QLabel("💾 Size: -")
        self.badge_size.setObjectName("metaBadge")

        badges_layout.addWidget(self.badge_duration)
        badges_layout.addWidget(self.badge_resolution)
        badges_layout.addWidget(self.badge_fps)
        badges_layout.addWidget(self.badge_codec)
        badges_layout.addWidget(self.badge_size)
        badges_layout.addStretch()

        layout.addLayout(badges_layout)
        return card

    def _build_config_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("cardFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(16)

        title = QLabel("Clip Settings")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # Presets Buttons Row
        lbl_presets = QLabel("Clip Length Preset:")
        lbl_presets.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        layout.addWidget(lbl_presets)

        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(8)

        self.btn_group_presets = QButtonGroup(self)
        self.btn_group_presets.setExclusive(True)

        presets = [
            ("30s", 30.0),
            ("60s (1 min)", 60.0),
            ("90s", 90.0),
            ("2 min", 120.0),
            ("3 min", 180.0),
            ("5 min", 300.0),
            ("Custom Duration", -1.0),
            ("Equal Parts", -2.0)
        ]

        self.preset_buttons = {}
        for text, val in presets:
            btn = QPushButton(text)
            btn.setProperty("class", "presetChip")
            btn.setCheckable(True)
            self.btn_group_presets.addButton(btn)
            presets_layout.addWidget(btn)
            self.preset_buttons[val] = btn
            btn.clicked.connect(lambda checked, v=val: self._on_preset_clicked(v))

        # Default select 60s (1 min)
        self.preset_buttons[60.0].setChecked(True)
        self.selected_preset_sec = 60.0

        layout.addLayout(presets_layout)

        # Dynamic Custom Duration Controls
        self.custom_row = QWidget()
        c_layout = QHBoxLayout(self.custom_row)
        c_layout.setContentsMargins(0, 4, 0, 0)
        c_layout.setSpacing(12)

        self.lbl_custom = QLabel("Custom Seconds:")
        self.lbl_custom.setStyleSheet("font-weight: 600;")
        self.spin_custom_sec = QDoubleSpinBox()
        self.spin_custom_sec.setRange(1.0, 7200.0)
        self.spin_custom_sec.setValue(60.0)
        self.spin_custom_sec.setSuffix(" sec")
        self.spin_custom_sec.valueChanged.connect(self._update_estimate)

        self.lbl_parts = QLabel("Number of Parts:")
        self.lbl_parts.setStyleSheet("font-weight: 600;")
        self.spin_parts = QSpinBox()
        self.spin_parts.setRange(2, 200)
        self.spin_parts.setValue(4)
        self.spin_parts.valueChanged.connect(self._update_estimate)

        c_layout.addWidget(self.lbl_custom)
        c_layout.addWidget(self.spin_custom_sec)
        c_layout.addWidget(self.lbl_parts)
        c_layout.addWidget(self.spin_parts)
        c_layout.addStretch()

        self.custom_row.setVisible(False)
        layout.addWidget(self.custom_row)

        # Mode Selection & Output Folder
        grid = QGridLayout()
        grid.setSpacing(12)

        lbl_mode = QLabel("Cutting Mode:")
        lbl_mode.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.combo_mode = QComboBox()
        self.combo_mode.addItem("⚡ Lossless (Zero Quality Loss, Instant Stream-Copy)", "lossless")
        self.combo_mode.addItem("🎯 Frame Accurate (Visually Lossless Re-encode)", "accurate")

        lbl_dest = QLabel("Output Folder:")
        lbl_dest.setStyleSheet("font-weight: 600; color: #cbd5e1;")

        dest_row = QHBoxLayout()
        self.txt_dest = QLineEdit()
        self.txt_dest.setPlaceholderText("Auto: <video_name>_clips next to source file")
        self.btn_browse_dest = QPushButton("📁 Choose...")
        self.btn_browse_dest.clicked.connect(self._browse_dest)
        dest_row.addWidget(self.txt_dest)
        dest_row.addWidget(self.btn_browse_dest)

        grid.addWidget(lbl_mode, 0, 0)
        grid.addWidget(self.combo_mode, 0, 1)
        grid.addWidget(lbl_dest, 1, 0)
        grid.addLayout(dest_row, 1, 1)

        layout.addLayout(grid)

        # Estimate badge
        self.lbl_estimate = QLabel("💡 Load a video to see estimated clip breakdown")
        self.lbl_estimate.setStyleSheet("font-size: 13px; font-weight: 600; color: #38bdf8;")
        layout.addWidget(self.lbl_estimate)

        return card

    def _build_action_area(self):
        act_box = QVBoxLayout()
        act_box.setSpacing(10)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.btn_split = QPushButton("🚀 Split Video Now (0% Quality Loss)")
        self.btn_split.setObjectName("primaryButton")
        self.btn_split.setEnabled(False)
        self.btn_split.clicked.connect(self._start_split)

        self.btn_cancel = QPushButton("✖ Cancel")
        self.btn_cancel.setObjectName("dangerButton")
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self._cancel_split)

        btn_row.addWidget(self.btn_split, stretch=4)
        btn_row.addWidget(self.btn_cancel, stretch=1)
        act_box.addLayout(btn_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        act_box.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setObjectName("statusText")
        self.lbl_status.setVisible(False)
        act_box.addWidget(self.lbl_status)

        self.main_layout.addLayout(act_box)

    def _build_results_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("cardFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        title = QLabel("Generated Clips")
        title.setObjectName("sectionTitle")
        top_row.addWidget(title)
        top_row.addStretch()

        self.btn_open_folder = QPushButton("📂 Open Output Folder")
        self.btn_open_folder.clicked.connect(self._open_output_folder)
        top_row.addWidget(self.btn_open_folder)

        layout.addLayout(top_row)

        self.list_clips = QListWidget()
        self.list_clips.setFixedHeight(180)
        self.list_clips.itemDoubleClicked.connect(self._on_clip_double_clicked)
        layout.addWidget(self.list_clips)

        hint = QLabel("💡 Tip: Double-click any clip to play it immediately in your media player.")
        hint.setStyleSheet("font-size: 11px; color: #94a3b8;")
        layout.addWidget(hint)

        return card

    def _on_preset_clicked(self, val: float):
        self.selected_preset_sec = val
        if val == -1.0:
            # Custom seconds
            self.custom_row.setVisible(True)
            self.lbl_custom.setVisible(True)
            self.spin_custom_sec.setVisible(True)
            self.lbl_parts.setVisible(False)
            self.spin_parts.setVisible(False)
        elif val == -2.0:
            # Parts
            self.custom_row.setVisible(True)
            self.lbl_custom.setVisible(False)
            self.spin_custom_sec.setVisible(False)
            self.lbl_parts.setVisible(True)
            self.spin_parts.setVisible(True)
        else:
            self.custom_row.setVisible(False)

        self._update_estimate()

    def _load_video(self, file_path: str):
        self.lbl_status.setText("Inspecting video metadata...")
        self.lbl_status.setVisible(True)

        self.info_worker = VideoInfoWorker(file_path)
        self.info_worker.info_ready.connect(self._on_info_loaded)
        self.info_worker.error.connect(self._on_info_error)
        self.info_worker.start()

    def _on_info_loaded(self, info: VideoInfo):
        self.current_video_info = info
        self.lbl_status.setVisible(False)

        # Populate meta card
        self.lbl_filename.setText(f"📹 {info.file_name}")
        self.badge_duration.setText(f"⏱️ {info.duration_str} ({info.duration_seconds:.1f}s)")
        self.badge_resolution.setText(f"📐 {info.resolution}")
        self.badge_fps.setText(f"⚡ {info.fps:.1f} FPS")
        self.badge_codec.setText(f"🎞️ {info.video_codec.upper()} / {info.audio_codec.upper()}")
        self.badge_size.setText(f"💾 {info.size_str}")

        self.meta_card.setVisible(True)
        self.drop_zone.setVisible(False)
        self.btn_split.setEnabled(True)

        self._update_estimate()

    def _on_info_error(self, err: str):
        self.lbl_status.setVisible(False)
        QMessageBox.critical(self, "Video Load Error", f"Could not inspect video:\n{err}")

    def _update_estimate(self):
        if not self.current_video_info:
            return

        dur = self.current_video_info.duration_seconds
        if dur <= 0:
            self.lbl_estimate.setText("Could not determine duration.")
            return

        if self.selected_preset_sec == -2.0:
            num_parts = self.spin_parts.value()
            segs = calculate_segments(dur, num_parts=num_parts)
            part_len = dur / num_parts
            self.lbl_estimate.setText(
                f"✂️ Will split into {num_parts} equal clips (~{format_seconds(part_len)} each)"
            )
        else:
            seg_len = (
                self.spin_custom_sec.value()
                if self.selected_preset_sec == -1.0
                else self.selected_preset_sec
            )
            segs = calculate_segments(dur, segment_duration=seg_len)
            self.lbl_estimate.setText(
                f"✂️ Will generate {len(segs)} clip(s) of ~{format_seconds(seg_len)} each"
            )

    def _browse_dest(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Destination")
        if folder:
            self.custom_output_dir = folder
            self.txt_dest.setText(folder)

    def _start_split(self):
        if not self.current_video_info:
            return

        dur = self.current_video_info.duration_seconds
        segment_sec = None
        num_parts = None

        if self.selected_preset_sec == -2.0:
            num_parts = self.spin_parts.value()
        elif self.selected_preset_sec == -1.0:
            segment_sec = self.spin_custom_sec.value()
        else:
            segment_sec = self.selected_preset_sec

        out_dir = self.txt_dest.text().strip() or None
        mode = self.combo_mode.currentData()

        # UI state during processing
        self.btn_split.setEnabled(False)
        self.btn_cancel.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.lbl_status.setVisible(True)
        self.lbl_status.setText("Starting lossless clipping engine...")
        self.results_card.setVisible(False)
        self.list_clips.clear()

        self.split_worker = VideoSplitWorker(
            input_file=self.current_video_info.file_path,
            output_dir=out_dir,
            segment_duration_sec=segment_sec,
            num_parts=num_parts,
            mode=mode
        )
        self.split_worker.progress.connect(self._on_split_progress)
        self.split_worker.finished.connect(self._on_split_finished)
        self.split_worker.error.connect(self._on_split_error)
        self.split_worker.cancelled.connect(self._on_split_cancelled)
        self.split_worker.start()

    def _cancel_split(self):
        if self.split_worker:
            self.lbl_status.setText("Cancelling...")
            self.split_worker.cancel()

    def _on_split_progress(self, p: SplitProgress):
        self.progress_bar.setValue(int(p.percentage))
        self.lbl_status.setText(p.message)

    def _on_split_finished(self, output_clips: list):
        self.btn_split.setEnabled(True)
        self.btn_cancel.setVisible(False)
        self.progress_bar.setValue(100)
        self.lbl_status.setText(f"🎉 Complete! {len(output_clips)} clips generated.")

        self.results_card.setVisible(True)
        self.list_clips.clear()
        for clip in output_clips:
            sz = format_bytes(os.path.getsize(clip)) if os.path.isfile(clip) else ""
            item = QListWidgetItem(f"🎬 {os.path.basename(clip)} ({sz})")
            item.setData(Qt.ItemDataRole.UserRole, clip)
            self.list_clips.addItem(item)

        if output_clips:
            self.custom_output_dir = os.path.dirname(output_clips[0])

    def _on_split_error(self, err: str):
        self.btn_split.setEnabled(True)
        self.btn_cancel.setVisible(False)
        self.lbl_status.setText("Error occurred.")
        QMessageBox.critical(self, "Split Error", f"An error occurred while clipping:\n{err}")

    def _on_split_cancelled(self):
        self.btn_split.setEnabled(True)
        self.btn_cancel.setVisible(False)
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Operation cancelled.")

    def _open_output_folder(self):
        folder = self.custom_output_dir
        if not folder and self.current_video_info:
            folder = os.path.dirname(self.current_video_info.file_path)

        if folder and os.path.isdir(folder):
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])

    def _on_clip_double_clicked(self, item: QListWidgetItem):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path and os.path.isfile(file_path):
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", file_path])
            else:
                subprocess.Popen(["xdg-open", file_path])
