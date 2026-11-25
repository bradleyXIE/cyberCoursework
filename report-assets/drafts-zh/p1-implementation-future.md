### 4.6 设计实施与测试

MSS 网络在 Cisco Packet Tracer 9.0.1 [15] 中搭建，所有内容都来自同一个设计源：design.py 和 build_topology.py 生成拓扑、布线以及每一台设备的 IOS 配置，再由 Packet Tracer 加载，并以原生格式保存为 CW_CST4562-Implementation.pkt；测试截图见附录 A，配置摘录见附录 B。check_config.py 将预期配置与 Packet Tracer 实际接受的配置进行比对，结果显示全部 13 台 IOS 设备缺失行数均为 0，且 MSS 自有的全部 10 台设备上都已生成 SSH RSA 密钥。这为 MSS 提供了可重复的重建方式，以及维护时可用的配置漂移（configuration drift）检查。打开文件后，需要约 2–3 分钟的模拟时间（Fast Forward，快进），OSPF、HSRP 和 STP 才能完成收敛（convergence）。

测试中暴露了 Packet Tracer 的三个行为特点，每一个都已在设计源中修正：3650 的端口配置只有在最后回放时才会生效，因此把它放在最后生成；在两台核心上拆分 DHCP 地址池（scope）时出现了重叠，因此改为 4.3 中的中继（relay）设计；缺少 IP SLA，且 OSPF 默认路由度量值（default metric）被忽略，因此采用了 4.4 中的浮动静态默认路由（floating static default）。

| 测试项 | 预期 | 结果 | 图号 |
|---|---|---|---|
| 核心控制平面（control plane） | HSRP 分担、Po1 正常、OSPF 达到 FULL | CORE-1 在 10/30/50/99 上为 Active；Po1(SU) 两个 LACP 成员均在线；与 10.10.0.2、.3 和 .4 的 OSPF 邻居均为 FULL | 图 02 |
| 路由与 STP | 默认路由经 EDGE-1；CORE-1 为根桥 | 最后求助网关（gateway of last resort）10.10.255.2 经 OSPF 学到；CORE-1 是 VLAN 10 的 RSTP 根桥 | 图 03 |
| DHCP 中继 | 从集中服务器经中继获得租约 | MKT-PC01 获得 10.10.10.171/24，网关 10.10.10.1，DHCP 服务器 10.10.40.11 | 图 04 |
| DNS | 内部和外部域名均可解析 | DNS 为 10.10.40.10；db-sales.mss.lan 和 www.public.test 均解析成功并有应答 | 图 04，图 05 |
| HTTPS 内网 | 内网通过 HTTPS 打开 | "MSS Ltd Intranet" 页面正常加载 | 图 06a |
| HTTP 被阻断 | 明文 HTTP 访问内网被拒绝 | Request Timeout（请求超时） | 图 06b |
| 跨部门数据库 | 市场部可访问销售部应用 | Ping 10.10.50.12 有回复；销售部页面通过 HTTPS 正常加载 | 图 05，图 06c |
| 备份隔离 | 用户无法访问 VLAN 60 | Ping DB-REPLICA 10.10.60.10 不可达 | 图 05 |
| 管理隔离 | 用户无法访问 VLAN 99 | Ping NMS 不可达，由 10.10.10.2 报告（ACL） | 图 05 |
| 仅管理员可 SSH | ADMIN-PC 成功，用户 PC 失败 | ADMIN-PC（10.10.99.50）到达 ACC-F1-MKT（10.10.99.21）的密码提示；MKT-PC01 显示 "Connection timed out" | 图 12a，图 12b |
| NAT/PAT | 内部主机通过同一个地址访问互联网 | 网页正常加载；地址转换 10.10.10.171:1028 映射为 203.0.113.2:1028 | 图 06d，图 07 |
| 端口安全与 DHCP 监听 | 限制生效，无违规 | Fa0/1–20 最多 2 个 MAC，模式 Restrict，违规 0 次；VLAN 10 启用监听（snooping），限速 20 pps | 图 08 |
| ISP-A 故障 | 流量切换到 ISP-B | 默认路由变为经 EDGE-2 的静态路由（AD 250）；ping 4/4 成功（TTL 124）；恢复后 OSPF 默认路由重新生效 | 图 09a–09c |
| 核心故障 | CORE-2 接管所有网关 | 约 8 秒后全部七个 HSRP 组在 CORE-2 上变为 Active；互联网 3/4、内网 4/4；抢占（preempt）使 CORE-1 恢复 | 图 10a，图 10b |
| ACL 计数器 | 策略条目被命中 | USERS-IN 命中数：拒绝备份 2，拒绝管理 2，HTTPS 内网 5，HTTPS 数据库 5，互联网 839 | 图 11 |
| Syslog 与 AAA | 集中日志与 RADIUS | NMS 收到两台核心发来的 HSRP/OSPF 消息；RADIUS 客户端已注册 | 图 13，图 14 |

