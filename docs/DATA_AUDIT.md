# Third-round status note

第三轮补充见SOURCE_RECOVERY.md：原20策略/18个B工作负载及其准入未改；新增同一官方guide的2个注入C案例（1来源组），业务说明A与研究者请求/禁止B分列，新增独立自然过授组0。受控开放主题任务不增加公开独立来源。

---

# Current audit status — Round 2

Twenty deduplicated source policies reviewed; ten supported cards generate eighteen disclosed B workloads. Eleven eligible overgrant scenarios derive from six original policies in one conservative template group. Five safe controls and two deficit diagnostics remain in full results. No source-authored legitimate workload A was independently established; all legitimate workload assumptions are researcher-added B. See PUBLIC_TASK_REVIEW.md and results/round2/summary/public_card_review.csv plus task_admission.csv. Public-source Broker deployments remain zero; actual controlled Mosquitto deployment evidence is separately recorded in ROUND2_BROKER_REPORT.md. Historical zero-admission text below refers to Round 1. Source rights and unknown independence remain unchanged.

# Source audit (2026-10-28)

Acquisition is independent of EBR-IoT. A bounded top-level name check found no named P-Verifier/CloudFix checkout; `acfix_feasibility/upstream` was inspected only at directory level and is a smart-contract resource, not reused. No EBR files or processes were inspected or changed. The EDA and data-quality skills were read and used for document grain, duplicate and missing-requirement checks. The audit does not infer intended authorization from observed requests.

## Acquired resources and rights

