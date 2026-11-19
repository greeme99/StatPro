# -*- coding: utf-8 -*-
"""
Perfect High-Contrast Complementary Dark Mode for statpro_sketch_motion_workflow.html
Addresses user request:
- 전체적으로 완벽한 다크모드 적용 (무채색 회색 박스 제거 -> 딥 슬레이트 칠판/초크 무드)
- 문장, 도형 등 고대비 보색(Complementary Color) 효과 적용으로 100% 가독성 극대화
- 5개 공정 카드의 텍스트, 체크리스트, 파이차트, 기어, 관리도, 도장, 스티커 전면 보색 적용
"""

import re
import shutil

with open('diagrams/statpro_sketch_motion_workflow.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. ENHANCE CSS
css_enhancements = """
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
      --header-bg: rgba(252, 249, 242, 0.96);
      --header-border: rgba(30, 58, 138, 0.2);
      --card-bg-white: #FFFFFF;
      --card-bg-subtle: rgba(255, 255, 255, 0.85);
      --stage-bg: rgba(255, 255, 255, 0.7);
      --stage-border: #1E3A8A;
      --dock-bg: #FFFFFF;
      --shadow-color: rgba(30, 58, 138, 0.15);
    }

    /* COMPREHENSIVE HIGH-CONTRAST CHALKBOARD DARK MODE */
    body.dark-mode {
      --paper-bg: #070B14;
      --paper-line: #162032;
      --paper-margin: #7F1D1D;
      --ink-navy: #F8FAFC;
      --ink-blue: #38BDF8;
      --ink-light-blue: #7DD3FC;
      --ink-red: #F87171;
      --ink-dark: #E2E8F0;
      --ink-gray: #94A3B8;
      --highlight-yellow: rgba(253, 224, 71, 0.2);
      --highlight-blue: rgba(56, 189, 248, 0.2);
      --header-bg: rgba(7, 11, 20, 0.96);
      --header-border: #38BDF8;
      --card-bg-white: #131C2E;
      --card-bg-subtle: rgba(19, 28, 46, 0.85);
      --stage-bg: #0D1424;
      --stage-border: #38BDF8;
      --dock-bg: #131C2E;
      --shadow-color: rgba(0, 0, 0, 0.6);
    }

    body.dark-mode {
      background-color: var(--paper-bg);
      background-image: 
        linear-gradient(90deg, transparent 59px, var(--paper-margin) 60px, transparent 62px),
        repeating-linear-gradient(0deg, transparent, transparent 27px, var(--paper-line) 28px);
      color: var(--ink-navy);
    }

    body.dark-mode .sketch-stage {
      background: var(--stage-bg);
      border: 2px solid var(--stage-border);
      box-shadow: 0 0 25px rgba(56, 189, 248, 0.18), 4px 4px 0px rgba(0, 0, 0, 0.5);
    }

    body.dark-mode .timeline-card {
      background: #111827;
      border: 2px solid #334155;
      box-shadow: 3px 3px 0px rgba(0, 0, 0, 0.4);
    }

    body.dark-mode .timeline-title {
      color: #F8FAFC;
      text-decoration: underline wavy #38BDF8;
    }

    body.dark-mode .narration-box {
      background: #111827;
      border: 2px solid #334155;
      box-shadow: 4px 4px 0px rgba(0, 0, 0, 0.4);
    }

    body.dark-mode .narration-title {
      color: #38BDF8;
    }

    body.dark-mode .narration-text {
      color: #E2E8F0;
    }

    body.dark-mode .sketch-tag-item {
      background: #1E293B;
      border: 1.5px solid #38BDF8;
      color: #7DD3FC;
    }

    body.dark-mode .memo-card {
      background: rgba(245, 158, 11, 0.12);
      border: 2px solid #F59E0B;
      box-shadow: 3px 3px 0px rgba(0, 0, 0, 0.4);
    }

    body.dark-mode .memo-header {
      color: #FDE047;
    }

    body.dark-mode .memo-body {
      color: #FEF08A;
    }

    body.dark-mode .decor-coffee path { stroke: #94A3B8; }
    body.dark-mode .decor-clips path { stroke: #38BDF8; }
    body.dark-mode .decor-pin circle { fill: #F87171; }
    body.dark-mode .decor-pencil polygon { fill: #FBBF24; stroke: #F8FAFC; }
"""

# Replace root & body.dark-mode blocks
html = re.sub(r':root\s*\{[\s\S]*?body\.dark-mode\s*\{[^}]+\}', css_enhancements.strip(), html)

# Ensure sketch-stage uses var(--stage-bg) and var(--stage-border)
stage_css_old = """    /* Canvas Stage Area */
    .sketch-stage {
      background: rgba(255, 255, 255, 0.65);
      border: 2px solid var(--ink-navy);"""

stage_css_new = """    /* Canvas Stage Area */
    .sketch-stage {
      background: var(--stage-bg);
      border: 2px solid var(--stage-border);"""

html = html.replace(stage_css_old, stage_css_new)

# 2. UPDATE renderSvgCanvas / renderStage in SCRIPT
# Replace the card rendering loop and renderCardDoodles completely with high-contrast complementary color logic

card_loop_old = """        html += `
          <g class="doodle-card ${isActive ? 'active' : ''}" onclick="jumpToStep(${idx})" transform="rotate(${rotation} ${c.x + c.w/2} ${c.y + c.h/2})">
            <!-- Sketch Box Shadow and Body -->
            <rect x="${c.x + 4}" y="${c.y + 4}" width="${c.w}" height="${c.h}" rx="14" fill="rgba(30, 58, 138, 0.08)"/>
            <rect x="${c.x}" y="${c.y}" width="${c.w}" height="${c.h}" rx="14" fill="${cardBg}" stroke="${borderColor}" stroke-width="${borderW}"/>
            
            <!-- Header Tape / Title -->
            <path d="M ${c.x + 10} ${c.y + 12} Q ${c.x + c.w/2} ${c.y + 10} ${c.x + c.w - 10} ${c.y + 12}" stroke="${isActive ? '#2563EB' : '#1E3A8A'}" stroke-width="2" fill="none"/>
            <text x="${c.x + c.w/2}" y="${c.y + 36}" text-anchor="middle" font-size="20" font-weight="700" fill="${titleColor}">${c.title}</text>
            <text x="${c.x + c.w/2}" y="${c.y + 56}" text-anchor="middle" font-size="14" fill="${subColor}">${c.sub}</text>
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
        `;"""

card_loop_new = """        const glowShadow = isDark ? (isActive ? 'rgba(56, 189, 248, 0.35)' : 'rgba(0, 0, 0, 0.5)') : 'rgba(30, 58, 138, 0.08)';
        const tapeStroke = isDark ? (isActive ? '#38BDF8' : '#64748B') : (isActive ? '#2563EB' : '#1E3A8A');
        const dashLineStroke = isDark ? '#334155' : '#E2E8F0';

        html += `
          <g class="doodle-card ${isActive ? 'active' : ''}" onclick="jumpToStep(${idx})" transform="rotate(${rotation} ${c.x + c.w/2} ${c.y + c.h/2})">
            <!-- Sketch Box Shadow and Body -->
            <rect x="${c.x + 4}" y="${c.y + 4}" width="${c.w}" height="${c.h}" rx="14" fill="${glowShadow}"/>
            <rect x="${c.x}" y="${c.y}" width="${c.w}" height="${c.h}" rx="14" fill="${cardBg}" stroke="${borderColor}" stroke-width="${borderW}" filter="${isDark && isActive ? 'drop-shadow(0 0 12px rgba(56,189,248,0.5))' : 'none'}"/>
            
            <!-- Header Tape / Title -->
            <path d="M ${c.x + 10} ${c.y + 12} Q ${c.x + c.w/2} ${c.y + 10} ${c.x + c.w - 10} ${c.y + 12}" stroke="${tapeStroke}" stroke-width="2" fill="none"/>
            <text x="${c.x + c.w/2}" y="${c.y + 36}" text-anchor="middle" font-size="20" font-weight="700" fill="${titleColor}">${c.title}</text>
            <text x="${c.x + c.w/2}" y="${c.y + 56}" text-anchor="middle" font-size="14" fill="${subColor}">${c.sub}</text>
            <line x1="${c.x + 15}" y1="${c.y + 66}" x2="${c.x + c.w - 15}" y2="${c.y + 66}" stroke="${dashLineStroke}" stroke-width="1.5" stroke-dasharray="4 2"/>

            <!-- Internal Doodles per Step (WITH HIGH-CONTRAST COMPLEMENTARY COLORS) -->
            ${renderCardDoodles(idx, c.x, c.y, c.w, c.h, isActive, isDark)}

            <!-- Active Highlighter Sticker -->
            ${isActive ? `
              <rect x="${c.x + 16}" y="${c.y + c.h - 38}" width="${c.w - 32}" height="26" rx="13" fill="#DC2626"/>
              <text x="${c.x + c.w/2}" y="${c.y + c.h - 21}" text-anchor="middle" font-size="15" font-weight="700" fill="#FFFFFF">★ 현재 진행 단계 ★</text>
            ` : `
              <rect x="${c.x + 20}" y="${c.y + c.h - 34}" width="${c.w - 40}" height="22" rx="11" fill="${isDark ? 'rgba(255,255,255,0.07)' : '#F1F5F9'}" stroke="${isDark ? '#475569' : '#CBD5E1'}"/>
              <text x="${c.x + c.w/2}" y="${c.y + c.h - 19}" text-anchor="middle" font-size="13" fill="${isDark ? '#CBD5E1' : '#64748B'}">클릭하여 탐색</text>
            `}
          </g>
        `;"""

html = html.replace(card_loop_old, card_loop_new)

# Update connective arrows colors in renderSvgCanvas
arrow_old = """        const strokeColor = isCurrentFlow ? "#DC2626" : (i < cur ? "#2563EB" : "#CBD5E1");
        const strokeW = isCurrentFlow ? 3 : 2;

        html += `
          <!-- Hand drawn wavy arrow -->
          <path d="M ${x1} ${y} Q ${(x1 + x2)/2} ${y - 12} ${x2} ${y}" fill="none" stroke="${strokeColor}" stroke-width="${strokeW}" ${isCurrentFlow ? 'stroke-dasharray="6 4"' : ''} marker-end="${isCurrentFlow ? 'url(#arrowRed)' : 'url(#arrowDoodle)'}"/>
        `;"""

arrow_new = """        const isDark = document.body.classList.contains('dark-mode');
        const arrowInactive = isDark ? "#334155" : "#CBD5E1";
        const arrowPast = isDark ? "#38BDF8" : "#2563EB";
        const arrowActive = isDark ? "#F43F5E" : "#DC2626";
        const strokeColor = isCurrentFlow ? arrowActive : (i < cur ? arrowPast : arrowInactive);
        const strokeW = isCurrentFlow ? 3.5 : 2;

        html += `
          <!-- Hand drawn wavy arrow -->
          <path d="M ${x1} ${y} Q ${(x1 + x2)/2} ${y - 12} ${x2} ${y}" fill="none" stroke="${strokeColor}" stroke-width="${strokeW}" ${isCurrentFlow ? 'stroke-dasharray="6 4"' : ''} marker-end="${isCurrentFlow ? 'url(#arrowRed)' : 'url(#arrowDoodle)'}"/>
        `;"""

html = html.replace(arrow_old, arrow_new)

# Update markers in defs
defs_old = """      let html = `
        <defs>
          <marker id="arrowDoodle" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#2563EB" />
          </marker>
          <marker id="arrowRed" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#DC2626" />
          </marker>
        </defs>
      `;"""

defs_new = """      const isDark = document.body.classList.contains('dark-mode');
      const doodleColor = isDark ? "#38BDF8" : "#2563EB";
      const redColor = isDark ? "#F43F5E" : "#DC2626";

      let html = `
        <defs>
          <marker id="arrowDoodle" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="${doodleColor}" />
          </marker>
          <marker id="arrowRed" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="${redColor}" />
          </marker>
        </defs>
      `;"""

html = html.replace(defs_old, defs_new)

# 3. REWRITE renderCardDoodles COMPLETELY WITH COMPLEMENTARY COLORS
new_doodles_function = """    // --- Specific Doodles Matching Image Style (HIGH CONTRAST & COMPLEMENTARY COLORS) ---
    function renderCardDoodles(idx, x, y, w, h, isActive, isDark) {
      if (idx === 0) {
        // Step 1: People Icons + Checklist
        const personStroke = isDark ? "#38BDF8" : "#1E3A8A";
        const checkRed = isDark ? "#F87171" : "#DC2626";
        const checkBlue = isDark ? "#38BDF8" : "#2563EB";
        const listText = isDark ? "#F1F5F9" : "#1E3A8A";
        const boxStroke = isDark ? "#38BDF8" : "#1E3A8A";

        return `
          <!-- 4 People Sketch -->
          <g transform="translate(${x + 25}, ${y + 80})">
            <!-- Person 1 -->
            <circle cx="20" cy="15" r="7" fill="none" stroke="${personStroke}" stroke-width="2"/>
            <path d="M 12 34 Q 20 25 28 34" fill="none" stroke="${personStroke}" stroke-width="2"/>
            <!-- Person 2 -->
            <circle cx="45" cy="15" r="7" fill="none" stroke="${personStroke}" stroke-width="2"/>
            <path d="M 37 34 Q 45 25 53 34" fill="none" stroke="${personStroke}" stroke-width="2"/>
            <!-- Person 3 -->
            <circle cx="70" cy="15" r="7" fill="none" stroke="${personStroke}" stroke-width="2"/>
            <path d="M 62 34 Q 70 25 78 34" fill="none" stroke="${personStroke}" stroke-width="2"/>
            <!-- Person 4 -->
            <circle cx="95" cy="15" r="7" fill="none" stroke="${personStroke}" stroke-width="2"/>
            <path d="M 87 34 Q 95 25 103 34" fill="none" stroke="${personStroke}" stroke-width="2"/>
            <!-- Checks above heads -->
            <path d="M 16 0 L 19 4 L 26 -2" fill="none" stroke="${checkRed}" stroke-width="2"/>
            <path d="M 41 0 L 44 4 L 51 -2" fill="none" stroke="${checkRed}" stroke-width="2"/>
            <path d="M 66 0 L 69 4 L 76 -2" fill="none" stroke="${checkRed}" stroke-width="2"/>
            <path d="M 91 0 L 94 4 L 101 -2" fill="none" stroke="${checkRed}" stroke-width="2"/>
            <text x="58" y="52" text-anchor="middle" font-size="14" font-weight="700" fill="${checkRed}">전문 엔지니어 참여</text>
          </g>

          <!-- Checklist (Crisp White in Dark Mode) -->
          <g transform="translate(${x + 22}, ${y + 155})" font-size="15" fill="${listText}">
            <rect x="0" y="0" width="16" height="16" fill="none" stroke="${boxStroke}" stroke-width="2"/>
            <path d="M 3 8 L 7 13 L 15 2" fill="none" stroke="${checkBlue}" stroke-width="2.5"/>
            <text x="24" y="14" font-weight="600">실험계획법 (DOE)</text>

            <rect x="0" y="30" width="16" height="16" fill="none" stroke="${boxStroke}" stroke-width="2"/>
            <path d="M 3 38 L 7 43 L 15 32" fill="none" stroke="${checkBlue}" stroke-width="2.5"/>
            <text x="24" y="44" font-weight="600">공정관리 (SPC 7도구)</text>

            <rect x="0" y="60" width="16" height="16" fill="none" stroke="${boxStroke}" stroke-width="2"/>
            <path d="M 3 68 L 7 73 L 15 62" fill="none" stroke="${checkBlue}" stroke-width="2.5"/>
            <text x="24" y="74" font-weight="600">고장분석 (FMEA 7단계)</text>

            <rect x="0" y="90" width="16" height="16" fill="none" stroke="${boxStroke}" stroke-width="2"/>
            <path d="M 3 98 L 7 103 L 15 92" fill="none" stroke="${checkBlue}" stroke-width="2.5"/>
            <text x="24" y="104" font-weight="600">개선 프로젝트 (DMAIC)</text>
          </g>
        `;
      } else if (idx === 1) {
        // Step 2: Pie Chart + SHA-256 Lock + Worksheet Revision
        const pieStroke = isDark ? "#38BDF8" : "#1E3A8A";
        const pieCircleFill = isDark ? "#0A101D" : "#FFFFFF";
        const pieSlice25 = isDark ? "#131C2E" : "#FFFFFF";
        const pieHatch = isDark ? "#38BDF8" : "#2563EB";
        const pieValidText = isDark ? "#FFFFFF" : "#1E3A8A";
        const pieNullText = isDark ? "#FDA4AF" : "#DC2626";

        const lockBoxBg = isDark ? "rgba(245, 158, 11, 0.15)" : "#FEF3C7";
        const lockBoxStroke = isDark ? "#F59E0B" : "#D97706";
        const lockTitle = isDark ? "#FDE047" : "#92400E";
        const lockDesc = isDark ? "#FEF08A" : "#B45309";

        const etagBoxBg = isDark ? "rgba(14, 165, 233, 0.15)" : "#DBEAFE";
        const etagBoxStroke = isDark ? "#38BDF8" : "#2563EB";
        const etagTitle = isDark ? "#7DD3FC" : "#1E40AF";
        const etagDesc = isDark ? "#BAE6FD" : "#1D4ED8";

        return `
          <!-- Hand-Drawn Pie Chart -->
          <g transform="translate(${x + 25}, ${y + 85})">
            <!-- Pie circle -->
            <circle cx="50" cy="50" r="42" fill="${pieCircleFill}" stroke="${pieStroke}" stroke-width="2.5"/>
            <!-- 75% Hatched Area -->
            <path d="M 50 50 L 50 8 A 42 42 0 1 0 92 50 Z" fill="${isDark ? 'rgba(56, 189, 248, 0.25)' : 'rgba(37, 99, 235, 0.15)'}"/>
            <!-- Hatch lines -->
            <line x1="15" y1="35" x2="45" y2="65" stroke="${pieHatch}" stroke-width="1.5"/>
            <line x1="22" y1="20" x2="68" y2="66" stroke="${pieHatch}" stroke-width="1.5"/>
            <line x1="35" y1="12" x2="78" y2="55" stroke="${pieHatch}" stroke-width="1.5"/>
            <!-- Uncut 25% slice -->
            <path d="M 50 50 L 50 8 A 42 42 0 0 1 92 50 Z" fill="${pieSlice25}"/>
            <line x1="50" y1="50" x2="50" y2="8" stroke="${pieStroke}" stroke-width="2.5"/>
            <line x1="50" y1="50" x2="92" y2="50" stroke="${pieStroke}" stroke-width="2.5"/>
            <text x="70" y="32" font-size="12" font-weight="700" fill="${pieNullText}">결측 2%</text>
            <text x="70" y="44" font-size="11" font-weight="600" fill="${pieNullText}">명시보존</text>
            <text x="25" y="70" font-size="13" font-weight="700" fill="${pieValidText}">유효 98%</text>
          </g>

          <!-- Lock & ETag Sketch Box -->
          <g transform="translate(${x + 20}, ${y + 200})">
            <rect x="0" y="0" width="165" height="42" rx="8" fill="${lockBoxBg}" stroke="${lockBoxStroke}" stroke-width="2"/>
            <text x="10" y="20" font-size="14" font-weight="700" fill="${lockTitle}">🔒 SHA-256 Digest 동결</text>
            <text x="10" y="35" font-size="12" font-weight="500" fill="${lockDesc}">Dataset Snapshot 원본 보존</text>

            <rect x="0" y="52" width="165" height="42" rx="8" fill="${etagBoxBg}" stroke="${etagBoxStroke}" stroke-width="2"/>
            <text x="10" y="72" font-size="14" font-weight="700" fill="${etagTitle}">✏️ Worksheet Revision</text>
            <text x="10" y="87" font-size="12" font-weight="500" fill="${etagDesc}">ETag 낙관적 잠금 관리</text>
          </g>
        `;
      } else if (idx === 2) {
        // Step 3: Spinning Gears + FastAPI Engine + Formula Box
        const gear1Fill = isDark ? "#0A101D" : "#FFFFFF";
        const gear1Stroke = isDark ? "#38BDF8" : "#1E3A8A";
        const gear1Center = isDark ? "#0284C7" : "#DBEAFE";
        const gear2Fill = isDark ? "#0A101D" : "#FFFFFF";
        const gear2Stroke = isDark ? "#FBBF24" : "#2563EB";
        const gear2Center = isDark ? "#D97706" : "#FEF08A";

        const engineText = isDark ? "#38BDF8" : "#2563EB";
        const formulaBg = isDark ? "rgba(16, 185, 129, 0.12)" : "#F8FAFC";
        const formulaStroke = isDark ? "#34D399" : "#64748B";
        const formulaTitle = isDark ? "#6EE7B7" : "#1E293B";
        const formulaText = isDark ? "#F8FAFC" : "#334155";

        return `
          <!-- Interlocking Gears -->
          <g transform="translate(${x + w/2}, ${y + 110})">
            <!-- Big Gear (Spinning) -->
            <g class="${isActive ? 'spin-gear' : ''}" style="transform-origin: 0px 0px;">
              <circle cx="0" cy="0" r="26" fill="${gear1Fill}" stroke="${gear1Stroke}" stroke-width="2.5"/>
              <circle cx="0" cy="0" r="10" fill="${gear1Center}" stroke="${gear1Stroke}" stroke-width="2"/>
              <rect x="-4" y="-34" width="8" height="8" fill="${gear1Stroke}"/>
              <rect x="-4" y="26" width="8" height="8" fill="${gear1Stroke}"/>
              <rect x="-34" y="-4" width="8" height="8" fill="${gear1Stroke}"/>
              <rect x="26" y="-4" width="8" height="8" fill="${gear1Stroke}"/>
              <rect x="-24" y="-24" width="8" height="8" fill="${gear1Stroke}" transform="rotate(45)"/>
              <rect x="18" y="18" width="8" height="8" fill="${gear1Stroke}" transform="rotate(45)"/>
              <rect x="-24" y="18" width="8" height="8" fill="${gear1Stroke}" transform="rotate(45)"/>
              <rect x="18" y="-24" width="8" height="8" fill="${gear1Stroke}" transform="rotate(45)"/>
            </g>

            <!-- Small Gear (Opposite Spin) -->
            <g class="${isActive ? 'spin-gear' : ''}" style="transform-origin: 36px 30px; animation-direction: reverse;">
              <circle cx="36" cy="30" r="16" fill="${gear2Fill}" stroke="${gear2Stroke}" stroke-width="2"/>
              <circle cx="36" cy="30" r="6" fill="${gear2Center}" stroke="${gear2Stroke}" stroke-width="1.5"/>
              <rect x="33" y="10" width="6" height="5" fill="${gear2Stroke}"/>
              <rect x="33" y="45" width="6" height="5" fill="${gear2Stroke}"/>
              <rect x="16" y="27" width="5" height="6" fill="${gear2Stroke}"/>
              <rect x="51" y="27" width="5" height="6" fill="${gear2Stroke}"/>
            </g>
          </g>

          <text x="${x + w/2}" y="${y + 185}" text-anchor="middle" font-size="16" font-weight="700" fill="${engineText}">FastAPI :8765 루프백 엔진</text>
          
          <!-- Formula Box -->
          <g transform="translate(${x + 18}, ${y + 205})">
            <rect x="0" y="0" width="170" height="85" rx="10" fill="${formulaBg}" stroke="${formulaStroke}" stroke-width="2" stroke-dasharray="4 2"/>
            <text x="12" y="22" font-size="14" font-weight="700" fill="${formulaTitle}">📊 통계 코어 연산:</text>
            <text x="12" y="42" font-size="13" font-weight="600" fill="${formulaText}">• 완전/일부요인 ANOVA</text>
            <text x="12" y="60" font-size="13" font-weight="600" fill="${formulaText}">• I-MR, Xbar-R, EWMA</text>
            <text x="12" y="78" font-size="13" font-weight="600" fill="${formulaText}">• 균형 교차 Gage R&R</text>
          </g>
        `;
      } else if (idx === 3) {
        // Step 4: Control Chart + Wiggling Alarm Clock (HIGH CONTRAST)
        const chartBg = isDark ? "#080E18" : "#FFFFFF";
        const chartBorder = isDark ? "#38BDF8" : "#1E3A8A";
        const uclColor = isDark ? "#F87171" : "#DC2626";
        const uclText = isDark ? "#FDA4AF" : "#DC2626";
        const clColor = isDark ? "#34D399" : "#16A34A";
        const clText = isDark ? "#6EE7B7" : "#16A34A";
        const polyStroke = isDark ? "#38BDF8" : "#2563EB";
        const outlierDot = isDark ? "#F43F5E" : "#DC2626";
        const outlierText = isDark ? "#FDE047" : "#DC2626";

        const clockBodyFill = isDark ? "#131C2E" : "#FFFFFF";
        const clockStroke = isDark ? "#F87171" : "#DC2626";
        const clockHands = isDark ? "#FFFFFF" : "#1E293B";

        const nelsonText = isDark ? "#F87171" : "#DC2626";
        const signalText = isDark ? "#F1F5F9" : "#1E293B";
        const cpkText = isDark ? "#34D399" : "#059669";

        return `
          <!-- Control Chart Doodle -->
          <g transform="translate(${x + 20}, ${y + 75})">
            <rect x="0" y="0" width="165" height="95" rx="8" fill="${chartBg}" stroke="${chartBorder}" stroke-width="2"/>
            <!-- Limits lines -->
            <line x1="8" y1="20" x2="157" y2="20" stroke="${uclColor}" stroke-width="1.5" stroke-dasharray="4 2"/>
            <text x="135" y="16" font-size="10" font-weight="700" fill="${uclText}">UCL</text>
            <line x1="8" y1="48" x2="157" y2="48" stroke="${clColor}" stroke-width="1.5"/>
            <text x="135" y="44" font-size="10" font-weight="700" fill="${clText}">CL</text>
            <line x1="8" y1="76" x2="157" y2="76" stroke="${uclColor}" stroke-width="1.5" stroke-dasharray="4 2"/>
            <text x="135" y="72" font-size="10" font-weight="700" fill="${uclText}">LCL</text>
            <!-- Plotted line points -->
            <polyline points="15,55 35,42 55,60 75,30 95,50 115,15 135,40" fill="none" stroke="${polyStroke}" stroke-width="2.5"/>
            <circle cx="115" cy="15" r="4.5" fill="${outlierDot}" stroke="#FFFFFF" stroke-width="1.5"/>
            <!-- Outlier callout -->
            <path d="M 115 11 Q 120 2 135 2" fill="none" stroke="${outlierText}" stroke-width="1.5"/>
            <text x="105" y="2" font-size="11" font-weight="800" fill="${outlierText}">Rule 1 이탈!</text>
          </g>

          <!-- Alarm Clock Doodle -->
          <g transform="translate(${x + 35}, ${y + 185})" class="${isActive ? 'alarm-wiggle' : ''}">
            <!-- Clock body -->
            <circle cx="30" cy="30" r="22" fill="${clockBodyFill}" stroke="${clockStroke}" stroke-width="2.5"/>
            <!-- Bells -->
            <path d="M 12 14 Q 10 4 20 10" fill="${clockStroke}"/>
            <path d="M 48 14 Q 50 4 40 10" fill="${clockStroke}"/>
            <!-- Legs -->
            <line x1="16" y1="48" x2="10" y2="56" stroke="${clockStroke}" stroke-width="2.5" stroke-linecap="round"/>
            <line x1="44" y1="48" x2="50" y2="56" stroke="${clockStroke}" stroke-width="2.5" stroke-linecap="round"/>
            <!-- Hands -->
            <line x1="30" y1="30" x2="30" y2="18" stroke="${clockHands}" stroke-width="2" stroke-linecap="round"/>
            <line x1="30" y1="30" x2="40" y2="30" stroke="${clockHands}" stroke-width="2" stroke-linecap="round"/>
            <!-- Sound waves -->
            <path d="M 4 25 Q -4 30 4 35" fill="none" stroke="${clockStroke}" stroke-width="2"/>
            <path d="M 56 25 Q 64 30 56 35" fill="none" stroke="${clockStroke}" stroke-width="2"/>
          </g>

          <g transform="translate(${x + 105}, ${y + 195})">
            <text x="0" y="16" font-size="16" font-weight="800" fill="${nelsonText}">Nelson Rules</text>
            <text x="0" y="34" font-size="14" font-weight="600" fill="${signalText}">8대 이상신호</text>
            <text x="0" y="52" font-size="14" font-weight="800" fill="${cpkText}">Cp/Cpk 판정</text>
          </g>
        `;
      } else {
        // Step 5: Document with Official Stamp + FMEA Link
        const docPaper = isDark ? "#0B1120" : "#FFFFFF";
        const docStroke = isDark ? "#94A3B8" : "#1E3A8A";
        const docCorner = isDark ? "#1E293B" : "#E2E8F0";
        const docLines = isDark ? "#64748B" : "#94A3B8";

        const stampColor = isDark ? "#F87171" : "#DC2626";
        const stampBg = isDark ? "rgba(248, 113, 113, 0.15)" : "rgba(220, 38, 38, 0.08)";

        const evidenceBg = isDark ? "rgba(239, 68, 68, 0.15)" : "#FEE2E2";
        const evidenceStroke = isDark ? "#F87171" : "#DC2626";
        const evidenceTitle = isDark ? "#FCA5A5" : "#991B1B";
        const evidenceDesc = isDark ? "#FECDD3" : "#B91C1C";

        return `
          <!-- Stamped Document -->
          <g transform="translate(${x + 25}, ${y + 80})">
            <!-- Sheet of paper with corner folded -->
            <path d="M 10 0 L 105 0 L 125 20 L 125 140 L 10 140 Z" fill="${docPaper}" stroke="${docStroke}" stroke-width="2.5"/>
            <path d="M 105 0 L 105 20 L 125 20" fill="${docCorner}" stroke="${docStroke}" stroke-width="2"/>
            <!-- Text lines -->
            <line x1="25" y1="30" x2="90" y2="30" stroke="${docLines}" stroke-width="2" stroke-linecap="round"/>
            <line x1="25" y1="45" x2="105" y2="45" stroke="${docLines}" stroke-width="2" stroke-linecap="round"/>
            <line x1="25" y1="60" x2="95" y2="60" stroke="${docLines}" stroke-width="2" stroke-linecap="round"/>
            <line x1="25" y1="75" x2="80" y2="75" stroke="${docLines}" stroke-width="2" stroke-linecap="round"/>

            <!-- Official Stamp (Red Circular Seal) -->
            <g class="${isActive ? 'stamp-pop' : ''}" transform="translate(65, 80) rotate(-10)">
              <circle cx="28" cy="28" r="24" fill="none" stroke="${stampColor}" stroke-width="2.5" stroke-dasharray="3 1"/>
              <circle cx="28" cy="28" r="20" fill="${stampBg}" stroke="${stampColor}" stroke-width="1.5"/>
              <text x="28" y="24" text-anchor="middle" font-size="11" font-weight="700" fill="${stampColor}">AIAG/VDA</text>
              <text x="28" y="37" text-anchor="middle" font-size="12" font-weight="800" fill="${stampColor}">승인 완료</text>
            </g>
          </g>

          <!-- Evidence Ref Box -->
          <g transform="translate(${x + 15}, ${y + 240})">
            <rect x="0" y="0" width="165" height="50" rx="8" fill="${evidenceBg}" stroke="${evidenceStroke}" stroke-width="2"/>
            <text x="8" y="20" font-size="14" font-weight="700" fill="${evidenceTitle}">🔗 Evidence Reference</text>
            <text x="8" y="38" font-size="12" font-weight="600" fill="${evidenceDesc}">FMEA 관리계획서 영구 바인딩</text>
          </g>
        `;
      }
    }"""

# Replace old renderCardDoodles
html = re.sub(r'// --- Specific Doodles Matching Image Style[\s\S]*?function renderCardDoodles\([\s\S]*?\n    \}', new_doodles_function.strip(), html)

# 4. ALSO UPDATE renderTimelineMarkers for Dark Mode
timeline_old = """        const color = isCurrent ? '#DC2626' : (isPassed ? '#2563EB' : '#94A3B8');
        const fill = isCurrent ? '#DC2626' : (isPassed ? '#3B82F6' : '#FFFFFF');

        html += `
          <!-- Marker Circle with Hatch -->
          <circle cx="${s.timelineX}" cy="32" r="${isCurrent ? 12 : 8}" fill="${fill}" stroke="#1E3A8A" stroke-width="2"/>"""

timeline_new = """        const isDark = document.body.classList.contains('dark-mode');
        const markerBorder = isDark ? '#38BDF8' : '#1E3A8A';
        const color = isCurrent ? (isDark ? '#F43F5E' : '#DC2626') : (isPassed ? (isDark ? '#38BDF8' : '#2563EB') : (isDark ? '#475569' : '#94A3B8'));
        const fill = isCurrent ? (isDark ? '#F43F5E' : '#DC2626') : (isPassed ? (isDark ? '#0284C7' : '#3B82F6') : (isDark ? '#0F172A' : '#FFFFFF'));

        html += `
          <!-- Marker Circle with Hatch -->
          <circle cx="${s.timelineX}" cy="32" r="${isCurrent ? 12 : 8}" fill="${fill}" stroke="${markerBorder}" stroke-width="2"/>"""

html = html.replace(timeline_old, timeline_new)

# Save to file
with open('diagrams/statpro_sketch_motion_workflow.html', 'w', encoding='utf-8') as f:
    f.write(html)

shutil.copyfile('diagrams/statpro_sketch_motion_workflow.html', 'C:/Users/0208m/.gemini/antigravity/brain/3b3a945f-274b-405e-9963-58792169202a/statpro_sketch_motion_workflow.html')
print("Successfully written high-contrast complementary dark mode to statpro_sketch_motion_workflow.html!")
