import json
import sys
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Usage: python show_bbox_from_json.py <json_path> [page_number]
if len(sys.argv) < 2:
    print("Usage: python show_bbox_from_json.py <json_path> [page_number]")
    sys.exit(1)

json_path = sys.argv[1]
page_number = int(sys.argv[2]) if len(sys.argv) > 2 else None

with open(json_path, encoding="utf-8") as f:
    data = json.load(f)

boxes = []
for el in data.get("elements", []):
    if page_number is not None and el.get("page") != page_number:
        continue
    coords = el.get("coordinates", [])
    if len(coords) == 4:
        xs = [pt["x"] for pt in coords]
        ys = [pt["y"] for pt in coords]
        x1, y1 = min(xs), min(ys)
        x2, y2 = max(xs), max(ys)
        boxes.append((x1, y1, x2, y2, el.get("category", ""), el.get("id", "")))

# 화면(0~1 정규화) 기준으로 bbox 시각화
fig, ax = plt.subplots(figsize=(8, 11))
ax.set_xlim(0, 1)
ax.set_ylim(1, 0)
ax.set_title(f"BBoxes from {json_path}\n(page {page_number if page_number else 'ALL'})")

for x1, y1, x2, y2, cat, eid in boxes:
    rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=2, edgecolor='r', facecolor='none')
    ax.add_patch(rect)
    ax.text(x1, y1, f"{cat}[{eid}]", fontsize=7, color='blue', verticalalignment='top')

plt.xlabel('x (normalized)')
plt.ylabel('y (normalized)')
plt.tight_layout()
plt.show()
