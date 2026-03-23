@echo off
chcp 65001 >nul
title Qwen - Manual Install Python and Node First

echo.
echo ========================================
echo   Install Python and Node.js first
echo   Then run deploy.bat
echo ========================================
echo.
echo Opening download pages...
echo.

start https://www.python.org/downloads/
start https://nodejs.org/

echo.
echo 1. Install Python 3.12+ - CHECK "Add Python to PATH"
echo 2. Install Node.js LTS
echo 3. Close this window, RESTART computer (or at least open new cmd)
echo 4. Double-click deploy.bat
echo.
pause
