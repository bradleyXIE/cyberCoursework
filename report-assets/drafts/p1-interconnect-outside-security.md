### 4.3 Interconnectivity between sections and floors

Each department, server zone and the management network has its own VLAN and a /24 from 10.10.0.0/16 [7]. The third octet equals the VLAN ID, so an address identifies its zone at a glance, and each /24 leaves ample room beyond today's 15–25 hosts per department. Gateways follow the plan below; server addresses are listed after it.

| VLAN | Name | Subnet | HSRP active | Role |
|---|---|---|---|---|
| 10 / 20 / 30 | MARKETING / SALES / GEN-SUPPORT | 10.10.10/20/30.0/24 | CORE-1 / CORE-2 / CORE-1 | Workstations, floors 1–3 |
| 40 | SERVICES | 10.10.40.0/24 | CORE-2 | Intranet, e-mail, DNS |
| 50 | DATA | 10.10.50.0/24 | CORE-1 | Departmental application and database servers |
| 60 | BACKUP | 10.10.60.0/24 | CORE-2 | Database replica and archive |
| 99 | MGMT | 10.10.99.0/24 | CORE-1 | Device management, NMS, ADMIN-PC |
| 900 | CORE-TRANSIT | 10.10.254.0/29 | – | Routed link between cores |
| 999 | PARKING | not routed | – | Native VLAN and unused ports |

| Server | Address | VLAN | Role | Switch port |
|---|---|---|---|---|
| INTRANET | 10.10.40.10 | 40 | Intranet (HTTPS), primary DNS, DHCP .11–.130 | DC-SW-A Fa0/1 |
| MAIL | 10.10.40.11 | 40 | SMTP/POP3, secondary DNS zone, DHCP .131–.250 | DC-SW-A Fa0/2 |
| DB-MKT / DB-SALES / DB-GS | 10.10.50.11 / .12 / .13 | 50 | Departmental application and database servers | DC-SW-A Fa0/3–5 |
| DB-REPLICA | 10.10.60.10 | 60 | Backup database server | DC-SW-B Fa0/1 |
| BACKUP-ARCHIVE | 10.10.60.11 | 60 | Backup and archive (FTP) | DC-SW-B Fa0/2 |
| NMS | 10.10.99.10 | 99 | Syslog, NTP, RADIUS | DC-SW-B Fa0/3 |
| ADMIN-PC | 10.10.99.50 | 99 | Administrator workstation | DC-SW-B Fa0/4 |

**Inter-VLAN routing and gateways.** Routing is performed on the SVIs of both cores, so inter-department traffic stays in the server room and the 2960 access switches remain Layer 2 only. On each routed VLAN CORE-1 holds .2, CORE-2 .3, and the gateway .1 is an HSRP virtual address [4]. HSRP version 2 is used (a Cisco extension of the protocol in RFC 2281 [4]); priorities 110/100 with preempt make CORE-1 active for VLANs 10/30/50/99 and CORE-2 for 20/40/60, so both cores carry traffic. Rapid-PVST root priorities (4096/8192) follow the same split, aligning the Layer 2 path with the active gateway [5]; the cores are also root for VLANs 900 and 999 so that root guard never blocks a downlink (Figure 02, Figure 03). When CORE-1 was isolated, CORE-2 became active for all seven groups about 8 s later and a Marketing PC kept Internet and intranet access; preempt restored the original roles afterwards (Figure 10a, Figure 10b).

**Trunks.** Every access and server-room switch is dual-homed (Gi0/1 to CORE-1, Gi0/2 to CORE-2), so losing one uplink or one core does not isolate a floor. Each trunk allows only the VLANs its switch needs – ACC-F1-MKT carries 10 and 99, DC-SW-B 60 and 99 – so a compromised switch cannot observe other zones. The native VLAN is the unrouted VLAN 999 and DTP is disabled (nonegotiate), removing the usual VLAN-hopping routes. The cores are joined by an LACP bundle (Port-channel1, Gi1/0/23–24) [6], so one failed cable does not separate them.

**OSPF.** The cores and both edges form area 0 [3]: core to core over VLAN 900 on Port-channel1, and each core to each edge over a /30 link. With passive-interface default, no device on a user VLAN can form an adjacency, and MD5 authentication on every routed link stops a rogue router injecting a false default route to divert MSS traffic. Figure 02 shows CORE-1 FULL with 10.10.0.2, 10.10.0.3 and 10.10.0.4.

**DHCP relay.** Both cores relay requests from VLANs 10, 20 and 30 to INTRANET (10.10.40.10) and MAIL (10.10.40.11) [9]. INTRANET leases .11–.130 and MAIL .131–.250 of each user VLAN, so the scopes never overlap and are designed to survive the loss of either server or either core; DHCP-server failure itself was not tested in Packet Tracer. Figure 04 shows MKT-PC01 receiving 10.10.10.171 from MAIL through the relay. The first design split each scope between DHCP pools on the two cores; testing showed that Packet Tracer's IOS DHCP honoured only one excluded-address range per subnet, so the pools overlapped. Moving the scopes to the servers removed the defect – a change driven directly by testing.

**DNS.** INTRANET is primary and MAIL secondary for mss.lan (intranet, mail, db-marketing, db-sales, db-support), plus www.public.test for the simulated Internet. Users reach services by name and a server can be re-addressed by changing one record (Figure 05). Packet Tracer's DHCP pools hand out a single DNS server (INTRANET), so MAIL's copy of the zone is the manual fallback; production DHCP would advertise both resolvers.

### 4.4 Outside connections

