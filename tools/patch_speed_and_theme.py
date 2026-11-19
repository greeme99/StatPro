"""Patch Speed Control (⚡ 0.5x / 1.0x / 1.5x / 2.0x) and Light/Dark Mode

across all motion diagram HTML files.
"""

import os
import re
import shutil

ARTIFACT_DIR = r"C:\Users\0208m\.gemini\antigravity\brain\3b3a945f-274b-405e-9963-58792169202a"

files = [
    "diagrams/statpro_roadmap_workflow.html",
    "diagrams/statpro_hub_workflow.html",
    "diagrams/statpro_interlock_workflow.html",
    "diagrams/statpro_sketch_motion_workflow.html",
    "diagrams/statpro_motion_workflow.html",
    "diagrams/docs_motion_workflow.html"
]

SPEED_CSS = """
    .btn-speed {
      min-width: 74px;
      justify-content: center;
      font-weight: 700;
      color: #2563eb;
      font-size: 12px;
    }
    body.dark-mode .btn-speed {
      color: #38bdf8;
    }
"""

SPEED_LOGIC = """
    const speeds = [
      { label: "⚡ 0.5x", ms: 4800 },
      { label: "⚡ 1.0x", ms: 2800 },
      { label: "⚡ 1.5x", ms: 1800 },
      { label: "⚡ 2.0x", ms: 1100 }
    ];
    let speedIdx = 1;

    function cycleSpeed() {
      speedIdx = (speedIdx + 1) % speeds.length;
      const b = document.getElementById('btnSpeed');
      if (b) b.textContent = speeds[speedIdx].label;
      if (typeof isPlaying !== 'undefined' && isPlaying) {
        clearInterval(timer);
        const stepFn = (typeof nextStep === 'function') ? nextStep : (typeof nextFlow === 'function' ? nextFlow : null);
        if (stepFn) timer = setInterval(stepFn, speeds[speedIdx].ms);
      }
    }
"""

for fpath in files:
    if not os.path.exists(fpath):
        print(f"Skipping missing {fpath}")
        continue

    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add CSS
    if ".btn-speed" not in content:
        content = content.replace("</style>", SPEED_CSS + "\n  </style>")

    # 2. Add Button in controls
    if 'id="btnSpeed"' not in content:
        if 'id="btnReset"' in content:
            content = content.replace(
                '<button class="btn" id="btnReset">',
                '<button class="btn btn-speed" id="btnSpeed" title="재생 속도 조절">⚡ 1.0x</button>\n        <button class="btn" id="btnReset">'
            )
            content = content.replace(
                '<button class="btn btn-icon" id="btnReset"',
                '<button class="btn btn-speed" id="btnSpeed" title="재생 속도 조절">⚡ 1.0x</button>\n        <button class="btn btn-icon" id="btnReset"'
            )
        elif 'id="btnTheme"' in content:
            content = content.replace(
                '<button class="btn',
                '<button class="btn btn-speed" id="btnSpeed" title="재생 속도 조절">⚡ 1.0x</button>\n        <button class="btn',
                1
            )

    # 3. Add JS Speed Logic
    if "const speeds =" not in content:
        content = content.replace("<script>", "<script>\n" + SPEED_LOGIC)

    # 4. Attach event listener
    if "btnSpeed.addEventListener" not in content:
        listener = """
    const bSpeed = document.getElementById('btnSpeed');
    if (bSpeed) bSpeed.addEventListener('click', cycleSpeed);
"""
        content = content.replace("</script>", listener + "\n  </script>")

    # 5. Fix any fixed timer intervals
    content = re.sub(r"timer\s*=\s*setInterval\(([^,]+),\s*\d+\);", r"timer = setInterval(\1, speeds[speedIdx].ms);", content)

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Successfully patched {fpath}")

    # Copy to brain artifact dir
    dest = os.path.join(ARTIFACT_DIR, os.path.basename(fpath))
    shutil.copy2(fpath, dest)
    print(f"Copied to artifact: {dest}")
