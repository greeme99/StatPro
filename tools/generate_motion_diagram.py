"""Motion Diagram Design Generator.

Generates self-explaining, interactive motion graphics HTML artifacts for
workflows and architecture diagrams with multiple theme options:
  1. swimlane: 3-tier role swimlanes + local privacy boundary + decision
  branching
  2. sketch: Notebook lined paper + pen ink + coffee steam + desk doodles +
  ruler timeline
  3. modern: Engineering dashboard + glassmorphism + particle stream + audio
  synth
  4. docs: Deep-dive architecture + rule callouts + formula inspection modal
  5. studio: Interactive studio that switches between all themes dynamically!
"""

import argparse
import json
import os
import sys

# Template generators for each theme are modularized below

def get_studio_html(workflow_data):
    """Generates the Multi-Theme Studio HTML allowing live switching between all 4 themes."""
    # Serialize workflow_data to JSON safe for script tag
    wf_json = json.dumps(workflow_data, ensure_ascii=False)
    
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Motion Diagram Studio - 디자인 테마 선택기</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gaegu:wght@400;700&family=Nanum+Pen+Script&display=swap">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Pretendard', sans-serif;
      background-color: #0f172a;
      color: #f8fafc;
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}
    
    /* Top Studio Nav Bar */
    .studio-bar {{
      height: 56px;
      background-color: #1e293b;
      border-bottom: 1px solid #334155;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 20px;
      z-index: 100;
      flex-shrink: 0;
    }}
    
    .studio-brand {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .studio-logo {{
      width: 28px;
      height: 28px;
      background: linear-gradient(135deg, #3b82f6, #8b5cf6);
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 14px;
    }}
    .studio-title {{
      font-size: 15px;
      font-weight: 700;
      letter-spacing: -0.01em;
    }}
    .studio-subtitle {{
      font-size: 11px;
      color: #94a3b8;
    }}
    
    /* Theme Switcher Pills */
    .theme-selector-group {{
      display: flex;
      align-items: center;
      background-color: #0f172a;
      border: 1px solid #334155;
      border-radius: 10px;
      padding: 4px;
      gap: 4px;
    }}
    
    .theme-btn {{
      padding: 6px 14px;
      border-radius: 6px;
      border: none;
      background: transparent;
      color: #94a3b8;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
      font-family: 'Pretendard', sans-serif;
    }}
    
    .theme-btn:hover {{
      color: #f8fafc;
      background-color: rgba(255, 255, 255, 0.05);
    }}
    
    .theme-btn.active {{
      background: #2563eb;
      color: #ffffff;
      box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);
    }}
    
    .actions-group {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    
    .btn-action {{
      padding: 6px 12px;
      border-radius: 6px;
      border: 1px solid #475569;
      background: #1e293b;
      color: #cbd5e1;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 5px;
      transition: all 0.2s;
    }}
    .btn-action:hover {{
      background: #334155;
      color: #ffffff;
    }}
    
    /* Frame Viewport */
    .viewport-container {{
      flex: 1;
      width: 100%;
      height: calc(100vh - 56px);
      position: relative;
      background-color: #0b1120;
    }}
    
    iframe.preview-frame {{
      width: 100%;
      height: 100%;
      border: none;
      display: block;
    }}
  </style>
</head>
<body>

  <header class="studio-bar">
    <div class="studio-brand">
      <div class="studio-logo">✦</div>
      <div>
        <div class="studio-title">Diagram Design Studio</div>
        <div class="studio-subtitle">모션그래픽 인터랙티브 아티팩트 테마 스위처</div>
      </div>
    </div>

    <!-- Theme Switcher -->
    <div class="theme-selector-group">
      <button class="theme-btn active" data-src="statpro_swimlane_workflow.html" onclick="switchTheme(this)">
        🏢 엔터프라이즈 스윔레인
      </button>
      <button class="theme-btn" data-src="statpro_sketch_motion_workflow.html" onclick="switchTheme(this)">
        📝 손글씨 줄노트 스케치
      </button>
      <button class="theme-btn" data-src="statpro_motion_workflow.html" onclick="switchTheme(this)">
        💻 모던 UI 대시보드
      </button>
      <button class="theme-btn" data-src="docs_motion_workflow.html" onclick="switchTheme(this)">
        📖 기술 문서 심층 파이프라인
      </button>
    </div>

    <div class="actions-group">
      <button class="btn-action" onclick="openNewTab()">
        <span>↗ 새 탭에서 열기</span>
      </button>
      <button class="btn-action" onclick="reloadFrame()">
        <span>↺ 새로고침</span>
      </button>
    </div>
  </header>

  <main class="viewport-container">
    <iframe id="previewFrame" class="preview-frame" src="statpro_swimlane_workflow.html"></iframe>
  </main>

  <script>
    let currentSrc = "statpro_swimlane_workflow.html";

    function switchTheme(btn) {{
      document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentSrc = btn.getAttribute('data-src');
      document.getElementById('previewFrame').src = currentSrc;
    }}

    function openNewTab() {{
      window.open(currentSrc, '_blank');
    }}

    function reloadFrame() {{
      const frame = document.getElementById('previewFrame');
      frame.src = frame.src;
    }}
  </script>
</body>
</html>
"""
    return html

def main():
    parser = argparse.ArgumentParser(description="Motion Diagram Design Artifact Generator")
    parser.add_argument("--theme", choices=["swimlane", "sketch", "modern", "docs", "studio", "all"], default="studio", help="Design theme to generate")
    parser.add_argument("--output-dir", default="diagrams", help="Output directory for generated artifacts")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    sample_wf = {
        "title": "StatPro 전체 표준 작업 흐름 (Overall End-to-End Workflow)",
        "subtitle": "로컬 퍼스트 SPC/MSA 통계 분석 & 품질 판정 파이프라인",
        "steps": [
            {
                "id": 1,
                "name": "원천 데이터 준비",
                "desc": "CSV·XLSX 원본 파일 로드 및 D:\\StatProData 로컬 격리 세션 생성",
                "security": "Air-gapped Local-First",
                "engine": "FastAPI + Polars Core"
            },
            {
                "id": 2,
                "name": "변수 및 규격 지정",
                "desc": "관리특성치(Y) 및 USL/LSL 엔지니어링 규격 설정 (결측치 0 대체 원천 차단)",
                "security": "Data Integrity Checked",
                "engine": "Virtual Grid + Pydantic"
            },
            {
                "id": 3,
                "name": "통계 분석 엔진 가동",
                "desc": "정규성 Anderson-Darling 및 8대 Nelson Rules 실시간 이상 검출",
                "security": "Vectorized Fast In-Memory",
                "engine": "SciPy / NumPy SPC Core"
            },
            {
                "id": 4,
                "name": "공정 안정 판정 분기",
                "desc": "Cpk 1.33 이상 정상 확정 vs 규격 이탈/이상 패턴 시 CAPA 조치 대기",
                "security": "Fail-safe Decision Gate",
                "engine": "Nelson Decision Logic"
            },
            {
                "id": 5,
                "name": "품질 보고서 출력 및 영구 저장",
                "desc": "독립형 단일 HTML 리포트 발행 및 Parquet 로컬 영구 보존",
                "security": "Permanent Archive",
                "engine": "Jinja2 Report Engine"
            }
        ]
    }

    if args.theme in ["studio", "all"]:
        studio_file = os.path.join(args.output_dir, "motion_diagram_studio.html")
        with open(studio_file, "w", encoding="utf-8") as f:
            f.write(get_studio_html(sample_wf))
        print(f"Generated Studio: {studio_file}")

        # Also generate launcher for the Studio
        bat_content = """@echo off
chcp 949 >nul
setlocal
title Motion Diagram Design Studio
set "HTML_FILE=%~dp0motion_diagram_studio.html"
if not exist "%HTML_FILE%" (
    echo [ERROR] HTML file not found: %HTML_FILE%
    pause
    exit /b 1
)
echo ========================================================
echo   Motion Diagram Design Studio (Theme Switcher)
echo ========================================================
echo.
echo Opening Motion Diagram Design Studio in Google Chrome...
start "" chrome "%HTML_FILE%"
if errorlevel 1 (
    echo Chrome not found in PATH, opening with default browser...
    start "" "%HTML_FILE%"
)
echo Done.
"""
        bat_file = os.path.join(args.output_dir, "open_motion_studio.bat")
        with open(bat_file, "wb") as f:
            f.write(bat_content.replace('\r\n', '\n').replace('\n', '\r\n').encode('cp949'))
        print(f"Generated Studio Launcher: {bat_file}")

if __name__ == "__main__":
    main()

