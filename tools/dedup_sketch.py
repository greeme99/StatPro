# -*- coding: utf-8 -*-
import re
import shutil

with open('diagrams/statpro_sketch_motion_workflow.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove the early duplicate block after <script>
early_dup = re.search(r'<script>\s*const speeds = \[[\s\S]*?function cycleSpeed\(\)\s*\{[\s\S]*?\}\s*(?=\/\/\s*---\s*Step Data)', html)
if early_dup:
    html = html.replace(early_dup.group(0), '<script>\n\n    ')
    print("Removed early duplicate speeds/cycleSpeed block!")

with open('diagrams/statpro_sketch_motion_workflow.html', 'w', encoding='utf-8') as f:
    f.write(html)

shutil.copyfile('diagrams/statpro_sketch_motion_workflow.html', 'C:/Users/0208m/.gemini/antigravity/brain/3b3a945f-274b-405e-9963-58792169202a/statpro_sketch_motion_workflow.html')
print("Saved and synced!")
