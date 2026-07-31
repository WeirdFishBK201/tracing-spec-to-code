# tracing-spec-to-code M05 Evaluation and Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

- Status: Approved — In Progress
- Milestone: M05 — Evaluation and release
- Spec: `docs/specs/tracing-spec-to-code-spec.md`
- Roadmap: `docs/plans/tracing-spec-to-code-roadmap.md`
- Design: `docs/design/2026-07-30-tracing-spec-to-code-m05-evaluation-release-design.md`
- Requirements: REQ-TS2C-015, REQ-TS2C-016
- Gate P: Approved on 2026-07-30
- Gate Δ: CP-09, CP-10, and CP-11 Approved on 2026-07-31

**Goal:** Produce reproducible Codex behavior, eight-client compatibility, and staged-candidate clean-clone evidence without publishing or mutating a remote.

**Architecture:** Reuse `tools/clients.json`, one versioned case file, and one standard-library evaluation CLI. CP-09 archives unchanged schema-v1 evidence and records active schema-v2 reruns; CP-10 adds one exact active-to-active full-group rebuild. Client actions remain manual.

**Tech Stack:** Python 3.10+ standard library (`argparse`, `dataclasses`, `datetime`, `json`, `pathlib`, `re`, `secrets`, `unittest`), existing local Git, and explicitly approved client CLIs/GUI sessions.

## Global Constraints

- Implement only M05; `npx`, remote-source installation, native-handle hardening, tag, Release, PR, merge and push remain out of scope.
- Do not install, log in, access the network, or invoke an external client without a separate just-in-time approval.
- Never write a real home/client root; use isolated project roots and synthetic repository fixtures.
- Store only reviewed evidence with no secrets, real-home paths, repository-external paths, `VGCCoach2`, or legacy `agentic-workflow` content.
- Reuse `tools/clients.json`; do not create another client registry, adapter framework, or persisted summary.
- Preserve the 16 schema-v1 records byte-for-byte under `evaluation/archive/cp09/`; no general supersession graph.
- Use TDD for deterministic code. Create one M05 milestone commit only after every gate passes; do not make per-task implementation commits or push.

## File map and contracts

- Create `evaluation/cases.json`: three paired baseline/pressure scenarios, two wording variants, and Level 1/2 case templates.
- Create `evaluation/README.md`: exact prompt execution, rationale review, client runbook, evidence recording, and approval boundaries.
- Create `tools/evaluate.py`: `prepare`, `record`, `validate`, and `summary` commands.
- Create `tests/test_evaluation.py`: case/evidence/CLI/summary and candidate-snapshot integration tests.
- Commit the 37 exact active/archive JSON files listed under Commit scope; optional reruns require another Gate Δ.
- Create the approved CP-09, CP-10, and CP-11 documents under `docs/changes/`.
- Modify `.gitignore`, `README.md`, `evaluation/README.md`, this plan, and the roadmap for local runtime hygiene, user commands, actual evidence, final status, and commit facts.
Library contracts in `tools/evaluate.py`:

```text
CaseSpec(id, scenario_id, run_type, prompt, skill_loaded, expected_decision, pressures, variant_group, decision_options, response_contract, document_schema_version)
EvidenceRecord(schema_version, run_id, case_id, client_id, skill_loaded, client_version, model, config, runtime_surface, attempt_id, prepared_at, session_ref, recorded_at, prompt, actual_decision, verbatim_rationale, outcome, reason, notes, rationale_review, supersedes_run_ids, rerun_of, change_proposal)
EvaluationSummary(baseline_observed, pressure_passed, wording_groups, level1_passed, level2_passed, blocked_runs, failed_runs, open_rationales)
EvaluationError(code, message, path=None)
load_cases(path: Path) -> tuple[CaseSpec, ...]
load_evidence(path: Path) -> EvidenceRecord
record_evidence(input_path: Path, evidence_dir: Path, cases_path: Path, registry_path: Path) -> Path
validate_suite(cases_path: Path, registry_path: Path, evidence_dir: Path) -> EvaluationSummary
```

