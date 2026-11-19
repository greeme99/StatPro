@echo off
chcp 65001 >nul
title StatPro Frontend (:5173)

cd /d "%~dp0..\web"

set "NPM_CMD="
if exist "%ProgramFiles%\nodejs\npm.cmd" set "NPM_CMD=%ProgramFiles%\nodejs\npm.cmd"
if defined NPM_CMD goto :npm_ready
if exist "C:\nvm4w\nodejs\npm.cmd" set "NPM_CMD=C:\nvm4w\nodejs\npm.cmd"
if defined NPM_CMD goto :npm_ready
for /f "delims=" %%I in ('where npm.cmd 2^>nul') do if not defined NPM_CMD set "NPM_CMD=%%I"
if defined NPM_CMD goto :npm_ready
echo [ERROR] npm.cmd를 찾을 수 없습니다. Node.js 설치 후 다시 실행하세요.
pause
exit /b 1
:npm_ready
set "NPM_CONFIG_PREFIX="
set "PREFIX="
for %%I in ("%NPM_CMD%") do set "NODE_BIN=%%~dpI"
set "PATH=%NODE_BIN%;%PATH%"

echo ======================================================================
echo              StatPro Web Frontend Dev Server (:5173)
echo ======================================================================
echo  - Directory : %CD%
echo  - Endpoint  : http://127.0.0.1:5173
echo ======================================================================
echo.

if exist "node_modules" goto :modules_ok
echo [*] node_modules를 찾을 수 없습니다. 의존성을 설치합니다...
call "%NPM_CMD%" ci
:modules_ok

rem Vite's default bundled config loader writes a temporary file under
rem node_modules\.vite-temp. The runner loader avoids that write and works in
rem locked-down workspaces as well as normal developer environments.
call "%NPM_CMD%" run dev -- --host 127.0.0.1 --port 5173 --configLoader runner

set "EXIT_CODE=%ERRORLEVEL%"
if "%EXIT_CODE%"=="0" exit /b 0
echo.
echo [ERROR] Frontend server stopped. Exit code: %EXIT_CODE%
pause
exit /b %EXIT_CODE%
