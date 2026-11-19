@echo off
chcp 949 >nul
title StatPro Chevron Arrow Pipeline Workflow
echo [StatPro] 셰브론 파이프라인(Chevron Arrow Pipeline)을 기본 웹 브라우저에서 실행합니다...
set "DIAGRAM_PATH=%~dp0statpro_chevron_pipeline_workflow.html"
if exist "%DIAGRAM_PATH%" (
    start "" "%DIAGRAM_PATH%"
) else (
    echo [오류] 다이어그램 파일을 찾을 수 없습니다: %DIAGRAM_PATH%
    pause
)
exit /b 0
