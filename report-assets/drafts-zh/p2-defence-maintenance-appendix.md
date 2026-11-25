## 8 防御机制

每项防御都对应一个已测试或已分析的发现。凡是 Packet Tracer 无法实际验证的控制措施，证据来自自动化配置检查（全部 13 台 IOS 设备缺失行数均为 0）。

| 发现 | MSS 设计中实施的防御 | 验证（图号或证据编号） | 进一步加固 |
|---|---|---|---|
| V1 备份数据库暴露 | 备份服务器位于隔离的 VLAN 60；USERS-IN 拒绝 10.10.60.0/24；BACKUP-OUT 只放行数据、服务和管理网段 | E05（5432 端口对员工显示为 filtered，从备份网段访问为 open）；10.10.60.10 不可达（图 05）；deny 规则命中计数（图 11） | 从 VLAN 50 到 VLAN 60 采用加密复制 |
| V2 明文凭据 | 内网门户和部门服务器仅提供 HTTPS；HTTP 被 USERS-IN 拒绝并已禁用 | E06–E08（TLS 1.3，抓包中不含 token）；HTTPS 可正常加载（图 06a、06c），HTTP 超时（图 06b） | 以 POP3S/IMAPS 和 SFTP 取代 POP3 和 FTP；用 Nmap ssl-enum-ciphers 审查加密套件 [14] |
| V3 访问控制失效（broken access control） | 应用层角色校验；设备管理仅限 VLAN 99（VTY access-class、USERS-IN） | E06（员工返回 403，管理员返回 200）；从 ADMIN-PC 发起 SSH 成功（图 12a），从 MKT-PC01 发起超时（图 12b） | 每次发布前用 OWASP ZAP 按 OWASP A01 [12] 进行测试 |
| A1 VLAN 跳跃（VLAN hopping，DTP、本征 VLAN） | Trunk 设为 nonegotiate，本征 VLAN 999 不参与路由，配置允许 VLAN 列表 | 配置检查，缺失行数为 0 | 定期从用户端口用 Yersinia 测试 |
| A2 私设 DHCP（rogue DHCP）/ DHCP 耗尽（starvation） | DHCP 侦听（DHCP snooping），上联口设为可信，限速 20 pps；端口安全（port-security） | VLAN 10 已启用侦听，20 pps（图 08） | 在 NMS 上对侦听丢包发出告警 |
| A3 ARP 欺骗（ARP spoofing）/ 中间人攻击（MITM） | 用户 VLAN 启用 DAI；TLS 保护被截获的流量 | 配置检查；E06–E08 | 在季度渗透测试中用 Bettercap 测试 |
| A4 MAC 泛洪（MAC flooding） | 端口安全：每个工作站端口 2 个 sticky MAC，每个服务器端口 1 个，违规模式 restrict | Fa0/1–20 最大值 2，违规 0 次（图 08） | 工位调整后复查 sticky MAC 表 |
| A5 STP 根桥抢占（STP root takeover） | 根桥固定在核心交换机上；边缘端口启用 BPDU guard；下联口启用 root guard | CORE-1 为 VLAN 10 的根桥（图 03）；核心故障后收敛正常（图 10a、10b） | 用 Yersinia 测试 BPDU 注入 |
| A6 暴力破解（brute force，SSH、RADIUS、邮件、FTP） | SSH v2、VTY access-class、带本地回退的 RADIUS；路由器和核心交换机上配置 3 次失败后 login block-for 120（Packet Tracer 的 2960 镜像不接受该命令） | 图 12a、12b；RADIUS 客户端（图 14）；集中 syslog（图 13） | 在实验环境中用 Hydra 测试；为邮件和 FTP 配置账号锁定 |
| A7 明文 FTP/POP3 | POP3 只能在 MAIL 上访问；到 BACKUP-ARCHIVE 的 FTP 只允许来自 VLAN 40/50/99（USERS-IN、BACKUP-OUT） | 配置检查；用户无法访问 DB-REPLICA（图 05） | POP3S/IMAPS 和 SFTP |
| A8 存储的密码哈希强度弱 | Enable secret 和 service password-encryption | 在 Packet Tracer 中观察到 Type 5 MD5 secret | 生产环境 IOS 使用 Type 8/9（scrypt）secret；用 Hashcat 审计 |
| A9 OSPF / HSRP 伪造（spoofing） | OSPF MD5 认证；passive-interface default | 配置 MD5 后邻居状态为 FULL（图 02） | 生产环境启用 HSRP 认证 |
| A10 互联网暴露 | PAT 隐藏内部地址；OUTSIDE-IN 防地址欺骗 [17] 和仅放行回应流量的策略 [16] | EDGE-1 上的 PAT 转换（图 07） | 每次边界变更后从外部用 Nmap 扫描 203.0.113.2 和 198.51.100.2（未在 Packet Tracer 中测试） |

