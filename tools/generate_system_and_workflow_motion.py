"""StatPro System Architecture & Business Workflow Motion Graphic Generator.

Grounded in:
  - README.md & DESIGN.md
  - docs/01.StatPro_SRS.md ~ docs/10.StatPro_AI_Copilot_Rule_Catalog.md
  - Python Core (src/statpro) & React Web (web/src)

Features:
  - Dual View Switcher: 1) System Architecture Topology vs 2) End-to-End
  Business Workflow
  - Live Self-Explaining Narration Engine (Play/Pause, Typewriter, Step-by-Step
  Highlight)
  - Animated SVG Connectors with moving signals and neon dashes
  - Responsive Theme Toggle (Dark / Light)
  - Detailed Information Drawer with verified codebase contracts and file
  locations
"""

import json
import os

HTML_CONTENT = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StatPro 전체 시스템 구성도 및 업무플로우 모션 가이드</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
  <style>
    :root {
      --bg-page: #0f172a;
      --bg-surface: #1e293b;
      --bg-card: #1e293b;
      --bg-card-hover: #27354f;
      --text-main: #f8fafc;
      --text-sub: #94a3b8;
      --border-color: #334155;
      --primary-blue: #3b82f6;
      --primary-hover: #2563eb;
      --neon-cyan: #06b6d4;
      --neon-green: #10b981;
      --neon-purple: #a855f7;
      --neon-amber: #f59e0b;
      --neon-pink: #ec4899;
      --card-shadow: 0 4px 20px -2px rgba(0,0,0,0.5);
      --font-body: 'Pretendard', sans-serif;
    }

    body.light-mode {
      --bg-page: #f8fafc;
      --bg-surface: #ffffff;
      --bg-card: #ffffff;
      --bg-card-hover: #f1f5f9;
      --text-main: #0f172a;
      --text-sub: #64748b;
      --border-color: #cbd5e1;
      --primary-blue: #2563eb;
      --primary-hover: #1d4ed8;
      --card-shadow: 0 4px 15px -2px rgba(0,0,0,0.08);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background-color: var(--bg-page);
      color: var(--text-main);
      font-family: var(--font-body);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: auto;
      transition: background 0.3s, color 0.3s;
    }

    .container {
      max-width: 1360px;
      margin: 0 auto;
      width: 100%;
      padding: 24px 28px;
      min-width: 1180px;
    }

    /* Top Navigation Header */
    .top-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 16px;
    }

    .brand-area {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .brand-logo {
      width: 36px;
      height: 36px;
      background: linear-gradient(135deg, var(--primary-blue), var(--neon-cyan));
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 900;
      font-size: 18px;
      color: #fff;
      box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
    }

    .brand-title h1 {
      font-size: 22px;
      font-weight: 800;
      letter-spacing: -0.02em;
    }

    .brand-badges {
      display: flex;
      gap: 8px;
      margin-top: 4px;
      font-size: 11px;
    }

    .badge-pill {
      background: rgba(59, 130, 246, 0.15);
      color: var(--primary-blue);
      border: 1px solid rgba(59, 130, 246, 0.3);
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 600;
    }

    /* View Switcher Tabs */
    .view-switcher {
      display: flex;
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 4px;
      gap: 4px;
    }

    .view-btn {
      padding: 8px 16px;
      border-radius: 7px;
      border: none;
      background: transparent;
      color: var(--text-sub);
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s;
    }

    .view-btn.active {
      background: var(--primary-blue);
      color: #ffffff;
      box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4);
    }

    /* Player Controls */
    .player-controls {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .btn-ctrl {
      padding: 8px 14px;
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }
    .btn-ctrl:hover {
      background: var(--bg-card-hover);
      border-color: var(--primary-blue);
    }

    .btn-play {
      background: var(--primary-blue);
      border-color: var(--primary-blue);
      color: #fff;
    }
    .btn-play:hover {
      background: var(--primary-hover);
    }

    /* Narration Banner */
    .narration-bar {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-left: 5px solid var(--primary-blue);
      border-radius: 10px;
      padding: 14px 20px;
      margin-bottom: 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      box-shadow: var(--card-shadow);
      transition: all 0.3s;
    }

    .narration-left {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .narration-icon {
      font-size: 24px;
      animation: pulseIcon 2s infinite ease-in-out;
    }
    @keyframes pulseIcon {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.15); }
    }

    .narration-content {
      line-height: 1.4;
    }

    .narration-title {
      font-size: 15px;
      font-weight: 800;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .narration-desc {
      font-size: 12px;
      color: var(--text-sub);
      margin-top: 2px;
    }

    .progress-pills {
      display: flex;
      gap: 6px;
    }

    .pill-dot {
      width: 10px;
      height: 10px;
      border-radius: 5px;
      background: var(--border-color);
      transition: all 0.3s;
    }
    .pill-dot.active {
      width: 28px;
      background: var(--primary-blue);
      box-shadow: 0 0 10px var(--primary-blue);
    }
    .pill-dot.done {
      background: var(--neon-cyan);
    }

    /* Main Stage Board */
    .stage-board {
      position: relative;
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 28px;
      margin-bottom: 24px;
      box-shadow: var(--card-shadow);
      min-height: 520px;
      overflow: visible;
    }

    /* SVG Connector Overlay */
    .svg-canvas {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 1;
    }

    .flow-line {
      fill: none;
      stroke: var(--border-color);
      stroke-width: 2;
      transition: stroke 0.3s, stroke-width 0.3s;
    }
    .flow-line.active {
      stroke: var(--primary-blue);
      stroke-width: 3;
      stroke-dasharray: 6, 6;
      animation: linePulse 1.2s linear infinite;
    }
    @keyframes linePulse {
      from { stroke-dashoffset: 24; }
      to { stroke-dashoffset: 0; }
    }

    /* VIEW 1: SYSTEM ARCHITECTURE TIERS */
    .arch-tiers-wrapper {
      position: relative;
      z-index: 2;
      display: flex;
      flex-direction: column;
      gap: 22px;
    }

    .arch-tier {
      display: grid;
      grid-template-columns: 220px 1fr;
      gap: 20px;
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 16px 20px;
      background: rgba(255, 255, 255, 0.02);
      position: relative;
      transition: all 0.3s;
    }
    .arch-tier.active-tier {
      border-color: var(--primary-blue);
      box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
      background: rgba(59, 130, 246, 0.04);
    }

    .tier-header {
      display: flex;
      flex-direction: column;
      justify-content: center;
      border-right: 1px dashed var(--border-color);
      padding-right: 14px;
    }

    .tier-tag {
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 2px;
    }

    .tier-name {
      font-size: 15px;
      font-weight: 800;
      color: var(--text-main);
    }

    .tier-tech {
      font-size: 11px;
      color: var(--text-sub);
      margin-top: 4px;
      font-family: monospace;
    }

    .tier-modules-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
    }

    .module-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 12px 14px;
      cursor: pointer;
      transition: all 0.25s ease;
      display: flex;
      flex-direction: column;
      position: relative;
      user-select: none;
    }
    .module-card:hover {
      transform: translateY(-2px);
      border-color: var(--primary-blue);
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .module-card.active {
      border-color: var(--neon-cyan);
      background: rgba(6, 182, 212, 0.12);
      transform: translateY(-3px);
      box-shadow: 0 0 15px rgba(6, 182, 212, 0.35);
    }

    .module-title {
      font-size: 12px;
      font-weight: 700;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 4px;
    }

    .module-desc {
      font-size: 10px;
      color: var(--text-sub);
      line-height: 1.35;
    }

    .module-contract {
      font-size: 9px;
      color: var(--neon-cyan);
      margin-top: 6px;
      font-family: monospace;
      font-weight: 600;
    }

    /* VIEW 2: BUSINESS WORKFLOW (7-STEP PIPELINE) */
    .workflow-chain-wrapper {
      position: relative;
      z-index: 2;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    .wf-steps-track {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      gap: 12px;
      position: relative;
    }

    .wf-card {
      background: var(--bg-card);
      border: 2px solid var(--border-color);
      border-radius: 12px;
      padding: 18px 12px;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      cursor: pointer;
      position: relative;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      min-height: 220px;
    }
    .wf-card:hover {
      transform: translateY(-4px);
      border-color: var(--primary-blue);
    }
    .wf-card.active {
      transform: translateY(-8px) scale(1.02);
      border-color: var(--neon-cyan);
      box-shadow: 0 10px 25px rgba(6, 182, 212, 0.3);
      background: rgba(6, 182, 212, 0.08);
    }

    .wf-badge-circle {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-weight: 900;
      font-size: 16px;
      margin-bottom: 12px;
      box-shadow: 0 4px 10px rgba(0,0,0,0.3);
      transition: all 0.3s;
    }
    .wf-card.active .wf-badge-circle {
      transform: scale(1.15);
      box-shadow: 0 0 18px currentColor;
    }

    .wf-icon {
      font-size: 22px;
      margin-bottom: 6px;
    }

    .wf-title {
      font-size: 13px;
      font-weight: 800;
      color: var(--text-main);
      margin-bottom: 6px;
      line-height: 1.3;
    }

    .wf-desc {
      font-size: 10px;
      color: var(--text-sub);
      line-height: 1.35;
    }

    /* Decision Branch Highlight Box */
    .decision-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-top: 10px;
    }

    .decision-card {
      border: 2px solid var(--border-color);
      border-radius: 12px;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      gap: 16px;
      background: var(--bg-card);
      transition: all 0.3s;
    }
    .decision-card.ok-branch {
      border-color: var(--neon-green);
      background: rgba(16, 185, 129, 0.06);
    }
    .decision-card.alert-branch {
      border-color: var(--neon-amber);
      background: rgba(245, 158, 11, 0.06);
    }

    .decision-badge {
      width: 42px;
      height: 42px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      flex-shrink: 0;
    }

    .decision-title {
      font-size: 14px;
      font-weight: 800;
    }
    .decision-sub {
      font-size: 11px;
      color: var(--text-sub);
      margin-top: 2px;
    }

    /* Bottom Info Drawer */
    .detail-drawer {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 14px;
      padding: 22px 26px;
      box-shadow: var(--card-shadow);
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 28px;
    }

    .drawer-left h3 {
      font-size: 16px;
      font-weight: 800;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .drawer-badge {
      font-size: 11px;
      background: rgba(59, 130, 246, 0.2);
      color: var(--primary-blue);
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 600;
    }

    .drawer-left p {
      font-size: 13px;
      color: var(--text-sub);
      line-height: 1.6;
      margin-bottom: 14px;
    }

    .checklist {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .check-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: var(--text-main);
    }
    .check-icon {
      color: var(--neon-green);
      font-weight: 900;
    }

    .drawer-right {
      border-left: 1px solid var(--border-color);
      padding-left: 24px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 12px;
    }

    .meta-row {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .meta-label {
      font-size: 10px;
      text-transform: uppercase;
      font-weight: 700;
      color: var(--text-sub);
      letter-spacing: 0.05em;
    }
    .meta-val {
      font-size: 14px;
      font-weight: 700;
      color: var(--text-main);
      font-family: monospace;
    }

    /* Footer */
    .footer-bar {
      margin-top: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      color: var(--text-sub);
      border-top: 1px solid var(--border-color);
      padding-top: 14px;
    }
  </style>
</head>
<body>

  <div class="container">
    <!-- Top Header -->
    <header class="top-header">
      <div class="brand-area">
        <div class="brand-logo">Σ</div>
        <div class="brand-title">
          <h1>StatPro 엔터프라이즈 모션 가이드</h1>
          <div class="brand-badges">
            <span class="badge-pill">시스템 구성도 &amp; 업무플로우 V1.1</span>
            <span>FastAPI 8765 · React 5173 · D:\\StatProData</span>
          </div>
        </div>
      </div>

      <!-- View Switcher -->
      <div class="view-switcher">
        <button class="view-btn active" id="tabArch" onclick="switchView('arch')">
          🖥️ 시스템 구성도 (Architecture)
        </button>
        <button class="view-btn" id="tabWorkflow" onclick="switchView('workflow')">
          🔄 업무 프로세스 플로우 (Workflow)
        </button>
      </div>

      <!-- Player Controls -->
      <div class="player-controls">
        <button class="btn-ctrl" id="btnPrev" title="이전 (←)">&lt;</button>
        <button class="btn-ctrl btn-play" id="btnPlay" title="자동 재생 (Space)">
          <span id="playIcon">▷</span> <span id="playText">자동 설명</span>
        </button>
        <button class="btn-ctrl" id="btnNext" title="다음 (→)">&gt;</button>
        <button class="btn-ctrl" id="btnReset" title="초기화 (R)">↺</button>
        <button class="btn-ctrl" id="btnTheme" title="다크/라이트 전환">🌙</button>
      </div>
    </header>

    <!-- Narration Banner -->
    <div class="narration-bar">
      <div class="narration-left">
        <span class="narration-icon" id="bannerIcon">🚀</span>
        <div class="narration-content">
          <div class="narration-title" id="bannerTitle">
            시스템 초기화 및 구성 탐색
          </div>
          <div class="narration-desc" id="bannerDesc">
            자동 재생을 누르면 현재 개발 기준선에 따른 시스템 4대 계층과 7단계 표준 품질 업무플로우를 순서대로 시연합니다.
          </div>
        </div>
      </div>
      <div class="progress-pills" id="progressPills"></div>
    </div>

    <!-- Main Stage Board -->
    <div class="stage-board" id="stageBoard">
      <svg class="svg-canvas" id="svgCanvas"></svg>

      <!-- VIEW 1: SYSTEM ARCHITECTURE TIERS -->
      <div class="arch-tiers-wrapper" id="viewArch">
        <!-- Tier 1: Frontend Client -->
        <div class="arch-tier active-tier" id="tier-1">
          <div class="tier-header">
            <span class="tier-tag" style="color: var(--neon-cyan);">Tier 01</span>
            <div class="tier-name">클라이언트 웹 UI</div>
            <div class="tier-tech">React 19 · Vite · Recharts<br>127.0.0.1:5173</div>
          </div>
          <div class="tier-modules-grid">
            <div class="module-card active" id="mod-spc" onclick="selectArch(0)">
              <div class="module-title">📊 SPC 작업공간</div>
              <div class="module-desc">I-MR, Xbar-R/S, EWMA, CUSUM, p/np/c/u, Laney P'/U', G/T 관리도</div>
              <div class="module-contract">spcCatalog.ts</div>
            </div>
            <div class="module-card" id="mod-doe" onclick="selectArch(1)">
              <div class="module-title">🧪 DOE &amp; 최적화</div>
              <div class="module-desc">요인배치, 중심합성, 반응표면(RSM), Desirability 다중응답 최적화</div>
              <div class="module-contract">analysisSelection.ts</div>
            </div>
            <div class="module-card" id="mod-fmea" onclick="selectArch(2)">
              <div class="module-title">📑 FMEA &amp; 관리계획</div>
              <div class="module-desc">AIAG/VDA 7단계, AP위험도 평가, PFMEA-Control Plan 추적, 승인</div>
              <div class="module-contract">types.ts (FMEA context)</div>
            </div>
            <div class="module-card" id="mod-copilot" onclick="selectArch(3)">
              <div class="module-title">🤖 AI Copilot 플라이아웃</div>
              <div class="module-desc">현장 Rule Catalog 우선 매칭 ➔ 명시적 허용 시에만 Gemini 2.5 Flash 호출</div>
              <div class="module-contract">copilotGuidance.ts</div>
            </div>
          </div>
        </div>

        <!-- Tier 2: API & Gateway Service -->
        <div class="arch-tier" id="tier-2">
          <div class="tier-header">
            <span class="tier-tag" style="color: var(--primary-blue);">Tier 02</span>
            <div class="tier-name">로컬 API &amp; 서비스</div>
            <div class="tier-tech">FastAPI · Uvicorn · Pydantic<br>127.0.0.1:8765</div>
          </div>
          <div class="tier-modules-grid">
            <div class="module-card" id="mod-api-runs" onclick="selectArch(4)">
              <div class="module-title">⚡ /api/runs</div>
              <div class="module-desc">통계 분석 비동기/동기 실행, ETag/If-Match 낙관적 동시성 제어</div>
              <div class="module-contract">src/statpro/api/server.py</div>
            </div>
            <div class="module-card" id="mod-api-worksheets" onclick="selectArch(5)">
              <div class="module-title">📋 /api/worksheets</div>
              <div class="module-desc">불변 데이터셋 스냅샷, 리비전 워크시트, 셀 단위 원자적 패치</div>
              <div class="module-contract">statpro/application/storage.py</div>
            </div>
            <div class="module-card" id="mod-api-fmea" onclick="selectArch(6)">
              <div class="module-title">🛡️ /api/fmea &amp; dmaic</div>
              <div class="module-desc">FMEA 연구 개정, 조치 등록, 기업 승인, DMAIC 단계별 프로젝트 바인딩</div>
              <div class="module-contract">statpro/fmea/engine.py</div>
            </div>
            <div class="module-card" id="mod-api-copilot" onclick="selectArch(7)">
              <div class="module-title">🧠 /api/copilot</div>
              <div class="module-desc">현장 Rule Catalog 42종 매칭 및 Fail-closed 로컬 폴백 엔진</div>
              <div class="module-contract">statpro/application/copilot.py</div>
            </div>
          </div>
        </div>

        <!-- Tier 3: Statistical & Domain Core -->
        <div class="arch-tier" id="tier-3">
          <div class="tier-header">
            <span class="tier-tag" style="color: var(--neon-purple);">Tier 03</span>
            <div class="tier-name">통계 도메인 엔진</div>
            <div class="tier-tech">Python 3.12 · SciPy · NumPy<br>Zero Mutable Global State</div>
          </div>
          <div class="tier-modules-grid">
            <div class="module-card" id="mod-stat-spc" onclick="selectArch(8)">
              <div class="module-title">📈 SPC &amp; Nelson Rules</div>
              <div class="module-desc">NIST 4대 규칙 + Nelson 8대 이상 패턴 전수 판정, 자동 경고</div>
              <div class="module-contract">statpro/analyses/spc.py</div>
            </div>
            <div class="module-card" id="mod-stat-doe" onclick="selectArch(9)">
              <div class="module-title">📐 DOE &amp; Response Engine</div>
              <div class="module-desc">ANOVA, 회귀계수, 잔차분석, 꼭짓점 최적화 및 Derringer 다중응답</div>
              <div class="module-contract">statpro/analyses/doe.py</div>
            </div>
            <div class="module-card" id="mod-stat-msa" onclick="selectArch(10)">
              <div class="module-title">📏 균형 교차 Gage R&amp;R</div>
              <div class="module-desc">ANOVA 방식 작업자-부품 교차 변동 분해, %GRR, 구별 범주수(ndc)</div>
              <div class="module-contract">statpro/analyses/msa.py</div>
            </div>
            <div class="module-card" id="mod-stat-bundle" onclick="selectArch(11)">
              <div class="module-title">📦 ResultBundle V1</div>
              <div class="module-desc">Draft 2020-12 스키마 검증, 입력 다이제스트 해시, 재현성 보장</div>
              <div class="module-contract">statpro/domain/result_bundle.py</div>
            </div>
          </div>
        </div>

        <!-- Tier 4: Storage & Security Sandbox -->
        <div class="arch-tier" id="tier-4">
          <div class="tier-header">
            <span class="tier-tag" style="color: var(--neon-green);">Tier 04</span>
            <div class="tier-name">보안 로컬 스토리지</div>
            <div class="tier-tech">D:\StatProData<br>Air-Gapped Local-First</div>
          </div>
          <div class="tier-modules-grid">
            <div class="module-card" id="mod-store-runs" onclick="selectArch(12)">
              <div class="module-title">🗄️ Atomic Document Store</div>
              <div class="module-desc">단일 프로세스 안전 원자적 쓰기(Atomic Write), JSON envelope 저장</div>
              <div class="module-contract">D:\StatProData\runs\</div>
            </div>
            <div class="module-card" id="mod-store-dataset" onclick="selectArch(13)">
              <div class="module-title">📄 CSV Dataset Snapshots</div>
              <div class="module-desc">업로드 원본의 SHA-256 불변 스냅샷 보존, 결측치 보정 금지</div>
              <div class="module-contract">D:\StatProData\datasets\</div>
            </div>
            <div class="module-card" id="mod-store-fmea" onclick="selectArch(14)">
              <div class="module-title">🔒 FMEA Audit Ledger</div>
              <div class="module-desc">불변 개정 이력, 서명 승인 증거, Action Priority 이력 보존</div>
              <div class="module-contract">D:\StatProData\fmea\</div>
            </div>
            <div class="module-card" id="mod-store-export" onclick="selectArch(15)">
              <div class="module-title">📑 단일 HTML / 4K 아카이브</div>
              <div class="module-desc">외부 통신 없는 자립형 인터랙티브 보고서, 벡터 차트 영구 저장</div>
              <div class="module-contract">D:\StatProData\exports\</div>
            </div>
          </div>
        </div>
      </div>

      <!-- VIEW 2: BUSINESS WORKFLOW CHAIN -->
      <div class="workflow-chain-wrapper" id="viewWorkflow" style="display: none;">
        <div class="wf-steps-track">
          <!-- Step 1 -->
          <div class="wf-card active" id="wf-0" onclick="selectWf(0)">
            <div class="wf-badge-circle" style="background: var(--neon-cyan); color: #000;">01</div>
            <div class="wf-icon">🧭</div>
            <div class="wf-title">홈 &amp; 분석 선택</div>
            <div class="wf-desc">Analysis Selection Helper<br>판단목적·데이터유형 가이드</div>
          </div>

          <!-- Step 2 -->
          <div class="wf-card" id="wf-1" onclick="selectWf(1)">
            <div class="wf-badge-circle" style="background: var(--primary-blue);">02</div>
            <div class="wf-icon">📂</div>
            <div class="wf-title">데이터 수집·검증</div>
            <div class="wf-desc">CSV 작업표 불변 스냅샷<br>결측치 0 대체 원천 금지</div>
          </div>

          <!-- Step 3 -->
          <div class="wf-card" id="wf-2" onclick="selectWf(2)">
            <div class="wf-badge-circle" style="background: var(--neon-purple);">03</div>
            <div class="wf-icon">📏</div>
            <div class="wf-title">측정시스템(MSA)</div>
            <div class="wf-desc">균형 교차 Gage R&amp;R<br>%GRR &lt; 10% 신뢰성 검증</div>
          </div>

          <!-- Step 4 -->
          <div class="wf-card" id="wf-3" onclick="selectWf(3)">
            <div class="wf-badge-circle" style="background: var(--neon-green);">04</div>
            <div class="wf-icon">📈</div>
            <div class="wf-title">공정 모니터링(SPC)</div>
            <div class="wf-desc">Xbar-R/S, I-MR 실시간 관리도<br>Nelson 8 Rules 이상 판정</div>
          </div>

          <!-- Step 5 -->
          <div class="wf-card" id="wf-4" onclick="selectWf(4)">
            <div class="wf-badge-circle" style="background: var(--neon-amber);">05</div>
            <div class="wf-icon">⚖️</div>
            <div class="wf-title">능력 &amp; FMEA 위험</div>
            <div class="wf-desc">Cpk/Ppk 공정능력 평가<br>AIAG/VDA 7단계 AP 조치</div>
          </div>

          <!-- Step 6 -->
          <div class="wf-card" id="wf-5" onclick="selectWf(5)">
            <div class="wf-badge-circle" style="background: var(--neon-pink);">06</div>
            <div class="wf-icon">🧪</div>
            <div class="wf-title">실험계획(DOE) 최적화</div>
            <div class="wf-desc">반응표면법(RSM) &amp; 요인배치<br>Desirability 다중응답 도출</div>
          </div>

          <!-- Step 7 -->
          <div class="wf-card" id="wf-6" onclick="selectWf(6)">
            <div class="wf-badge-circle" style="background: #6366f1;">07</div>
            <div class="wf-icon">📑</div>
            <div class="wf-title">대시보드 &amp; 리포트</div>
            <div class="wf-desc">ResultBundle 지표 스냅샷<br>단일 HTML / 4K 아카이빙</div>
          </div>
        </div>

        <!-- Decision Gate Branches -->
        <div class="decision-row">
          <div class="decision-card ok-branch" id="branch-ok">
            <div class="decision-badge" style="background: rgba(16, 185, 129, 0.2); color: var(--neon-green);">✅</div>
            <div>
              <div class="decision-title" style="color: var(--neon-green);">공정 안정 판정 (Cpk ≥ 1.33 &amp; 이상 룰 부재)</div>
              <div class="decision-sub">표준 공정 조건 확정 승인 ➔ Control Plan 이관 및 정기 모니터링 유지</div>
            </div>
          </div>
          <div class="decision-card alert-branch" id="branch-alert">
            <div class="decision-badge" style="background: rgba(245, 158, 11, 0.2); color: var(--neon-amber);">⚠️</div>
            <div>
              <div class="decision-title" style="color: var(--neon-amber);">이상 감지 및 고위험 (Nelson 위배 or High AP)</div>
              <div class="decision-sub">현장 원인 파악 (파레토/특성요인도) ➔ FMEA 조치 계획 수립 ➔ DOE 최적화 수행</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Info Drawer -->
    <div class="detail-drawer">
      <div class="drawer-left">
        <h3 id="drawerTitle">
          <span class="drawer-badge" id="drawerBadge">Tier 01</span>
          <span id="drawerHeading">클라이언트 웹 UI &amp; 작업공간</span>
        </h3>
        <p id="drawerDesc">
          React 19 + TypeScript 기반의 로컬 퍼스트 웹 애플리케이션으로, 복잡한 통계 분석을 직관적인 7단계 표준 작업 흐름(홈 ➔ 작업공간 ➔ 작업흐름 ➔ 입력 ➔ 실행 ➔ 검토 ➔ 출력)으로 가이드합니다.
        </p>
        <ul class="checklist" id="drawerChecklist">
          <li class="check-item"><span class="check-icon">✓</span> 로컬 전용 127.0.0.1:5173 호스팅</li>
          <li class="check-item"><span class="check-icon">✓</span> Recharts 기반 고해상도 반응형 관리도</li>
          <li class="check-item"><span class="check-icon">✓</span> ETag 기반 낙관적 동시성 제어로 안전한 멀티 세션 작업</li>
        </ul>
      </div>

      <div class="drawer-right">
        <div class="meta-row">
          <span class="meta-label">핵심 소스 경로</span>
          <span class="meta-val" id="metaPath">web/src/App.tsx</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">참조 개발 문서</span>
          <span class="meta-val" id="metaDoc">docs/06.StatPro_Development_Stack.md</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">보안 및 실행 계약</span>
          <span class="meta-val" id="metaRule">Air-gapped Local-First</span>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="footer-bar">
      <div>StatPro Architecture &amp; Quality Workflow System · Grounded on Production Codebase &amp; Docs</div>
      <div>Python 3.12 · FastAPI 0.148 · React 19.3 · Atomic Document Store V1</div>
    </footer>
  </div>

  <script>
    let currentView = 'arch'; // 'arch' | 'workflow'
    let currentStep = 0;
    let isPlaying = false;
    let timer = null;

    const archData = [
      {
        badge: "Tier 01: Client",
        title: "통계적 공정관리(SPC) 작업공간",
        desc: "I-MR, Xbar-R, Xbar-S, EWMA, CUSUM 등 계량형 및 p, np, c, u, Laney P'/U', G/T 등 계수형/희귀사건 관리도를 실시간 렌더링합니다.",
        checks: ["Recharts 기반 고성능 반응형 SVG 차트", "Nelson 8대 이상 룰 위배 포인트 붉은 점 마킹", "Western Electric 4대 보조 규칙 실시간 감지"],
        path: "web/src/spcCatalog.ts",
        doc: "docs/02.StatPro_PRD_FS.md",
        rule: "ISO 21747 / AIAG SPC 표준 준수"
      },
      {
        badge: "Tier 01: Client",
        title: "실험계획법(DOE) & 다중응답 최적화",
        desc: "2수준 완전/부분 요인배치, 반응표면법(Box-Behnken, CCD), Plackett-Burman 설계 및 Derringer 만족도(Desirability) 다중응답 최적화를 시각화합니다.",
        checks: ["ANOVA 표, 주효과/상호작용도 실시간 시각화", "꼭짓점 최적화 및 제약조건 탐색", "고객/규제기관 제출용 HTML/JSON 내보내기"],
        path: "web/src/analysisSelection.ts",
        doc: "docs/03.StatPro_IA.md",
        rule: "재현 가능한 파라미터 다이제스트"
      },
      {
        badge: "Tier 01: Client",
        title: "FMEA & 관리계획서(Control Plan) 연계",
        desc: "AIAG/VDA 7단계 표준 FMEA를 작성하고, Action Priority(AP) 위험도 매트릭스에 따른 조치 등록, 승인 및 PFMEA-Control Plan 추적성을 보장합니다.",
        checks: ["불변 개정(Revision) 모델로 감사 추적성 확보", "SPC/MSA 실행 결과(Run ID)를 조치 근거로 직접 연결", "기업 IdP 기반 역할/직무분리(SoD) 승인"],
        path: "web/src/types.ts",
        doc: "docs/08.StatPro_Menu_UI_Proposal.md",
        rule: "불변 감사 추적성 (Audit Trail)"
      },
      {
        badge: "Tier 01: Client",
        title: "AI Copilot 현장 의사결정 도우미",
        desc: "우측 플라이아웃 패널에서 현장 작업공간을 감지하고, 검토된 42종 현장 Rule Catalog를 기반으로 최적 도구와 메뉴 경로, 체크리스트를 우선 추천합니다.",
        checks: ["현장 Rulebase 우선 매칭 (계산 설정 자동 변경 금지)", "관리자가 허용한 경우에만 Gemini 2.5 Flash 호출", "네트워크 단절 시 안전하게 로컬 규칙으로 폴백"],
        path: "web/src/copilotGuidance.ts",
        doc: "docs/10.StatPro_AI_Copilot_Rule_Catalog.md",
        rule: "Fail-closed 로컬 안전성"
      },
      {
        badge: "Tier 02: API",
        title: "FastAPI /api/runs 분석 실행 엔드포인트",
        desc: "모든 통계 연산을 단일 프로세스 안전하게 호출하며, ETag와 If-Match 헤더를 활용해 다중 사용자/세션 간 충돌을 방지합니다.",
        checks: ["OpenAPI 자동 문서화 (/docs)", "Pydantic V2 입력 스키마 엄격 검증", "유효하지 않은 입력 시 AnalysisInputError 즉각 반환"],
        path: "src/statpro/api/server.py",
        doc: "docs/06.StatPro_Development_Stack.md",
        rule: "ETag 낙관적 동시성 제어"
      },
      {
        badge: "Tier 02: API",
        title: "FastAPI /api/worksheets 데이터 서비스",
        desc: "CSV 원본의 불변 데이터셋 스냅샷을 생성하고, 리비전 기반의 워크시트에서 행/열 단위 원자적 조회를 제공합니다.",
        checks: ["결측치 0 자동 대체 원천 금지 (Null 격리)", "대용량 데이터 커서 기반 페이징 (Cursor Paging)", "UTF-8 / CP949 인코딩 무결성 자동 보정"],
        path: "src/statpro/application/storage.py",
        doc: "docs/02.StatPro_PRD_FS.md",
        rule: "결측치 0 대체 금지 원칙"
      },
      {
        badge: "Tier 02: API",
        title: "FastAPI /api/fmea & /api/dmaic 서비스",
        desc: "FMEA 연구 상태 전이(작성 ➔ 검토요청 ➔ 승인)와 DMAIC 단계별 산출물 바인딩을 관리합니다.",
        checks: ["상태 머신 기반 엄격한 라이프사이클 통제", "조치 권고안 등록 시 완료 증거 파일 첨부", "DMAIC 프로젝트 헌장과 수율 지표 연결"],
        path: "src/statpro/fmea/engine.py",
        doc: "docs/08.StatPro_Menu_UI_Proposal.md",
        rule: "품질 거버넌스 준수"
      },
      {
        badge: "Tier 02: API",
        title: "FastAPI /api/copilot 지능형 안내 엔진",
        desc: "사용자 세션 상태를 분석하여 42종 Rule Catalog와 대조하고 지능형 조언을 즉시 제공합니다.",
        checks: ["비동기 HTTPX 기반 Gemini API 호출", "환경변수 STATPRO_COPILOT_LLM_ENABLED 가드", "프롬프트 인젝션 및 데이터 유출 방지"],
        path: "src/statpro/application/copilot.py",
        doc: "docs/10.StatPro_AI_Copilot_Rule_Catalog.md",
        rule: "선택형 외부 LLM 연동"
      },
      {
        badge: "Tier 03: Core",
        title: "Python 3.12 SPC & Nelson 8 Rules 연산 엔진",
        desc: "전역 상태(Global State)가 없는 순수 함수형 구조로, 동일 입력에 항상 동일한 결과를 반환하며 공개 표준 수식을 엄격히 준수합니다.",
        checks: ["NIST 공식 레퍼런스 데이터셋 전수 검증 완료", "군내 변동(Within) vs 전체 변동(Overall) 분리", "1점 3시그마, 9점 편향, 6점 추세 등 8대 이상 룰 검출"],
        path: "src/statpro/analyses/spc.py",
        doc: "docs/07.StatPro_Test_Report.md",
        rule: "100% 재현 가능한 통계 엔진"
      },
      {
        badge: "Tier 03: Core",
        title: "DOE 요인배치 및 반응표면 최적화 엔진",
        desc: "Scipy 최적화 알고리즘과 행렬 연산을 활용하여 다중 반응변수의 목표값, 최대화, 최소화를 동시 만족하는 최적 인자 조합을 계산합니다.",
        checks: ["선별 설계(Plackett-Burman) 별칭 구조 산출", "중심합성설계(CCD) 및 Box-Behnken 2차 회귀식 적합", "Derringer-Suich 다중 만족도 함수 최적화"],
        path: "src/statpro/analyses/doe.py",
        doc: "docs/02.StatPro_PRD_FS.md",
        rule: "다중응답 Desirability 수렴"
      },
      {
        badge: "Tier 03: Core",
        title: "균형 교차 Gage R&R 측정시스템 분석",
        desc: "작업자(Appraiser)와 부품(Part)의 교차 2원 배치 분산분석(Two-way ANOVA)을 수행하여 측정 시스템 자체의 변동을 정밀 분해합니다.",
        checks: ["반복성(Repeatability) vs 재현성(Reproducibility) 분해", "%GRR < 10% (합격), 10~30% (조건부), > 30% (불가) 판정", "구별 범주 수(ndc >= 5) 측정 분해능 검증"],
        path: "src/statpro/analyses/msa.py",
        doc: "docs/02.StatPro_PRD_FS.md",
        rule: "AIAG MSA 4th Edition 기준"
      },
      {
        badge: "Tier 03: Core",
        title: "ResultBundle V1 불변 결과 계약",
        desc: "분석 결과, 원본 다이제스트, 엔진 버전, 적용 가정, 경고를 하나의 불변 JSON 봉투(Envelope)에 밀봉하여 저장합니다.",
        checks: ["Draft 2020-12 JSON Schema 검증 통과 필수", "수치 반올림은 도메인 코어 밖 UI 레이어에서만 수행", "ResultBundle을 통한 감사 재현 완벽 보장"],
        path: "src/statpro/domain/result_bundle.py",
        doc: "docs/06.StatPro_Development_Stack.md",
        rule: "Schema Contract V1 Enforced"
      },
      {
        badge: "Tier 04: Storage",
        title: "원자적 문서 스토리지 (Atomic JSON Store)",
        desc: "임시 파일 쓰기 후 원자적 이름 변경(Atomic Rename) 방식을 적용하여 정전이나 비정상 종료 시에도 파일 손상을 100% 방지합니다.",
        checks: ["단일 프로세스 로컬 안전 파일 락", "Run ID 기반 불변 디렉토리 구조", "손상 없는 트랜잭션 안전성 보장"],
        path: "D:\\StatProData\\runs\\",
        doc: "docs/06.StatPro_Development_Stack.md",
        rule: "ACID 보장 Atomic Write"
      },
      {
        badge: "Tier 04: Storage",
        title: "불변 CSV 데이터셋 스냅샷",
        desc: "사용자가 업로드한 원본 CSV는 변경 불가능한 읽기 전용 스냅샷으로 보존되며, 분석 실행 시 항상 이 불변 스냅샷을 참조합니다.",
        checks: ["SHA-256 무결성 체크섬 자동 기록", "데이터 변조 및 덮어쓰기 원천 방지", "결측치 처리 이력 완전 추적"],
        path: "D:\\StatProData\\datasets\\",
        doc: "docs/02.StatPro_PRD_FS.md",
        rule: "Data Integrity & Immutability"
      },
      {
        badge: "Tier 04: Storage",
        title: "FMEA 감사 원장 및 승인 증거 저장소",
        desc: "FMEA 개정판과 권고 조치 완료 증거 문서, 승인 이력을 체계적으로 격리 보관합니다.",
        checks: ["개정 번호별 디렉토리 격리", "첨부 증거 파일 로컬 암호화 저장", "감사관 검토용 풀 패키지 출력 지원"],
        path: "D:\\StatProData\\fmea\\",
        doc: "docs/08.StatPro_Menu_UI_Proposal.md",
        rule: "규제 감사 대비 영구 보존"
      },
      {
        badge: "Tier 04: Storage",
        title: "독립형 단일 HTML 리포트 및 4K 아카이브",
        desc: "외부 인터넷 연결이나 서버 없이도 열람 가능한 Self-contained 단일 파일 HTML과 4K 고해상도 벡터 차트를 영구 저장합니다.",
        checks: ["CSS/JS/차트 데이터 단일 파일 번들링", "품질 검토 보고서 원클릭 인쇄/PDF 호환", "D:\\StatProData\\exports\\ 영구 보존"],
        path: "D:\\StatProData\\exports\\",
        doc: "docs/01.StatPro_SRS.md",
        rule: "Zero Dependency Self-contained"
      }
    ];

    const workflowData = [
      {
        badge: "Step 01",
        title: "홈 대시보드 & 분석 선택 도우미 (Analysis Selection)",
        desc: "현장 엔지니어가 판단 목적(차이 검정, 공정 감시, 최적화 등), 데이터 유형(연속형, 이산형), 표본 구조를 입력하여 최적의 분석 도구를 안내받습니다.",
        checks: ["홈 대시보드에서 최근 실행 이력 및 FMEA 즉각 확인", "Analysis Selection 도우미로 통계 방법 오류 원천 방지", "AI Copilot의 현장 맞춤 추천 가이드 연계"],
        path: "web/src/pages/AnalysisSelectionPage.tsx",
        doc: "docs/08.StatPro_Menu_UI_Proposal.md",
        rule: "표준 시작점: 홈(Home) ➔ 작업공간(Workspace)"
      },
      {
        badge: "Step 02",
        title: "데이터 수집 및 결측치 무결성 검증 (Data Validation)",
        desc: "CSV 원본을 로컬 스토리지에 불변 스냅샷으로 저장합니다. 통계 왜곡을 일으키는 '결측치 0 자동 대체'는 원천 차단되며 Null 격리 처리됩니다.",
        checks: ["UTF-8 / CP949 인코딩 무결성 자동 검출", "가상화 그리드를 통한 100만 행 즉각 프리뷰", "공학 규격(USL/LSL)과 관리 한계(UCL/LCL) 명확한 분리 입력"],
        path: "web/src/pages/WorksheetsPage.tsx",
        doc: "docs/02.StatPro_PRD_FS.md",
        rule: "결측치 0 임의 대체 엄격 금지"
      },
      {
        badge: "Step 03",
        title: "측정시스템 분석 (MSA Gage R&R 검증)",
        desc: "공정 데이터를 분석하기 전, 계측기와 작업자로 인한 측정 오차가 허용 수준인지 균형 교차 Gage R&R으로 사전 검증합니다.",
        checks: ["%GRR < 10%: 측정 시스템 합격, 신뢰 데이터 확보", "%GRR 10~30%: 조건부 허용, 중요 공정 보정 필요", "ndc >= 5: 충분한 공정 분해능 보유 확인"],
        path: "src/statpro/analyses/msa.py",
        doc: "docs/02.StatPro_PRD_FS.md",
        rule: "선행 조건: 측정 신뢰성 확보 후 SPC 개시"
      },
      {
        badge: "Step 04",
        title: "실시간 공정 모니터링 & 이상 룰 감지 (SPC & Nelson Rules)",
        desc: "I-MR, Xbar-R/S 관리도를 가동하여 공정 평균과 산포의 안정성을 실시간 감시하고, Nelson 8 Rules를 전수 검사합니다.",
        checks: ["Rule 1: 1점이 관리한계(±3σ) 이탈 ➔ 특수원인 경보", "Rule 2: 연속 9점이 중심선 한쪽에 위치 ➔ 공정 이동", "Western Electric 4대 보조 규칙 및 변동성 동시 감시"],
        path: "src/statpro/analyses/spc.py",
        doc: "docs/07.StatPro_Test_Report.md",
        rule: "실시간 이상 원인 자동 마킹"
      },
      {
        badge: "Step 05",
        title: "공정능력 지수 산출 & FMEA 고장 위험도 평가",
        desc: "Anderson-Darling 정규성 검정 후 Cp/Cpk/Pp/Ppk를 산출하며, 이상 발생 시 AIAG/VDA 7단계 FMEA의 Action Priority(AP)를 재평가합니다.",
        checks: ["정규성 만족 시 Cpk, 비정규 시 경험적/변환 공정능력 적용", "High AP 발생 시 즉시 예방/탐지 조치 요구 트리거", "PFMEA와 현장 관리계획서(Control Plan) 간 추적성 유지"],
        path: "src/statpro/fmea/engine.py",
        doc: "docs/02.StatPro_PRD_FS.md",
        rule: "Cpk ≥ 1.33 관리 상태 목표"
      },
      {
        badge: "Step 06",
        title: "실험계획법(DOE) 기반 공정 최적화 및 Desirability 도출",
        desc: "수율 저하나 산포 과다 문제 해결을 위해 요인배치법과 반응표면법(RSM)을 실행하고, 다중 응답 만족도(Desirability)를 극대화합니다.",
        checks: ["유의미한 주효과 및 2차 상호작용 인자 선별", "회귀 방정식 적합 및 등고선/반응표면도 생성", "제약 조건 하에서의 최적 파라미터 조합 산출"],
        path: "src/statpro/analyses/doe.py",
        doc: "docs/02.StatPro_PRD_FS.md",
        rule: "최적 공정 윈도우(Process Window) 도출"
      },
      {
        badge: "Step 07",
        title: "품질 대시보드 지표 연동 & 단일 HTML / 4K 아카이빙",
        desc: "모든 분석 실행 결과(ResultBundle)를 품질 대시보드에 불변 스냅샷으로 바인딩하고, 단일 파일 HTML 리포트를 발행하여 영구 보존합니다.",
        checks: ["D:\\StatProData 스토리지에 분석 이력 100% 영구 보존", "외부 라이브러리 없이 독립 동작하는 고해상도 HTML 리포트", "기업 ERP 및 품질 보증 결재 시스템으로 즉시 내보내기"],
        path: "src/statpro/quality_dashboard.py",
        doc: "docs/01.StatPro_SRS.md",
        rule: "엔드투엔드 재현성 및 감사 자립성"
      }
    ];

    function updatePills() {
      const container = document.getElementById('progressPills');
      container.innerHTML = '';
      const total = currentView === 'arch' ? archData.length : workflowData.length;
      for (let i = 0; i < total; i++) {
        const d = document.createElement('div');
        d.className = 'pill-dot' + (i === currentStep ? ' active' : (i < currentStep ? ' done' : ''));
        container.appendChild(d);
      }
    }

    function switchView(view) {
      if (isPlaying) togglePlay();
      currentView = view;
      currentStep = 0;

      if (view === 'arch') {
        document.getElementById('tabArch').classList.add('active');
        document.getElementById('tabWorkflow').classList.remove('active');
        document.getElementById('viewArch').style.display = 'flex';
        document.getElementById('viewWorkflow').style.display = 'none';
        updateArchView();
      } else {
        document.getElementById('tabWorkflow').classList.add('active');
        document.getElementById('tabArch').classList.remove('active');
        document.getElementById('viewWorkflow').style.display = 'flex';
        document.getElementById('viewArch').style.display = 'none';
        updateWfView();
      }
    }

    function updateArchView() {
      const data = archData[currentStep];

      // Active Tier highlight
      const tierIdx = Math.floor(currentStep / 4) + 1;
      for (let t = 1; t <= 4; t++) {
        const el = document.getElementById('tier-' + t);
        if (el) {
          if (t === tierIdx) el.classList.add('active-tier');
          else el.classList.remove('active-tier');
        }
      }

      // Active module card highlight
      document.querySelectorAll('#viewArch .module-card').forEach((c, idx) => {
        if (idx === currentStep) c.classList.add('active');
        else c.classList.remove('active');
      });

      // Narration
      document.getElementById('bannerIcon').textContent = '🖥️';
      document.getElementById('bannerTitle').textContent = `[${data.badge}] ${data.title}`;
      document.getElementById('bannerDesc').textContent = data.desc;

      // Drawer
      document.getElementById('drawerBadge').textContent = data.badge;
      document.getElementById('drawerHeading').textContent = data.title;
      document.getElementById('drawerDesc').textContent = data.desc;
      document.getElementById('metaPath').textContent = data.path;
      document.getElementById('metaDoc').textContent = data.doc;
      document.getElementById('metaRule').textContent = data.rule;

      const chk = document.getElementById('drawerChecklist');
      chk.innerHTML = '';
      data.checks.forEach(c => {
        const li = document.createElement('li');
        li.className = 'check-item';
        li.innerHTML = `<span class="check-icon">✓</span> ${c}`;
        chk.appendChild(li);
      });

      updatePills();
    }

    function updateWfView() {
      const data = workflowData[currentStep];

      // Highlight step card
      for (let i = 0; i < 7; i++) {
        const c = document.getElementById('wf-' + i);
        if (c) {
          if (i === currentStep) c.classList.add('active');
          else c.classList.remove('active');
        }
      }

      // Branch highlights on step 4/5
      const okB = document.getElementById('branch-ok');
      const alB = document.getElementById('branch-alert');
      if (currentStep >= 3) {
        okB.style.opacity = '1';
        alB.style.opacity = '1';
      } else {
        okB.style.opacity = '0.6';
        alB.style.opacity = '0.6';
      }

      // Narration
      document.getElementById('bannerIcon').textContent = '🔄';
      document.getElementById('bannerTitle').textContent = `[${data.badge}] ${data.title}`;
      document.getElementById('bannerDesc').textContent = data.desc;

      // Drawer
      document.getElementById('drawerBadge').textContent = data.badge;
      document.getElementById('drawerHeading').textContent = data.title;
      document.getElementById('drawerDesc').textContent = data.desc;
      document.getElementById('metaPath').textContent = data.path;
      document.getElementById('metaDoc').textContent = data.doc;
      document.getElementById('metaRule').textContent = data.rule;

      const chk = document.getElementById('drawerChecklist');
      chk.innerHTML = '';
      data.checks.forEach(c => {
        const li = document.createElement('li');
        li.className = 'check-item';
        li.innerHTML = `<span class="check-icon">✓</span> ${c}`;
        chk.appendChild(li);
      });

      updatePills();
    }

    function selectArch(idx) {
      currentStep = idx;
      updateArchView();
    }

    function selectWf(idx) {
      currentStep = idx;
      updateWfView();
    }

    function nextStep() {
      const max = currentView === 'arch' ? archData.length : workflowData.length;
      currentStep = (currentStep + 1) % max;
      if (currentView === 'arch') updateArchView();
      else updateWfView();
    }

    function prevStep() {
      const max = currentView === 'arch' ? archData.length : workflowData.length;
      currentStep = (currentStep - 1 + max) % max;
      if (currentView === 'arch') updateArchView();
      else updateWfView();
    }

    function togglePlay() {
      if (isPlaying) {
        clearInterval(timer);
        isPlaying = false;
        document.getElementById('playIcon').textContent = '▷';
        document.getElementById('playText').textContent = '자동 설명';
      } else {
        isPlaying = true;
        document.getElementById('playIcon').textContent = '❚❚';
        document.getElementById('playText').textContent = '일시 정지';
        timer = setInterval(nextStep, 3200);
      }
    }

    function resetPlay() {
      if (isPlaying) togglePlay();
      currentStep = 0;
      if (currentView === 'arch') updateArchView();
      else updateWfView();
    }

    document.getElementById('btnPlay').addEventListener('click', togglePlay);
    document.getElementById('btnNext').addEventListener('click', () => { if(isPlaying) togglePlay(); nextStep(); });
    document.getElementById('btnPrev').addEventListener('click', () => { if(isPlaying) togglePlay(); prevStep(); });
    document.getElementById('btnReset').addEventListener('click', resetPlay);
    document.getElementById('btnTheme').addEventListener('click', () => {
      document.body.classList.toggle('light-mode');
      const isLight = document.body.classList.contains('light-mode');
      document.getElementById('btnTheme').textContent = isLight ? '☀️' : '🌙';
    });

    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space') { e.preventDefault(); togglePlay(); }
      else if (e.code === 'ArrowRight') nextStep();
      else if (e.code === 'ArrowLeft') prevStep();
      else if (e.code === 'KeyR') resetPlay();
      else if (e.code === 'Digit1') switchView('arch');
      else if (e.code === 'Digit2') switchView('workflow');
    });

    // Initialize
    updateArchView();
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

    html_file = os.path.join("diagrams", "statpro_system_and_workflow_motion.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print(f"Generated: {html_file}")

    art_file = os.path.join(artifact_dir, "statpro_system_and_workflow_motion.html")
    with open(art_file, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print(f"Generated artifact: {art_file}")

    generate_bat("open_system_and_workflow_motion.bat", "System Architecture & Workflow Motion Guide", "statpro_system_and_workflow_motion.html")

if __name__ == "__main__":
    main()
