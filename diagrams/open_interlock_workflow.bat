@echo off
chcp 949 >nul
setlocal
title StatPro Interlocking Chain Workflow
set "HTML_FILE=%~dp0statpro_interlock_workflow.html"
if not exist "%HTML_FILE%" (
    echo [ERROR] HTML file not found: %HTML_FILE%
    pause
    exit /b 1
)
echo ========================================================
echo   StatPro Interlocking Chain Workflow Launcher
echo ========================================================
echo.
echo Opening Interlocking Chain Workflow in Google Chrome...
start "" chrome "%HTML_FILE%"
if errorlevel 1 (
    echo Chrome not found in PATH, opening with default browser...
    start "" "%HTML_FILE%"
)
echo Done.
