@echo off
chcp 65001 >nul
cd /d "%~dp0.."
title Qwen - One-Click Deploy (China)
call "%~dp0deploy.bat"