故障切换测试中最初丢失的几个 ICMP 包，发生在新路径上进行 ARP 解析期间；这是 Packet Tracer 的行为，不是设计缺陷。

### 4.7 剩余风险与局限

以下局限仍然存在：

- **接入交换机。** 每层楼只有一台交换机；如果 ACC-F1-MKT 发生故障，市场部全部 20 名用户都会断网，直到更换设备为止。冷备件（cold spare）是当前的缓解措施。
- **服务器网卡。** 在 Packet Tracer 中每台服务器只有一块网卡（NIC），因此 DC-SW-A 故障会导致主服务器下线，不过 DC-SW-B 上的副本库和归档服务器仍然可用。
- **只有一间服务器机房。** 机柜 A 和机柜 B 分开了交换机和供电线路，但两者都位于一楼的同一个房间，因此一旦发生机房级事故，两份数据副本都会受到影响。
- **ISP 故障检测。** 故障切换依赖于 EDGE-1 的 WAN 接口断开；如果上游 ISP 出现故障但链路仍保持 up，在没有 IP SLA 的情况下将无法检测到。
- **明文服务与存储的密钥。** 到 BACKUP-ARCHIVE 的 POP3 和 FTP 仍未加密，且 Packet Tracer 存储的是 type 5 MD5 密码哈希；HSRP 认证未配置。
- **模拟范围。** ISP 路由器和公共 Web 服务器都是模拟的，并且只测试了 ISP-A 和 CORE-1 两种故障。

## 5 未来改进与结论

### 5.1 未来改进建议

以下建议用于弥补 4.7 中的局限，并为 MSS 的发展做好准备：

| 建议 | 对 MSS 的好处 |
|---|---|
| 采用支持 StackWise 堆叠的 Catalyst 9200/9300 作为接入交换机 | 每层楼使用堆叠、双归属（dual-homed）的成员交换机，消除接入交换机单点故障 |
| 10G 光纤上联 | 利用规划中的 OM4 竖井光缆路由，满足部门间数据传输量的增长 |
| IP SLA 跟踪 ISP | 不仅能检测链路断开，还能检测上游 ISP 故障，并将默认路由切换到 EDGE-2 |
| 边界部署下一代防火墙（NGFW） | 在仅允许回包的 OUTSIDE-IN ACL 之外，增加应用层检测和入侵防御 [16] |
| 802.1X/网络准入控制（NAC） | 在开放端口访问之前，通过现有 RADIUS 服务对设备进行认证，与端口安全形成互补 |
| 带控制器的无线网络 | 利用 3650 的 PoE+ 供电能力；各 WLAN 映射到现有的部门 VLAN 和 ACL |
| 安全信息与事件管理（SIEM） | 对已集中到 NMS 的 syslog 进行关联分析，更快发现安全事件 [13] |
| IPv6 双栈 | 按 VLAN 划分的地址规划可以直接映射为 IPv6 前缀 |
| 加密的邮件和文件协议 | 使用 IMAPS/POP3S 和 SFTP，消除剩余的明文凭据 [12]；在生产环境 IOS 上使用 type 8/9 密码哈希 |
| 异地/不可篡改备份 | 将 DB-REPLICA 和 BACKUP-ARCHIVE 的副本存放在服务器机房之外，防范机房级损失和勒索软件 |

### 5.2 总结与结论

本组为 MSS Ltd 设计并实施了一个安全、有弹性的网络。由两台 Catalyst 3650 交换机组成的折叠核心（collapsed core）适合 60 名用户、三层楼的站点：在提供设备冗余的同时，省去了汇聚层（distribution layer）的成本；双归属的接入交换机和约 40% 的空闲端口为扩展留出了空间。九个 VLAN 将部门、服务、数据、备份和管理分隔开来；核心 ACL 允许每位员工通过 HTTPS 访问每个部门的数据库，同时隔离备份和管理网络。纵深防御（defence in depth）从接入层的端口安全、DHCP 监听和 DAI，延伸到仅限 SSH、由 RADIUS 支撑的管理访问，以及具备防地址欺骗（anti-spoofing）、仅允许回包的网络边界。

Packet Tracer 中的测试证实了所需的各项行为：DHCP 中继、内部 DNS、仅限 HTTPS 的内网、跨部门数据库访问、备份与管理隔离、PAT，以及 ISP-A 和 CORE-1 两种故障下的切换。配置由单一设计源生成并经过自动检查，使网络可复现、可审计；未来改进建议则为 MSS 提供了分阶段消除剩余风险的路径。
