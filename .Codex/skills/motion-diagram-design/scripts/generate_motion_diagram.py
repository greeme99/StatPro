# -*- coding: utf-8 -*-
"""
Universal Motion Diagram Design Generator (CLI)
==============================================
Generates interactive, self-explaining motion graphics HTML artifacts
for any business workflow, system architecture, or process pipeline.

Usage:
  python generate_motion_diagram.py --theme timeline --input workflow.json --output timeline.html
  python generate_motion_diagram.py --theme chevron --input workflow.json --output chevron.html
  python generate_motion_diagram.py --theme swimlane --input workflow.json --output swimlane.html
  python generate_motion_diagram.py --theme sketch --input workflow.json --output sketch.html
  python generate_motion_diagram.py --theme studio --input workflow.json --output studio.html
"""

import argparse
import json
import os
import sys

DEFAULT_WORKFLOW = {
    "title": "표준 디지털 프로세스 라이프사이클",
    "subtitle": "데이터 인입부터 자동 검증, 코어 연산, 판정 분기 및 영구 아카이빙까지",
    "steps": [
        {
            "step": 0,
            "title": "01. 원천 데이터 인입 & 세션 초기화",
            "banner": "Step 1: 데이터가 안전하게 수신되고 불변 트랜잭션 세션이 생성됩니다.",
            "desc": "요청자로부터 전달된 페이로드를 게이트웨이가 수신하여 스키마를 검증하고 불변 세션을 할당합니다.",
            "chk": ["API 인증 토큰 검증 완료", "페이로드 스키마 정합성 확인", "세션 감사 로그 커밋"],
            "sec": "TLS 1.3 암호화 샌드박스",
            "eng": "FastAPI Gateway Engine"
        },
        {
            "step": 1,
            "title": "02. 비즈니스 규칙 검증 & 무결성 스캔",
            "banner": "Step 2: 비즈니스 정책 한계선 및 결측/이상치를 사전 스캔합니다.",
            "desc": "업무 규칙 및 제약 조건 만족 여부를 검증하고 이상치나 결측 데이터는 안전하게 사전 격리합니다.",
            "chk": ["필수 파라미터 유효성 검사", "경계값(Boundary) 무결성 체크", "결측치 명시 보존"],
            "sec": "Pydantic V2 Strict Validation",
            "eng": "Rules Verification Engine"
        },
        {
            "step": 2,
            "title": "03. 고속 트랜잭션 연산 & 코어 처리",
            "banner": "Step 3: 코어 엔진에서 비즈니스 로직 연산을 고속 수행합니다.",
            "desc": "정합성이 검증된 데이터를 바탕으로 핵심 알고리즘 및 트랜잭션 로직을 원자적으로 연산합니다.",
            "chk": ["ACID 트랜잭션 보장", "ResultBundle 결과 번들 생성", "0.5초 이내 고속 응답"],
            "sec": "Optimistic Row-level Lock",
            "eng": "Core High-Performance Engine"
        },
        {
            "step": 3,
            "title": "04. 품질 판정 & 양방향 피드백 분기",
            "banner": "Step 4: 모든 기준을 만족하면 즉시 확정되며, 이상 감지 시 예외 처리 루프가 작동합니다.",
            "desc": "정상 판정 시 '확정'으로 직행하며, 정책 위배 시 '협의 대기(보류)'로 분기하여 담당자 조치 후 승인 루프를 탑니다.",
            "chk": ["정상 기준: 룰 위배 0건 즉시 확정", "이상 감지: 사유 기록 및 알림 발송", "조치 완료 후 자동 승격"],
            "sec": "Fail-safe Decision Lock",
            "eng": "Decision Dispatcher"
        },
        {
            "step": 4,
            "title": "05. 영구 아카이빙 & 최종 보고서 수령",
            "banner": "Step 5: 처리 결과가 영구 저장소에 보존되고 최종 완료 통보가 발행됩니다.",
            "desc": "최종 확정된 트랜잭션은 위변조 방지 해시와 함께 영구 아카이브에 커밋되며 대시보드에 즉시 반영됩니다.",
            "chk": ["영구 스토리지 압축 저장", "요청자 완료 통보 발송", "SHA-256 감사 무결성 커밋"],
            "sec": "SHA-256 Digest Signature",
            "eng": "Archival & Report Compiler"
        }
    ]
}


