"""MSS Ltd network design: one source of truth for the Packet Tracer build.

Everything the topology needs (device roles, cabling, addressing, VLANs and
per-device IOS configuration) is derived from the tables in this module.
build_topology.py applies it to a Packet Tracer file; docs can be generated
from the same data so the report and the simulation never drift apart.

Credentials below are lab-only values for the simulation.
"""

DOMAIN = "mss.lan"
ADMIN_USER = "netadmin"
ADMIN_SECRET = "MssAdmin#2026"
ENABLE_SECRET = "MssEnable#2026"
OSPF_KEY = "MssOspf2026"
RADIUS_KEY = "MssRadius2026"
NMS_IP = "10.10.99.10"
DNS1, DNS2 = "10.10.40.10", "10.10.40.11"

# ---------------------------------------------------------------- VLAN plan
VLANS = {
    10: ("MARKETING", "10.10.10.0", "F1 Marketing, 20 workstations"),
    20: ("SALES", "10.10.20.0", "F2 Sales, 25 workstations"),
    30: ("GEN-SUPPORT", "10.10.30.0", "F3 General Support, 15 workstations"),
    40: ("SERVICES", "10.10.40.0", "Intranet, e-mail and DNS"),
    50: ("DATA", "10.10.50.0", "Departmental application and database servers"),
    60: ("BACKUP", "10.10.60.0", "Backup database replica and archive (isolated)"),
    99: ("MGMT", "10.10.99.0", "Device management, NMS, admin workstation"),
    900: ("CORE-TRANSIT", "10.10.254.0", "Routed transit between the two cores"),
    999: ("PARKING", None, "Native VLAN and unused ports, never routed"),
}
USER_VLANS = (10, 20, 30)
SERVER_VLANS = (40, 50, 60)
# HSRP active / STP root ownership (load sharing between the two cores)
ACTIVE = {"CORE-1": (10, 30, 50, 99), "CORE-2": (20, 40, 60)}

def net(v, host):
    a, b, c, _ = VLANS[v][1].split(".")
    return f"{a}.{b}.{c}.{host}"

# Central DHCP with relay: both cores forward client broadcasts
# (ip helper-address) to two DHCP servers that lease different halves of each
# user subnet, so either server or either core can fail without stopping
# address assignment. (Packet Tracer's IOS DHCP honours only one
# excluded-address range per subnet, so split scopes on the cores overlap.)
DHCP_SERVERS = {"INTRANET": (11, 120), "MAIL": (131, 120)}   # (first host, lease count)

# ---------------------------------------------------------------- devices
# GUI/legacy device name in the base file -> final name
RENAME = {
    "Multilayer Switch2": "CORE-1", "Multilayer Switch3": "CORE-2",
    "Router2": "EDGE-1", "Router3": "EDGE-2",
    "Router1": "ISP-A", "Router5": "ISP-B",
    "Switch7": "INET-SW", "Simulated-Internet": "WEB-PUBLIC",
    "Switch3": "ACC-F1-MKT", "Switch2": "ACC-F2-SALES1",
    "Switch5": "ACC-F2-SALES2", "Switch4": "ACC-F3-GS",
    "SW-SERVICES": "DC-SW-A", "Switch9": "DC-SW-B",
    "Intranet": "INTRANET", "Mail": "MAIL",
    "SERVER_M": "DB-MKT", "SERVER_S": "DB-SALES", "SERVER_GS": "DB-GS",
    "Server0": "DB-REPLICA", "Backup": "BACKUP-ARCHIVE", "Server1": "NMS",
    "Backup-Console": "ADMIN-PC",
}

