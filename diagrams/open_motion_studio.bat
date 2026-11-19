@echo off
chcp 949 >nul
setlocal
title StatPro Motion Diagram Studio (7 Themes)
set "HTML_FILE=%~dp0motion_diagram_studio.html"
if not exist "%HTML_FILE%" (
    echo [ERROR] HTML file not found: %HTML_FILE%
    pause
    exit /b 1
)
echo ========================================================
echo   StatPro Motion Diagram Studio (7 Themes) Launcher
echo ========================================================
echo.
echo Opening Motion Diagram Studio (7 Themes) in Google Chrome...
start "" chrome "%HTML_FILE%"
if errorlevel 1 (
    echo Chrome not found in PATH, opening with default browser...
    start "" "%HTML_FILE%"
)
echo Done.
