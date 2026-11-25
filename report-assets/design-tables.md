## VLAN and addressing plan

| VLAN | Name | Subnet | Gateway (HSRP VIP) | CORE-1 / CORE-2 | HSRP active | Purpose |
|---|---|---|---|---|---|---|
| 10 | MARKETING | 10.10.10.0/24 | 10.10.10.1 | 10.10.10.2 / 10.10.10.3 | CORE-1 | F1 Marketing, 20 workstations |
| 20 | SALES | 10.10.20.0/24 | 10.10.20.1 | 10.10.20.2 / 10.10.20.3 | CORE-2 | F2 Sales, 25 workstations |
| 30 | GEN-SUPPORT | 10.10.30.0/24 | 10.10.30.1 | 10.10.30.2 / 10.10.30.3 | CORE-1 | F3 General Support, 15 workstations |
| 40 | SERVICES | 10.10.40.0/24 | 10.10.40.1 | 10.10.40.2 / 10.10.40.3 | CORE-2 | Intranet, e-mail and DNS |
| 50 | DATA | 10.10.50.0/24 | 10.10.50.1 | 10.10.50.2 / 10.10.50.3 | CORE-1 | Departmental application and database servers |
| 60 | BACKUP | 10.10.60.0/24 | 10.10.60.1 | 10.10.60.2 / 10.10.60.3 | CORE-2 | Backup database replica and archive (isolated) |
| 99 | MGMT | 10.10.99.0/24 | 10.10.99.1 | 10.10.99.2 / 10.10.99.3 | CORE-1 | Device management, NMS, admin workstation |
| 900 | CORE-TRANSIT | 10.10.254.0/29 | - | 10.10.254.1 / .2 | - | Routed transit between the two cores |
| 999 | PARKING | none (not routed) | - | - | - | Native VLAN and unused ports, never routed |

## DHCP scopes (relayed by both cores)

| Server | VLAN 10 | VLAN 20 | VLAN 30 |
|---|---|---|---|
| INTRANET (10.10.40.10) | 10.10.10.11-10.10.10.130 | 10.10.20.11-10.10.20.130 | 10.10.30.11-10.10.30.130 |
| MAIL (10.10.40.11) | 10.10.10.131-10.10.10.250 | 10.10.20.131-10.10.20.250 | 10.10.30.131-10.10.30.250 |

## Servers

| Server | Address | VLAN | Role | Switch port |
|---|---|---|---|---|
| INTRANET | 10.10.40.10/24 | 40 | Intranet (HTTPS) and primary DNS | DC-SW-A FastEthernet0/1 |
| MAIL | 10.10.40.11/24 | 40 | SMTP/POP3 e-mail and secondary DNS | DC-SW-A FastEthernet0/2 |
| DB-MKT | 10.10.50.11/24 | 50 | Marketing application and database server | DC-SW-A FastEthernet0/3 |
| DB-SALES | 10.10.50.12/24 | 50 | Sales application and database server | DC-SW-A FastEthernet0/4 |
| DB-GS | 10.10.50.13/24 | 50 | General Support application and database server | DC-SW-A FastEthernet0/5 |
| DB-REPLICA | 10.10.60.10/24 | 60 | Backup database server (replica of all three) | DC-SW-B FastEthernet0/1 |
| BACKUP-ARCHIVE | 10.10.60.11/24 | 60 | Backup and archive server (FTP target) | DC-SW-B FastEthernet0/2 |
| NMS | 10.10.99.10/24 | 99 | Syslog, NTP and RADIUS AAA | DC-SW-B FastEthernet0/3 |
| ADMIN-PC | 10.10.99.50/24 | 99 | Network administrator workstation | DC-SW-B FastEthernet0/4 |

## Switch management addresses

| Switch | Floor / room | Mgmt IP | Uplinks |
|---|---|---|---|
| ACC-F1-MKT | F1 IDF, 20 workstation ports (VLAN 10) | 10.10.99.21 | Gi0/1->CORE-1 GigabitEthernet1/0/1, Gi0/2->CORE-2 GigabitEthernet1/0/1 |
| ACC-F2-SALES1 | F2 IDF, 13 workstation ports (VLAN 20) | 10.10.99.22 | Gi0/1->CORE-1 GigabitEthernet1/0/2, Gi0/2->CORE-2 GigabitEthernet1/0/2 |
| ACC-F2-SALES2 | F2 IDF, 12 workstation ports (VLAN 20) | 10.10.99.23 | Gi0/1->CORE-1 GigabitEthernet1/0/3, Gi0/2->CORE-2 GigabitEthernet1/0/3 |
| ACC-F3-GS | F3 IDF, 15 workstation ports (VLAN 30) | 10.10.99.24 | Gi0/1->CORE-1 GigabitEthernet1/0/4, Gi0/2->CORE-2 GigabitEthernet1/0/4 |
| DC-SW-A | Server room, VLANs 40, 50 | 10.10.99.25 | Gi0/1->CORE-1 GigabitEthernet1/0/5, Gi0/2->CORE-2 GigabitEthernet1/0/5 |
| DC-SW-B | Server room, VLANs 60, 99 | 10.10.99.26 | Gi0/1->CORE-1 GigabitEthernet1/0/6, Gi0/2->CORE-2 GigabitEthernet1/0/6 |

