[[PAGEBREAK]]
# Appendices
## Appendix A: Packet Tracer test evidence

All screenshots were taken in Cisco Packet Tracer 9.0.1 on 25 November 2026 from a verification copy of CW_CST4562-Implementation.pkt whose console lines open in privileged mode; the network configuration is otherwise identical to the submitted file.

[[FIG:fig02-core1-hsrp-lacp-ospf.jpg|Figure 02 – CORE-1: show standby brief, show etherchannel summary and show ip ospf neighbor]]

[[FIG:fig03-core1-route-stp.jpg|Figure 03 – CORE-1 routing table (default via EDGE-1) and RSTP root for VLAN 10]]

[[FIG:fig04-pc-dhcp-relay.jpg|Figure 04 – MKT-PC01 receives 10.10.10.171 from MAIL (10.10.40.11) through the core DHCP relay]]

[[FIG:fig05-pc-acl-tests.jpg|Figure 05 – Policy tests from MKT-PC01: NMS and DB-REPLICA blocked, Internet and DB-SALES allowed]]

[[FIG:fig06a-browser-intranet-https.jpg|Figure 06a – https://intranet.mss.lan loads from a Marketing PC]]

[[FIG:fig06b-browser-intranet-http-blocked.jpg|Figure 06b – plain http://intranet.mss.lan is refused (Request Timeout)]]

[[FIG:fig06c-browser-db-sales-cross-dept.jpg|Figure 06c – Marketing PC opens the Sales application/database front end over HTTPS]]

[[FIG:fig06d-browser-public-web-nat.jpg|Figure 06d – Marketing PC reaches the simulated public web site through PAT]]

[[FIG:fig07-edge1-nat-pat.jpg|Figure 07 – EDGE-1 PAT translation 10.10.10.171:1028 to 203.0.113.2:1028]]

[[FIG:fig08-access-portsec-snooping.jpg|Figure 08 – ACC-F1-MKT port security and DHCP snooping status]]

[[FIG:fig09a-edge1-wan-shutdown.jpg|Figure 09a – ISP-A failure simulated by shutting EDGE-1 Gi0/2]]

[[FIG:fig09b-core1-floating-default.jpg|Figure 09b – CORE-1 default route moves to the floating static via EDGE-2 (AD 250)]]

[[FIG:fig09c-pc-ping-via-isp-b.jpg|Figure 09c – Marketing PC reaches the Internet via ISP-B (TTL 124) during the ISP-A failure]]

[[FIG:fig10a-core2-hsrp-takeover.jpg|Figure 10a – CORE-1 isolated: CORE-2 becomes active for all seven HSRP groups]]

[[FIG:fig10b-pc-during-core1-failure.jpg|Figure 10b – Marketing PC keeps Internet and intranet access while CORE-1 is down]]

[[FIG:fig11-core1-acl-counters.jpg|Figure 11 – USERS-IN hit counters on CORE-1]]

[[FIG:fig12a-admin-ssh-reachable.jpg|Figure 12a – SSH from ADMIN-PC (VLAN 99) reaches the switch login prompt]]

[[FIG:fig12b-user-ssh-blocked.jpg|Figure 12b – SSH from MKT-PC01 is blocked]]

[[FIG:fig13-nms-central-syslog.jpg|Figure 13 – NMS receives syslog from both cores]]

[[FIG:fig14-nms-radius-aaa-masked.jpg|Figure 14 – NMS RADIUS clients and administrator account (keys masked)]]
