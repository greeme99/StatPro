import os

bat_content = """@echo off
chcp 949 >nul
setlocal
title StatPro Sketch Motion Workflow
set "HTML_FILE=%~dp0statpro_sketch_motion_workflow.html"
if not exist "%HTML_FILE%" (
    echo [ERROR] HTML file not found: %HTML_FILE%
    pause
    exit /b 1
)
echo ========================================================
echo   StatPro Hand-drawn Sketch Motion Workflow Launcher
echo ========================================================
echo.
echo Opening hand-drawn sketch motion workflow in Google Chrome...
start "" chrome "%HTML_FILE%"
if errorlevel 1 (
    echo Chrome not found in PATH, opening with default browser...
    start "" "%HTML_FILE%"
)
echo Done.
"""

bat_path = os.path.join('diagrams', 'open_sketch_motion.bat')
with open(bat_path, 'wb') as f:
    f.write(bat_content.replace('\r\n', '\n').replace('\n', '\r\n').encode('cp949'))
print('Successfully generated', bat_path)