EDGE-1 connects to ISP-A (203.0.113.0/30) and EDGE-2 to ISP-B (198.51.100.0/30) through separate building ducts, so no single router, provider or cable failure removes Internet access. Each edge has a routed link to both cores, so either edge stays reachable when one core fails.

**PAT.** Each edge translates 10.10.0.0/16 (access-list 1) to its WAN address with overload on Gi0/2. MSS needs only one public address per provider, which suits the limited budget, and internal addressing is never exposed (Figure 07, Figure 06d).

**OUTSIDE-IN ACL.** Applied inbound on each WAN interface [16], it drops RFC 1918 and loopback sources, which can only be spoofed when arriving from the Internet [17], then permits only established TCP, echo-reply and unreachable messages. MSS publishes no public services: external mail is assumed to be received and filtered by the provider's mail relay, which MAIL reaches through outbound sessions, so OUTSIDE-IN needs no unsolicited inbound rule. CDP is disabled on the WAN so device details are not advertised to the provider.

**Primary/standby failover.** Only EDGE-1 originates a default route into OSPF; each core also holds a floating static default (AD 250) towards EDGE-2, used only when the OSPF default disappears. This was chosen because the Packet Tracer 2911 image has no IP SLA or object tracking and Packet Tracer ignored OSPF default-route metrics. With EDGE-1 Gi0/2 shut, CORE-1's default moved to the static route via 10.10.255.10 and a Marketing PC reached 192.0.2.10 via ISP-B (4/4, TTL 124) once ARP had resolved; restoring the interface returned the default to EDGE-1 automatically (Figure 09a–09c). As failover reacts only to EDGE-1 losing its own path, IP SLA tracking of the ISP path is recommended in production.

**Simulated Internet.** Provider links and the public web server use the RFC 5737 ranges 192.0.2.0/24, 198.51.100.0/24 and 203.0.113.0/24 [8], so no real organisation's addresses appear; provider-assigned addresses replace them in deployment without internal changes.

### 4.5 Protocols, software and security

**Inter-VLAN policy.** Named ACLs on both cores enforce the zone policy whichever core is active.

| ACL (applied) | Permitted | Denied | Threat addressed |
|---|---|---|---|
| USERS-IN (in, VLANs 10/20/30) | DHCP; DNS; HTTPS to INTRANET; SMTP/POP3 to MAIL; HTTPS to all DATA servers; ping; Internet | VLANs 60 and 99; infrastructure links; plain HTTP and other server ports; host-to-host traffic between departments (except ping) | Compromised workstation reaching backups or management; lateral movement; cleartext intranet logins |
| BACKUP-OUT (out, VLAN 60) | DATA, SERVICES and MGMT sources | Everything else, including user VLANs | Deletion or encryption of replica and archive from a user host |
| MGMT-OUT (out, VLAN 99) | Return traffic; syslog, NTP, RADIUS to NMS | Everything else | Attacks on NMS, RADIUS and ADMIN-PC |

Every department reaches every departmental database, as required, but only through the HTTPS front end in VLAN 50, so data sharing passes through controlled servers rather than between workstations. Figure 05, Figure 06a–06c and the USERS-IN hit counters in Figure 11 show allowed and denied flows. The vulnerability lab reproduced this isolation for V1 by detaching the backup database from the employee network (E04, E05). Replication and archiving are procedural and not simulated in Packet Tracer: DB-MKT, DB-SALES and DB-GS replicate to DB-REPLICA over the VLAN 50 to 60 path that BACKUP-OUT permits, nightly exports go to BACKUP-ARCHIVE by FTP (SFTP in production), and restores are tested quarterly (Section 9).

**Access-layer protections** [2]:

| Control | Threat addressed |
|---|---|
| Port-security, sticky, restrict (max 2 MACs workstations, 1 servers) | MAC flooding; unauthorised devices at desk outlets (Figure 08) |
| DHCP snooping, trusted uplinks, 20 pps limit | Rogue DHCP server; DHCP starvation (Figure 08) |
| Dynamic ARP Inspection on user VLANs | ARP spoofing and man-in-the-middle |
| PortFast + BPDU guard; root guard on core downlinks | Rogue switch seizing the STP root |
| Nonegotiate trunks, native VLAN 999, allowed lists | VLAN hopping |
| Unused ports shut in VLAN 999; CDP off on user ports | Patching into spare outlets; reconnaissance |

**Device hardening.** All MSS-owned IOS devices accept SSH version 2 only (RSA 2048), and an access-class limits VTY lines to VLAN 99: SSH from ADMIN-PC reaches the prompt while MKT-PC01 times out (Figure 12a, Figure 12b). AAA uses RADIUS on the NMS for individual administrator accounts (Figure 14), with local fallback if the NMS fails; the console authenticates locally. Enable secret, service password-encryption, exec timeouts, a legal banner and a disabled HTTP server complete the baseline, and routers and cores block logins for 120 s after three failures in 60 s (the Packet Tracer 2960 image rejects this command, so the six switches rely on the VTY access-class and RADIUS).

**Logging and time.** All devices send syslog to the NMS and take NTP from it, so events from different devices can be correlated during an investigation (Figure 13).

**Server services.** Each server runs only its role – HTTPS on INTRANET and the departmental servers, SMTP/POP3 on MAIL, FTP on BACKUP-ARCHIVE, DNS and DHCP on INTRANET and MAIL – with unused services, including the default FTP account and plain HTTP, disabled to shrink the attack surface (Figure 06b). FTP and POP3 remain cleartext and are treated as residual risks.