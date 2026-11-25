"""Apply design.py to a Packet Tracer base file.

usage: python3 build_topology.py BASE.pkt OUT.pkt

BASE.pkt must already contain the physical devices (the GUI-added 3650s,
2911s and servers); this script renames them, re-cables everything, writes
IOS running/startup configuration, VLAN databases, server services, PC
addressing, layout, notes and clusters.
"""
import copy
import sys
import uuid
import xml.etree.ElementTree as ET

import design as D
from ptcodec import decode, encode

SWITCH_MODELS = ("2960-24TT", "3650-24PS")


def text(parent, tag, value):
    el = parent.find(tag)
    if el is None:
        el = ET.SubElement(parent, tag)
    el.text = str(value)
    return el


def ports_of(module, out):
    for p in module.findall("PORT"):
        out.append(p)
    for s in module.findall("SLOT"):
        m = s.find("MODULE")
        if m is not None:
            ports_of(m, out)
    return out


def main(src, dst):
    root = ET.fromstring(decode(open(src, "rb").read()))
    devs = root.find("NETWORK/DEVICES")
    by_name, ref_name = {}, {}
    for d in devs:
        e = d.find("ENGINE")
        ref_name[e.findtext("SAVE_REF_ID")] = e.findtext("NAME")
        by_name[e.findtext("NAME")] = d

    # ---- department membership of the 60 workstations, from the old cabling
    dept_of_switch = {"Switch3": "MKT", "Switch2": "SALES", "Switch5": "SALES", "Switch4": "GS"}
    members = {"MKT": [], "SALES": [], "GS": []}
    for l in root.find("NETWORK/LINKS"):
        c = l.find("CABLE")
        a, b = ref_name[c.findtext("FROM")], ref_name[c.findtext("TO")]
        for x, y in ((a, b), (b, a)):
            if x.startswith("PC") and y in dept_of_switch:
                members[dept_of_switch[y]].append(x)
    key = lambda n: int(n[2:])
    for k in members:
        members[k].sort(key=key)
    assert [len(members[k]) for k in ("MKT", "SALES", "GS")] == [20, 25, 15], members

    # ---- rename devices
    rename = dict(D.RENAME)
    prefix = {"MKT": "MKT-PC", "SALES": "SAL-PC", "GS": "GS-PC"}
    for k, pcs in members.items():
        for i, pc in enumerate(pcs, 1):
            rename[pc] = f"{prefix[k]}{i:02d}"
    for old, new in rename.items():
        d = by_name.pop(old)
        e = d.find("ENGINE")
        e.find("NAME").text = new
        text(e, "SYS_NAME", new)
        by_name[new] = d
    leftovers = [n for n in by_name if not n.startswith("Power Distribution")
                 and n not in rename.values()]
    assert not leftovers, f"unmapped devices: {leftovers}"
    ref = {n: d.find("ENGINE").findtext("SAVE_REF_ID") for n, d in by_name.items()}
    model = {n: d.find("ENGINE/TYPE").get("model") for n, d in by_name.items()}

    # ---- cabling
    pcs = {
        "ACC-F1-MKT": [f"MKT-PC{i:02d}" for i in range(1, 21)],
        "ACC-F2-SALES1": [f"SAL-PC{i:02d}" for i in range(1, 14)],
        "ACC-F2-SALES2": [f"SAL-PC{i:02d}" for i in range(14, 26)],
        "ACC-F3-GS": [f"GS-PC{i:02d}" for i in range(1, 16)],
    }
    linkroot = root.find("NETWORK/LINKS")
    template = copy.deepcopy(linkroot[0])
    for l in list(linkroot):
        linkroot.remove(l)
    seen_ports = set()
    for a, pa, b, pb in D.links(pcs):
        for dev, p in ((a, pa), (b, pb)):
            assert (dev, p) not in seen_ports, (dev, p)
            seen_ports.add((dev, p))
        lk = copy.deepcopy(template)
        c = lk.find("CABLE")
        c.find("FROM").text, c.find("TO").text = ref[a], ref[b]
        p1, p2 = c.findall("PORT")
        p1.text, p2.text = pa, pb
        c.find("LENGTH").text = "3"
        sa, sb = model[a] in SWITCH_MODELS, model[b] in SWITCH_MODELS
        ra, rb = model[a] in ("2911", "2901"), model[b] in ("2911", "2901")
        same = (sa and sb) or (ra and rb)
        c.findall("TYPE")[-1].text = "eCrossOver" if same else "eStraightThrough"
        linkroot.append(lk)

    # ---- IOS devices
    for n, d in by_name.items():
        if model[n] not in ("2960-24TT", "3650-24PS", "2911", "2901"):
            continue
        e = d.find("ENGINE")
        cfg = ["!"] + D.ios_config(n)
        for tag in ("RUNNINGCONFIG", "STARTUPCONFIG"):
            el = e.find(tag)
            for x in list(el):
                el.remove(x)
            for line in cfg:
                ET.SubElement(el, "LINE").text = line
        vl = e.find("VLANS")
        if vl is not None:
            keep = [v for v in vl if v.get("number") in ("1", "1002", "1003", "1004", "1005")]
            for v in list(vl):
                vl.remove(v)
            want = {int(v.get("number")): v for v in keep}
            for vid in D.switch_vlans(n):
                want[vid] = ET.Element("VLAN", {"name": D.VLANS[vid][0], "number": str(vid), "rspan": "0"})
            for vid in sorted(want):
                vl.append(want[vid])

    # ---- end devices
    def set_ip(n, ip, mask, gw, dns, dhcp=False):
        e = by_name[n].find("ENGINE")
        p = ports_of(e.find("MODULE"), [])[0]
        text(p, "PORT_DHCP_ENABLE", "true" if dhcp else "false")
        text(p, "IP", "" if dhcp else ip)
        text(p, "SUBNET", "" if dhcp else mask)
        text(e, "GATEWAY", "" if dhcp else gw)
        dc = e.find("DNS_CLIENT")
        if dc is not None:
            text(dc, "SERVER_IP", "" if dhcp else dns)

    for pclist in pcs.values():
        for pc in pclist:
            set_ip(pc, "", "", "", "", dhcp=True)
    for srv, (vlan, host, _) in D.SERVERS.items():
        set_ip(srv, D.net(vlan, host), "255.255.255.0", D.net(vlan, 1), D.DNS1)
    set_ip("WEB-PUBLIC", "192.0.2.10", "255.255.255.0", "192.0.2.1", "")

    def services(n, http=False, https=False, dns=False, mail=False, ftp=None,
                 syslog=False, ntp=False, aaa=False, page=None):
        e = by_name[n].find("ENGINE")
        if e.find("HTTP_SERVER") is not None:
            text(e.find("HTTP_SERVER"), "ENABLED", int(http))
        if e.find("HTTPS_SERVER") is not None:
            text(e.find("HTTPS_SERVER"), "HTTPSENABLED", int(https))
        ds = e.find("DNS_SERVER")
        if ds is not None:
            text(ds, "ENABLED", int(dns))
            db = ds.find("NAMESERVER-DATABASE")
            for x in list(db):
                db.remove(x)
            if dns:
                for name, ip in D.DNS_RECORDS:
                    rr = ET.SubElement(db, "RESOURCE-RECORD")
                    for t, v in (("TYPE", "A-REC"), ("NAME", name), ("TTL", "86400"), ("IPADDRESS", ip)):
                        ET.SubElement(rr, t).text = v
        es = e.find("EMAIL_SERVER")
        if es is not None:
            for x in list(es):
                es.remove(x)
            for t, v in (("SMTP_ENABLED", int(mail)), ("SMTP_DOMAIN", D.DOMAIN if mail else ""),
                         ("POP3_ENABLED", int(mail)), ("FORWARD_MAIL", 0)):
                ET.SubElement(es, t).text = str(v)
            users = [("marketing", "MssMail-Mkt26"), ("sales", "MssMail-Sal26"),
                     ("support", "MssMail-Gs26"), ("itadmin", "MssMail-Adm26")] if mail else []
            ET.SubElement(es, "NO_OF_USERS").text = str(len(users))
            for i, (u, pw) in enumerate(users):
                ET.SubElement(es, f"USER{i}").text = u
                ET.SubElement(es, f"PASSWORD{i}").text = pw
                ET.SubElement(es, f"NO_OF_MAILS{i}").text = "0"
        fs = e.find("FTP_SERVER")
        if fs is not None:
            text(fs, "ENABLED", int(bool(ftp)))
            um = fs.find("USER_ACCOUNT_MNGR")
            for x in list(um):
                um.remove(x)
            for u, pw in (ftp or []):
                acc = ET.SubElement(um, "ACCOUNT")
                for t, v in (("USERNAME", u), ("PASSWORD", pw), ("PERMISSIONS", "RWNL")):
                    ET.SubElement(acc, t).text = v
        for tag, on in (("SYSLOG_SERVER", syslog), ("NTP_SERVER", ntp)):
            if e.find(tag) is not None:
                text(e.find(tag), "ENABLED", int(on))
        acs = e.find("ACS_SERVER")
        if acs is not None:
            text(acs, "ENABLED", int(aaa))
            for sub in ("USERS", "ACS_CLIENTS"):
                el = acs.find(sub)
                for x in list(el):
                    el.remove(x)
            if aaa:
                u = ET.SubElement(acs.find("USERS"), "USER")
                for t, v in (("NAME", D.ADMIN_USER), ("PASSWORD", D.ADMIN_SECRET), ("DESCRIPTION", "network administrator")):
                    ET.SubElement(u, t).text = v
                clients = [("CORE-1", "10.10.99.2"), ("CORE-2", "10.10.99.3")]
                clients += [(sw, D.net(99, v[1])) for sw, v in D.ACCESS.items()]
                clients += [(sw, D.net(99, v[1])) for sw, v in D.DC.items()]
                for c, _, cip, ed, _, eip in D.TRANSIT:
                    clients.append((ed, eip))
                for cname, ip in clients:
                    cl = ET.SubElement(acs.find("ACS_CLIENTS"), "CLIENT")
                    for t, v in (("HOST_IP", ip), ("KEY", D.RADIUS_KEY), ("DESCRIPTION", cname), ("SERVER_TYPE", "RADIUS")):
                        ET.SubElement(cl, t).text = v
        for dsrv in e.iter("DHCP_SERVER"):
            text(dsrv, "ENABLED", int(n in D.DHCP_SERVERS))
            if n not in D.DHCP_SERVERS:
                continue
            first, count = D.DHCP_SERVERS[n]
            pools = dsrv.find("POOLS")
            tmpl = copy.deepcopy(pools.find("POOL"))
            for x in list(pools):
                pools.remove(x)

            def ip_add(ip, k):
                a = [int(x) for x in ip.split(".")]
                v = (a[0] << 24 | a[1] << 16 | a[2] << 8 | a[3]) + k
                return ".".join(str(v >> sh & 255) for sh in (24, 16, 8, 0))

            # serverPool must exist; it covers the services VLAN the server sits in
            plan = [("serverPool", 40, 200 if n == "INTRANET" else 225, 20)]
            plan += [(f"VLAN{v}-{D.VLANS[v][0]}", v, first, count) for v in D.USER_VLANS]
            for pname, v, start, cnt in plan:
                p = copy.deepcopy(tmpl)
                start_ip = D.net(v, start)
                for t, val in (("NAME", pname), ("NETWORK", D.net(v, 0)), ("MASK", "255.255.255.0"),
                               ("DEFAULT_ROUTER", D.net(v, 1)), ("START_IP", start_ip),
                               ("END_IP", ip_add(start_ip, cnt)), ("DNS_SERVER", D.DNS1),
                               ("MAX_USERS", cnt), ("DOMAIN_NAME", D.DOMAIN)):
                    text(p, t, val)
                pools.append(p)
        if page:
            for f in e.iter("FILE"):
                if f.findtext("NAME") == "index.html":
                    f.find("FILE_CONTENT").find("TEXT").text = page

    def html(title, body):
        return (f"<html><center><font size='+2' color='#1f4e79'>{title}</font></center><hr>"
                f"<p>{body}</p><p><small>MSS Ltd - Packet Tracer simulation</small></p></html>")

    services("INTRANET", https=True, dns=True,
             page=html("MSS Ltd Intranet", "Company news, HR forms and links to the departmental applications. Served over HTTPS only."))
    services("MAIL", dns=True, mail=True)
    for srv, dept in (("DB-MKT", "Marketing"), ("DB-SALES", "Sales"), ("DB-GS", "General Support")):
        services(srv, https=True,
                 page=html(f"{dept} application and database",
                           f"Departmental data set for {dept}. Reachable from all departments over HTTPS; replicated nightly to DB-REPLICA."))
    services("DB-REPLICA", ftp=[("replica", "MssReplica#26")])
    services("BACKUP-ARCHIVE", ftp=[("backup", "MssBackup#26")])
    services("NMS", syslog=True, ntp=True, aaa=True)
    services("WEB-PUBLIC", http=True, https=True,
             page=html("www.public.test", "Simulated public Internet web site. Reaching this page proves NAT and the ISP path work."))

    # ---- layout
    pos = {
        "INET-SW": (700, 20), "WEB-PUBLIC": (830, 20),
        "ISP-A": (560, 95), "ISP-B": (880, 95),
        "EDGE-1": (560, 175), "EDGE-2": (880, 175),
        "CORE-1": (560, 262), "CORE-2": (880, 262),
        "ACC-F1-MKT": (170, 365), "ACC-F2-SALES1": (520, 365),
        "ACC-F2-SALES2": (760, 365), "ACC-F3-GS": (1000, 365),
        "DC-SW-A": (1160, 150), "DC-SW-B": (1160, 400),
        "INTRANET": (1250, 35), "MAIL": (1340, 35),
        "DB-MKT": (1250, 135), "DB-SALES": (1340, 135), "DB-GS": (1295, 225),
        "DB-REPLICA": (1250, 345), "BACKUP-ARCHIVE": (1340, 345),
        "NMS": (1250, 445), "ADMIN-PC": (1340, 445),
    }
    for n, (x, y) in pos.items():
        lg = by_name[n].find("WORKSPACE/LOGICAL")
        lg.find("X").text, lg.find("Y").text = str(x), str(y)
    cl_names = {"General Support": ("F3 General Support - VLAN 30 - 15 PCs", 1000, 470),
                "Marketing": ("F1 Marketing - VLAN 10 - 20 PCs", 170, 470),
                "Sales": ("F2 Sales - VLAN 20 - 25 PCs", 640, 470)}
    for cl in root.iter("CLUSTER"):
        nm = cl.find("NAME")
        if nm is not None and nm.text in cl_names:
            nm.text, x, y = cl_names[nm.text]
            cl.find("X").text, cl.find("Y").text = str(x), str(y)

    # ---- notes and zone boxes
    notes = next(n for n in root.iter("NOTES") if n.find("NOTE") is not None)
    tmpl_note = copy.deepcopy(notes[0])
    for x in list(notes):
        notes.remove(x)
    note_text = [
        (10, 5, "MSS LTD CAMPUS LAN - collapsed core (2x Catalyst 3650: HSRP, LACP, OSPF), dual edge, dual ISP"),
        (10, 25, "VLAN 10 MKT 10.10.10.0/24 | 20 SALES 10.10.20.0/24 | 30 GS 10.10.30.0/24 | gateway .1 = HSRP VIP"),
        (10, 45, "VLAN 40 SERVICES 10.10.40.0/24 | 50 DATA 10.10.50.0/24 | 60 BACKUP 10.10.60.0/24 | 99 MGMT 10.10.99.0/24"),
        (10, 65, "VLAN 900 core transit 10.10.254.0/29 | VLAN 999 native + parked ports | WAN 203.0.113.0/30, 198.51.100.0/30"),
        (300, 88, "SIMULATED ISPs (not MSS-owned)"),
        (300, 168, "EDGE: NAT/PAT + inbound ACL"),
        (300, 188, "EDGE-1 primary, EDGE-2 standby"),
        (300, 290, "CORE-1 HSRP active: VLAN 10/30/50/99"),
        (930, 290, "CORE-2 HSRP active: VLAN 20/40/60"),
        (1130, 5, "SERVER ROOM RACK A - services and data"),
        (1130, 300, "SERVER ROOM RACK B - backup (isolated) + mgmt"),
        (120, 395, "Floor 1 IDF"), (600, 395, "Floor 2 IDF"), (950, 395, "Floor 3 IDF"),
    ]
    for i, (x, y, t) in enumerate(note_text):
        n = copy.deepcopy(tmpl_note)
        n.set("uuid", "{" + str(uuid.UUID(int=0x4D5353000000000000000000 + i)) + "}")
        n.find("X").text, n.find("Y").text, n.find("TEXT").text = str(x), str(y), t
        n.find("Z").text = str(40100 + i)
        notes.append(n)
    rects = root.find("RECTANGLES")
    tmpl_rect = copy.deepcopy(rects[0])
    for x in list(rects):
        rects.remove(x)
    boxes = [(290, 80, 970, 130, "#7f7f7f"), (290, 158, 970, 215, "#c00000"),
             (290, 240, 1110, 310, "#1f4e79"), (1120, 0, 1400, 290, "#548235"),
             (1120, 296, 1400, 520, "#bf8f00")]
    for i, (x1, y1, x2, y2, col) in enumerate(boxes):
        r = copy.deepcopy(tmpl_rect)
        r.set("uuid", "{" + str(uuid.UUID(int=0x4D5352000000000000000000 + i)) + "}")
        r.find("TopLeftX").text, r.find("TopLeftY").text = str(x1), str(y2)
        r.find("BottomRightX").text, r.find("BottomRightY").text = str(x2), str(y1)
        r.find("Filled").set("OUTLINECOLOR", col)
        rects.append(r)

    # ---- history from earlier drafts is not part of the deliverable
    cl = root.find("COMMAND_LOGS")
    if cl is not None:
        for x in list(cl):
            cl.remove(x)

    open(dst, "wb").write(encode(ET.tostring(root)))
    print(f"wrote {dst}: {len(by_name)} devices, {len(linkroot)} links")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
