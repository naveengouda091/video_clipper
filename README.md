# ✂️ Clipper — Lossless Video Splitter

A modern, high-performance desktop application and CLI tool that splits long videos into short **1-minute**, **custom duration**, or **equal part** clips **without losing a single pixel of quality** (0% quality loss) and at lightning-fast speeds.

---

## ⚡ How It Works: Zero Quality Loss

Traditional video editors decompress and re-encode video frames, which degrades visual quality, introduces compression artifacts, changes color spaces, and takes minutes or hours.

**Clipper** uses **Stream-Copy Mode (`-c copy`)**:
- Video and audio bitstreams are copied directly packet-by-packet without decoding or re-encoding.
- **100% Mathematically Identical Quality**: Original resolution (4K, 1080p), high framerates (60/120fps), HDR color depth, bitrates, and audio tracks remain 100% intact.
- **Extreme Speed**: Slicing an entire 1-hour 4K video takes just **1 to 3 seconds** (operating at 300x–1000x real-time speed).

---

## ✨ Features

- 🎯 **Preset Durations**: 1-click presets for **30s** (Reels/Shorts teasers), **60s (1 min)** (Standard YouTube Shorts / TikTok), **90s**, **2 min**, **3 min**, **5 min**.
- ⏱️ **Custom Durations**: Split by custom seconds or minutes (e.g. `45s`, `1.5m`, `75s`, `01:30`).
- 🔢 **Split into N Equal Parts**: Divide any long video evenly into 2, 4, 10, or more parts.
- 🎨 **Modern Dark Desktop GUI (PyQt6)**:
  - Drag-and-drop video dropzone.
  - Video metadata inspector (duration, resolution, fps, codecs, file size).
  - Real-time estimated clip count indicator before splitting.
  - Progress bar and live status feedback.
  - Generated clips list with 1-click **Play** and **Open Output Folder** buttons.
- 💻 **Powerful CLI Tool**: Automate batch processing from terminal or scripts.
- 📑 **Automatic Manifest**: Saves a structured `manifest.json` in the output folder recording every clip's start/end timestamps, durations, and file sizes.
- 🔄 **Two Cutting Engines**:
  - **⚡ Lossless Stream-Copy** *(Default & Recommended)*: 0% quality loss, instant cutting.
  - **🎯 Frame-Accurate Mode**: Visually lossless re-encoding for exact frame-level cuts.

---

## 🚀 Quick Start

### 1. Requirements

Ensure you have Python 3.10+ installed. Install dependencies:
```bash
pip install -r requirements.txt
```

> **Note**: Clipper uses `imageio-ffmpeg` which automatically bundles a standalone, high-performance FFmpeg binary on Windows. No manual FFmpeg PATH configuration is required!

### 2. Launch the Desktop Application

Double-click `run.bat` or run:
```bash
python app.py
```

---

## 💻 CLI Usage

You can also use Clipper directly from PowerShell or Command Prompt:

```bash
# Split into 1-minute clips (default)
python cli.py video.mp4

# Split into 30-second clips for TikTok/Shorts
python cli.py video.mp4 -d 30s

# Split into 2.5-minute clips and save to a custom folder
python cli.py video.mp4 -d 2m30s -o ./my_clips/

# Split video into 4 equal segments
python cli.py video.mp4 --parts 4

# View video metadata without cutting
python cli.py video.mp4 --info

# Open output folder automatically when finished
python cli.py video.mp4 -d 60s --open
```

### Supported Time Formats:
- Seconds: `60`, `60s`, `45.5`
- Minutes: `1m`, `2.5m`, `3m`
- Combined: `1m30s`, `2m15s`
- Timestamps: `01:00`, `01:30`, `00:05:00`

---

## 📂 Project Structure

```
clipper/
├── .gitignore               # Git ignore rules for builds, clips, and caches
├── README.md                # Documentation and guide
├── requirements.txt         # Python dependencies (PyQt6, imageio-ffmpeg)
├── run.bat                  # 1-click Windows launcher
├── app.py                   # Main entry point (launches GUI or CLI)
├── cli.py                   # Command-line interface with rich output
├── core/
│   ├── __init__.py
│   ├── ffmpeg_locator.py    # Auto-locates system or bundled FFmpeg binary
│   ├── video_info.py        # Extracts metadata (resolution, duration, codecs)
│   └── splitter.py          # Lossless stream-copy & frame-accurate engine
├── ui/
│   ├── __init__.py
│   ├── main_window.py       # PyQt6 modern dark-themed GUI
│   ├── styles.py            # Design tokens & QSS styles
│   └── worker.py            # Non-blocking background worker threads
└── tests/
    └── test_clipper.py      # Automated unit tests for engine & CLI
```

---

## 🧪 Running Tests

To run the automated test suite:
```bash
python -m unittest tests/test_clipper.py
```

---

## 📄 License
MIT License. Feel free to use and adapt for personal or commercial projects.
