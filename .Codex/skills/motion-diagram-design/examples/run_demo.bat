@echo off
chcp 949 >nul
setlocal
title Universal Motion Diagram Design Suite Launcher
echo ========================================================
echo   Universal Motion Diagram Design Suite (V3.0)
echo ========================================================
echo.
echo 10대 모션 다이어그램 통합 스튜디오 데모를 기본 브라우저에서 실행합니다...
echo.
set "DEMO_PATH=%~dp0demo_studio.html"
if exist "%DEMO_PATH%" (
    start "" "%DEMO_PATH%"
) else (
    echo [오류] demo_studio.html 파일을 찾을 수 없습니다.
    pause
    exit /b 1
)
exit /b 0