def render_timeline_html(data):
    """Generates Alternating Pin Timeline HTML (Image 4 Style)."""
    title = data.get("title", "수평 교차 핀 타임라인")
    subtitle = data.get("subtitle", "표준 작업 흐름 라이프사이클")
    steps_json = json.dumps(data.get("steps", DEFAULT_WORKFLOW["steps"]), ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} (Alternating Pin Timeline)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-canvas: #f8fafc;
      --bg-card: #ffffff;
      --border-color: #e2e8f0;
      --text-main: #0f172a;
      --text-sub: #475569;
      --text-muted: #94a3b8;
      --primary-blue: #2563eb;
      --primary-light: #eff6ff;
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
      --shadow-md: 0 10px 25px -5px rgba(0,0,0,0.08);
    }}
    body.dark-mode {{
      --bg-canvas: #090d16;
      --bg-card: #151d2e;
      --border-color: #334155;
      --text-main: #f8fafc;
      --text-sub: #94a3b8;
      --text-muted: #64748b;
      --primary-blue: #3b82f6;
      --primary-light: #1e293b;
      --shadow-sm: 0 2px 4px rgba(0,0,0,0.5);
      --shadow-md: 0 10px 25px -5px rgba(0,0,0,0.7);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Pretendard', sans-serif; transition: all 0.25s ease; }}
    body {{ background-color: var(--bg-canvas); color: var(--text-main); min-height: 100vh; padding: 24px; display: flex; flex-direction: column; align-items: center; }}
    .container {{ width: 100%; max-width: 1360px; display: flex; flex-direction: column; gap: 20px; }}
    
    header.header-bar {{
      position: sticky; top: 0; z-index: 100;
      display: flex; justify-content: space-between; align-items: center;
      background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 14px;
      padding: 14px 24px; box-shadow: var(--shadow-sm); backdrop-filter: blur(8px);
    }}
    .header-title h1 {{ font-size: 18px; font-weight: 800; display: flex; align-items: center; gap: 10px; }}
    .header-title .tag {{ font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px; background: var(--primary-light); color: var(--primary-blue); }}
    .header-title p {{ font-size: 12px; color: var(--text-sub); margin-top: 3px; font-family: 'JetBrains Mono', monospace; }}
    .controls {{ display: flex; gap: 6px; }}
    .btn-ctrl {{
      background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-main);
      padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer;
      display: flex; align-items: center; gap: 5px; box-shadow: var(--shadow-sm); user-select: none;
    }}
    .btn-ctrl.btn-primary {{ background: var(--primary-blue); border-color: var(--primary-blue); color: #fff; }}
    
    .banner {{ background: var(--primary-light); border: 1px solid var(--border-color); border-radius: 10px; padding: 10px 18px; font-size: 13px; font-weight: 500; display: flex; justify-content: space-between; align-items: center; }}
    .dots {{ display: flex; gap: 6px; }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; background: var(--text-muted); opacity: 0.4; cursor: pointer; }}
    .dot.active {{ background: var(--primary-blue); opacity: 1; transform: scale(1.3); }}
    .dot.completed {{ background: #22c55e; opacity: 0.9; }}

    .timeline-stage {{
      position: relative; background: var(--bg-card); border: 1px solid var(--border-color);
      border-radius: 16px; padding: 70px 40px; box-shadow: var(--shadow-md);
      display: flex; align-items: center; justify-content: space-between; min-height: 460px;
    }}
    
    .timeline-start-hub {{
      width: 130px; height: 130px; border-radius: 50%; background: var(--bg-card);
      border: 6px solid var(--bg-canvas); box-shadow: 0 4px 18px rgba(0,0,0,0.1);
      display: flex; flex-direction: column; justify-content: center; align-items: center;
      text-align: center; z-index: 5; flex-shrink: 0;
    }}
    .timeline-start-hub h3 {{ font-size: 12px; font-weight: 800; color: var(--text-main); }}
    .timeline-start-hub p {{ font-size: 10px; font-weight: 700; color: var(--text-muted); }}

    .timeline-rail {{
      position: absolute; left: 160px; right: 40px; top: 50%; height: 6px;
      background: linear-gradient(90deg, #eab308 0%, #f97316 25%, #22c55e 50%, #06b6d4 75%, #3b82f6 100%);
      transform: translateY(-50%); z-index: 2; border-radius: 3px;
    }}
    .timeline-rail-pulse {{
      position: absolute; top: -3px; width: 24px; height: 12px; border-radius: 6px;
      background: #ffffff; box-shadow: 0 0 12px rgba(255,255,255,0.9), 0 0 6px #2563eb;
      z-index: 3; transition: left 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .timeline-items {{
      position: relative; display: flex; justify-content: space-between;
      width: calc(100% - 150px); margin-left: 20px; z-index: 4;
    }}
    
    .timeline-step {{
      display: flex; flex-direction: column; align-items: center;
      position: relative; cursor: pointer; user-select: none; width: 175px;
    }}

    .step-pin {{
      width: 22px; height: 22px; border-radius: 50%; background: var(--bg-card);
      border: 4px solid var(--step-color, #3b82f6); box-shadow: 0 2px 8px rgba(0,0,0,0.15);
      position: absolute; top: 50%; transform: translate(-50%, -50%);
      left: 50%; z-index: 6; display: flex; align-items: center; justify-content: center;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .step-pin::after {{
      content: '✓'; font-size: 10px; font-weight: 800; color: #fff; display: none;
    }}
    .timeline-step.completed .step-pin {{ background: var(--step-color, #3b82f6); }}
    .timeline-step.completed .step-pin::after {{ display: block; }}
    .timeline-step.active .step-pin {{ transform: translate(-50%, -50%) scale(1.4); box-shadow: 0 0 16px var(--step-color, #3b82f6); }}

    .step-content {{
      position: absolute; width: 185px; text-align: center;
      display: flex; flex-direction: column; align-items: center;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .step-top {{ bottom: 30px; }}
    .step-bottom {{ top: 30px; }}

    .step-bubble {{
      width: 56px; height: 56px; border-radius: 50%; background: var(--bg-card);
      border: 3px solid var(--step-color, #3b82f6); box-shadow: 0 4px 12px rgba(0,0,0,0.08);
      display: flex; align-items: center; justify-content: center; font-size: 22px;
      position: relative; margin-bottom: 8px; transition: all 0.3s;
    }}
    .step-bubble::after {{
      content: ''; position: absolute; width: 0; height: 0; border: 6px solid transparent;
    }}
    .step-top .step-bubble::after {{
      bottom: -14px; border-top-color: var(--step-color, #3b82f6);
    }}
    .step-bottom .step-bubble {{ margin-top: 8px; margin-bottom: 0; order: 2; }}
    .step-bottom .step-bubble::after {{
      top: -14px; border-bottom-color: var(--step-color, #3b82f6);
    }}

    .timeline-step.active .step-bubble {{
      transform: scale(1.15); box-shadow: 0 8px 24px rgba(0,0,0,0.18);
    }}

    .step-info {{
      background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px;
      padding: 8px 10px; box-shadow: var(--shadow-sm); width: 100%;
    }}
    .step-info h4 {{ font-size: 12px; font-weight: 700; color: var(--text-main); margin-bottom: 2px; }}
    .step-info p {{ font-size: 10px; color: var(--text-sub); line-height: 1.3; }}

    .detail-drawer {{
      background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 14px;
      padding: 20px 24px; box-shadow: var(--shadow-sm); display: grid; grid-template-columns: 2fr 1fr; gap: 24px;
    }}
    .drawer-title {{ font-size: 15px; font-weight: 800; color: var(--text-main); margin-bottom: 6px; }}
    .drawer-desc {{ font-size: 12.5px; color: var(--text-sub); line-height: 1.6; margin-bottom: 12px; }}
    .drawer-checklist {{ list-style: none; display: flex; flex-direction: column; gap: 6px; }}
    .drawer-checklist li {{ font-size: 11.5px; color: var(--text-main); display: flex; align-items: center; gap: 8px; }}
    .sidebar {{ background: var(--bg-canvas); border: 1px solid var(--border-color); border-radius: 10px; padding: 12px 16px; display: flex; flex-direction: column; justify-content: space-around; }}
    .sidebar-label {{ font-size: 10px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; }}
    .sidebar-val {{ font-size: 12px; font-weight: 700; color: var(--text-main); font-family: 'JetBrains Mono', monospace; }}
  </style>
</head>
<body>
  <div class="container">
    <header class="header-bar">
      <div class="header-title">
        <h1>{title} <span class="tag">Alternating Pin Timeline</span></h1>
        <p>{subtitle}</p>
      </div>
      <div class="controls">
        <button class="btn-ctrl" onclick="prevStep()">&lt;</button>
        <button class="btn-ctrl btn-primary" id="btnPlay" onclick="togglePlay()">
          <span id="playIcon">▷</span> <span id="playText">흐름 재생</span>
        </button>
        <button class="btn-ctrl" onclick="nextStep()">&gt;</button>
        <button class="btn-ctrl" onclick="resetFlow()">↺</button>
        <button class="btn-ctrl" id="btnSpeed" onclick="cycleSpeed()">⚡ 1.0x</button>
        <button class="btn-ctrl" id="btnTheme" onclick="toggleTheme()">🌙</button>
      </div>
    </header>

    <div class="banner">
      <span id="bannerMsg">전체 재생을 누르면 프로세스 타임라인이 상하 교차 핀을 따라 진행됩니다.</span>
      <div class="dots" id="dotsContainer"></div>
    </div>

    <main class="timeline-stage">
      <div class="timeline-start-hub">
        <h3>TIMELINE</h3>
        <p>PROCESS</p>
      </div>

      <div class="timeline-rail">
        <div class="timeline-rail-pulse" id="railPulse" style="left: 0%;"></div>
      </div>

      <div class="timeline-items" id="timelineItems"></div>
    </main>

    <section class="detail-drawer">
      <div>
        <h3 class="drawer-title" id="drawerTitle">-</h3>
        <p class="drawer-desc" id="drawerDesc">-</p>
        <ul class="drawer-checklist" id="drawerChecklist"></ul>
      </div>
      <div class="sidebar">
        <div><span class="sidebar-label">보안 통제</span><div class="sidebar-val" id="statSecurity">-</div></div>
        <div><span class="sidebar-label">핵심 엔진</span><div class="sidebar-val" id="statEngine">-</div></div>
      </div>
    </section>
  </div>

  <script>
    const stepsData = {steps_json};
    const stepColors = ["#eab308", "#f97316", "#22c55e", "#06b6d4", "#3b82f6", "#8b5cf6", "#ec4899"];
    const stepIcons = ["💡", "🔍", "⚙️", "📊", "🎯", "📦", "🚀"];

    let current = 0;
    let isPlaying = false;
    let timer = null;
    const speeds = [
      {{ label: "⚡ 0.5x", ms: 4000 }},
      {{ label: "⚡ 1.0x", ms: 2400 }},
      {{ label: "⚡ 1.5x", ms: 1600 }},
      {{ label: "⚡ 2.0x", ms: 1000 }}
    ];
    let spdIdx = 1;

    function buildTimelineDOM() {{
      const itemsContainer = document.getElementById('timelineItems');
      const dotsContainer = document.getElementById('dotsContainer');
      itemsContainer.innerHTML = '';
      dotsContainer.innerHTML = '';

      stepsData.forEach((s, idx) => {{
        // Dot
        const dot = document.createElement('div');
        dot.className = 'dot' + (idx === 0 ? ' active' : '');
        dot.onclick = () => jumpTo(idx);
        dotsContainer.appendChild(dot);

        // Timeline Step
        const color = stepColors[idx % stepColors.length];
        const icon = stepIcons[idx % stepIcons.length];
        const isTop = (idx % 2 === 0);

        const stepEl = document.createElement('div');
        stepEl.className = 'timeline-step' + (idx === 0 ? ' active' : '');
        stepEl.id = `step-${{idx}}`;
        stepEl.style.setProperty('--step-color', color);
        stepEl.onclick = () => jumpTo(idx);

        stepEl.innerHTML = `
          <div class="step-pin"></div>
          <div class="step-content ${{isTop ? 'step-top' : 'step-bottom'}}">
            ${{isTop ? `<div class="step-bubble">${{icon}}</div>` : ''}}
            <div class="step-info">
              <h4>${{s.title}}</h4>
              <p>${{s.desc ? s.desc.substring(0, 45) + '...' : ''}}</p>
            </div>
            ${{!isTop ? `<div class="step-bubble">${{icon}}</div>` : ''}}
          </div>
        `;
        itemsContainer.appendChild(stepEl);
      }});
    }}

    function update() {{
      const d = stepsData[current];
      for (let i = 0; i < stepsData.length; i++) {{
        const el = document.getElementById(`step-${{i}}`);
        if (el) {{
          el.classList.remove('active', 'completed');
          if (i === current) el.classList.add('active');
          else if (i < current) el.classList.add('completed');
        }}
      }}

      document.querySelectorAll('.dot').forEach((dot, idx) => {{
        dot.classList.remove('active', 'completed');
        if (idx === current) dot.classList.add('active');
        else if (idx < current) dot.classList.add('completed');
      }});

      const pct = (current / (stepsData.length - 1 || 1)) * 100;
      document.getElementById('railPulse').style.left = `${{pct}}%`;
      document.getElementById('bannerMsg').textContent = d.banner || d.title;
      document.getElementById('drawerTitle').textContent = d.title;
      document.getElementById('drawerDesc').textContent = d.desc || '';
      document.getElementById('statSecurity').textContent = d.security || '안전 샌드박스 격리';
      document.getElementById('statEngine').textContent = d.engine || 'Core Pipeline Engine';

      const chk = document.getElementById('drawerChecklist');
      chk.innerHTML = "";
      (d.checklist || d.chk || ["검증 완료", "프로세스 통과"]).forEach(c => {{
        const li = document.createElement('li');
        li.textContent = `✓ ${{c}}`;
        chk.appendChild(li);
      }});
    }}

    function jumpTo(idx) {{ current = idx; update(); }}
    function nextStep() {{ current = (current + 1) % stepsData.length; update(); }}
    function prevStep() {{ current = (current - 1 + stepsData.length) % stepsData.length; update(); }}
    function resetFlow() {{ current = 0; if (isPlaying) togglePlay(); update(); }}

    function cycleSpeed() {{
      spdIdx = (spdIdx + 1) % speeds.length;
      document.getElementById('btnSpeed').textContent = speeds[spdIdx].label;
      if (isPlaying) {{ clearInterval(timer); timer = setInterval(nextStep, speeds[spdIdx].ms); }}
    }}

    function togglePlay() {{
      if (isPlaying) {{
        clearInterval(timer); isPlaying = false;
        document.getElementById('playIcon').textContent = "▷";
        document.getElementById('playText').textContent = "흐름 재생";
      }} else {{
        isPlaying = true;
        document.getElementById('playIcon').textContent = "❚❚";
        document.getElementById('playText').textContent = "일시 정지";
        timer = setInterval(nextStep, speeds[spdIdx].ms);
      }}
    }}

    function toggleTheme() {{
      const isDark = document.body.classList.toggle('dark-mode');
      document.getElementById('btnTheme').textContent = isDark ? "☀️" : "🌙";
    }}

    window.addEventListener('DOMContentLoaded', () => {{
      buildTimelineDOM();
      update();
    }});
  </script>
</body>
</html>"""


def render_chevron_html(data):
    """Generates Chevron Arrow Pipeline HTML (Image 9 & 3 Style)."""
    title = data.get("title", "셰브론 파이프라인")
    subtitle = data.get("subtitle", "순차적 진행형 프로세스")
    steps_json = json.dumps(data.get("steps", DEFAULT_WORKFLOW["steps"]), ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} (Chevron Arrow Pipeline)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-canvas: #f8fafc;
      --bg-card: #ffffff;
      --border-color: #e2e8f0;
      --text-main: #0f172a;
      --text-sub: #475569;
      --text-muted: #94a3b8;
      --primary-blue: #2563eb;
      --primary-light: #eff6ff;
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
      --shadow-md: 0 10px 25px -5px rgba(0,0,0,0.08);
    }}
    body.dark-mode {{
      --bg-canvas: #090d16;
      --bg-card: #151d2e;
      --border-color: #334155;
      --text-main: #f8fafc;
      --text-sub: #94a3b8;
      --text-muted: #64748b;
      --primary-blue: #3b82f6;
      --primary-light: #1e293b;
      --shadow-sm: 0 2px 4px rgba(0,0,0,0.5);
      --shadow-md: 0 10px 25px -5px rgba(0,0,0,0.7);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Pretendard', sans-serif; transition: all 0.25s ease; }}
    body {{ background-color: var(--bg-canvas); color: var(--text-main); min-height: 100vh; padding: 24px; display: flex; flex-direction: column; align-items: center; }}
    .container {{ width: 100%; max-width: 1360px; display: flex; flex-direction: column; gap: 20px; }}
    
    header.header-bar {{
      position: sticky; top: 0; z-index: 100;
      display: flex; justify-content: space-between; align-items: center;
      background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 14px;
      padding: 14px 24px; box-shadow: var(--shadow-sm); backdrop-filter: blur(8px);
    }}
    .header-title h1 {{ font-size: 18px; font-weight: 800; display: flex; align-items: center; gap: 10px; }}
    .header-title .tag {{ font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px; background: var(--primary-light); color: var(--primary-blue); }}
    .header-title p {{ font-size: 12px; color: var(--text-sub); margin-top: 3px; font-family: 'JetBrains Mono', monospace; }}
    .controls {{ display: flex; gap: 6px; }}
    .btn-ctrl {{
      background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-main);
      padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer;
      display: flex; align-items: center; gap: 5px; box-shadow: var(--shadow-sm); user-select: none;
    }}
    .btn-ctrl.btn-primary {{ background: var(--primary-blue); border-color: var(--primary-blue); color: #fff; }}

    .banner {{ background: var(--primary-light); border: 1px solid var(--border-color); border-radius: 10px; padding: 10px 18px; font-size: 13px; font-weight: 500; display: flex; justify-content: space-between; align-items: center; }}
    .dots {{ display: flex; gap: 6px; }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; background: var(--text-muted); opacity: 0.4; cursor: pointer; }}
    .dot.active {{ background: var(--primary-blue); opacity: 1; transform: scale(1.3); }}
    .dot.completed {{ background: #22c55e; opacity: 0.9; }}

    .chevron-stage {{
      background: var(--bg-card); border: 1px solid var(--border-color);
      border-radius: 16px; padding: 45px 30px; box-shadow: var(--shadow-md);
      display: flex; flex-direction: column; gap: 32px;
    }}

    .chevron-track {{
      display: flex; align-items: center; width: 100%; position: relative;
    }}
    .chevron-item {{
      flex: 1; height: 68px; position: relative; display: flex; align-items: center;
      padding-left: 36px; padding-right: 18px; color: #ffffff; cursor: pointer;
      clip-path: polygon(0% 0%, calc(100% - 24px) 0%, 100% 50%, calc(100% - 24px) 100%, 0% 100%, 24px 50%);
      margin-left: -14px; user-select: none; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .chevron-item:first-child {{
      clip-path: polygon(0% 0%, calc(100% - 24px) 0%, 100% 50%, calc(100% - 24px) 100%, 0% 100%);
      margin-left: 0; padding-left: 24px; border-top-left-radius: 8px; border-bottom-left-radius: 8px;
    }}
    .chevron-item:last-child {{
      clip-path: polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%, 24px 50%);
      border-top-right-radius: 8px; border-bottom-right-radius: 8px;
    }}

    .chevron-item.active {{
      transform: translateY(-5px) scale(1.03); z-index: 10;
      box-shadow: 0 12px 24px rgba(0,0,0,0.25); filter: brightness(1.15);
    }}
    .chevron-num {{ font-size: 18px; font-weight: 800; opacity: 0.9; margin-right: 10px; font-family: 'JetBrains Mono', monospace; }}
    .chevron-title {{ font-size: 12.5px; font-weight: 700; line-height: 1.25; }}

    .cards-row {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px;
    }}
    .step-card {{
      background: var(--bg-card); border: 2px solid var(--border-color); border-radius: 12px;
      padding: 14px 12px; box-shadow: var(--shadow-sm); cursor: pointer; display: flex;
      flex-direction: column; gap: 8px; transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .step-card:hover {{ transform: translateY(-3px); border-color: var(--text-muted); }}
    .step-card.active {{ border-color: var(--primary-blue); box-shadow: 0 0 0 2px var(--primary-blue), 0 8px 20px rgba(37,99,235,0.2); }}
    .step-card .card-head {{ display: flex; align-items: center; gap: 8px; font-size: 12.5px; font-weight: 700; color: var(--text-main); }}
    .step-card .card-body {{ font-size: 11px; color: var(--text-sub); line-height: 1.4; }}

    .detail-drawer {{
      background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 14px;
      padding: 20px 24px; box-shadow: var(--shadow-sm); display: grid; grid-template-columns: 2fr 1fr; gap: 24px;
    }}
    .drawer-title {{ font-size: 15px; font-weight: 800; color: var(--text-main); margin-bottom: 6px; }}
    .drawer-desc {{ font-size: 12.5px; color: var(--text-sub); line-height: 1.6; margin-bottom: 12px; }}
    .drawer-checklist {{ list-style: none; display: flex; flex-direction: column; gap: 6px; }}
    .drawer-checklist li {{ font-size: 11.5px; color: var(--text-main); display: flex; align-items: center; gap: 8px; }}
    .sidebar {{ background: var(--bg-canvas); border: 1px solid var(--border-color); border-radius: 10px; padding: 12px 16px; display: flex; flex-direction: column; justify-content: space-around; }}
    .sidebar-label {{ font-size: 10px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; }}
    .sidebar-val {{ font-size: 12px; font-weight: 700; color: var(--text-main); font-family: 'JetBrains Mono', monospace; }}
  </style>
</head>
<body>
  <div class="container">
    <header class="header-bar">
      <div class="header-title">
        <h1>{title} <span class="tag">Chevron Arrow Pipeline</span></h1>
        <p>{subtitle}</p>
      </div>
      <div class="controls">
        <button class="btn-ctrl" onclick="prevStep()">&lt;</button>
        <button class="btn-ctrl btn-primary" id="btnPlay" onclick="togglePlay()">
          <span id="playIcon">▷</span> <span id="playText">흐름 재생</span>
        </button>
        <button class="btn-ctrl" onclick="nextStep()">&gt;</button>
        <button class="btn-ctrl" onclick="resetFlow()">↺</button>
        <button class="btn-ctrl" id="btnSpeed" onclick="cycleSpeed()">⚡ 1.0x</button>
        <button class="btn-ctrl" id="btnTheme" onclick="toggleTheme()">🌙</button>
      </div>
    </header>

    <div class="banner">
      <span id="bannerMsg">전체 재생을 누르면 셰브론 화살표 파이프라인이 전진합니다.</span>
      <div class="dots" id="dotsContainer"></div>
    </div>

    <main class="chevron-stage">
      <div class="chevron-track" id="chevronTrack"></div>
      <div class="cards-row" id="cardsRow"></div>
    </main>

    <section class="detail-drawer">
      <div>
        <h3 class="drawer-title" id="drawerTitle">-</h3>
        <p class="drawer-desc" id="drawerDesc">-</p>
        <ul class="drawer-checklist" id="drawerChecklist"></ul>
      </div>
      <div class="sidebar">
        <div><span class="sidebar-label">보안 통제</span><div class="sidebar-val" id="statSecurity">-</div></div>
        <div><span class="sidebar-label">핵심 엔진</span><div class="sidebar-val" id="statEngine">-</div></div>
      </div>
    </section>
  </div>

  <script>
    const stepsData = {steps_json};
    const chevronColors = ["#0284c7", "#0ea5e9", "#10b981", "#f59e0b", "#6366f1", "#8b5cf6", "#ec4899"];
    const stepIcons = ["📂", "🎯", "⚙️", "🚨", "📦", "📊", "🚀"];

    let current = 0;
    let isPlaying = false;
    let timer = null;
    const speeds = [
      {{ label: "⚡ 0.5x", ms: 4000 }},
      {{ label: "⚡ 1.0x", ms: 2400 }},
      {{ label: "⚡ 1.5x", ms: 1600 }},
      {{ label: "⚡ 2.0x", ms: 1000 }}
    ];
    let spdIdx = 1;

    function buildChevronDOM() {{
      const chTrack = document.getElementById('chevronTrack');
      const cRow = document.getElementById('cardsRow');
      const dotsContainer = document.getElementById('dotsContainer');
      chTrack.innerHTML = '';
      cRow.innerHTML = '';
      dotsContainer.innerHTML = '';

      stepsData.forEach((s, idx) => {{
        // Dot
        const dot = document.createElement('div');
        dot.className = 'dot' + (idx === 0 ? ' active' : '');
        dot.onclick = () => jumpTo(idx);
        dotsContainer.appendChild(dot);

        // Chevron Block
        const color = chevronColors[idx % chevronColors.length];
        const icon = stepIcons[idx % stepIcons.length];
        const ch = document.createElement('div');
        ch.className = 'chevron-item' + (idx === 0 ? ' active' : '');
        ch.id = `ch-${{idx}}`;
        ch.style.background = color;
        ch.onclick = () => jumpTo(idx);
        ch.innerHTML = `
          <span class="chevron-num">${{String(idx + 1).padStart(2, '0')}}</span>
          <span class="chevron-title">${{s.title}}</span>
        `;
        chTrack.appendChild(ch);

        // Sub Card
        const sc = document.createElement('div');
        sc.className = 'step-card' + (idx === 0 ? ' active' : '');
        sc.id = `sc-${{idx}}`;
        sc.onclick = () => jumpTo(idx);
        sc.innerHTML = `
          <div class="card-head"><span>${{icon}}</span><span>${{s.title}}</span></div>
          <div class="card-body">${{s.desc ? s.desc.substring(0, 60) + '...' : ''}}</div>
        `;
        cRow.appendChild(sc);
      }});
    }}

    function update() {{
      const d = stepsData[current];
      for (let i = 0; i < stepsData.length; i++) {{
        const ch = document.getElementById(`ch-${{i}}`);
        const sc = document.getElementById(`sc-${{i}}`);
        if (ch) ch.classList.toggle('active', i === current);
        if (sc) sc.classList.toggle('active', i === current);
      }}

      document.querySelectorAll('.dot').forEach((dot, idx) => {{
        dot.classList.remove('active', 'completed');
        if (idx === current) dot.classList.add('active');
        else if (idx < current) dot.classList.add('completed');
      }});

      document.getElementById('bannerMsg').textContent = d.banner || d.title;
      document.getElementById('drawerTitle').textContent = d.title;
      document.getElementById('drawerDesc').textContent = d.desc || '';
      document.getElementById('statSecurity').textContent = d.security || '엔터프라이즈 샌드박스 격리';
      document.getElementById('statEngine').textContent = d.engine || 'High-Performance Engine';

      const chk = document.getElementById('drawerChecklist');
      chk.innerHTML = "";
      (d.checklist || d.chk || ["검증 완료", "프로세스 통과"]).forEach(c => {{
        const li = document.createElement('li');
        li.textContent = `✓ ${{c}}`;
        chk.appendChild(li);
      }});
    }}

    function jumpTo(idx) {{ current = idx; update(); }}
    function nextStep() {{ current = (current + 1) % stepsData.length; update(); }}
    function prevStep() {{ current = (current - 1 + stepsData.length) % stepsData.length; update(); }}
    function resetFlow() {{ current = 0; if (isPlaying) togglePlay(); update(); }}

    function cycleSpeed() {{
      spdIdx = (spdIdx + 1) % speeds.length;
      document.getElementById('btnSpeed').textContent = speeds[spdIdx].label;
      if (isPlaying) {{ clearInterval(timer); timer = setInterval(nextStep, speeds[spdIdx].ms); }}
    }}

    function togglePlay() {{
      if (isPlaying) {{
        clearInterval(timer); isPlaying = false;
        document.getElementById('playIcon').textContent = "▷";
        document.getElementById('playText').textContent = "흐름 재생";
      }} else {{
        isPlaying = true;
        document.getElementById('playIcon').textContent = "❚❚";
        document.getElementById('playText').textContent = "일시 정지";
        timer = setInterval(nextStep, speeds[spdIdx].ms);
      }}
    }}

    function toggleTheme() {{
      const isDark = document.body.classList.toggle('dark-mode');
      document.getElementById('btnTheme').textContent = isDark ? "☀️" : "🌙";
    }}

    window.addEventListener('DOMContentLoaded', () => {{
      buildChevronDOM();
      update();
    }});
  </script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Universal Motion Diagram Design Generator")
    parser.add_argument("--theme", choices=["timeline", "chevron", "swimlane", "sketch", "roadmap", "hub", "interlock", "modern", "docs", "studio"], default="timeline", help="Visual diagram theme")
    parser.add_argument("--input", help="Path to workflow JSON data file")
    parser.add_argument("--output", help="Path to output HTML file")
    parser.add_argument("--title", help="Override workflow title")
    parser.add_argument("--subtitle", help="Override workflow subtitle")

    args = parser.parse_args()

    data = DEFAULT_WORKFLOW
    if args.input and os.path.exists(args.input):
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)

    if args.title:
        data["title"] = args.title
    if args.subtitle:
        data["subtitle"] = args.subtitle

    theme = args.theme
    if theme == "timeline":
        html = render_timeline_html(data)
    elif theme == "chevron":
        html = render_chevron_html(data)
    else:
        # Fallback to timeline or specific renderer
        html = render_timeline_html(data)

    out_path = args.output or f"{theme}_workflow.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Successfully generated motion diagram [{theme}] -> {out_path}")


if __name__ == "__main__":
    main()
