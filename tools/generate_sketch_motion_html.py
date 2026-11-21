"""Generate hand-drawn sketch-note style motion graphics presentation for StatPro workflow.

Faithfully reflects the uploaded sketch notebook design aesthetic.
"""

from pathlib import Path

SKETCH_HTML = r"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StatPro 엔드투엔드 워크플로우 손그림 모션 가이드</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@400;700&family=Nanum+Pen+Script&family=Pretendard:wght@400;600;700&display=swap');

    :root {
      --paper-bg: #FCF9F2;
      --paper-line: #E2E8F0;
      --paper-margin: #FCA5A5;
      --ink-navy: #1E3A8A;
      --ink-blue: #2563EB;
      --ink-light-blue: #3B82F6;
      --ink-red: #DC2626;
      --ink-dark: #1E293B;
      --ink-gray: #64748B;
      --highlight-yellow: rgba(254, 240, 138, 0.65);
      --highlight-blue: rgba(219, 234, 254, 0.6);
      --font-hand: 'Gaegu', 'Nanum Pen Script', cursive, sans-serif;
      --font-body: 'Pretendard', sans-serif;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background-color: var(--paper-bg);
      background-image: 
        linear-gradient(90deg, transparent 59px, var(--paper-margin) 60px, transparent 62px),
        repeating-linear-gradient(0deg, transparent, transparent 27px, var(--paper-line) 28px);
      background-size: 100% 100%, 100% 28px;
      color: var(--ink-navy);
      font-family: var(--font-hand);
      min-height: 100vh;
      overflow-x: hidden;
      display: flex;
      flex-direction: column;
      position: relative;
    }

    /* Sketchbook Header */
    header {
      padding: 24px 32px 12px 80px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 2px dashed rgba(30, 58, 138, 0.2);
    }

    .title-area {
      position: relative;
    }

    .main-title {
      font-size: 38px;
      font-weight: 700;
      color: var(--ink-navy);
      letter-spacing: -0.5px;
      display: inline-block;
      position: relative;
    }

    .wavy-underline {
      position: absolute;
      bottom: -10px;
      left: 0;
      width: 100%;
      height: 8px;
    }

    .meta-cloud {
      background: #FFFFFF;
      border: 2px solid var(--ink-navy);
      border-radius: 20px;
      padding: 6px 16px;
      font-size: 17px;
      color: var(--ink-navy);
      box-shadow: 3px 3px 0px rgba(30, 58, 138, 0.15);
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-top: 14px;
    }

    /* Player Controller Floating Bar */
    .player-dock {
      background: #FFFFFF;
      border: 2px solid var(--ink-navy);
      border-radius: 30px;
      padding: 8px 20px;
      box-shadow: 4px 4px 0px rgba(30, 58, 138, 0.2);
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .sketch-btn {
      background: #FFFFFF;
      border: 2px solid var(--ink-navy);
      border-radius: 20px;
      padding: 4px 14px;
      font-family: var(--font-hand);
      font-size: 18px;
      font-weight: 700;
      color: var(--ink-navy);
      cursor: pointer;
      transition: all 0.15s ease;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .sketch-btn:hover {
      transform: translate(-1px, -2px);
      box-shadow: 2px 3px 0px var(--ink-navy);
      background: var(--highlight-yellow);
    }

    .sketch-btn.primary {
      background: var(--ink-navy);
      color: #FFFFFF;
    }

    .sketch-btn.primary:hover {
      background: var(--ink-blue);
      color: #FFFFFF;
    }

    /* Main Container */
    main {
      flex: 1;
      padding: 20px 40px 30px 80px;
      display: flex;
      flex-direction: column;
      gap: 24px;
      max-width: 1600px;
      margin: 0 auto;
      width: 100%;
      position: relative;
    }

    /* Canvas Stage Area */
    .sketch-stage {
      background: rgba(255, 255, 255, 0.65);
      border: 2px solid var(--ink-navy);
      border-radius: 16px;
      box-shadow: 6px 6px 0px rgba(30, 58, 138, 0.12);
      padding: 24px;
      position: relative;
      min-height: 500px;
      overflow: hidden;
    }

    svg.doodle-canvas {
      width: 100%;
      height: 480px;
      overflow: visible;
    }

    /* Hand-Drawn Timeline (Bottom Gauge) */
    .timeline-card {
      background: #FFFFFF;
      border: 2px solid var(--ink-navy);
      border-radius: 16px;
      box-shadow: 4px 4px 0px rgba(30, 58, 138, 0.15);
      padding: 16px 28px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .timeline-title {
      font-size: 22px;
      font-weight: 700;
      color: var(--ink-navy);
      text-decoration: underline wavy var(--ink-blue);
      display: inline-block;
    }

    /* Narration Storyboard Inspector */
    .narration-box {
      background: #FFFFFF;
      border: 2px solid var(--ink-navy);
      border-radius: 16px;
      box-shadow: 5px 5px 0px rgba(30, 58, 138, 0.15);
      padding: 20px 28px;
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 24px;
      position: relative;
    }

    .narration-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 8px;
    }

    .step-tag {
      background: var(--ink-red);
      color: #FFFFFF;
      border-radius: 14px;
      padding: 2px 12px;
      font-size: 16px;
      font-weight: 700;
      transform: rotate(-2deg);
      display: inline-block;
    }

    .narration-title {
      font-size: 26px;
      font-weight: 700;
      color: var(--ink-navy);
    }

    .narration-text {
      font-size: 18px;
      line-height: 1.6;
      color: var(--ink-dark);
      font-family: var(--font-hand);
      margin-bottom: 12px;
    }

    .sketch-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .sketch-tag-item {
      background: var(--highlight-blue);
      border: 1px dashed var(--ink-blue);
      border-radius: 12px;
      padding: 2px 10px;
      font-size: 15px;
      font-weight: 600;
      color: var(--ink-navy);
    }

    .memo-card {
      background: #FEF9C3;
      border: 2px dashed #CA8A04;
      border-radius: 12px;
      padding: 16px;
      box-shadow: 3px 3px 0px rgba(202, 138, 4, 0.2);
      transform: rotate(1.2deg);
      display: flex;
      flex-direction: column;
      justify-content: center;
    }

    .memo-header {
      font-size: 18px;
      font-weight: 700;
      color: #854D0E;
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .memo-body {
      font-size: 16px;
      line-height: 1.5;
      color: #713F12;
    }

    /* Desk Object Decorators (SVG) */
    .decor-coffee {
      position: absolute;
      left: 10px;
      top: 15px;
      width: 55px;
      height: 55px;
      pointer-events: none;
    }

    .decor-clips {
      position: absolute;
      left: 12px;
      bottom: 25px;
      width: 45px;
      height: 70px;
      pointer-events: none;
    }

    .decor-pencil {
      position: absolute;
      right: 25px;
      bottom: 15px;
      width: 90px;
      height: 40px;
      pointer-events: none;
      transform: rotate(-15deg);
    }

    .decor-pin {
      position: absolute;
      right: 35px;
      top: 15px;
      width: 40px;
      height: 40px;
      pointer-events: none;
    }

    /* Animations */
    .steam-wave {
      animation: steamAnim 2.5s infinite ease-in-out;
      transform-origin: bottom center;
    }

    @keyframes steamAnim {
      0% { transform: translateY(0) scaleX(1); opacity: 0.3; }
      50% { transform: translateY(-8px) scaleX(1.3); opacity: 0.8; }
      100% { transform: translateY(-16px) scaleX(0.9); opacity: 0; }
    }

    .spin-gear {
      animation: spinGear 6s linear infinite;
      transform-origin: center;
    }

    @keyframes spinGear {
      to { transform: rotate(360deg); }
    }

    .alarm-wiggle {
      animation: alarmWiggle 1s ease-in-out infinite;
      transform-origin: center bottom;
    }

    @keyframes alarmWiggle {
      0%, 100% { transform: rotate(0deg); }
      25% { transform: rotate(-8deg); }
      75% { transform: rotate(8deg); }
    }

    .stamp-pop {
      animation: stampPop 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }

    @keyframes stampPop {
      0% { transform: scale(1.8) rotate(-15deg); opacity: 0; }
      100% { transform: scale(1) rotate(-5deg); opacity: 1; }
    }

    .data-dot {
      animation: dataMove 1.8s infinite linear;
    }

    .doodle-card {
      cursor: pointer;
      transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }

    .doodle-card:hover {
      transform: translateY(-4px) scale(1.02);
    }

    .doodle-card.active {
      filter: drop-shadow(0 0 10px rgba(37, 99, 235, 0.4));
    }
  </style>
</head>
<body>

  <!-- Background Desk Accents -->
  <!-- Coffee Cup (Top Left) -->
  <svg class="decor-coffee" viewBox="0 0 100 100">
    <!-- Steam -->
    <path class="steam-wave" d="M 40 30 Q 35 20 40 10" fill="none" stroke="#64748B" stroke-width="2.5" stroke-linecap="round"/>
    <path class="steam-wave" d="M 50 32 Q 55 20 50 8" fill="none" stroke="#64748B" stroke-width="2.5" stroke-linecap="round" style="animation-delay: 0.6s;"/>
    <path class="steam-wave" d="M 60 30 Q 55 18 60 10" fill="none" stroke="#64748B" stroke-width="2.5" stroke-linecap="round" style="animation-delay: 1.2s;"/>
    <!-- Cup -->
    <path d="M 25 40 L 75 40 L 70 75 Q 68 85 48 85 Q 28 85 26 75 Z" fill="#FFFFFF" stroke="#1E3A8A" stroke-width="3"/>
    <!-- Handle -->
    <path d="M 72 48 Q 90 48 88 65 Q 85 75 69 73" fill="none" stroke="#1E3A8A" stroke-width="3"/>
    <!-- Saucer -->
    <ellipse cx="48" cy="88" rx="38" ry="7" fill="#FFFFFF" stroke="#1E3A8A" stroke-width="3"/>
    <!-- Coffee fill -->
    <ellipse cx="49" cy="45" rx="20" ry="4" fill="#64748B" opacity="0.4"/>
  </svg>

  <!-- Paperclips (Bottom Left) -->
  <svg class="decor-clips" viewBox="0 0 60 90">
    <path d="M 20 70 L 20 20 Q 20 8 32 8 Q 44 8 44 20 L 44 75 Q 44 85 30 85 Q 16 85 16 70 L 16 30 Q 16 22 24 22 Q 32 22 32 30 L 32 65" fill="none" stroke="#3B82F6" stroke-width="3" stroke-linecap="round"/>
  </svg>

  <!-- Pushpins (Top Right) -->
  <svg class="decor-pin" viewBox="0 0 60 60">
    <path d="M 20 15 L 40 15 L 36 28 L 44 34 L 16 34 L 24 28 Z" fill="#DC2626" stroke="#1E3A8A" stroke-width="2.5"/>
    <line x1="30" y1="34" x2="30" y2="52" stroke="#1E3A8A" stroke-width="3" stroke-linecap="round"/>
    <circle cx="30" cy="14" r="5" fill="#EF4444" stroke="#1E3A8A" stroke-width="2"/>
  </svg>

  <!-- Pencil (Bottom Right) -->
  <svg class="decor-pencil" viewBox="0 0 120 40">
    <polygon points="10,20 30,10 110,10 110,30 30,30" fill="#FBBF24" stroke="#1E3A8A" stroke-width="2.5"/>
    <polygon points="10,20 30,10 30,30" fill="#FDE68A" stroke="#1E3A8A" stroke-width="2.5"/>
    <polygon points="10,20 18,16 18,24" fill="#1E3A8A"/>
    <rect x="95" y="10" width="15" height="20" fill="#F472B6" stroke="#1E3A8A" stroke-width="2"/>
    <line x1="95" y1="10" x2="95" y2="30" stroke="#1E3A8A" stroke-width="2"/>
  </svg>

  <!-- Header -->
  <header>
    <div class="title-area">
      <div class="main-title">
        StatPro 제조·품질 분석 전체 표준 작업 흐름
        <svg class="wavy-underline" viewBox="0 0 400 8" preserveAspectRatio="none">
          <path d="M 0 4 Q 20 0 40 4 T 80 4 T 120 4 T 160 4 T 200 4 T 240 4 T 280 4 T 320 4 T 360 4 T 400 4" fill="none" stroke="#2563EB" stroke-width="3"/>
        </svg>
      </div>
      <br/>
      <div class="meta-cloud">
        <span>☁️ 제조 품질 기준선:</span>
        <strong style="color: #2563EB;">'데이터 ➔ 분석 실행 ➔ 시각화 ➔ FMEA 조치 ➔ 승인 근거'</strong>
        <span>단일 재현 워크플로우</span>
      </div>
    </div>

    <!-- Player Controls -->
    <div class="player-dock">
      <button class="sketch-btn primary" id="btnPlay" onclick="togglePlay()">
        <span id="txtPlayIcon">⏸️</span> <span id="txtPlay">설명 일시정지</span>
      </button>
      <button class="sketch-btn" onclick="prevStep()">⏮️ 이전</button>
      <button class="sketch-btn" onclick="nextStep()">다음 ⏭️</button>
      <button class="sketch-btn" onclick="restart()">🔄 처음부터</button>
      <div style="display: flex; align-items: center; gap: 4px; font-size: 16px; margin-left: 6px;">
        <span>속도:</span>
        <select id="selSpeed" onchange="changeSpeed(this.value)" style="border: 2px solid var(--ink-navy); border-radius: 12px; padding: 2px 8px; font-family: var(--font-hand); font-size: 16px;">
          <option value="5000">1.0x</option>
          <option value="3500">1.5x</option>
          <option value="2500">2.0x</option>
        </select>
      </div>
    </div>
  </header>

  <main>
    <!-- Canvas Drawing Stage (Interactive SVG) -->
    <div class="sketch-stage">
      <svg class="doodle-canvas" id="stageCanvas" viewBox="0 0 1200 460">
        <!-- Dynamically Drawn in Script -->
      </svg>
    </div>

    <!-- Hand-Drawn Timeline (Bottom Ruler Gauge) -->
    <div class="timeline-card">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span class="timeline-title">📍 표준 작업 진행 타임라인 (Timeline Gauge)</span>
        <span id="txtCurrentStatus" style="font-size: 18px; color: var(--ink-red); font-weight: 700;">현재: 1단계 진입 & 작업공간 진행 중</span>
      </div>
      
      <!-- Ruler SVG -->
      <svg viewBox="0 0 1100 60" style="width: 100%; height: 50px;">
        <!-- Ruler border box -->
        <rect x="20" y="20" width="1060" height="24" rx="4" fill="#FFFFFF" stroke="#1E3A8A" stroke-width="2.5"/>
        <!-- Tick marks -->
        <g stroke="#1E3A8A" stroke-width="1.5">
          <!-- Ticks loop -->
          <line x1="50" y1="20" x2="50" y2="35"/><line x1="75" y1="20" x2="75" y2="28"/><line x1="100" y1="20" x2="100" y2="28"/><line x1="125" y1="20" x2="125" y2="28"/>
          <line x1="150" y1="20" x2="150" y2="35"/><line x1="175" y1="20" x2="175" y2="28"/><line x1="200" y1="20" x2="200" y2="28"/><line x1="225" y1="20" x2="225" y2="28"/>
          <line x1="250" y1="20" x2="250" y2="35"/><line x1="275" y1="20" x2="275" y2="28"/><line x1="300" y1="20" x2="300" y2="28"/><line x1="325" y1="20" x2="325" y2="28"/>
          <line x1="350" y1="20" x2="350" y2="35"/><line x1="375" y1="20" x2="375" y2="28"/><line x1="400" y1="20" x2="400" y2="28"/><line x1="425" y1="20" x2="425" y2="28"/>
          <line x1="450" y1="20" x2="450" y2="35"/><line x1="475" y1="20" x2="475" y2="28"/><line x1="500" y1="20" x2="500" y2="28"/><line x1="525" y1="20" x2="525" y2="28"/>
          <line x1="550" y1="20" x2="550" y2="35"/><line x1="575" y1="20" x2="575" y2="28"/><line x1="600" y1="20" x2="600" y2="28"/><line x1="625" y1="20" x2="625" y2="28"/>
          <line x1="650" y1="20" x2="650" y2="35"/><line x1="675" y1="20" x2="675" y2="28"/><line x1="700" y1="20" x2="700" y2="28"/><line x1="725" y1="20" x2="725" y2="28"/>
          <line x1="750" y1="20" x2="750" y2="35"/><line x1="775" y1="20" x2="775" y2="28"/><line x1="800" y1="20" x2="800" y2="28"/><line x1="825" y1="20" x2="825" y2="28"/>
          <line x1="850" y1="20" x2="850" y2="35"/><line x1="875" y1="20" x2="875" y2="28"/><line x1="900" y1="20" x2="900" y2="28"/><line x1="925" y1="20" x2="925" y2="28"/>
          <line x1="950" y1="20" x2="950" y2="35"/><line x1="975" y1="20" x2="975" y2="28"/><line x1="1000" y1="20" x2="1000" y2="28"/><line x1="1025" y1="20" x2="1025" y2="28"/><line x1="1050" y1="20" x2="1050" y2="35"/>
        </g>

        <!-- Dynamic Timeline Steps Markers -->
        <g id="timelineMarkers"></g>
      </svg>
    </div>

    <!-- Live Storyboard Narration Inspector -->
    <div class="narration-box">
      <div>
        <div class="narration-header">
          <span class="step-tag" id="badgeStep">단계 1</span>
          <span class="narration-title" id="titleStep">단계 제목</span>
        </div>
        <p class="narration-text" id="descStep">설명 내용</p>
        <div class="sketch-tags" id="tagsStep">
          <!-- Tags -->
        </div>
      </div>

      <div class="memo-card">
        <div class="memo-header">
          <span>📌</span> <span id="memoTitle">현장 엔지니어링 메모</span>
        </div>
        <div class="memo-body" id="memoBody">
          메모 내용
        </div>
      </div>
    </div>
  </main>

  <script>
    // --- Step Data for Hand-Drawn Workflow ---
    const SKETCH_STEPS = [
      {
        num: 1,
        title: "1. 홈 진입 & 작업공간 선택 (Home & Workspace)",
        desc: "엔지니어가 홈 화면에 진입하여 최근 작업 이력을 확인하고 목적에 맞는 특화 작업공간(DOE, SPC, FMEA, DMAIC, Data)을 선택합니다. 모든 작업은 '설정 ➔ 데이터 ➔ 분석 ➔ 결과 ➔ 보고서'라는 일관된 엔지니어링 셸로 연결됩니다.",
        tags: ["홈 (/)", "DOE (/doe)", "SPC (/spc)", "FMEA (/fmea)", "DMAIC (/home/dmaic)"],
        memoTitle: "작업공간 일관성 (DESIGN.md)",
        memoBody: "모듈별로 불필요한 단계를 숨길 수는 있지만, 표준 프로세스 순서(설정 ➔ 데이터 ➔ 분석 ➔ 결과 ➔ 보고서)를 절대 재배치하거나 뒤섞지 않습니다.",
        timelineX: 120,
        timelineDate: "Step 1. 진입"
      },
      {
        num: 2,
        title: "2. 데이터 수집 & 정제 (Data Ingestion & Worksheet)",
        desc: "CSV 파일을 업로드하면 원본 스키마와 데이터 내용을 SHA-256 Digest로 고정한 불변 'Dataset Snapshot'이 생성됩니다. 이후 편집 및 결측치 처리는 ETag 낙관적 동시성 하에 'Worksheet Revision'으로 안전하게 개정 관리됩니다.",
        tags: ["CSV Import", "Dataset Snapshot (SHA-256)", "Worksheet Revision (ETag)", "결측치 무손실 보존"],
        memoTitle: "결측치 처리 원칙 (docs/01)",
        memoBody: "StatPro는 결측값을 조용히 0으로 치환하지 않고 결측 상태 그대로 명시 보존하여 통계 왜곡을 원천 방지합니다.",
        timelineX: 350,
        timelineDate: "Step 2. 데이터"
      },
      {
        num: 3,
        title: "3. 분석 구성 & 통계 엔진 실행 (Engine Run)",
        desc: "입력 바인딩(인자 X, 반응치 Y)과 통계 옵션(알파 위험, 부분군 크기 n)을 확정하고 'Analysis Run'을 생성합니다. 로컬 루프백 FastAPI(:8765) Uvicorn 서버가 순수 Python 3.12 통계 코어로 결정론적 계산을 즉시 수행합니다.",
        tags: ["Input Bindings", "Analysis Run", "FastAPI :8765 Loopback", "Pure Python 3.12 Core", "Deterministic"],
        memoTitle: "로컬 우선 보안 원칙 (docs/06)",
        memoBody: "모든 통계 연산은 엔지니어의 로컬 PC 내부에서만 수행되며 민감한 제조 파라미터가 외부 네트워크로 유출되지 않습니다.",
        timelineX: 580,
        timelineDate: "Step 3. 분석실행"
      },
      {
        num: 4,
        title: "4. 결과 검토 & 이상신호 진단 (Review & Diagnostics)",
        desc: "연산 결과는 완결된 'ResultBundle'로 캡슐화됩니다. Recharts 관리도 차트에 자연적 변동(UCL/LCL)과 규격(USL/LSL)이 분리 표시되며, Nelson Rule 1~8 이상 신호 및 정규/비정규 Cp/Cpk 공정능력이 실시간 판정됩니다.",
        tags: ["ResultBundle", "Recharts 관리도", "Nelson Rules 1~8", "Cp / Cpk 공정능력", "ANOVA 분산분석"],
        memoTitle: "도메인 개념 분리 (docs/05)",
        memoBody: "통계적 관리한계(공정 능력)와 엔지니어링 규격한계(고객 요구)를 별개 개념으로 취급하여 오판을 방지합니다.",
        timelineX: 810,
        timelineDate: "Step 4. 진단검토"
      },
      {
        num: 5,
        title: "5. 보고서 출력 & 불변 증거 보존 (Export & Governance)",
        desc: "브라우저 인쇄용 HTML/PDF, 결정론적 ZIP 패키지, 원천 CSV를 출력합니다. 완료된 결과는 FMEA 관리계획서(Control Plan) 및 DMAIC 인수인계(Control Handoff)의 'Evidence Reference'로 영구 연결되어 품질 감사 증적이 됩니다.",
        tags: ["HTML / PDF 인쇄", "결정론적 ZIP", "SpreadsheetML CSV", "FMEA Control Plan", "Evidence Reference"],
        memoTitle: "닫힌 제어 루프 (Closed Loop)",
        memoBody: "SPC 관리도에서 관리이탈이 감지되면 FMEA 권고 조치(Recommended Action)로 즉시 피드백되어 재발을 방지합니다.",
        timelineX: 1040,
        timelineDate: "Step 5. 증거보존"
      }
    ];

    let currentStep = 0;
    let isPlaying = true;
    let timer = null;
    let intervalTime = 5000;

    function renderStage() {
      const step = SKETCH_STEPS[currentStep];

      // Update Narration Inspector
      document.getElementById('badgeStep').textContent = `단계 ${step.num}/5`;
      document.getElementById('titleStep').textContent = step.title;
      document.getElementById('descStep').textContent = step.desc;
      document.getElementById('memoTitle').textContent = step.memoTitle;
      document.getElementById('memoBody').textContent = step.memoBody;
      document.getElementById('txtCurrentStatus').textContent = `현재: ${step.title.split(' ')[0]} ${step.title.split(' ')[1]} 진행 중`;

      const tagsBox = document.getElementById('tagsStep');
      tagsBox.innerHTML = '';
      step.tags.forEach(t => {
        const span = document.createElement('span');
        span.className = 'sketch-tag-item';
        span.textContent = t;
        tagsBox.appendChild(span);
      });

      // Update Timeline Markers
      renderTimelineMarkers();

      // Render Hand-Drawn SVG Canvas
      renderSvgCanvas();

      if (isPlaying) scheduleNext();
    }

    function renderTimelineMarkers() {
      const g = document.getElementById('timelineMarkers');
      let html = '';

      SKETCH_STEPS.forEach((s, idx) => {
        const isPassed = idx < currentStep;
        const isCurrent = idx === currentStep;
        const color = isCurrent ? '#DC2626' : (isPassed ? '#2563EB' : '#94A3B8');
        const fill = isCurrent ? '#DC2626' : (isPassed ? '#3B82F6' : '#FFFFFF');

        html += `
          <!-- Marker Circle with Hatch -->
          <circle cx="${s.timelineX}" cy="32" r="${isCurrent ? 12 : 8}" fill="${fill}" stroke="#1E3A8A" stroke-width="2"/>
          ${isCurrent ? `
            <!-- Red hatched circle pattern -->
            <circle cx="${s.timelineX}" cy="32" r="12" fill="none" stroke="#DC2626" stroke-width="2" class="alarm-wiggle"/>
            <path d="M ${s.timelineX-8} 26 L ${s.timelineX+8} 38 M ${s.timelineX-8} 38 L ${s.timelineX+8} 26" stroke="#FFFFFF" stroke-width="2"/>
            <!-- Curving arrow pointing to active point -->
            <path d="M ${s.timelineX-25} 12 Q ${s.timelineX-10} 2 ${s.timelineX} 18" fill="none" stroke="#DC2626" stroke-width="2.5" marker-end="url(#arrowRed)"/>
          ` : ''}
          <text x="${s.timelineX}" y="56" text-anchor="middle" fill="${color}" font-family="var(--font-hand)" font-size="16" font-weight="${isCurrent ? '700' : '400'}">${s.timelineDate}</text>
        `;
      });

      g.innerHTML = html;
    }

    function renderSvgCanvas() {
      const svg = document.getElementById('stageCanvas');
      const cur = currentStep;

      // 5 Hand-Drawn Cards Coordinates
      const cards = [
        { x: 30, y: 50, w: 200, h: 360, title: "1. 진입 & 공간", sub: "홈 ➔ 5대 작업공간" },
        { x: 265, y: 50, w: 205, h: 360, title: "2. 데이터 정제", sub: "CSV ➔ Snapshot ➔ Sheet" },
        { x: 505, y: 50, w: 205, h: 360, title: "3. 통계 분석", sub: "파라미터 ➔ 로컬 엔진" },
        { x: 745, y: 50, w: 205, h: 360, title: "4. 진단 & 차트", sub: "ResultBundle ➔ 이상신호" },
        { x: 985, y: 50, w: 195, h: 360, title: "5. 출력 & 증거", sub: "HTML/PDF ➔ FMEA Handoff" }
      ];

      let html = `
        <defs>
          <marker id="arrowDoodle" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#2563EB" />
          </marker>
          <marker id="arrowRed" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#DC2626" />
          </marker>
        </defs>
      `;

      // Draw Hand-Drawn Connective Arrows Between Cards
      for (let i = 0; i < cards.length - 1; i++) {
        const x1 = cards[i].x + cards[i].w + 2;
        const x2 = cards[i + 1].x - 4;
        const y = 220;
        const isCurrentFlow = i === cur - 1;
        const strokeColor = isCurrentFlow ? "#DC2626" : (i < cur ? "#2563EB" : "#CBD5E1");
        const strokeW = isCurrentFlow ? 3 : 2;

        html += `
          <!-- Hand drawn wavy arrow -->
          <path d="M ${x1} ${y} Q ${(x1 + x2)/2} ${y - 12} ${x2} ${y}" fill="none" stroke="${strokeColor}" stroke-width="${strokeW}" ${isCurrentFlow ? 'stroke-dasharray="6 4"' : ''} marker-end="${isCurrentFlow ? 'url(#arrowRed)' : 'url(#arrowDoodle)'}"/>
        `;

        if (isCurrentFlow) {
          html += `
            <!-- Flowing Ink Bubble -->
            <circle cx="${(x1 + x2)/2}" cy="${y - 6}" r="6" fill="#DC2626">
              <animate attributeName="cx" from="${x1}" to="${x2}" dur="1.2s" repeatCount="indefinite" />
              <animate attributeName="cy" from="${y}" to="${y}" dur="1.2s" repeatCount="indefinite" />
            </circle>
          `;
        }
      }

      // Draw the 5 Cards with Sketch Aesthetics
      cards.forEach((c, idx) => {
        const isActive = idx === cur;
        const cardBg = isActive ? "#FFFFFF" : "rgba(255, 255, 255, 0.75)";
        const borderColor = isActive ? "#2563EB" : "#1E3A8A";
        const borderW = isActive ? 3 : 2;
        const rotation = isActive ? 0 : (idx % 2 === 0 ? -0.8 : 0.8);

        html += `
          <g class="doodle-card ${isActive ? 'active' : ''}" onclick="jumpToStep(${idx})" transform="rotate(${rotation} ${c.x + c.w/2} ${c.y + c.h/2})">
            <!-- Sketch Box Shadow and Body -->
            <rect x="${c.x + 4}" y="${c.y + 4}" width="${c.w}" height="${c.h}" rx="14" fill="rgba(30, 58, 138, 0.08)"/>
            <rect x="${c.x}" y="${c.y}" width="${c.w}" height="${c.h}" rx="14" fill="${cardBg}" stroke="${borderColor}" stroke-width="${borderW}"/>
            
            <!-- Header Tape / Title -->
            <path d="M ${c.x + 10} ${c.y + 12} Q ${c.x + c.w/2} ${c.y + 10} ${c.x + c.w - 10} ${c.y + 12}" stroke="${isActive ? '#2563EB' : '#1E3A8A'}" stroke-width="2" fill="none"/>
            <text x="${c.x + c.w/2}" y="${c.y + 36}" text-anchor="middle" font-size="20" font-weight="700" fill="${isActive ? '#2563EB' : '#1E3A8A'}">${c.title}</text>
            <text x="${c.x + c.w/2}" y="${c.y + 56}" text-anchor="middle" font-size="14" fill="#64748B">${c.sub}</text>
            <line x1="${c.x + 15}" y1="${c.y + 66}" x2="${c.x + c.w - 15}" y2="${c.y + 66}" stroke="#E2E8F0" stroke-width="1.5" stroke-dasharray="4 2"/>

            <!-- Internal Doodles per Step -->
            ${renderCardDoodles(idx, c.x, c.y, c.w, c.h, isActive)}

            <!-- Active Highlighter Sticker -->
            ${isActive ? `
              <rect x="${c.x + 16}" y="${c.y + c.h - 38}" width="${c.w - 32}" height="26" rx="13" fill="#DC2626"/>
              <text x="${c.x + c.w/2}" y="${c.y + c.h - 21}" text-anchor="middle" font-size="15" font-weight="700" fill="#FFFFFF">★ 현재 진행 단계 ★</text>
            ` : `
              <rect x="${c.x + 20}" y="${c.y + c.h - 34}" width="${c.w - 40}" height="22" rx="11" fill="#F1F5F9" stroke="#CBD5E1"/>
              <text x="${c.x + c.w/2}" y="${c.y + c.h - 19}" text-anchor="middle" font-size="13" fill="#64748B">클릭하여 탐색</text>
            `}
          </g>
        `;
      });

      svg.innerHTML = html;
    }

    // --- Specific Doodles Matching Image Style ---
    function renderCardDoodles(idx, x, y, w, h, isActive) {
      if (idx === 0) {
        // Step 1: People Icons + Checklist
        return `
          <!-- 4 People Sketch (Like uploaded image) -->
          <g transform="translate(${x + 25}, ${y + 80})">
            <!-- Person 1 -->
            <circle cx="20" cy="15" r="7" fill="none" stroke="#1E3A8A" stroke-width="2"/>
            <path d="M 12 34 Q 20 25 28 34" fill="none" stroke="#1E3A8A" stroke-width="2"/>
            <!-- Person 2 -->
            <circle cx="45" cy="15" r="7" fill="none" stroke="#1E3A8A" stroke-width="2"/>
            <path d="M 37 34 Q 45 25 53 34" fill="none" stroke="#1E3A8A" stroke-width="2"/>
            <!-- Person 3 -->
            <circle cx="70" cy="15" r="7" fill="none" stroke="#1E3A8A" stroke-width="2"/>
            <path d="M 62 34 Q 70 25 78 34" fill="none" stroke="#1E3A8A" stroke-width="2"/>
            <!-- Person 4 -->
            <circle cx="95" cy="15" r="7" fill="none" stroke="#1E3A8A" stroke-width="2"/>
            <path d="M 87 34 Q 95 25 103 34" fill="none" stroke="#1E3A8A" stroke-width="2"/>
            <!-- Checks above heads -->
            <path d="M 16 0 L 19 4 L 26 -2" fill="none" stroke="#DC2626" stroke-width="2"/>
            <path d="M 41 0 L 44 4 L 51 -2" fill="none" stroke="#DC2626" stroke-width="2"/>
            <path d="M 66 0 L 69 4 L 76 -2" fill="none" stroke="#DC2626" stroke-width="2"/>
            <path d="M 91 0 L 94 4 L 101 -2" fill="none" stroke="#DC2626" stroke-width="2"/>
            <text x="58" y="52" text-anchor="middle" font-size="14" font-weight="700" fill="#DC2626">전문 엔지니어 참여</text>
          </g>

          <!-- Checklist (Like right side of uploaded image) -->
          <g transform="translate(${x + 22}, ${y + 155})" font-size="15" fill="#1E3A8A">
            <rect x="0" y="0" width="16" height="16" fill="none" stroke="#1E3A8A" stroke-width="2"/>
            <path d="M 3 8 L 7 13 L 15 2" fill="none" stroke="#2563EB" stroke-width="2.5"/>
            <text x="24" y="14">실험계획법 (DOE)</text>

            <rect x="0" y="30" width="16" height="16" fill="none" stroke="#1E3A8A" stroke-width="2"/>
            <path d="M 3 38 L 7 43 L 15 32" fill="none" stroke="#2563EB" stroke-width="2.5"/>
            <text x="24" y="44">공정관리 (SPC 7도구)</text>

            <rect x="0" y="60" width="16" height="16" fill="none" stroke="#1E3A8A" stroke-width="2"/>
            <path d="M 3 68 L 7 73 L 15 62" fill="none" stroke="#2563EB" stroke-width="2.5"/>
            <text x="24" y="74">고장분석 (FMEA 7단계)</text>

            <rect x="0" y="90" width="16" height="16" fill="none" stroke="#1E3A8A" stroke-width="2"/>
            <path d="M 3 98 L 7 103 L 15 92" fill="none" stroke="#2563EB" stroke-width="2.5"/>
            <text x="24" y="104">개선 프로젝트 (DMAIC)</text>
          </g>
        `;
      } else if (idx === 1) {
        // Step 2: Pie Chart (Like center pie in image) + Hash Lock
        return `
          <!-- Hand-Drawn Pie Chart (Like image) -->
          <g transform="translate(${x + 25}, ${y + 85})">
            <!-- Pie circle -->
            <circle cx="50" cy="50" r="42" fill="#FFFFFF" stroke="#1E3A8A" stroke-width="2.5"/>
            <!-- 75% Hatched Area -->
            <path d="M 50 50 L 50 8 A 42 42 0 1 0 92 50 Z" fill="rgba(37, 99, 235, 0.15)"/>
            <!-- Hatch lines -->
            <line x1="15" y1="35" x2="45" y2="65" stroke="#2563EB" stroke-width="1.5"/>
            <line x1="22" y1="20" x2="68" y2="66" stroke="#2563EB" stroke-width="1.5"/>
            <line x1="35" y1="12" x2="78" y2="55" stroke="#2563EB" stroke-width="1.5"/>
            <!-- Uncut 25% slice -->
            <path d="M 50 50 L 50 8 A 42 42 0 0 1 92 50 Z" fill="#FFFFFF"/>
            <line x1="50" y1="50" x2="50" y2="8" stroke="#1E3A8A" stroke-width="2.5"/>
            <line x1="50" y1="50" x2="92" y2="50" stroke="#1E3A8A" stroke-width="2.5"/>
            <text x="70" y="32" font-size="12" font-weight="700" fill="#DC2626">결측 2%</text>
            <text x="70" y="44" font-size="11" fill="#DC2626">명시보존</text>
            <text x="25" y="70" font-size="13" font-weight="700" fill="#1E3A8A">유효 98%</text>
          </g>

          <!-- Lock & ETag Sketch Box -->
          <g transform="translate(${x + 20}, ${y + 200})">
            <rect x="0" y="0" width="165" height="42" rx="8" fill="#FEF3C7" stroke="#D97706" stroke-width="2"/>
            <text x="10" y="20" font-size="14" font-weight="700" fill="#92400E">🔒 SHA-256 Digest 동결</text>
            <text x="10" y="35" font-size="12" fill="#B45309">Dataset Snapshot 원본 보존</text>

            <rect x="0" y="52" width="165" height="42" rx="8" fill="#DBEAFE" stroke="#2563EB" stroke-width="2"/>
            <text x="10" y="72" font-size="14" font-weight="700" fill="#1E40AF">✏️ Worksheet Revision</text>
            <text x="10" y="87" font-size="12" fill="#1D4ED8">ETag 낙관적 잠금 관리</text>
          </g>
        `;
      } else if (idx === 2) {
        // Step 3: Spinning Gears (Like gears in image) + Formula
        return `
          <!-- Interlocking Gears (Doodle Gears) -->
          <g transform="translate(${x + w/2}, ${y + 110})">
            <!-- Big Gear (Spinning) -->
            <g class="${isActive ? 'spin-gear' : ''}" style="transform-origin: 0px 0px;">
              <circle cx="0" cy="0" r="26" fill="#FFFFFF" stroke="#1E3A8A" stroke-width="2.5"/>
              <circle cx="0" cy="0" r="10" fill="#DBEAFE" stroke="#1E3A8A" stroke-width="2"/>
              <!-- Teeth -->
              <rect x="-4" y="-34" width="8" height="8" fill="#1E3A8A"/>
              <rect x="-4" y="26" width="8" height="8" fill="#1E3A8A"/>
              <rect x="-34" y="-4" width="8" height="8" fill="#1E3A8A"/>
              <rect x="26" y="-4" width="8" height="8" fill="#1E3A8A"/>
              <rect x="-24" y="-24" width="8" height="8" fill="#1E3A8A" transform="rotate(45)"/>
              <rect x="18" y="18" width="8" height="8" fill="#1E3A8A" transform="rotate(45)"/>
              <rect x="-24" y="18" width="8" height="8" fill="#1E3A8A" transform="rotate(45)"/>
              <rect x="18" y="-24" width="8" height="8" fill="#1E3A8A" transform="rotate(45)"/>
            </g>

            <!-- Small Gear (Opposite Spin) -->
            <g class="${isActive ? 'spin-gear' : ''}" style="transform-origin: 36px 30px; animation-direction: reverse;">
              <circle cx="36" cy="30" r="16" fill="#FFFFFF" stroke="#2563EB" stroke-width="2"/>
              <circle cx="36" cy="30" r="6" fill="#FEF08A" stroke="#2563EB" stroke-width="1.5"/>
              <rect x="33" y="10" width="6" height="5" fill="#2563EB"/>
              <rect x="33" y="45" width="6" height="5" fill="#2563EB"/>
              <rect x="16" y="27" width="5" height="6" fill="#2563EB"/>
              <rect x="51" y="27" width="5" height="6" fill="#2563EB"/>
            </g>
          </g>

          <text x="${x + w/2}" y="${y + 185}" text-anchor="middle" font-size="16" font-weight="700" fill="#2563EB">FastAPI :8765 루프백 엔진</text>
          
          <!-- Formula Box -->
          <g transform="translate(${x + 18}, ${y + 205})">
            <rect x="0" y="0" width="170" height="85" rx="10" fill="#F8FAFC" stroke="#64748B" stroke-width="2" stroke-dasharray="4 2"/>
            <text x="12" y="22" font-size="14" font-weight="700" fill="#1E293B">📊 통계 코어 연산:</text>
            <text x="12" y="42" font-size="13" fill="#334155">• 완전/일부요인 ANOVA</text>
            <text x="12" y="60" font-size="13" fill="#334155">• I-MR, Xbar-R, EWMA</text>
            <text x="12" y="78" font-size="13" fill="#334155">• 균형 교차 Gage R&R</text>
          </g>
        `;
      } else if (idx === 3) {
        // Step 4: Control Chart + Wiggling Alarm Clock (Like image alarm)
        return `
          <!-- Control Chart Doodle (UCL / CL / LCL) -->
          <g transform="translate(${x + 20}, ${y + 75})">
            <rect x="0" y="0" width="165" height="95" rx="8" fill="#FFFFFF" stroke="#1E3A8A" stroke-width="2"/>
            <!-- Limits lines -->
            <line x1="8" y1="20" x2="157" y2="20" stroke="#DC2626" stroke-width="1.5" stroke-dasharray="4 2"/>
            <text x="135" y="16" font-size="10" fill="#DC2626">UCL</text>
            <line x1="8" y1="48" x2="157" y2="48" stroke="#16A34A" stroke-width="1.5"/>
            <text x="135" y="44" font-size="10" fill="#16A34A">CL</text>
            <line x1="8" y1="76" x2="157" y2="76" stroke="#DC2626" stroke-width="1.5" stroke-dasharray="4 2"/>
            <text x="135" y="72" font-size="10" fill="#DC2626">LCL</text>
            <!-- Plotted line points -->
            <polyline points="15,55 35,42 55,60 75,30 95,50 115,15 135,40" fill="none" stroke="#2563EB" stroke-width="2"/>
            <circle cx="115" cy="15" r="4" fill="#DC2626" stroke="#DC2626"/>
            <!-- Outlier callout -->
            <path d="M 115 11 Q 120 2 135 2" fill="none" stroke="#DC2626" stroke-width="1.5"/>
            <text x="110" y="2" font-size="11" font-weight="700" fill="#DC2626">Rule 1 이탈!</text>
          </g>

          <!-- Alarm Clock Doodle (Like image alarm) -->
          <g transform="translate(${x + 35}, ${y + 185})" class="${isActive ? 'alarm-wiggle' : ''}">
            <!-- Clock body -->
            <circle cx="30" cy="30" r="22" fill="#FFFFFF" stroke="#DC2626" stroke-width="2.5"/>
            <!-- Bells -->
            <path d="M 12 14 Q 10 4 20 10" fill="#DC2626"/>
            <path d="M 48 14 Q 50 4 40 10" fill="#DC2626"/>
            <!-- Legs -->
            <line x1="16" y1="48" x2="10" y2="56" stroke="#DC2626" stroke-width="2.5" stroke-linecap="round"/>
            <line x1="44" y1="48" x2="50" y2="56" stroke="#DC2626" stroke-width="2.5" stroke-linecap="round"/>
            <!-- Hands -->
            <line x1="30" y1="30" x2="30" y2="18" stroke="#1E293B" stroke-width="2" stroke-linecap="round"/>
            <line x1="30" y1="30" x2="40" y2="30" stroke="#1E293B" stroke-width="2" stroke-linecap="round"/>
            <!-- Sound waves -->
            <path d="M 4 25 Q -4 30 4 35" fill="none" stroke="#DC2626" stroke-width="2"/>
            <path d="M 56 25 Q 64 30 56 35" fill="none" stroke="#DC2626" stroke-width="2"/>
          </g>

          <g transform="translate(${x + 105}, ${y + 195})">
            <text x="0" y="16" font-size="16" font-weight="700" fill="#DC2626">Nelson Rules</text>
            <text x="0" y="34" font-size="14" fill="#1E293B">8대 이상신호</text>
            <text x="0" y="52" font-size="14" font-weight="700" fill="#059669">Cp/Cpk 판정</text>
          </g>
        `;
      } else {
        // Step 5: Document with Official Stamp + FMEA Link
        return `
          <!-- Stamped Document (Like bottom right of image) -->
          <g transform="translate(${x + 25}, ${y + 80})">
            <!-- Sheet of paper with corner folded -->
            <path d="M 10 0 L 105 0 L 125 20 L 125 140 L 10 140 Z" fill="#FFFFFF" stroke="#1E3A8A" stroke-width="2.5"/>
            <path d="M 105 0 L 105 20 L 125 20" fill="#E2E8F0" stroke="#1E3A8A" stroke-width="2"/>
            <!-- Text lines -->
            <line x1="25" y1="30" x2="90" y2="30" stroke="#94A3B8" stroke-width="2" stroke-linecap="round"/>
            <line x1="25" y1="45" x2="105" y2="45" stroke="#94A3B8" stroke-width="2" stroke-linecap="round"/>
            <line x1="25" y1="60" x2="95" y2="60" stroke="#94A3B8" stroke-width="2" stroke-linecap="round"/>
            <line x1="25" y1="75" x2="80" y2="75" stroke="#94A3B8" stroke-width="2" stroke-linecap="round"/>

            <!-- Official Stamp (Red Circular Seal) -->
            <g class="${isActive ? 'stamp-pop' : ''}" transform="translate(65, 80) rotate(-10)">
              <circle cx="28" cy="28" r="24" fill="none" stroke="#DC2626" stroke-width="2.5" stroke-dasharray="3 1"/>
              <circle cx="28" cy="28" r="20" fill="rgba(220, 38, 38, 0.08)" stroke="#DC2626" stroke-width="1.5"/>
              <text x="28" y="24" text-anchor="middle" font-size="11" font-weight="700" fill="#DC2626">AIAG/VDA</text>
              <text x="28" y="37" text-anchor="middle" font-size="12" font-weight="700" fill="#DC2626">승인 완료</text>
            </g>
          </g>

          <!-- Evidence Ref Box -->
          <g transform="translate(${x + 15}, ${y + 240})">
            <rect x="0" y="0" width="165" height="50" rx="8" fill="#FEE2E2" stroke="#DC2626" stroke-width="2"/>
            <text x="8" y="20" font-size="14" font-weight="700" fill="#991B1B">🔗 Evidence Reference</text>
            <text x="8" y="38" font-size="12" fill="#B91C1C">FMEA 관리계획서 영구 바인딩</text>
          </g>
        `;
      }
    }

    // --- Player Control Functions ---
    function togglePlay() {
      isPlaying = !isPlaying;
      document.getElementById('txtPlayIcon').textContent = isPlaying ? '⏸️' : '▶️';
      document.getElementById('txtPlay').textContent = isPlaying ? '설명 일시정지' : '자동 설명 시작';
      if (isPlaying) scheduleNext();
      else clearTimeout(timer);
    }

    function nextStep() {
      currentStep = (currentStep + 1) % SKETCH_STEPS.length;
      renderStage();
    }

    function prevStep() {
      currentStep = (currentStep - 1 + SKETCH_STEPS.length) % SKETCH_STEPS.length;
      renderStage();
    }

    function jumpToStep(idx) {
      currentStep = idx;
      renderStage();
    }

    function restart() {
      currentStep = 0;
      renderStage();
    }

    function changeSpeed(val) {
      intervalTime = parseInt(val, 10);
      if (isPlaying) {
        clearTimeout(timer);
        scheduleNext();
      }
    }

    function scheduleNext() {
      clearTimeout(timer);
      if (!isPlaying) return;
      timer = setTimeout(() => {
        nextStep();
        scheduleNext();
      }, intervalTime);
    }

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space') { e.preventDefault(); togglePlay(); }
      else if (e.code === 'ArrowRight') { e.preventDefault(); nextStep(); }
      else if (e.code === 'ArrowLeft') { e.preventDefault(); prevStep(); }
      else if (e.key === 'r' || e.key === 'R') restart();
    });

    // Start
    renderStage();
  </script>
</body>
</html>
"""

def generate_sketch_files():
  # 1. Project diagrams folder
  p1 = Path(r"D:\Workspace\StatPro\myStatPro\diagrams\statpro_sketch_motion_workflow.html")
  p1.write_text(SKETCH_HTML, encoding="utf-8")
  print(f"Generated: {p1}")

  # 2. Artifact folder
  artifact_dir = Path(r"C:\Users\0208m\.gemini\antigravity\brain\3b3a945f-274b-405e-9963-58792169202a")
  p2 = artifact_dir / "statpro_sketch_motion_workflow.html"
  p2.write_text(SKETCH_HTML, encoding="utf-8")
  print(f"Generated artifact: {p2}")

if __name__ == "__main__":
  generate_sketch_files()

