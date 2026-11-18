# Round 2 public-source admission review

This review uses existing local pinned sources only, without additional downloads. Run `python scripts/review_public_round2.py`; the executable task cards and complete declared candidate policies are in `data/tasks/round2_public.json`. Each card records a pinned source URL, file and extracted-policy SHA-256, original policy and Expected object, extraction key, group, supported/excluded decision and reason. Excluded cards remain in the same artifact.

## Fixed scope and requirements

Twenty distinct extracted policy documents were examined: eight P-Verifier family/user documents and twelve CloudFix IoT-related originals. P-Verifier's Statement2 is explicitly chosen for paired before/after wrappers; no claim is made that it is a real erroneous deployment. The entire wrapper is retained upstream and hashed. CloudFix originals remain complete; unsupported conditions/actions/variables are never dropped to make a policy admissible.

No original legitimate communication requirement was independently established for these twenty cards. P-Verifier's explicit `Expected.NotReceive` supplies source-authored forbidden topic strings for eight documents. At the pinned commit, `config_reader.py` line 27 maps `Expected.type:0` mechanically to `check0`; `main.py` dispatches only `check1` through `check5`, so it has no special supported `check0` meaning and would report an unknown check type if execution reaches that branch. A regression test directly invokes the original Reader to confirm the `check0` mapping without needing Z3. The integer zero in the README's **result** taxonomy is not evidence that the input type field denotes a valid check or a validated security oracle. Only literal `NotReceive` strings are adopted as experiment-specific forbidden requirements; this project does **not** claim to adopt or reproduce the complete original oracle. These source expectations are not claims about independent real-world application requirements. Every legitimate topic requirement is researcher-added category B.

Three workload settings were fixed before generating or evaluating repairs:

1. S1_status: a reader requires each non-forbidden device status topic.
2. S2_status_ack: the same reader additionally requires get/accepted and update/accepted acknowledgement topics.
3. S3_device_inbox: a fixed device requires its declared application inbox, while an adjacent private subtopic is forbidden.

Settings use device names seen in source policies solely to instantiate a declared researcher workload. **Allow rules are not evidence that communication is legitimate.** S1/S2 do not describe recovered business requirements. S3 is also a hypothesis, including the ESP8266 inbox choice in CloudFix 67; that task is a missing-permission diagnosis rather than an overauthorization repair case.

P-Verifier suffix resources (`topic/...`, `topicfilter/...`) retain their original namespace; CloudFix retains full ARNs. No AWS-to-Mosquitto rewrite occurs. P-Verifier assumes a fixed already authenticated principal with this single policy attached, because the dataset lacks a complete binding/connect configuration. CloudFix fixed-device cases enforce their explicit Connect permissions. The external publisher is assumed authorized to publish every catalog topic. Identity variables, Conditions, management/service actions and policy attachment recovery are unsupported. Provisioning-specific `$aws` workflows are excluded from this application-inbox review, rather than claimed to have been evaluated.

The offline semantics distinguish AWS string `*`/`?` authorization from MQTT `+`/`#` filter matching, require a usable subscription **and** Receive permission, apply explicit Deny precedence and implicit deny, and allow the fixed connection precondition only as stated per task. Authorization of one of a finite declared set of filters is sufficient for delivery. Claims are bounded to those filters/topics; neither universal safety nor universal legal-topic availability is proven.

## Admission and denominator

|Stage|Count|Meaning|
|---|---:|---|
|Reviewed distinct extracted policies|20|Policy-document deduplication; not independent deployments|
|Supported B workload cards|10|8 P-Verifier + CloudFix 252 and 67|
|Unsupported/excluded policy cards|10|Variables, conditions, unsupported actions or outside application scope|
|B task scenarios including controls/diagnostics|18|S1/S2 variants are dependent workloads, never independent samples|
|Originally unsafe scenarios|12|Within finite domain only|
|Originally missing explicit business scenarios|2|Includes one mixed safety/business failure|
|Main overauthorization repair denominator|11|Original unsafe **and** original legitimate workload available|
|Safe controls|5|Retained, not counted as repaired faults|
|Mixed overgrant/undergrant diagnostic excluded from repair denominator|1|PUB05_S2_status_ack is unsafe and missing legitimate communication; `out_of_scope_mixed`|
|Pure undergrant diagnostic excluded from repair denominator|1|PUB20_S3_device_inbox is safe but missing legitimate communication; `out_of_scope_undergrant`|

The 11 eligible scenarios come from **six original policy documents and one conservative P-Verifier template group**. Those family/user files share identifiers, resource topology and filename pattern; merging them is more defensible than calling them independent families. CloudFix records 252/67 have distinct resource topology and record IDs, but source-project independence remains unknown. Across the entire supported review there are three group IDs; **there are not three independently established overauthorization source families**. This is a material evidence limitation.

All P-Verifier variants remain in development. CloudFix 67 is development diagnostic; 252 is a held-out confirmation **safe control**, with no costs tuned on it. These splits provide no independent confirmation of overauthorization repair. Original per-record forum links, intended workloads and binding metadata were not recovered, so confirmatory real-deployment claims are unavailable.

## Candidate space and check entry

`src.public_round2.evaluate(policy, task)` returns safety, legitimate availability, witnesses and missing topics. `candidate_edits(task)` returns complete candidate policies, IDs, unit costs and explanations. The list is fixed before repair and shared by B4/SPR. Unit cost is one statement deletion, a single-action **Allow** narrowing to the declared legitimate exact resource catalog, or append of a Receive Deny for the forbidden finite catalog. A catalog narrowing is admitted only if every proposed resource string contains neither AWS `*` nor `?` and is authorized by the **same original statement considered alone**. Since its new language is a finite set of exact strings, these membership checks establish containment in that original AWS resource glob language. Deny statements cannot be catalog-replaced. This is exact AWS resource-set containment, not MQTT filter equivalence or AWS-to-Mosquitto translation. Operation count and changed-statement count coincide for each provided single edit but must not be conflated for future compositions. Added Allow operations were deliberately omitted; the pure-undergrant PUB20 case has no feasible single edit in this space. Deletion candidates are retained as specified, including deletion of existing Deny statements; deletion must therefore still be checked against all hard constraints and is not claimed to be intrinsically permission-decreasing.

Each candidate list is a finite collection of one-edit alternatives; zero-edit must be included by the solver. Optimality may only be claimed relative to this list, unless a solver separately specifies and enumerates composed edits. Single-edit feasibility recorded in task cards is a construction sanity check, not a solver timing result or independent verification. For the 11 eligible scenarios at least one declared candidate satisfies the finite checks. This simple repairability is not evidence of an algorithmic advance.

## Remaining evidential limits

No reviewed public-source case has been deployed on AWS or Mosquitto. Zero public-source Broker cases are admitted. No new source licensing permission was obtained; original checkouts and copied task-card policies remain local research materials and must be excluded from a public redistributable archive until rights are resolved. The task cards support a transparent **derived-task feasibility study**, not a large real-error benchmark. The next useful work is independent checks and method comparison on this frozen subset, followed by original requirement and provenance recovery; generating more same-template variants would not resolve the independence gap.
