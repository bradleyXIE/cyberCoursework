"""Fill the group's Word template with the report markdown.

usage: python fill_template.py TEMPLATE.docx OUT.docx part1.md part2.md ...
Keeps the template cover page, styles and fonts; replaces the placeholder
body; renders headings, paragraphs, bullet/numbered lists, tables, code
blocks and [[FIG:file|caption]] / [[PAGEBREAK]] markers.
"""
import copy
import re
import sys

import docx
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor, Twips

ASSETS = "/Users/xiezhijie/MDX/cyberCoursework/report-assets/"
MEMBERS = [("ZHIJIE XIE", "M01141159"), ("GUL KHALID KHAN I", "M01144661"),
           ("BOON SUNI", "M01155019"), ("ADAM PETER", "M01156859")]
BULLET_NUMID, DECIMAL_NUMID = "5", "1"

tpl, out, parts = sys.argv[1], sys.argv[2], sys.argv[3:]
import os as _os
ZH = _os.environ.get("REPORT_LANG") == "zh"   # Chinese study copy
T = (lambda en, zh: zh if ZH else en)
d = docx.Document(tpl)
body = d.element.body

# ------------------------------------------------------------------ styles
styles_el = d.styles.element


def add_style(xml):
    from lxml import etree
    styles_el.append(etree.fromstring(xml))


W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
add_style(f'<w:style {W} w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/>'
          '<w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:uiPriority w:val="9"/><w:qFormat/>'
          '<w:pPr><w:keepNext/><w:spacing w:before="160" w:after="60"/><w:outlineLvl w:val="2"/></w:pPr>'
          '<w:rPr><w:b/><w:i/><w:sz w:val="22"/></w:rPr></w:style>')
add_style(f'<w:style {W} w:type="paragraph" w:styleId="Caption"><w:name w:val="caption"/>'
          '<w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:jc w:val="center"/><w:spacing w:before="40" w:after="160"/></w:pPr>'
          '<w:rPr><w:i/><w:sz w:val="18"/></w:rPr></w:style>')
add_style(f'<w:style {W} w:type="paragraph" w:customStyle="1" w:styleId="CodeBlock"><w:name w:val="Code Block"/>'
          '<w:basedOn w:val="Normal"/><w:pPr><w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/><w:spacing w:before="0" w:after="0"/></w:pPr>'
          '<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/><w:sz w:val="16"/></w:rPr></w:style>')
for sid, before, after in (("Heading1", 360, 120), ("Heading2", 240, 80)):
    st = d.styles.element.xpath(f'w:style[@w:styleId="{sid}"]')[0]
    ppr = st.find(qn("w:pPr"))
    for tag in ("w:spacing", "w:ind"):
        el = ppr.find(qn(tag))
        if el is not None:
            ppr.remove(el)
    sp = OxmlElement("w:spacing"); sp.set(qn("w:before"), str(before)); sp.set(qn("w:after"), str(after))
    kn = OxmlElement("w:keepNext")
    ppr.insert(0, kn); ppr.append(sp)
if ZH:  # East Asian font for every style that inherits from the defaults
    for rpr in styles_el.xpath("w:docDefaults/w:rPrDefault/w:rPr") + styles_el.xpath('w:style[@w:styleId="Normal"]/w:rPr'):
        rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
        rf.set(qn("w:eastAsia"), "PingFang SC")
# Body text spacing and justification
bt = d.styles["Body Text"]
bt.paragraph_format.space_after = Pt(6)
bt.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# ------------------------------------------------------------------ cover
children = list(body.iterchildren())
first_sect_idx = next(i for i, el in enumerate(children)
                      if el.tag == qn("w:p") and el.find(".//" + qn("w:sectPr")) is not None)
prepared = next(p for p in d.paragraphs if p.text.strip().startswith("Prepared"))


def set_cell_shading(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def set_table_borders(tbl, color="808080"):
    tblPr = tbl._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:space"), "0"); e.set(qn("w:color"), color)
        b.append(e)
    tblPr.append(b)


def add_runs(p, text, size=None, bold=None, color=None):
    pattern = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*)")
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            r = p.add_run(text[pos:m.start()])
            fmt(r, size, bold, color)
        t = m.group(0)
        if t.startswith("**"):
            r = p.add_run(t[2:-2]); fmt(r, size, True, color)
        elif t.startswith("`"):
            r = p.add_run(t[1:-1]); fmt(r, (size or 11) - 1, bold, color); r.font.name = "Consolas"
        else:
            r = p.add_run(t[1:-1]); fmt(r, size, bold, color); r.italic = True
        pos = m.end()
    if pos < len(text):
        r = p.add_run(text[pos:]); fmt(r, size, bold, color)


def fmt(r, size, bold, color):
    if size: r.font.size = Pt(size)
    if bold: r.bold = True
    if color: r.font.color.rgb = RGBColor.from_string(color)


