@echo off
chcp 949 >nul
title StatPro Docs & Architecture Workflow Motion Guide

set "HTML_PATH=%~dp0docs_motion_workflow.html"

set "CHROME_BIN="
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not defined CHROME_BIN if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not defined CHROME_BIN if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

if defined CHROME_BIN (
    start "" "%CHROME_BIN%" "%HTML_PATH%"
) else (
    start "" "%HTML_PATH%"
)

echo [�Ϸ�] docs �� README ��� ���� ��� ��ũ�÷ο� ���̵尡 ���Ƚ��ϴ�.
timeout /t 2 >nul
