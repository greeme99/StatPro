# -*- coding: utf-8 -*-
"""
Generate 2 New Infographic Themes matching user images:
1. statpro_alternating_timeline_workflow.html (Image 4: Alternating Pin Timeline)
2. statpro_chevron_pipeline_workflow.html (Image 9: Chevron Arrow Pipeline)
With full Light/Dark mode, Speed control, Step navigation, and self-explaining motion!
"""

import os
import shutil

# 1. ALTERNATING TIMELINE (Image 4)
ALT_TIMELINE_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StatPro 수평 교차 핀 타임라인 (Alternating Pin Timeline)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-canvas: #f8fafc;
      --bg-card: #ffffff;
      --border-color: #e2e8f0;
      --text-main: #0f172a;
      --text-sub: #475569;
      --text-muted: #94a3b8;
      --primary-blue: #2563eb;
      --primary-light: #eff6ff;
      --color-1: #eab308;
      --color-2: #f97316;
      --color-3: #22c55e;
      --color-4: #06b6d4;
      --color-5: #3b82f6;
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
      --shadow-md: 0 10px 25px -5px rgba(0,0,0,0.08);
      --shadow-active: 0 0 0 3px rgba(37,99,235,0.2), 0 12px 24px -4px rgba(37,99,235,0.25);
    }
    body.dark-mode {
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
      --shadow-active: 0 0 0 3px rgba(59,130,246,0.3), 0 12px 24px -4px rgba(59,130,246,0.35);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Pretendard', sans-serif; transition: all 0.25s ease; }
    body { background-color: var(--bg-canvas); color: var(--text-main); min-height: 100vh; padding: 28px; display: flex; flex-direction: column; align-items: center; }
    .container { width: 100%; max-width: 1360px; display: flex; flex-direction: column; gap: 24px; }
    
    .header-bar {
      display: flex; justify-content: space-between; align-items: center;
      background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 14px;
      padding: 16px 24px; box-shadow: var(--shadow-sm);
    }
    .header-title h1 { font-size: 20px; font-weight: 800; display: flex; align-items: center; gap: 10px; }
    .header-title .tag { font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px; background: var(--primary-light); color: var(--primary-blue); }
    .header-title p { font-size: 12px; color: var(--text-sub); margin-top: 4px; font-family: 'JetBrains Mono', monospace; }
    .controls { display: flex; gap: 8px; }
    .btn-ctrl {
      background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-main);
      padding: 7px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer;
      display: flex; align-items: center; gap: 6px; box-shadow: var(--shadow-sm);
    }
    .btn-ctrl.btn-primary { background: var(--primary-blue); border-color: var(--primary-blue); color: #fff; }
    
    .banner { background: var(--primary-light); border: 1px solid var(--border-color); border-radius: 10px; padding: 12px 20px; font-size: 13px; font-weight: 500; display: flex; justify-content: space-between; align-items: center; }
    .dots { display: flex; gap: 6px; }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--text-muted); opacity: 0.4; cursor: pointer; }
    .dot.active { background: var(--primary-blue); opacity: 1; transform: scale(1.3); }
    .dot.completed { background: #22c55e; opacity: 0.9; }

    /* Alternating Timeline Stage (Image 4) */
    .timeline-stage {
      position: relative; background: var(--bg-card); border: 1px solid var(--border-color);
      border-radius: 16px; padding: 80px 40px; box-shadow: var(--shadow-md);
      display: flex; align-items: center; justify-content: space-between; min-height: 480px;
    }
    
    /* Left Big Hub Circle */
    .timeline-start-hub {
      width: 140px; height: 140px; border-radius: 50%; background: var(--bg-card);
      border: 8px solid var(--bg-canvas); box-shadow: 0 4px 20px rgba(0,0,0,0.1);
      display: flex; flex-direction: column; justify-content: center; align-items: center;
      text-align: center; z-index: 5; flex-shrink: 0;
    }
    .timeline-start-hub h3 { font-size: 13px; font-weight: 800; color: var(--text-main); }
    .timeline-start-hub p { font-size: 10px; font-weight: 700; color: var(--text-muted); letter-spacing: 1px; }

    /* Main Connecting Horizontal Bar */
    .timeline-rail {
      position: absolute; left: 160px; right: 40px; top: 50%; height: 6px;
      background: linear-gradient(90deg, #eab308 0%, #f97316 25%, #22c55e 50%, #06b6d4 75%, #3b82f6 100%);
      transform: translateY(-50%); z-index: 2; border-radius: 3px;
    }
    .timeline-rail-pulse {
      position: absolute; top: -3px; width: 24px; height: 12px; border-radius: 6px;
      background: #ffffff; box-shadow: 0 0 12px rgba(255,255,255,0.9), 0 0 6px #2563eb;
      z-index: 3; transition: left 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* Steps Track */
    .timeline-items {
      position: relative; display: flex; justify-content: space-between;
      width: calc(100% - 160px); margin-left: 20px; z-index: 4;
    }
    
    .timeline-step {
      display: flex; flex-direction: column; align-items: center;
      position: relative; cursor: pointer; user-select: none; width: 180px;
    }

    /* Center Anchor Pin on Rail */
    .step-pin {
      width: 22px; height: 22px; border-radius: 50%; background: var(--bg-card);
      border: 4px solid var(--color-1); box-shadow: 0 2px 8px rgba(0,0,0,0.15);
      position: absolute; top: 50%; transform: translate(-50%, -50%);
      left: 50%; z-index: 6; display: flex; align-items: center; justify-content: center;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .step-pin::after {
      content: '✓'; font-size: 10px; font-weight: 800; color: #fff; display: none;
    }
    .timeline-step.completed .step-pin { background: var(--color-1); }
    .timeline-step.completed .step-pin::after { display: block; }
    .timeline-step.active .step-pin { transform: translate(-50%, -50%) scale(1.4); box-shadow: 0 0 16px var(--color-1); }

    /* Alternating Content: TOP vs BOTTOM */
    .step-content {
      position: absolute; width: 190px; text-align: center;
      display: flex; flex-direction: column; align-items: center;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .step-top { bottom: 30px; }
    .step-bottom { top: 30px; }

    /* Teardrop Pointer Circle (Image 4) */
    .step-bubble {
      width: 60px; height: 60px; border-radius: 50%; background: var(--bg-card);
      border: 3px solid var(--color-1); box-shadow: 0 4px 12px rgba(0,0,0,0.08);
      display: flex; align-items: center; justify-content: center; font-size: 24px;
      position: relative; margin-bottom: 8px; transition: all 0.3s;
    }
    .step-bubble::after {
      content: ''; position: absolute; width: 0; height: 0; border: 6px solid transparent;
    }
    .step-top .step-bubble::after {
      bottom: -14px; border-top-color: var(--color-1);
    }
    .step-bottom .step-bubble { margin-top: 8px; margin-bottom: 0; order: 2; }
    .step-bottom .step-bubble::after {
      top: -14px; border-bottom-color: var(--color-1);
    }

    .timeline-step.active .step-bubble {
      transform: scale(1.15); box-shadow: 0 8px 24px rgba(0,0,0,0.18);
    }

    .step-info {
      background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px;
      padding: 8px 12px; box-shadow: var(--shadow-sm); width: 100%;
    }
    .step-info h4 { font-size: 12px; font-weight: 700; color: var(--text-main); margin-bottom: 2px; }
    .step-info p { font-size: 10px; color: var(--text-sub); line-height: 1.3; }

    /* Drawer */
    .detail-drawer {
      background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 14px;
      padding: 22px 26px; box-shadow: var(--shadow-sm); display: grid; grid-template-columns: 2fr 1fr; gap: 28px;
    }
    .drawer-title { font-size: 16px; font-weight: 800; color: var(--text-main); margin-bottom: 6px; }
    .drawer-desc { font-size: 13px; color: var(--text-sub); line-height: 1.6; margin-bottom: 12px; }
    .drawer-checklist { list-style: none; display: flex; flex-direction: column; gap: 6px; }
    .drawer-checklist li { font-size: 12px; color: var(--text-main); display: flex; align-items: center; gap: 8px; }
    .sidebar { background: var(--bg-canvas); border: 1px solid var(--border-color); border-radius: 10px; padding: 14px 18px; display: flex; flex-direction: column; justify-content: space-around; }
    .sidebar-label { font-size: 10.5px; font-weight: 600; color: var(--text-muted); }
    .sidebar-val { font-size: 12.5px; font-weight: 700; color: var(--text-main); font-family: 'JetBrains Mono', monospace; }
  </style>
</head>
<body>
  <div class="container">
    <header class="header-bar">
      <div class="header-title">
        <h1>StatPro 수평 교차 핀 타임라인 <span class="tag">Alternating Pin Timeline</span></h1>
        <p>인포그래픽 디자인 템플릿 (Image 4 반영) · 실시간 품질 라이프사이클</p>
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
      <span id="bannerMsg">전체 재생을 누르면 5단계 품질 타임라인이 상하 교차 핀을 따라 진행됩니다.</span>
      <div class="dots">
        <div class="dot active" onclick="jumpTo(0)"></div>
        <div class="dot" onclick="jumpTo(1)"></div>
        <div class="dot" onclick="jumpTo(2)"></div>
        <div class="dot" onclick="jumpTo(3)"></div>
        <div class="dot" onclick="jumpTo(4)"></div>
      </div>
    </div>

    <main class="timeline-stage">
      <div class="timeline-start-hub">
        <h3>STATPRO</h3>
        <p>TIMELINE</p>
      </div>

      <div class="timeline-rail">
        <div class="timeline-rail-pulse" id="railPulse" style="left: 0%;"></div>
      </div>

      <div class="timeline-items">
        <!-- Step 1: TOP (Yellow) -->
        <div class="timeline-step active" id="step-0" onclick="jumpTo(0)">
          <div class="step-pin" style="--color-1: #eab308;"></div>
          <div class="step-content step-top">
            <div class="step-bubble" style="--color-1: #eab308;">💡</div>
            <div class="step-info">
              <h4>01. 원천 데이터 로드</h4>
              <p>CSV/XLSX 계측 파일 수집<br>인코딩 감지 · 결측치 격리</p>
            </div>
          </div>
        </div>

        <!-- Step 2: BOTTOM (Orange) -->
        <div class="timeline-step" id="step-1" onclick="jumpTo(1)">
          <div class="step-pin" style="--color-1: #f97316;"></div>
          <div class="step-content step-bottom">
            <div class="step-info">
              <h4>02. 규격 &amp; 변수 지정</h4>
              <p>특성치(Y) · 구분자(X) 매핑<br>LSL/USL 한계선 검증</p>
            </div>
            <div class="step-bubble" style="--color-1: #f97316;">🔍</div>
          </div>
        </div>

        <!-- Step 3: TOP (Green) -->
        <div class="timeline-step" id="step-2" onclick="jumpTo(2)">
          <div class="step-pin" style="--color-1: #22c55e;"></div>
          <div class="step-content step-top">
            <div class="step-bubble" style="--color-1: #22c55e;">📋</div>
            <div class="step-info">
              <h4>03. 통계 연산 코어</h4>
              <p>Anderson-Darling 정규성<br>Cpk 공정능력 · 8 Rules</p>
            </div>
          </div>
        </div>

        <!-- Step 4: BOTTOM (Cyan) -->
        <div class="timeline-step" id="step-3" onclick="jumpTo(3)">
          <div class="step-pin" style="--color-1: #06b6d4;"></div>
          <div class="step-content step-bottom">
            <div class="step-info">
              <h4>04. 실시간 모니터링</h4>
              <p>uPlot 인터랙티브 관리도<br>이상 패턴 적색 하이라이트</p>
            </div>
            <div class="step-bubble" style="--color-1: #06b6d4;">📊</div>
          </div>
        </div>

        <!-- Step 5: TOP (Blue) -->
        <div class="timeline-step" id="step-4" onclick="jumpTo(4)">
          <div class="step-pin" style="--color-1: #3b82f6;"></div>
          <div class="step-content step-top">
            <div class="step-bubble" style="--color-1: #3b82f6;">🎯</div>
            <div class="step-info">
              <h4>05. 품질 판정 수령</h4>
              <p>독립 실행 HTML 보고서<br>D:/StatProData Parquet 저장</p>
            </div>
          </div>
        </div>
      </div>
    </main>

    <section class="detail-drawer">
      <div>
        <h3 class="drawer-title" id="drawerTitle">원천 데이터 로드 및 로컬 세션 초기화</h3>
        <p class="drawer-desc" id="drawerDesc">엔지니어가 CSV 또는 XLSX 계측 파일을 드롭하면, StatPro UI가 즉시 파싱하여 무손실 세션을 생성합니다.</p>
        <ul class="drawer-checklist" id="drawerChecklist">
          <li>✓ 인코딩 자동 감지 (UTF-8, CP949)</li>
          <li>✓ 결측치 0 대체 금지 원칙 준수</li>
        </ul>
      </div>
      <div class="sidebar">
        <div><span class="sidebar-label">보안 통제</span><div class="sidebar-val" id="statSecurity">로컬 샌드박스 격리</div></div>
        <div><span class="sidebar-label">핵심 엔진</span><div class="sidebar-val" id="statEngine">Polars In-Memory DataFrame</div></div>
      </div>
    </section>
  </div>

  <script>
    const steps = [
      {
        title: "01. 원천 데이터 로드 및 로컬 세션 초기화",
        banner: "Step 1: 품질 엔지니어가 계측 데이터를 임포트하고 무손실 세션을 생성합니다.",
        desc: "CSV 또는 XLSX 계측 파일을 드래그&드롭하면 로컬 Polars 엔진이 파싱하여 Null 격리 세션을 생성합니다.",
        chk: ["인코딩 자동 감지 (UTF-8, CP949)", "결측치 0 대체 금지"],
        sec: "로컬 샌드박스 격리 (외부 전송 0%)", eng: "Polars In-Memory Engine", pulse: "0%"
      },
      {
        title: "02. 변수 매핑 및 LSL/USL 규격 검증",
        banner: "Step 2: 관리 특성치(Y) 및 군 구분자(X)를 지정하고 한계선을 검증합니다.",
        desc: "수치형 연속형 변수를 Y로 지정하고 LSL, Target, USL 규격을 검증하여 Subgroup 크기를 자동 판별합니다.",
        chk: ["Subgroup 크기 자동 판별", "LSL < Target < USL 정합성"],
        sec: "세션 메타데이터 로컬 캐싱", eng: "Pydantic V2 Strict Validator", pulse: "25%"
      },
      {
        title: "03. Anderson-Darling 및 Nelson 8 Rules 연산",
        banner: "Step 3: 정규성 검정 및 관리도 이상 패턴을 실시간 연산합니다.",
        desc: "Anderson-Darling 정규성 p-value와 Nelson 8 Rules 위배 포인트를 고속 연산합니다.",
        chk: ["Anderson-Darling A² 및 p-value", "Nelson Rules 1~8 자동 스캔"],
        sec: "NumPy / SciPy 네이티브 연산", eng: "StatPro Stats Core", pulse: "50%"
      },
      {
        title: "04. 실시간 인터랙티브 관리도 모니터링",
        banner: "Step 4: uPlot 기반 60fps 차트에 관리한계선과 이상 패턴을 표시합니다.",
        desc: "Xbar-R/S 관리도 상에 관리한계선(UCL, CL, LCL)을 그리고 이상 위배 포인트를 빨간색으로 하이라이트합니다.",
        chk: ["uPlot 60fps 대용량 렌더링", "조치 이력(CAPA) 연동"],
        sec: "Fail-safe 클라이언트 렌더링", eng: "uPlot / Canvas Engine", pulse: "75%"
      },
      {
        title: "05. 품질 판정 보고서 수령 및 아카이빙",
        banner: "Step 5: 단일 파일 HTML 리포트를 발행하고 Parquet로 영구 보존합니다.",
        desc: "인터랙티브 차트와 조치 이력이 결합된 단일 HTML 리포트를 D:/StatProData에 저장합니다.",
        chk: ["Parquet 무손실 압축 보존", "오프라인 단일 HTML 리포트"],
        sec: "SHA256 체크섬 커밋", eng: "Jinja2 Report Compiler", pulse: "100%"
      }
    ];

    let current = 0;
    let isPlaying = false;
    let timer = null;
    const speeds = [
      { label: "⚡ 0.5x", ms: 4000 },
      { label: "⚡ 1.0x", ms: 2400 },
      { label: "⚡ 1.5x", ms: 1600 },
      { label: "⚡ 2.0x", ms: 1000 }
    ];
    let spdIdx = 1;

    function update() {
      const d = steps[current];
      for (let i = 0; i < steps.length; i++) {
        const el = document.getElementById(`step-${i}`);
        el.classList.remove('active', 'completed');
        if (i === current) el.classList.add('active');
        else if (i < current) el.classList.add('completed');
      }

      document.querySelectorAll('.dot').forEach((dot, idx) => {
        dot.classList.remove('active', 'completed');
        if (idx === current) dot.classList.add('active');
        else if (idx < current) dot.classList.add('completed');
      });

      document.getElementById('railPulse').style.left = d.pulse;
      document.getElementById('bannerMsg').textContent = d.banner;
      document.getElementById('drawerTitle').textContent = d.title;
      document.getElementById('drawerDesc').textContent = d.desc;
      document.getElementById('statSecurity').textContent = d.sec;
      document.getElementById('statEngine').textContent = d.eng;

      const chk = document.getElementById('drawerChecklist');
      chk.innerHTML = "";
      d.chk.forEach(c => {
        const li = document.createElement('li');
        li.textContent = `✓ ${c}`;
        chk.appendChild(li);
      });
    }

    function jumpTo(idx) { current = idx; update(); }
    function nextStep() { current = (current + 1) % steps.length; update(); }
    function prevStep() { current = (current - 1 + steps.length) % steps.length; update(); }
    function resetFlow() { current = 0; if (isPlaying) togglePlay(); update(); }

    function cycleSpeed() {
      spdIdx = (spdIdx + 1) % speeds.length;
      document.getElementById('btnSpeed').textContent = speeds[spdIdx].label;
      if (isPlaying) { clearInterval(timer); timer = setInterval(nextStep, speeds[spdIdx].ms); }
    }

    function togglePlay() {
      if (isPlaying) {
        clearInterval(timer); isPlaying = false;
        document.getElementById('playIcon').textContent = "▷";
        document.getElementById('playText').textContent = "흐름 재생";
      } else {
        isPlaying = true;
        document.getElementById('playIcon').textContent = "❚❚";
        document.getElementById('playText').textContent = "일시 정지";
        timer = setInterval(nextStep, speeds[spdIdx].ms);
      }
    }

    function toggleTheme() {
      const isDark = document.body.classList.toggle('dark-mode');
      document.getElementById('btnTheme').textContent = isDark ? "☀️" : "🌙";
    }

    window.addEventListener('DOMContentLoaded', update);
  </script>
</body>
</html>
"""

with open('diagrams/statpro_alternating_timeline_workflow.html', 'w', encoding='utf-8') as f:
    f.write(ALT_TIMELINE_HTML)

shutil.copyfile('diagrams/statpro_alternating_timeline_workflow.html', 'C:/Users/0208m/.gemini/antigravity/brain/3b3a945f-274b-405e-9963-58792169202a/statpro_alternating_timeline_workflow.html')
print("Created statpro_alternating_timeline_workflow.html!")
