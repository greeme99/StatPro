import os

with open('diagrams/motion_diagram_studio.html', 'r', encoding='utf-8') as f:
    c = f.read()

new_btn = """      <button class="theme-btn active" data-src="statpro_system_and_workflow_motion.html" onclick="switchTheme(this)">
        ⭐ 전체 시스템 구성도 & 업무플로우
      </button>
"""
if 'statpro_system_and_workflow_motion.html' not in c:
    c = c.replace('<button class="theme-btn active"', '<button class="theme-btn"')
    c = c.replace('<div class="theme-selector-group">', '<div class="theme-selector-group">\n' + new_btn)
    c = c.replace('src="statpro_roadmap_workflow.html"', 'src="statpro_system_and_workflow_motion.html"')
    c = c.replace('let currentSrc = "statpro_roadmap_workflow.html";', 'let currentSrc = "statpro_system_and_workflow_motion.html";')
    with open('diagrams/motion_diagram_studio.html', 'w', encoding='utf-8') as f:
        f.write(c)
    art_path = r'C:\Users\0208m\.gemini\antigravity\brain\3b3a945f-274b-405e-9963-58792169202a\motion_diagram_studio.html'
    with open(art_path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('Studio successfully updated with master system view!')
else:
    print('Already present')
