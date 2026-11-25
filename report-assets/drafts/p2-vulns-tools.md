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

The tools were chosen to test the weaknesses in section 6 with evidence that the MSS network can act on: open ports, certificates and cipher suites, readable credentials and access-control responses. For each tool, this section states the MSS question it answers, the control it checks and whether it was run. Packet Tracer cannot run these tools, so the three zones that matter for the analysis (user, service and backup) were rebuilt in an isolated Docker lab (section 7.3). Packet Tracer remains the evidence for the ACLs, routing and failover (Figures 05, 11 and 12).

### 7.1 Tool selection and assessment plan

Three criteria governed the selection. Each tool had to answer a question about a named MSS zone rather than a general one; it had to produce output that can be stored and repeated after every change (section 9); and it had to fit a company that will invest in quality but not without limit. For that reason the group chose Greenbone/OpenVAS for authenticated scanning. Nessus Essentials was rejected because its 16-address licence is below the 18 MSS servers and network devices (eight servers and ten switches and routers) that must be scanned.

| Category | Tool (Kali / Windows) | Use in the MSS assessment | Control verified | Executed? |
|---|---|---|---|---|
| Information gathering | Nmap; Zenmap (GUI) | Discover hosts and listening services per zone; confirm that a user VLAN sees only what USERS-IN permits (V1, A10) [14] | USERS-IN, BACKUP-OUT, MGMT-OUT, OUTSIDE-IN | Nmap: yes (Figures 7.1, 7.3, 7.4). Zenmap: no, same engine |
| Sniffing and spoofing | tcpdump (Kali); Wireshark (Windows and macOS builds) | Find readable credentials crossing the core (V2, A7) | HTTPS-only intranet; residual POP3 and FTP risk | tcpdump: yes. Wireshark: TShark 4.6.9 on the lab captures (Figures 7.2, 7.5); GUI not used |
| Vulnerability analysis | Greenbone/OpenVAS; Nmap NSE `ssl-enum-ciphers` | Authenticated scans of servers and devices; TLS version and cipher review of INTRANET and the departmental front ends (V2, A8) | Patching, disabled unused services, TLS configuration | NSE: yes (Figure 7.4). Greenbone: no, planned |
| Web application analysis | curl (scripted); OWASP ZAP; Burp Suite Community; Nikto | Test that every role check is enforced on the server, not only in the interface (V3) [12] | Role checks, HTTPS-only access | curl: yes (Figure 7.6). ZAP, Burp and Nikto: no, planned |
| Password auditing | Hydra; John the Ripper or Hashcat | Under written authorisation and against lab copies only: lockout policy and strength of exported type 5 hashes (A6, A8) | `login block-for`, VTY access-class, RADIUS AAA, secret strength | No, planned |
| Layer-2 testing | Yersinia; Bettercap | Confirm in a lab replica that trunk, DHCP, ARP and STP protections hold (A1 to A5) | DTP off, native VLAN 999, DHCP snooping, DAI, port-security, BPDU guard, root guard [2] | No, planned |
| Windows administration | Wireshark; Nmap/Zenmap; PuTTY (`plink`) | Verification from ADMIN-PC (10.10.99.50): captures, scans and SSH version 2 checks | VTY restricted to VLAN 99; SSH version 2 only | PuTTY: no. Management-VLAN reachability: Packet Tracer (Figures 12a, 12b) |
| Exploitation | Metasploit Framework | Docker lab only: confirm that V1 is exploitable at baseline and unreachable after hardening | VLAN 60 isolation, BACKUP-OUT | No, planned |
| Wireless | Aircrack-ng suite | Not applicable to the wired design; rogue access point survey and WPA2/WPA3-Enterprise checks once the WLAN in 5.1 exists | 802.1X and RADIUS (future) | No |

### 7.2 Implementation examples within the MSS scenario

Each example gives the command, the zone it targets and the result. Results marked **lab** were produced on 25 November 2026 in the Docker replica described in section 7.3 and are reproduced in Figures 7.1 to 7.6. Commands marked **planned** are written for the production network or a pilot rebuild from the same design source; no result is claimed for them. Every scan is limited to MSS address ranges, and external scans are made only from an authorised vantage point.

**Nmap: host discovery and service inventory (lab).** A host-discovery sweep from the employee bridge lists the intranet and the client, and the Docker bridge gateway (172.29.216.1), which is not an MSS device. The protected backup segment cannot be swept at all, because the client has no route to it; a TCP connect to the backup database reports `filtered (net-unreach)` (Figure 7.3). The production equivalent is planned as:

```
nmap -sn 10.10.10.0/24         # planned: inventory of Marketing VLAN 10 against 20 registered workstations
nmap -sn 10.10.60.0/24         # planned: expected to find no live hosts from a user VLAN
```