ACCESS = {
    # name: (vlan, mgmt host, floor, core port, number of workstations)
    "ACC-F1-MKT": (10, 21, "F1", "GigabitEthernet1/0/1", 20),
    "ACC-F2-SALES1": (20, 22, "F2", "GigabitEthernet1/0/2", 13),
    "ACC-F2-SALES2": (20, 23, "F2", "GigabitEthernet1/0/3", 12),
    "ACC-F3-GS": (30, 24, "F3", "GigabitEthernet1/0/4", 15),
}
DC = {
    # name: (vlans carried, mgmt host, core port, [(port, server, vlan)])
    "DC-SW-A": ((40, 50), 25, "GigabitEthernet1/0/5", [
        ("FastEthernet0/1", "INTRANET", 40), ("FastEthernet0/2", "MAIL", 40),
        ("FastEthernet0/3", "DB-MKT", 50), ("FastEthernet0/4", "DB-SALES", 50),
        ("FastEthernet0/5", "DB-GS", 50)]),
    "DC-SW-B": ((60, 99), 26, "GigabitEthernet1/0/6", [
        ("FastEthernet0/1", "DB-REPLICA", 60), ("FastEthernet0/2", "BACKUP-ARCHIVE", 60),
        ("FastEthernet0/3", "NMS", 99), ("FastEthernet0/4", "ADMIN-PC", 99)]),
}
SERVERS = {
    # name: (vlan, host, role)
    "INTRANET": (40, 10, "Intranet (HTTPS) and primary DNS"),
    "MAIL": (40, 11, "SMTP/POP3 e-mail and secondary DNS"),
    "DB-MKT": (50, 11, "Marketing application and database server"),
    "DB-SALES": (50, 12, "Sales application and database server"),
    "DB-GS": (50, 13, "General Support application and database server"),
    "DB-REPLICA": (60, 10, "Backup database server (replica of all three)"),
    "BACKUP-ARCHIVE": (60, 11, "Backup and archive server (FTP target)"),
    "NMS": (99, 10, "Syslog, NTP and RADIUS AAA"),
    "ADMIN-PC": (99, 50, "Network administrator workstation"),
}
DNS_RECORDS = [
    ("intranet." + DOMAIN, net(40, 10)), ("mail." + DOMAIN, net(40, 11)),
    ("db-marketing." + DOMAIN, net(50, 11)), ("db-sales." + DOMAIN, net(50, 12)),
    ("db-support." + DOMAIN, net(50, 13)), ("www.public.test", "192.0.2.10"),
]

# Routed point-to-point links: (core, core port, core ip, edge, edge port, edge ip)
TRANSIT = [
    ("CORE-1", "GigabitEthernet1/0/21", "10.10.255.1", "EDGE-1", "GigabitEthernet0/0", "10.10.255.2"),
    ("CORE-2", "GigabitEthernet1/0/21", "10.10.255.5", "EDGE-1", "GigabitEthernet0/1", "10.10.255.6"),
    ("CORE-1", "GigabitEthernet1/0/22", "10.10.255.9", "EDGE-2", "GigabitEthernet0/0", "10.10.255.10"),
    ("CORE-2", "GigabitEthernet1/0/22", "10.10.255.13", "EDGE-2", "GigabitEthernet0/1", "10.10.255.14"),
]
LOOPBACK = {"CORE-1": "10.10.0.1", "CORE-2": "10.10.0.2", "EDGE-1": "10.10.0.3", "EDGE-2": "10.10.0.4"}
CORE_TRANSIT_IP = {"CORE-1": "10.10.254.1", "CORE-2": "10.10.254.2"}
EDGE_WAN = {
    # edge: (isp, wan ip, isp ip, OSPF default metric)
    "EDGE-1": ("ISP-A", "203.0.113.2", "203.0.113.1", 10),
    "EDGE-2": ("ISP-B", "198.51.100.2", "198.51.100.1", 50),
}

# ---------------------------------------------------------------- cabling
def links(pcs):
    """Return (a, a_port, b, b_port) tuples. pcs: {access switch: [pc names]}."""
    out = []
    for sw, (_, _, _, cport, _) in ACCESS.items():
        out.append((sw, "GigabitEthernet0/1", "CORE-1", cport))
        out.append((sw, "GigabitEthernet0/2", "CORE-2", cport))
        for i, pc in enumerate(pcs[sw], 1):
            out.append((sw, f"FastEthernet0/{i}", pc, "FastEthernet0"))
    for sw, (_, _, cport, members) in DC.items():
        out.append((sw, "GigabitEthernet0/1", "CORE-1", cport))
        out.append((sw, "GigabitEthernet0/2", "CORE-2", cport))
        for port, srv, _ in members:
            out.append((sw, port, srv, "FastEthernet0"))
    out.append(("CORE-1", "GigabitEthernet1/0/23", "CORE-2", "GigabitEthernet1/0/23"))
    out.append(("CORE-1", "GigabitEthernet1/0/24", "CORE-2", "GigabitEthernet1/0/24"))
    for c, cp, _, e, ep, _ in TRANSIT:
        out.append((c, cp, e, ep))
    out.append(("EDGE-1", "GigabitEthernet0/2", "ISP-A", "GigabitEthernet0/0"))
    out.append(("EDGE-2", "GigabitEthernet0/2", "ISP-B", "GigabitEthernet0/0"))
    out.append(("ISP-A", "GigabitEthernet0/1", "INET-SW", "GigabitEthernet0/1"))
    out.append(("ISP-B", "GigabitEthernet0/1", "INET-SW", "GigabitEthernet0/2"))
    out.append(("WEB-PUBLIC", "FastEthernet0", "INET-SW", "FastEthernet0/1"))
    return out

