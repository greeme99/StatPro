"""Generates an interactive, self-explaining motion graphics HTML presentation for StatPro Workflows.

Compliant with StatPro Design System (Work App Design System v1.0).
"""

from pathlib import Path

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StatPro 워크플로우 인터랙티브 모션 가이드</title>
  <style>
    :root {
      --brand-50: #EEF4FE;
      --brand-100: #D8E6FD;
      --brand-300: #83B0F9;
      --brand-500: #4F8EF7;
      --brand-600: #2F6FE4;
      --brand-700: #1E56C4;
      --neutral-0: #FFFFFF;
      --neutral-50: #F7F8FB;
      --neutral-100: #F0F2F7;
      --neutral-200: #E3E6EF;
      --neutral-300: #CBD1E0;
      --neutral-400: #8A90A8;
      --neutral-600: #5A6080;
      --neutral-800: #2A3040;
      --neutral-900: #111827;
      --success-100: #C9F2E1;
      --success-500: #2ECC8A;
      --success-700: #0B7A4B;
      --warning-100: #FDEFCD;
      --warning-500: #F0B429;
      --danger-100: #FDDCDC;
      --danger-500: #F75555;
      --info-500: #06B6D4;
      --dark-canvas: #0F1420;
      --dark-surface: #171D2B;
      --dark-raised: #1E2637;
      --dark-border: #2A3346;
      --dark-ink: #E8EAF2;
      --dark-ink-2: #A3AAC2;
      --bg: #0F1420;
      --surface: #171D2B;
      --raised: #1E2637;
      --border: #2A3346;
      --text-main: #E8EAF2;
      --text-muted: #A3AAC2;
      --radius-sm: 4px;
      --radius-md: 8px;
      --radius-lg: 12px;
      --radius-pill: 9999px;
      --shadow-md: 0 4px 20px rgba(0, 0, 0, 0.35);
      --font: 'Pretendard Variable', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
    }

    [data-theme="light"] {
      --bg: #F7F8FB;
      --surface: #FFFFFF;
      --raised: #F0F2F7;
      --border: #E3E6EF;
      --text-main: #111827;
      --text-muted: #5A6080;
      --shadow-md: 0 4px 16px rgba(17, 24, 39, 0.08);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: var(--font);
      background-color: var(--bg);
      color: var(--text-main);
      overflow-x: hidden;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      transition: background-color 0.3s ease, color 0.3s ease;
    }

    /* Top Navigation Header */
    header {
      height: 64px;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 28px;
      position: sticky;
      top: 0;
      z-index: 100;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .logo-badge {
      width: 34px;
      height: 34px;
      background: linear-gradient(135deg, var(--brand-500), var(--brand-700));
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-weight: 800;
      font-size: 16px;
      box-shadow: 0 2px 8px rgba(79, 142, 247, 0.4);
    }

    .brand-title {
      font-size: 17px;
      font-weight: 700;
      letter-spacing: -0.3px;
    }

    .brand-sub {
      font-size: 12px;
      color: var(--text-muted);
      margin-left: 6px;
      font-weight: 400;
    }

    /* Tab Switcher */
    .tab-group {
      display: flex;
      background: var(--raised);
      padding: 4px;
      border-radius: var(--radius-pill);
      border: 1px solid var(--border);
      gap: 4px;
    }

    .tab-btn {
      padding: 6px 18px;
      border-radius: var(--radius-pill);
      border: none;
      background: transparent;
      color: var(--text-muted);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
    }

    .tab-btn.active {
      background: var(--brand-600);
      color: #FFFFFF;
      box-shadow: 0 2px 6px rgba(47, 111, 228, 0.4);
    }

    .top-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .icon-btn {
      background: var(--raised);
      border: 1px solid var(--border);
      color: var(--text-main);
      width: 36px;
      height: 36px;
      border-radius: var(--radius-md);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s ease;
      font-size: 16px;
    }

    .icon-btn:hover {
      background: var(--border);
    }

    /* Progress bar */
    .progress-track {
      height: 3px;
      background: var(--border);
      width: 100%;
      position: relative;
    }

    .progress-bar {
      height: 100%;
      background: linear-gradient(90deg, var(--brand-500), var(--success-500));
      width: 20%;
      transition: width 0.4s ease;
    }

    /* Main Layout */
    main {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 24px 28px;
      gap: 20px;
      max-width: 1680px;
      margin: 0 auto;
      width: 100%;
    }

    /* Control & Storyboard Bar */
    .player-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 16px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
      box-shadow: var(--shadow-md);
    }

    .player-controls {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .ctrl-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 16px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border);
      background: var(--raised);
      color: var(--text-main);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .ctrl-btn:hover {
      background: var(--border);
    }

    .ctrl-btn.primary {
      background: var(--brand-600);
      color: #fff;
      border-color: var(--brand-700);
    }

    .ctrl-btn.primary:hover {
      background: var(--brand-500);
    }

    .step-badges {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .step-pill {
      padding: 6px 14px;
      border-radius: var(--radius-pill);
      background: var(--raised);
      border: 1px solid var(--border);
      color: var(--text-muted);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.25s ease;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .step-pill.active {
      background: var(--brand-50);
      border-color: var(--brand-500);
      color: var(--brand-700);
      box-shadow: 0 0 12px rgba(79, 142, 247, 0.35);
      transform: translateY(-1px);
    }

    [data-theme="dark"] .step-pill.active {
      background: rgba(79, 142, 247, 0.2);
      border-color: var(--brand-500);
      color: #83B0F9;
    }

    .speed-select {
      background: var(--raised);
      border: 1px solid var(--border);
      color: var(--text-main);
      padding: 6px 10px;
      border-radius: var(--radius-md);
      font-size: 12px;
      cursor: pointer;
    }

    /* Motion Canvas Area */
    .canvas-container {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 24px;
      min-height: 520px;
      position: relative;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: var(--shadow-md);
    }

    svg.stage {
      width: 100%;
      height: 500px;
      overflow: visible;
    }

    /* SVG Elements Styling & Animations */
    .flow-card {
      transition: all 0.35s cubic-bezier(0.2, 0, 0, 1);
      cursor: pointer;
    }

    .flow-card:hover {
      filter: brightness(1.15);
      transform: translateY(-3px);
    }

    .flow-card.active-phase {
      filter: drop-shadow(0 0 16px rgba(79, 142, 247, 0.6));
    }

    .pulse-ring {
      animation: pulseAnimation 2s infinite ease-out;
      transform-origin: center;
    }

    @keyframes pulseAnimation {
      0% { r: 12px; opacity: 0.9; stroke-width: 3px; }
      100% { r: 36px; opacity: 0; stroke-width: 1px; }
    }

    .data-particle {
      animation: flowAlongPath 2.5s infinite linear;
    }

    /* Live Narration & Inspector Drawer */
    .narration-panel {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 20px 24px;
      box-shadow: var(--shadow-md);
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 24px;
      position: relative;
    }

    .narration-content h3 {
      font-size: 18px;
      font-weight: 700;
      color: var(--brand-500);
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .narration-badge {
      font-size: 11px;
      font-weight: 700;
      background: var(--brand-50);
      color: var(--brand-700);
      padding: 2px 8px;
      border-radius: var(--radius-pill);
      border: 1px solid var(--brand-300);
    }

    [data-theme="dark"] .narration-badge {
      background: rgba(79, 142, 247, 0.2);
      color: var(--brand-300);
    }

    .narration-body {
      font-size: 14px;
      line-height: 1.7;
      color: var(--text-main);
      margin-bottom: 12px;
    }

    .key-points {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .point-tag {
      background: var(--raised);
      border: 1px solid var(--border);
      padding: 4px 10px;
      border-radius: var(--radius-sm);
      font-size: 12px;
      color: var(--text-muted);
      font-family: monospace;
    }

    .side-tip {
      background: var(--raised);
      border-left: 3px solid var(--success-500);
      padding: 14px 16px;
      border-radius: 0 var(--radius-md) var(--radius-md) 0;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }

    .side-tip-title {
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--success-500);
      margin-bottom: 4px;
    }

    .side-tip-desc {
      font-size: 13px;
      line-height: 1.5;
      color: var(--text-muted);
    }

    /* Footer info */
    footer {
      text-align: center;
      padding: 16px;
      font-size: 12px;
      color: var(--text-muted);
      border-top: 1px solid var(--border);
    }

    /* Path animations */
    .animated-path {
      stroke-dasharray: 8 6;
      animation: dashMove 1.5s linear infinite;
    }

    @keyframes dashMove {
      to { stroke-dashoffset: -28; }
    }
  </style>
</head>
<body>

  <!-- Header -->
  <header>
    <div class="brand">
      <div class="logo-badge">SP</div>
      <div>
        <span class="brand-title">StatPro</span>
        <span class="brand-sub">엔터프라이즈 통계 품질 워크플로우 가이드</span>
      </div>
    </div>

    <!-- Mode Selector -->
    <div class="tab-group">
      <button class="tab-btn active" id="tabOverall" onclick="switchMode('overall')">1. 전체 표준 워크플로우</button>
      <button class="tab-btn" id="tabIntegrated" onclick="switchMode('integrated')">2. DMAIC 연계 워크플로우</button>
    </div>

    <div class="top-actions">
      <button class="icon-btn" onclick="toggleTheme()" title="테마 전환 (Light/Dark)">🌓</button>
    </div>
  </header>

  <div class="progress-track">
    <div class="progress-bar" id="progressBar"></div>
  </div>

  <main>
    <!-- Motion Storyboard & Controller -->
    <div class="player-card">
      <div class="player-controls">
        <button class="ctrl-btn primary" id="playBtn" onclick="togglePlay()">
          <span id="playIcon">⏸️</span> <span id="playText">일시정지</span>
        </button>
        <button class="ctrl-btn" onclick="prevStep()">⏮️ 이전</button>
        <button class="ctrl-btn" onclick="nextStep()">다음 ⏭️</button>
        <button class="ctrl-btn" onclick="restart()">🔄 처음부터</button>
      </div>

      <div class="step-badges" id="stepPills">
        <!-- Rendered dynamically -->
      </div>

      <div>
        <label style="font-size: 12px; color: var(--text-muted); margin-right: 6px;">속도:</label>
        <select class="speed-select" id="speedSelect" onchange="changeSpeed(this.value)">
          <option value="5000">1.0x (표준)</option>
          <option value="3500">1.5x (빠름)</option>
          <option value="2500">2.0x (신속)</option>
        </select>
      </div>
    </div>

    <!-- Visual Motion Stage (SVG) -->
    <div class="canvas-container">
      <svg class="stage" id="svgStage" viewBox="0 0 1200 480">
        <!-- Dynamic SVG Scene -->
      </svg>
    </div>

    <!-- Live Guided Tour & Narration Inspector -->
    <div class="narration-panel">
      <div class="narration-content">
        <h3 id="narTitle">
          <span id="stepNumberBadge" class="narration-badge">단계 1/5</span>
          <span id="stepHeading">단계 제목</span>
        </h3>
        <p class="narration-body" id="stepDescription">단계 상세 설명</p>
        <div class="key-points" id="stepTags">
          <!-- Tags -->
        </div>
      </div>
      <div class="side-tip">
        <div class="side-tip-title" id="tipLabel">제조 현장 거버넌스 팁</div>
        <div class="side-tip-desc" id="tipText">팁 내용</div>
      </div>
    </div>
  </main>

  <footer>
    StatPro Local Analytics Core • ISO/AIAG/VDA 7단계 & DMAIC 품질 혁신 통합 아키텍처 • 키보드: [Space] 재생/정지, [←/→] 단계 이동
  </footer>

  <script>
    // --- Data Definition for Workflow Modes ---
    const OVERALL_STEPS = [
      {
        num: 1,
        title: "진입 & 작업공간 선택 (Entry & Workspace)",
        badge: "단계 1/5",
        desc: "사용자가 홈 화면(/)에 진입하여 최근 작업 이력을 확인하고, 목적에 맞는 특화 작업공간(DOE, SPC, FMEA, DMAIC, Data)을 선택합니다. 각 작업공간은 제조 엔지니어링 표준 흐름을 제공합니다.",
        tags: ["Home (/)", "DOE (/doe)", "SPC (/spc)", "FMEA (/fmea)", "DMAIC (/home/dmaic)"],
        tipTitle: "엔지니어링 접근성",
        tipText: "데스크톱 우선(Desktop-first) 반응형 UI로 구성되어 있으며 7대 품질 도구와 표준 분석 카드를 한눈에 탐색할 수 있습니다.",
        focusIndex: 0
      },
      {
        num: 2,
        title: "데이터 수집 & 정제 (Data Ingestion & Worksheet)",
        badge: "단계 2/5",
        desc: "CSV 파일을 업로드하면 불변 스키마를 가진 'Dataset Snapshot'이 생성되어 SHA-256 Digest가 고정됩니다. 이후 편집 및 필터링은 'Worksheet Revision'으로 낙관적 동시성(ETag) 하에 안전하게 관리됩니다.",
        tags: ["CSV Import", "Dataset Snapshot", "SHA-256 Digest", "Worksheet Revision", "ETag"],
        tipTitle: "결측값 무손실 원칙",
        tipText: "StatPro는 결측 데이터를 조용히 0으로 치환하지 않고 결측 상태 그대로 명시 보존하여 분석 왜곡을 방지합니다.",
        focusIndex: 1
      },
      {
        num: 3,
        title: "분석 파라미터 구성 & 실행 (Configuration & Engine Run)",
        badge: "단계 3/5",
        desc: "인자(X)와 반응치(Y) 컬럼을 바인딩하고 알파 위험(α), 부분군 크기(n), 관리선 옵션을 확정합니다. StatPro 로컬 통계 코어(FastAPI/Uvicorn)가 즉시 기동하여 계산을 수행하고 불변 Analysis Run을 기록합니다.",
        tags: ["Input Bindings", "Analysis Run", "Pure Python Engine", "FastAPI / Uvicorn", "Immutable Run"],
        tipTitle: "결정론적 재현성",
        tipText: "동일한 입력 Digest와 엔진 버전 조합은 항상 완전히 동일한 수치 결과를 산출하는 결정론적(Deterministic) 계산을 보장합니다.",
        focusIndex: 2
      },
      {
        num: 4,
        title: "결과 검토 & 통계 진단 (Review & ResultBundle)",
        badge: "단계 4/5",
        desc: "분석 결과는 표준 경계 객체인 'ResultBundle'로 캡슐화됩니다. Recharts 반응형 시각화 차트와 함께 Nelson 이상 신호 1~8 규칙, ANOVA 분산분석표, 잔차 진단, Cp/Cpk 공정능력 지수가 실시간 검증됩니다.",
        tags: ["ResultBundle", "Recharts Visualizer", "Nelson Rules 1~8", "ANOVA", "Cp/Cpk Capability"],
        tipTitle: "도메인 개념 분리",
        tipText: "통계적 관리한계(UCL/LCL: 자연 변동)와 고객 규격한계(USL/LSL: 엔지니어링 요구)를 명확히 구분하여 이중선으로 표시합니다.",
        focusIndex: 3
      },
      {
        num: 5,
        title: "보고서 출력 & 불변 증거 보존 (Export & Governance)",
        badge: "단계 5/5",
        desc: "검증된 결과는 브라우저 인쇄용 HTML/PDF, 결정론적 ZIP 패키지, SpreadsheetML 원천 CSV로 출력됩니다. 또한 결과 번들은 FMEA 및 DMAIC의 'Evidence Reference'로 영구 보존되어 품질 감사 근거가 됩니다.",
        tags: ["Print HTML/PDF", "Deterministic ZIP", "SpreadsheetML CSV", "Evidence Reference", "Quality Snapshot"],
        tipTitle: "품질 대시보드 연동",
        tipText: "저장된 ResultBundle의 수치 경로는 /quality 대시보드 지표 스냅샷으로 연결되어 DPMO 및 위험 우선순위를 지속 추적합니다.",
        focusIndex: 4
      }
    ];

    const INTEGRATED_STEPS = [
      {
        num: 1,
        title: "1. 정의 (Define) — 프로젝트 목표 & 고객 가치 규명",
        badge: "DMAIC 1단계",
        desc: "프로젝트 헌장(Charter), 고객의 소리(VOC), SIPOC 공정 맵, 문제 정의서를 통해 품질 문제의 현상과 목표 격차를 명확히 정의합니다. 핵심품질특성(CTQ)과 공정 시작/종료 경계를 불변 문서로 보존합니다.",
        tags: ["DmaicCharter", "VoiceOfCustomer (VOC)", "SipocMap", "CTQ Identification", "Problem Statement"],
        tipTitle: "불변 개정 관리",
        tipText: "프로젝트 헌장과 VOC는 변경될 때마다 새로운 revision과 parentDigest를 생성하여 승인 이력을 위변조 없이 보존합니다.",
        focusIndex: 0
      },
      {
        num: 2,
        title: "2. 측정 (Measure) — 측정시스템 신뢰성 & 공정 기준선",
        badge: "DMAIC 2단계",
        desc: "데이터 수집 계획을 수립하고, Gage R&R(교차 설계)을 실행하여 측정기 반복성과 재현성을 선행 검증합니다. 통과된 신뢰성 데이터를 기반으로 I-MR, Xbar-R 기준선 관리도와 정규/비정규 Cp/Cpk를 산출합니다.",
        tags: ["Data Collection Plan", "Gage R&R (Crossed)", "%Study Var / %Tol", "Baseline SPC", "Cp / Cpk / Ppk"],
        tipTitle: "FMEA 검사장비 연계",
        tipText: "Gage R&R 결과(Analysis Run)는 FMEA 관리계획서의 검사 장비 적합성 증적(Evidence Ref)으로 자동 바인딩됩니다.",
        focusIndex: 1
      },
      {
        num: 3,
        title: "3. 분석 (Analyze) — 80/20 핵심 불량 선별 & 6M 원인 규명",
        badge: "DMAIC 3단계",
        desc: "파레토 분석으로 다빈도/고비용 결함 항목을 80/20 원칙으로 압축하고, 6M(인원, 설비, 자재, 작업, 측정, 환경) 특성요인도(Fishbone)를 통해 잠재 원인 가설을 체계화한 후 근본원인(RCA)을 검증합니다.",
        tags: ["Pareto Analysis", "6M Fishbone Diagram", "Root Cause Analysis (RCA)", "Critical X Identification"],
        tipTitle: "결함 분석 (/defects) 연계",
        tipText: "현장 체크 시트 개정 근거에서 범주별 결함·기회·단위손실을 집계하여 DPMO 및 위험 우선순위를 도출합니다.",
        focusIndex: 2
      },
      {
        num: 4,
        title: "4. 개선 (Improve) — 실험계획법(DOE) & 최적 조건 도출",
        badge: "DMAIC 4단계",
        desc: "검증된 핵심 요인(X)들을 대상으로 완전/일부 요인설계(2-level) 또는 중심합성(CCD)/Box-Behnken 반응표면설계를 실행합니다. 다중응답 만족도 함수(Desirability)를 통해 최적 공정 레시피를 수학적으로 확정합니다.",
        tags: ["DOE Factorial", "Response Surface (CCD/BBD)", "Desirability Optimizer", "Solution Matrix", "Pilot Plan"],
        tipTitle: "반응표면 3D 등고선",
        tipText: "정상점과 능선(Ridge) 분석을 통해 공정 윈도우(Operating Window)를 시각화하여 엔지니어의 의사결정을 지원합니다.",
        focusIndex: 3
      },
      {
        num: 5,
        title: "5. 관리 (Control) — FMEA 관리계획서 & 실시간 피드백 루프",
        badge: "DMAIC 5단계",
        desc: "최적화된 레시피를 FMEA 관리계획서(Control Plan)에 정착시키고, SPC 관리도(I-MR, Xbar-R, EWMA, CUSUM)로 실시간 이상 신호를 모니터링합니다. 관리이탈 발생 시 FMEA 권고 조치로 피드백되는 닫힌 루프를 완성합니다.",
        tags: ["FMEA Control Plan", "Live SPC Monitoring", "Reaction Plan", "Quality Metric Snapshot", "Control Handoff"],
        tipTitle: "닫힌 제어 루프 (Closed Loop)",
        tipText: "SPC의 Nelson 이상 신호는 FMEA 권고 조치의 실행 증거로 연결되어 재발 방지와 표준 작업 개정으로 환류됩니다.",
        focusIndex: 4
      }
    ];

    let currentMode = 'overall'; // 'overall' or 'integrated'
    let currentStep = 0;
    let isPlaying = true;
    let timer = null;
    let intervalTime = 5000;

    // --- Switch Workflow Mode ---
    function switchMode(mode) {
      currentMode = mode;
      currentStep = 0;
      document.getElementById('tabOverall').classList.toggle('active', mode === 'overall');
      document.getElementById('tabIntegrated').classList.toggle('active', mode === 'integrated');
      renderPills();
      updateStage();
    }

    // --- Render Step Badges ---
    function renderPills() {
      const steps = currentMode === 'overall' ? OVERALL_STEPS : INTEGRATED_STEPS;
      const container = document.getElementById('stepPills');
      container.innerHTML = '';
      steps.forEach((s, idx) => {
        const btn = document.createElement('button');
        btn.className = `step-pill ${idx === currentStep ? 'active' : ''}`;
        btn.innerHTML = `<span>${s.num}</span> <span>${currentMode === 'overall' ? s.title.split(' ')[0] : s.title.split(' ')[1]}</span>`;
        btn.onclick = () => jumpToStep(idx);
        container.appendChild(btn);
      });
    }

    // --- Step Navigation ---
    function jumpToStep(idx) {
      currentStep = idx;
      updateStage();
    }

    function nextStep() {
      const steps = currentMode === 'overall' ? OVERALL_STEPS : INTEGRATED_STEPS;
      currentStep = (currentStep + 1) % steps.length;
      updateStage();
    }

    function prevStep() {
      const steps = currentMode === 'overall' ? OVERALL_STEPS : INTEGRATED_STEPS;
      currentStep = (currentStep - 1 + steps.length) % steps.length;
      updateStage();
    }

    function restart() {
      currentStep = 0;
      updateStage();
    }

    function togglePlay() {
      isPlaying = !isPlaying;
      document.getElementById('playIcon').textContent = isPlaying ? '⏸️' : '▶️';
      document.getElementById('playText').textContent = isPlaying ? '일시정지' : '재생';
      if (isPlaying) scheduleNext();
      else clearTimeout(timer);
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

    // --- Render Visual Stage (SVG) ---
    function updateStage() {
      const steps = currentMode === 'overall' ? OVERALL_STEPS : INTEGRATED_STEPS;
      const step = steps[currentStep];

      // Update ProgressBar
      const pct = ((currentStep + 1) / steps.length) * 100;
      document.getElementById('progressBar').style.width = `${pct}%`;

      // Update Pills
      const pills = document.querySelectorAll('.step-pill');
      pills.forEach((p, i) => p.classList.toggle('active', i === currentStep));

      // Update Narration Panel
      document.getElementById('stepNumberBadge').textContent = step.badge;
      document.getElementById('stepHeading').textContent = step.title;
      document.getElementById('stepDescription').textContent = step.desc;
      document.getElementById('tipLabel').textContent = step.tipTitle;
      document.getElementById('tipText').textContent = step.tipText;

      const tagsContainer = document.getElementById('stepTags');
      tagsContainer.innerHTML = '';
      step.tags.forEach(t => {
        const span = document.createElement('span');
        span.className = 'point-tag';
        span.textContent = t;
        tagsContainer.appendChild(span);
      });

      // Render Stage SVG
      const svg = document.getElementById('svgStage');
      if (currentMode === 'overall') {
        renderOverallSvg(svg, currentStep);
      } else {
        renderIntegratedSvg(svg, currentStep);
      }

      if (isPlaying) scheduleNext();
    }

    // --- Overall Stage Renderer ---
    function renderOverallSvg(svg, activeIndex) {
      const phases = [
        { title: "1. 진입 & 작업공간", sub: "홈 / 5대 작업공간", color: "#0284c7", x: 40 },
        { title: "2. 데이터 수집 & 정제", sub: "CSV / Snapshot / Sheet", color: "#475569", x: 275 },
        { title: "3. 분석 구성 & 실행", sub: "바인딩 / 통계 엔진", color: "#6366f1", x: 510 },
        { title: "4. 결과 검토 & 진단", sub: "ResultBundle / 차트 / 이상신호", color: "#10b981", x: 745 },
        { title: "5. 출력 & 증거 보존", sub: "HTML / ZIP / Evidence Ref", color: "#f59e0b", x: 980 }
      ];

      let html = `
        <defs>
          <linearGradient id="cardGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#1E2637" stop-opacity="0.9"/>
            <stop offset="100%" stop-color="#171D2B" stop-opacity="0.95"/>
          </linearGradient>
          <filter id="glowEffect" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
      `;

      // Draw Main Flow Pipeline Lines
      for (let i = 0; i < phases.length - 1; i++) {
        const x1 = phases[i].x + 180;
        const x2 = phases[i + 1].x;
        const y = 200;
        const isPassed = i < activeIndex;
        const isCurrent = i === activeIndex - 1;
        const lineColor = isPassed || isCurrent ? "#4F8EF7" : "#2A3346";
        const strokeW = isCurrent ? 4 : 2;

        html += `
          <line x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" stroke="${lineColor}" stroke-width="${strokeW}" ${isCurrent ? 'class="animated-path"' : ''}/>
          <polygon points="${x2-8},${y-5} ${x2},${y} ${x2-8},${y+5}" fill="${lineColor}"/>
        `;

        // If current moving line, add glowing particle
        if (isCurrent) {
          html += `
            <circle cx="${(x1 + x2) / 2}" cy="${y}" r="5" fill="#83B0F9" filter="url(#glowEffect)">
              <animate attributeName="cx" from="${x1}" to="${x2}" dur="1.2s" repeatCount="indefinite" />
            </circle>
          `;
        }
      }

      // Draw Phase Columns & Content
      phases.forEach((p, idx) => {
        const isActive = idx === activeIndex;
        const y = 80;
        const w = 180;
        const h = 260;
        const strokeColor = isActive ? p.color : "#2A3346";
        const strokeW = isActive ? 3 : 1;
        const glow = isActive ? 'filter="url(#glowEffect)"' : '';
        const scale = isActive ? 'transform="scale(1.03)" style="transform-origin: ' + (p.x + w/2) + 'px 210px;"' : '';

        html += `
          <g class="flow-card ${isActive ? 'active-phase' : ''}" ${scale} onclick="jumpToStep(${idx})">
            <!-- Box Background -->
            <rect x="${p.x}" y="${y}" width="${w}" height="${h}" rx="12" fill="url(#cardGrad)" stroke="${strokeColor}" stroke-width="${strokeW}" ${glow}/>
            
            <!-- Header bar -->
            <rect x="${p.x}" y="${y}" width="${w}" height="42" rx="12" fill="${p.color}" opacity="${isActive ? 0.9 : 0.2}"/>
            <text x="${p.x + w/2}" y="${y + 26}" text-anchor="middle" fill="#FFFFFF" font-size="13" font-weight="700">${p.title}</text>
            <text x="${p.x + w/2}" y="${y + 60}" text-anchor="middle" fill="#A3AAC2" font-size="11">${p.sub}</text>

            <!-- Inner Visual Badges -->
            ${getPhaseVisuals(idx, p.x + 14, y + 80, w - 28, isActive)}

            <!-- Pulse indicator if active -->
            ${isActive ? `
              <circle cx="${p.x + w/2}" cy="${y + h + 24}" r="16" fill="none" stroke="${p.color}" class="pulse-ring"/>
              <circle cx="${p.x + w/2}" cy="${y + h + 24}" r="7" fill="${p.color}"/>
              <text x="${p.x + w/2}" y="${y + h + 44}" text-anchor="middle" fill="${p.color}" font-size="11" font-weight="700">현재 활성 단계</text>
            ` : ''}
          </g>
        `;
      });

      svg.innerHTML = html;
    }

    function getPhaseVisuals(phaseIdx, x, y, w, isActive) {
      if (phaseIdx === 0) {
        return `
          <rect x="${x}" y="${y}" width="${w}" height="28" rx="4" fill="#0284c7" opacity="0.3"/>
          <text x="${x+10}" y="${y+18}" fill="#E8EAF2" font-size="11">🏠 홈 대시보드</text>
          <rect x="${x}" y="${y+34}" width="${w}" height="28" rx="4" fill="#0284c7" opacity="0.3"/>
          <text x="${x+10}" y="${y+52}" fill="#E8EAF2" font-size="11">📈 SPC / DOE 공간</text>
          <rect x="${x}" y="${y+68}" width="${w}" height="28" rx="4" fill="#0284c7" opacity="0.3"/>
          <text x="${x+10}" y="${y+86}" fill="#E8EAF2" font-size="11">🛡️ FMEA / DMAIC</text>
        `;
      } else if (phaseIdx === 1) {
        return `
          <rect x="${x}" y="${y}" width="${w}" height="32" rx="4" fill="#475569" opacity="0.3"/>
          <text x="${x+10}" y="${y+20}" fill="#E8EAF2" font-size="11">📄 CSV 업로드 / 파싱</text>
          <rect x="${x}" y="${y+38}" width="${w}" height="32" rx="4" fill="#475569" opacity="0.4"/>
          <text x="${x+10}" y="${y+58}" fill="#E8EAF2" font-size="11">🔒 Dataset Snapshot</text>
          <rect x="${x}" y="${y+76}" width="${w}" height="32" rx="4" fill="#475569" opacity="0.5"/>
          <text x="${x+10}" y="${y+96}" fill="#E8EAF2" font-size="11">✏️ Worksheet (ETag)</text>
        `;
      } else if (phaseIdx === 2) {
        return `
          <rect x="${x}" y="${y}" width="${w}" height="32" rx="4" fill="#6366f1" opacity="0.3"/>
          <text x="${x+10}" y="${y+20}" fill="#E8EAF2" font-size="11">⚙️ X·Y 파라미터 매핑</text>
          <rect x="${x}" y="${y+38}" width="${w}" height="48" rx="6" fill="#4F46E5" opacity="${isActive ? 0.9 : 0.4}"/>
          <text x="${x+10}" y="${y+58}" fill="#FFFFFF" font-size="11" font-weight="700">🚀 통계 코어 엔진</text>
          <text x="${x+10}" y="${y+74}" fill="#D8E6FD" font-size="10">FastAPI :8765 실행</text>
        `;
      } else if (phaseIdx === 3) {
        return `
          <rect x="${x}" y="${y}" width="${w}" height="30" rx="4" fill="#10b981" opacity="0.3"/>
          <text x="${x+10}" y="${y+19}" fill="#E8EAF2" font-size="11">📦 ResultBundle 객체</text>
          <rect x="${x}" y="${y+36}" width="${w}" height="30" rx="4" fill="#10b981" opacity="0.3"/>
          <text x="${x+10}" y="${y+55}" fill="#E8EAF2" font-size="11">📊 Recharts 관리도 차트</text>
          <rect x="${x}" y="${y+72}" width="${w}" height="30" rx="4" fill="#10b981" opacity="0.3"/>
          <text x="${x+10}" y="${y+91}" fill="#E8EAF2" font-size="11">⚠️ Nelson 이상 신호 진단</text>
        `;
      } else {
        return `
          <rect x="${x}" y="${y}" width="${w}" height="30" rx="4" fill="#f59e0b" opacity="0.3"/>
          <text x="${x+10}" y="${y+19}" fill="#E8EAF2" font-size="11">🖨️ 브라우저 HTML/PDF</text>
          <rect x="${x}" y="${y+36}" width="${w}" height="30" rx="4" fill="#f59e0b" opacity="0.3"/>
          <text x="${x+10}" y="${y+55}" fill="#E8EAF2" font-size="11">🗜️ DOE ZIP / CSV 패키지</text>
          <rect x="${x}" y="${y+72}" width="${w}" height="30" rx="4" fill="#B45309" opacity="${isActive ? 0.9 : 0.5}"/>
          <text x="${x+10}" y="${y+91}" fill="#FFFFFF" font-size="11" font-weight="700">🔗 Evidence Ref 보존</text>
        `;
      }
    }

    // --- Integrated (DMAIC) Stage Renderer ---
    function renderIntegratedSvg(svg, activeIndex) {
      const steps = [
        { title: "Define (정의)", role: "헌장·VOC·SIPOC", color: "#0284c7", x: 40 },
        { title: "Measure (측정)", role: "Gage R&R·기준선 SPC", color: "#ca8a04", x: 275 },
        { title: "Analyze (분석)", role: "파레토·6M 특성요인도", color: "#db2777", x: 510 },
        { title: "Improve (개선)", role: "DOE 요인설계·반응표면", color: "#16a34a", x: 745 },
        { title: "Control (관리)", role: "FMEA 관리계획·SPC 루프", color: "#9333ea", x: 980 }
      ];

      let html = `
        <defs>
          <linearGradient id="dmaicGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#1E2637" stop-opacity="0.9"/>
            <stop offset="100%" stop-color="#171D2B" stop-opacity="0.95"/>
          </linearGradient>
          <filter id="glowEffectDmaic" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
      `;

      // Big Stage Progression Arrows
      for (let i = 0; i < steps.length - 1; i++) {
        const x1 = steps[i].x + 180;
        const x2 = steps[i + 1].x;
        const y = 200;
        const isPassed = i < activeIndex;
        const isCurrent = i === activeIndex - 1;
        const lineColor = isPassed || isCurrent ? steps[i].color : "#2A3346";
        const strokeW = isCurrent ? 4 : 2;

        html += `
          <line x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" stroke="${lineColor}" stroke-width="${strokeW}" ${isCurrent ? 'class="animated-path"' : ''}/>
          <polygon points="${x2-8},${y-5} ${x2},${y} ${x2-8},${y+5}" fill="${lineColor}"/>
        `;

        if (isCurrent) {
          html += `
            <circle cx="${(x1 + x2) / 2}" cy="${y}" r="6" fill="#F0B429" filter="url(#glowEffectDmaic)">
              <animate attributeName="cx" from="${x1}" to="${x2}" dur="1.2s" repeatCount="indefinite" />
            </circle>
          `;
        }
      }

      // Draw Top/Bottom Feedback Curved Loops (Evidence References)
      // 1. Measure(MSA) -> Control(FMEA) (Top Arc)
      const msaX = 275 + 90;
      const fmeaX = 980 + 90;
      html += `
        <path d="M ${msaX} 80 Q ${(msaX + fmeaX) / 2} 15 ${fmeaX} 80" fill="none" stroke="#0284c7" stroke-width="2" stroke-dasharray="6 4" class="animated-path" opacity="0.7"/>
        <text x="${(msaX + fmeaX) / 2}" y="32" text-anchor="middle" fill="#83B0F9" font-size="11" font-weight="700">🔗 [Evidence Ref] Gage R&R 측정시스템 신뢰성 증적 ➔ FMEA 검사장비 연계</text>
      `;

      // 2. Control(Live SPC) -> Control(FMEA) (Feedback Red Arc at bottom)
      html += `
        <path d="M ${fmeaX - 30} 340 Q ${fmeaX - 100} 420 ${fmeaX + 30} 340" fill="none" stroke="#F75555" stroke-width="2.5" stroke-dasharray="6 4" class="animated-path" opacity="0.8"/>
        <text x="${fmeaX}" y="420" text-anchor="middle" fill="#F75555" font-size="11" font-weight="700">⚠️ SPC 관리이탈 시 FMEA 권고조치 피드백 루프</text>
      `;

      // Render DMAIC Stage Columns
      steps.forEach((s, idx) => {
        const isActive = idx === activeIndex;
        const y = 80;
        const w = 180;
        const h = 260;
        const strokeColor = isActive ? s.color : "#2A3346";
        const strokeW = isActive ? 3 : 1;
        const glow = isActive ? 'filter="url(#glowEffectDmaic)"' : '';
        const scale = isActive ? 'transform="scale(1.03)" style="transform-origin: ' + (s.x + w/2) + 'px 210px;"' : '';

        html += `
          <g class="flow-card ${isActive ? 'active-phase' : ''}" ${scale} onclick="jumpToStep(${idx})">
            <rect x="${s.x}" y="${y}" width="${w}" height="${h}" rx="12" fill="url(#dmaicGrad)" stroke="${strokeColor}" stroke-width="${strokeW}" ${glow}/>
            
            <rect x="${s.x}" y="${y}" width="${w}" height="42" rx="12" fill="${s.color}" opacity="${isActive ? 0.9 : 0.2}"/>
            <text x="${s.x + w/2}" y="${y + 26}" text-anchor="middle" fill="#FFFFFF" font-size="13" font-weight="700">${s.title}</text>
            <text x="${s.x + w/2}" y="${y + 60}" text-anchor="middle" fill="#A3AAC2" font-size="11">${s.role}</text>

            ${getDmaicVisuals(idx, s.x + 14, y + 80, w - 28, isActive)}

            ${isActive ? `
              <circle cx="${s.x + w/2}" cy="${y + h + 24}" r="16" fill="none" stroke="${s.color}" class="pulse-ring"/>
              <circle cx="${s.x + w/2}" cy="${y + h + 24}" r="7" fill="${s.color}"/>
              <text x="${s.x + w/2}" y="${y + h + 44}" text-anchor="middle" fill="${s.color}" font-size="11" font-weight="700">진행 중인 품질 단계</text>
            ` : ''}
          </g>
        `;
      });

      svg.innerHTML = html;
    }

    function getDmaicVisuals(idx, x, y, w, isActive) {
      if (idx === 0) {
        return `
          <rect x="${x}" y="${y}" width="${w}" height="28" rx="4" fill="#0284c7" opacity="0.3"/>
          <text x="${x+10}" y="${y+18}" fill="#E8EAF2" font-size="11">📜 프로젝트 헌장</text>
          <rect x="${x}" y="${y+34}" width="${w}" height="28" rx="4" fill="#0284c7" opacity="0.3"/>
          <text x="${x+10}" y="${y+52}" fill="#E8EAF2" font-size="11">🗣️ 고객의 소리 (VOC)</text>
          <rect x="${x}" y="${y+68}" width="${w}" height="28" rx="4" fill="#0284c7" opacity="0.3"/>
          <text x="${x+10}" y="${y+86}" fill="#E8EAF2" font-size="11">🗺️ SIPOC 공정 맵</text>
        `;
      } else if (idx === 1) {
        return `
          <rect x="${x}" y="${y}" width="${w}" height="32" rx="4" fill="#CA8A04" opacity="${isActive ? 0.9 : 0.4}"/>
          <text x="${x+10}" y="${y+20}" fill="#FFFFFF" font-size="11" font-weight="700">🔬 Gage R&R 교차분석</text>
          <rect x="${x}" y="${y+38}" width="${w}" height="28" rx="4" fill="#ca8a04" opacity="0.3"/>
          <text x="${x+10}" y="${y+56}" fill="#E8EAF2" font-size="11">📉 기준선 SPC 관리도</text>
          <rect x="${x}" y="${y+72}" width="${w}" height="28" rx="4" fill="#ca8a04" opacity="0.3"/>
          <text x="${x+10}" y="${y+90}" fill="#E8EAF2" font-size="11">📊 정규/비정규 Cp/Cpk</text>
        `;
      } else if (idx === 2) {
        return `
          <rect x="${x}" y="${y}" width="${w}" height="28" rx="4" fill="#db2777" opacity="0.3"/>
          <text x="${x+10}" y="${y+18}" fill="#E8EAF2" font-size="11">📊 80/20 파레토 분석</text>
          <rect x="${x}" y="${y+34}" width="${w}" height="32" rx="4" fill="#DB2777" opacity="${isActive ? 0.9 : 0.4}"/>
          <text x="${x+10}" y="${y+54}" fill="#FFFFFF" font-size="11" font-weight="700">🐟 6M 특성요인도</text>
          <rect x="${x}" y="${y+72}" width="${w}" height="28" rx="4" fill="#db2777" opacity="0.3"/>
          <text x="${x+10}" y="${y+90}" fill="#E8EAF2" font-size="11">🔍 핵심 인자(X) 도출</text>
        `;
      } else if (idx === 3) {
        return `
          <rect x="${x}" y="${y}" width="${w}" height="28" rx="4" fill="#16a34a" opacity="0.3"/>
          <text x="${x+10}" y="${y+18}" fill="#E8EAF2" font-size="11">🧪 DOE 완전/일부요인</text>
          <rect x="${x}" y="${y+34}" width="${w}" height="32" rx="4" fill="#16A34A" opacity="${isActive ? 0.9 : 0.4}"/>
          <text x="${x+10}" y="${y+54}" fill="#FFFFFF" font-size="11" font-weight="700">🎯 Desirability 최적화</text>
          <rect x="${x}" y="${y+72}" width="${w}" height="28" rx="4" fill="#16a34a" opacity="0.3"/>
          <text x="${x+10}" y="${y+90}" fill="#E8EAF2" font-size="11">📋 개선안 선정 & 파일럿</text>
        `;
      } else {
        return `
          <rect x="${x}" y="${y}" width="${w}" height="32" rx="4" fill="#9333EA" opacity="${isActive ? 0.9 : 0.5}"/>
          <text x="${x+10}" y="${y+20}" fill="#FFFFFF" font-size="11" font-weight="700">📋 FMEA 관리계획서</text>
          <rect x="${x}" y="${y+38}" width="${w}" height="28" rx="4" fill="#9333ea" opacity="0.3"/>
          <text x="${x+10}" y="${y+56}" fill="#E8EAF2" font-size="11">📡 SPC 실시간 모니터링</text>
          <rect x="${x}" y="${y+72}" width="${w}" height="28" rx="4" fill="#9333ea" opacity="0.3"/>
          <text x="${x+10}" y="${y+90}" fill="#E8EAF2" font-size="11">📈 품질 대시보드 지표</text>
        `;
      }
    }

    // --- Theme Toggle ---
    function toggleTheme() {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', next);
      updateStage();
    }

    // --- Keyboard Shortcuts ---
    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space') {
        e.preventDefault();
        togglePlay();
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        nextStep();
      } else if (e.code === 'ArrowLeft') {
        e.preventDefault();
        prevStep();
      } else if (e.key === '1') {
        switchMode('overall');
      } else if (e.key === '2') {
        switchMode('integrated');
      } else if (e.key === 'r' || e.key === 'R') {
        restart();
      }
    });

    // Initial Startup
    document.documentElement.setAttribute('data-theme', 'dark');
    renderPills();
    updateStage();
  </script>
</body>
</html>
"""

def generate_motion_files():
  # 1. Project directory
  p1 = Path(r"D:\Workspace\StatPro\sav.loc\diagrams\statpro_motion_workflow.html")
  p1.write_text(HTML_CONTENT, encoding="utf-8")
  print(f"Generated: {p1}")

  # 2. Artifact directory
  artifact_dir = Path(r"C:\Users\0208m\.gemini\antigravity\brain\3b3a945f-274b-405e-9963-58792169202a")
  p2 = artifact_dir / "statpro_motion_workflow.html"
  p2.write_text(HTML_CONTENT, encoding="utf-8")
  print(f"Generated artifact: {p2}")

if __name__ == "__main__":
  generate_motion_files()

