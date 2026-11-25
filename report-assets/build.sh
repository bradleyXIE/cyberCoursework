#!/bin/bash
set -e
R=/Users/xiezhijie/MDX/cyberCoursework/report-assets
T="/Users/xiezhijie/MDX/cyberCoursework/Coursework Template.docx"
OUT="$1"
W=/private/tmp/claude-501/-Users-xiezhijie-MDX/a4a10621-665b-4e04-a6ae-c6ca5e643bb3/scratchpad/render
MD=""
for f in p1-intro-analysis p1-design-topology-media p1-interconnect-outside-security p1-implementation-future p2-vulns-tools p2-defence-maintenance-appendix refs appendix-evidence appendix-config appendix-activity; do MD="$MD $R/drafts/$f.md"; done
rm -rf "$W"; mkdir -p "$W"
.venv/bin/python fill_template.py "$T" "$W/pass1.docx" $MD >/dev/null
(cd "$W" && timeout 240 soffice --headless --convert-to pdf --outdir . pass1.docx >/dev/null 2>&1)
python3 toc_pages.py "$W/pass1.pdf" "$W/toc.json" $MD
TOC_JSON="$W/toc.json" .venv/bin/python fill_template.py "$T" "$OUT" $MD
cp "$OUT" "$W/final.docx"
(cd "$W" && timeout 240 soffice --headless --convert-to pdf --outdir . final.docx >/dev/null 2>&1)
pdfinfo "$W/final.pdf" | grep Pages
