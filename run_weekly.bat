@echo off
REM run_weekly.bat update|weekly
set MODE=%1
if "%MODE%"=="" set MODE=weekly
python src\pipeline_weekly.py
