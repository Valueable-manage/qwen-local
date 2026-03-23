@echo off
chcp 65001 >nul
cd /d "%~dp0.."
title Qwen - One-Click Deploy

echo.
echo ========================================
echo   Qwen One-Click Deploy
echo   Double-click to install and run
echo ========================================
echo.
echo   If Python/Node not installed, will auto-install via winget.
echo   UAC prompt may appear - click Yes.
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0setup.ps1"

if errorlevel 1 (
    echo.
    echo Deploy failed. Press any key to exit...
    pause >nul
    exit /b 1
)
