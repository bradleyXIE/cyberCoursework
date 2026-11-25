[[PAGEBREAK]]

# 第二部分：漏洞分析

## 6 网络设置中的安全漏洞

小组以用户 VLAN 上一名普通员工的视角评估 MSS 设计，因为场景要求每位员工都能访问共享服务和全部三个部门数据库，这使内部网络成为最可能的滥用来源。其中三个弱点在隔离实验环境中被复现并修复（V1–V3）；另外十个弱点（A1–A10）则对照 Packet Tracer 配置进行了分析，其可能性和影响均按缺少相应控制措施时的情况评级。

| ID | 弱点 | 在 MSS 设计中的位置 | 可能性 | 影响 | 对 MSS 的重要性 |
|---|---|---|---|---|---|
| V1（已测试） | 备份数据库可从用户网络访问 | DB-REPLICA 10.10.60.10，VLAN 60；两台核心上的 USERS-IN 和 BACKUP-OUT | 高 | 高 | 副本保存了全部三个部门数据库的拷贝，因此一台被攻陷的工作站既能读取或破坏在线数据，也能读取或破坏用于恢复的副本。 |
| V2（已测试） | 凭据以明文 HTTP 传输、可被读取 | INTRANET 10.10.40.10，VLAN 40 | 高 | 高 | 全体员工都使用内网门户；以明文发送的令牌（token）可被任何截获它的人重放。 |
| V3（已测试） | 普通员工能调用管理员导出接口 | 内网门户及各部门 HTTPS 前端（VLAN 40 和 50） | 中 | 高 | 网络 ACL 必须放行到每台部门服务器的 HTTPS，因此应用层的角色检查是阻止批量导出的唯一屏障 [12]。 |
| A1 | 中继协商 / 本征 VLAN（native VLAN）滥用 | 接入层到核心以及数据中心交换机的中继（trunk）链路 | 低 | 高 | 带标签的帧可能直接到达 VLAN 60 或 99，绕过核心上的 ACL。 |
| A2 | 私设 DHCP 服务器或 DHCP 地址耗尽 | 用户 VLAN 10/20/30；INTRANET 和 MAIL 上经中继提供的 DHCP | 中 | 中 | 私设服务器可能下发虚假的网关或 DNS 服务器；地址耗尽则会使每层楼多达 25 名用户无法获得地址 [9]。 |
| A3 | 基于 ARP 的流量截获 | 用户 VLAN 及 HSRP 网关 .1 | 中 | 高 | 伪造网关会让攻击者插入员工与内网门户、邮件及数据库服务器之间。 |
| A4 | MAC 地址表溢出 | ACC-F1-MKT、ACC-F2-SALES1/2、ACC-F3-GS | 低 | 中 | 被泛洪的帧会把同一楼层交换机上其他用户的流量暴露出来。 |
| A5 | 生成树（spanning-tree）根桥抢占 | 接入端口及核心下行链路 | 低 | 高 | 非法根桥会把流量从 CORE-1/CORE-2 引走，并破坏与 HSRP 对齐的负载分担 [5]。 |
| A6 | 针对 SSH、邮件和 FTP 的密码猜测 | 设备 VTY 线路（来自 VLAN 99）、MAIL（来自用户 VLAN）、BACKUP-ARCHIVE（来自 VLAN 40/50/99） | 中 | 高 | 一旦猜中 `netadmin` 凭据，就能获得网络设备的管理控制权。 |
| A7 | 用户与 MAIL 之间的明文 POP3，以及从数据区、服务区和管理区到 BACKUP-ARCHIVE 的明文 FTP | MAIL（POP3）、BACKUP-ARCHIVE（FTP） | 高 | 中 | 邮件和备份凭据以可读形式穿过核心；这仍是一项剩余风险。 |
| A8 | 设备配置中较弱的旧式密码哈希 | IOS 设备上的 Type 5（MD5）`enable secret` 和 `username` 密文 | 低 | 高 | 泄露的配置备份可能被离线破解。 |
| A9 | 未经认证的路由 / 网关协议报文 | OSPF 区域 0 链路、核心上的 HSRP 组 | 低 | 高 | OSPF 使用了 MD5 认证 [3]，但 HSRP 未配置认证，因此伪造的 hello 报文可能夺取活动网关角色 [4]。 |
| A10 | 边缘路由器面向互联网暴露 | EDGE-1 203.0.113.2、EDGE-2 198.51.100.2 | 中 | 高 | 边缘路由器是唯一从互联网可见的设备，并承载着 MSS 的全部流量。 |

## 7 用于分析的 Kali Linux 和 Windows 工具

### 7.1 按工具类别划分的评估计划

