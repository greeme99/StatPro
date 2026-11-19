"""Generate robust Windows batch files with CP949 encoding and CRLF newlines."""

from pathlib import Path

START_BAT = r"""@echo off
chcp 949 >nul
title StatPro Launcher

cd /d "%~dp0"

echo ======================================================================
echo                  StatPro 로컬 개발 환경 시작
echo ======================================================================
echo.

:: 1. Python 가상환경 점검
echo [1/5] Python 가상환경 점검 중...
set "PY_CMD=%~dp0.venv\Scripts\python.exe"
if not exist "%PY_CMD%" set "PY_CMD=py -3.12"
echo    - Python 실행기: %PY_CMD%

:: 2. 데이터 저장소 설정
echo [2/5] 데이터 저장소 확인 중...
set "STORAGE_DIR=D:\StatProData"
if not exist "%STORAGE_DIR%" set "STORAGE_DIR=%~dp0data"
if not exist "%STORAGE_DIR%" mkdir "%STORAGE_DIR%"
echo    - 저장소 경로: %STORAGE_DIR%

:: 3. 프론트엔드 환경 확인
echo [3/5] 프론트엔드 환경 확인 중...
if exist "%~dp0web\node_modules" goto :fe_ready
echo    - web\node_modules가 없습니다. 설치를 진행합니다...
pushd "%~dp0web"
call npm ci
popd
:fe_ready
echo    - 프론트엔드 환경 준비 완료.

:: 4. 크롬 브라우저 경로 확인
set "CHROME_BIN="
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not defined CHROME_BIN if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not defined CHROME_BIN if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

:: 5. 서버 실행
echo [4/5] 백엔드 및 프론트엔드 서버 실행 중...

:: 백엔드 확인 및 시작
curl.exe -s -m 1 http://127.0.0.1:8765/docs >nul 2>&1
if %errorlevel% equ 0 goto :be_already_running
echo    - 백엔드 API 서버를 시작합니다 : 포트 8765
start "StatPro-Backend" cmd.exe /k call "%~dp0tools\run_backend.bat"
goto :check_fe

:be_already_running
echo    - 백엔드 서버가 이미 실행 중입니다 : 포트 8765

:check_fe
:: 프론트엔드 확인 및 시작
curl.exe -s -m 1 http://127.0.0.1:5173/ >nul 2>&1
if %errorlevel% equ 0 goto :fe_already_running
echo    - 프론트엔드 Vite 서버를 시작합니다 : 포트 5173
start "StatPro-Frontend" cmd.exe /k call "%~dp0tools\run_frontend.bat"
goto :wait_servers

:fe_already_running
echo    - 프론트엔드 서버가 이미 실행 중입니다 : 포트 5173

:wait_servers
:: 6. 서버 응답 대기
echo [5/5] 서버 응답 대기 중...
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
echo [경고] 서버 응답 대기 시간이 초과되었습니다. 브라우저 실행을 계속 진행합니다.
goto :launch_browser

:servers_ready
echo    - 백엔드 및 프론트엔드 서버 준비 완료!

:launch_browser
echo.
echo Chrome 브라우저에서 StatPro를 실행합니다...
if defined CHROME_BIN goto :launch_chrome
echo [안내] 기본 웹 브라우저로 엽니다.
start "" "http://127.0.0.1:5173"
goto :show_dashboard

:launch_chrome
echo    - Chrome 브라우저 실행: %CHROME_BIN%
start "" "%CHROME_BIN%" "http://127.0.0.1:5173"

:show_dashboard
echo.
echo ======================================================================
echo           StatPro 로컬 시스템이 성공적으로 실행되었습니다!
echo ======================================================================
echo    - 웹 인터페이스      : http://127.0.0.1:5173
echo    - 백엔드 REST API    : http://127.0.0.1:8765
echo    - API 문서 (Swagger) : http://127.0.0.1:8765/docs
echo    - 데이터 스토리지    : %STORAGE_DIR%
echo ======================================================================
echo.
echo [안내]
echo    * 시스템을 계속 이용하시려면 이 창을 최소화해 두세요.
echo    * 서버를 모두 종료하려면 이 창에서 아무 키나 누르거나 stop.bat을 실행하세요.
echo.
pause >nul
echo.
echo 서버를 종료하는 중입니다...
call "%~dp0stop.bat"
"""

