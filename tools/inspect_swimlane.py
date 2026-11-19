import re

with open('diagrams/statpro_swimlane_workflow.html', 'r', encoding='utf-8') as f:
    text = f.read()

titles = re.findall(r'<div class="title">([^<]+)</div>', text)
print(f"Total titles: {len(titles)}")
for t in titles:
    print(f"- {t}")

lane_headers = re.findall(r'<div class="lane-header">([\s\S]*?)</div>', text)
print(f"\nLane Headers: {len(lane_headers)}")
for h in lane_headers:
    clean = re.sub(r'<[^>]+>', ' ', h).strip()
    print(f"- {clean}")
