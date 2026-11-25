# Part 1: Implementation

## 1 Introduction, aim and overview

### 1.1 Introduction

This report presents the group's network design for MSS Ltd, an organisation of three departments housed on three floors of one building. The design was implemented and tested in Cisco Packet Tracer 9.0.1 [15] (file CW_CST4562-Implementation.pkt). It was produced to meet the brief's requirements for shared services, departmental data, backup and redundancy within a limited budget. The report also includes a vulnerability analysis of the most serious risks to MSS, with the matching defence mechanisms and a maintenance guideline.

### 1.2 Aim and objectives

The aim is to design, implement and test a secure, resilient and cost-conscious network that gives every MSS employee the services the brief requires, and to show by testing that the security and redundancy measures work.

The objectives are to:

1. analyse the scenario and turn the brief's requirements and assumptions into measurable design requirements (Section 2);
2. design a topology, VLAN/IP plan and cabling plan sized for current users with room for growth (Figure 00, Figure 01);
3. provide Internet, intranet, e-mail and departmental database access for all employees, with a separate backup database and archive;
4. remove single points of failure at the core, server, edge and ISP levels where the budget allows;
5. apply layered security controls and prove each one with a Packet Tracer test (Figures 02–14);
6. analyse vulnerabilities with appropriate tools, show the defence for each one, and propose a maintenance schedule.

### 1.3 Overview of the present scenario

MSS Ltd has 60 workstations: Marketing on floor 1 (20), Sales on floor 2 (25) and General Support on floor 3 (15). Each department mostly uses its own applications and keeps its own database of local information. However, some applications move data between departments, and every employee must be able to reach every departmental database. All staff need Internet, intranet and e-mail. The brief assumes departmental servers for applications and large data sets, e-mail and intranet servers, database and backup database servers, a backup/archive server, a redundancy plan, and ongoing vulnerability analysis and maintenance. The budget is limited, but MSS is willing to pay for quality.

## 2 Analysis of the present scenario and requirements

### 2.1 Analysis

**User counts and growth.** With 15–25 users per floor, the design needs one access switch on floors 1 and 3 and two on floor 2. Sales needs 25 ports, which is more than one 24-port switch provides, so it is split across two switches (13 and 12 ports). This leaves 23 spare ports on floor 2 and about 40% spare access ports overall. A /24 subnet per department (254 hosts compared with 15–25 today) means growth will not force re-addressing.

**Scale and topology.** Sixty users in one building do not justify a separate distribution layer, which would add cost, devices and failure points. A collapsed core of two multilayer switches gives device redundancy at lower cost, and the design can later grow by adding access switches or a distribution pair.

**Cross-department data access.** All employees need access to every departmental database, so the database servers cannot sit inside the departmental VLANs. They are placed in a shared DATA VLAN that is reachable over HTTPS from every user VLAN (Figure 06c). Direct host-to-host traffic between departments is denied, except ICMP echo kept for support. This means data moves between departments only through the departmental servers, which limits lateral movement.

**Availability.** Every department depends on shared servers and the Internet. A failure at the core, the edge or the ISP would therefore affect the whole company, so each of these layers is duplicated. The backup copy of the data must survive a failure of the primary, so the replica and archive are installed in a separate rack and on a separate switch from the primary servers.

**Security.** The backup database and the management plane hold the most sensitive assets. Users have no business need to reach them directly, so they are isolated from the user VLANs (Figure 05, Figure 12b). The user population is internal and on shared floors, so the access layer needs controls against rogue devices, spoofing and MAC flooding.

**Budget.** Fixed-configuration access switches are used where only Layer 2 and security features are needed. Routing, HSRP, DHCP relay and ACLs are concentrated on the two cores. Configuration as code reduces the cost of maintenance and rebuilds.

### 2.2 Requirements

| # | Brief requirement / assumption | Design element that satisfies it | Evidence |
|---|---|---|---|
| R1 | Internet access for all | Dual edge routers with PAT; OSPF default route from EDGE-1 | Figure 06d, Figure 07 |
| R2 | Intranet for all | INTRANET server (10.10.40.10), HTTPS only, primary DNS | Figure 06a, Figure 06b |
| R3 | E-mail for all | MAIL server (10.10.40.11), SMTP/POP3, secondary DNS; Internet mail via the provider's relay | Configured (USERS-IN SMTP/POP3 entries, 4.5); not tested end to end in Packet Tracer |
| R4 | Departmental servers for applications and large data sets | DB-MKT, DB-SALES and DB-GS in DATA VLAN 50 with an HTTPS front end | Figure 06c |
| R5 | All employees can access any departmental database | USERS-IN permits HTTPS from every user VLAN to 10.10.50.0/24 | Figure 05, Figure 06c, Figure 11 |
| R6 | Backup database server | DB-REPLICA (10.10.60.10) in isolated VLAN 60 on DC-SW-B/Rack B | Figure 05 (users denied) |
| R7 | Backup/archive server | BACKUP-ARCHIVE (10.10.60.11); BACKUP-OUT allows only the data, services and management zones | Server table (4.3), ACL table (4.5) |
| R8 | Redundancy plan for system failure | Dual cores (HSRP), dual-homed switches, LACP Po1, dual PSUs, dual edges/ISPs, two DHCP servers, secondary DNS zone on MAIL | Figure 02, Figure 09a–c, Figure 10a–b |
| R9 | Security, vulnerability analysis and maintenance | VLAN segmentation and ACLs, access-layer controls, device hardening, Docker/Kali test lab, maintenance schedule | Figure 08, Figure 11–14; vulnerability section |
| R10 | Limited budget, quality investment | Collapsed core, fixed access switches, configuration as code with drift check | Qualitative justification (2.1, 4.1); no costed bill of materials |

### 2.3 Assumptions

- MSS occupies a single building with three floors; one department per floor, as stated in the brief (Figure 00).
- A lockable room on floor 1 is available as the secure server room (MDF), with badge access, UPS and A/B power feeds, and space for two racks. Each floor has a small IDF for its access switch or switches.
- Two separate building ducts allow two vertical riser routes, one to each core.
- MSS can contract Internet circuits from two different providers (ISP-A primary, ISP-B standby). In the simulation these are routers using RFC 5737 documentation addresses [8].
- Workstation counts are as stated in the brief; growth is expected but has not been quantified.
- Each server role is represented by one Packet Tracer server with a single NIC. In production, dual-homed servers would be specified.
- Packet Tracer limitations were accepted and documented. The 2960-24TT stands in for production Catalyst 9200 access switches. Copper Gigabit uplinks represent the proposed OM4 fibre risers. IP SLA/object tracking is not available, so a floating static default route (AD 250) was used.