STOP_BAT = r"""@echo off
chcp 949 >nul
title StatPro 서버 종료

echo ======================================================================
echo                     StatPro 서버 종료
echo ======================================================================
echo.

echo [*] 포트 8765 (백엔드) 점유 프로세스 확인 및 종료...
for /f "tokens=5" %%a in ('netstat -ano -p tcp ^| findstr ":8765 " ^| findstr "LISTENING"') do (
    echo    - 백엔드 프로세스 PID %%a 강제 종료 중...
    taskkill /F /PID %%a >nul 2>&1
)

echo [*] 포트 5173 (프론트엔드) 점유 프로세스 확인 및 종료...
for /f "tokens=5" %%a in ('netstat -ano -p tcp ^| findstr ":5173 " ^| findstr "LISTENING"') do (
    echo    - 프론트엔드 프로세스 PID %%a 강제 종료 중...
    taskkill /F /PID %%a >nul 2>&1
)

taskkill /FI "WINDOWTITLE eq StatPro Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq StatPro Frontend*" /F >nul 2>&1

echo.
echo ======================================================================
echo StatPro 서버가 모두 종료되었습니다.
echo ======================================================================
echo.
ping 127.0.0.1 -n 3 >nul
"""

RUN_BAT = r"""@echo off
call "%~dp0start.bat"
"""

RUN_BACKEND_BAT = r"""@echo off
chcp 949 >nul
title StatPro Backend (:8765)

cd /d "%~dp0.."

set "PY_CMD=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PY_CMD%" set "PY_CMD=py -3.12"

set "STORAGE_DIR=D:\StatProData"
if not exist "%STORAGE_DIR%" set "STORAGE_DIR=%~dp0..\data"
if not exist "%STORAGE_DIR%" mkdir "%STORAGE_DIR%"

echo ======================================================================
echo              StatPro API Backend Server (:8765)
echo ======================================================================
echo  - Python     : %PY_CMD%
echo  - Storage    : %STORAGE_DIR%
echo  - Endpoint   : http://127.0.0.1:8765
echo  - Swagger UI : http://127.0.0.1:8765/docs
echo ======================================================================
echo.

"%PY_CMD%" -m statpro.api.server --storage "%STORAGE_DIR%" --host 127.0.0.1 --port 8765

if %errorlevel% neq 0 (
    echo.
    echo [오류] 백엔드 서버가 비정상 종료되었습니다 (코드: %errorlevel%).
    pause
)
"""

RUN_FRONTEND_BAT = r"""@echo off
chcp 949 >nul
title StatPro Frontend (:5173)

cd /d "%~dp0..\web"

echo ======================================================================
echo              StatPro Web Frontend Dev Server (:5173)
echo ======================================================================
echo  - Directory : %CD%
echo  - Endpoint  : http://127.0.0.1:5173
echo ======================================================================
echo.

if exist "node_modules" goto :modules_ok
echo [*] node_modules가 없습니다. 의존성을 설치합니다...
call npm ci
:modules_ok

call npm run dev -- --host 127.0.0.1 --port 5173

if %errorlevel% neq 0 (
    echo.
    echo [오류] 프론트엔드 개발 서버가 비정상 종료되었습니다 (코드: %errorlevel%).
    pause
)
"""

files = {
    r"D:\Workspace\StatPro\sav.loc\start.bat": START_BAT,
    r"D:\Workspace\StatPro\sav.loc\stop.bat": STOP_BAT,
    r"D:\Workspace\StatPro\sav.loc\run.bat": RUN_BAT,
    r"D:\Workspace\StatPro\sav.loc\tools\run_backend.bat": RUN_BACKEND_BAT,
    r"D:\Workspace\StatPro\sav.loc\tools\run_frontend.bat": RUN_FRONTEND_BAT,
}

for path_str, content in files.items():
    p = Path(path_str)
    normalized = content.strip().replace("\r\n", "\n").replace("\n", "\r\n") + "\r\n"
    p.write_bytes(normalized.encode("cp949"))
    print(f"Written: {p.name} ({len(normalized)} chars, CRLF, CP949)")
