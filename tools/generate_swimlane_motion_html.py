import os
import shutil

HTML_CONTENT = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StatPro 전체 표준 작업 흐름 (Overall End-to-End Workflow)</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
  <style>
    :root {
      --bg-page: #f8fafc;
      --bg-card: #ffffff;
      --text-main: #0f172a;
      --text-sub: #64748b;
      --border-color: #cbd5e1;
      --border-dashed: #94a3b8;
      --banner-bg: #eff6ff;
      --banner-border: #bfdbfe;
      --banner-text: #1e40af;
      --primary-blue: #2563eb;
      --primary-hover: #1d4ed8;
      --success-border: #22c55e;
      --success-bg: #f0fdf4;
      --warning-border: #d97706;
      --warning-bg: #fffbeb;
      --box-shadow: 0 1px 3px rgba(0,0,0,0.07), 0 1px 2px rgba(0,0,0,0.04);
      --box-shadow-active: 0 10px 25px -5px rgba(37, 99, 235, 0.25), 0 8px 10px -6px rgba(37, 99, 235, 0.2);
      --connector-color: #64748b;
      --connector-active: #2563eb;
      --lane-bg-1: #ffffff;
      --lane-bg-2: #ffffff;
      --lane-bg-3: #ffffff;
      --privacy-box-bg: rgba(240, 253, 244, 0.4);
      --privacy-box-border: #86efac;
    }

    body.dark-mode {
      --bg-page: #0b1120;
      --bg-card: #1e293b;
      --text-main: #f1f5f9;
      --text-sub: #94a3b8;
      --border-color: #334155;
      --border-dashed: #475569;
      --banner-bg: #172554;
      --banner-border: #1e40af;
      --banner-text: #93c5fd;
      --primary-blue: #3b82f6;
      --primary-hover: #60a5fa;
      --success-border: #4ade80;
      --success-bg: #064e3b;
      --warning-border: #fbbf24;
      --warning-bg: #451a03;
      --box-shadow: 0 2px 4px rgba(0,0,0,0.4);
      --box-shadow-active: 0 0 20px rgba(59, 130, 246, 0.45);
      --connector-color: #94a3b8;
      --connector-active: #60a5fa;
      --lane-bg-1: #1e293b;
      --lane-bg-2: #1e293b;
      --lane-bg-3: #1e293b;
      --privacy-box-bg: rgba(6, 78, 59, 0.2);
      --privacy-box-border: #059669;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background-color: var(--bg-page);
      color: var(--text-main);
      font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: auto;
      transition: background-color 0.3s ease, color 0.3s ease;
      padding-bottom: 40px;
    }

    /* Container */
    .app-container {
      max-width: 1320px;
      margin: 0 auto;
      width: 100%;
      padding: 24px 28px;
      min-width: 1100px;
    }

    /* Top Navigation Header */
    .top-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 16px;
    }

    .title-area h1 {
      font-size: 24px;
      font-weight: 700;
      letter-spacing: -0.02em;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .badge-group {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: var(--text-sub);
    }

    .badge-pill {
      background-color: #dbeafe;
      color: #1e40af;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 4px;
    }

    body.dark-mode .badge-pill {
      background-color: #1e3a8a;
      color: #bfdbfe;
    }

    /* Control Buttons */
    .controls-group {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 1px solid var(--border-color);
      background-color: var(--bg-card);
      color: var(--text-main);
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      padding: 8px 14px;
      transition: all 0.2s ease;
      user-select: none;
      box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }

    .btn:hover {
      background-color: #f1f5f9;
      border-color: #94a3b8;
    }
    body.dark-mode .btn:hover {
      background-color: #334155;
    }

    .btn-icon {
      width: 38px;
      height: 38px;
      padding: 0;
      border-radius: 8px;
    }

    .btn-primary {
      background-color: var(--primary-blue);
      border-color: var(--primary-blue);
      color: #ffffff;
      padding: 8px 18px;
      gap: 6px;
    }

    .btn-primary:hover {
      background-color: var(--primary-hover);
      border-color: var(--primary-hover);
    }

    /* Notification Banner Bar */
    .banner-bar {
      background-color: var(--banner-bg);
      border: 1px solid var(--banner-border);
      border-radius: 8px;
      padding: 12px 20px;
      margin-bottom: 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: var(--banner-text);
      font-size: 14px;
      font-weight: 500;
      box-shadow: 0 1px 2px rgba(0,0,0,0.03);
      transition: all 0.3s ease;
    }

    .banner-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .banner-icon {
      font-size: 16px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }

    .banner-text-content {
      line-height: 1.4;
    }

    .banner-progress {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .progress-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: #cbd5e1;
      transition: all 0.3s;
    }
    .progress-dot.active {
      background-color: var(--primary-blue);
      width: 24px;
      border-radius: 4px;
    }
    .progress-dot.completed {
      background-color: #3b82f6;
    }

    /* Diagram Canvas / Grid */
    .diagram-board {
      position: relative;
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 30px 24px 30px 24px;
      box-shadow: var(--box-shadow);
      margin-bottom: 24px;
      overflow: visible;
    }

    /* SVG Connector Overlay */
    .svg-connectors {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 1;
    }

    .conn-path {
      stroke: var(--connector-color);
      stroke-width: 1.5;
      fill: none;
      transition: stroke 0.3s, stroke-width 0.3s;
    }

    .conn-path.dashed {
      stroke-dasharray: 4, 4;
    }

    .conn-path.active {
      stroke: var(--connector-active);
      stroke-width: 2.2;
      stroke-dasharray: 6, 6;
      animation: dashMove 1s linear infinite;
    }

    @keyframes dashMove {
      from { stroke-dashoffset: 24; }
      to { stroke-dashoffset: 0; }
    }

    .conn-label {
      position: absolute;
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 4px;
      padding: 2px 6px;
      font-size: 11px;
      font-weight: 500;
      color: var(--text-sub);
      white-space: nowrap;
      z-index: 2;
      box-shadow: 0 1px 2px rgba(0,0,0,0.05);
      transition: all 0.3s;
      transform: translate(-50%, -50%);
    }

    .conn-label.active {
      border-color: var(--primary-blue);
      color: var(--primary-blue);
      font-weight: 700;
      transform: translate(-50%, -50%) scale(1.05);
    }

    /* Swimlanes Layout */
    .swimlanes-wrapper {
      position: relative;
      z-index: 2;
      display: flex;
      flex-direction: column;
      gap: 40px;
    }

    .swimlane {
      display: grid;
      grid-template-columns: 140px 1fr;
      align-items: center;
      position: relative;
      min-height: 100px;
    }

    .lane-label-box {
      padding-right: 18px;
    }

    .lane-label-box h3 {
      font-size: 14px;
      font-weight: 700;
      color: var(--text-main);
      margin-bottom: 4px;
    }

    .lane-label-box p {
      font-size: 11px;
      color: var(--text-sub);
      line-height: 1.3;
    }

    .nodes-track {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 20px;
      position: relative;
    }

    /* Privacy Boundary Box (Dashed Box around Local Core) */
    .privacy-boundary {
      position: absolute;
      top: -14px;
      left: -12px;
      right: -12px;
      bottom: -14px;
      border: 2px dashed var(--privacy-box-border);
      background-color: var(--privacy-box-bg);
      border-radius: 12px;
      pointer-events: none;
      z-index: -1;
      transition: all 0.3s;
    }

    .privacy-tag {
      position: absolute;
      top: 10px;
      left: 20px;
      font-size: 11px;
      font-weight: 600;
      color: #15803d;
      display: flex;
      align-items: center;
      gap: 5px;
    }
    body.dark-mode .privacy-tag {
      color: #86efac;
    }

    /* Diagram Node Card */
    .node-card {
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 14px 14px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      text-align: center;
      min-height: 84px;
      cursor: pointer;
      position: relative;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      user-select: none;
    }

    .node-card:hover {
      border-color: #94a3b8;
      transform: translateY(-2px);
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08);
    }

    .node-card.active {
      border-color: var(--primary-blue);
      box-shadow: var(--box-shadow-active);
      transform: translateY(-3px);
      background-color: #f8faff;
    }
    body.dark-mode .node-card.active {
      background-color: #1e3a5f;
    }

    .node-card .title {
      font-size: 13px;
      font-weight: 700;
      color: var(--text-main);
      margin-bottom: 4px;
      letter-spacing: -0.01em;
    }

    .node-card .desc {
      font-size: 11px;
      color: var(--text-sub);
      line-height: 1.3;
    }

    /* Distinct Nodes (Green / Orange) */
    .node-card.node-success {
      border: 2px solid var(--success-border);
      background-color: var(--success-bg);
    }
    .node-card.node-success .title {
      color: #166534;
    }
    body.dark-mode .node-card.node-success .title {
      color: #86efac;
    }

    .node-card.node-warning {
      border: 2px solid var(--warning-border);
      background-color: var(--warning-bg);
    }
    .node-card.node-warning .title {
      color: #9a3412;
    }
    body.dark-mode .node-card.node-warning .title {
      color: #fde68a;
    }

    .node-card.empty-placeholder {
      visibility: hidden;
      border: none;
      box-shadow: none;
      pointer-events: none;
    }

    /* Step Detail Drawer / Info Panel */
    .detail-drawer {
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px 24px;
      box-shadow: var(--box-shadow);
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 24px;
    }

    .drawer-title {
      font-size: 16px;
      font-weight: 700;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .drawer-badge {
      font-size: 12px;
      padding: 2px 8px;
      border-radius: 4px;
      background: #e2e8f0;
      color: #334155;
    }

    .drawer-desc {
      font-size: 13px;
      color: var(--text-sub);
      line-height: 1.6;
      margin-bottom: 12px;
    }

    .drawer-checklist {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .drawer-checklist li {
      font-size: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--text-main);
    }

    .check-icon {
      color: #16a34a;
      font-weight: bold;
    }

    .drawer-stats {
      border-left: 1px solid var(--border-color);
      padding-left: 24px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 12px;
    }

    .stat-item {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .stat-label {
      font-size: 11px;
      color: var(--text-sub);
      text-transform: uppercase;
      font-weight: 600;
    }

    .stat-value {
      font-size: 16px;
      font-weight: 700;
      color: var(--text-main);
    }

    /* Footer Info */
    .footer-bar {
      margin-top: 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      color: var(--text-sub);
      padding: 0 4px;
    }

    .footer-links {
      display: flex;
      gap: 14px;
    }

    .footer-links a {
      color: var(--primary-blue);
      text-decoration: none;
      font-weight: 500;
    }
    .footer-links a:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>

  <div class="app-container">
    <!-- Top Header -->
    <header class="top-header">
      <div class="title-area">
        <h1>StatPro 전체 표준 작업 흐름 (Overall End-to-End Workflow)</h1>
        <div class="badge-group">
          <span class="badge-pill">운영 단계 · 로컬 퍼스트 v1.0</span>
          <span>DESIGN.md &amp; docs/ 기준 · 2026-11-07 KST</span>
        </div>
      </div>

      <!-- Controls -->
      <div class="controls-group">
        <button class="btn btn-icon" id="btnPrev" title="이전 단계 (←)">&lt;</button>
        <button class="btn btn-primary" id="btnPlay" title="자동 재생 / 일시정지 (Space)">
          <span id="playIcon">▷</span> <span id="playText">흐름 재생</span>
        </button>
        <button class="btn btn-icon" id="btnNext" title="다음 단계 (→)">&gt;</button>
        <button class="btn btn-icon" id="btnReset" title="처음으로 되돌리기 (R)">↺</button>
        <button class="btn btn-icon" id="btnTheme" title="다크/라이트 모드 전환">🌙</button>
      </div>
    </header>

    <!-- Notification / Instruction Banner -->
    <div class="banner-bar">
      <div class="banner-left">
        <span class="banner-icon">ℹ️</span>
        <div class="banner-text-content" id="bannerMessage">
          전체 재생을 누르면 데이터 입력부터 통계 판정·보고서 출력까지 단계별로 보여줍니다.
        </div>
      </div>
      <div class="banner-progress" id="progressDots">
        <div class="progress-dot active" data-step="0"></div>
        <div class="progress-dot" data-step="1"></div>
        <div class="progress-dot" data-step="2"></div>
        <div class="progress-dot" data-step="3"></div>
        <div class="progress-dot" data-step="4"></div>
      </div>
    </div>

    <!-- Diagram Canvas Board -->
    <div class="diagram-board" id="diagramBoard">
      <!-- SVG Connectors Layer -->
      <svg class="svg-connectors" id="svgConnectors">
        <defs>
          <marker id="arrowGray" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#64748b" />
          </marker>
          <marker id="arrowBlue" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#2563eb" />
          </marker>
        </defs>

        <!-- Swimlane 1 Horizontal Solid Line -->
        <path id="conn-1-1" class="conn-path" d="M 334 76 L 392 76" marker-end="url(#arrowGray)"></path>
        <path id="conn-1-2" class="conn-path" d="M 570 76 L 628 76" marker-end="url(#arrowGray)"></path>
        <path id="conn-1-3" class="conn-path" d="M 806 76 L 864 76" marker-end="url(#arrowGray)"></path>

        <!-- Vertical Dashed Lines from Row 1 to Row 2 -->
        <path id="conn-v-1" class="conn-path dashed" d="M 245 118 L 245 186" marker-end="url(#arrowGray)"></path>
        <path id="conn-v-2" class="conn-path dashed" d="M 481 118 L 481 186" marker-end="url(#arrowGray)"></path>
        <path id="conn-v-3" class="conn-path dashed" d="M 717 118 L 717 186" marker-end="url(#arrowGray)"></path>
        <path id="conn-v-4" class="conn-path dashed" d="M 953 118 L 953 186" marker-end="url(#arrowGray)"></path>

        <!-- Vertical Dashed Lines from Row 2 to Row 3 -->
        <path id="conn-v2-1" class="conn-path dashed" d="M 245 272 L 245 340" marker-end="url(#arrowGray)"></path>
        <path id="conn-v2-2" class="conn-path dashed" d="M 481 272 L 481 340" marker-end="url(#arrowGray)"></path>
        <path id="conn-v2-3" class="conn-path dashed" d="M 717 272 L 717 340" marker-end="url(#arrowGray)"></path>

        <!-- Row 3 Local Core Horizontal Connections -->
        <path id="conn-3-1" class="conn-path" d="M 334 382 L 392 382" marker-end="url(#arrowGray)"></path>
        <path id="conn-3-2" class="conn-path" d="M 570 382 L 628 382" marker-end="url(#arrowGray)"></path>
        <!-- Branch to Success (Up) and Warning (Down) -->
        <path id="conn-3-branch-up" class="conn-path" d="M 806 365 L 864 365" marker-end="url(#arrowGray)"></path>
        <path id="conn-3-branch-down" class="conn-path" d="M 806 405 L 864 430" marker-end="url(#arrowGray)"></path>

        <!-- Return Line to UI/Report (Vertical dashed up to Row 2 / Row 1) -->
        <path id="conn-v-ret" class="conn-path dashed" d="M 953 336 L 953 274" marker-end="url(#arrowGray)"></path>
      </svg>

      <!-- Badges on Connectors -->
      <div class="conn-label" style="top: 76px; left: 363px;" id="lbl-1-1">전달</div>
      <div class="conn-label" style="top: 76px; left: 599px;" id="lbl-1-2">매핑 확인</div>
      <div class="conn-label" style="top: 76px; left: 835px;" id="lbl-1-3">피드백</div>

      <div class="conn-label" style="top: 152px; left: 245px;" id="lbl-v-1">파일 업로드</div>
      <div class="conn-label" style="top: 152px; left: 481px;" id="lbl-v-2">규격/옵션 설정</div>
      <div class="conn-label" style="top: 152px; left: 717px;" id="lbl-v-3">조치 이력 입력</div>
      <div class="conn-label" style="top: 152px; left: 953px;" id="lbl-v-4">보고서 열람</div>

      <div class="conn-label" style="top: 306px; left: 245px;" id="lbl-v2-1">Polars 파싱</div>
      <div class="conn-label" style="top: 306px; left: 481px;" id="lbl-v2-2">통계 연산 요청</div>
      <div class="conn-label" style="top: 306px; left: 717px;" id="lbl-v2-3">이상 룰 검출</div>

      <div class="conn-label" style="top: 382px; left: 363px;" id="lbl-3-1">무결성 검증</div>
      <div class="conn-label" style="top: 382px; left: 599px;" id="lbl-3-2">관리도 계산</div>

      <div class="conn-label" style="top: 350px; left: 835px;" id="lbl-branch-1">모든 규칙 준수</div>
      <div class="conn-label" style="top: 425px; left: 835px;" id="lbl-branch-2">규격 이탈/특수원인</div>

      <div class="conn-label" style="top: 306px; left: 953px;" id="lbl-v-ret">상태 반영</div>

      <!-- Swimlanes Content -->
      <div class="swimlanes-wrapper">

        <!-- Lane 1: 품질/현장 엔지니어 -->
        <div class="swimlane" id="lane1">
          <div class="lane-label-box">
            <h3>품질·현장 엔지니어</h3>
            <p>측정자 · 분석 담당자<br>품질 보증팀</p>
          </div>
          <div class="nodes-track">
            <div class="node-card" id="node-1-1" data-step="0">
              <div class="title">원천 데이터 준비</div>
              <div class="desc">CSV · XLSX 원본<br>계측기 직접 수집</div>
            </div>
            <div class="node-card" id="node-1-2" data-step="1">
              <div class="title">변수 및 규격 지정</div>
              <div class="desc">특성치(Y) · 구분자(X)<br>LSL / USL 규격 입력</div>
            </div>
            <div class="node-card" id="node-1-3" data-step="2">
              <div class="title">분석 실행 요청</div>
              <div class="desc">정규성 · 관리도<br>공정능력 · Gage R&amp;R</div>
            </div>
            <div class="node-card empty-placeholder"></div>
            <div class="node-card" id="node-1-5" data-step="4">
              <div class="title">품질 판정 보고서 수령</div>
              <div class="desc">단일 HTML 아카이브<br>4K 고해상도 시각화</div>
            </div>
          </div>
        </div>

        <!-- Lane 2: StatPro 로컬 UI 클라이언트 -->
        <div class="swimlane" id="lane2">
          <div class="lane-label-box">
            <h3>StatPro 클라이언트</h3>
            <p>React + Vite<br>127.0.0.1:5173</p>
          </div>
          <div class="nodes-track">
            <div class="node-card" id="node-2-1" data-step="0">
              <div class="title">데이터 임포트 뷰어</div>
              <div class="desc">드래그&amp;드롭 프리뷰<br>인코딩 자동 감지</div>
            </div>
            <div class="node-card" id="node-2-2" data-step="1">
              <div class="title">가상화 그리드 &amp; 검증</div>
              <div class="desc">결측치 0 대체 금지<br>데이터 타입 정합성</div>
            </div>
            <div class="node-card" id="node-2-3" data-step="2">
              <div class="title">인터랙티브 차트</div>
              <div class="desc">Xbar-R/S 관리도<br>히스토그램 커브 매핑</div>
            </div>
            <div class="node-card empty-placeholder"></div>
            <div class="node-card" id="node-2-5" data-step="4">
              <div class="title">보고서 뷰어 &amp; 출력</div>
              <div class="desc">조치 이력 동기화<br>PDF / HTML 내보내기</div>
            </div>
          </div>
        </div>

        <!-- Lane 3: StatPro 분석 엔진 & 보안 스토리지 -->
        <div class="swimlane" id="lane3" style="margin-top: 10px;">
          <div class="lane-label-box">
            <h3>로컬 분석 코어</h3>
            <p>FastAPI · Polars<br>127.0.0.1:8765</p>
          </div>
          <div class="nodes-track" style="position: relative;">
            <!-- Privacy Boundary Box -->
            <div class="privacy-boundary">
              <div class="privacy-tag">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                </svg>
                원천 측정 데이터 및 통계 연산은 이 PC 내부(D:\\StatProData)에서만 100% 처리
              </div>
            </div>

            <div class="node-card" id="node-3-1" data-step="0">
              <div class="title">로컬 파일 파서</div>
              <div class="desc">Polars 고속 파싱<br>SQLite 세션 생성</div>
            </div>
            <div class="node-card" id="node-3-2" data-step="1">
              <div class="title">전처리 &amp; 결측 필터</div>
              <div class="desc">엄격한 결측 격리<br>이상치 사전 스캔</div>
            </div>
            <div class="node-card" id="node-3-3" data-step="2">
              <div class="title">통계 연산 코어</div>
              <div class="desc">Anderson-Darling<br>Nelson 8 Rules · Cpk</div>
            </div>
            <!-- Branch 1 (Success - Up) -->
            <div class="node-card node-success" id="node-3-4-ok" data-step="3" style="position: relative; top: -14px;">
              <div class="title">확정 (공정 안정)</div>
              <div class="desc">Cp/Cpk ≥ 1.33<br>관리상태 유지 승인</div>
            </div>
            <div class="node-card" id="node-3-5" data-step="4">
              <div class="title">로컬 아카이빙</div>
              <div class="desc">Parquet 영구 보존<br>메타데이터 커밋</div>
            </div>

            <!-- Branch 2 (Warning - Down) located below Branch 1 -->
            <div class="node-card node-warning" id="node-3-4-warn" data-step="3" style="grid-column: 4; position: relative; top: 18px; margin-top: -64px;">
              <div class="title">협의 대기 (이상 감지)</div>
              <div class="desc">규격 이탈 or 룰 위배<br>CAPA 원인 분석 요구</div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- Step Detail Explanation Drawer -->
    <div class="detail-drawer" id="detailDrawer">
      <div class="drawer-left">
        <div class="drawer-title">
          <span id="drawerStepTag" class="drawer-badge">Step 1</span>
          <span id="drawerHeading">원천 데이터 로드 및 로컬 세션 초기화</span>
        </div>
        <p class="drawer-desc" id="drawerDescription">
          품질 측정자가 현장 계측기나 CSV/Excel 파일을 업로드하면, 외부 클라우드 전송 없이 로컬 전용 스토리지(D:\StatProData)에 안전하게 격리되어 세션이 생성됩니다.
        </p>
        <ul class="drawer-checklist" id="drawerChecklist">
          <li><span class="check-icon">✓</span> 로컬 파일 시스템 자동 마운트 (D:\StatProData)</li>
          <li><span class="check-icon">✓</span> UTF-8 / CP949 인코딩 무결성 자동 검출</li>
          <li><span class="check-icon">✓</span> 에어갭(Air-gapped) 환경 완전 보장</li>
        </ul>
      </div>

      <div class="drawer-stats">
        <div class="stat-item">
          <span class="stat-label">보안 수준</span>
          <span class="stat-value" id="statSecurity">로컬 전용 (Air-gapped)</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">실행 엔진</span>
          <span class="stat-value" id="statEngine">FastAPI + Polars Core</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">설계 원칙</span>
          <span class="stat-value" id="statRule">DESIGN.md 5-Step 파이프라인</span>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="footer-bar">
      <div>StatPro Architecture &amp; Workflow Motion System · Version 1.0</div>
      <div class="footer-links">
        <a href="javascript:void(0)" onclick="selectStep(0)">1. 데이터 로드</a>
        <a href="javascript:void(0)" onclick="selectStep(1)">2. 규격/전처리</a>
        <a href="javascript:void(0)" onclick="selectStep(2)">3. 통계 연산</a>
        <a href="javascript:void(0)" onclick="selectStep(3)">4. 안정/이상 판정</a>
        <a href="javascript:void(0)" onclick="selectStep(4)">5. 보고서 출력</a>
      </div>
    </footer>
  </div>

  <script>
    // Step Definitions
    const stepsData = [
      {
        step: 0,
        title: "원천 데이터 로드 및 로컬 세션 초기화",
        banner: "Step 1: 측정자가 CSV/Excel을 등록하면 로컬 PC(D:\\StatProData)에 격리 세션이 초기화됩니다.",
        activeNodes: ["node-1-1", "node-2-1", "node-3-1"],
        activeConns: ["conn-v-1", "conn-v2-1"],
        activeLabels: ["lbl-v-1", "lbl-v2-1"],
        desc: "측정자가 CSV/Excel 파일을 드래그하면, 외부 서버 통신 없이 100% 로컬 환경에서 Polars 엔진을 통해 즉각적인 무손실 파싱이 수행됩니다.",
        checklist: [
          "로컬 파일 시스템 자동 마운트 (D:\\\\StatProData)",
          "UTF-8 / CP949 / EUC-KR 인코딩 자동 보정",
          "대용량 측정 행 100만 건 기준 0.5초 이내 즉각 프리뷰"
        ],
        security: "로컬 전용 (Air-gapped)",
        engine: "FastAPI + Polars Parser",
        rule: "DESIGN.md 1단계 (설정/로드)"
      },
      {
        step: 1,
        title: "변수 매핑, 규격 설정 및 결측치 무결성 검증",
        banner: "Step 2: 관리 특성치(Y)와 군(Subgroup)을 매핑하고, 결측치는 절대 0으로 임의 대체하지 않습니다.",
        activeNodes: ["node-1-2", "node-2-2", "node-3-2"],
        activeConns: ["conn-1-1", "conn-v-2", "conn-v2-2", "conn-3-1"],
        activeLabels: ["lbl-1-1", "lbl-v-2", "lbl-v2-2", "lbl-3-1"],
        desc: "엔지니어가 관리한계(UCL/LCL)의 산출 기준과 고객 공학 규격(USL/LSL)을 분리 입력합니다. 통계 왜곡을 유발하는 '결측치 0 자동 대체'는 원천 차단됩니다.",
        checklist: [
          "관리규격(Control Limits)과 엔지니어링 규격(Spec Limits) 엄격한 분리",
          "결측치 임의 0 보정 금지 (Null 격리 처리 및 사용자 확인 토스트)",
          "가상화 테이블 그리드를 통한 고속 정렬 및 실시간 타입 검증"
        ],
        security: "무결성 검증 (Data Integrity)",
        engine: "Virtual Grid + Pydantic Schema",
        rule: "DESIGN.md 2단계 (데이터 검증)"
      },
      {
        step: 2,
        title: "고속 통계 분석 엔진 및 SPC Nelson Rules 가동",
        banner: "Step 3: Anderson-Darling 정규성 검정, Xbar-R/S 관리도 연산 및 8대 Nelson Rules를 실시간 평가합니다.",
        activeNodes: ["node-1-3", "node-2-3", "node-3-3"],
        activeConns: ["conn-1-2", "conn-v-3", "conn-v2-3", "conn-3-2"],
        activeLabels: ["lbl-1-2", "lbl-v-3", "lbl-v2-3", "lbl-3-2"],
        desc: "Scipy 및 최적화된 통계 알고리즘으로 정규성, 공정능력(Cp/Cpk/Pp/Ppk), Gage R&R을 일괄 연산하고, 8가지 Nelson 이상 패턴을 실시간 검출합니다.",
        checklist: [
          "Anderson-Darling (p >= 0.05) 정규분포 적합도 자동 판정",
          "Shewhart & Nelson 8 Rules (1점 3시그마 이탈, 연속 9점 편향 등) 전수 검사",
          "군내 변동(Within) 기반 Cp/Cpk vs 전체 변동(Overall) 기반 Pp/Ppk 산출"
        ],
        security: "고속 인메모리 연산",
        engine: "NumPy / SciPy Vectorized Core",
        rule: "DESIGN.md 3단계 (통계 분석)"
      },
      {
        step: 3,
        title: "공정 안정 판정 분기 (확정 vs 협의 대기/이상 조치)",
        banner: "Step 4: 통계 판정 결과에 따라 공정 안정(확정) 또는 이상 감지(조치 대기) 분기로 즉각 배분됩니다.",
        activeNodes: ["node-3-4-ok", "node-3-4-warn"],
        activeConns: ["conn-3-branch-up", "conn-3-branch-down"],
        activeLabels: ["lbl-branch-1", "lbl-branch-2"],
        desc: "Cpk 1.33 이상이며 관리한계 이탈이 없는 경우 '공정 안정 확정' 처리되며, 규격 이탈이나 특수원인이 발견되면 즉시 경고 토스트와 함께 원인 규명 대기 상태로 전환됩니다.",
        checklist: [
          "정상: Cpk >= 1.33 및 이상원인 부재 -> 표준 작업 유지 확정",
          "이상: 규칙 위배 포인트 붉은 점 하이라이트 및 엔지니어 알림",
          "조치 이력(5Why / CAPA) 입력 폼 활성화 및 세션 로그 기록"
        ],
        security: "품질 리스크 방지 (Fail-safe)",
        engine: "Decision Logic & Alarm Dispatcher",
        rule: "DESIGN.md 4단계 (결과 및 판정)"
      },
      {
        step: 4,
        title: "품질 보고서 수령 및 단일 HTML / 4K 아카이빙",
        banner: "Step 5: 인터랙티브 차트와 조치 이력이 결합된 단일 HTML 보고서가 D:\\StatProData에 영구 저장됩니다.",
        activeNodes: ["node-1-5", "node-2-5", "node-3-5"],
        activeConns: ["conn-1-3", "conn-v-ret", "conn-v-4"],
        activeLabels: ["lbl-1-3", "lbl-v-ret", "lbl-v-4"],
        desc: "외부 의존성이 없는 독립형 인터랙티브 HTML 리포트와 고해상도 4K 차트 이미지가 생성되어, 사내 ERP나 품질 문서 시스템으로 즉시 내보내집니다.",
        checklist: [
          "단일 파일(Self-contained) HTML 리포트 자동 생성",
          "고해상도 Plotly SVG / 4K PNG 차트 원클릭 다운로드",
          "Parquet 압축 스토리지로 로컬 이력 100% 영구 보존"
        ],
        security: "로컬 아카이빙 (Permanent Retention)",
        engine: "Jinja2 Report Generator + Parquet",
        rule: "DESIGN.md 5단계 (최종 보고서)"
      }
    ];

    let currentStep = 0;
    let isPlaying = false;
    let timer = null;

    // DOM Elements
    const btnPlay = document.getElementById('btnPlay');
    const playIcon = document.getElementById('playIcon');
    const playText = document.getElementById('playText');
    const btnPrev = document.getElementById('btnPrev');
    const btnNext = document.getElementById('btnNext');
    const btnReset = document.getElementById('btnReset');
    const btnTheme = document.getElementById('btnTheme');
    const bannerMsg = document.getElementById('bannerMessage');
    const dots = document.querySelectorAll('.progress-dot');

    const drawerStepTag = document.getElementById('drawerStepTag');
    const drawerHeading = document.getElementById('drawerHeading');
    const drawerDesc = document.getElementById('drawerDescription');
    const drawerChecklist = document.getElementById('drawerChecklist');
    const statSecurity = document.getElementById('statSecurity');
    const statEngine = document.getElementById('statEngine');
    const statRule = document.getElementById('statRule');

    function updateView() {
      const data = stepsData[currentStep];

      // Reset all active classes
      document.querySelectorAll('.node-card').forEach(n => n.classList.remove('active'));
      document.querySelectorAll('.conn-path').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.conn-label').forEach(l => l.classList.remove('active'));

      // Highlight active nodes
      data.activeNodes.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.add('active');
      });

      // Highlight active connectors & markers
      data.activeConns.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
          el.classList.add('active');
          el.setAttribute('marker-end', 'url(#arrowBlue)');
        }
      });
      // Reset non-active markers
      document.querySelectorAll('.conn-path:not(.active)').forEach(p => {
        p.setAttribute('marker-end', 'url(#arrowGray)');
      });

      // Highlight active labels
      data.activeLabels.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.add('active');
      });

      // Update banner
      bannerMsg.textContent = data.banner;

      // Update progress dots
      dots.forEach((dot, idx) => {
        dot.classList.remove('active', 'completed');
        if (idx === currentStep) {
          dot.classList.add('active');
        } else if (idx < currentStep) {
          dot.classList.add('completed');
        }
      });

      // Update detail drawer
      drawerStepTag.textContent = `Step ${data.step + 1}`;
      drawerHeading.textContent = data.title;
      drawerDesc.textContent = data.desc;
      statSecurity.textContent = data.security;
      statEngine.textContent = data.engine;
      statRule.textContent = data.rule;

      drawerChecklist.innerHTML = "";
      data.checklist.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `<span class="check-icon">✓</span> ${item}`;
        drawerChecklist.appendChild(li);
      });
    }

    function selectStep(stepIndex) {
      currentStep = stepIndex;
      updateView();
    }

    function nextStep() {
      currentStep = (currentStep + 1) % stepsData.length;
      updateView();
    }

    function prevStep() {
      currentStep = (currentStep - 1 + stepsData.length) % stepsData.length;
      updateView();
    }

    function togglePlay() {
      if (isPlaying) {
        clearInterval(timer);
        isPlaying = false;
        playIcon.textContent = "▷";
        playText.textContent = "흐름 재생";
        btnPlay.classList.remove('btn-pause');
      } else {
        isPlaying = true;
        playIcon.textContent = "❚❚";
        playText.textContent = "일시 정지";
        timer = setInterval(() => {
          if (currentStep >= stepsData.length - 1) {
            currentStep = 0;
          } else {
            currentStep++;
          }
          updateView();
        }, 3200);
      }
    }

    function resetWorkflow() {
      if (isPlaying) togglePlay();
      currentStep = 0;
      updateView();
    }

    // Attach Click Events to Nodes
    document.querySelectorAll('.node-card[data-step]').forEach(card => {
      card.addEventListener('click', () => {
        const step = parseInt(card.getAttribute('data-step'), 10);
        selectStep(step);
      });
    });

    // Control Listeners
    btnPlay.addEventListener('click', togglePlay);
    btnNext.addEventListener('click', () => {
      if (isPlaying) togglePlay();
      nextStep();
    });
    btnPrev.addEventListener('click', () => {
      if (isPlaying) togglePlay();
      prevStep();
    });
    btnReset.addEventListener('click', resetWorkflow);

    // Dark Mode Toggle
    btnTheme.addEventListener('click', () => {
      document.body.classList.toggle('dark-mode');
      const isDark = document.body.classList.contains('dark-mode');
      btnTheme.textContent = isDark ? "☀️" : "🌙";
    });

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space') {
        e.preventDefault();
        togglePlay();
      } else if (e.code === 'ArrowRight') {
        nextStep();
      } else if (e.code === 'ArrowLeft') {
        prevStep();
      } else if (e.code === 'KeyR') {
        resetWorkflow();
      }
    });

    // Initialize View
    updateView();
  </script>
</body>
</html>
"""

def main():
    target_path = os.path.join("diagrams", "statpro_swimlane_workflow.html")
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print("Generated:", target_path)

    # Artifact copy
    artifact_dir = r"C:\Users\0208m\.gemini\antigravity\brain\3b3a945f-274b-405e-9963-58792169202a"
    artifact_path = os.path.join(artifact_dir, "statpro_swimlane_workflow.html")
    with open(artifact_path, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print("Generated artifact:", artifact_path)

if __name__ == "__main__":
    main()