| 类别 | 工具（Kali / Windows） | 在 MSS 评估中的用途 | 验证的控制措施 | 是否实际运行？ |
|---|---|---|---|---|
| 信息收集 | Nmap / Zenmap | 按 VLAN 发现存活主机和监听服务；确认从用户 VLAN 只有被允许的服务会响应（V1、A10） | USERS-IN、BACKUP-OUT、MGMT-OUT、OUTSIDE-IN [14] | Nmap：是（实验环境）；Zenmap：否 |
| 嗅探与欺骗 | tcpdump / Wireshark | 检查用户 VLAN 与服务器之间的流量中是否有可读凭据（V2、A7） | 仅 HTTPS 的内网门户；剩余的 FTP/POP3 风险 | tcpdump：是（实验环境）；Wireshark：否 |
| 漏洞分析 | Greenbone/OpenVAS（Nessus Essentials 只覆盖 16 个 IP 地址，少于 MSS 的 18 台服务器和 IOS 设备）、Nmap NSE `ssl-enum-ciphers` | 对服务器和 IOS 设备做认证扫描（authenticated scan）；审查 INTRANET 以及 DB-MKT/DB-SALES/DB-GS 的 TLS 版本和加密套件 | 补丁、禁用不用的服务、TLS 配置 | 否（已计划） |
| Web 应用分析 | OWASP ZAP、Burp Suite Community、Nikto | 审查内网门户及各部门前端的访问控制和传输缺陷（V2、V3）[12] | 角色检查、仅 HTTPS 访问 | 否（已用 curl 完成等效检查） |
| 密码审计 | Hydra、John the Ripper / Hashcat | 仅在书面授权下、针对实验副本进行：测试锁定策略以及导出的 type 5 哈希强度（A6、A8） | `login block-for`、VTY access-class、RADIUS AAA、密文强度 | 否 |
| 二层测试 | Yersinia、Bettercap | 在实验复制环境中确认中继、DHCP、ARP 和 STP 防护有效（A1–A5） | 关闭 DTP、本征 VLAN 999、DHCP 监听（DHCP snooping）、动态 ARP 检测 DAI、端口安全（port-security）、BPDU 防护（BPDU guard）、根防护（root guard）[2] | 否 |
| Windows | Wireshark、Nmap/Zenmap、PuTTY | 从 ADMIN-PC（10.10.99.50）进行管理员侧验证：抓包、扫描和 SSH v2 检查 | VTY 仅限 VLAN 99、仅允许 SSH v2 | 否 |
| 漏洞利用 | Metasploit Framework | 仅限 Docker 实验环境：确认 V1 在基线状态下可被利用，加固后不再可达 | VLAN 60 隔离、BACKUP-OUT | 否 |
| 无线 | Aircrack-ng 套件 | 不适用于当前的有线设计；目前用于排查私设接入点，待 5.1 中的 WLAN 建成后用于 WPA2/WPA3-Enterprise 检查 | 802.1X/RADIUS（未来） | 否 |

### 7.2 MSS 场景中的实施示例

Packet Tracer 无法运行这些工具，因此以下示例适用于生产网络，或根据同一设计源生成的试点重建环境。每次扫描都限定在 MSS 地址范围内，只用于发现和验证。

对市场部 VLAN 做一次主机发现扫描，可得到一份清单，用来与登记在册的 20 台工作站比对。从市场部工作站对备份 VLAN 执行同样的扫描，应发现不到任何存活主机，因为 USERS-IN 在任何 ICMP 放行规则之前就拒绝了 10.10.60.0/24；而从 ADMIN-PC 执行时，它作为阳性对照（positive control），因为 BACKUP-OUT 允许管理 VLAN 访问。

```
nmap -sn 10.10.10.0/24
nmap -sn 10.10.60.0/24
```

从用户 VLAN 对共享服务器做服务扫描，结果应只列出 USERS-IN 允许的服务：INTRANET 上的 HTTPS，以及 MAIL 上的 SMTP 和 POP3。

```
nmap -sV -Pn 10.10.40.10-11
```

一个 NSE 脚本会报告内网门户和三个部门前端所提供的 TLS 版本和加密套件。

```
nmap --script ssl-enum-ciphers -p 443 10.10.40.10 10.10.50.11-13
```

为确认没有凭据以明文穿过核心，将在预定的时间窗口内于 DC-SW-A 的监控端口上抓包，并在 ADMIN-PC 上用 Wireshark 或用 tcpdump 进行审查。HTTPS 会话中不应出现可读的 `Authorization` 头部，而 POP3 和 FTP 登录预计在计划迁移到安全协议之前仍然可见（A7）。

```
tcpdump -nn -A -r <capture>.pcap
```

从经授权的外部位置扫描两个 WAN 地址，应显示没有开放端口，因为 OUTSIDE-IN 只放行由内部发起的会话的回应流量（A10）[16]。`established` 关键字是无状态的，因此 ACK 探测会被报告为 unfiltered（未过滤）——这也是 5.1 中提议部署下一代防火墙的原因之一。此项外部测试未在 Packet Tracer 中运行。

```
nmap -sS -Pn -p- 203.0.113.2 198.51.100.2
```

使用 Nikto 和 OWASP ZAP 基线扫描检查 Web 前端的传输和头部弱点，结果应不报告任何访问控制或加密方面的问题（A01/A02）[12]：

