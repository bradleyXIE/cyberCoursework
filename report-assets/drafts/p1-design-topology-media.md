## 3 Proposed LAN design

### 3.1 Building and room plan

The building plan (Figure 00) places an Intermediate Distribution Frame (IDF) on each floor beside the department it serves, and a secure floor-1 server room that acts as the Main Distribution Frame (MDF). This keeps both ISP entries, the core and the servers in one controlled room.

[[FIG:fig00-building-plan.png|Figure 00 – Building and room plan: floor IDFs, dual risers and the floor-1 server room (not to scale)]]

| Floor | Department | IDF switch(es) | Ports used / available | Spare |
|---|---|---|---|---|
| 1 | Marketing (20) | ACC-F1-MKT | 20 / 24 | 4 |
| 2 | Sales (25) | ACC-F2-SALES1, ACC-F2-SALES2 | 13 + 12 / 48 | 23 |
| 3 | General Support (15) | ACC-F3-GS | 15 / 24 | 9 |

Sales needs more than one 24-port switch, so floor 2 receives two, which also gives it the largest growth margin. Overall 36 of 96 access ports (close to 40%) are spare, so departments can add staff without new hardware. Unused ports are shut and placed in the non-routed VLAN 999, so spare capacity is not an open entry point.

The server room has badge access, a UPS and separate A and B power feeds, and holds two mirrored racks:

- **Rack A:** CORE-1, EDGE-1, DC-SW-A and the primary servers (INTRANET, MAIL, DB-MKT, DB-SALES, DB-GS).
- **Rack B:** CORE-2, EDGE-2, DC-SW-B, DB-REPLICA, BACKUP-ARCHIVE, NMS and ADMIN-PC.

Each database and its replica therefore sit in different racks, on different switches and on different power feeds, so no single rack, switch or feed failure removes both copies of MSS data. Each IDF is reached by two physically separate risers (Riser A to CORE-1, Riser B to CORE-2), and ISP-A and ISP-B enter through separate building ducts, so one damaged route cannot isolate a floor or cut both Internet services.

### 3.2 Logical design overview

The logical topology (Figure 01) divides the network into security zones; each user, server and management zone is a VLAN with a /24 in 10.10.0.0/16 [7], the core transit uses a /29 and VLAN 999 is never routed.

[[FIG:fig01-logical-topology.jpg|Figure 01 – Logical topology of the MSS Ltd network in Packet Tracer 9.0.1 (CW_CST4562-Implementation.pkt)]]

| Zone | VLAN | Contents | Policy intent |
|---|---|---|---|
| Users | 10, 20, 30 | Departmental workstations | Services, all departmental databases (HTTPS) and Internet; no host-to-host traffic between departments except ping |
| Services | 40 | INTRANET, MAIL, DNS | Shared by all staff |
| Data | 50 | DB-MKT, DB-SALES, DB-GS | Every department may use every database |
| Backup | 60 | DB-REPLICA, BACKUP-ARCHIVE | Only data, services and management zones |
| Management | 99 | NMS, ADMIN-PC, switch management | Only return traffic and syslog/NTP/RADIUS |
| Infrastructure | 900 | Core-to-core transit | Not reachable by users |
| Parking | 999 | Native VLAN, unused ports | Never routed |
| Edge | – | EDGE-1/2 to ISP-A/B | PAT outbound, replies only inbound |

Because the gateways (HSRP virtual IP .1) and inter-VLAN ACLs sit on the cores, every inter-zone flow crosses an enforcement point, while traffic within a department stays on its floor switch.

## 4 Details of the proposed LAN design

### 4.1 Topology and architecture

Two cores serve MSS's three floors directly, with no separate distribution layer. For 60 users in one three-storey building, a separate distribution layer would add devices, cost and failure points without providing capacity or resilience MSS needs; redundancy comes from duplicating the core instead. Growth remains possible by adding access switches or stacks, or a distribution pair later.

Every access switch and both server-room switches are dual-homed (Gi0/1 to CORE-1, Gi0/2 to CORE-2). The cores are joined by an LACP EtherChannel, Port-channel1 on Gi1/0/23–24 [6], which survives the loss of one member and also carries transit VLAN 900; Figure 02 shows Po1 in use with both members bundled.

Both cores carry traffic rather than one standing idle: gateway and spanning-tree roles are split per VLAN, as detailed in 4.3.

Two 2911 edge routers each have a routed link to both cores, so losing one core or one edge router still leaves an Internet path; EDGE-1 serves ISP-A (primary) and EDGE-2 serves ISP-B (standby).

**Device choices.** The Catalyst 3650-24PS is used only at the core, because only the core needs Layer 3 routing, HSRP, DHCP relay, ACLs and LACP; its two AC power supplies match the A/B feeds and its PoE+ ports support future phones or access points [1]. The 2960-24TT serves the floors and server room, where only Layer 2 forwarding and port security (port-security, DHCP snooping, DAI) are needed [2]; keeping routing at the core keeps access hardware inexpensive within MSS's limited budget. The 2911 provides NAT and WAN filtering at each ISP boundary. Packet Tracer limits the access model to the 2960-24TT (24 Fast Ethernet ports, two Gigabit uplinks); for production the group recommends Catalyst 9200 access switches.

| Device | Model | Qty | Location | Role |
|---|---|---|---|---|
| CORE-1, CORE-2 | Catalyst 3650-24PS, dual AC PSU | 2 | Racks A/B | Routing, HSRP, OSPF, DHCP relay, ACLs, LACP |
| ACC-F1-MKT, ACC-F2-SALES1/2, ACC-F3-GS | Catalyst 2960-24TT | 4 | Floor IDFs | Workstation access, port security |
| DC-SW-A, DC-SW-B | Catalyst 2960-24TT | 2 | Racks A/B | Services/data (A); backup/management (B) |
| EDGE-1, EDGE-2 | Cisco 2911 | 2 | Racks A/B | PAT and inbound filtering to ISP-A/ISP-B |
| Servers | – | 8 | Racks A/B | Services, data, backup, NMS |
| Workstations and ADMIN-PC | – | 61 | Floors 1–3; VLAN 99 | 20 + 25 + 15 users; administration |

The ISP routers (2901) and public web server only simulate the Internet and are not MSS equipment.

### 4.2 Media and cabling

**Horizontal.** Desk outlets are cabled with Cat6 U/UTP to a patch panel in the floor IDF, with each permanent link within 90 m [10]. An IDF on every floor keeps desk runs short enough to meet this limit without further telecommunications rooms, and Cat6 gives the Gigabit and PoE headroom that the phones and access points proposed in 5.1 need.

**Riser.** Each riser uplink aggregates a whole department, so bandwidth and resilience matter most there. The group recommends OM4 multimode fibre with 1G/10G SFP modules on both risers: uplinks can move to 10 Gb/s without re-cabling as departmental data sets grow. In Packet Tracer the 2960-24TT copper Gigabit uplinks (Gi0/1, Gi0/2) are the functional equivalent; the logical design is unchanged.

**Server room.** Short Cat6A patch leads connect servers, server-room switches and cores, giving 10G headroom on the densest runs.

**Routes and labelling.** Riser A and Riser B follow separate routes and the ISP circuits use separate ducts, so one route failure affects only one member of each redundant pair. Every cable is labelled at both ends as `<room>-<rack>-<panel>-<port>`, and leads are colour-coded by VLAN class, so a technician can trace a fault to a specific port and spot a wrongly patched management or backup port during inspection.
