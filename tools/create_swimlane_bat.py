import os

bat_content = """@echo off
chcp 949 >nul
setlocal
title StatPro Swimlane Workflow Motion Guide
set "HTML_FILE=%~dp0statpro_swimlane_workflow.html"
if not exist "%HTML_FILE%" (
    echo [ERROR] HTML file not found: %HTML_FILE%
    pause
    exit /b 1
)
echo ========================================================
echo   StatPro Overall End-to-End Swimlane Motion Launcher
echo ========================================================
echo.
echo Opening End-to-End Swimlane Motion Workflow in Google Chrome...
start "" chrome "%HTML_FILE%"
if errorlevel 1 (
    echo Chrome not found in PATH, opening with default browser...
    start "" "%HTML_FILE%"
)
echo Done.
"""

bat_path = os.path.join('diagrams', 'open_swimlane_workflow.bat')
with open(bat_path, 'wb') as f:
    f.write(bat_content.replace('\r\n', '\n').replace('\n', '\r\n').encode('cp949'))
print('Successfully generated', bat_path)

