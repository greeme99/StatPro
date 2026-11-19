@echo off
chcp 949 >nul
setlocal
title StatPro Strategy Diamond Hub Workflow
set "HTML_FILE=%~dp0statpro_hub_workflow.html"
if not exist "%HTML_FILE%" (
    echo [ERROR] HTML file not found: %HTML_FILE%
    pause
    exit /b 1
)
echo ========================================================
echo   StatPro Strategy Diamond Hub Workflow Launcher
echo ========================================================
echo.
echo Opening Strategy Diamond Hub Workflow in Google Chrome...
start "" chrome "%HTML_FILE%"
if errorlevel 1 (
    echo Chrome not found in PATH, opening with default browser...
    start "" "%HTML_FILE%"
)
echo Done.
