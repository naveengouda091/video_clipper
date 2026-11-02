import os
import shutil
import subprocess
from typing import Optional

_CACHED_FFMPEG_PATH: Optional[str] = None


def get_ffmpeg_path() -> str:
    """
    Finds and returns an absolute path to a functional FFmpeg executable.
    Checks:
    1. System PATH ('ffmpeg')
    2. imageio-ffmpeg bundled binary
    3. Common Windows directory locations
    Raises RuntimeError if no functional FFmpeg binary can be found.
    """
    global _CACHED_FFMPEG_PATH
    if _CACHED_FFMPEG_PATH and os.path.isfile(_CACHED_FFMPEG_PATH):
        return _CACHED_FFMPEG_PATH

    # 1. System PATH
    path_from_env = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if path_from_env and _verify_executable(path_from_env):
        _CACHED_FFMPEG_PATH = path_from_env
        return _CACHED_FFMPEG_PATH

    # 2. imageio-ffmpeg bundled binary
    try:
        import imageio_ffmpeg
        imgio_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if imgio_exe and os.path.isfile(imgio_exe) and _verify_executable(imgio_exe):
            _CACHED_FFMPEG_PATH = imgio_exe
            return _CACHED_FFMPEG_PATH
    except Exception:
        pass

    # 3. Known common paths on Windows
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
    candidate_paths = [
        os.path.join(local_app_data, "Microsoft", "WinGet", "Links", "ffmpeg.exe"),
        "C:\\ffmpeg\\bin\\ffmpeg.exe",
        "C:\\ProgramData\\chocolatey\\bin\\ffmpeg.exe",
        os.path.join(program_files, "ffmpeg", "bin", "ffmpeg.exe"),
    ]

    for cand in candidate_paths:
        if os.path.isfile(cand) and _verify_executable(cand):
            _CACHED_FFMPEG_PATH = cand
            return _CACHED_FFMPEG_PATH

    raise RuntimeError(
        "FFmpeg executable not found. Please ensure FFmpeg or 'imageio-ffmpeg' is installed."
    )


def _verify_executable(path: str) -> bool:
    try:
        res = subprocess.run(
            [path, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            text=True,
            timeout=5
        )
        return res.returncode == 0
    except Exception:
        return False


if __name__ == "__main__":
    try:
        print("FFmpeg located at:", get_ffmpeg_path())
    except Exception as e:
        print("Error:", e)
