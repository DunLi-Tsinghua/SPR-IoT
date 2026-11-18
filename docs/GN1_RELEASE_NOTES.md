# G_N1 comparison and publication snapshot

The current manuscript is eight pages. A restricted, non-optimal neutral-bridge baseline is added; original G remains unchanged. The new successful 144-run batch is results/gn1_comparison_20261118_v2. Code, 36 existing inputs, order seed 20261118, cap 3 and per-process 5s budget were frozen before execution. Hardware is i9-13980HX, 33,959,825,408 bytes RAM, 32 logical processors; memory load at freeze was 94%, with no host-load isolation. The batch took 190.32s; single observations imply no significant speed advantage.

|Template|G|G_N1|E|Q|
|---|---|---|---|---|
|Branches|9/9|9/9|9/9|9/9|
|Priority overlap|9/9|9/9|9/9|9/9|
|Subscription|9/9|9/9|9/9|9/9|
|Redundant Allow|3/9|7/9|7/9|7/9|
|Total|30/36|34/36|34/36|34/36|

The four recovered cases are s2/n1/seed17, s2/n1/seed31, s2/n2/seed17 and s2/n2/seed31; bridges perform neutral deletion then Deny or narrowing. Full intermediate policies and task/run identifiers are in bridges.csv and raw JSON. All 34 common completed G_N1/E/Q returns have equal measured lexicographic costs. This is an observation, not a G_N1 optimality proof. Two G_N1 stalls remain; new E/Q have two timeouts each, not infeasibility certificates.

The first new attempt is retained separately with 28 E/Q recorder errors due to a duplicate elapsed field. A regression test fixes the recorder; the whole queue was rerun, not only failed entries. The first attempt is excluded from method comparison. Full local tests: 58 pass. Independent concrete postchecks: 1,806 topics, finite scope. Neither run adds independent real-error sources.

Historical data/curves remain separate and unchanged. Their E/Q 34/36 had one infeasible/one timeout. 127 Broker probes, 80 controls, 300 latency messages, 15 offline and 10 Broker complete pairs are retained. Secondary configuration sizes, generation/readiness, memory and marginal-time observations remain in their original CSV/raw records; the paper prioritizes the matched-baseline table. Abstract/conclusion now acknowledge recovery of the strict-G gap. Proposition 1, authors, references and graph PDFs are unchanged; no submission/fee acceptance occurs.

Local publication content is allowlisted by scripts/build_public_release.py. Upstream raw policies and production credentials are excluded; path redactions are recorded with original/published hashes. Public reuse is not falsely presented as a blanket MIT license. Current main remains paper/current/SPR_IoT.tex; the release directory is a generated delivery snapshot. No public link or accessible remote commit is asserted before actual publication verification.

Verified public repository: https://github.com/DunLi-Tsinghua/SPR-IoT (initial remote commit 281db56f274ba4916db68dbfbab72df9b98c3f8f). The manuscript now links to this repository. This publication update changes no experiment or figure.

Editorial update: the introduction now distinguishes repair from passing listed examples; Section III-E is condensed to one paragraph while retaining export preflight, independent enumeration/AWS interpretation and finite Broker validation. Eight pages, figures, references and experimental results are unchanged.
