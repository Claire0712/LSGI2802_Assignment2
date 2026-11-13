# Implementation decisions

The approved proposal is refined where raw data require explicit rules. These are modelling decisions, not observed resident behaviour.

1. Origins are census-guided outdoor-network proxies, not population-weighted centroids or validated residential entrances. Within each TPU, candidate census polygons with positive population are ranked by whole-group density; choose the outdoor network vertex inside the polygon–TPU intersection nearest its point-on-surface. Cross-TPU census populations are never allocated to individual TPUs. Additional candidates provide origin sensitivity. This improves reproducibility but cannot represent every resident. Report proxy coverage, shifts and missing TPUs.
2. North Kwai Chung temporarily shares the Ha Kwai Chung site; count 76 distinct destination sites rather than 77 directory entries. Preserve both source records in raw data. Tung Wah Eastern's within-campus relocation remains a location uncertainty and is excluded in sensitivity analysis.
3. Lift edges use a provisional 60 m/min traversal speed without waiting. This avoids falsely applying a fixed wait repeatedly to segmented lifts; include sensitivity by excluding lift edges if necessary. All ordinary segments use 3D geometric length / 80 m/min. Stair physiology, waits and indoor access schedules remain limitations.
4. Only enabled and non-paid network edges enter the graph. Nodes share XYZ at millimetre precision. Direction is retained. No XY-only junction creation or ferry links. AccessTimeID is recorded; until associated schedules are verified, indoor edges use static access assumptions, tested against an outdoor-only variant if feasible.
5. Clinic access connectors use the nearest outdoor-network vertex and explicit connector length. These are entrance approximations; lengths >50 m require scrutiny. They are not field-verified legal paths. Sensitivity analyses and route plots must expose this uncertainty.

## Verified refinements after obtaining full FGDB

The complete official FGDB (revision 16 September 2026; acquired 24 October) contains 465,892 features and both schedule tables. It supersedes the incomplete REST download. No incomplete-network results are used.

The implemented reference is ordinary Monday 15:00, excluding public holidays. All 76 distinct sites' consultation-hour text was inspected: Ta Kwu Ling (source ID 47) and Kam Tin (65) do not offer consultation then; the baseline therefore has 74 sites. Stanley and Sha Tau Kok do offer consultation at this time. This is a static availability snapshot, not a simulation of arrival-time-dependent appointments.

Network OPEN/CLOSE tables are evaluated against MON/WD/ED intervals at 15:00, including overnight intervals. Restricted segments with an unresolved schedule are excluded and counted; null AccessTimeID means no supplied restriction. This replaces the earlier tentative static-all-indoor assumption. Real-time closures and special public-holiday rules remain outside scope.

## Topology sensitivity

Exact millimetre XYZ identity produced 555 weak components. An audit found a 0.046 m gap affecting a model-disconnected proxy. The final graph adds 73 bidirectional links of at most 0.1 m Euclidean XYZ length, exclusively between previously separate components. Their actual lengths enter costs and their cover is unknown. There are 497 weak components afterwards. The exact-XYZ results and OD matrices are retained under results/exact_xyz; this explicitly bounded tolerance does not planarize crossings or bridge metre-scale gaps. Remaining model disconnections are not proof of real-world isolation.