# ---------------------------------------------------------------- IOS config
def baseline(host, radius=True, platform="router"):
    """Hardening applied to every MSS-owned IOS device."""
    l = [
        "service timestamps log datetime msec",
        "service timestamps debug datetime msec",
        "service password-encryption",
        f"hostname {host}",
        f"enable secret {ENABLE_SECRET}",
        f"username {ADMIN_USER} privilege 15 secret {ADMIN_SECRET}",
        "no ip domain-lookup",
        f"ip domain-name {DOMAIN}",
    ]
    # Packet Tracer's 2960 image rejects these; the 3650 rejects the first.
    if platform == "router":
        l += ["security passwords min-length 10"]
    if platform in ("router", "l3switch"):
        l += ["login block-for 120 attempts 3 within 60"]
    if radius:
        l += [
            "aaa new-model",
            "aaa authentication login default group radius local",
            "aaa authentication login CONSOLE none" if TEST_CONSOLE else "aaa authentication login CONSOLE local",
            f"radius-server host {NMS_IP} auth-port 1645 key {RADIUS_KEY}",
        ]
    l += [
        "crypto key generate rsa general-keys modulus 2048",
        "ip ssh version 2",
        "ip ssh authentication-retries 3",
        "ip ssh time-out 60",
        "no ip http server",
        f"ntp server {NMS_IP}",
        f"logging host {NMS_IP}",
        "banner motd #Authorised access to MSS Ltd network devices only. All sessions are logged.#",
        "access-list 10 remark SSH allowed only from the management VLAN",
        "access-list 10 permit 10.10.99.0 0.0.0.255",
    ]
    return l

import os
# MSS_TEST_CONSOLE=1 builds a verification copy whose console opens straight
# into privileged mode, so show commands can be captured without typing
# credentials. The deliverable is always built without it.
TEST_CONSOLE = os.environ.get("MSS_TEST_CONSOLE") == "1"
# Feature switches used only while isolating Packet Tracer simulator crashes.
DISABLED = set(filter(None, os.environ.get("MSS_DISABLE", "").split(",")))

def _drop(lines):
    rules = {
        "sticky": lambda x: x.strip() == "switchport port-security mac-address sticky",
        "portsec": lambda x: x.strip().startswith("switchport port-security"),
        "dai": lambda x: "arp inspection" in x,
        "snoop": lambda x: "dhcp snooping" in x,
        "lacp": lambda x: x.strip().startswith("channel-group"),
        "rootguard": lambda x: x.strip() == "spanning-tree guard root",
        "bpduguard": lambda x: "bpduguard" in x,
        "rapid": lambda x: x.strip() == "spanning-tree mode rapid-pvst",
    }
    active = [rules[d] for d in DISABLED]
    return [x for x in lines if not any(r(x) for r in active)]

def lines_block(radius=True):
    if TEST_CONSOLE:
        l = ["line con 0", " exec-timeout 0 0", " logging synchronous", " privilege level 15"]
        l += [" login authentication CONSOLE"] if radius else []
        for rng in ("0 4", "5 15"):
            l += [f"line vty {rng}", " access-class 10 in", " exec-timeout 10 0", " transport input ssh",
                  " login authentication default" if radius else " login local"]
        return l + ["end"]
    login = ["login authentication CONSOLE"] if radius else ["login local"]
    vty_login = ["login authentication default"] if radius else ["login local"]
    l = ["line con 0", " exec-timeout 5 0", " logging synchronous"] + [" " + x for x in login]
    for rng in ("0 4", "5 15"):
        l += [f"line vty {rng}", " access-class 10 in", " exec-timeout 10 0",
              " transport input ssh"] + [" " + x for x in vty_login]
    return l + ["end"]

