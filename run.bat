@echo off
title Clipper - Lossless Video Splitter
cd /d "%~dp0"

echo ========================================================
echo   Starting Clipper (Lossless Video Splitter) ...
echo ========================================================

python app.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Something went wrong running Clipper.
    pause
)
