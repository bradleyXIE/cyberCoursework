## Appendix B: Configuration excerpts

Excerpts from the running configuration saved by Packet Tracer in CW_CST4562-Implementation.pkt. Password hashes and shared keys are removed. The full configurations of all 13 IOS devices are in the .pkt file and are generated from implementation-lab/packet-tracer/design.py.

### B.1 CORE-1 (gateway, HSRP, trunks, routed uplink, OSPF, AAA)

```
aaa new-model
aaa authentication login CONSOLE local 
aaa authentication login default group radius local 
ip ssh version 2
ip ssh time-out 60
interface Port-channel1
 description LACP bundle to CORE-2 (Gi1/0/23-24)
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,30,40,50,60,99,900
 switchport mode trunk
 switchport nonegotiate
interface GigabitEthernet1/0/1
 description Downlink to ACC-F1-MKT
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,99
 switchport mode trunk
 switchport nonegotiate
 spanning-tree guard root
interface GigabitEthernet1/0/21
 description Routed link to EDGE-1 GigabitEthernet0/0
 no switchport
 ip address 10.10.255.1 255.255.255.252
 ip ospf message-digest-key 1 md5 <key removed>
 duplex auto
 speed auto
interface Vlan10
 description F1 Marketing, 20 workstations
 mac-address 00e0.8faa.4101
 ip address 10.10.10.2 255.255.255.0
 ip helper-address 10.10.40.10
 ip helper-address 10.10.40.11
 ip access-group USERS-IN in
 standby version 2
 standby 10 ip 10.10.10.1
 standby 10 priority 110
 standby 10 preempt
router ospf 1
 router-id 10.10.0.1
 log-adjacency-changes
 area 0 authentication message-digest
 passive-interface default
 no passive-interface GigabitEthernet1/0/21
 no passive-interface GigabitEthernet1/0/22
 no passive-interface Vlan900
 network 10.10.0.0 0.0.255.255 area 0
ip route 0.0.0.0 0.0.0.0 10.10.255.10 250
line vty 0 4
 access-class 10 in
 login authentication default
 transport input ssh
```

### B.2 EDGE-1 (routed links, NAT/PAT, WAN filter)

```
interface GigabitEthernet0/0
 description Routed link to CORE-1 GigabitEthernet1/0/21
 ip address 10.10.255.2 255.255.255.252
 ip ospf message-digest-key 1 md5 <key removed>
 ip nat inside
 duplex auto
 speed auto
interface GigabitEthernet0/2
 description WAN to ISP-A
 ip address 203.0.113.2 255.255.255.252
 no ip proxy-arp
 ip nat outside
 ip access-group OUTSIDE-IN in
 duplex auto
 speed auto
 no cdp enable
router ospf 1
 router-id 10.10.0.3
 log-adjacency-changes
 area 0 authentication message-digest
 passive-interface default
 no passive-interface GigabitEthernet0/0
 no passive-interface GigabitEthernet0/1
 network 10.10.0.0 0.0.255.255 area 0
 default-information originate
ip nat inside source list 1 interface GigabitEthernet0/2 overload
ip route 0.0.0.0 0.0.0.0 203.0.113.1 
ip route 10.10.0.0 255.255.0.0 Null0 254
access-list 1 remark inside networks translated by PAT
access-list 1 permit 10.10.0.0 0.0.255.255
ip access-list extended OUTSIDE-IN
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

### B.3 ACC-F1-MKT (access-port template, unused port, uplink, management)

```
ip arp inspection vlan 10
ip dhcp snooping vlan 10
no ip dhcp snooping information option
ip dhcp snooping
spanning-tree mode rapid-pvst
interface FastEthernet0/1
 description MARKETING workstation F1-desk-01
 switchport access vlan 10
 ip dhcp snooping limit rate 20
 switchport mode access
 switchport nonegotiate
 switchport port-security
 switchport port-security maximum 2
 switchport port-security mac-address sticky 
 switchport port-security violation restrict 
 switchport port-security mac-address sticky 00D0.97C0.3CB5
 no cdp enable
 spanning-tree portfast
 spanning-tree bpduguard enable
interface FastEthernet0/21
 description UNUSED - parked and shut
 switchport access vlan 999
 switchport mode access
 shutdown
interface GigabitEthernet0/1
 description Uplink to CORE-1 GigabitEthernet1/0/1
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,99
 ip arp inspection trust
 ip dhcp snooping trust
 switchport mode trunk
 switchport nonegotiate
interface Vlan99
 description Management
 ip address 10.10.99.21 255.255.255.0
ip default-gateway 10.10.99.1
```
