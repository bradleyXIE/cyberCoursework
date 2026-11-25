# CST4562 coursework

MSS Ltd network implementation and vulnerability assessment (group of four: Zhijie Xie, Gul Khalid Khan I, Boon Suni, Adam Peter).

- [Group report](report-assets/CST4562-Group-Report.docx) is built on the group's [Word template](Coursework%20Template.docx). It contains Part 1 (implementation), Part 2 (vulnerability analysis), references, the Packet Tracer test screenshots (Appendix A) and the group activity list.
- [Implementation topology](CW_CST4562-Implementation.pkt) has a collapsed core with two Catalyst 3650 switches running HSRP, LACP and OSPF, dual-homed floor switches, two edge routers on two ISPs, segmented server VLANs and an isolated backup VLAN. Open it in Packet Tracer 9.0.1 and press Fast Forward for about 2–3 minutes of simulated time so the network converges before you test it.
- [Packet Tracer tooling](implementation-lab/packet-tracer/) holds the single design source (`design.py`). `build_topology.py` rebuilds the .pkt from `base-gui.pkt` and `check_config.py` checks the configuration that Packet Tracer accepted. Lab credentials live in `design.py` and are for the simulation only.
- [Simulator evidence](implementation-lab/evidence/PT-implementation-verification.txt) records the Packet Tracer observations. Screenshots are in [report-assets](report-assets/).
- [Vulnerability lab](vulnerability-lab/README.md) contains the Docker runner and evidence used in Part II. The latest run is in `evidence/rerun-20261125`.
- [Coursework brief](CST4562_CW.pdf) lists the assessment requirements.

Rebuild the topology from the design source:

```sh
cd implementation-lab/packet-tracer
python3 build_topology.py base-gui.pkt ../../CW_CST4562-Implementation.pkt
```

Open the new file in Packet Tracer, let it converge, save it, then run `python3 check_config.py ../../CW_CST4562-Implementation.pkt`.