**Nmap: service scan of the shared servers (lab and planned).** The baseline lab, where the database was attached to the employee bridge, answered on 5432/tcp with `syn-ack` and identified PostgreSQL (Figure 7.1). After hardening the same address returned `filtered (no-response)`, while the backup-side positive control still answered (E05). The production scan that the group plans to repeat after every change is:

```
nmap -sV -Pn 10.10.40.10-11    # planned: should show only HTTPS on INTRANET and SMTP and POP3 on MAIL
```

**Nmap NSE: TLS versions and cipher suites (lab).** The script was run against the hardened intranet (Figure 7.4). The intranet offers TLS 1.2 and TLS 1.3 only, which matches the TLS 1.2 minimum set in the lab fixture. The output also shows a residual weakness: the 13 TLS 1.2 suites include six static RSA key-exchange suites, which provide no forward secrecy, and four CBC-mode suites with SHA-1 MACs. Nmap grades every suite A, so the grade alone would not reveal this. Nmap prints the TLS 1.3 suites in its own notation (`TLS_AKE_WITH_…`); the suite that curl negotiated in E08 was `TLS_AES_256_GCM_SHA384`. The production cipher list should keep only the ECDHE suites with AEAD ciphers. The planned production scan is:

```
nmap --script ssl-enum-ciphers -p 443 10.10.40.10 10.10.50.11-13    # planned
```

**tcpdump and TShark: credential exposure (lab).** TShark, the command-line form of Wireshark, was run on the two 25 November captures with a display filter for HTTP requests. The baseline capture contains four requests, and three carry `Authorization: Bearer` tokens for the employee and administrator roles in readable form. Figure 7.2 is a window capture of the group's Wireshark with the filter `http.request` applied and packet 16 expanded, showing `Authorization: Bearer LAB-EMPLOYEE-ONLY` in the details pane and the same bytes in the hex pane. The hardened capture contains no HTTP request at all, and each of its four TLS ClientHello messages carries the server name `intranet.lab`. Figure 7.5 is a Wireshark capture of those four messages; the zero HTTP count comes from the TShark run in the same script (C04). The ClientHello is labelled TLSv1.2 at the record layer, as TLS 1.3 clients usually are; E08 confirms that TLS 1.3 was negotiated. The same display filter is planned for a monitoring-port capture on DC-SW-A, with the planned tcpdump command:

```
tshark -r <capture>.pcap -Y "http.authorization or http.request"    # planned: expected to return 0 after the move to HTTPS
tcpdump -nn -A -r <capture>.pcap                                    # planned: reviewed by hand for readable credentials
```

After the move to HTTPS, POP3 and FTP logins should still match the following Wireshark filter, which is the control for the residual risk A7:

```
pop.request.command == "PASS" || ftp.request.command == "PASS"
```

**curl: scripted authorisation tests (lab).** The role model was tested by sending the same export request with no token, an employee token and an administrator token. Anonymous requests returned 401, the employee directory returned 200, the employee export returned 403 with `administrator role required`, and the administrator export returned 200 (Figure 7.6). This is the check for OWASP A01 broken access control [12]. The production version targets the departmental front ends, which the network ACLs must leave open to every employee:

```
curl -sS -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer <employee-token>" https://db-sales.mss.lan/admin/export    # planned: expected 403
```

**Greenbone/OpenVAS: authenticated scan (planned).** A scan task is defined from VLAN 99 for 10.10.40.10-11, 10.10.50.11-13 and 10.10.60.10-11, so the backup servers are scanned only from the zone allowed to reach them.
**Nikto and OWASP ZAP baseline (planned).** Web front ends are checked for transport and header weaknesses. A clean result should show no access-control or cryptographic findings beyond those already accepted in section 8:

```
nikto -h intranet.mss.lan -p 443 -ssl
zap-baseline.py -t https://db-sales.mss.lan
```

**External exposure (planned).** From an authorised external vantage point, a scan of both edge addresses should show no open ports, because OUTSIDE-IN permits only replies to sessions opened from inside (A10) [16]. The `established` keyword is stateless, so acknowledgement probes would be reported as unfiltered. This is one reason for the next-generation firewall proposed in section 5.1.

```
nmap -sS -Pn -p- 203.0.113.2 198.51.100.2    # planned, authorised external vantage point only
```

**PuTTY `plink` and SSH version 2 (planned).** Administrators confirm from ADMIN-PC that a switch accepts only SSH version 2 and only from the management VLAN. Packet Tracer already shows the same policy: SSH from ADMIN-PC reaches the login prompt (Figure 12a) and SSH from a Marketing PC times out (Figure 12b).

```
plink -ssh -2 -l netadmin 10.10.99.21    # planned, run from ADMIN-PC
```

