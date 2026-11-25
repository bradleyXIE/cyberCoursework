"""Compare intended IOS lines (design.py) with what Packet Tracer actually kept.

usage: python3 check_config.py SAVED.pkt [device ...]

Packet Tracer silently drops commands it does not support when it replays a
running-config, so any intended line missing from the PT-saved file is either
unsupported or rewritten. Known rewrites (hashed secrets, RSA key generation,
macro commands) are filtered out.
"""
import re
import sys
import xml.etree.ElementTree as ET

import design as D
from ptcodec import decode

REWRITTEN = (
    re.compile(r"^(enable secret|username \S+ privilege 15 secret) "),
    re.compile(r"^crypto key generate"),
    re.compile(r"^radius-server host .* key "),
    re.compile(r"^ip ospf message-digest-key 1 md5 "),
    re.compile(r"^(end|!)$"),
    # IOS defaults that Packet Tracer does not print back
    re.compile(r"^(no shutdown|exec-timeout 10 0|ip ssh authentication-retries 3|no ip http server"
               r"|spanning-tree extend system-id|switchport port-security maximum 1"
               r"|standby \d+ priority 100)$"),
    re.compile(r"^logging host "),   # printed as "logging <ip>"
    re.compile(r"^banner motd "),    # delimiter is re-rendered
    # VLAN definitions live in the VLAN database (checked separately)
    re.compile(r"^(vtp mode transparent|vlan \d+|name \S+)$"),
)


def norm(s):
    return " ".join(s.split())


def main(path, only):
    root = ET.fromstring(decode(open(path, "rb").read()))
    bad = 0
    for d in root.find("NETWORK/DEVICES"):
        e = d.find("ENGINE")
        n = e.findtext("NAME")
        if e.find("TYPE").get("model") not in ("2960-24TT", "3650-24PS", "2911", "2901"):
            continue
        if only and n not in only:
            continue
        raw_saved = [l.text or "" for l in e.find("RUNNINGCONFIG")]
        have = {norm(s) for s in raw_saved}
        # pair sub-commands with their parent so " shutdown" under the wrong port is noticed
        ctx, have_ctx = None, set()
        for s in raw_saved:
            if s.startswith(" "):
                have_ctx.add((ctx, norm(s)))
            elif s.strip() not in ("!", ""):
                ctx = norm(s)
        missing, ctx = [], None
        for raw in D.ios_config(n):
            s = norm(raw)
            if any(r.search(s) for r in REWRITTEN):
                continue
            if raw.startswith(" "):
                if (ctx, s) not in have_ctx:
                    missing.append(f"[{ctx}] {s}")
            else:
                ctx = s
                if s not in have:
                    missing.append(s)
        vl = e.find("VLANS")
        if vl is not None:
            have_v = {int(v.get("number")) for v in vl}
            for vid in D.switch_vlans(n):
                if vid not in have_v:
                    missing.append(f"VLAN {vid} not in VLAN database")
        rsa = e.find("SECURITY")
        rsa_ok = rsa is not None and rsa.findtext("MODULUS_BITS") not in (None, "0")
        need_rsa = not n.startswith(("ISP", "INET"))
        print(f"== {n}: {len(missing)} missing, RSA {'ok' if rsa_ok else ('MISSING' if need_rsa else 'n/a')}")
        uniq = []
        for m in missing:
            key = re.sub(r"(FastEthernet0/|GigabitEthernet1/0/|Vlan)\d+", r"\1N", m)
            if key not in uniq:
                uniq.append(key)
        for m in uniq[:40]:
            print("   ", m)
        bad += len(missing)
    print("total missing", bad)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
