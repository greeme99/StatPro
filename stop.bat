@echo off
chcp 65001 >nul
title StatPro 시스템 종료

echo ======================================================================
echo                     StatPro 시스템 종료
echo ======================================================================
echo.

echo [*] 포트 8765 (백엔드) 사용 프로세스를 확인 후 종료합니다...
for /f "tokens=5" %%a in ('netstat -ano -p tcp ^| findstr ":8765 " ^| findstr "LISTENING"') do (
    echo    - 백엔드 프로세스 PID %%a 강제 종료 중...
    taskkill /F /PID %%a >nul 2>&1
)

echo [*] 포트 5173 (프론트엔드) 사용 프로세스를 확인 후 종료합니다...
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
