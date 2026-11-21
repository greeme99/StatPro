"""Generate comprehensive docs-driven motion workflow presentation HTML.

Reflects docs/ (01~09) and README.md: Architecture, Data Lifecycle, and FMEA/DMAIC Closed Loop.
"""

from pathlib import Path

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StatPro 아키텍처 & 품질 워크플로우 종합 모션 가이드 (docs & README 기반)</title>
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
      --warning-700: #8A5A00;
      --danger-100: #FDDCDC;
      --danger-500: #F75555;
      --danger-600: #D42B2B;
      --info-500: #06B6D4;
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

    /* Header */
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

    /* View Switcher */
    .tab-group {
      display: flex;
      background: var(--raised);
      padding: 4px;
      border-radius: var(--radius-pill);
      border: 1px solid var(--border);
      gap: 4px;
    }

    .tab-btn {
      padding: 6px 16px;
      border-radius: var(--radius-pill);
      border: none;
      background: transparent;
      color: var(--text-muted);
      font-size: 12px;
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
      gap: 10px;
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
      font-size: 15px;
    }

    .icon-btn:hover { background: var(--border); }

    .progress-track {
      height: 3px;
      background: var(--border);
      width: 100%;
    }

    .progress-bar {
      height: 100%;
      background: linear-gradient(90deg, var(--brand-500), var(--success-500));
      width: 20%;
      transition: width 0.4s ease;
    }

    /* Main Container */
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

    /* Control Player */
    .player-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 14px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      box-shadow: var(--shadow-md);
    }

    .player-controls {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .ctrl-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 14px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border);
      background: var(--raised);
      color: var(--text-main);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .ctrl-btn:hover { background: var(--border); }

    .ctrl-btn.primary {
      background: var(--brand-600);
      color: #fff;
      border-color: var(--brand-700);
    }

    .ctrl-btn.primary:hover { background: var(--brand-500); }

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

    /* Motion Stage Canvas */
    .canvas-container {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 20px;
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
      0% { r: 10px; opacity: 0.9; stroke-width: 3px; }
      100% { r: 36px; opacity: 0; stroke-width: 1px; }
    }

    .animated-path {
      stroke-dasharray: 8 6;
      animation: dashMove 1.5s linear infinite;
    }

    @keyframes dashMove {
      to { stroke-dashoffset: -28; }
    }

    /* Live Narration & Inspector */
    .narration-panel {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 20px 24px;
      box-shadow: var(--shadow-md);
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 24px;
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

    footer {
      text-align: center;
      padding: 16px;
      font-size: 12px;
      color: var(--text-muted);
      border-top: 1px solid var(--border);
    }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <div class="logo-badge">SP</div>
      <div>
        <span class="brand-title">StatPro</span>
        <span class="brand-sub">docs/ & README.md 기반 종합 제품 워크플로우 가이드</span>
      </div>
    </div>

    <div class="tab-group">
      <button class="tab-btn active" id="tabLayer" onclick="switchView('layer')">1. 계층 아키텍처 (06.Stack)</button>
      <button class="tab-btn" id="tabData" onclick="switchView('data')">2. 엔드투엔드 파이프라인 (README)</button>
      <button class="tab-btn" id="tabLoop" onclick="switchView('loop')">3. FMEA & DMAIC 폐루프 (03.IA)</button>
    </div>

    <div class="top-actions">
      <button class="icon-btn" onclick="toggleTheme()" title="테마 전환">🌓</button>
    </div>
  </header>

  <div class="progress-track">
    <div class="progress-bar" id="progressBar"></div>
  </div>

  <main>
    <div class="player-card">
      <div class="player-controls">
        <button class="ctrl-btn primary" id="playBtn" onclick="togglePlay()">
          <span id="playIcon">⏸️</span> <span id="playText">일시정지</span>
        </button>
        <button class="ctrl-btn" onclick="prevStep()">⏮️ 이전</button>
        <button class="ctrl-btn" onclick="nextStep()">다음 ⏭️</button>
        <button class="ctrl-btn" onclick="restart()">🔄 처음부터</button>
      </div>

      <div class="step-badges" id="stepPills"></div>

      <div>
        <label style="font-size: 12px; color: var(--text-muted); margin-right: 6px;">속도:</label>
        <select class="speed-select" id="speedSelect" onchange="changeSpeed(this.value)">
          <option value="5000">1.0x (표준)</option>
          <option value="3500">1.5x (빠름)</option>
          <option value="2500">2.0x (신속)</option>
        </select>
      </div>
    </div>

    <div class="canvas-container">
      <svg class="stage" id="svgStage" viewBox="0 0 1200 480"></svg>
    </div>

    <div class="narration-panel">
      <div class="narration-content">
        <h3 id="narTitle">
          <span id="stepNumberBadge" class="narration-badge">단계 1/4</span>
          <span id="stepHeading">단계 제목</span>
        </h3>
        <p class="narration-body" id="stepDescription">단계 상세 설명</p>
        <div class="key-points" id="stepTags"></div>
      </div>
      <div class="side-tip">
        <div class="side-tip-title" id="tipLabel">아키텍처 원칙</div>
        <div class="side-tip-desc" id="tipText">내용</div>
      </div>
    </div>
  </main>

  <footer>
    StatPro Enterprise Analytics • docs/01~09 & README.md 표준 규격 준수 • 단축키: [Space] 재생/정지, [←/→] 단계 이동, [1/2/3] 뷰 전환
  </footer>

  <script>
    // --- Data Sources mapped from docs/ and README.md ---
    const VIEW_DATA = {
      layer: [
        {
          num: 1,
          title: "프레젠테이션 계층 (Presentation Layer - web/)",
          badge: "Layer 1/4",
          desc: "React 19.3, TypeScript 7.0, Tailwind CSS v4.3, Vite 8.3 기반의 경량·반응형 로컬 웹 UI입니다. 차트 런타임은 Recharts 3.10으로 고정되어 있으며 WCAG 2.1 AA 및 키보드 전용 조작을 100% 지원합니다.",
          tags: ["React 19.3", "Vite 8.3", "Tailwind v4", "Recharts 3.10", "WCAG 2.1 AA", "Desktop-First"],
          tipTitle: "차트 엔진 거버넌스 (docs/06)",
          tipText: "대규모 벤치마크용 ECharts는 web/benchmarks에 격리되어 제품 런타임으로 유입되지 않으며, 제품 차트는 순수 Recharts만 사용합니다.",
          focusIndex: 0
        },
        {
          num: 2,
          title: "API & 어댑터 계층 (Adapter Layer - statpro.api)",
          badge: "Layer 2/4",
          desc: "FastAPI 0.148와 Uvicorn 0.54 기반의 루프백(127.0.0.1:8765) 전용 로컬 REST API입니다. Pydantic 2.13 모델과 OpenAPI 표준 계약을 통해 UI, CLI, 파이프라인에 동일한 통계 계산 엔드포인트를 제공합니다.",
          tags: ["FastAPI 0.148", "Uvicorn 0.54", "Pydantic 2.13", "127.0.0.1:8765 Loopback", "OpenAPI"],
          tipTitle: "로컬 우선 보안 원칙 (docs/01)",
          tipText: "모든 분석은 로컬 PC 내부에서만 실행되며, 민감한 제조 데이터와 엔지니어링 파라미터가 외부 네트워크로 절대 전송되지 않습니다.",
          focusIndex: 1
        },
        {
          num: 3,
          title: "도메인 & 통계 코어 계층 (Core Layer - statpro.analyses)",
          badge: "Layer 3/4",
          desc: "Python 3.12 기반의 결정론적(Deterministic) 계산 엔진입니다. 완전/일부요인 DOE, 중심합성(CCD)/Box-Behnken 반응표면, I-MR/Xbar-R/EWMA/CUSUM 관리도, Gage R&R, AIAG/VDA 7단계 FMEA 모델을 순수 코드로 실행합니다.",
          tags: ["statpro.analyses", "DOE Core", "SPC 7 Tools", "Crossed Gage R&R", "AIAG/VDA FMEA", "ResultBundle"],
          tipTitle: "NIST 기준값 검증 (docs/07)",
          tipText: "NIST 및 글로벌 표준 테스트 벡터에 대한 수치 허용오차 통과율 100%를 달성했으며, Python 254개 테스트로 상시 검증됩니다.",
          focusIndex: 2
        },
        {
          num: 4,
          title: "영속성 & 거버넌스 계층 (Persistence & Governance Layer)",
          badge: "Layer 4/4",
          desc: "Atomic JSON Document Store를 통해 단일 프로세스 안전 파일 I/O를 수행합니다. 원천 Dataset Snapshot의 SHA-256 Digest 고정, Worksheet Revision의 ETag 낙관적 동시성, 불변 Evidence Reference로 완전한 추적성을 보장합니다.",
          tags: ["Atomic JSON Store", "SHA-256 Digest", "ETag Concurrency", "Evidence Reference", "CycloneDX SBOM"],
          tipTitle: "무손실 데이터 거버넌스 (docs/09)",
          tipText: "결측값은 임의로 0으로 치환되지 않고 결측 상태 그대로 명시 보존되며, 라이선스 허용 목록 fail-closed 검사(OSS 게이트)를 통과합니다.",
          focusIndex: 3
        }
      ],
      data: [
        {
          num: 1,
          title: "1. 데이터 인입 및 스냅샷 동결 (Dataset Snapshot)",
          badge: "Stage 1/5",
          desc: "현장 CSV 파일을 업로드하면 원본 스키마와 데이터 내용을 SHA-256 Digest로 고정한 'Dataset Snapshot'이 생성됩니다. 원본 파일은 변형되지 않는 불변 원천으로 보존됩니다.",
          tags: ["CSV Import", "Dataset Snapshot", "SHA-256 Digest", "Immutable Raw Data"],
          tipTitle: "정량 목표 (docs/01)",
          tipText: "분석 결과의 입력·변환·옵션 출처 추적 가능률 100% 및 결과 재현율 100%를 보증하는 핵심 출발점입니다.",
          focusIndex: 0
        },
        {
          num: 2,
          title: "2. 워크시트 개정 및 변수 바인딩 (Worksheet Revision)",
          badge: "Stage 2/5",
          desc: "스냅샷 위에 'Worksheet' 레이어를 얹어 수치형/범주형 타입 프로파일링, 결측치 처리, 파생 열 생성 작업을 수행합니다. ETag 기반 낙관적 동시성으로 작업 버전 충돌을 차단합니다.",
          tags: ["Worksheet Revision", "Type Profiling", "ETag Locking", "Input Bindings (X, Y)"],
          tipTitle: "작업표 독립성 (CONTEXT-MAP)",
          tipText: "Shared Data 컨텍스트는 통계적 해석이나 FMEA 상태를 소유하지 않고 순수한 데이터 무결성과 revision만 담당합니다.",
          focusIndex: 1
        },
        {
          num: 3,
          title: "3. 통계 코어 분석 실행 (Analysis Run)",
          badge: "Stage 3/5",
          desc: "바인딩된 인자와 통계 옵션(알파 위험, 부분군 크기 n)을 결합하여 'Analysis Run'을 생성합니다. 엔진 버전과 입력 digest가 고정된 채 FastAPI 코어에서 연산이 수행됩니다.",
          tags: ["Analysis Run", "Engine Version Binding", "Deterministic Compute", "FastAPI Service"],
          tipTitle: "입력 검증 원칙 (docs/06)",
          tipText: "유효하지 않은 입력은 AnalysisInputError로 명시적 실패하며, 불완전한 계산을 정상인 것처럼 왜곡 표시하지 않습니다.",
          focusIndex: 2
        },
        {
          num: 4,
          title: "4. 결과 검토 및 이상 신호 진단 (ResultBundle)",
          badge: "Stage 4/5",
          desc: "연산 결과는 표준 'ResultBundle'로 캡슐화됩니다. Recharts 반응형 차트 위에 관리한계선(UCL/LCL)과 규격한계선(USL/LSL)이 렌더링되며, Nelson 이상 신호 1~8 규칙과 공정능력(Cp/Cpk)이 즉시 진단됩니다.",
          tags: ["ResultBundle Envelope", "Nelson Rules 1~8", "Process Capability (Cp/Cpk)", "ANOVA Table"],
          tipTitle: "관리한계 vs 규격한계 (docs/05)",
          tipText: "공정 자체의 자연적 변동(관리한계)과 설계상의 고객 요구(규격한계)는 별개의 도메인 개념으로 명확히 구분 표시됩니다.",
          focusIndex: 3
        },
        {
          num: 5,
          title: "5. 다중 형식 출력 및 증거 연계 (Export & Evidence)",
          badge: "Stage 5/5",
          desc: "결과는 브라우저 인쇄용 HTML/PDF, 결정론적 ZIP 패키지, SpreadsheetML 호환 CSV로 출력됩니다. 결과 번들은 FMEA 및 DMAIC의 'Evidence Reference'로 바인딩되어 품질 관리의 근거가 됩니다.",
          tags: ["HTML / PDF Export", "Deterministic ZIP", "SpreadsheetML CSV", "Evidence Reference"],
          tipTitle: "품질 지표 스냅샷 (/quality)",
          tipText: "저장된 ResultBundle의 수치 경로는 불변 품질 지표 스냅샷으로 연결되어 대시보드에서 DPMO 및 위험도를 상시 추적합니다.",
          focusIndex: 4
        }
      ],
      loop: [
        {
          num: 1,
          title: "정의 (Define) ➔ 측정 (Measure) : CTQ & MSA 적합성",
          badge: "Loop 1/4",
          desc: "프로젝트 헌장과 고객의 소리(VOC)에서 도출된 핵심품질특성(CTQ)을 측정 단계로 인계합니다. 데이터 수집 전 Gage R&R(교차설계)을 실행하여 측정시스템의 반복성·재현성을 사전에 검증합니다.",
          tags: ["Charter & VOC", "CTQ Handoff", "Gage R&R Crossed", "%Study Var / %Tol"],
          tipTitle: "측정기 증적 바인딩 (docs/02)",
          tipText: "Gage R&R 분석 결과는 FMEA 관리계획서의 검사 장비 적합성 증적(Evidence Ref)으로 즉시 연계됩니다.",
          focusIndex: 0
        },
        {
          num: 2,
          title: "분석 (Analyze) ➔ 개선 (Improve) : 원인 규명 & DOE 최적화",
          badge: "Loop 2/4",
          desc: "파레토 분석으로 불량 요인을 80/20으로 압축하고 6M 특성요인도로 도출한 핵심 원인(X)을 DOE 실험계획으로 이관합니다. 2수준 요인설계 및 중심합성(CCD) 반응표면과 Desirability 만족도 함수로 최적 공정 조건을 도출합니다.",
          tags: ["Pareto 80/20", "6M Fishbone", "DOE Factorial", "Response Surface (CCD)", "Desirability Recipe"],
          tipTitle: "3D 반응표면 & 등고선 (docs/06)",
          tipText: "결정론적 등각 투영 3D 와이어프레임과 토큰 기반 SVG 등고선 표면을 통해 최적 공정 윈도우를 시각화합니다.",
          focusIndex: 1
        },
        {
          num: 3,
          title: "개선 (Improve) ➔ 관리 (Control) : FMEA 관리계획서 정착",
          badge: "Loop 3/4",
          desc: "최적화된 공정 레시피와 허용 윈도우를 FMEA 관리계획서(Control Plan)의 핵심 관리항목으로 등록합니다. 공정 흐름-고장 모드-Action Priority(AP)와 연계된 표준 작업 절차를 수립합니다.",
          tags: ["Control Plan", "Action Priority (AP)", "PFMEA Linkage", "Reaction Plan", "Control Handoff"],
          tipTitle: "불변 FMEA 추적성 (docs/03)",
          tipText: "FMEA 연구는 AIAG/VDA 7단계를 엄격히 준수하며 공정흐름–공정특성–PFMEA–Control Plan 간 명시적 ID로 추적됩니다.",
          focusIndex: 2
        },
        {
          num: 4,
          title: "관리 (Control) ➔ FMEA : 실시간 SPC 감시 & 권고조치 피드백",
          badge: "Loop 4/4",
          desc: "관리계획서에 따라 SPC 관리도(I-MR, Xbar-R, EWMA, CUSUM)로 실시간 이상 신호를 감시합니다. 관리 이탈이나 Nelson 신호 발생 시 FMEA 권고 조치(Recommended Action)로 즉시 피드백되는 '완전한 닫힌 루프(Closed-Loop)'를 형성합니다.",
          tags: ["SPC Live Monitoring", "Nelson Rule Trigger", "FMEA Action Feedback", "Closed-Loop Governance"],
          tipTitle: "제조 품질 무결성",
          tipText: "이 닫힌 루프를 통해 품질 이상이 단발성 조치로 끝나지 않고 표준 FMEA 문서와 관리계획서의 지속적 개정으로 환류됩니다.",
          focusIndex: 3
        }
      ]
    };

    let currentView = 'layer'; // 'layer', 'data', 'loop'
    let currentStep = 0;
    let isPlaying = true;
    let timer = null;
    let intervalTime = 5000;

    function switchView(view) {
      currentView = view;
      currentStep = 0;
      document.getElementById('tabLayer').classList.toggle('active', view === 'layer');
      document.getElementById('tabData').classList.toggle('active', view === 'data');
      document.getElementById('tabLoop').classList.toggle('active', view === 'loop');
      renderPills();
      updateStage();
    }

    function renderPills() {
      const steps = VIEW_DATA[currentView];
      const container = document.getElementById('stepPills');
      container.innerHTML = '';
      steps.forEach((s, idx) => {
        const btn = document.createElement('button');
        btn.className = `step-pill ${idx === currentStep ? 'active' : ''}`;
        btn.innerHTML = `<span>${s.num}</span> <span>${s.title.split(' ')[0]}</span>`;
        btn.onclick = () => jumpToStep(idx);
        container.appendChild(btn);
      });
    }

    function jumpToStep(idx) {
      currentStep = idx;
      updateStage();
    }

    function nextStep() {
      const steps = VIEW_DATA[currentView];
      currentStep = (currentStep + 1) % steps.length;
      updateStage();
    }

    function prevStep() {
      const steps = VIEW_DATA[currentView];
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

    function updateStage() {
      const steps = VIEW_DATA[currentView];
      const step = steps[currentStep];

      // Progress Bar
      const pct = ((currentStep + 1) / steps.length) * 100;
      document.getElementById('progressBar').style.width = `${pct}%`;

      // Update Badges
      const pills = document.querySelectorAll('.step-pill');
      pills.forEach((p, i) => p.classList.toggle('active', i === currentStep));

      // Update Narration
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

      // Render Active SVG
      const svg = document.getElementById('svgStage');
      if (currentView === 'layer') renderLayerSvg(svg, currentStep);
      else if (currentView === 'data') renderDataSvg(svg, currentStep);
      else renderLoopSvg(svg, currentStep);

      if (isPlaying) scheduleNext();
    }

    // --- Renderer 1: Architecture Layers ---
    function renderLayerSvg(svg, activeIdx) {
      const layers = [
        { name: "프레젠테이션 계층 (Presentation)", desc: "React 19 + TypeScript + Tailwind v4 + Recharts (web/)", color: "#0284c7", y: 60 },
        { name: "API & 어댑터 계층 (Adapter)", desc: "FastAPI + Uvicorn (127.0.0.1:8765 루프백 전용 REST API)", color: "#6366f1", y: 155 },
        { name: "도메인 & 통계 코어 (Core)", desc: "DOE · SPC 7도구 · Gage R&R · FMEA 7단계 · ResultBundle (statpro/)", color: "#10b981", y: 250 },
        { name: "영속성 & 거버넌스 (Persistence)", desc: "Atomic JSON Document Store · SHA-256 Digest · ETag · Evidence Ref", color: "#f59e0b", y: 345 }
      ];

      let html = `
        <defs>
          <filter id="glowLayer" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="6" result="blur"/>
            <feComposite in="SourceGraphic" in2="blur" operator="over"/>
          </filter>
        </defs>
      `;

      // Inter-layer flow arrows
      for (let i = 0; i < layers.length - 1; i++) {
        const y1 = layers[i].y + 70;
        const y2 = layers[i + 1].y;
        const isActiveFlow = i === activeIdx - 1;
        html += `
          <line x1="600" y1="${y1}" x2="600" y2="${y2}" stroke="${isActiveFlow ? '#4F8EF7' : '#2A3346'}" stroke-width="${isActiveFlow ? 3 : 2}" ${isActiveFlow ? 'class="animated-path"' : ''}/>
          <polygon points="595,${y2-6} 600,${y2} 605,${y2-6}" fill="${isActiveFlow ? '#4F8EF7' : '#2A3346'}"/>
        `;
        if (isActiveFlow) {
          html += `
            <circle cx="600" cy="${(y1 + y2) / 2}" r="5" fill="#83B0F9" filter="url(#glowLayer)">
              <animate attributeName="cy" from="${y1}" to="${y2}" dur="1s" repeatCount="indefinite" />
            </circle>
          `;
        }
      }

      // Draw Layers
      layers.forEach((l, idx) => {
        const isActive = idx === activeIdx;
        const strokeW = isActive ? 3 : 1;
        const glow = isActive ? 'filter="url(#glowLayer)"' : '';
        const scale = isActive ? 'transform="scale(1.02)" style="transform-origin: 600px ' + (l.y + 35) + 'px;"' : '';

        html += `
          <g class="flow-card ${isActive ? 'active-phase' : ''}" ${scale} onclick="jumpToStep(${idx})">
            <rect x="150" y="${l.y}" width="900" height="70" rx="10" fill="#171D2B" stroke="${isActive ? l.color : '#2A3346'}" stroke-width="${strokeW}" ${glow}/>
            <rect x="150" y="${l.y}" width="16" height="70" rx="4" fill="${l.color}"/>
            <text x="185" y="${l.y + 28}" fill="#FFFFFF" font-size="14" font-weight="700">${l.name}</text>
            <text x="185" y="${l.y + 50}" fill="#A3AAC2" font-size="12">${l.desc}</text>
            ${isActive ? `
              <circle cx="1010" cy="${l.y + 35}" r="14" fill="none" stroke="${l.color}" class="pulse-ring"/>
              <circle cx="1010" cy="${l.y + 35}" r="6" fill="${l.color}"/>
            ` : ''}
          </g>
        `;
      });

      svg.innerHTML = html;
    }

    // --- Renderer 2: Data & Execution Pipeline ---
    function renderDataSvg(svg, activeIdx) {
      const stages = [
        { title: "1. Dataset Snapshot", sub: "CSV 동결 · SHA-256", color: "#0284c7", x: 40 },
        { title: "2. Worksheet Revision", sub: "타입 프로파일 · ETag", color: "#475569", x: 275 },
        { title: "3. Analysis Run", sub: "엔진 바인딩 · 계산", color: "#6366f1", x: 510 },
        { title: "4. ResultBundle", sub: "차트 · 이상신호 진단", color: "#10b981", x: 745 },
        { title: "5. Export & Evidence", sub: "HTML/PDF · 지표보존", color: "#f59e0b", x: 980 }
      ];

      let html = `<defs><filter id="glowData" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6" result="blur"/><feComposite in="SourceGraphic" in2="blur" operator="over"/></filter></defs>`;

      // Horizontal flow pipeline
      for (let i = 0; i < stages.length - 1; i++) {
        const x1 = stages[i].x + 180;
        const x2 = stages[i + 1].x;
        const y = 220;
        const isCurrent = i === activeIdx - 1;
        html += `
          <line x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" stroke="${isCurrent ? '#4F8EF7' : '#2A3346'}" stroke-width="${isCurrent ? 3 : 2}" ${isCurrent ? 'class="animated-path"' : ''}/>
          <polygon points="${x2-8},${y-5} ${x2},${y} ${x2-8},${y+5}" fill="${isCurrent ? '#4F8EF7' : '#2A3346'}"/>
        `;
        if (isCurrent) {
          html += `
            <circle cx="${(x1 + x2) / 2}" cy="${y}" r="5" fill="#83B0F9" filter="url(#glowData)">
              <animate attributeName="cx" from="${x1}" to="${x2}" dur="1.2s" repeatCount="indefinite" />
            </circle>
          `;
        }
      }

      stages.forEach((s, idx) => {
        const isActive = idx === activeIdx;
        const y = 100;
        const w = 180;
        const h = 240;
        const scale = isActive ? 'transform="scale(1.03)" style="transform-origin: ' + (s.x + w/2) + 'px 220px;"' : '';

        html += `
          <g class="flow-card ${isActive ? 'active-phase' : ''}" ${scale} onclick="jumpToStep(${idx})">
            <rect x="${s.x}" y="${y}" width="${w}" height="${h}" rx="12" fill="#171D2B" stroke="${isActive ? s.color : '#2A3346'}" stroke-width="${isActive ? 3 : 1}" ${isActive ? 'filter="url(#glowData)"' : ''}/>
            <rect x="${s.x}" y="${y}" width="${w}" height="40" rx="12" fill="${s.color}" opacity="${isActive ? 0.9 : 0.25}"/>
            <text x="${s.x + w/2}" y="${y + 25}" text-anchor="middle" fill="#FFFFFF" font-size="12" font-weight="700">${s.title}</text>
            <text x="${s.x + w/2}" y="${y + 60}" text-anchor="middle" fill="#A3AAC2" font-size="11">${s.sub}</text>

            <circle cx="${s.x + w/2}" cy="${y + 130}" r="32" fill="#1E2637" stroke="${s.color}" stroke-width="2"/>
            <text x="${s.x + w/2}" y="${y + 135}" text-anchor="middle" font-size="20">${['📄', '✏️', '⚙️', '📊', '🖨️'][idx]}</text>

            ${isActive ? `
              <circle cx="${s.x + w/2}" cy="${y + h + 24}" r="14" fill="none" stroke="${s.color}" class="pulse-ring"/>
              <circle cx="${s.x + w/2}" cy="${y + h + 24}" r="6" fill="${s.color}"/>
              <text x="${s.x + w/2}" y="${y + h + 42}" text-anchor="middle" fill="${s.color}" font-size="11" font-weight="700">진행 중</text>
            ` : ''}
          </g>
        `;
      });

      svg.innerHTML = html;
    }

    // --- Renderer 3: Closed-Loop FMEA & DMAIC ---
    function renderLoopSvg(svg, activeIdx) {
      const nodes = [
        { title: "정의 & 측정", sub: "VOC ➔ Gage R&R 적합성", color: "#0284c7", x: 100, y: 120 },
        { title: "분석 & 개선", sub: "80/20 파레토 ➔ DOE 최적화", color: "#ca8a04", x: 750, y: 120 },
        { title: "관리계획 정착", sub: "FMEA Control Plan 등록", color: "#16a34a", x: 750, y: 310 },
        { title: "실시간 감시 & 피드백", sub: "SPC 관리도 ➔ FMEA 권고조치", color: "#9333ea", x: 100, y: 310 }
      ];

      let html = `<defs><filter id="glowLoop" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6" result="blur"/><feComposite in="SourceGraphic" in2="blur" operator="over"/></filter></defs>`;

      // Closed Loop Arrows (Clockwise)
      const paths = [
        { x1: 450, y1: 170, x2: 750, y2: 170, label: "CTQ & 핵심 인자(X's)" },
        { x1: 925, y1: 220, x2: 925, y2: 310, label: "최적화 레시피 인계" },
        { x1: 750, y1: 360, x2: 450, y2: 360, label: "실시간 SPC 관리도 감시" },
        { x1: 275, y1: 310, x2: 275, y2: 220, label: "이상 발생 시 FMEA 조치 환류" }
      ];

      paths.forEach((p, idx) => {
        const isCurrent = idx === activeIdx;
        html += `
          <line x1="${p.x1}" y1="${p.y1}" x2="${p.x2}" y2="${p.y2}" stroke="${isCurrent ? '#4F8EF7' : '#2A3346'}" stroke-width="${isCurrent ? 3 : 2}" ${isCurrent ? 'class="animated-path"' : ''}/>
          <text x="${(p.x1 + p.x2) / 2}" y="${(p.y1 + p.y2) / 2 - 8}" text-anchor="middle" fill="${isCurrent ? '#83B0F9' : '#5A6080'}" font-size="11" font-weight="${isCurrent ? '700' : '400'}">${p.label}</text>
        `;
        if (isCurrent) {
          html += `
            <circle cx="${(p.x1 + p.x2) / 2}" cy="${(p.y1 + p.y2) / 2}" r="5" fill="#83B0F9" filter="url(#glowLoop)">
              <animate attributeName="${p.x1 === p.x2 ? 'cy' : 'cx'}" from="${p.x1 === p.x2 ? p.y1 : p.x1}" to="${p.x1 === p.x2 ? p.y2 : p.x2}" dur="1.2s" repeatCount="indefinite"/>
            </circle>
          `;
        }
      });

      nodes.forEach((n, idx) => {
        const isActive = idx === activeIdx;
        const w = 350;
        const h = 100;
        const scale = isActive ? 'transform="scale(1.03)" style="transform-origin: ' + (n.x + w/2) + 'px ' + (n.y + h/2) + 'px;"' : '';

        html += `
          <g class="flow-card ${isActive ? 'active-phase' : ''}" ${scale} onclick="jumpToStep(${idx})">
            <rect x="${n.x}" y="${n.y}" width="${w}" height="${h}" rx="12" fill="#171D2B" stroke="${isActive ? n.color : '#2A3346'}" stroke-width="${isActive ? 3 : 1}" ${isActive ? 'filter="url(#glowLoop)"' : ''}/>
            <rect x="${n.x}" y="${n.y}" width="12" height="${h}" rx="4" fill="${n.color}"/>
            <text x="${n.x + 28}" y="${n.y + 40}" fill="#FFFFFF" font-size="15" font-weight="700">${n.title}</text>
            <text x="${n.x + 28}" y="${n.y + 68}" fill="#A3AAC2" font-size="12">${n.sub}</text>
            ${isActive ? `
              <circle cx="${n.x + w - 30}" cy="${n.y + h/2}" r="14" fill="none" stroke="${n.color}" class="pulse-ring"/>
              <circle cx="${n.x + w - 30}" cy="${n.y + h/2}" r="6" fill="${n.color}"/>
            ` : ''}
          </g>
        `;
      });

      svg.innerHTML = html;
    }

    function toggleTheme() {
      const cur = document.documentElement.getAttribute('data-theme');
      document.documentElement.setAttribute('data-theme', cur === 'light' ? 'dark' : 'light');
      updateStage();
    }

    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space') { e.preventDefault(); togglePlay(); }
      else if (e.code === 'ArrowRight') { e.preventDefault(); nextStep(); }
      else if (e.code === 'ArrowLeft') { e.preventDefault(); prevStep(); }
      else if (e.key === '1') switchView('layer');
      else if (e.key === '2') switchView('data');
      else if (e.key === '3') switchView('loop');
      else if (e.key === 'r' || e.key === 'R') restart();
    });

    document.documentElement.setAttribute('data-theme', 'dark');
    renderPills();
    updateStage();
  </script>
</body>
</html>
"""

def generate_docs_motion_files():
  # 1. Save in diagrams/
  p1 = Path(r"D:\Workspace\StatPro\myStatPro\diagrams\docs_motion_workflow.html")
  p1.write_text(HTML_CONTENT, encoding="utf-8")
  print(f"Generated: {p1}")

  # 2. Save in Artifact directory
  artifact_dir = Path(r"C:\Users\0208m\.gemini\antigravity\brain\3b3a945f-274b-405e-9963-58792169202a")
  p2 = artifact_dir / "docs_motion_workflow.html"
  p2.write_text(HTML_CONTENT, encoding="utf-8")
  print(f"Generated artifact: {p2}")

if __name__ == "__main__":
  generate_docs_motion_files()

