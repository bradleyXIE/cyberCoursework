"""Render chapter 7 terminal screenshots from the lab evidence files.

Each figure is a terminal-style image of text captured by the lab scripts
(vulnerability-lab/run.sh and vulnerability-lab/ch7-tool-examples.sh).
Nothing is retyped: text is read from the evidence files and only cut to
the relevant lines.

usage: <python with pillow> ch7-screenshots.py
"""
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

ROOT = "/Users/xiezhijie/MDX/cyberCoursework"
LAB = os.path.join(ROOT, "vulnerability-lab", "evidence")
OUT = os.path.join(ROOT, "report-assets")
MENLO = "/System/Library/Fonts/Menlo.ttc"

FONT_SIZE = 26          # 2x resolution so the figure stays sharp when scaled to ~6 in
PAD = 36
TITLE_H = 64
LINE_GAP = 8
MAX_CHARS = 96
BG = (255, 255, 255)
BAR = (232, 232, 232)
BORDER = (170, 170, 170)
INK = (30, 30, 30)
PROMPT = (31, 78, 121)
GREY = (110, 110, 110)


def read(path):
    with open(path, encoding="utf8", errors="replace") as fh:
        return fh.read().rstrip("\n").splitlines()


def between(lines, start, stop=None):
    """Lines from the first line containing `start` up to (excluding) the first later line containing `stop`."""
    begin = next(i for i, line in enumerate(lines) if start in line)
    end = len(lines)
    if stop is not None:
        end = next((i for i in range(begin + 1, len(lines)) if stop in lines[i]), len(lines))
    return lines[begin:end]


def wrap(lines):
    out = []
    for line in lines:
        if len(line) <= MAX_CHARS:
            out.append(line)
        else:
            out.extend(textwrap.wrap(line, MAX_CHARS, subsequent_indent="    ",
                                     break_long_words=True, break_on_hyphens=False))
    return out


def render(lines, title, out_name):
    font = ImageFont.truetype(MENLO, FONT_SIZE, index=0)
    # tshark -T fields separates columns with tabs, which Menlo cannot draw; use a visible separator
    lines = wrap([line.replace("\t", " | ").rstrip(" |") for line in lines])
    char_w = font.getlength("M")
    line_h = FONT_SIZE + LINE_GAP
    width = int(char_w * MAX_CHARS + 2 * PAD)
    height = int(TITLE_H + PAD + line_h * len(lines) + PAD)
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width - 1, height - 1], outline=BORDER, width=3)
    draw.rectangle([0, 0, width - 1, TITLE_H], fill=BAR)
    draw.line([0, TITLE_H, width, TITLE_H], fill=BORDER, width=2)
    for i, colour in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        cx = 30 + i * 36
        draw.ellipse([cx - 9, TITLE_H // 2 - 9, cx + 9, TITLE_H // 2 + 9], fill=colour)
    tw = font.getlength(title)
    draw.text(((width - tw) / 2, TITLE_H // 2 - FONT_SIZE / 2 - 2), title, font=font, fill=GREY)
    y = TITLE_H + PAD
    for line in lines:
        colour = PROMPT if line.startswith("$ ") else INK
        draw.text((PAD, y), line, font=font, fill=colour)
        y += line_h
    img.save(os.path.join(OUT, out_name), optimize=True)
    print(out_name, img.size, len(lines), "lines")


def main():
    rerun = os.path.join(LAB, "rerun-20261125")
    ch7 = os.path.join(LAB, "ch7-tools")
    c04 = read(os.path.join(ch7, "C04-tshark-capture-review.txt"))
    e01 = read(os.path.join(rerun, "E01-baseline-nmap.txt"))

    # Figure 7.1 - baseline: PostgreSQL answers on the employee bridge (first Nmap run in E01)
    first_run = e01[:next(i for i in range(1, len(e01)) if e01[i].startswith("Starting Nmap"))]
    render(
        ["$ nmap -sT -sV --version-light -Pn -n --reason -p 5432 172.29.216.20"]
        + [line for line in first_run if line.strip()],
        "kali client on employee bridge (baseline)", "fig7-1-baseline-backup-db-exposed.png")

    # Figure 7.2 - baseline: tshark decodes the bearer token from cleartext HTTP
    render(
        between(c04, "$ tshark -r E03-baseline.pcap", '$ tshark -r E07-hardened.pcap -Y "http.authorization'),
        "tshark on E03-baseline.pcap (25 Nov run)", "fig7-2-baseline-token-in-clear.png")

    # Figure 7.3 - hardened: discovery from the employee segment and the protected segment
    render(
        read(os.path.join(ch7, "C01-discovery-user-segment.txt"))
        + [""]
        + read(os.path.join(ch7, "C02-discovery-protected-segment.txt")),
        "kali client on employee bridge (hardened)", "fig7-3-hardened-discovery.png")

    # Figure 7.4 - hardened: cipher suites offered by the intranet
    render(
        read(os.path.join(ch7, "C03-ssl-enum-ciphers.txt")),
        "nmap ssl-enum-ciphers against the hardened intranet", "fig7-4-ssl-enum-ciphers.png")

    # Figure 7.5 - hardened: capture review shows no HTTP frames and TLS with SNI
    render(
        between(c04, '$ tshark -r E07-hardened.pcap -Y "http.authorization'),
        "tshark on E07-hardened.pcap (25 Nov run)", "fig7-5-hardened-capture-review.png")

    # Figure 7.6 - role-based access control on the export route, hardened lab
    render(
        ["$ curl --cacert lab-ca.pem -H \"Authorization: ...\" https://intranet.lab:8443/... (E06)"]
        + read(os.path.join(rerun, "E06-hardened-https.txt")),
        "curl against the hardened intranet (25 Nov run)", "fig7-6-hardened-access-control.png")


if __name__ == "__main__":
    main()
