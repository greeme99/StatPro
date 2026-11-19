# -*- coding: utf-8 -*-
import re
import shutil

with open('diagrams/statpro_sketch_motion_workflow.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Change line 614 let intervalTime = 5000; to intervalTime = 2800;
# And change line 969 let intervalTime = speeds[1].ms; to intervalTime = speeds[1].ms; (without let)
html = html.replace('let intervalTime = 5000;', 'let intervalTime = 2800;')
html = html.replace('let intervalTime = speeds[1].ms;', 'intervalTime = speeds[1].ms;')

# Fix duplicate closure at scheduleNext
# Check scheduleNext
old_sched = """      timer = setTimeout(() => {
        currentStep = (currentStep + 1) % SKETCH_STEPS.length;
        renderStage();
        scheduleNext();
      }, intervalTime);
    }, intervalTime);"""

new_sched = """      timer = setTimeout(() => {
        currentStep = (currentStep + 1) % SKETCH_STEPS.length;
        renderStage();
        scheduleNext();
      }, intervalTime);"""

html = html.replace(old_sched, new_sched)

with open('diagrams/statpro_sketch_motion_workflow.html', 'w', encoding='utf-8') as f:
    f.write(html)

shutil.copyfile('diagrams/statpro_sketch_motion_workflow.html', 'C:/Users/0208m/.gemini/antigravity/brain/3b3a945f-274b-405e-9963-58792169202a/statpro_sketch_motion_workflow.html')
print("Cleaned up intervalTime and closures!")