def vlan_defs(vids):
    l = ["vtp mode transparent"]
    for v in vids:
        l += [f"vlan {v}", f" name {VLANS[v][0]}"]
    return l

def access_switch(name):
    vlan, mhost, floor, cport, n = ACCESS[name]
    vname = VLANS[vlan][0]
    l = baseline(name, platform="l2switch") + vlan_defs((vlan, 99, 999)) + [
        "ip dhcp snooping",
        f"ip dhcp snooping vlan {vlan}",
        "no ip dhcp snooping information option",
        f"ip arp inspection vlan {vlan}",
        "spanning-tree mode rapid-pvst",
        "spanning-tree extend system-id",
    ]
    for i in range(1, 25):
        l.append(f"interface FastEthernet0/{i}")
        if i <= n:
            l += [f" description {vname} workstation {floor}-desk-{i:02d}",
                  f" switchport access vlan {vlan}", " switchport mode access",
                  " switchport nonegotiate",
                  " switchport port-security", " switchport port-security maximum 2",
                  " switchport port-security violation restrict",
                  " switchport port-security mac-address sticky",
                  " spanning-tree portfast", " spanning-tree bpduguard enable",
                  " ip dhcp snooping limit rate 20", " no cdp enable"]
        else:
            l += [" description UNUSED - parked and shut", " switchport access vlan 999",
                  " switchport mode access", " shutdown"]
    for gi, core in (("GigabitEthernet0/1", "CORE-1"), ("GigabitEthernet0/2", "CORE-2")):
        l += [f"interface {gi}", f" description Uplink to {core} {cport}",
              " switchport trunk native vlan 999", f" switchport trunk allowed vlan {vlan},99",
              " switchport mode trunk", " switchport nonegotiate",
              " ip dhcp snooping trust", " ip arp inspection trust"]
    l += ["interface Vlan1", " no ip address", " shutdown",
          "interface Vlan99", " description Management", f" ip address {net(99, mhost)} 255.255.255.0",
          " no shutdown", f"ip default-gateway {net(99, 1)}"]
    return l + lines_block()

def dc_switch(name):
    vids, mhost, cport, members = DC[name]
    used = {p: (s, v) for p, s, v in members}
    allowed = ",".join(str(v) for v in sorted(set(vids) | {99}))
    l = baseline(name, platform="l2switch") + vlan_defs(tuple(sorted(set(vids) | {99, 999}))) + [
        "spanning-tree mode rapid-pvst", "spanning-tree extend system-id"]
    for i in range(1, 25):
        port = f"FastEthernet0/{i}"
        l.append(f"interface {port}")
        if port in used:
            srv, v = used[port]
            l += [f" description {srv} - {SERVERS[srv][2]}", f" switchport access vlan {v}",
                  " switchport mode access", " switchport nonegotiate",
                  " switchport port-security", " switchport port-security maximum 1",
                  " switchport port-security violation restrict",
                  " switchport port-security mac-address sticky",
                  " spanning-tree portfast", " spanning-tree bpduguard enable", " no cdp enable"]
        else:
            l += [" description UNUSED - parked and shut", " switchport access vlan 999",
                  " switchport mode access", " shutdown"]
    for gi, core in (("GigabitEthernet0/1", "CORE-1"), ("GigabitEthernet0/2", "CORE-2")):
        l += [f"interface {gi}", f" description Uplink to {core} {cport}",
              " switchport trunk native vlan 999", f" switchport trunk allowed vlan {allowed}",
              " switchport mode trunk", " switchport nonegotiate"]
    l += ["interface Vlan1", " no ip address", " shutdown",
          "interface Vlan99", " description Management", f" ip address {net(99, mhost)} 255.255.255.0",
          " no shutdown", f"ip default-gateway {net(99, 1)}"]
    return l + lines_block()

