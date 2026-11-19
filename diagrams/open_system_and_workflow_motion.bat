@echo off
chcp 949 >nul
setlocal
title StatPro System Architecture & Workflow Motion Guide
set "HTML_FILE=%~dp0statpro_system_and_workflow_motion.html"
if not exist "%HTML_FILE%" (
    echo [ERROR] HTML file not found: %HTML_FILE%
    pause
    exit /b 1
)
echo ========================================================
echo   StatPro System Architecture & Workflow Motion Guide Launcher
echo ========================================================
echo.
echo Opening System Architecture & Workflow Motion Guide in Google Chrome...
start "" chrome "%HTML_FILE%"
if errorlevel 1 (
    echo Chrome not found in PATH, opening with default browser...
    start "" "%HTML_FILE%"
)
echo Done.