# members table under "Prepared by:"
mt = d.add_table(rows=1 + len(MEMBERS), cols=2)
mt.alignment = WD_TABLE_ALIGNMENT.CENTER
set_table_borders(mt)
for i, (a, b) in enumerate([("Group member", "Student ID")] + MEMBERS):
    for j, v in enumerate((a, b)):
        c = mt.rows[i].cells[j]
        c.width = Inches(2.6 if j == 0 else 1.6)
        c.paragraphs[0].style = d.styles["Table Paragraph"]
        add_runs(c.paragraphs[0], v, size=11, bold=(i == 0), color="FFFFFF" if i == 0 else None)
        if i == 0:
            set_cell_shading(c, "1F3864")
prepared._p.addnext(mt._tbl)
sub = OxmlElement("w:p")
mt._tbl.addnext(sub)
sp = docx.text.paragraph.Paragraph(sub, prepared._parent)
sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_runs(sp, T("Topic: MSS Ltd campus LAN – design, implementation and vulnerability analysis", "主题：MSS Ltd 园区局域网——设计、实施与漏洞分析（中文学习版）"), size=11)
sp2 = OxmlElement("w:p"); sub.addnext(sp2)
sp2 = docx.text.paragraph.Paragraph(sp2, prepared._parent)
sp2.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_runs(sp2, T("Submission: 11 December 2026  ·  Packet Tracer file: CW_CST4562-Implementation.pkt", "提交日期：2026 年 12 月 11 日  ·  Packet Tracer 文件：CW_CST4562-Implementation.pkt"), size=10)

# remove the placeholder body after the cover section (keep final sectPr)
children = list(body.iterchildren())
first_sect_idx = next(i for i, el in enumerate(children)
                      if el.tag == qn("w:p") and el.find(".//" + qn("w:sectPr")) is not None)
final_sect = body.find(qn("w:sectPr"))
for el in children[first_sect_idx + 1:]:
    if el is not final_sect:
        body.remove(el)
# body section geometry: Letter, 1" top/bottom, template side margins
final_sect.find(qn("w:pgMar")).set(qn("w:bottom"), "1080")
final_sect.find(qn("w:pgMar")).set(qn("w:top"), "1080")
CONTENT_IN = (12240 - 1440 - 1080) / 1440  # 6.75 in


def new_par(style="Body Text"):
    p = d.add_paragraph(style=style)  # appended before final sectPr by python-docx
    return p


# footer page numbers on the body section
sec = d.sections[-1]
sec.footer.is_linked_to_previous = False
fp = sec.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
for kind, txt in (("begin", None), ("instr", " PAGE "), ("end", None)):
    r = fp.add_run()
    if kind == "instr":
        it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; r._r.append(it)
    else:
        fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), kind); r._r.append(fc)
    r.font.size = Pt(9)
sec.header.is_linked_to_previous = False
hp = sec.header.paragraphs[0]
hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
add_runs(hp, T("CST4562 Group Coursework – MSS Ltd campus LAN", "CST4562 小组作业 – MSS Ltd 园区局域网（中文学习版）"), size=8, color="7F7F7F")

# contents (Word fills page numbers on open; settings.updateFields is set)
p = new_par("heading 1"); p.add_run(T("Contents", "目录"))
p = new_par("Body Text")
for kind, txt in (("begin", None), ("instr", ' TOC \\o "1-2" \\h \\z \\u '), ("separate", None)):
    r = p.add_run()
    if kind == "instr":
        it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; r._r.append(it)
    else:
        fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), kind); r._r.append(fc)
import json, os
toc_pages = json.load(open(os.environ["TOC_JSON"])) if os.environ.get("TOC_JSON") else {}
heads = []
for f in parts:
    for line in open(f, encoding="utf8"):
        mm = re.match(r"^(#{1,3})\s+(.*)$", line)
        if mm and not line.startswith("# Appendices"):
            heads.append((len(mm.group(1)), mm.group(2).replace("**", "").strip()))
first = True
for lvl, text in heads:
    q = p if first else new_par("Body Text")
    first = False
    q.paragraph_format.space_after = Pt(1)
    q.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if lvl == 3:
        q.paragraph_format.left_indent = Inches(0.3)
    tabs = q.paragraph_format.tab_stops
    from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
    tabs.add_tab_stop(Inches(CONTENT_IN), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    add_runs(q, text + "\t" + str(toc_pages.get(text, "")), size=10.5 if lvl == 3 else 11, bold=(lvl < 3))
    last_toc = q
r = last_toc.add_run(); fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), "end"); r._r.append(fc)
new_par().add_run().add_break(WD_BREAK.PAGE)
s = d.settings.element
uf = OxmlElement("w:updateFields"); uf.set(qn("w:val"), "true"); s.append(uf)

# ------------------------------------------------------------------ markdown
fig_count = 0