USERS_IN = [
    "remark DHCP to the core relay/servers",
    "permit udp any any eq bootps",
    "remark replies to admin troubleshooting",
    "permit icmp any 10.10.99.0 0.0.0.255 echo-reply",
    "remark protected zones: backup, management, infrastructure",
    "deny ip any 10.10.60.0 0.0.0.255",
    "deny ip any 10.10.99.0 0.0.0.255",
    "deny ip any 10.10.254.0 0.0.0.255",
    "deny ip any 10.10.255.0 0.0.0.255",
    "deny ip any 10.10.0.0 0.0.0.255",
    "remark shared services",
    f"permit udp any host {DNS1} eq domain",
    f"permit udp any host {DNS2} eq domain",
    f"permit tcp any host {DNS1} eq 443",
    f"permit tcp any host {DNS2} eq smtp",
    f"permit tcp any host {DNS2} eq pop3",
    "permit icmp any 10.10.40.0 0.0.0.255 echo",
    "deny ip any 10.10.40.0 0.0.0.255",
    "remark every department may use every departmental application/database over HTTPS",
    "permit tcp any 10.10.50.0 0.0.0.255 eq 443",
    "permit icmp any 10.10.50.0 0.0.0.255 echo",
    "deny ip any 10.10.50.0 0.0.0.255",
    "remark no direct host-to-host traffic between departments (ping allowed for support)",
    "permit icmp any 10.10.0.0 0.0.255.255 echo",
    "deny ip any 10.10.0.0 0.0.255.255",
    "remark Internet",
    "permit ip any any",
]
BACKUP_OUT = [
    "remark only data, service and management zones may reach backup",
    "permit ip 10.10.50.0 0.0.0.255 10.10.60.0 0.0.0.255",
    "permit ip 10.10.40.0 0.0.0.255 10.10.60.0 0.0.0.255",
    "permit ip 10.10.99.0 0.0.0.255 10.10.60.0 0.0.0.255",
    "deny ip any any",
]
MGMT_OUT = [
    "remark return traffic for admin sessions",
    "permit tcp any 10.10.99.0 0.0.0.255 established",
    "permit icmp any 10.10.99.0 0.0.0.255 echo-reply",
    "permit icmp any 10.10.99.0 0.0.0.255 unreachable",
    "permit udp any eq domain 10.10.99.0 0.0.0.255",
    "remark device telemetry and AAA towards the NMS",
    f"permit udp 10.10.0.0 0.0.255.255 host {NMS_IP} eq 514",
    f"permit udp 10.10.0.0 0.0.255.255 host {NMS_IP} eq 123",
    f"permit udp 10.10.0.0 0.0.255.255 host {NMS_IP} eq 1645",
    f"permit udp 10.10.0.0 0.0.255.255 host {NMS_IP} eq 1646",
    "deny ip any any",
]

def acl(name, entries):
    return [f"ip access-list extended {name}"] + [" " + e for e in entries]

def core(name):
    """Packet Tracer 9 only applies 3650 physical-port configuration reliably
    when it is replayed after the rest of the configuration, so the port
    section is moved to just before the line configuration."""
    l = _core(name)
    first = next(i for i, x in enumerate(l) if x.startswith("interface GigabitEthernet1/0/"))
    last = max(i for i, x in enumerate(l) if x.startswith("interface GigabitEthernet1/1/")) + 1
    while l[last].startswith(" "):
        last += 1
    ports, rest = l[first:last], l[:first] + l[last:]
    li = rest.index("line con 0")
    return rest[:li] + ports + rest[li:]

