[[PAGEBREAK]]

# Part 2: Vulnerability analysis

## 6 Security vulnerabilities in the network setup

The group assessed the MSS design from the position of an ordinary employee on a user VLAN, because the scenario requires every employee to reach shared services and all three departmental databases, which makes the internal network the most likely source of misuse. Three weaknesses were reproduced and fixed in an isolated lab (V1–V3); ten further weaknesses (A1–A10) were analysed against the Packet Tracer configuration, and likelihood and impact are rated as they would be without the corresponding control.

| ID | Weakness | Location in the MSS design | Likelihood | Impact | Why it matters for MSS |
|---|---|---|---|---|---|
| V1 (tested) | Backup database reachable from the user network | DB-REPLICA 10.10.60.10, VLAN 60; USERS-IN and BACKUP-OUT on both cores | High | High | The replica holds copies of all three departmental databases, so one compromised workstation could read or destroy the recovery copy as well as the live data. |
| V2 (tested) | Credentials readable in plain HTTP | INTRANET 10.10.40.10, VLAN 40 | High | High | All staff use the intranet; a token sent in clear can be replayed by anyone who captures it. |
| V3 (tested) | Employee able to call the administrator export | Intranet and departmental HTTPS front ends (VLANs 40 and 50) | Medium | High | Network ACLs must permit HTTPS to every departmental server, so the application role check is the only barrier to bulk export [12]. |
| A1 | Trunk negotiation / native VLAN misuse | Access-to-core and DC-switch trunks | Low | High | Tagged frames could reach VLAN 60 or 99 directly, bypassing the core ACLs. |
| A2 | Rogue or exhausted DHCP | User VLANs 10/20/30; DHCP on INTRANET and MAIL via relay | Medium | Medium | A rogue server could hand out a false gateway or DNS server; exhaustion would deny addresses to up to 25 users per floor [9]. |
| A3 | ARP-based interception | User VLANs and HSRP gateway .1 | Medium | High | Spoofing the gateway would place an attacker between staff and the intranet, mail and database servers. |
| A4 | MAC table overflow | ACC-F1-MKT, ACC-F2-SALES1/2, ACC-F3-GS | Low | Medium | Flooded frames would expose other users' traffic on the same floor switch. |
| A5 | Spanning-tree root takeover | Access ports and core downlinks | Low | High | A rogue root would redirect traffic away from CORE-1/CORE-2 and break the HSRP-aligned load sharing [5]. |
| A6 | Password guessing on SSH, mail and FTP | Device VTY lines (from VLAN 99), MAIL (from user VLANs), BACKUP-ARCHIVE (from VLANs 40/50/99) | Medium | High | A guessed `netadmin` credential would give administrative control of the network devices. |
| A7 | Cleartext POP3 between users and MAIL, and cleartext FTP from the data, services and management zones to BACKUP-ARCHIVE | MAIL (POP3), BACKUP-ARCHIVE (FTP) | High | Medium | Mail and backup credentials cross the core in readable form; this remains a residual risk. |
| A8 | Weak legacy password hashes in device configurations | Type 5 (MD5) `enable secret` and `username` secrets on the IOS devices | Low | High | A leaked configuration backup could be cracked offline. |
| A9 | Unauthenticated routing/gateway protocol messages | OSPF area 0 links, HSRP groups on the cores | Low | High | OSPF uses MD5 authentication [3], but HSRP authentication is not configured, so a forged hello could claim the active gateway role [4]. |
| A10 | Internet-facing exposure of the edge routers | EDGE-1 203.0.113.2, EDGE-2 198.51.100.2 | Medium | High | The edges are the only devices visible from the Internet and carry all MSS traffic. |

## 7 Kali Linux and Windows tools for the analysis

### 7.1 Assessment plan by tool category

