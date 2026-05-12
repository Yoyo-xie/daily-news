@echo off
chcp 65001 >nul
cd /d "D:\Projects\TrendRadar"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
uv run python -m trendradar >> "D:\Projects\TrendRadar\output\daily-run.log" 2>&1
