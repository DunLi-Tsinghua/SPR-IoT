# Fourth-round Broker protocol (E5/E6, frozen before Broker outcomes)

Date: 2026-10-28. This protocol is a finite evaluation on the existing Mosquitto 2.1.2 Windows single-machine loopback testbed. It adds no packages and preserves all first/second/third-round evidence. E5 and E6 are separate from repair computation; no deployment time is relabeled as solver time.

## Preselected tasks and methods

Selection is by declared structure/scale/status before reading Broker outcomes, not by successful repairs. Four representatives are frozen:

1. `E1_K1_two_namespaces`: the two-namespace baseline, edit cap 2.
2. The **v2 semantic-pressure** task with structure s1, scale n2, seed17 (priority/deny interaction), edit cap 3.
3. The **v2 semantic-pressure** task with structure s2, scale n3, seed17 (redundant allow interaction), edit cap 3.
4. `E1_K4_conflict`: predeclared language requirement conflict, edit cap 2; retain its original deployment and any no-policy method outputs as NA.

The earlier pressure-v1 task inventory is not formal source diversity. No fourth-round Broker run has been performed on it. Binding the two structure/scale/seed selectors to v2 file IDs will be recorded in the manifest before deployment; it is not an outcome-dependent change of selection.

E5 uses B0 plus the applicable prescheduled methods: B4/SPR/Finite for the two E1 baselines, and B4/SPR/Greedy for the two pressure representatives. No extra pressure-Finite algorithm run is inferred. An unplanned method is not_scheduled NA, distinct from solver timeout, no solution, conflict, invalid export or deployment failure. E6 uses B0 versus SPR on the same four representatives, including NA for absent repaired policies. No nonexistent or invalid policy is deployed.

## Identical finite request plan

Each task retains its entire explicit finite required/forbidden catalog and fixed subscription-filter catalog. For tasks without challenge records, directory-external challenges are generated deterministically from each catalog topic by appending `/child` and `/newbranch/leaf`. Labels are determined from the task's already declared required/forbidden patterns, including an explicit conflict label if both apply. Existing challenge records are reused when available. Select the first two lexicographically distinct noncatalog, nonboundary topics per label (required, forbidden, conflict, unspecified), before any Broker outcome. This is a bounded diagnostic subset, not an all-topic benchmark.

A separate boundary domain always contains the valid unique topics `[root, root+'//public', '$spr/NEW', '/']`, removing exact duplicates with the task catalog. Labels follow declared requirement patterns. The same frozen catalog/challenge/boundary list is used for every method and contains no method-specific handcrafted examples. Unspecified requests remain unspecified. Each E5 task/filter/topic is tested once on fresh reader/publisher connections and fresh subscriptions. Observation window 0.6 seconds; MQTT3.1.1, QoS1, clean sessions, retain false. Record CONNACK, SUBACK, PUBACK, message IDs, actual payloads, DUP/QoS, and Broker verbose events. No receipt within the window is an observation, not a universal denial proof.

Publisher send rules authorize all test topic names: `#` for ordinary topics plus explicit `$` prefix rules as needed. A separate local observer identity has only a fixed `spr4_control/positive` subscription/receive grant. Each actual deployment includes an observer-channel positive probe before and after its test phase; these are logged separately, not added to policy-task or main-probe denominators. Main task identities/roles are not widened to create positive controls. No observer-control count is claimed unless its actual artifacts exist.

The concrete expectation checker uses the separate regex interpreter, not the optimizer matcher. Export only the declared single-role fixed-identity subset, unique priorities within an ACL event and one subscription ACL kind. Unsupported semantics is NA, not approximated. Exact effective JSON, fixed identities/roles/defaults, Broker configuration, source/result/manifest hashes, timestamps and logs are retained per deployment.

## E6 repeated paired complete runs

Five **complete paired runs** per preselected representative use B0 and SPR, with method order randomized independently by `random.Random(41028)` and saved before the first deployment. A pair is the task/repeat unit. Message observations are not independent tasks or experimental repetitions. Missing policy, method timeout, invalid export, deployment failure or incomplete pairs remain explicit NA; no zero latency is substituted.

