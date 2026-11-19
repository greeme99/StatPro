@echo off
chcp 949 >nul
title Open Excalidraw Viewer

echo ======================================================================
echo             Excalidraw �� ��� �� ���̾�׷� ���� ����
echo ======================================================================
echo.
echo 1. Chrome ���������� https://excalidraw.com �� ���ϴ�.
echo 2. ���̾�׷� ������ Ž����� ���ϴ�.
echo 3. ���� Ž���⿡�� ���� ������ Excalidraw ȭ������ �巡�� �� ����ϼ���:
echo    - statpro-overall-workflow.excalidraw
echo    - statpro-integrated-workflow.excalidraw
echo.

set "CHROME_BIN="
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not defined CHROME_BIN if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not defined CHROME_BIN if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

if defined CHROME_BIN (
    start "" "%CHROME_BIN%" "https://excalidraw.com"
) else (
    start "" "https://excalidraw.com"
)

explorer.exe "%~dp0"

echo [�Ϸ�] �������� ���̾�׷� ������ ���Ƚ��ϴ�.
timeout /t 3 >nul
