@echo off
chcp 949 >nul
setlocal
title StatPro Roadmap Highway Workflow
set "HTML_FILE=%~dp0statpro_roadmap_workflow.html"
if not exist "%HTML_FILE%" (
    echo [ERROR] HTML file not found: %HTML_FILE%
    pause
    exit /b 1
)
echo ========================================================
echo   StatPro Roadmap Highway Workflow Launcher
echo ========================================================
echo.
echo Opening Roadmap Highway Workflow in Google Chrome...
start "" chrome "%HTML_FILE%"
if errorlevel 1 (
    echo Chrome not found in PATH, opening with default browser...
    start "" "%HTML_FILE%"
)
echo Done.