Each deployment starts a new Broker process on a reserved loopback port, loads its full generated policy, performs authenticated readiness and observer control, creates fresh main clients, requests the same fixed subscription catalog, runs the fixed message plan, performs the trailing observer control, and stops only its own child process. No existing service is installed, stopped or restarted.

Separate raw measurements:

- reader policy ACL count, full exported ACL count, dynamic-security JSON bytes and broker configuration bytes;
- export/configuration generation and write time (excluding solving and one-time official identity bootstrap);
- process-start to first successful authenticated observer CONNACK (startup-to-authenticated-ready, not isolated parser time);
- main reader/publisher authentication durations and per-filter SUBACK duration/results;
- fixed small-message sender/receiver observation latency.

The message plan is exactly 10 messages of 64 ASCII payload bytes to the first explicit required catalog topic, using one in-flight QoS1 message, 10ms pause after completion, fresh unique IDs and fixed payload padding. The same topic/payload size and subscription plan is used before/after. A receiver thread timestamps complete receipt independently of publisher PUBACK; latency is local Python-client send-to-receive observation time in milliseconds, including OS/thread/loopback costs. TCP_NODELAY is fixed for both clients. Raw PUBACK duration and delivery/DUP state are retained. Absence of an authorized legitimate path is a status, not a fast successful delivery. The conflict representative's contradictory topic is labeled conflict and is not counted as a legitimate complete repair.

Per-run latency summaries reduce the 10 messages to a run-level median/mean; raw message values remain available. Save all five paired post-minus-pre values for generation, startup, authentication and run-level message metrics. No confidence interval is manufactured from ten messages. Do not claim a faster configuration is preferable when its security/legality state differs. No throughput, multidevice deployment or saturation claim is supported by this small sequential plan.

## Finite resource budget and stopping rules

Budget, not an unmeasured forecast: E5 permits at most 4 tasks x 4 applicable methods, at most 512 main filter/topic probes; E6 permits at most 4 tasks x 2 methods x 5 repeats = 40 deployment slots and 400 planned workload messages. Observer controls are separately bounded at 2 per deployment slot. The fixed request plan and its actual slot/probe counts are saved before execution. If the frozen plan exceeds a cap, report protocol_budget_not_supported before measuring; do not prune requests using results.

Total logical wall-clock budget is **1800 seconds**, partitioned as at most 700 seconds for E5 and the remaining budget for E6. Broker startup budget is 8 seconds; socket I/O timeouts 2 seconds; workload message receive deadline 1 second; owned-process shutdown deadline 5 seconds. Check phase/global deadlines before every deployment/probe/message. On exhaustion, preserve partial records and mark all remaining slots budget_exhausted NA. A currently active bounded operation and shutdown may add up to 30 seconds beyond the logical deadline. Host/service hangs are external execution failures rather than algorithm or Broker costs. This is a maximum allowed budget, not an assertion that the experiment will take that long.

## Outputs and integrity

Expected new root: `results/round4/broker`. Freeze `manifest.json`, `order.json` and protocol/hash metadata first. Record `deployments.csv`, `probes.csv`, `delivery_summary.csv`, `message_latency.csv`, `overhead_runs.csv`, `paired_differences.csv`, actual per-case JSON/config/log/control records and structured failures. Every nondeployed method has an explicit row with NA measurements and reason. Report task-level numerators/denominators separately by catalog/challenge/boundary and label; do not average only successful policies. Runtime comparisons use compatible completed pairs while reporting the total and missing pair counts.

Independent read-only audit must reconcile publisher PUBACK/incoming-PUBLISH counts, Broker forwarded messages, client payload IDs and separate concrete expectations. Confirm result/figure table values from raw records. Keep unfavorable finite repairs, timeout/unsat/conflict outputs and deploy failures. Do not modify older measured archives or unrelated projects.
