"""Write the design tables used by the report (markdown) from design.py."""
import design as D

out = []
out.append("## VLAN and addressing plan\n")
out.append("| VLAN | Name | Subnet | Gateway (HSRP VIP) | CORE-1 / CORE-2 | HSRP active | Purpose |")
out.append("|---|---|---|---|---|---|---|")
for v, (name, base, purpose) in D.VLANS.items():
    if base is None:
        out.append(f"| {v} | {name} | none (not routed) | - | - | - | {purpose} |"); continue
    if v == 900:
        out.append(f"| {v} | {name} | 10.10.254.0/29 | - | 10.10.254.1 / .2 | - | {purpose} |"); continue
    act = "CORE-1" if v in D.ACTIVE["CORE-1"] else "CORE-2"
    out.append(f"| {v} | {name} | {base}/24 | {D.net(v,1)} | {D.net(v,2)} / {D.net(v,3)} | {act} | {purpose} |")
out.append("\n## DHCP scopes (relayed by both cores)\n")
out.append("| Server | VLAN 10 | VLAN 20 | VLAN 30 |\n|---|---|---|---|")
for s, (first, cnt) in D.DHCP_SERVERS.items():
    out.append(f"| {s} ({D.net(40, D.SERVERS[s][1])}) | " + " | ".join(f"{D.net(v, first)}-{D.net(v, first+cnt-1)}" for v in D.USER_VLANS) + " |")
out.append("\n## Servers\n")
out.append("| Server | Address | VLAN | Role | Switch port |\n|---|---|---|---|---|")
port = {srv: f"{sw} {p}" for sw, (_, _, _, m) in D.DC.items() for p, srv, _ in m}
for s, (v, h, role) in D.SERVERS.items():
    out.append(f"| {s} | {D.net(v,h)}/24 | {v} | {role} | {port[s]} |")
out.append("\n## Switch management addresses\n")
out.append("| Switch | Floor / room | Mgmt IP | Uplinks |\n|---|---|---|---|")
for sw, (v, mh, floor, cport, n) in D.ACCESS.items():
    out.append(f"| {sw} | {floor} IDF, {n} workstation ports (VLAN {v}) | {D.net(99,mh)} | Gi0/1->CORE-1 {cport}, Gi0/2->CORE-2 {cport} |")
for sw, (vids, mh, cport, m) in D.DC.items():
    out.append(f"| {sw} | Server room, VLANs {', '.join(map(str, vids))} | {D.net(99,mh)} | Gi0/1->CORE-1 {cport}, Gi0/2->CORE-2 {cport} |")
out.append("\n## Routed links\n")
out.append("| Link | Addresses |\n|---|---|")
for c, cp, cip, e, ep, eip in D.TRANSIT:
    out.append(f"| {c} {cp} - {e} {ep} | {cip} - {eip} /30 |")
for e, (isp, wan, nh, _) in D.EDGE_WAN.items():
    out.append(f"| {e} Gi0/2 - {isp} Gi0/0 | {wan} - {nh} /30 |")
out.append("| CORE-1 - CORE-2 (VLAN 900 over Po1) | 10.10.254.1 - 10.10.254.2 /29 |")
out.append("| Loopbacks (router IDs) | " + ", ".join(f"{k} {v}" for k, v in D.LOOPBACK.items()) + " |")
out.append("\n## ACL USERS-IN (inbound on VLAN 10/20/30 SVIs)\n```\n" + "\n".join(D.USERS_IN) + "\n```")
out.append("\n## ACL BACKUP-OUT (outbound on VLAN 60)\n```\n" + "\n".join(D.BACKUP_OUT) + "\n```")
out.append("\n## ACL MGMT-OUT (outbound on VLAN 99)\n```\n" + "\n".join(D.MGMT_OUT) + "\n```")
out.append("\n## ACL OUTSIDE-IN (inbound on EDGE WAN)\n```\n" + "\n".join(D.OUTSIDE_IN) + "\n```")
open("../../report-assets/design-tables.md", "w").write("\n".join(out) + "\n")
for n in ("CORE-1", "EDGE-1", "ACC-F1-MKT", "DC-SW-B"):
    open(f"../../report-assets/config-{n}.txt", "w").write("\n".join(D.ios_config(n)) + "\n")
print("ok")