| Category | Tool (Kali / Windows) | Use in the MSS assessment | Control verified | Executed? |
|---|---|---|---|---|
| Information gathering | Nmap / Zenmap | Discover live hosts and listening services per VLAN; confirm that only permitted services answer from a user VLAN (V1, A10) | USERS-IN, BACKUP-OUT, MGMT-OUT, OUTSIDE-IN [14] | Nmap: yes (lab); Zenmap: no |
| Sniffing and spoofing | tcpdump / Wireshark | Inspect traffic between user VLANs and servers for readable credentials (V2, A7) | HTTPS-only intranet; residual FTP/POP3 risk | tcpdump: yes (lab); Wireshark: no |
| Vulnerability analysis | Greenbone/OpenVAS (Nessus Essentials covers only 16 IP addresses, fewer than the 18 MSS servers and IOS devices), Nmap NSE `ssl-enum-ciphers` | Authenticated scans of servers and IOS devices; TLS version and cipher review of INTRANET and DB-MKT/DB-SALES/DB-GS | Patching, disabled unused services, TLS configuration | No (planned) |
| Web application analysis | OWASP ZAP, Burp Suite Community, Nikto | Review intranet and departmental front ends for access-control and transport faults (V2, V3) [12] | Role checks, HTTPS-only access | No (equivalent checks were run with curl) |
| Password auditing | Hydra, John the Ripper / Hashcat | Only under written authorisation and against lab copies: test the lockout policy and the strength of exported type 5 hashes (A6, A8) | `login block-for`, VTY access-class, RADIUS AAA, secret strength | No |
| Layer-2 testing | Yersinia, Bettercap | Confirm in a lab replica that trunk, DHCP, ARP and STP protections hold (A1–A5) | DTP off, native VLAN 999, DHCP snooping, DAI, port-security, BPDU guard, root guard [2] | No |
| Windows | Wireshark, Nmap/Zenmap, PuTTY | Administrator-side verification from ADMIN-PC (10.10.99.50): captures, scans and SSH v2 checks | VTY restricted to VLAN 99, SSH v2 only | No |
| Exploitation | Metasploit Framework | Docker lab only: confirm that V1 is exploitable at baseline and no longer reachable after hardening | VLAN 60 isolation, BACKUP-OUT | No |
| Wireless | Aircrack-ng suite | Not applicable to the current wired design; rogue access point survey now and WPA2/WPA3-Enterprise checks once the WLAN in 5.1 exists | 802.1X/RADIUS (future) | No |

### 7.2 Implementation examples within the MSS scenario

Packet Tracer cannot run these tools, so the following examples apply to the production network or a pilot rebuild generated from the same design source. Each scan is limited to MSS address ranges and is used for discovery and verification only.

A host-discovery sweep of the Marketing VLAN gives an inventory to compare with the 20 registered workstations. Run from a Marketing workstation against the backup VLAN, the same sweep should find no live hosts, because USERS-IN denies 10.10.60.0/24 before any ICMP permit; from ADMIN-PC it acts as a positive control, since BACKUP-OUT admits the management VLAN.

```
nmap -sn 10.10.10.0/24
nmap -sn 10.10.60.0/24
```

A service scan of the shared servers from a user VLAN should list only what USERS-IN permits: HTTPS on INTRANET, and SMTP and POP3 on MAIL.

```
nmap -sV -Pn 10.10.40.10-11
```

An NSE script reports the TLS versions and cipher suites offered by the intranet and the three departmental front ends.

```
nmap --script ssl-enum-ciphers -p 443 10.10.40.10 10.10.50.11-13
```

To confirm that no credentials cross the core in clear, a capture would be taken on a monitoring port on DC-SW-A during a scheduled window and reviewed in Wireshark on ADMIN-PC or with tcpdump. HTTPS sessions should show no readable `Authorization` header, while POP3 and FTP logins are expected to remain visible until the planned move to secure protocols (A7).

```
tcpdump -nn -A -r <capture>.pcap
```

From an authorised external vantage point, a scan of both WAN addresses should show no open ports, because OUTSIDE-IN permits only replies to sessions opened from inside (A10) [16]. The `established` keyword is stateless, so ACK probes would be reported as unfiltered – one reason for the next-generation firewall proposed in 5.1. This external test was not run in Packet Tracer.

```
nmap -sS -Pn -p- 203.0.113.2 198.51.100.2
```

Web front ends are checked for transport and header weaknesses with Nikto and an OWASP ZAP baseline scan, which should report no access-control or cryptographic findings (A01/A02) [12]:

```
nikto -h intranet.mss.lan -p 443 -ssl
zap-baseline.py -t https://db-sales.mss.lan
```

In Wireshark on ADMIN-PC, a display filter isolates any cleartext credentials; after the move to HTTPS only POP3 and FTP logins should match (A7):