这些控制措施共同构成纵深防御（defence in depth）。物理层面，机房使用门禁卡控制，副本服务器放在单独的机柜中。在二层，端口安全、DHCP 侦听、DAI 和 STP 防护措施可以把来自工位端口的攻击限制住。在三层，核心 ACL 把各部门限制在所需的服务内，边界 ACL 和 PAT 则守住互联网边界。管理面只能从 VLAN 99 通过 SSH 并经 RADIUS 认证访问，应用层强制使用 HTTPS 并做角色校验。即使数据库凭据泄露，仅凭这一点，市场部工作站仍然无法访问 DB-REPLICA。

## 9 日常维护中的安全与漏洞分析指南

只有在设计随变更持续复测的情况下，它才能保持安全。下面的时间表适合预算有限、60 名用户的公司，复用小组已有的工具和免费扫描器，并与 CIS Controls v8 [13] 保持一致。

| 频率 | 活动 | 工具 | 负责角色 | 产出 |
|---|---|---|---|---|
| 每天 | 查看登录、HSRP/OSPF、端口安全和侦听事件 | NMS syslog | 网络管理员 | 审查记录或事件工单 |
| 每次变更后 | 重新运行配置漂移检查（configuration drift check）和 Docker 漏洞实验 | check_config.py；装有 Kali 工具的 Docker 实验环境 | 网络管理员 | 缺失行数为 0；V1–V3 实验结果为 PASS |
| 每次变更后 | 通过 SSH 把每台设备的配置复制到 ADMIN-PC，再上传到 BACKUP-ARCHIVE | 从 ADMIN-PC 使用 SSH；FTP（生产环境用 SFTP） | 网络管理员 | 带日期的配置归档 |
| 每月 | 对服务器和设备进行认证漏洞扫描 | Greenbone/OpenVAS | 安全负责人 | 带风险评级的扫描报告 |
| 每月 | 为服务器和工作站打补丁；查看 IOS 安全公告 | 厂商更新渠道 | 服务器管理员 | 补丁日志 |
| 每季度 | 对 DB-REPLICA 和 BACKUP-ARCHIVE 数据做恢复测试 | 把数据库恢复到隔离的测试主机 | 服务器管理员 | 恢复耗时和完整性结果 |
| 每季度 | 审查 RADIUS、本地回退账号和应用管理员账号 | NMS RADIUS 用户列表 | IT 经理 | 签字确认的账号清单 |
| 每季度 | 针对已分析漏洞进行内部渗透测试 | Nmap、Yersinia、Bettercap、OWASP ZAP；Hydra 仅针对实验环境副本 | 安全负责人 | 测试报告 |
| 每年 | 对 203.0.113.2 和 198.51.100.2 进行外部测试 | 从外部使用 Nmap | 安全负责人 / IT 经理 | 更新后的安全策略 |

每次测试都遵循 NIST SP 800-115 的规划、发现、攻击和报告四个阶段 [11]：

1. **授权与交战规则（rules of engagement）。** 由 IT 经理出具书面许可，明确测试范围内的地址、时间窗口、工具和紧急叫停联系人。ISP 设备不在范围内；漏洞利用在使用合成数据的 Docker 实验环境中进行。
2. **基线。** 以最新的配置归档和扫描结果为参照；漂移检查必须显示缺失行数为 0，这样发现的问题反映的是设计本身，而不是未记录的变更。
3. **扫描。** 分别从用户 VLAN、VLAN 99 和边界外部发起扫描，因为每个区域应当看到不同的攻击面。
4. **验证。** 对发现的问题进行人工确认，就像 V1–V3 用 Nmap、tcpdump 和 curl 确认的那样。
5. **修复。** 修复要经过变更控制，并先写入设计源文件，使重建和漂移检查始终具有权威性。
6. **复测。** 重新运行同一条命令，并加上正向对照（positive control，如 E05），证明合法服务仍然正常工作。
7. **报告。** 报告记录发现、风险、证据、修复、复测结果和负责人，并作为年度策略审查的输入。
