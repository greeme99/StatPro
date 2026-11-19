@echo off
chcp 65001 >nul
title StatPro Backend (:8765)

cd /d "%~dp0.."

set "PY_CMD=%~dp0..\.venv\Scripts\python.exe"
set "PY_ARGS="
if exist "%PY_CMD%" goto :python_ready
where py >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.12 or the project .venv was not found.
    pause
    exit /b 1
)
set "PY_CMD=py"
set "PY_ARGS=-3.12"
:python_ready

set "STORAGE_DIR=D:\StatProData"
if not exist "%STORAGE_DIR%" set "STORAGE_DIR=%~dp0..\data"
if not exist "%STORAGE_DIR%" mkdir "%STORAGE_DIR%"

echo ======================================================================
echo              StatPro API Backend Server (:8765)
echo ======================================================================
echo  - Python     : %PY_CMD% %PY_ARGS%
echo  - Storage    : %STORAGE_DIR%
echo  - Endpoint   : http://127.0.0.1:8765
echo  - Swagger UI : http://127.0.0.1:8765/docs
echo ======================================================================
echo.

"%PY_CMD%" %PY_ARGS% -m statpro.api.server --storage "%STORAGE_DIR%" --host 127.0.0.1 --port 8765

set "EXIT_CODE=%ERRORLEVEL%"
if "%EXIT_CODE%"=="0" exit /b 0
echo.
echo [ERROR] Backend server stopped. Exit code: %EXIT_CODE%
pause
exit /b %EXIT_CODE%
