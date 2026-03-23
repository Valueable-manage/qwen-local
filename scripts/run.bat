@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set HF_ENDPOINT=https://hf-mirror.com
title Qwen
echo Starting Qwen...
REM Prefer venv to avoid uv run sync overwriting GPU torch
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe start.py
) else (
    uv run --no-sync python start.py
)
if errorlevel 1 pause