```
http.authorization || pop.request.command == "PASS" || ftp.request.command == "PASS"
```

A Greenbone authenticated scan task is defined from VLAN 99 for 10.10.40.10-11, 10.10.50.11-13 and 10.10.60.10-11, so backup servers are scanned from the only zone allowed to reach them. Administrators confirm that devices accept SSH version 2 only from ADMIN-PC with PuTTY's command-line client:

```
plink -ssh -2 -l netadmin 10.10.99.21
```

Password auditing (Hydra against lab copies of the VTY lines; John the Ripper or Hashcat against exported type 5 hashes) and layer-2 tests (Yersinia for DTP, DHCP and STP; Bettercap for ARP) are run only in a lab rebuild generated from the same design source, under written authorisation. The expected outcomes are: login blocked for 120 s after three failures on routers and cores; trunks not negotiated; DHCP snooping rate limits and BPDU guard err-disabling the test port; DAI dropping forged ARP replies. These tools were not executed for this report.

### 7.3 Lab implementation and results

V1–V3 were tested in a disposable Docker lab on 25 November 2026. Two bridges were created as internal-only networks (`internal=true`), no container published a port (`published={}`), and all data was synthetic (for example `MSS-LAB-SYNTHETIC-RECORD`). The containers map to MSS zones as follows:

- Kali client 172.29.216.10: an employee PC on a user VLAN;
- Python intranet application 172.29.216.30: INTRANET;
- PostgreSQL backup database 172.29.217.20 on the protected bridge: DB-REPLICA in VLAN 60;
- baseline only: a second attachment of the same database to the employee bridge as 172.29.216.20, modelling the missing segmentation.

E00 records Nmap 7.991, curl 8.22.0 (OpenSSL 3.6.5), tcpdump 4.99.6, Python 3.12.3, PostgreSQL 16.15 and Docker 29.9.2. OpenSSL generated the self-signed lab certificate (CN=intranet.lab, RSA 2048) that curl trusted through `--cacert`. The commands were:

```
nmap -sT -sV --version-light -Pn -n --reason -p 5432 172.29.216.20
nmap -sT -sV --version-light -Pn -n --reason -p 8080,8443 172.29.216.30
curl -sS --max-time 5 --cacert /tmp/lab-ca.pem --resolve "intranet.lab:8443:172.29.216.30" \
  -H "Authorization: Bearer LAB-EMPLOYEE-ONLY" https://intranet.lab:8443/admin/export
tcpdump -nn -A -r /tmp/capture.pcap
```

The baseline used `http://intranet.lab:8080`; tcpdump captured with the filter `host 172.29.216.30 and tcp`. The hardened phase reflects the Packet Tracer design: the database was detached from the employee bridge (VLAN 60 isolation), the intranet served HTTPS only, and the export route enforced the administrator role. Each phase requested the export anonymously and with the employee and administrator tokens. The run ended with `PASS · ports, backup isolation, access controls and transport checks`.

| Weakness | Baseline result | Hardened result | Evidence |
|---|---|---|---|
| V1 Backup database reachable | 172.29.216.20 5432/tcp open postgresql (syn-ack) | 172.29.216.20 5432/tcp filtered (no-response); 172.29.217.20 5432/tcp filtered (net-unreach) | E01, E04, E05 |
| V2 Cleartext credentials | 8080/tcp open http, 8443 closed; capture shows `Authorization: Bearer LAB-EMPLOYEE-ONLY` | 8080 closed, 8443 open ssl/http; TLSv1.3 / TLS_AES_256_GCM_SHA384, subject CN=intranet.lab verified; wrong hostname rejected (curl exit 60); no bearer token in capture | E01, E03, E05, E07, E08 |
| V3 Employee calls administrator export | Anonymous 401; employee 200; administrator 200 | Anonymous 401; employee 403 "administrator role required"; administrator 200 | E02, E06 |
| Positive control from backup network | – | `nmap -sT -Pn -n --reason -p 5432 172.29.217.20` from the protected bridge: 5432/tcp open (syn-ack) | E05 |

The positive control shows that hardening removed the exposure without breaking the service for authorised zones. All testing was authorised, isolated from production and Internet hosts, and limited to the agreed scope, following the planning, discovery, attack and reporting phases of NIST SP 800-115 [11].
