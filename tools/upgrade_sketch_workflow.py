# -*- coding: utf-8 -*-
"""
Upgrade statpro_sketch_motion_workflow.html:
- Sticky top header (position: sticky; top: 0; z-index: 1000) so controls are ALWAYS visible.
- Complete top control bar:
  1. Prev (⏮️ 이전)
  2. Play / Pause (⏸️ 일시정지 / ▶️ 흐름 재생)
  3. Next (다음 ⏭️)
  4. Reset (🔄 처음부터)
  5. Speed (⚡ 1.0x - cycling 0.5x, 1.0x, 1.5x, 2.0x)
  6. Theme (🌙 / ☀️ - Light / Dark mode toggle)
- Full Dark Mode support for chalkboard / dark notebook mood.
- Dynamically rendered SVG cards adapting to theme.
"""

import re
import shutil

with open('diagrams/statpro_sketch_motion_workflow.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update CSS
# Check if dark-mode is defined
css_patch = """
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
      --header-bg: rgba(252, 249, 242, 0.94);
      --header-border: rgba(30, 58, 138, 0.2);
      --card-bg-white: #FFFFFF;
      --card-bg-subtle: rgba(255, 255, 255, 0.85);
      --dock-bg: #FFFFFF;
      --shadow-color: rgba(30, 58, 138, 0.15);
    }

    body.dark-mode {
      --paper-bg: #0b1120;
      --paper-line: #1e293b;
      --paper-margin: #991b1b;
      --ink-navy: #f8fafc;
      --ink-blue: #60a5fa;
      --ink-light-blue: #93c5fd;
      --ink-red: #f87171;
      --ink-dark: #cbd5e1;
      --ink-gray: #94a3b8;
      --highlight-yellow: rgba(234, 179, 8, 0.25);
      --highlight-blue: rgba(59, 130, 246, 0.25);
      --header-bg: rgba(11, 17, 32, 0.94);
      --header-border: rgba(96, 165, 250, 0.3);
      --card-bg-white: #1e293b;
      --card-bg-subtle: rgba(30, 41, 59, 0.85);
      --dock-bg: #1e293b;
      --shadow-color: rgba(0, 0, 0, 0.4);
    }
"""

# Replace root CSS block
html = re.sub(r':root\s*\{[^}]+\}', css_patch.strip(), html)

# Replace header CSS to be sticky with backdrop filter
header_css = """
    /* Sticky Sketchbook Header (ALWAYS VISIBLE AT TOP) */
    header {
      position: sticky;
      top: 0;
      z-index: 1000;
      background: var(--header-bg);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      padding: 14px 32px 14px 70px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 2px dashed var(--header-border);
      box-shadow: 0 4px 16px var(--shadow-color);
      transition: all 0.25s ease;
    }

    .title-area {
      position: relative;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .main-title {
      font-size: 28px;
      font-weight: 700;
      color: var(--ink-navy);
      letter-spacing: -0.5px;
      display: inline-block;
      position: relative;
    }

    .wavy-underline {
      position: absolute;
      bottom: -6px;
      left: 0;
      width: 100%;
      height: 6px;
    }

    .meta-cloud {
      background: var(--card-bg-white);
      border: 1.5px solid var(--ink-navy);
      border-radius: 14px;
      padding: 3px 12px;
      font-size: 13px;
      color: var(--ink-navy);
      box-shadow: 2px 2px 0px var(--shadow-color);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    /* Player Controller Floating Bar */
    .player-dock {
      background: var(--dock-bg);
      border: 2px solid var(--ink-navy);
      border-radius: 30px;
      padding: 6px 14px;
      box-shadow: 3px 3px 0px var(--shadow-color);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .sketch-btn {
      background: var(--card-bg-white);
      border: 1.5px solid var(--ink-navy);
      border-radius: 16px;
      padding: 5px 12px;
      font-family: var(--font-hand);
      font-size: 16px;
      font-weight: 700;
      color: var(--ink-navy);
      cursor: pointer;
      transition: all 0.15s ease;
      display: flex;
      align-items: center;
      gap: 5px;
      user-select: none;
    }

    .sketch-btn:hover {
      transform: translate(-1px, -2px);
      box-shadow: 2px 2px 0px var(--ink-navy);
      background: var(--highlight-yellow);
    }

    .sketch-btn.primary {
      background: var(--ink-navy);
      color: var(--paper-bg);
      border-color: var(--ink-navy);
    }

    .sketch-btn.primary:hover {
      background: var(--ink-blue);
      color: #FFFFFF;
    }

    .sketch-btn.btn-theme {
      font-size: 17px;
      padding: 5px 10px;
    }
"""

html = re.sub(r'/\* Sketchbook Header \*/[\s\S]*?\.sketch-btn\.primary:hover\s*\{[^}]+\}', header_css.strip(), html)

# Also update timeline-card, narration-box, memo-card to use variables
html = html.replace('.timeline-card {\n      background: #FFFFFF;', '.timeline-card {\n      background: var(--card-bg-white);')
html = html.replace('.narration-box {\n      background: #FFFFFF;', '.narration-box {\n      background: var(--card-bg-white);')
html = html.replace('.memo-card {\n      background: #FEF9C3;', '.memo-card {\n      background: var(--card-bg-white);')

# 2. Update Header HTML Block
new_header_html = """  <!-- Sticky Header with Full Controls -->
  <header>
    <div class="title-area">
      <div class="main-title">
        StatPro 제조·품질 분석 표준 작업 흐름
        <svg class="wavy-underline" viewBox="0 0 400 8" preserveAspectRatio="none">
          <path d="M 0 4 Q 20 0 40 4 T 80 4 T 120 4 T 160 4 T 200 4 T 240 4 T 280 4 T 320 4 T 360 4 T 400 4" fill="none" stroke="#2563EB" stroke-width="3"/>
        </svg>
      </div>
      <div class="meta-cloud">
        <span>☁️ 제조 품질 기준선:</span>
        <strong style="color: var(--ink-blue);">'데이터 ➔ 분석 ➔ 차트 ➔ FMEA ➔ 승인'</strong>
        <span>단일 재현 워크플로우</span>
      </div>
    </div>

    <!-- Player Controls Dock -->
    <div class="player-dock">
      <button class="sketch-btn" onclick="prevStep()" title="이전 단계 (←)">⏮️ 이전</button>
      <button class="sketch-btn primary" id="btnPlay" onclick="togglePlay()" title="흐름 재생 / 일시정지 (Space)">
        <span id="txtPlayIcon">⏸️</span> <span id="txtPlay">일시정지</span>
      </button>
      <button class="sketch-btn" onclick="nextStep()" title="다음 단계 (→)">다음 ⏭️</button>
      <button class="sketch-btn" onclick="restart()" title="처음부터 (R)">🔄 처음부터</button>
      <button class="sketch-btn" id="btnSpeed" onclick="cycleSpeed()" title="재생 속도 조절">⚡ 1.0x</button>
      <button class="sketch-btn btn-theme" id="btnTheme" onclick="toggleTheme()" title="화면 모드 (라이트/다크)">🌙</button>
    </div>
  </header>"""

html = re.sub(r'<!-- Header -->[\s\S]*?</header>', new_header_html, html)

# 3. Update JavaScript Functions
# Update speed & play logic
old_js_funcs = """    // --- Player Control Functions ---
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
    }"""

new_js_funcs = """    // --- Player Control Functions & Speed / Theme Controls ---
    const speeds = [
      { label: "⚡ 0.5x", ms: 4800 },
      { label: "⚡ 1.0x", ms: 2800 },
      { label: "⚡ 1.5x", ms: 1800 },
      { label: "⚡ 2.0x", ms: 1100 }
    ];
    let speedIdx = 1;
    let intervalTime = speeds[1].ms;

    function cycleSpeed() {
      speedIdx = (speedIdx + 1) % speeds.length;
      intervalTime = speeds[speedIdx].ms;
      const b = document.getElementById('btnSpeed');
      if (b) b.textContent = speeds[speedIdx].label;
      if (isPlaying) {
        clearTimeout(timer);
        scheduleNext();
      }
    }

    function toggleTheme() {
      const isDark = document.body.classList.toggle('dark-mode');
      const b = document.getElementById('btnTheme');
      if (b) b.textContent = isDark ? "☀️" : "🌙";
      renderStage();
    }

    function togglePlay() {
      isPlaying = !isPlaying;
      const icon = document.getElementById('txtPlayIcon');
      const txt = document.getElementById('txtPlay');
      if (icon) icon.textContent = isPlaying ? '⏸️' : '▶️';
      if (txt) txt.textContent = isPlaying ? '일시정지' : '흐름 재생';
      if (isPlaying) scheduleNext();
      else clearTimeout(timer);
    }

    function nextStep() {
      currentStep = (currentStep + 1) % SKETCH_STEPS.length;
      renderStage();
      if (isPlaying) scheduleNext();
    }

    function prevStep() {
      currentStep = (currentStep - 1 + SKETCH_STEPS.length) % SKETCH_STEPS.length;
      renderStage();
      if (isPlaying) scheduleNext();
    }

    function jumpToStep(idx) {
      currentStep = idx;
      renderStage();
      if (isPlaying) scheduleNext();
    }

    function restart() {
      currentStep = 0;
      renderStage();
      if (isPlaying) scheduleNext();
    }

    function scheduleNext() {
      clearTimeout(timer);
      if (!isPlaying) return;
      timer = setTimeout(() => {
        currentStep = (currentStep + 1) % SKETCH_STEPS.length;
        renderStage();
        scheduleNext();
      }, intervalTime);
    }"""

html = re.sub(r'// --- Player Control Functions ---[\s\S]*?function scheduleNext\(\)\s*\{[\s\S]*?\}', new_js_funcs, html)

# 4. Update renderStage card background & border colors for dark mode
render_card_match = """        const isActive = idx === cur;
        const cardBg = isActive ? "#FFFFFF" : "rgba(255, 255, 255, 0.75)";
        const borderColor = isActive ? "#2563EB" : "#1E3A8A";
        const borderW = isActive ? 3 : 2;"""

render_card_replacement = """        const isActive = idx === cur;
        const isDark = document.body.classList.contains('dark-mode');
        const cardBg = isDark ? (isActive ? "#1E293B" : "rgba(15, 23, 42, 0.85)") : (isActive ? "#FFFFFF" : "rgba(255, 255, 255, 0.85)");
        const borderColor = isDark ? (isActive ? "#60A5FA" : "#475569") : (isActive ? "#2563EB" : "#1E3A8A");
        const titleColor = isDark ? (isActive ? "#93C5FD" : "#F8FAFC") : (isActive ? "#2563EB" : "#1E3A8A");
        const subColor = isDark ? "#94A3B8" : "#64748B";
        const borderW = isActive ? 3 : 2;"""

html = html.replace(render_card_match, render_card_replacement)
html = html.replace('fill="${isActive ? \'#2563EB\' : \'#1E3A8A\'}">${c.title}', 'fill="${titleColor}">${c.title}')
html = html.replace('fill="#64748B">${c.sub}', 'fill="${subColor}">${c.sub}')

# Clean up duplicate speed event listeners at end of script
html = re.sub(r'const bSpeed = document\.getElementById\(\'btnSpeed\'\);[\s\S]*?if \(bSpeed\) bSpeed\.addEventListener\(\'click\', cycleSpeed\);', '', html)

with open('diagrams/statpro_sketch_motion_workflow.html', 'w', encoding='utf-8') as f:
    f.write(html)

shutil.copyfile('diagrams/statpro_sketch_motion_workflow.html', 'C:/Users/0208m/.gemini/antigravity/brain/3b3a945f-274b-405e-9963-58792169202a/statpro_sketch_motion_workflow.html')
print("Successfully upgraded statpro_sketch_motion_workflow.html!")
