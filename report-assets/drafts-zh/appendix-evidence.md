[[PAGEBREAK]]
# 附录
## 附录 A：Packet Tracer 测试证据

所有截图均于 2026 年 11 月 25 日在 Cisco Packet Tracer 9.0.1 中拍摄，所用文件是 CW_CST4562-Implementation.pkt 的一个验证副本，其控制台（console）线路登录后直接进入特权模式（privileged mode）；除此之外，网络配置与提交的文件完全相同。

[[FIG:fig02-core1-hsrp-lacp-ospf.jpg|图 02 – CORE-1：show standby brief、show etherchannel summary 和 show ip ospf neighbor]]

[[FIG:fig03-core1-route-stp.jpg|图 03 – CORE-1 路由表（默认路由经 EDGE-1）以及 VLAN 10 的快速生成树协议（RSTP）根桥]]

[[FIG:fig04-pc-dhcp-relay.jpg|图 04 – MKT-PC01 通过核心交换机上的 DHCP 中继（DHCP relay）从 MAIL（10.10.40.11）获得地址 10.10.10.171]]

[[FIG:fig05-pc-acl-tests.jpg|图 05 – 从 MKT-PC01 进行的策略测试：NMS 和 DB-REPLICA 被阻止，Internet 和 DB-SALES 被允许]]

[[FIG:fig06a-browser-intranet-https.jpg|图 06a – 在市场部电脑上可以打开 https://intranet.mss.lan]]

[[FIG:fig06b-browser-intranet-http-blocked.jpg|图 06b – 明文 http://intranet.mss.lan 被拒绝（Request Timeout）]]

[[FIG:fig06c-browser-db-sales-cross-dept.jpg|图 06c – 市场部电脑通过 HTTPS 打开销售部的应用/数据库前端]]

[[FIG:fig06d-browser-public-web-nat.jpg|图 06d – 市场部电脑通过端口地址转换（PAT）访问模拟的公网网站]]

[[FIG:fig07-edge1-nat-pat.jpg|图 07 – EDGE-1 上的 PAT 转换：10.10.10.171:1028 转换为 203.0.113.2:1028]]

[[FIG:fig08-access-portsec-snooping.jpg|图 08 – ACC-F1-MKT 的端口安全（port security）与 DHCP 监听（DHCP snooping）状态]]

[[FIG:fig09a-edge1-wan-shutdown.jpg|图 09a – 通过关闭 EDGE-1 的 Gi0/2 模拟 ISP-A 故障]]

[[FIG:fig09b-core1-floating-default.jpg|图 09b – CORE-1 的默认路由切换到经 EDGE-2 的浮动静态路由（floating static route，AD 250）]]

[[FIG:fig09c-pc-ping-via-isp-b.jpg|图 09c – ISP-A 故障期间，市场部电脑经 ISP-B 访问 Internet（TTL 124）]]

[[FIG:fig10a-core2-hsrp-takeover.jpg|图 10a – CORE-1 被隔离：CORE-2 成为全部七个热备份路由协议 HSRP 组的活动（active）路由器]]

[[FIG:fig10b-pc-during-core1-failure.jpg|图 10b – CORE-1 宕机期间，市场部电脑仍能访问 Internet 和内网]]

[[FIG:fig11-core1-acl-counters.jpg|图 11 – CORE-1 上 USERS-IN 的命中计数器]]

[[FIG:fig12a-admin-ssh-reachable.jpg|图 12a – 从 ADMIN-PC（VLAN 99）发起的 SSH 到达交换机登录提示符]]

[[FIG:fig12b-user-ssh-blocked.jpg|图 12b – 从 MKT-PC01 发起的 SSH 被阻止]]

[[FIG:fig13-nms-central-syslog.jpg|图 13 – NMS 接收来自两台核心交换机的系统日志（syslog）]]

[[FIG:fig14-nms-radius-aaa-masked.jpg|图 14 – NMS 上的 RADIUS 客户端和管理员账户（密钥已遮盖）]]
