#!/bin/bash
set -e
R=/Users/xiezhijie/MDX/cyberCoursework/report-assets
DRAFTS=${DRAFTS:-drafts}
PY=${PY:-python3}   # needs python-docx and pillow
T="/Users/xiezhijie/MDX/cyberCoursework/Coursework Template.docx"
OUT="$1"
W=${W:-$(mktemp -d)}   # render folder for the intermediate PDF
MD=""
for f in p1-intro-analysis p1-design-topology-media p1-interconnect-outside-security p1-implementation-future p2-vulns-tools p2-defence-maintenance-appendix refs appendix-evidence appendix-config appendix-lab appendix-activity; do MD="$MD $R/$DRAFTS/$f.md"; done
mkdir -p "$W"
"$PY" "$R/fill_template.py" "$T" "$W/pass1.docx" $MD >/dev/null
(cd "$W" && timeout 240 soffice --headless --convert-to pdf --outdir . pass1.docx >/dev/null 2>&1)
python3 "$R/toc_pages.py" "$W/pass1.pdf" "$W/toc.json" $MD
TOC_JSON="$W/toc.json" "$PY" "$R/fill_template.py" "$T" "$OUT" $MD
cp "$OUT" "$W/final.docx"
(cd "$W" && timeout 240 soffice --headless --convert-to pdf --outdir . final.docx >/dev/null 2>&1)
pdfinfo "$W/final.pdf" | grep Pages
