"""Comprehensive Visual Themes Generator for Motion Diagram Design Skill.

Implements all infographic styles provided in user images:
  1. ROADMAP: Winding asphalt highway with animated lane dashes, ascending
  curve, and numbered location pin flags.
  2. HUB: Central strategy diamond/gear core with radial dashed beams and 5
  pill cards.
  3. INTERLOCK: Interlocking puzzle/notched horizontal cards with circular badge
  nodes and colored borders.
  4. STUDIO: Upgraded 7-theme switcher studio with live tab switching.
"""

import json
import os
import shutil

ROADMAP_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StatPro 아스팔트 고속도로 로드맵 (Roadmap Highway Timeline)</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
  <style>
    :root {
      --bg-page: #f8fafc;
      --bg-card: #ffffff;
      --text-main: #0f172a;
      --text-sub: #64748b;
      --road-asphalt: #334155;
      --road-border: #1e293b;
      --road-dash: #ffffff;
      --primary-blue: #2563eb;
      --color-step1: #eab308;
      --color-step2: #10b981;
      --color-step3: #3b82f6;
      --color-step4: #8b5cf6;
      --color-step5: #ec4899;
      --border-color: #e2e8f0;
      --card-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -2px rgba(0,0,0,0.05);
    }
    body.dark-mode {
      --bg-page: #090d16;
      --bg-card: #1e293b;
      --text-main: #f8fafc;
      --text-sub: #94a3b8;
      --road-asphalt: #1e293b;
      --road-border: #0f172a;
      --border-color: #334155;
      --card-shadow: 0 10px 15px -3px rgba(0,0,0,0.4);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg-page);
      color: var(--text-main);
      font-family: 'Pretendard', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: auto;
      transition: background 0.3s;
    }
    .container {
      max-width: 1280px;
      margin: 0 auto;
      width: 100%;
      padding: 24px;
      min-width: 1100px;
    }
    /* Header & Controls */
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }
    .title-box h1 {
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .badge {
      font-size: 11px;
      background: #e0f2fe;
      color: #0369a1;
      padding: 3px 8px;
      border-radius: 4px;
      font-weight: 600;
    }
    body.dark-mode .badge {
      background: #0369a1;
      color: #e0f2fe;
    }
    .controls {
      display: flex;
      gap: 8px;
      align-items: center;
    }
    .btn {
      padding: 8px 14px;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      border-radius: 8px;
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }
    .btn:hover { background: #f1f5f9; }
    body.dark-mode .btn:hover { background: #334155; }
    .btn-primary {
      background: #2563eb;
      border-color: #2563eb;
      color: #fff;
    }
    .btn-primary:hover { background: #1d4ed8; }

    /* Narration Banner */
    .banner {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-left: 4px solid var(--primary-blue);
      border-radius: 8px;
      padding: 14px 20px;
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: var(--card-shadow);
    }
    .banner-text {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .banner-sub {
      font-size: 12px;
      color: var(--text-sub);
      margin-top: 2px;
      font-weight: 400;
    }

    /* Roadmap Canvas Stage */
    .roadmap-stage {
      position: relative;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 40px 30px;
      margin-bottom: 24px;
      box-shadow: var(--card-shadow);
      min-height: 440px;
      overflow: hidden;
    }
    .svg-road-layer {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
    }
    .road-track {
      fill: none;
      stroke: var(--road-asphalt);
      stroke-width: 44;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .road-border {
      fill: none;
      stroke: var(--road-border);
      stroke-width: 48;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .road-dashes {
      fill: none;
      stroke: var(--road-dash);
      stroke-width: 3;
      stroke-dasharray: 12, 16;
      stroke-linecap: round;
      animation: roadMotion 1.5s linear infinite;
    }
    @keyframes roadMotion {
      from { stroke-dashoffset: 28; }
      to { stroke-dashoffset: 0; }
    }

    /* Pin Markers */
    .pin-group {
      position: absolute;
      transform: translate(-50%, -100%);
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
      z-index: 10;
    }
    .pin-head {
      width: 48px;
      height: 48px;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 10px rgba(0,0,0,0.25);
      position: relative;
      transition: all 0.3s;
    }
    .pin-head-inner {
      transform: rotate(45deg);
      color: #fff;
      font-weight: 800;
      font-size: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .pin-stalk {
      width: 2px;
      height: 18px;
      border-left: 2px dashed #94a3b8;
    }
    .pin-base-dot {
      width: 26px;
      height: 26px;
      border-radius: 50%;
      background: #fff;
      border: 3px solid;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: 800;
      box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .pin-group.active {
      transform: translate(-50%, -105%) scale(1.15);
      z-index: 20;
    }
    .pin-group.active .pin-head {
      box-shadow: 0 0 20px currentColor;
    }

    /* Step Cards Placed Along Road */
    .step-card {
      position: absolute;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 12px 16px;
      width: 200px;
      box-shadow: var(--card-shadow);
      transform: translate(-50%, 0);
      cursor: pointer;
      transition: all 0.3s;
      z-index: 5;
    }
    .step-card:hover, .step-card.active {
      border-color: var(--primary-blue);
      transform: translate(-50%, -3px);
      box-shadow: 0 8px 16px rgba(37,99,235,0.15);
    }
    .step-card.active {
      background: #f0f7ff;
    }
    body.dark-mode .step-card.active {
      background: #1e3a5f;
    }
    .step-card-num {
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 2px;
    }
    .step-card-title {
      font-size: 13px;
      font-weight: 700;
      color: var(--text-main);
      margin-bottom: 4px;
    }
    .step-card-desc {
      font-size: 11px;
      color: var(--text-sub);
      line-height: 1.4;
    }

    /* Car/Vehicle Animation on Path */
    .vehicle-marker {
      position: absolute;
      width: 32px;
      height: 32px;
      background: #2563eb;
      border: 2px solid #fff;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 15px rgba(37,99,235,0.7);
      color: #fff;
      font-size: 16px;
      z-index: 15;
      transition: all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
      transform: translate(-50%, -50%);
    }

    /* Bottom Info Drawer */
    .drawer {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px 24px;
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 24px;
      box-shadow: var(--card-shadow);
    }
    .drawer h3 {
      font-size: 16px;
      font-weight: 800;
      margin-bottom: 8px;
    }
    .drawer p {
      font-size: 13px;
      color: var(--text-sub);
      line-height: 1.6;
      margin-bottom: 12px;
    }
    .checklist {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 6px;
      font-size: 12px;
    }
    .check-item {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .check-icon {
      color: #10b981;
      font-weight: bold;
    }
    .meta-box {
      border-left: 1px solid var(--border-color);
      padding-left: 20px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 12px;
      font-size: 12px;
    }
    .meta-item-label {
      color: var(--text-sub);
      font-size: 11px;
      text-transform: uppercase;
      font-weight: 600;
    }
    .meta-item-val {
      font-size: 15px;
      font-weight: 700;
      color: var(--text-main);
    }
  </style>
</head>
<body>

  <div class="container">
    <header class="header">
      <div class="title-box">
        <h1>StatPro 커브드 아스팔트 로드맵 타임라인</h1>
        <span class="badge">INFOGRAPHIC ROADMAP THEME</span>
      </div>
      <div class="controls">
        <button class="btn" id="btnPrev">&lt;</button>
        <button class="btn btn-primary" id="btnPlay">
          <span id="playIcon">▷</span> <span id="playText">흐름 주행</span>
        </button>
        <button class="btn" id="btnNext">&gt;</button>
        <button class="btn" id="btnReset">↺</button>
        <button class="btn" id="btnTheme">🌙</button>
      </div>
    </header>

    <div class="banner">
      <div>
        <div class="banner-text" id="bannerTitle">
          <span>🚗 Step 1. 원천 데이터 준비 (CSV / 계측기 직접 수집)</span>
        </div>
        <div class="banner-sub" id="bannerSub">
          공정 측정자가 원천 데이터를 입력하면 D:\\StatProData 로컬 스토리지에 세션이 생성됩니다.
        </div>
      </div>
      <div id="stepCounter" style="font-weight: 800; font-size: 14px; color: #2563eb;">1 / 5</div>
    </div>

    <!-- Highway Canvas -->
    <div class="roadmap-stage">
      <svg class="svg-road-layer" viewBox="0 0 1200 440">
        <!-- Road Outer Border -->
        <path class="road-border" d="M 60 360 C 240 360, 280 340, 400 320 C 540 300, 580 180, 720 180 C 860 180, 920 100, 1140 100" />
        <!-- Road Asphalt Layer -->
        <path class="road-track" d="M 60 360 C 240 360, 280 340, 400 320 C 540 300, 580 180, 720 180 C 860 180, 920 100, 1140 100" />
        <!-- Road White Dashed Lane Line -->
        <path class="road-dashes" d="M 60 360 C 240 360, 280 340, 400 320 C 540 300, 580 180, 720 180 C 860 180, 920 100, 1140 100" />
      </svg>

      <!-- Pin 1 -->
      <div class="pin-group active" id="pin-0" style="left: 140px; top: 345px; color: #eab308;" onclick="selectStep(0)">
        <div class="pin-head" style="background: #eab308;">
          <div class="pin-head-inner">🔍</div>
        </div>
        <div class="pin-stalk"></div>
        <div class="pin-base-dot" style="border-color: #eab308; color: #eab308;">1</div>
      </div>
      <div class="step-card active" id="card-0" style="left: 140px; top: 220px;" onclick="selectStep(0)">
        <div class="step-card-num" style="color: #eab308;">Step 01</div>
        <div class="step-card-title">원천 데이터 로드</div>
        <div class="step-card-desc">CSV · XLSX 계측기 파일<br>D:\StatProData 로컬 격리</div>
      </div>

      <!-- Pin 2 -->
      <div class="pin-group" id="pin-1" style="left: 360px; top: 310px; color: #10b981;" onclick="selectStep(1)">
        <div class="pin-head" style="background: #10b981;">
          <div class="pin-head-inner">⚙️</div>
        </div>
        <div class="pin-stalk"></div>
        <div class="pin-base-dot" style="border-color: #10b981; color: #10b981;">2</div>
      </div>
      <div class="step-card" id="card-1" style="left: 360px; top: 375px;" onclick="selectStep(1)">
        <div class="step-card-num" style="color: #10b981;">Step 02</div>
        <div class="step-card-title">변수 & 규격 매핑</div>
        <div class="step-card-desc">결측치 0 대체 원천 금지<br>USL / LSL 공학규격 분리</div>
      </div>

      <!-- Pin 3 -->
      <div class="pin-group" id="pin-2" style="left: 600px; top: 220px; color: #3b82f6;" onclick="selectStep(2)">
        <div class="pin-head" style="background: #3b82f6;">
          <div class="pin-head-inner">📊</div>
        </div>
        <div class="pin-stalk"></div>
        <div class="pin-base-dot" style="border-color: #3b82f6; color: #3b82f6;">3</div>
      </div>
      <div class="step-card" id="card-2" style="left: 600px; top: 80px;" onclick="selectStep(2)">
        <div class="step-card-num" style="color: #3b82f6;">Step 03</div>
        <div class="step-card-title">통계 연산 코어</div>
        <div class="step-card-desc">정규성 AD검정 · Gage R&R<br>Nelson 8 Rules 실시간 판정</div>
      </div>

      <!-- Pin 4 -->
      <div class="pin-group" id="pin-3" style="left: 820px; top: 165px; color: #8b5cf6;" onclick="selectStep(3)">
        <div class="pin-head" style="background: #8b5cf6;">
          <div class="pin-head-inner">⚖️</div>
        </div>
        <div class="pin-stalk"></div>
        <div class="pin-base-dot" style="border-color: #8b5cf6; color: #8b5cf6;">4</div>
      </div>
      <div class="step-card" id="card-3" style="left: 820px; top: 235px;" onclick="selectStep(3)">
        <div class="step-card-num" style="color: #8b5cf6;">Step 04</div>
        <div class="step-card-title">안정 판정 & 조치 분기</div>
        <div class="step-card-desc">Cpk ≥ 1.33 확정 승인<br>이상 감지 시 CAPA 분기</div>
      </div>

      <!-- Pin 5 -->
      <div class="pin-group" id="pin-4" style="left: 1060px; top: 85px; color: #ec4899;" onclick="selectStep(4)">
        <div class="pin-head" style="background: #ec4899;">
          <div class="pin-head-inner">🎯</div>
        </div>
        <div class="pin-stalk"></div>
        <div class="pin-base-dot" style="border-color: #ec4899; color: #ec4899;">5</div>
      </div>
      <div class="step-card" id="card-4" style="left: 1060px; top: 155px;" onclick="selectStep(4)">
        <div class="step-card-num" style="color: #ec4899;">Step 05</div>
        <div class="step-card-title">단일 HTML 보고서</div>
        <div class="step-card-desc">4K 시각화 · 조치이력 결합<br>Parquet 영구 아카이빙</div>
      </div>

      <!-- Dynamic Moving Vehicle Marker -->
      <div class="vehicle-marker" id="vehicle" style="left: 140px; top: 358px;">🚗</div>
    </div>

    <!-- Info Drawer -->
    <div class="drawer">
      <div>
        <h3 id="drawerTitle">Step 1. 원천 데이터 준비 및 로컬 세션 격리</h3>
        <p id="drawerDesc">
          측정자가 현장 계측기(RS-232, 엑셀, CSV)로부터 데이터를 로드합니다. 모든 데이터는 네트워크를 타지 않고 D:\StatProData 에 안전하게 격리 보관됩니다.
        </p>
        <ul class="checklist" id="drawerChecklist">
          <li class="check-item"><span class="check-icon">✓</span> 에어갭(Air-gapped) 환경 완전 보장</li>
          <li class="check-item"><span class="check-icon">✓</span> 인코딩 자동 감지 (UTF-8 / CP949 / EUC-KR)</li>
          <li class="check-item"><span class="check-icon">✓</span> Polars 고속 인메모리 파서 즉각 탑재</li>
        </ul>
      </div>
      <div class="meta-box">
        <div>
          <div class="meta-item-label">파이프라인 단계</div>
          <div class="meta-item-val" id="metaStep">1 / 5 (준비 단계)</div>
        </div>
        <div>
          <div class="meta-item-label">주요 통계 엔진</div>
          <div class="meta-item-val" id="metaEngine">FastAPI + Polars File Parser</div>
        </div>
        <div>
          <div class="meta-item-label">품질 기준</div>
          <div class="meta-item-val" id="metaRule">DESIGN.md 무결성 검증</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const roadSteps = [
      {
        x: 140, y: 358,
        title: "🚗 Step 1. 원천 데이터 준비 (CSV / 계측기 직접 수집)",
        sub: "공정 측정자가 원천 데이터를 입력하면 D:\\\\StatProData 로컬 스토리지에 세션이 생성됩니다.",
        drawerTitle: "Step 1. 원천 데이터 준비 및 로컬 세션 격리",
        drawerDesc: "측정자가 현장 계측기(RS-232, 엑셀, CSV)로부터 데이터를 로드합니다. 모든 데이터는 네트워크를 타지 않고 D:\\\\StatProData 에 안전하게 격리 보관됩니다.",
        checks: ["에어갭(Air-gapped) 환경 완전 보장", "인코딩 자동 감지 (UTF-8 / CP949 / EUC-KR)", "Polars 고속 인메모리 파서 즉각 탑재"],
        step: "1 / 5 (준비 단계)", engine: "FastAPI + Polars File Parser", rule: "DESIGN.md 무결성 검증"
      },
      {
        x: 360, y: 328,
        title: "⚙️ Step 2. 변수 및 규격 매핑 (결측치 0 대체 금지)",
        sub: "관리특성치(Y)와 군(Subgroup)을 매핑하며, 엔지니어링 규격(USL/LSL)을 명확히 분리 정의합니다.",
        drawerTitle: "Step 2. 변수 및 규격 매핑 (엄격한 결측 격리)",
        drawerDesc: "관리한계(UCL/LCL) 산출 기준과 제품 공학 규격(USL/LSL)을 엄격히 분리합니다. 통계 왜곡을 일으키는 '결측치 0 자동 대체'는 원천 차단됩니다.",
        checks: ["관리규격 vs 공학규격 엄격한 분리", "결측치 0 자동 대체 금지 (Null 격리 및 알림)", "가상화 그리드를 통한 실시간 데이터 프리뷰"],
        step: "2 / 5 (전처리/매핑)", engine: "Virtual Table Grid + Pydantic", rule: "결측치 보정 원천 금지"
      },
      {
        x: 600, y: 235,
        title: "📊 Step 3. 통계 연산 코어 (정규성 · 관리도 · Nelson 8 Rules)",
        sub: "Anderson-Darling 정규성 검정과 Shewhart 관리도, 8가지 Nelson 이상 룰을 전수 판정합니다.",
        drawerTitle: "Step 3. 통계 분석 코어 엔진 실시간 가동",
        drawerDesc: "군내 변동(Within) 기반 Cp/Cpk와 전체 변동(Overall) 기반 Pp/Ppk를 동시 산출하고, 1점 3시그마 이탈, 9점 연속 편향 등 Nelson 8대 룰을 실시간 감지합니다.",
        checks: ["Anderson-Darling (p >= 0.05) 정규성 검정", "Nelson 8 Rules 이상 패턴 실시간 마킹", "Gage R&R (%GRR, ndc) 측정시스템 신뢰도 검증"],
        step: "3 / 5 (통계 연산)", engine: "NumPy / SciPy Vectorized Core", rule: "ISO 21747 / AIAG SPC 표준"
      },
      {
        x: 820, y: 178,
        title: "⚖️ Step 4. 공정 판정 & 조치 분기 (확정 vs 협의 대기)",
        sub: "Cpk 1.33 이상은 표준 작업 유지 확정, 이상 룰 감지 시 CAPA 5Why 조치 대기로 분기됩니다.",
        drawerTitle: "Step 4. 공정 안정 판정 분기 (확정 vs 이상 감지)",
        drawerDesc: "통계 연산 결과에 따라 자동 분기됩니다. 안정 상태는 표준 승인 처리되고, 특수원인이 발견되면 경고 토스트와 함께 현장 엔지니어 조치 이력 입력을 요구합니다.",
        checks: ["정상: Cpk >= 1.33 관리상태 유지 승인", "이상: 관리한계 이탈 포인트 붉은 점 하이라이트", "5Why / CAPA 현장 원인분석 조치 기록 폼 활성화"],
        step: "4 / 5 (판정 및 조치)", engine: "SPC Decision Gate + Alarm Dispatcher", rule: "Fail-safe 조치 프로세스"
      },
      {
        x: 1060, y: 100,
        title: "🎯 Step 5. 단일 HTML 보고서 수령 및 Parquet 영구 아카이빙",
        sub: "외부 통신 없는 자립형 인터랙티브 보고서가 발행되고, 원본과 메타데이터가 압축 보존됩니다.",
        drawerTitle: "Step 5. 단일 HTML 리포트 및 로컬 아카이빙",
        drawerDesc: "Plotly 고해상도 벡터 차트와 분석 결과, 조치 이력이 결합된 단일 HTML 보고서를 생성합니다. 모든 세션은 Parquet 포맷으로 D:\StatProData 에 영구 저장됩니다.",
        checks: ["Self-contained 단일 파일 HTML 리포트 출력", "4K PNG / 벡터 SVG 차트 원클릭 내보내기", "Parquet 압축 스토리지로 로컬 이력 100% 영구 보존"],
        step: "5 / 5 (보고서/저장)", engine: "Jinja2 Report Generator + Parquet", rule: "단일 파일 자립성 보장"
      }
    ];

    let current = 0;
    let timer = null;
    let isPlaying = false;

    function updateView() {
      const data = roadSteps[current];
      // Update Vehicle
      const v = document.getElementById('vehicle');
      v.style.left = data.x + 'px';
      v.style.top = data.y + 'px';

      // Update pins and cards
      for (let i = 0; i < 5; i++) {
        const pin = document.getElementById('pin-' + i);
        const card = document.getElementById('card-' + i);
        if (i === current) {
          pin.classList.add('active');
          card.classList.add('active');
        } else {
          pin.classList.remove('active');
          card.classList.remove('active');
        }
      }

      // Update banners
      document.getElementById('bannerTitle').innerHTML = `<span>${data.title}</span>`;
      document.getElementById('bannerSub').textContent = data.sub;
      document.getElementById('stepCounter').textContent = `${current + 1} / 5`;

      // Update Drawer
      document.getElementById('drawerTitle').textContent = data.drawerTitle;
      document.getElementById('drawerDesc').textContent = data.drawerDesc;
      document.getElementById('metaStep').textContent = data.step;
      document.getElementById('metaEngine').textContent = data.engine;
      document.getElementById('metaRule').textContent = data.rule;

      const chkList = document.getElementById('drawerChecklist');
      chkList.innerHTML = '';
      data.checks.forEach(c => {
        const li = document.createElement('li');
        li.className = 'check-item';
        li.innerHTML = `<span class="check-icon">✓</span> ${c}`;
        chkList.appendChild(li);
      });
    }

    function selectStep(idx) {
      current = idx;
      updateView();
    }

    function nextStep() {
      current = (current + 1) % roadSteps.length;
      updateView();
    }

    function prevStep() {
      current = (current - 1 + roadSteps.length) % roadSteps.length;
      updateView();
    }

    function togglePlay() {
      if (isPlaying) {
        clearInterval(timer);
        isPlaying = false;
        document.getElementById('playIcon').textContent = '▷';
        document.getElementById('playText').textContent = '흐름 주행';
      } else {
        isPlaying = true;
        document.getElementById('playIcon').textContent = '❚❚';
        document.getElementById('playText').textContent = '일시 정지';
        timer = setInterval(() => {
          nextStep();
        }, 3000);
      }
    }

    function resetRoad() {
      if (isPlaying) togglePlay();
      current = 0;
      updateView();
    }

    document.getElementById('btnPlay').addEventListener('click', togglePlay);
    document.getElementById('btnNext').addEventListener('click', () => { if(isPlaying) togglePlay(); nextStep(); });
    document.getElementById('btnPrev').addEventListener('click', () => { if(isPlaying) togglePlay(); prevStep(); });
    document.getElementById('btnReset').addEventListener('click', resetRoad);
    document.getElementById('btnTheme').addEventListener('click', () => {
      document.body.classList.toggle('dark-mode');
      document.getElementById('btnTheme').textContent = document.body.classList.contains('dark-mode') ? '☀️' : '🌙';
    });

    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space') { e.preventDefault(); togglePlay(); }
      else if (e.code === 'ArrowRight') nextStep();
      else if (e.code === 'ArrowLeft') prevStep();
      else if (e.code === 'KeyR') resetRoad();
    });

    updateView();
  </script>
</body>
</html>
"""

HUB_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StatPro 다이아몬드 코어 & 방사형 허브 (Strategy Diamond Hub & Spoke)</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
  <style>
    :root {
      --bg-page: #f8fafc;
      --bg-card: #ffffff;
      --text-main: #0f172a;
      --text-sub: #64748b;
      --border-color: #e2e8f0;
      --hub-color: #2563eb;
      --card-shadow: 0 4px 6px -1px rgba(0,0,0,0.06);
    }
    body.dark-mode {
      --bg-page: #090d16;
      --bg-card: #1e293b;
      --text-main: #f8fafc;
      --text-sub: #94a3b8;
      --border-color: #334155;
      --card-shadow: 0 10px 15px -3px rgba(0,0,0,0.4);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg-page);
      color: var(--text-main);
      font-family: 'Pretendard', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: auto;
      transition: background 0.3s;
    }
    .container {
      max-width: 1240px;
      margin: 0 auto;
      width: 100%;
      padding: 24px;
      min-width: 1000px;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }
    .title-box h1 {
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .badge {
      font-size: 11px;
      background: #e0f2fe;
      color: #0369a1;
      padding: 3px 8px;
      border-radius: 4px;
      font-weight: 600;
    }
    .controls { display: flex; gap: 8px; align-items: center; }
    .btn {
      padding: 8px 14px;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      border-radius: 8px;
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }
    .btn:hover { background: #f1f5f9; }
    body.dark-mode .btn:hover { background: #334155; }
    .btn-primary { background: #2563eb; border-color: #2563eb; color: #fff; }
    .btn-primary:hover { background: #1d4ed8; }

    /* Hub Stage Layout */
    .hub-stage {
      position: relative;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 50px 30px;
      margin-bottom: 24px;
      display: grid;
      grid-template-columns: 360px 1fr;
      align-items: center;
      box-shadow: var(--card-shadow);
      min-height: 480px;
    }

    /* Central Diamond Hub */
    .hub-center-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      position: relative;
    }
    .diamond-card {
      width: 220px;
      height: 220px;
      background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
      border: 4px solid #2563eb;
      border-radius: 28px;
      transform: rotate(45deg);
      box-shadow: 0 15px 35px rgba(37,99,235,0.25);
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    body.dark-mode .diamond-card {
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
      border-color: #3b82f6;
    }
    .diamond-inner {
      transform: rotate(-45deg);
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      padding: 10px;
    }
    .diamond-icon {
      font-size: 36px;
      margin-bottom: 6px;
      animation: hubPulse 2s infinite ease-in-out;
    }
    @keyframes hubPulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.08); }
    }
    .diamond-title {
      font-size: 16px;
      font-weight: 800;
      color: var(--text-main);
    }
    .diamond-sub {
      font-size: 11px;
      color: var(--text-sub);
      margin-top: 4px;
      line-height: 1.3;
    }

    /* Radial Spokes & Pill Cards */
    .spokes-container {
      display: flex;
      flex-direction: column;
      gap: 16px;
      padding-left: 40px;
      position: relative;
    }
    .svg-spokes {
      position: absolute;
      top: 0;
      left: -80px;
      width: 120px;
      height: 100%;
      pointer-events: none;
    }
    .spoke-line {
      fill: none;
      stroke: #94a3b8;
      stroke-width: 2;
      stroke-dasharray: 4, 4;
      transition: all 0.3s;
    }
    .spoke-line.active {
      stroke: #2563eb;
      stroke-width: 3;
      stroke-dasharray: 6, 6;
      animation: spokeDash 1s linear infinite;
    }
    @keyframes spokeDash {
      from { stroke-dashoffset: 24; }
      to { stroke-dashoffset: 0; }
    }

    /* Pill Cards */
    .pill-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 9999px;
      padding: 10px 24px 10px 14px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.04);
      cursor: pointer;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      position: relative;
      user-select: none;
    }
    .pill-card:hover {
      transform: translateX(6px);
      border-color: #94a3b8;
    }
    .pill-card.active {
      transform: translateX(10px);
      box-shadow: 0 8px 20px -4px rgba(37,99,235,0.25);
      border-width: 2px;
    }

    .pill-badge {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 16px;
      color: #fff;
      flex-shrink: 0;
      box-shadow: 0 3px 6px rgba(0,0,0,0.15);
    }
    .pill-info {
      flex: 1;
    }
    .pill-title {
      font-size: 14px;
      font-weight: 700;
      color: var(--text-main);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .pill-desc {
      font-size: 12px;
      color: var(--text-sub);
      margin-top: 2px;
    }

    /* Card Specific Colors */
    .card-1.active { border-color: #eab308; background: #fefce8; }
    .card-2.active { border-color: #10b981; background: #f0fdf4; }
    .card-3.active { border-color: #3b82f6; background: #eff6ff; }
    .card-4.active { border-color: #8b5cf6; background: #f5f3ff; }
    .card-5.active { border-color: #ec4899; background: #fdf2f8; }

    body.dark-mode .card-1.active { background: #422006; }
    body.dark-mode .card-2.active { background: #064e3b; }
    body.dark-mode .card-3.active { background: #1e3a5f; }
    body.dark-mode .card-4.active { background: #2e1065; }
    body.dark-mode .card-5.active { background: #500724; }

    /* Bottom Info Drawer */
    .drawer {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px 24px;
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 24px;
      box-shadow: var(--card-shadow);
    }
    .drawer h3 { font-size: 16px; font-weight: 800; margin-bottom: 8px; }
    .drawer p { font-size: 13px; color: var(--text-sub); line-height: 1.6; margin-bottom: 12px; }
    .checklist { list-style: none; display: flex; flex-direction: column; gap: 6px; font-size: 12px; }
    .check-item { display: flex; align-items: center; gap: 8px; }
    .check-icon { color: #10b981; font-weight: bold; }
    .meta-box {
      border-left: 1px solid var(--border-color);
      padding-left: 20px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 12px;
      font-size: 12px;
    }
    .meta-item-label { color: var(--text-sub); font-size: 11px; text-transform: uppercase; font-weight: 600; }
    .meta-item-val { font-size: 15px; font-weight: 700; color: var(--text-main); }
  </style>
</head>
<body>

  <div class="container">
    <header class="header">
      <div class="title-box">
        <h1>StatPro 다이아몬드 코어 &amp; 방사형 허브</h1>
        <span class="badge">STRATEGY DIAMOND HUB THEME</span>
      </div>
      <div class="controls">
        <button class="btn" id="btnPrev">&lt;</button>
        <button class="btn btn-primary" id="btnPlay">
          <span id="playIcon">▷</span> <span id="playText">허브 순환</span>
        </button>
        <button class="btn" id="btnNext">&gt;</button>
        <button class="btn" id="btnReset">↺</button>
        <button class="btn" id="btnTheme">🌙</button>
      </div>
    </header>

    <!-- Hub Stage -->
    <div class="hub-stage">
      <!-- Left: Central Diamond Core Hub -->
      <div class="hub-center-container">
        <div class="diamond-card" id="centerDiamond">
          <div class="diamond-inner">
            <div class="diamond-icon">💎</div>
            <div class="diamond-title">StatPro Core</div>
            <div class="diamond-sub">Local-First<br>Engine &amp; Storage</div>
          </div>
        </div>
      </div>

      <!-- Right: Spoke Pill Cards -->
      <div class="spokes-container">
        <svg class="svg-spokes" viewBox="0 0 120 380">
          <path id="spoke-0" class="spoke-line active" d="M 0 190 C 40 190, 40 30, 120 30" />
          <path id="spoke-1" class="spoke-line" d="M 0 190 C 40 190, 40 100, 120 100" />
          <path id="spoke-2" class="spoke-line" d="M 0 190 L 120 190" />
          <path id="spoke-3" class="spoke-line" d="M 0 190 C 40 190, 40 280, 120 280" />
          <path id="spoke-4" class="spoke-line" d="M 0 190 C 40 190, 40 350, 120 350" />
        </svg>

        <div class="pill-card card-1 active" id="card-0" onclick="selectStep(0)">
          <div class="pill-badge" style="background: #eab308;">01</div>
          <div class="pill-info">
            <div class="pill-title">
              <span>원천 데이터 수집 &amp; 로컬 격리</span>
              <span style="font-size: 11px; color: #eab308;">INPUT</span>
            </div>
            <div class="pill-desc">CSV · XLSX 계측기 데이터 로드 및 D:\StatProData 에어갭 세션 초기화</div>
          </div>
        </div>

        <div class="pill-card card-2" id="card-1" onclick="selectStep(1)">
          <div class="pill-badge" style="background: #10b981;">02</div>
          <div class="pill-info">
            <div class="pill-title">
              <span>변수 매핑 &amp; 결측 무결성 검증</span>
              <span style="font-size: 11px; color: #10b981;">VALIDATION</span>
            </div>
            <div class="pill-desc">결측치 0 대체 원천 금지, 공학규격(USL/LSL) 분리 입력 및 그리드 프리뷰</div>
          </div>
        </div>

        <div class="pill-card card-3" id="card-2" onclick="selectStep(2)">
          <div class="pill-badge" style="background: #3b82f6;">03</div>
          <div class="pill-info">
            <div class="pill-title">
              <span>통계 연산 코어 &amp; Nelson 8 Rules</span>
              <span style="font-size: 11px; color: #3b82f6;">COMPUTE</span>
            </div>
            <div class="pill-desc">Anderson-Darling 정규성, Gage R&amp;R, 8대 Nelson 이상 패턴 실시간 판정</div>
          </div>
        </div>

        <div class="pill-card card-4" id="card-3" onclick="selectStep(3)">
          <div class="pill-badge" style="background: #8b5cf6;">04</div>
          <div class="pill-info">
            <div class="pill-title">
              <span>공정 안정 판정 분기 (확정 vs 조치)</span>
              <span style="font-size: 11px; color: #8b5cf6;">DECISION</span>
            </div>
            <div class="pill-desc">Cpk ≥ 1.33 정상 확정 vs 이상 감지 시 CAPA 5Why 조치 대기 분기 배분</div>
          </div>
        </div>

        <div class="pill-card card-5" id="card-4" onclick="selectStep(4)">
          <div class="pill-badge" style="background: #ec4899;">05</div>
          <div class="pill-info">
            <div class="pill-title">
              <span>품질 보고서 출력 &amp; 영구 아카이빙</span>
              <span style="font-size: 11px; color: #ec4899;">REPORT</span>
            </div>
            <div class="pill-desc">단일 HTML 리포트 발행, 4K 벡터 차트 내보내기, Parquet 영구 보존</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Info Drawer -->
    <div class="drawer">
      <div>
        <h3 id="drawerTitle">Step 1. 원천 데이터 수집 &amp; 로컬 격리 세션</h3>
        <p id="drawerDesc">
          현장 계측기나 파일로부터 데이터를 불러와 로컬 PC 내부(D:\StatProData)에 안전하게 저장합니다.
        </p>
        <ul class="checklist" id="drawerChecklist">
          <li class="check-item"><span class="check-icon">✓</span> 에어갭(Air-gapped) 환경 완전 보장</li>
          <li class="check-item"><span class="check-icon">✓</span> 인코딩 자동 보정 (UTF-8, CP949, EUC-KR)</li>
          <li class="check-item"><span class="check-icon">✓</span> Polars 고속 인메모리 파서 즉각 탑재</li>
        </ul>
      </div>
      <div class="meta-box">
        <div>
          <div class="meta-item-label">선택 단계</div>
          <div class="meta-item-val" id="metaStep">Step 1 / 5</div>
        </div>
        <div>
          <div class="meta-item-label">아키텍처 레이어</div>
          <div class="meta-item-val" id="metaEngine">FastAPI Local Core Server</div>
        </div>
        <div>
          <div class="meta-item-label">설계 준수</div>
          <div class="meta-item-val" id="metaRule">DESIGN.md 1단계 로드</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const hubSteps = [
      {
        title: "Step 1. 원천 데이터 수집 & 로컬 격리 세션",
        desc: "현장 계측기나 파일로부터 데이터를 불러와 로컬 PC 내부(D:\\\\StatProData)에 안전하게 저장합니다.",
        checks: ["에어갭(Air-gapped) 환경 완전 보장", "인코딩 자동 보정 (UTF-8, CP949, EUC-KR)", "Polars 고속 인메모리 파서 즉각 탑재"],
        step: "Step 1 / 5", engine: "FastAPI Local Core Server", rule: "DESIGN.md 1단계 로드"
      },
      {
        title: "Step 2. 변수 매핑 & 결측 무결성 검증",
        desc: "관리특성치(Y)와 군(Subgroup)을 매핑하며, 엔지니어링 규격(USL/LSL)을 명확히 분리 정의합니다. 결측치 0 자동 대체는 엄격히 금지됩니다.",
        checks: ["관리규격 vs 공학규격 엄격한 분리", "결측치 0 자동 대체 금지 (Null 격리 및 알림)", "가상화 그리드를 통한 실시간 데이터 프리뷰"],
        step: "Step 2 / 5", engine: "Virtual Table Grid + Pydantic", rule: "결측치 보정 원천 금지"
      },
      {
        title: "Step 3. 통계 연산 코어 & Nelson 8 Rules",
        desc: "Anderson-Darling 정규성 검정과 Shewhart 관리도, 8가지 Nelson 이상 룰을 전수 판정합니다.",
        checks: ["Anderson-Darling (p >= 0.05) 정규성 검정", "Nelson 8 Rules 이상 패턴 실시간 마킹", "Gage R&R (%GRR, ndc) 측정시스템 신뢰도 검증"],
        step: "Step 3 / 5", engine: "NumPy / SciPy Vectorized Core", rule: "ISO 21747 / AIAG SPC 표준"
      },
      {
        title: "Step 4. 공정 판정 & 조치 분기 (확정 vs 협의 대기)",
        desc: "Cpk 1.33 이상은 표준 작업 유지 확정, 이상 룰 감지 시 CAPA 5Why 조치 대기로 분기됩니다.",
        checks: ["정상: Cpk >= 1.33 관리상태 유지 승인", "이상: 관리한계 이탈 포인트 붉은 점 하이라이트", "5Why / CAPA 현장 원인분석 조치 기록 폼 활성화"],
        step: "Step 4 / 5", engine: "SPC Decision Gate + Alarm Dispatcher", rule: "Fail-safe 조치 프로세스"
      },
      {
        title: "Step 5. 품질 보고서 출력 & 영구 아카이빙",
        desc: "Plotly 고해상도 벡터 차트와 분석 결과, 조치 이력이 결합된 단일 HTML 보고서를 생성합니다.",
        checks: ["Self-contained 단일 파일 HTML 리포트 출력", "4K PNG / 벡터 SVG 차트 원클릭 내보내기", "Parquet 압축 스토리지로 로컬 이력 100% 영구 보존"],
        step: "Step 5 / 5", engine: "Jinja2 Report Generator + Parquet", rule: "단일 파일 자립성 보장"
      }
    ];

    let current = 0;
    let timer = null;
    let isPlaying = false;

    function updateView() {
      const data = hubSteps[current];

      for (let i = 0; i < 5; i++) {
        const card = document.getElementById('card-' + i);
        const spoke = document.getElementById('spoke-' + i);
        if (i === current) {
          card.classList.add('active');
          spoke.classList.add('active');
        } else {
          card.classList.remove('active');
          spoke.classList.remove('active');
        }
      }

      document.getElementById('drawerTitle').textContent = data.title;
      document.getElementById('drawerDesc').textContent = data.desc;
      document.getElementById('metaStep').textContent = data.step;
      document.getElementById('metaEngine').textContent = data.engine;
      document.getElementById('metaRule').textContent = data.rule;

      const chkList = document.getElementById('drawerChecklist');
      chkList.innerHTML = '';
      data.checks.forEach(c => {
        const li = document.createElement('li');
        li.className = 'check-item';
        li.innerHTML = `<span class="check-icon">✓</span> ${c}`;
        chkList.appendChild(li);
      });
    }

    function selectStep(idx) {
      current = idx;
      updateView();
    }

    function nextStep() {
      current = (current + 1) % hubSteps.length;
      updateView();
    }

    function prevStep() {
      current = (current - 1 + hubSteps.length) % hubSteps.length;
      updateView();
    }

    function togglePlay() {
      if (isPlaying) {
        clearInterval(timer);
        isPlaying = false;
        document.getElementById('playIcon').textContent = '▷';
        document.getElementById('playText').textContent = '허브 순환';
      } else {
        isPlaying = true;
        document.getElementById('playIcon').textContent = '❚❚';
        document.getElementById('playText').textContent = '일시 정지';
        timer = setInterval(nextStep, 2800);
      }
    }

    function resetHub() {
      if (isPlaying) togglePlay();
      current = 0;
      updateView();
    }

    document.getElementById('btnPlay').addEventListener('click', togglePlay);
    document.getElementById('btnNext').addEventListener('click', () => { if(isPlaying) togglePlay(); nextStep(); });
    document.getElementById('btnPrev').addEventListener('click', () => { if(isPlaying) togglePlay(); prevStep(); });
    document.getElementById('btnReset').addEventListener('click', resetHub);
    document.getElementById('btnTheme').addEventListener('click', () => {
      document.body.classList.toggle('dark-mode');
      document.getElementById('btnTheme').textContent = document.body.classList.contains('dark-mode') ? '☀️' : '🌙';
    });

    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space') { e.preventDefault(); togglePlay(); }
      else if (e.code === 'ArrowRight') nextStep();
      else if (e.code === 'ArrowLeft') prevStep();
      else if (e.code === 'KeyR') resetHub();
    });

    updateView();
  </script>
</body>
</html>
"""

INTERLOCK_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StatPro 인터로킹 퍼즐 카드 체인 (Interlocking Process Chain)</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
  <style>
    :root {
      --bg-page: #f8fafc;
      --bg-card: #ffffff;
      --text-main: #0f172a;
      --text-sub: #64748b;
      --border-color: #cbd5e1;
      --card-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    body.dark-mode {
      --bg-page: #090d16;
      --bg-card: #1e293b;
      --text-main: #f8fafc;
      --text-sub: #94a3b8;
      --border-color: #334155;
      --card-shadow: 0 10px 15px -3px rgba(0,0,0,0.4);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg-page);
      color: var(--text-main);
      font-family: 'Pretendard', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: auto;
      transition: background 0.3s;
    }
    .container {
      max-width: 1240px;
      margin: 0 auto;
      width: 100%;
      padding: 24px;
      min-width: 1050px;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
    }
    .title-box h1 {
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .badge {
      font-size: 11px;
      background: #e0f2fe;
      color: #0369a1;
      padding: 3px 8px;
      border-radius: 4px;
      font-weight: 600;
    }
    .controls { display: flex; gap: 8px; align-items: center; }
    .btn {
      padding: 8px 14px;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      border-radius: 8px;
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }
    .btn:hover { background: #f1f5f9; }
    body.dark-mode .btn:hover { background: #334155; }
    .btn-primary { background: #2563eb; border-color: #2563eb; color: #fff; }
    .btn-primary:hover { background: #1d4ed8; }

    /* Interlocking Chain Stage */
    .interlock-stage {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 40px 24px;
      margin-bottom: 24px;
      box-shadow: var(--card-shadow);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      position: relative;
    }

    /* Interlocking Puzzle Card */
    .puzzle-card {
      flex: 1;
      background: var(--bg-card);
      border: 2px solid var(--border-color);
      border-radius: 16px;
      padding: 24px 18px;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      cursor: pointer;
      position: relative;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 2px 4px rgba(0,0,0,0.04);
      min-height: 240px;
    }
    .puzzle-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    .puzzle-card.active {
      transform: translateY(-8px) scale(1.03);
      box-shadow: 0 15px 25px -5px rgba(37,99,235,0.25);
      border-color: #2563eb;
      background: #f8faff;
    }
    body.dark-mode .puzzle-card.active {
      background: #1e3a5f;
    }

    /* Notch Connector between cards */
    .puzzle-card::after {
      content: "▶";
      position: absolute;
      right: -15px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 14px;
      color: #94a3b8;
      z-index: 5;
    }
    .puzzle-card:last-child::after {
      display: none;
    }

    .card-badge-circle {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-weight: 800;
      font-size: 18px;
      margin-bottom: 14px;
      box-shadow: 0 4px 8px rgba(0,0,0,0.15);
      transition: all 0.3s;
    }
    .puzzle-card.active .card-badge-circle {
      transform: scale(1.1);
    }

    .card-icon {
      font-size: 24px;
      margin-bottom: 8px;
    }
    .card-title {
      font-size: 14px;
      font-weight: 800;
      color: var(--text-main);
      margin-bottom: 6px;
    }
    .card-desc {
      font-size: 11px;
      color: var(--text-sub);
      line-height: 1.4;
    }

    /* Theme colors */
    .color-1 { background: #0284c7; }
    .color-2 { background: #0d9488; }
    .color-3 { background: #16a34a; }
    .color-4 { background: #eab308; }
    .color-5 { background: #ea580c; }

    /* Bottom Info Drawer */
    .drawer {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px 24px;
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 24px;
      box-shadow: var(--card-shadow);
    }
    .drawer h3 { font-size: 16px; font-weight: 800; margin-bottom: 8px; }
    .drawer p { font-size: 13px; color: var(--text-sub); line-height: 1.6; margin-bottom: 12px; }
    .checklist { list-style: none; display: flex; flex-direction: column; gap: 6px; font-size: 12px; }
    .check-item { display: flex; align-items: center; gap: 8px; }
    .check-icon { color: #10b981; font-weight: bold; }
    .meta-box {
      border-left: 1px solid var(--border-color);
      padding-left: 20px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 12px;
      font-size: 12px;
    }
    .meta-item-label { color: var(--text-sub); font-size: 11px; text-transform: uppercase; font-weight: 600; }
    .meta-item-val { font-size: 15px; font-weight: 700; color: var(--text-main); }
  </style>
</head>
<body>

  <div class="container">
    <header class="header">
      <div class="title-box">
        <h1>StatPro 인터로킹 퍼즐 카드 체인</h1>
        <span class="badge">INTERLOCKING PUZZLE CHAIN</span>
      </div>
      <div class="controls">
        <button class="btn" id="btnPrev">&lt;</button>
        <button class="btn btn-primary" id="btnPlay">
          <span id="playIcon">▷</span> <span id="playText">체인 재생</span>
        </button>
        <button class="btn" id="btnNext">&gt;</button>
        <button class="btn" id="btnReset">↺</button>
        <button class="btn" id="btnTheme">🌙</button>
      </div>
    </header>

    <!-- Interlocking Stage -->
    <div class="interlock-stage">
      <div class="puzzle-card active" id="card-0" onclick="selectStep(0)">
        <div class="card-badge-circle color-1">01</div>
        <div class="card-icon">📂</div>
        <div class="card-title">원천 데이터 로드</div>
        <div class="card-desc">CSV · XLSX 계측 파일<br>D:\StatProData 에어갭 세션</div>
      </div>

      <div class="puzzle-card" id="card-1" onclick="selectStep(1)">
        <div class="card-badge-circle color-2">02</div>
        <div class="card-icon">🔍</div>
        <div class="card-title">변수 &amp; 규격 매핑</div>
        <div class="card-desc">결측치 0 대체 원천 금지<br>USL/LSL 공학규격 분리</div>
      </div>

      <div class="puzzle-card" id="card-2" onclick="selectStep(2)">
        <div class="card-badge-circle color-3">03</div>
        <div class="card-icon">⚙️</div>
        <div class="card-title">통계 연산 코어</div>
        <div class="card-desc">정규성 AD검정 · Gage R&amp;R<br>Nelson 8 Rules 판정</div>
      </div>

      <div class="puzzle-card" id="card-3" onclick="selectStep(3)">
        <div class="card-badge-circle color-4">04</div>
        <div class="card-icon">⚖️</div>
        <div class="card-title">안정 판정 분기</div>
        <div class="card-desc">Cpk ≥ 1.33 정상 확정<br>이상 감지 시 CAPA 분기</div>
      </div>

      <div class="puzzle-card" id="card-4" onclick="selectStep(4)">
        <div class="card-badge-circle color-5">05</div>
        <div class="card-icon">📋</div>
        <div class="card-title">품질 보고서 출력</div>
        <div class="card-desc">단일 HTML 리포트 발행<br>Parquet 영구 아카이빙</div>
      </div>
    </div>

    <!-- Info Drawer -->
    <div class="drawer">
      <div>
        <h3 id="drawerTitle">Step 1. 원천 데이터 준비 및 로컬 세션 격리</h3>
        <p id="drawerDesc">
          측정자가 현장 계측기(RS-232, 엑셀, CSV)로부터 데이터를 로드합니다. 모든 데이터는 네트워크를 타지 않고 D:\StatProData 에 안전하게 격리 보관됩니다.
        </p>
        <ul class="checklist" id="drawerChecklist">
          <li class="check-item"><span class="check-icon">✓</span> 에어갭(Air-gapped) 환경 완전 보장</li>
          <li class="check-item"><span class="check-icon">✓</span> 인코딩 자동 보정 (UTF-8, CP949, EUC-KR)</li>
          <li class="check-item"><span class="check-icon">✓</span> Polars 고속 인메모리 파서 즉각 탑재</li>
        </ul>
      </div>
      <div class="meta-box">
        <div>
          <div class="meta-item-label">파이프라인 단계</div>
          <div class="meta-item-val" id="metaStep">Step 1 / 5</div>
        </div>
        <div>
          <div class="meta-item-label">아키텍처 엔진</div>
          <div class="meta-item-val" id="metaEngine">FastAPI Local Core Server</div>
        </div>
        <div>
          <div class="meta-item-label">설계 준수</div>
          <div class="meta-item-val" id="metaRule">DESIGN.md 5-Step 체인</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const interlockSteps = [
      {
        title: "Step 1. 원천 데이터 준비 및 로컬 세션 격리",
        desc: "측정자가 현장 계측기(RS-232, 엑셀, CSV)로부터 데이터를 로드합니다. 모든 데이터는 네트워크를 타지 않고 D:\\\\StatProData 에 안전하게 격리 보관됩니다.",
        checks: ["에어갭(Air-gapped) 환경 완전 보장", "인코딩 자동 보정 (UTF-8, CP949, EUC-KR)", "Polars 고속 인메모리 파서 즉각 탑재"],
        step: "Step 1 / 5", engine: "FastAPI Local Core Server", rule: "DESIGN.md 1단계 로드"
      },
      {
        title: "Step 2. 변수 매핑 & 결측 무결성 검증",
        desc: "관리특성치(Y)와 군(Subgroup)을 매핑하며, 엔지니어링 규격(USL/LSL)을 명확히 분리 정의합니다. 결측치 0 자동 대체는 엄격히 금지됩니다.",
        checks: ["관리규격 vs 공학규격 엄격한 분리", "결측치 0 자동 대체 금지 (Null 격리 및 알림)", "가상화 그리드를 통한 실시간 데이터 프리뷰"],
        step: "Step 2 / 5", engine: "Virtual Table Grid + Pydantic", rule: "결측치 보정 원천 금지"
      },
      {
        title: "Step 3. 통계 연산 코어 & Nelson 8 Rules",
        desc: "Anderson-Darling 정규성 검정과 Shewhart 관리도, 8가지 Nelson 이상 룰을 전수 판정합니다.",
        checks: ["Anderson-Darling (p >= 0.05) 정규성 검정", "Nelson 8 Rules 이상 패턴 실시간 마킹", "Gage R&R (%GRR, ndc) 측정시스템 신뢰도 검증"],
        step: "Step 3 / 5", engine: "NumPy / SciPy Vectorized Core", rule: "ISO 21747 / AIAG SPC 표준"
      },
      {
        title: "Step 4. 공정 판정 & 조치 분기 (확정 vs 협의 대기)",
        desc: "Cpk 1.33 이상은 표준 작업 유지 확정, 이상 룰 감지 시 CAPA 5Why 조치 대기로 분기됩니다.",
        checks: ["정상: Cpk >= 1.33 관리상태 유지 승인", "이상: 관리한계 이탈 포인트 붉은 점 하이라이트", "5Why / CAPA 현장 원인분석 조치 기록 폼 활성화"],
        step: "Step 4 / 5", engine: "SPC Decision Gate + Alarm Dispatcher", rule: "Fail-safe 조치 프로세스"
      },
      {
        title: "Step 5. 품질 보고서 출력 & 영구 아카이빙",
        desc: "Plotly 고해상도 벡터 차트와 분석 결과, 조치 이력이 결합된 단일 HTML 보고서를 생성합니다.",
        checks: ["Self-contained 단일 파일 HTML 리포트 출력", "4K PNG / 벡터 SVG 차트 원클릭 내보내기", "Parquet 압축 스토리지로 로컬 이력 100% 영구 보존"],
        step: "Step 5 / 5", engine: "Jinja2 Report Generator + Parquet", rule: "단일 파일 자립성 보장"
      }
    ];

    let current = 0;
    let timer = null;
    let isPlaying = false;

    function updateView() {
      const data = interlockSteps[current];

      for (let i = 0; i < 5; i++) {
        const card = document.getElementById('card-' + i);
        if (i === current) card.classList.add('active');
        else card.classList.remove('active');
      }

      document.getElementById('drawerTitle').textContent = data.title;
      document.getElementById('drawerDesc').textContent = data.desc;
      document.getElementById('metaStep').textContent = data.step;
      document.getElementById('metaEngine').textContent = data.engine;
      document.getElementById('metaRule').textContent = data.rule;

      const chkList = document.getElementById('drawerChecklist');
      chkList.innerHTML = '';
      data.checks.forEach(c => {
        const li = document.createElement('li');
        li.className = 'check-item';
        li.innerHTML = `<span class="check-icon">✓</span> ${c}`;
        chkList.appendChild(li);
      });
    }

    function selectStep(idx) {
      current = idx;
      updateView();
    }

    function nextStep() {
      current = (current + 1) % interlockSteps.length;
      updateView();
    }

    function prevStep() {
      current = (current - 1 + interlockSteps.length) % interlockSteps.length;
      updateView();
    }

    function togglePlay() {
      if (isPlaying) {
        clearInterval(timer);
        isPlaying = false;
        document.getElementById('playIcon').textContent = '▷';
        document.getElementById('playText').textContent = '체인 재생';
      } else {
        isPlaying = true;
        document.getElementById('playIcon').textContent = '❚❚';
        document.getElementById('playText').textContent = '일시 정지';
        timer = setInterval(nextStep, 2800);
      }
    }

    function resetInterlock() {
      if (isPlaying) togglePlay();
      current = 0;
      updateView();
    }

    document.getElementById('btnPlay').addEventListener('click', togglePlay);
    document.getElementById('btnNext').addEventListener('click', () => { if(isPlaying) togglePlay(); nextStep(); });
    document.getElementById('btnPrev').addEventListener('click', () => { if(isPlaying) togglePlay(); prevStep(); });
    document.getElementById('btnReset').addEventListener('click', resetInterlock);
    document.getElementById('btnTheme').addEventListener('click', () => {
      document.body.classList.toggle('dark-mode');
      document.getElementById('btnTheme').textContent = document.body.classList.contains('dark-mode') ? '☀️' : '🌙';
    });

    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space') { e.preventDefault(); togglePlay(); }
      else if (e.code === 'ArrowRight') nextStep();
      else if (e.code === 'ArrowLeft') prevStep();
      else if (e.code === 'KeyR') resetInterlock();
    });

    updateView();
  </script>
</body>
</html>
"""

UPGRADED_STUDIO_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Motion Diagram Studio - 인포그래픽 & 다이어그램 디자인 스위처</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Pretendard', sans-serif;
      background-color: #0f172a;
      color: #f8fafc;
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    
    .studio-bar {
      height: 60px;
      background-color: #1e293b;
      border-bottom: 1px solid #334155;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      z-index: 100;
      flex-shrink: 0;
    }
    
    .studio-brand {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .studio-logo {
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, #3b82f6, #8b5cf6);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 16px;
      box-shadow: 0 2px 6px rgba(59,130,246,0.3);
    }
    .studio-title {
      font-size: 15px;
      font-weight: 800;
      letter-spacing: -0.01em;
    }
    .studio-subtitle {
      font-size: 10px;
      color: #94a3b8;
    }
    
    /* Theme Switcher Pills */
    .theme-selector-group {
      display: flex;
      align-items: center;
      background-color: #0f172a;
      border: 1px solid #334155;
      border-radius: 10px;
      padding: 4px;
      gap: 3px;
      overflow-x: auto;
      max-width: 820px;
    }
    
    .theme-btn {
      padding: 6px 11px;
      border-radius: 6px;
      border: none;
      background: transparent;
      color: #94a3b8;
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 5px;
      transition: all 0.2s ease;
      font-family: 'Pretendard', sans-serif;
      white-space: nowrap;
    }
    
    .theme-btn:hover {
      color: #f8fafc;
      background-color: rgba(255, 255, 255, 0.05);
    }
    
    .theme-btn.active {
      background: #2563eb;
      color: #ffffff;
      box-shadow: 0 2px 5px rgba(37, 99, 235, 0.4);
    }
    
    .actions-group {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .btn-action {
      padding: 6px 12px;
      border-radius: 6px;
      border: 1px solid #475569;
      background: #1e293b;
      color: #cbd5e1;
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 5px;
      transition: all 0.2s;
    }
    .btn-action:hover {
      background: #334155;
      color: #ffffff;
    }
    
    .viewport-container {
      flex: 1;
      width: 100%;
      height: calc(100vh - 60px);
      position: relative;
      background-color: #0b1120;
    }
    
    iframe.preview-frame {
      width: 100%;
      height: 100%;
      border: none;
      display: block;
    }
  </style>
</head>
<body>

  <header class="studio-bar">
    <div class="studio-brand">
      <div class="studio-logo">✦</div>
      <div>
        <div class="studio-title">Motion Diagram Studio</div>
        <div class="studio-subtitle">7대 인포그래픽 &amp; 다이어그램 테마 선택기</div>
      </div>
    </div>

    <!-- Theme Switcher -->
    <div class="theme-selector-group">
      <button class="theme-btn active" data-src="statpro_roadmap_workflow.html" onclick="switchTheme(this)">
        🛣️ 아스팔트 로드맵
      </button>
      <button class="theme-btn" data-src="statpro_hub_workflow.html" onclick="switchTheme(this)">
        💎 다이아몬드 허브
      </button>
      <button class="theme-btn" data-src="statpro_interlock_workflow.html" onclick="switchTheme(this)">
        🧩 인터로킹 퍼즐 체인
      </button>
      <button class="theme-btn" data-src="statpro_swimlane_workflow.html" onclick="switchTheme(this)">
        🏢 3단 스윔레인
      </button>
      <button class="theme-btn" data-src="statpro_sketch_motion_workflow.html" onclick="switchTheme(this)">
        📝 손글씨 줄노트 스케치
      </button>
      <button class="theme-btn" data-src="statpro_motion_workflow.html" onclick="switchTheme(this)">
        💻 모던 UI 대시보드
      </button>
      <button class="theme-btn" data-src="docs_motion_workflow.html" onclick="switchTheme(this)">
        📖 기술 문서 파이프라인
      </button>
    </div>

    <div class="actions-group">
      <button class="btn-action" onclick="openNewTab()">
        <span>↗ 새 탭</span>
      </button>
      <button class="btn-action" onclick="reloadFrame()">
        <span>↺ 새로고침</span>
      </button>
    </div>
  </header>

  <main class="viewport-container">
    <iframe id="previewFrame" class="preview-frame" src="statpro_roadmap_workflow.html"></iframe>
  </main>

  <script>
    let currentSrc = "statpro_roadmap_workflow.html";

    function switchTheme(btn) {
      document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentSrc = btn.getAttribute('data-src');
      document.getElementById('previewFrame').src = currentSrc;
    }

    function openNewTab() {
      window.open(currentSrc, '_blank');
    }

    function reloadFrame() {
      const frame = document.getElementById('previewFrame');
      frame.src = frame.src;
    }
  </script>
</body>
</html>
"""

def generate_bat(name, title, html_name):
    bat_content = f"""@echo off
chcp 949 >nul
setlocal
title StatPro {title}
set "HTML_FILE=%~dp0{html_name}"
if not exist "%HTML_FILE%" (
    echo [ERROR] HTML file not found: %HTML_FILE%
    pause
    exit /b 1
)
echo ========================================================
echo   StatPro {title} Launcher
echo ========================================================
echo.
echo Opening {title} in Google Chrome...
start "" chrome "%HTML_FILE%"
if errorlevel 1 (
    echo Chrome not found in PATH, opening with default browser...
    start "" "%HTML_FILE%"
)
echo Done.
"""
    path = os.path.join("diagrams", name)
    with open(path, "wb") as f:
        f.write(bat_content.replace('\r\n', '\n').replace('\n', '\r\n').encode('cp949'))
    print(f"Generated Launcher: {path}")

def main():
    os.makedirs("diagrams", exist_ok=True)
    artifact_dir = r"C:\Users\0208m\.gemini\antigravity\brain\3b3a945f-274b-405e-9963-58792169202a"
    os.makedirs(artifact_dir, exist_ok=True)

    files = {
        "statpro_roadmap_workflow.html": ROADMAP_HTML,
        "statpro_hub_workflow.html": HUB_HTML,
        "statpro_interlock_workflow.html": INTERLOCK_HTML,
        "motion_diagram_studio.html": UPGRADED_STUDIO_HTML
    }

    for fname, content in files.items():
        local_path = os.path.join("diagrams", fname)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated: {local_path}")

        # Artifact copy
        art_path = os.path.join(artifact_dir, fname)
        with open(art_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated artifact: {art_path}")

    # Launchers
    generate_bat("open_roadmap_workflow.bat", "Roadmap Highway Workflow", "statpro_roadmap_workflow.html")
    generate_bat("open_hub_workflow.bat", "Strategy Diamond Hub Workflow", "statpro_hub_workflow.html")
    generate_bat("open_interlock_workflow.bat", "Interlocking Chain Workflow", "statpro_interlock_workflow.html")
    generate_bat("open_motion_studio.bat", "Motion Diagram Studio (7 Themes)", "motion_diagram_studio.html")

if __name__ == "__main__":
    main()
