### 4.6 Design implementation and testing

The MSS network was built in Cisco Packet Tracer 9.0.1 [15] from a single design source: design.py and build_topology.py generate the topology, cabling and every IOS configuration, which Packet Tracer then loads and natively saves as CW_CST4562-Implementation.pkt; test screenshots are in Appendix A and configuration excerpts in Appendix B. check_config.py compares the intended configuration with what Packet Tracer accepted, reporting 0 missing lines on all 13 IOS devices and SSH RSA keys present on all 10 MSS-owned devices. This gives MSS a repeatable rebuild and a drift check for maintenance. After opening, about 2–3 minutes of simulated time (Fast Forward) are needed for OSPF, HSRP and STP to converge.

Testing exposed three Packet Tracer behaviours, each fixed in the design source: 3650 port configuration is applied only when replayed last, so it is generated last; the core split DHCP scope overlapped, leading to the relayed design in 4.3; and the missing IP SLA and ignored OSPF default metrics led to the floating static default in 4.4.

| Test | Expected | Result | Figure |
|---|---|---|---|
| Core control plane | HSRP split, Po1 up, OSPF FULL | CORE-1 Active for 10/30/50/99; Po1(SU) with both LACP members; OSPF FULL with 10.10.0.2, .3 and .4 | Figure 02 |
| Routing and STP | Default via EDGE-1; CORE-1 root | Last resort 10.10.255.2 via OSPF; CORE-1 RSTP root for VLAN 10 | Figure 03 |
| DHCP relay | Relayed lease from a central server | MKT-PC01 10.10.10.171/24, gateway 10.10.10.1, DHCP server 10.10.40.11 | Figure 04 |
| DNS | Internal and external names resolve | DNS 10.10.40.10; db-sales.mss.lan and www.public.test resolved and answered | Figure 04, Figure 05 |
| HTTPS intranet | Intranet loads over HTTPS | "MSS Ltd Intranet" page loads | Figure 06a |
| HTTP blocked | Plain HTTP to intranet denied | Request Timeout | Figure 06b |
| Cross-department database | Marketing reaches Sales application | Ping 10.10.50.12 replies; Sales page loads over HTTPS | Figure 05, Figure 06c |
| Backup isolation | Users cannot reach VLAN 60 | Ping DB-REPLICA 10.10.60.10 unreachable | Figure 05 |
| Management isolation | Users cannot reach VLAN 99 | Ping NMS unreachable, reported by 10.10.10.2 (ACL) | Figure 05 |
| SSH from admin only | ADMIN-PC succeeds, user PC fails | ADMIN-PC (10.10.99.50) reaches the ACC-F1-MKT (10.10.99.21) password prompt; MKT-PC01 "Connection timed out" | Figure 12a, Figure 12b |
| NAT/PAT | Internal hosts reach Internet behind one address | Web page loads; translation 10.10.10.171:1028 to 203.0.113.2:1028 | Figure 06d, Figure 07 |
| Port security and snooping | Limits active, no violations | Fa0/1–20 maximum 2, Restrict, 0 violations; snooping on VLAN 10, 20 pps | Figure 08 |
| ISP-A failure | Traffic moves to ISP-B | Default becomes static AD 250 via EDGE-2; ping 4/4 (TTL 124); OSPF default returns on restore | Figure 09a–09c |
| Core failure | CORE-2 takes over all gateways | All seven HSRP groups Active on CORE-2 after about 8 s; Internet 3/4, intranet 4/4; preempt restores CORE-1 | Figure 10a, Figure 10b |
| ACL counters | Policy entries matched | USERS-IN hits: deny backup 2, deny management 2, HTTPS intranet 5, HTTPS DB 5, Internet 839 | Figure 11 |
| Syslog and AAA | Central logging and RADIUS | NMS receives HSRP/OSPF messages from both cores; RADIUS clients registered | Figure 13, Figure 14 |

The first ICMP packets lost in the failover tests occur while ARP resolves along the new path; this is Packet Tracer behaviour, not a design fault.

### 4.7 Residual risks and limitations

The following limitations remain:

- **Access switches.** Each floor switch is single; if ACC-F1-MKT fails, all 20 Marketing users lose access until it is replaced. A cold spare is the immediate mitigation.
- **Server NICs.** Each server has one NIC in Packet Tracer, so a DC-SW-A failure removes the primary servers, although the replica and archive on DC-SW-B remain.
- **Single server room.** Racks A and B separate switches and power feeds, but both sit in one floor-1 room, so a room-level incident affects both copies of the data.
- **ISP detection.** Failover relies on EDGE-1 losing its WAN interface; an upstream ISP fault that leaves the link up would not be detected without IP SLA.
- **Cleartext services and stored secrets.** POP3 and FTP to BACKUP-ARCHIVE remain unencrypted, and Packet Tracer stores type 5 MD5 secrets; HSRP authentication is not configured.
- **Simulation scope.** The ISP routers and public web server are simulated, and only ISP-A and CORE-1 failures were tested.

## 5 Future proposition and conclusion

### 5.1 Future proposition

The proposals below close the limitations in 4.7 and prepare MSS for growth:

| Proposal | Benefit for MSS |
|---|---|
| Catalyst 9200/9300 access with StackWise | Stacked, dual-homed members per floor remove the access-switch single point |
| 10G fibre uplinks | Uses the proposed OM4 riser routes for growth in inter-department data transfer |
| IP SLA ISP tracking | Detects upstream ISP faults, not just link loss, and moves the default to EDGE-2 |
| NGFW at the edge | Adds application inspection and intrusion prevention beyond the reply-only OUTSIDE-IN ACL [16] |
| 802.1X/NAC | Authenticates devices against the existing RADIUS service before port access, complementing port security |
| Wireless with controller | Uses the 3650 PoE+ capacity; WLANs mapped to the existing departmental VLANs and ACLs |
| SIEM | Correlates the syslog already centralised on the NMS for faster incident detection [13] |
| IPv6 dual stack | The per-VLAN plan maps directly to IPv6 prefixes |
| Encrypted mail and file protocols | IMAPS/POP3S and SFTP remove remaining cleartext credentials [12]; type 8/9 secrets on production IOS |
| Offsite/immutable backup | Copies of DB-REPLICA and BACKUP-ARCHIVE outside the server room protect against room-level loss and ransomware |

### 5.2 Summary and conclusion

The group has designed and implemented a secure, resilient network for MSS Ltd. A collapsed core of two Catalyst 3650 switches suits a 60-user, three-floor site, giving device redundancy without the cost of a distribution layer, while dual-homed access switches and about 40% spare ports allow growth. Nine VLANs separate departments, services, data, backup and management; core ACLs let every employee reach every departmental database over HTTPS while isolating backup and management. Defence in depth extends from port security, DHCP snooping and DAI at the access layer to SSH-only, RADIUS-backed management and an anti-spoofing, reply-only edge.

Testing in Packet Tracer confirmed the required behaviour: relayed DHCP, internal DNS, HTTPS-only intranet, cross-department database access, backup and management isolation, PAT, and failover from both ISP-A and CORE-1. Configuration generated from one source and checked automatically keeps the network reproducible and auditable, and the future proposition gives MSS a staged path to close the residual risks.
