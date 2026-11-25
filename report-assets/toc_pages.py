"""Find the page each heading lands on in a rendered PDF -> JSON."""
import json, re, subprocess, sys
pdf, out, mds = sys.argv[1], sys.argv[2], sys.argv[3:]
n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
pages = [subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", pdf, "-"], capture_output=True, text=True).stdout for i in range(1, n + 1)]
norm = lambda s: re.sub(r"\s+", " ", s).strip()
heads = []
for f in mds:
    for line in open(f, encoding="utf8"):
        m = re.match(r"^(#{1,3})\s+(.*)$", line)
        if m: heads.append(m.group(2).replace("**", "").strip())
res, start = {}, 3   # skip cover and contents
for h in heads:
    key = norm(h)[:40]
    for i in range(start - 1, n):
        if key in norm(pages[i]):
            res[h] = i + 1; start = i + 1; break
json.dump(res, open(out, "w"), indent=1)
print(len(res), "of", len(heads))