Stable policy codes: `CASE_INVALID`, `RUN_EXISTS`, `EVIDENCE_INVALID`, `SENSITIVE_CONTENT`, `EVALUATION_INCOMPLETE`, `EVALUATION_FAILED`. CLI returns `0` for a successful requested operation, `1` for policy failure/blocker, and `2` for invalid arguments or unexpected runtime failure.

## Tasks

### M05-T01 — Evaluation contract and CLI

**Objective:** Produce a strict offline case/evidence validator and CLI without invoking any real client.
**Requirements:** REQ-TS2C-015, REQ-TS2C-016.
**Files/contracts:** Modify `evaluation/cases.json`, `evaluation/README.md`, `tools/evaluate.py`, and `tests/test_evaluation.py`; preserve the CLI commands and stable codes above.

- [x] Build and review schema-v1 case/evidence/CLI/summary contracts; 30 targeted and 210 full tests passed with four Windows skips.
- [x] Add RED tests for duplicate execution identity, time ordering, placeholder environment values, baseline/loaded mismatch, behavioral wording contracts, archive exclusion, invalid `rerun_of`, and missing/mixed CP-09 provenance.
- [x] Extend `prepare`/`record` with schema-v2 execution metadata and exact CP-09 rerun fields; keep exclusive writes and sensitive-content checks.
- [x] Make `validate` require comparable pair environments, five distinct wording sessions, the exact archive set, and only active non-recursive evidence counts.
- [x] Run targeted/full tests and obtain independent spec and quality reviews before any Codex rerun; 45 targeted and 225 full tests PASS with four Windows skips, reviews PASS.
- [x] Add the approved CP-10 exact full-group rebuild contract with RED/GREEN tests; preserve CP-09 archive validation and immutable active evidence. 60 targeted and 240 full tests PASS with four Windows skips; independent spec and quality reviews PASS.

### M05-T02 — Codex baseline, pressure, and wording evidence

**Objective:** Complete 3 baseline + 3 loaded pressure + 10 effective wording results through immutable CP-09 evidence and the approved CP-10 commit-boundary rebuild.
**Requirements:** REQ-TS2C-015, REQ-TS2C-016.
**Files/contracts:** Preserve the CP-09 archive and 16 active v2 files; add the exact five CP-10 replacement files named under Commit scope and record exact approved commands in `evaluation/README.md`.

- [x] Move all 16 v1 files without content changes, prove archive hashes match, and require the active T02 suite to report incomplete.
- [x] Capture one exact Codex CLI path/version, explicit model, config snapshot, isolated loaded/unloaded roots, and 16 fresh CP-09 runs with distinct execution identities.
- [x] Review all CP-09 rationales; retain the immutable `wording-commit-boundary-07` `new-rationale` failure and require deterministic validation to fail closed.
- [x] Complete the CP-10 deterministic contract and independent reviews before any replacement session.
- [x] After separate approval, run and review the exact five fresh CP-10 replacements; effective summary reports `3 observed + 3/3 + 5/5 + 5/5`, zero failures, and zero open rationales.

### M05-T03 — External-client scope disposition

**Objective:** Preserve an honest boundary after the user retained ownership of Level 1 discovery/minimal-flow and Level 2 structure/smoke execution.
**Requirements:** REQ-TS2C-015, REQ-TS2C-016.
**Files:** Modify `README.md`, `evaluation/README.md`, this plan, and the roadmap; do not create any `client-*.json` result.
**Consumes:** The user direction on 2026-07-31 to perform the eight-client testing independently.
**Produces:** An explicit user-owned external verification boundary with no fabricated PASS evidence.

- [x] Record that the user retained ownership of the eight-client discovery/smoke matrix and directed T04 closeout to proceed without Codex executing T03.
- [x] Exclude all eight `client-*.json` paths from the candidate and retain the unfiltered evaluation validator as a fail-closed check.
- [x] Document that the local candidate proves only the baseline, pressure, wording, deterministic repository, and clean-clone gates; it does not claim `5/5 + 3/3` client completion.

### M05-T04 — Release-ready candidate, documentation, and milestone commit