```
nikto -h intranet.mss.lan -p 443 -ssl
zap-baseline.py -t https://db-sales.mss.lan
```

在 ADMIN-PC 的 Wireshark 中，用一个显示过滤器筛出所有明文凭据；迁移到 HTTPS 之后，应只有 POP3 和 FTP 登录会被匹配（A7）：

```
http.authorization || pop.request.command == "PASS" || ftp.request.command == "PASS"
```

在 VLAN 99 上为 10.10.40.10-11、10.10.50.11-13 和 10.10.60.10-11 定义一个 Greenbone 认证扫描任务，使备份服务器从唯一被允许访问它们的区域接受扫描。管理员使用 PuTTY 的命令行客户端确认设备只接受来自 ADMIN-PC 的 SSH 第 2 版连接：

```
plink -ssh -2 -l netadmin 10.10.99.21
```

密码审计（用 Hydra 针对 VTY 线路的实验副本；用 John the Ripper 或 Hashcat 针对导出的 type 5 哈希）和二层测试（用 Yersinia 测试 DTP、DHCP 和 STP；用 Bettercap 测试 ARP）只在根据同一设计源生成的实验重建环境中、并在书面授权下进行。预期结果为：路由器和核心在三次失败后封锁登录 120 秒；中继不进行协商；DHCP 监听的速率限制和 BPDU 防护将测试端口置为 err-disabled；DAI 丢弃伪造的 ARP 应答。本报告未实际运行这些工具。

### 7.3 实验实施与结果

V1–V3 于 2026 年 11 月 25 日在一个一次性的 Docker 实验环境中进行了测试。创建了两个仅限内部的网桥（`internal=true`），没有任何容器发布端口（`published={}`），所有数据均为合成数据（例如 `MSS-LAB-SYNTHETIC-RECORD`）。各容器与 MSS 区域的对应关系如下：

- Kali 客户端 172.29.216.10：用户 VLAN 上的一台员工电脑；
- Python 内网应用 172.29.216.30：INTRANET；
- 位于受保护网桥上的 PostgreSQL 备份数据库 172.29.217.20：VLAN 60 中的 DB-REPLICA；
- 仅限基线阶段：同一数据库以 172.29.216.20 的地址再接入员工网桥，用以模拟缺失的网段隔离。

E00 记录了 Nmap 7.991、curl 8.22.0（OpenSSL 3.6.5）、tcpdump 4.99.6、Python 3.12.3、PostgreSQL 16.15 和 Docker 29.9.2。OpenSSL 生成了自签名的实验证书（CN=intranet.lab，RSA 2048），curl 通过 `--cacert` 信任该证书。所用命令如下：

```
nmap -sT -sV --version-light -Pn -n --reason -p 5432 172.29.216.20
nmap -sT -sV --version-light -Pn -n --reason -p 8080,8443 172.29.216.30
curl -sS --max-time 5 --cacert /tmp/lab-ca.pem --resolve "intranet.lab:8443:172.29.216.30" \
  -H "Authorization: Bearer LAB-EMPLOYEE-ONLY" https://intranet.lab:8443/admin/export
tcpdump -nn -A -r /tmp/capture.pcap
```

基线阶段使用 `http://intranet.lab:8080`；tcpdump 使用过滤器 `host 172.29.216.30 and tcp` 抓包。加固阶段反映 Packet Tracer 中的设计：数据库从员工网桥上断开（VLAN 60 隔离），内网应用只提供 HTTPS，导出路由强制要求管理员角色。每个阶段都分别以匿名方式、员工令牌和管理员令牌请求导出。运行最终输出 `PASS · ports, backup isolation, access controls and transport checks`。

| 弱点 | 基线结果 | 加固后结果 | 证据 |
|---|---|---|---|
| V1 备份数据库可达 | 172.29.216.20 5432/tcp open postgresql（syn-ack） | 172.29.216.20 5432/tcp filtered（no-response）；172.29.217.20 5432/tcp filtered（net-unreach） | E01、E04、E05 |
| V2 明文凭据 | 8080/tcp open http，8443 closed；抓包中可见 `Authorization: Bearer LAB-EMPLOYEE-ONLY` | 8080 closed，8443 open ssl/http；TLSv1.3 / TLS_AES_256_GCM_SHA384，主体 CN=intranet.lab 验证通过；错误主机名被拒绝（curl 退出码 60）；抓包中无 bearer 令牌 | E01、E03、E05、E07、E08 |
| V3 员工调用管理员导出接口 | 匿名 401；员工 200；管理员 200 | 匿名 401；员工 403 "administrator role required"；管理员 200 | E02、E06 |
| 来自备份网络的阳性对照 | – | 从受保护网桥执行 `nmap -sT -Pn -n --reason -p 5432 172.29.217.20`：5432/tcp open（syn-ack） | E05 |

阳性对照表明，加固消除了暴露面，同时没有破坏授权区域对该服务的使用。所有测试均经过授权，与生产环境和互联网主机隔离，并限定在约定范围内，遵循 NIST SP 800-115 的规划、发现、攻击和报告阶段 [11]。