def _core(name):
    me = 2 if name == "CORE-1" else 3
    other_active = ACTIVE["CORE-2" if name == "CORE-1" else "CORE-1"]
    routed = [v for v in VLANS if VLANS[v][1] and v != 900]
    l = baseline(name, platform="l3switch") + ["ip routing"] + vlan_defs(tuple(VLANS)) + [
        "spanning-tree mode rapid-pvst", "spanning-tree extend system-id",
        # the cores are also root for the transit and parking VLANs, otherwise an
        # access switch wins the election and root guard blocks the downlinks
        "spanning-tree vlan " + ",".join(map(str, ACTIVE[name] + ((900, 999) if name == "CORE-1" else ()))) + " priority 4096",
        "spanning-tree vlan " + ",".join(map(str, other_active + ((900, 999) if name == "CORE-2" else ()))) + " priority 8192",
    ]
    downlinks = {cport: (sw, f"{v},99") for sw, (v, _, _, cport, _) in ACCESS.items()}
    for sw, (vids, _, cport, _) in DC.items():
        downlinks[cport] = (sw, ",".join(str(v) for v in sorted(set(vids) | {99})))
    trunk_all = ",".join(str(v) for v in VLANS if v != 999)
    transit = {cp: (ip, e, ep) for c, cp, ip, e, ep, _ in TRANSIT if c == name}
    for i in list(range(1, 25)):
        port = f"GigabitEthernet1/0/{i}"
        l.append(f"interface {port}")
        if port in downlinks:
            sw, allowed = downlinks[port]
            l += [f" description Downlink to {sw}", " switchport trunk native vlan 999",
                  f" switchport trunk allowed vlan {allowed}", " switchport mode trunk",
                  " switchport nonegotiate", " spanning-tree guard root"]
        elif port in transit:
            ip, e, ep = transit[port]
            l += [f" description Routed link to {e} {ep}", " no switchport",
                  f" ip address {ip} 255.255.255.252",
                  f" ip ospf message-digest-key 1 md5 {OSPF_KEY}"]
        elif i in (23, 24):
            other = "CORE-2" if name == "CORE-1" else "CORE-1"
            l += [f" description Port-channel1 member to {other}", " switchport trunk native vlan 999",
                  f" switchport trunk allowed vlan {trunk_all}", " switchport mode trunk",
                  " switchport nonegotiate", " channel-group 1 mode active"]
        else:
            l += [" description UNUSED - parked and shut", " switchport access vlan 999",
                  " switchport mode access", " shutdown"]
    for i in range(1, 5):
        l += [f"interface GigabitEthernet1/1/{i}", " description UNUSED uplink module port", " shutdown"]
    other = "CORE-2" if name == "CORE-1" else "CORE-1"
    l += ["interface Port-channel1", f" description LACP bundle to {other} (Gi1/0/23-24)",
          " switchport trunk native vlan 999", f" switchport trunk allowed vlan {trunk_all}",
          " switchport mode trunk", " switchport nonegotiate",
          "interface Loopback0", f" ip address {LOOPBACK[name]} 255.255.255.255",
          "interface Vlan1", " no ip address", " shutdown"]
    for v in routed:
        pri = 110 if v in ACTIVE[name] else 100
        l += [f"interface Vlan{v}", f" description {VLANS[v][2]}",
              f" ip address {net(v, me)} 255.255.255.0",
              " standby version 2", f" standby {v} ip {net(v, 1)}",
              f" standby {v} priority {pri}", f" standby {v} preempt"]
        if v in USER_VLANS:
            l += [f" ip helper-address {net(40, SERVERS[s][1])}" for s in DHCP_SERVERS]
            l.append(" ip access-group USERS-IN in")
        if v == 60:
            l.append(" ip access-group BACKUP-OUT out")
        if v == 99:
            l.append(" ip access-group MGMT-OUT out")
    l += ["interface Vlan900", " description Routed transit between cores",
          f" ip address {CORE_TRANSIT_IP[name]} 255.255.255.248",
          f" ip ospf message-digest-key 1 md5 {OSPF_KEY}",
          "router ospf 1", f" router-id {LOOPBACK[name]}", " log-adjacency-changes",
          " passive-interface default",
          " no passive-interface GigabitEthernet1/0/21",
          " no passive-interface GigabitEthernet1/0/22",
          " no passive-interface Vlan900",
          " network 10.10.0.0 0.0.255.255 area 0",
          " area 0 authentication message-digest"]
    # Only EDGE-1 originates the OSPF default (primary ISP). If EDGE-1 or its
    # default disappears, this floating static (AD 250) sends traffic to EDGE-2.
    backup = next(eip for c, _, _, e, _, eip in TRANSIT if c == name and e == "EDGE-2")
    l += [f"ip route 0.0.0.0 0.0.0.0 {backup} 250"]
    l += acl("USERS-IN", USERS_IN) + acl("BACKUP-OUT", BACKUP_OUT) + acl("MGMT-OUT", MGMT_OUT)
    return l + lines_block()