**Objective:** Prove the exact staged local candidate is reproducible from a clean local clone and create one verified M05 commit without claiming the user-owned client matrix.
**Requirements:** REQ-TS2C-015, REQ-TS2C-016.
**Files:** Modify `.gitignore`, `README.md`, this plan, and the roadmap; stage the exact Commit scope below.
**Consumes:** T01–T02 passing evidence, the T03 user-owned boundary, design acceptance criteria, and M03 exact-scope/precommit policy.
**Produces:** Completed evidence tables, candidate tree hash, clean-clone results, final matching commit, and clean local status.

- [x] Document evaluation commands and boundaries; record actual task/review/evidence results, four platform skips if unchanged, baseline dirty paths, exact scope, and commit draft in this plan.
- [x] Run the targeted/full suites, validators, installer matrix, Python 3.10 grammar, content-scoped isolation scan, archive checks, and `git diff --check`; require all applicable checks PASS.
- [x] Obtain final independent spec and code-quality reviews, update review evidence to PASS, and stage only the exact Commit scope with literal pathspecs.
- [x] Export that index with `git checkout-index --all --prefix=<candidate>/source/`; configure the temp repo identity plus `core.autocrlf=false`, make a throwaway commit, require its `HEAD^{tree}` to equal the candidate hash, then `git clone --local` it and rerun tests, validators, installer matrix, README help commands, metadata checks, and evaluation summary.
- [x] Prepare one local `feat(evaluation): add reproducible release evidence` commit and its read-only `precommit`/post-commit checks. Record the actual commit and matching tree hash only in the delivery summary, then stop without push.

## Milestone verification

```text
python -m unittest tests.test_evaluation -v
python -m unittest discover -s tests -v
python tools/evaluate.py validate --run-type baseline --run-type pressure --run-type wording
python tools/evaluate.py summary --run-type baseline --run-type pressure --run-type wording --format json
python tools/evaluate.py validate
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo tests/fixtures/valid-project
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo . --format json
python C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tracing-spec-to-code
rg -n "VGCCoach2|agentic-workflow" README.md skills/tracing-spec-to-code evaluation/README.md evaluation/cases.json evaluation/evidence evaluation/archive
git diff --check
```

Expected: deterministic tests/validators PASS; Codex `3 observed + 3/3 + 5/5 + 5/5`; the unfiltered client-dependent evaluation fails closed until user evidence exists; isolation has no matches; candidate clean clone matches the staged/final tree.

## Traceability

| Task | Requirements | Implementation | Tests |
|---|---|---|---|
| `M05-T01` | `REQ-TS2C-015, REQ-TS2C-016` | `evaluation/cases.json, evaluation/README.md, tools/evaluate.py` | `tests/test_evaluation.py` |
| `M05-T02` | `REQ-TS2C-015, REQ-TS2C-016` | `skills/tracing-spec-to-code/SKILL.md, evaluation/archive/cp09/baseline-gate-01.json, evaluation/evidence/baseline-gate-02.json, evaluation/evidence/wording-commit-boundary-15.json` | `tests/test_evaluation.py` |
| `M05-T03` | `REQ-TS2C-015, REQ-TS2C-016` | `README.md, evaluation/README.md, docs/changes/tracing-spec-to-code-cp11-user-owned-client-verification.md, docs/plans/tracing-spec-to-code-m05-evaluation-release.md` | `docs/changes/tracing-spec-to-code-cp11-user-owned-client-verification.md` |
| `M05-T04` | `REQ-TS2C-015, REQ-TS2C-016` | `.gitignore, README.md, docs/plans/tracing-spec-to-code-m05-evaluation-release.md, docs/plans/tracing-spec-to-code-roadmap.md` | `tests/test_evaluation.py` |

## Evidence and commit

### Task status

| Task | Status | Actual verification |
|---|---|---|
| `M05-T01` | `Completed` | `cp10-contract: PASS` |
| `M05-T02` | `Completed` | `recorded-evidence: PASS` |
| `M05-T03` | `Completed` | `scope-disposition: PASS` |
| `M05-T04` | `Completed` | `release-candidate: PASS` |

- Approved proposals: CP-09, CP-10, CP-11
- Deviations: v1 T02 evidence failed independent quality review; CP-09 rerun exposed an authority-channel gap requiring the immutable CP-10 full-group rebuild; on 2026-07-31 the user retained ownership of the eight-client live matrix and directed T04 closeout without Codex executing T03, so no client PASS evidence is claimed; `evaluation/.runtime/` is ignored as a non-release local workspace so T04 can retain drafts without polluting final status.
- Baseline dirty paths: None

