# /// script
# dependencies = ["matplotlib", "pillow"]
# ///
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from PIL import Image, ImageDraw
A = "/Users/xiezhijie/MDX/cyberCoursework/report-assets/"

# ---- building / room plan
fig, ax = plt.subplots(figsize=(11, 6.2), dpi=170)
ax.set_xlim(0, 110); ax.set_ylim(0, 64); ax.axis("off")
floors = [
    (2, "Floor 1 - Marketing (VLAN 10)", "20 desks  |  IDF-1 rack: ACC-F1-MKT", "#dbe8f5"),
    (22, "Floor 2 - Sales (VLAN 20)", "25 desks  |  IDF-2 rack: ACC-F2-SALES1 + ACC-F2-SALES2", "#e2f0d9"),
    (42, "Floor 3 - General Support (VLAN 30)", "15 desks  |  IDF-3 rack: ACC-F3-GS", "#fbe5d6"),
]
for y, title, sub, col in floors:
    ax.add_patch(Rectangle((2, y), 78, 18, fc=col, ec="#404040", lw=1.2))
    ax.text(4, y + 15.5, title, fontsize=11, weight="bold")
    ax.text(4, y + 12.6, sub, fontsize=8.5)
    n = {2: 20, 22: 25, 42: 15}[y]
    cols = 10 if n > 15 else 8
    for i in range(n):
        cx = 6 + (i % cols) * 5.2; cy = y + 8.5 - (i // cols) * 3.2
        ax.add_patch(Rectangle((cx, cy), 3.6, 2.0, fc="white", ec="#7f7f7f", lw=0.6))
    ax.add_patch(Rectangle((66, y + 2), 11, 7, fc="#ffffff", ec="#1f4e79", lw=1.4, hatch="//"))
    ax.text(71.5, y + 5.5, "IDF", ha="center", va="center", fontsize=8, weight="bold", color="#1f4e79")
# server room / MDF on floor 1
ax.add_patch(FancyBboxPatch((83, 2), 25, 38, boxstyle="round,pad=0.3", fc="#f2f2f2", ec="#000000", lw=1.5))
ax.text(95.5, 37.2, "Floor 1 secure server room (MDF)", ha="center", fontsize=9, weight="bold")
ax.text(95.5, 34.6, "badge access, UPS, A/B power feeds", ha="center", fontsize=7.5)
racks = [(84.5, 18, "Rack A", "CORE-1, EDGE-1\nDC-SW-A\nINTRANET, MAIL\nDB-MKT, DB-SALES, DB-GS"),
         (96.5, 18, "Rack B", "CORE-2, EDGE-2\nDC-SW-B\nDB-REPLICA\nBACKUP-ARCHIVE\nNMS, ADMIN-PC")]
for x, y, t, body in racks:
    ax.add_patch(Rectangle((x, y - 13), 10.5, 27, fc="white", ec="#548235", lw=1.3))
    ax.text(x + 5.25, y + 11.5, t, ha="center", fontsize=8.5, weight="bold", color="#548235")
    ax.text(x + 5.25, y + 4.5, body, ha="center", va="top", fontsize=6.5, linespacing=1.4)
ax.text(95.5, 3.2, "ISP-A and ISP-B enter via separate ducts", ha="center", fontsize=7)
# risers
for x, lab, col in ((60, "Riser A -> CORE-1", "#c00000"), (63.5, "Riser B -> CORE-2", "#1f4e79")):
    ax.plot([x, x], [6, 58], color=col, lw=2.2, ls="--")
    ax.text(x - 0.6, 60, lab, fontsize=7.5, color=col, rotation=0, ha="center")
for y in (2, 22, 42):
    ax.plot([66, 63.5], [y + 5, y + 5], color="#1f4e79", lw=1.2)
    ax.plot([66, 60], [y + 6.5, y + 6.5], color="#c00000", lw=1.2)
ax.plot([60, 83], [6, 6], color="#c00000", lw=2.2, ls="--")
ax.plot([63.5, 83], [9, 9], color="#1f4e79", lw=2.2, ls="--")
ax.text(2, 62, "MSS Ltd - building and room plan (not to scale). Every IDF is dual-homed to both cores over physically separate risers.",
        fontsize=9, style="italic")
plt.savefig(A + "fig00-building-plan.png", bbox_inches="tight"); plt.close()

# ---- mask lab credentials in the AAA screenshot
im = Image.open(A + "fig14-nms-radius-aaa.jpg").convert("RGB")
w, h = im.size
d = ImageDraw.Draw(im)
# Key column (right side of client table) and Password column (right half of user table)
d.rectangle([int(w * 0.715), int(h * 0.36), int(w * 0.91), int(h * 0.69)], fill=(90, 90, 90))
d.rectangle([int(w * 0.52), int(h * 0.865), int(w * 0.91), int(h * 0.905)], fill=(90, 90, 90))
im.save(A + "fig14-nms-radius-aaa-masked.jpg", quality=92)
print("ok", w, h)
