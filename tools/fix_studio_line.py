import shutil

with open('diagrams/motion_diagram_studio.html', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'data-src="statpro_system_and_workflow_motion.html" onclick="switchTheme(this)">\n        🛣️'
replacement = 'data-src="statpro_roadmap_workflow.html" onclick="switchTheme(this)">\n        🛣️'

if target in text:
    text = text.replace(target, replacement)
    print("Found and replaced target!")
else:
    # Try with CRLF
    target_crlf = 'data-src="statpro_system_and_workflow_motion.html" onclick="switchTheme(this)">\r\n        🛣️'
    replacement_crlf = 'data-src="statpro_roadmap_workflow.html" onclick="switchTheme(this)">\r\n        🛣️'
    if target_crlf in text:
        text = text.replace(target_crlf, replacement_crlf)
        print("Found and replaced CRLF target!")

with open('diagrams/motion_diagram_studio.html', 'w', encoding='utf-8') as f:
    f.write(text)

shutil.copy2('diagrams/motion_diagram_studio.html', r'C:\Users\0208m\.gemini\antigravity\brain\3b3a945f-274b-405e-9963-58792169202a\motion_diagram_studio.html')
print("Updated studio successfully.")