|Resource|Pinned commit|Acquisition|License / redistribution|
|---|---|---|---|
|[P-Verifier](https://github.com/P-Verifier/P-Verifier)|e79bc6d8ebf602ca5bdb002f18ff92402b2e4f57|git shallow clone|No LICENSE/COPYING found; no blanket redistribution permission established|
|[CloudFix](https://github.com/bethelhall/fixmypolicy)|7334a1be34946909df7e1eef6276f6803135410d|git shallow clone|No LICENSE/COPYING found; no blanket redistribution permission established|
|[PV-Evaluation](https://github.com/P-Verifier/PV-Evaluation)|not acquired|clone stopped after partial transfer, >364 MB, no checked-out files|Unknown; excluded from measured counts|

Keep upstream checkouts local and excluded from any redistributable package until rights are clarified. Public access is not a license. Manifests contain relative filenames and SHA-256 of every acquired Git-tracked file (excluding generated Python caches); source files are preserved. Retrieval used network-enabled execution after the default sandbox could not resolve GitHub. Partial PV-Evaluation git objects are not data usable by this project.

## Counts and grain

P-Verifier has **843 non-git files, 834 JSON documents, 541 unique canonical whole JSON documents**. The documents include wrappers, policies, expectations, family variants and repeated copies. Extracting `Statement`, `Statement1`, and `Statement2` gives 969 policy-document occurrences and 547 distinct ordered-statement hashes. This is **not 834 independent repair tasks**. The 27 parent directories are inventory strata, not verified independent source projects. All 834 JSON files parsed. 911 extracted occurrences contain explicit `iot:` actions; 893 have only Sid/Effect/Action/Resource syntax, which does not establish semantic support or repair feasibility.

CloudFix has **33,281 non-git files, 16,769 JSON files** across originals, faulty variants, repaired results, request suites and backups. 92 do not parse as JSON. There are 8,354 unique parseable canonical JSON documents, 12,492 extracted policy occurrences, and 4,468 distinct ordered-statement hashes. These broad counts deliberately include research artifacts and are not an independent-task denominator.

The specific `clouldfix/data/original_policy` directory contains **282 valid JSON files / 276 unique canonical full documents**. Only **22 files contain explicit `iot:` text**; other IAM policies must not be described as MQTT policies. This lexical count is not an applicability decision. IAM conditions and service actions need an explicit adapter, and forum origin / ground-truth correctness remain upstream claims rather than independently established facts.

P-Verifier/CloudFix extracted-statement exact-hash overlap is 0. P-Verifier/PV-Evaluation overlap is **unknown**, not zero: PV-Evaluation has not been obtained. Normalization preserves statement and action-array order; semantically equivalent policies may still have different hashes. Family clustering needs provenance review, not only exact deduplication.

## Repair-task status and splitting

The acquired public resources provide **zero admitted repair tasks in this first audit**: legitimate business needs, identity bindings, supported semantics and independent checks have not been validated for each policy. No AWS policy is silently translated into a Mosquitto deployment. Public-source supported-semantic policy count is therefore **not yet established**, and publicly sourced deployable Mosquitto cases are **0**. Controlled tasks in `data/tasks` belong to category C and must be counted separately by the pilot; they do not increase public independent source groups.

At present there are **two acquired repository origins**, not two proven independent populations of real deployments. No policy family has been admitted to a confirmatory split. Before admission, attach original project/family/template group IDs, declare any supplemental requirements as category B, and reserve entire families. Never split variants across development/confirmation. Do not tune candidate costs on confirmation tasks. Requests generated by CloudFix are not independently established business ground truth.

## Original-tool smoke tests

Both original commands were actually invoked with Python 3.14; logs are in `results/raw/upstream`:

* P-Verifier `main.py -i policy_benchmark/family_policies/allow_mode/complex_family_#_error.json` failed during import: `ModuleNotFoundError: z3`. A local free Z3 download was attempted but stopped due slow download and no need for main pilot dependency. P-Verifier has **not successfully analyzed** a case here.
* CloudFix original `clouldfix/code/validate_requests.py --help` failed during import: `ModuleNotFoundError: frontend` (Quacky dependency absent from checkout). This is a validator smoke test, not a repair execution. CloudFix repair has **not run**; its local model/Quacky/ABC dependencies have not been provisioned. No paid API or credentials were used.

Reproduce the full local inventory with `python scripts/audit_sources.py`. Source counts and per-file hashes are machine-readable in `data/manifests/source_audit.json` and `source_files.csv`. Audit-only syntax feature counters are occurrences, not independent cases. The measured quantities must remain distinct from the pilot repair denominators.

## Round 2 append-only update

The first-audit zero-admission result above is preserved as history. Round 2 reviewed 20 distinct extracted policy documents without further downloads. See `PUBLIC_TASK_REVIEW.md` and `data/tasks/round2_public.json` for pinned per-card evidence and exclusions. Ten policy cards support explicitly researcher-added category B workloads, yielding 18 dependent scenarios: 11 eligible overauthorization repairs, five safe controls, one mixed overgrant/undergrant diagnostic (PUB05_S2), and one pure undergrant diagnostic (PUB20_S3). The eligible repairs originate in six P-Verifier documents but only **one conservative template group**. Two CloudFix record groups provide a safe control and undergrant diagnosis; they do not increase the overauthorization source-family count. No original legitimate business requirements or public-source deployable Broker cases were established, and no upstream redistribution rights were resolved. P-Verifier `Expected.type:0` maps to unsupported `check0` at the pinned commit; only the literal `NotReceive` strings are adopted as experimental forbidden requirements, not the complete original oracle. Counts of scenarios, documents, groups and genuinely independent source deployments remain distinct.


## Manuscript grain clarification — 2026-11-02

Rechecking the pinned source-file manifest and the extraction implementation confirms 834/834 valid P-Verifier JSON files; 541 distinct hashes of complete JSON documents; and 969 extracted `{Statement: value}` occurrences with 547 distinct extracted-object hashes. The extractor recursively recognizes Statement, Statement1 and Statement2. Both hash normalizations sort object keys and retain all array orders. The difference 541 vs 547 is therefore a change of statistical unit and denominator, not a statement-order ablation. Complete documents preserve wrappers and nonpolicy fields; extracted objects do not. No count is a number of independent repair tasks. The legacy field name `unique_statement_documents` denotes these extracted objects. The nonmutating recount is recorded in results/revision_20261102/pverifier_grain_check.json; historical source manifests and results are unchanged.