**Password auditing and layer-2 tests (planned, not executed).** Hydra would be pointed only at lab copies of the VTY lines, and John the Ripper or Hashcat only at exported type 5 hashes. Yersinia (DTP, DHCP, STP) and Bettercap (ARP) would be run only in a lab rebuild generated from the same design source. The expected outcomes are: login blocked for 120 seconds after three failures on routers and cores; trunks not negotiated; DHCP snooping rate limits and BPDU guard err-disabling the test port; and DAI dropping forged ARP replies. These tests need the lab rebuild and written authorisation, so no result is claimed in this report.

### 7.3 Lab implementation and results

The lab ran on 25 November 2026 (UTC). Two Docker bridges were created as internal-only networks (`internal=true`), no container published a port (`published={}`), and all data was synthetic, for example the record `MSS-LAB-SYNTHETIC-RECORD`. The containers map to MSS zones as follows:

- Kali client 172.29.216.10: an employee PC on a user VLAN;
- Python intranet application 172.29.216.30: INTRANET;
- PostgreSQL backup database 172.29.217.20 on the protected bridge: DB-REPLICA in VLAN 60;
- baseline only: a second attachment of the same database to the employee bridge as 172.29.216.20, modelling the missing segmentation.

E00 records Nmap 7.991, curl 8.22.0 (OpenSSL 3.6.5), tcpdump 4.99.6, Python 3.12.3, PostgreSQL 16.15 and Docker 29.9.2; TShark 4.6.9 was used on the macOS host. OpenSSL generated the self-signed lab certificate (CN=intranet.lab, RSA 2048) that curl trusted through `--cacert`. The main commands were:

```
nmap -sT -sV --version-light -Pn -n --reason -p 5432 172.29.216.20
nmap -sT -sV --version-light -Pn -n --reason -p 8080,8443 172.29.216.30
curl -sS --max-time 5 --cacert /tmp/lab-ca.pem --resolve "intranet.lab:8443:172.29.216.30" \
  -H "Authorization: Bearer LAB-EMPLOYEE-ONLY" https://intranet.lab:8443/admin/export
tcpdump -nn -A -r /tmp/capture.pcap
```

The baseline used `http://intranet.lab:8080`, and tcpdump captured with the filter `host 172.29.216.30 and tcp`. The hardened phase reflects the Packet Tracer design: the database was detached from the employee bridge (the VLAN 60 isolation), the intranet served HTTPS only, and the export route enforced the administrator role. Each phase requested the export anonymously and with the employee and administrator tokens. The run ended with `PASS · ports, backup isolation, access controls and transport checks`.

A second script, `ch7-tool-examples.sh`, rebuilt the hardened topology and produced the discovery, cipher-enumeration and capture-review outputs used in Figures 7.3 to 7.5. Its output also ended with a PASS line. Both scripts are in the vulnerability lab and run without any port published to the host.

| Weakness | Baseline result | Hardened result | Evidence |
|---|---|---|---|
| V1 Backup database reachable | 172.29.216.20 5432/tcp open postgresql (syn-ack) | 172.29.216.20 5432/tcp filtered (no-response); 172.29.217.20 5432/tcp filtered (net-unreach) | E01, E04, E05 |
| V2 Cleartext credentials | 8080/tcp open http, 8443 closed; three bearer tokens readable in the capture | 8080 closed, 8443 open ssl/http; TLSv1.3 with TLS_AES_256_GCM_SHA384 negotiated, subject CN=intranet.lab verified; wrong hostname rejected (curl exit 60); no HTTP request in the capture; residual weak TLS 1.2 suites (C03) | E01, E03, E05, E07, E08, C03, C04 |
| V3 Employee calls administrator export | Anonymous 401; employee 200; administrator 200 | Anonymous 401; employee 403 "administrator role required"; administrator 200 | E02, E06 |
| Discovery from the employee segment | Database answers on 172.29.216.20 (5432/tcp open) on the employee bridge | Intranet and client only; protected backup segment not routable (0 hosts swept) | E01, C01, C02 |
| Positive control from backup network | – | `nmap -sT -Pn -n --reason -p 5432 172.29.217.20` from the protected bridge: 5432/tcp open (syn-ack) | E05 |

Figures 7.1 to 7.6 are reproduced in Appendix C. Two limits apply. The Docker bridges show routing isolation, not the MSS ACLs; the ACL decisions are evidenced in Packet Tracer (Figures 05, 11 and 12). The lab also tests only the intranet fixture, not the departmental front ends or the mail and FTP services, which remain residual risks in section 8. The positive control shows that hardening removed the exposure without breaking the service for authorised zones. All testing was authorised, isolated from production and Internet hosts, and limited to the agreed scope, following the planning, discovery, attack and reporting phases of NIST SP 800-115 [11].