### Verification

| Scope | Command | Expected | Actual | Result |
|---|---|---|---|---|
| Targeted | `python -m unittest tests.test_evaluation -v` | All pass | `62/62 PASS` | `PASS` |
| Broader | `python -m unittest discover -s tests -v` | All pass | `242/242 PASS` | `PASS` |
| Evaluation | filtered `evaluate.py validate/summary` | Complete local matrix | `local-matrix: PASS` | `PASS` |
| Fail-closed | unfiltered `evaluate.py validate` | Exit 1 without client evidence | `fail-closed: PASS` | `PASS` |
| Client boundary | user-owned Level 1 discovery + Level 2 smoke | No fabricated result | `boundary: PASS` | `PASS` |
| Candidate | staged local candidate clean-clone gate | All local gates pass | `candidate: PASS` | `PASS` |
| Fixture | repository validator on valid fixture | No issues | `fixture: PASS` | `PASS` |
| Repository | repository self-validator | Valid JSON | `repository: PASS` | `PASS` |
| Skill | `quick_validate.py skills/tracing-spec-to-code` | Valid Skill | `skill: PASS` | `PASS` |
| Matrix | installer matrix test | 8 clients × 2 scopes | `16/16 PASS` | `PASS` |
| Grammar | `ast.parse(..., feature_version=(3, 10))` | All Python files parse | `41/41 PASS` | `PASS` |
| Isolation | content-scoped `rg` scan | No matches | `isolation: PASS` | `PASS` |
| Diff | `git diff --check` | No errors | `diff: PASS` | `PASS` |
| Reviews | `independent spec and code-quality reviews` | No blockers | `final-reviews: PASS` | `PASS` |

The filtered evaluation summary is `3` observed baselines, `3/3` pressure,
`5/5` semantic-scope, and `5/5` commit-boundary, with zero failures, blocked
runs, or open rationales. Four full-suite skips are unchanged Windows platform
limitations. The unfiltered evaluation intentionally reports
`EVALUATION_INCOMPLETE: level1 clients are incomplete`.

The final quality review found two pre-candidate gaps. TDD regression tests
first reproduced a raw `TypeError` for non-string `run_type` and copied
execution identities across Level 1 records. `load_cases` now returns the
stable `CASE_INVALID` policy result, and `validate_suite` requires distinct
`attempt_id` and `session_ref` values across every active schema-v2 record.

The staged candidate, its throwaway source commit, and its local clean clone
had the same tree. The clean clone repeated 62 targeted and 242 full tests,
the 16-combination installer matrix, fixture/repository/Skill validators,
README help commands, evidence metadata counts, isolation scanning, and the
filtered/unfiltered evaluation boundary. Per milestone-commit policy, the
actual final tree and commit hashes are reported after commit rather than
written back into the commit that they identify.

### Commit scope