OUTSIDE_IN = [
    "remark anti-spoofing: private and loopback sources never arrive from the Internet",
    "deny ip 10.0.0.0 0.255.255.255 any",
    "deny ip 172.16.0.0 0.15.255.255 any",
    "deny ip 192.168.0.0 0.0.255.255 any",
    "deny ip 127.0.0.0 0.255.255.255 any",
    "remark only replies to sessions opened from inside",
    "permit tcp any any established",
    "permit icmp any any echo-reply",
    "permit icmp any any unreachable",
    "deny ip any any",
]

def edge(name):
    isp, wan, nh, metric = EDGE_WAN[name]
    l = baseline(name)
    for c, cp, cip, e, ep, eip in TRANSIT:
        if e != name:
            continue
        l += [f"interface {ep}", f" description Routed link to {c} {cp}",
              f" ip address {eip} 255.255.255.252", " ip nat inside",
              f" ip ospf message-digest-key 1 md5 {OSPF_KEY}", " no shutdown"]
    l += ["interface GigabitEthernet0/2", f" description WAN to {isp}",
          f" ip address {wan} 255.255.255.252", " ip nat outside",
          " ip access-group OUTSIDE-IN in", " no ip proxy-arp", " no cdp enable", " no shutdown",
          "interface Loopback0", f" ip address {LOOPBACK[name]} 255.255.255.255",
          "router ospf 1", f" router-id {LOOPBACK[name]}", " log-adjacency-changes",
          " passive-interface default",
          " no passive-interface GigabitEthernet0/0", " no passive-interface GigabitEthernet0/1",
          " network 10.10.0.0 0.0.255.255 area 0", " area 0 authentication message-digest",
          *([" default-information originate"] if name == "EDGE-1" else []),
          f"ip route 0.0.0.0 0.0.0.0 {nh}",
          "ip route 10.10.0.0 255.255.0.0 Null0 254",
          "access-list 1 remark inside networks translated by PAT",
          "access-list 1 permit 10.10.0.0 0.0.255.255",
          "ip nat inside source list 1 interface GigabitEthernet0/2 overload"]
    l += acl("OUTSIDE-IN", OUTSIDE_IN)
    return l + lines_block()

def isp(name):
    a = name == "ISP-A"
    l = [f"hostname {name}", "no ip domain-lookup",
         "interface GigabitEthernet0/0", " description Customer MSS Ltd",
         f" ip address {'203.0.113.1' if a else '198.51.100.1'} 255.255.255.252", " no shutdown",
         "interface GigabitEthernet0/1", " description Internet exchange LAN",
         f" ip address {'192.0.2.2' if a else '192.0.2.3'} 255.255.255.0",
         " standby version 2", " standby 1 ip 192.0.2.1",
         f" standby 1 priority {110 if a else 100}", " standby 1 preempt", " no shutdown",
         (f"ip route 198.51.100.0 255.255.255.252 192.0.2.3" if a
          else f"ip route 203.0.113.0 255.255.255.252 192.0.2.2"),
         "line con 0", "line vty 0 4", " login", "end"]
    return l

def inet_sw():
    return ["hostname INET-SW", "no ip domain-lookup",
            "interface FastEthernet0/1", " description WEB-PUBLIC",
            "interface GigabitEthernet0/1", " description ISP-A",
            "interface GigabitEthernet0/2", " description ISP-B", "end"]

def ios_config(name):
    return _drop(_ios_config(name))

def _ios_config(name):
    if name in ACCESS:
        return access_switch(name)
    if name in DC:
        return dc_switch(name)
    if name.startswith("CORE"):
        return core(name)
    if name.startswith("EDGE"):
        return edge(name)
    if name.startswith("ISP"):
        return isp(name)
    if name == "INET-SW":
        return inet_sw()
    raise KeyError(name)

def switch_vlans(name):
    if name in ACCESS:
        return (ACCESS[name][0], 99, 999)
    if name in DC:
        return tuple(sorted(set(DC[name][0]) | {99, 999}))
    if name.startswith("CORE"):
        return tuple(VLANS)
    return ()