def add_table(rows):
    cells = [[c.strip() for c in re.sub(r"^\||\|$", "", r).split("|")] for r in rows]
    head, data = cells[0], cells[2:]
    n = len(head)
    vis = lambda t: sum(2 if ord(ch) > 0x2E80 else 1 for ch in t)   # CJK glyphs are double width
    lens = [min(55, max(5, max(vis(x[i]) if i < len(x) else 0 for x in [head] + data))) for i in range(n)]
    tot = sum(lens)
    t = d.add_table(rows=1 + len(data), cols=n)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    set_table_borders(t, "A6A6A6")
    for ri, row in enumerate([head] + data):
        tr = t.rows[ri]._tr
        trPr = tr.get_or_add_trPr()
        cs = OxmlElement("w:cantSplit"); trPr.append(cs)
        if ri == 0:
            th = OxmlElement("w:tblHeader"); trPr.append(th)
        for ci in range(n):
            c = t.rows[ri].cells[ci]
            c.width = Inches(CONTENT_IN * lens[ci] / tot)
            par = c.paragraphs[0]
            par.style = d.styles["Table Paragraph"]
            par.paragraph_format.space_after = Pt(0)
            add_runs(par, row[ci] if ci < len(row) else "", size=9, bold=(ri == 0), color="FFFFFF" if ri == 0 else None)
            if ri == 0:
                set_cell_shading(c, "1F3864")
    spacer = new_par(); spacer.paragraph_format.space_after = Pt(2)


def add_figure(file, caption):
    global fig_count
    fig_count += 1
    path = ASSETS + file
    from PIL import Image
    w, h = Image.open(path).size
    width = min(CONTENT_IN, 6.5)
    height = width * h / w
    if height > 7.2:
        width = 7.2 * w / h
    p = new_par("Body Text"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Inches(width))
    c = new_par("Caption"); add_runs(c, caption)


def render(md):
    lines = md.replace("\r", "").split("\n")
    i, para = 0, []

    def flush():
        nonlocal para
        if para:
            p = new_par("Body Text"); add_runs(p, " ".join(para)); para = []

    while i < len(lines):
        l = lines[i]
        if l.strip() and not re.match(r"^\s*\d+[.)]\s+", l):
            _num_state["last_kind"] = None
        if not l.strip():
            flush(); i += 1; continue
        if l.startswith("[[PAGEBREAK]]"):
            flush(); new_par().add_run().add_break(WD_BREAK.PAGE); i += 1; continue
        m = re.match(r"^\[\[FIG:([^|\]]+)\|([^\]]+)\]\]", l)
        if m:
            flush(); add_figure(m.group(1).strip(), m.group(2).strip()); i += 1; continue
        m = re.match(r"^(#{1,4})\s+(.*)$", l)
        if m:
            flush()
            lvl = len(m.group(1))
            style = {1: "heading 1", 2: "heading 1", 3: "heading 2", 4: "heading 3"}[lvl]
            text = m.group(2).replace("**", "")
            if lvl == 1:   # Part headings become a coloured banner line
                p = new_par("Title"); add_runs(p, text, size=16, bold=True, color="1F3864")
                p.paragraph_format.keep_with_next = True
                p.paragraph_format.space_before = Pt(6)
            else:
                p = new_par(style); add_runs(p, text)
            i += 1; continue
        if l.startswith("```"):
            flush(); i += 1; code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i]); i += 1
            i += 1
            for k, c in enumerate(code):
                p = new_par("Code Block"); p.add_run(c if c else " ")
                p.paragraph_format.keep_together = True
                if k < len(code) - 1:
                    p.paragraph_format.keep_with_next = True
            new_par().paragraph_format.space_after = Pt(0)
            continue
        if l.strip().startswith("|"):
            flush(); rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip()); i += 1
            if len(rows) >= 2:
                add_table(rows)
            continue
        m = re.match(r"^\s*[-*]\s+(.*)$", l)
        if m:
            flush(); p = new_par("List Paragraph"); add_runs(p, m.group(1)); numbering(p, BULLET_NUMID)
            i += 1; continue
        m = re.match(r"^\s*\d+[.)]\s+(.*)$", l)
        if m:
            flush()
            if _num_state["last_kind"] != "num":
                _num_state["current"] = new_decimal_num()
            p = new_par("List Paragraph"); add_runs(p, m.group(1)); numbering(p, _num_state["current"])
            _num_state["last_kind"] = "num"
            i += 1; continue
        para.append(l.strip()); i += 1
    flush()


_num_state = {"last_kind": None, "current": None}


def new_decimal_num():
    from lxml import etree
    np_el = d.part.numbering_part.element
    ids = [int(x) for x in np_el.xpath("w:num/@w:numId")]
    nid = str(max(ids) + 1)
    np_el.append(etree.fromstring(
        f'<w:num {W} w:numId="{nid}"><w:abstractNumId w:val="4"/>'
        '<w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride></w:num>'))
    return nid


def numbering(p, numid):
    pPr = p._p.get_or_add_pPr()
    numPr = OxmlElement("w:numPr")
    il = OxmlElement("w:ilvl"); il.set(qn("w:val"), "0")
    ni = OxmlElement("w:numId"); ni.set(qn("w:val"), numid)
    numPr.append(il); numPr.append(ni); pPr.append(numPr)
    p.paragraph_format.space_after = Pt(2)


for f in parts:
    render(open(f, encoding="utf8").read())

# restart numbering is not needed; save
d.core_properties.author = "CST4562 group (Xie, Khan, Suni, Peter)"
d.core_properties.title = "MSS Ltd campus LAN - CST4562 group report"
d.save(out)
print("saved", out, "figures:", fig_count)
