# -*- coding: utf-8 -*-
import shutil

bats = {
    'open_alternating_timeline.bat': """@echo off
chcp 949 >nul
title StatPro Alternating Pin Timeline Workflow
echo [StatPro] 수평 교차 핀 타임라인(Alternating Pin Timeline)을 기본 웹 브라우저에서 실행합니다...
set "DIAGRAM_PATH=%~dp0statpro_alternating_timeline_workflow.html"
if exist "%DIAGRAM_PATH%" (
    start "" "%DIAGRAM_PATH%"
) else (
    echo [오류] 다이어그램 파일을 찾을 수 없습니다: %DIAGRAM_PATH%
    pause
)
exit /b 0
""",
    'open_chevron_pipeline.bat': """@echo off
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
"""
}

for name, content in bats.items():
    p = f'diagrams/{name}'
    with open(p, 'wb') as f:
        f.write(content.replace('\n', '\r\n').encode('cp949'))
    shutil.copyfile(p, f'C:/Users/0208m/.gemini/antigravity/brain/3b3a945f-274b-405e-9963-58792169202a/{name}')
    print(f"Created {name}")
