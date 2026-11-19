@echo off
chcp 65001 >nul
title StatPro Launcher

cd /d "%~dp0"

echo ======================================================================
echo                  StatPro 통합 실행 환경 시작
echo ======================================================================
echo.

REM 1. Verify Python runtime.
echo [1/5] Python 실행환경 확인 중...
if exist "%~dp0.venv\Scripts\python.exe" (
    echo    - Python: %~dp0.venv\Scripts\python.exe
) else (
    where py >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] 프로젝트 .venv 또는 Python Launcher를 찾을 수 없습니다.
        pause
        exit /b 1
    )
    py -3.12 --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python 3.12를 찾을 수 없습니다.
        pause
        exit /b 1
    )
    echo    - Python: py -3.12
)

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
echo    - npm: %NPM_CMD%

where curl.exe >nul 2>&1
if errorlevel 1 (
    echo [ERROR] curl.exe를 찾을 수 없습니다.
    pause
    exit /b 1
)

REM 2. Verify storage location.
echo [2/5] 데이터 저장소 확인 중...
set "STORAGE_DIR=D:\StatProData"
if not exist "%STORAGE_DIR%" set "STORAGE_DIR=%~dp0data"
if not exist "%STORAGE_DIR%" mkdir "%STORAGE_DIR%"
echo    - 저장소 경로: %STORAGE_DIR%

REM 3. Verify frontend dependencies.
echo [3/5] 프론트엔드 환경 확인 중...
if exist "%~dp0web\node_modules" goto :fe_ready
echo    - web\node_modules를 설치합니다. 시간이 걸릴 수 있습니다...
pushd "%~dp0web"
call "%NPM_CMD%" ci
popd
:fe_ready
echo    - 프론트엔드 환경 준비 완료.

REM 4. Locate Chrome.
set "CHROME_BIN="
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not defined CHROME_BIN if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not defined CHROME_BIN if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

REM 5. Start services.
echo [4/5] 백엔드 및 프론트엔드 서버 확인 중...

REM Check and start backend.
curl.exe -s -m 1 http://127.0.0.1:8765/docs >nul 2>&1
if %errorlevel% equ 0 goto :be_already_running
echo    - 백엔드 API 서버를 시작합니다: 포트 8765
start "StatPro-Backend" cmd.exe /k call "%~dp0tools\run_backend.bat"
goto :check_fe

:be_already_running
echo    - 백엔드 서버가 이미 실행 중입니다: 포트 8765

:check_fe
REM Check and start frontend.
curl.exe -s -m 1 http://127.0.0.1:5173/ >nul 2>&1
if %errorlevel% equ 0 goto :fe_already_running
echo    - 프론트엔드 Vite 서버를 시작합니다: 포트 5173
start "StatPro-Frontend" cmd.exe /k call "%~dp0tools\run_frontend.bat"
goto :wait_servers

:fe_already_running
echo    - 프론트엔드 서버가 이미 실행 중입니다: 포트 5173

:wait_servers
REM 6. Wait for both services.
echo [5/5] 서버 준비 대기 중...
set WAIT_COUNT=0

:wait_loop
set /a WAIT_COUNT+=1
if %WAIT_COUNT% gtr 30 goto :wait_timeout

curl.exe -s -m 1 http://127.0.0.1:8765/docs >nul 2>&1
if %errorlevel% neq 0 (
    ping 127.0.0.1 -n 2 >nul
    goto :wait_loop
)

curl.exe -s -m 1 http://127.0.0.1:5173/ >nul 2>&1
if %errorlevel% neq 0 (
    ping 127.0.0.1 -n 2 >nul
    goto :wait_loop
)

goto :servers_ready

:wait_timeout
echo [안내] 서버 준비 대기 시간을 초과했습니다. 브라우저는 계속 시작합니다.
goto :launch_browser

:servers_ready
echo    - 백엔드 및 프론트엔드 서버 준비 완료!

:launch_browser
echo.
echo Chrome 브라우저로 StatPro를 시작합니다...
if defined CHROME_BIN goto :launch_chrome
echo [안내] 기본 웹 브라우저로 실행합니다.
start "" "http://127.0.0.1:5173"
goto :show_dashboard

:launch_chrome
echo    - Chrome 실행 경로: %CHROME_BIN%
start "" "%CHROME_BIN%" "http://127.0.0.1:5173"

:show_dashboard
echo.
echo ======================================================================
echo           StatPro 통합 시스템이 브라우저로 시작되었습니다!
echo ======================================================================
echo    - 웹 대시보드      : http://127.0.0.1:5173
echo    - 백엔드 REST API   : http://127.0.0.1:8765
echo    - API 문서 (Swagger): http://127.0.0.1:8765/docs
echo    - 데이터 디렉터리  : %STORAGE_DIR%
echo ======================================================================
echo.
echo [안내]
echo    * 시스템을 계속 이용하려면 이 창을 최소화해 두세요.
echo    * 실행을 종료하려면 이 창에서 아무 키나 누르거나 stop.bat를 실행하세요.
echo.
pause >nul
echo.
echo 시스템을 종료하는 중입니다...
call "%~dp0stop.bat"
