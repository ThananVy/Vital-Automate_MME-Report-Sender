@echo off
cd /d "%~dp0"
uv run python send_reports.py
pause