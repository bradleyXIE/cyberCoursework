## 8 Defence mechanisms

Each defence is traced to a tested or analysed finding. Where Packet Tracer could not exercise a control, the evidence is the automated configuration check (0 missing lines on all 13 IOS devices).

| Finding | Defence implemented in the MSS design | Verification (figure or evidence ID) | Further hardening |
|---|---|---|---|
| V1 Exposed backup database | Backup servers in isolated VLAN 60; USERS-IN denies 10.10.60.0/24; BACKUP-OUT admits only data, services and management | E05 (5432 filtered from employees, open from backup network); 10.10.60.10 unreachable (Figure 05); deny hits (Figure 11) | Encrypted replication from VLAN 50 to VLAN 60 |
| V2 Cleartext credentials | HTTPS-only intranet and departmental servers; HTTP denied by USERS-IN and disabled | E06–E08 (TLS 1.3, token absent from capture); C04 (no HTTP request in capture); HTTPS loads (Figure 06a, 06c), HTTP times out (Figure 06b) | Cipher review found six static-RSA and four SHA-1 CBC suites still offered (C03, Figure 7.4): keep only ECDHE with AEAD ciphers; POP3S/IMAPS and SFTP instead of POP3 and FTP [14] |
| V3 Broken access control | Application role checks; device administration confined to VLAN 99 (VTY access-class, USERS-IN) | E06 (employee 403, admin 200); SSH from ADMIN-PC succeeds (Figure 12a), from MKT-PC01 times out (Figure 12b) | Test against OWASP A01 [12] with OWASP ZAP before each release |
| A1 VLAN hopping (DTP, native VLAN) | Nonegotiate trunks, unrouted native VLAN 999, allowed VLAN lists | Configuration check, 0 missing lines | Periodic Yersinia test from a user port |
| A2 Rogue DHCP / starvation | DHCP snooping with trusted uplinks and 20 pps limit; port-security | Snooping enabled on VLAN 10, 20 pps (Figure 08) | Alert on snooping drops at the NMS |
| A3 ARP spoofing / MITM | DAI on user VLANs; TLS protects intercepted traffic | Configuration check; E06–E08 | Bettercap test in quarterly penetration test |
| A4 MAC flooding | Port-security: 2 sticky MACs per workstation port, 1 per server port, restrict | Fa0/1–20 max 2, 0 violations (Figure 08) | Review sticky MAC tables after desk moves |
| A5 STP root takeover | Root fixed on the cores; BPDU guard on edge ports; root guard on downlinks | CORE-1 root for VLAN 10 (Figure 03); clean reconvergence after core failure (Figure 10a, 10b) | Test BPDU injection with Yersinia |
| A6 Brute force (SSH, RADIUS, mail, FTP) | SSH v2, VTY access-class, RADIUS with local fallback; login block-for 120 after 3 failures on routers and cores (rejected by the Packet Tracer 2960 image) | Figure 12a, 12b; RADIUS clients (Figure 14); central syslog (Figure 13) | Hydra test in the lab; lockout on mail and FTP |
| A7 Cleartext FTP/POP3 | POP3 reachable only on MAIL; FTP to BACKUP-ARCHIVE only from VLANs 40/50/99 (USERS-IN, BACKUP-OUT) | Configuration check; DB-REPLICA unreachable from users (Figure 05) | POP3S/IMAPS and SFTP |
| A8 Weak stored password hashes | Enable secret and service password-encryption | Type 5 MD5 secrets observed in Packet Tracer | Type 8/9 (scrypt) secrets on production IOS; audit with Hashcat |
| A9 OSPF / HSRP spoofing | OSPF MD5 authentication; passive-interface default | Neighbours FULL with MD5 configured (Figure 02) | HSRP authentication in production |
| A10 Internet exposure | PAT hides internal addressing; OUTSIDE-IN anti-spoofing [17] and replies-only policy [16] | PAT translation on EDGE-1 (Figure 07) | External Nmap scan of 203.0.113.2 and 198.51.100.2 after every edge change (not tested in Packet Tracer) |

Together these controls give defence in depth. Physically, the server room is badge-controlled and the replica is in a separate rack. At layer 2, port-security, DHCP snooping, DAI and STP guards contain attacks from a desk port. At layer 3, core ACLs limit departments to needed services, while the edge ACL and PAT guard the Internet boundary. Management is reachable only from VLAN 99 over SSH with RADIUS, and applications enforce HTTPS and role checks. A leaked database credential alone would still not let a Marketing workstation reach DB-REPLICA.

## 9 Guideline for security and vulnerability analysis in regular maintenance

The design remains secure only if it is retested as it changes. The schedule suits a 60-user company on a limited budget, reusing the group's tooling and free scanners, in line with CIS Controls v8 [13].

| Frequency | Activity | Tool | Owner role | Output |
|---|---|---|---|---|
| Daily | Review login, HSRP/OSPF, port-security and snooping events | NMS syslog | Network administrator | Review note or incident ticket |
| After every change | Rerun the configuration drift check and the Docker vulnerability lab | check_config.py; Docker lab (run.sh and ch7-tool-examples.sh) with Kali tools | Network administrator | 0 missing lines; lab PASS for V1–V3; discovery and cipher outputs unchanged |
| After every change | Copy each device configuration to ADMIN-PC over SSH, then upload it to BACKUP-ARCHIVE | SSH from ADMIN-PC; FTP (SFTP in production) | Network administrator | Dated configuration archive |
| Monthly | Authenticated vulnerability scan of servers and devices | Greenbone/OpenVAS | Security lead | Rated scan report |
| Monthly | Patch servers and workstations; review IOS advisories | Vendor update channels | Server administrator | Patch log |
| Quarterly | Restore test of DB-REPLICA and BACKUP-ARCHIVE data | Database restore to isolated test host | Server administrator | Restore time and integrity result |
| Quarterly | Review RADIUS, local fallback and application admin accounts | NMS RADIUS user list | IT manager | Signed account list |
| Quarterly | Internal penetration test of the analysed vulnerabilities | Nmap, Yersinia, Bettercap, OWASP ZAP; Hydra against lab copies only | Security lead | Test report |
| Annually | External test of 203.0.113.2 and 198.51.100.2 | Nmap from outside | Security lead / IT manager | Updated security policy |

Each test follows the NIST SP 800-115 phases of planning, discovery, attack and reporting [11]:

1. **Authorisation and rules of engagement.** Written permission from the IT manager defines in-scope addresses, time window, tools and a stop contact. ISP equipment is excluded; exploitation uses the Docker lab with synthetic data.
2. **Baseline.** The latest configuration archive and scan are the reference; the drift check must show 0 missing lines, so findings reflect the design rather than untracked changes.
3. **Scan.** Scans run from a user VLAN, VLAN 99 and outside the edge, as each zone should see a different attack surface.
4. **Verify.** Findings are confirmed manually, as V1–V3 were with Nmap, tcpdump and curl.
5. **Remediate.** Fixes pass change control and enter the design source first, keeping the rebuild and drift check authoritative.
6. **Retest.** The same command is rerun with a positive control (as in E05) proving the legitimate service still works.
7. **Report.** The report records finding, risk, evidence, fix, retest result and owner, and feeds the annual policy review.

