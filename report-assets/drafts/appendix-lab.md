[[PAGEBREAK]]

## Appendix C: Lab tool output for chapter 7

Figures 7.1, 7.3, 7.4 and 7.6 are rendered from the text that the lab scripts wrote to `vulnerability-lab/evidence` (`rerun-20261125` and `ch7-tools`), with only the relevant lines cut; no output was retyped. Figures 7.2 and 7.5 are window captures of the group's Wireshark, reading the 25 November captures `E03-baseline.pcap` and `E07-hardened.pcap`. Figures are numbered to match section 7.

[[FIG:fig7-1-baseline-backup-db-exposed.png|Figure 7.1 – Baseline: the PostgreSQL backup database answers Nmap from the employee bridge (E01)]]
[[FIG:fig7-2-baseline-token-in-clear.png|Figure 7.2 – Baseline: Wireshark (desktop, display filter http.request, packet 16 expanded) shows the employee bearer token in cleartext HTTP requests (E03)]]
[[FIG:fig7-3-hardened-discovery.png|Figure 7.3 – Hardened: discovery from the employee bridge lists only the intranet; the protected segment has no route (C01, C02)]]
[[FIG:fig7-4-ssl-enum-ciphers.png|Figure 7.4 – Hardened: Nmap ssl-enum-ciphers lists the TLS 1.2 and 1.3 suites offered by the intranet (C03)]]
[[FIG:fig7-5-hardened-capture-review.png|Figure 7.5 – Hardened: Wireshark (desktop, display filter tls.handshake.type == 1) shows four TLS ClientHello messages with SNI intranet.lab; the same capture has no HTTP request (E07, C04)]]
[[FIG:fig7-6-hardened-access-control.png|Figure 7.6 – Hardened: anonymous 401; employee directory 200; employee export 403; administrator export 200 (E06)]]
