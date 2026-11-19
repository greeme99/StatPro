@echo off
chcp 949 >nul
title StatPro Workflow Motion Guide Launcher

set "HTML_PATH=%~dp0statpro_motion_workflow.html"

set "CHROME_BIN="
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not defined CHROME_BIN if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not defined CHROME_BIN if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

if defined CHROME_BIN (
    start "" "%CHROME_BIN%" "%HTML_PATH%"
) else (
    start "" "%HTML_PATH%"
)

echo [�Ϸ�] ��� ���̵� ���������̼��� ���������� ���Ƚ��ϴ�.
timeout /t 2 >nul