| Path | Purpose |
|---|---|
| `.gitignore` | Exclude local evaluation runtime workspaces from release status |
| `README.md` | Document evaluation and release-ready commands |
| `skills/tracing-spec-to-code/SKILL.md` | Clarify current-user authority for external side effects |
| `evaluation/README.md` | Define the approved execution/runbook boundary |
| `evaluation/cases.json` | Define paired scenarios and client case templates |
| `tools/evaluate.py` | Implement prepare/record/validate/summary |
| `tests/test_evaluation.py` | Verify deterministic evaluation contracts |
| `docs/plans/tracing-spec-to-code-m05-evaluation-release.md` | Record M05 plan, actual evidence, and commit facts |
| `docs/plans/tracing-spec-to-code-roadmap.md` | Record final M05 delivery state |
| `docs/changes/tracing-spec-to-code-cp09-reproducible-evaluation-reruns.md` | Record approved Gate Δ |
| `docs/changes/tracing-spec-to-code-cp10-authority-channel-wording-rebuild.md` | Record approved authority-channel Gate Δ |
| `docs/changes/tracing-spec-to-code-cp11-user-owned-client-verification.md` | Record the approved external-client ownership and sequencing Gate Δ |
| `evaluation/archive/cp09/baseline-gate-01.json` | Preserve v1 gate baseline |
| `evaluation/archive/cp09/baseline-context-01.json` | Preserve v1 context baseline |
| `evaluation/archive/cp09/baseline-verification-git-01.json` | Preserve v1 verification/Git baseline |
| `evaluation/archive/cp09/loaded-gate-01.json` | Preserve v1 gate pressure |
| `evaluation/archive/cp09/loaded-context-01.json` | Preserve v1 context pressure |
| `evaluation/archive/cp09/loaded-verification-git-01.json` | Preserve v1 verification/Git pressure |
| `evaluation/archive/cp09/wording-semantic-scope-01.json` | Preserve v1 semantic run 1 |
| `evaluation/archive/cp09/wording-semantic-scope-02.json` | Preserve v1 semantic run 2 |
| `evaluation/archive/cp09/wording-semantic-scope-03.json` | Preserve v1 semantic run 3 |
| `evaluation/archive/cp09/wording-semantic-scope-04.json` | Preserve v1 semantic run 4 |
| `evaluation/archive/cp09/wording-semantic-scope-05.json` | Preserve v1 semantic run 5 |
| `evaluation/archive/cp09/wording-commit-boundary-01.json` | Preserve v1 commit run 1 |
| `evaluation/archive/cp09/wording-commit-boundary-02.json` | Preserve v1 commit run 2 |
| `evaluation/archive/cp09/wording-commit-boundary-03.json` | Preserve v1 commit run 3 |
| `evaluation/archive/cp09/wording-commit-boundary-04.json` | Preserve v1 commit run 4 |
| `evaluation/archive/cp09/wording-commit-boundary-05.json` | Preserve v1 commit run 5 |
| `evaluation/evidence/baseline-gate-02.json` | Record v2 gate baseline |
| `evaluation/evidence/baseline-context-02.json` | Record v2 context baseline |
| `evaluation/evidence/baseline-verification-git-02.json` | Record v2 verification/Git baseline |
| `evaluation/evidence/loaded-gate-02.json` | Record v2 gate pressure |
| `evaluation/evidence/loaded-context-02.json` | Record v2 context pressure |
| `evaluation/evidence/loaded-verification-git-02.json` | Record v2 verification/Git pressure |
| `evaluation/evidence/wording-semantic-scope-06.json` | Record v2 semantic run 6 |
| `evaluation/evidence/wording-semantic-scope-07.json` | Record v2 semantic run 7 |
| `evaluation/evidence/wording-semantic-scope-08.json` | Record v2 semantic run 8 |
| `evaluation/evidence/wording-semantic-scope-09.json` | Record v2 semantic run 9 |
| `evaluation/evidence/wording-semantic-scope-10.json` | Record v2 semantic run 10 |
| `evaluation/evidence/wording-commit-boundary-06.json` | Record v2 commit run 6 |
| `evaluation/evidence/wording-commit-boundary-07.json` | Record v2 commit run 7 |
| `evaluation/evidence/wording-commit-boundary-08.json` | Record v2 commit run 8 |
| `evaluation/evidence/wording-commit-boundary-09.json` | Record v2 commit run 9 |
| `evaluation/evidence/wording-commit-boundary-10.json` | Record v2 commit run 10 |
| `evaluation/evidence/wording-commit-boundary-11.json` | Replace CP-09 commit run 6 under CP-10 |
| `evaluation/evidence/wording-commit-boundary-12.json` | Replace CP-09 commit run 7 under CP-10 |
| `evaluation/evidence/wording-commit-boundary-13.json` | Replace CP-09 commit run 8 under CP-10 |
| `evaluation/evidence/wording-commit-boundary-14.json` | Replace CP-09 commit run 9 under CP-10 |
| `evaluation/evidence/wording-commit-boundary-15.json` | Replace CP-09 commit run 10 under CP-10 |
Client results are excluded by the user-owned T03 boundary. Ranges and globs are never passed to Git or precommit.

### Commit draft

```text
feat(evaluation): add reproducible release evidence

Milestone: M05 Evaluation and release
Requirements: REQ-TS2C-015, REQ-TS2C-016
Change-Proposals: CP-09, CP-10, CP-11
```