## Routed links

| Link | Addresses |
|---|---|
| CORE-1 GigabitEthernet1/0/21 - EDGE-1 GigabitEthernet0/0 | 10.10.255.1 - 10.10.255.2 /30 |
| CORE-2 GigabitEthernet1/0/21 - EDGE-1 GigabitEthernet0/1 | 10.10.255.5 - 10.10.255.6 /30 |
| CORE-1 GigabitEthernet1/0/22 - EDGE-2 GigabitEthernet0/0 | 10.10.255.9 - 10.10.255.10 /30 |
| CORE-2 GigabitEthernet1/0/22 - EDGE-2 GigabitEthernet0/1 | 10.10.255.13 - 10.10.255.14 /30 |
| EDGE-1 Gi0/2 - ISP-A Gi0/0 | 203.0.113.2 - 203.0.113.1 /30 |
| EDGE-2 Gi0/2 - ISP-B Gi0/0 | 198.51.100.2 - 198.51.100.1 /30 |
| CORE-1 - CORE-2 (VLAN 900 over Po1) | 10.10.254.1 - 10.10.254.2 /29 |
| Loopbacks (router IDs) | CORE-1 10.10.0.1, CORE-2 10.10.0.2, EDGE-1 10.10.0.3, EDGE-2 10.10.0.4 |

## ACL USERS-IN (inbound on VLAN 10/20/30 SVIs)
```
remark DHCP to the core relay/servers
permit udp any any eq bootps
remark replies to admin troubleshooting
permit icmp any 10.10.99.0 0.0.0.255 echo-reply
remark protected zones: backup, management, infrastructure
deny ip any 10.10.60.0 0.0.0.255
deny ip any 10.10.99.0 0.0.0.255
deny ip any 10.10.254.0 0.0.0.255
deny ip any 10.10.255.0 0.0.0.255
deny ip any 10.10.0.0 0.0.0.255
remark shared services
permit udp any host 10.10.40.10 eq domain
permit udp any host 10.10.40.11 eq domain
permit tcp any host 10.10.40.10 eq 443
permit tcp any host 10.10.40.11 eq smtp
permit tcp any host 10.10.40.11 eq pop3
permit icmp any 10.10.40.0 0.0.0.255 echo
deny ip any 10.10.40.0 0.0.0.255
remark every department may use every departmental application/database over HTTPS
permit tcp any 10.10.50.0 0.0.0.255 eq 443
permit icmp any 10.10.50.0 0.0.0.255 echo
deny ip any 10.10.50.0 0.0.0.255
remark no direct host-to-host traffic between departments (ping allowed for support)
permit icmp any 10.10.0.0 0.0.255.255 echo
deny ip any 10.10.0.0 0.0.255.255
remark Internet
permit ip any any
```

## ACL BACKUP-OUT (outbound on VLAN 60)
```
remark only data, service and management zones may reach backup
permit ip 10.10.50.0 0.0.0.255 10.10.60.0 0.0.0.255
permit ip 10.10.40.0 0.0.0.255 10.10.60.0 0.0.0.255
permit ip 10.10.99.0 0.0.0.255 10.10.60.0 0.0.0.255
deny ip any any
```

## ACL MGMT-OUT (outbound on VLAN 99)
```
remark return traffic for admin sessions
permit tcp any 10.10.99.0 0.0.0.255 established
permit icmp any 10.10.99.0 0.0.0.255 echo-reply
permit icmp any 10.10.99.0 0.0.0.255 unreachable
permit udp any eq domain 10.10.99.0 0.0.0.255
remark device telemetry and AAA towards the NMS
permit udp 10.10.0.0 0.0.255.255 host 10.10.99.10 eq 514
permit udp 10.10.0.0 0.0.255.255 host 10.10.99.10 eq 123
permit udp 10.10.0.0 0.0.255.255 host 10.10.99.10 eq 1645
permit udp 10.10.0.0 0.0.255.255 host 10.10.99.10 eq 1646
deny ip any any
```

## ACL OUTSIDE-IN (inbound on EDGE WAN)
```
remark anti-spoofing: private and loopback sources never arrive from the Internet
deny ip 10.0.0.0 0.255.255.255 any
deny ip 172.16.0.0 0.15.255.255 any
deny ip 192.168.0.0 0.0.255.255 any
deny ip 127.0.0.0 0.255.255.255 any
remark only replies to sessions opened from inside
permit tcp any any established
permit icmp any any echo-reply
permit icmp any any unreachable
deny ip any any
```
