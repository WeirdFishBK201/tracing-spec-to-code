# Readable Localized Workflow Terminology Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

- Status: Completed
- Milestone: M06 — Readable localized terminology
- Spec: `docs/specs/tracing-spec-to-code-spec.md`
- Roadmap: `docs/plans/tracing-spec-to-code-roadmap.md`
- Design: `docs/superpowers/specs/2026-07-31-readable-localized-workflow-terminology-design.md`
- Requirements: REQ-TS2C-017, REQ-TS2C-016
- Implementation approval: Approved on 2026-07-31
- Change approval: Not applicable; CR-01 through CR-12 are historical migration inputs

**Goal:** Replace the current-tree workflow vocabulary with one canonical English contract and make routine user prompts select English or Simplified Chinese from the most recent user message.

**Architecture:** The validator, evidence model, evaluation harness, templates, and maintained artifacts use canonical English names only. The Skill treats workflow states as semantic concepts and renders their user-facing labels from a two-language table; no compatibility parser, alias, or dual-write path is retained.

**Tech Stack:** Python 3.10+ standard library, Markdown, JSON, YAML, Git, and `unittest`.

## Global Constraints

- Implement only M06 and REQ-TS2C-017.
- Canonical terms are Requirements Confirmation, Implementation Approval, Change Approval, and Change Request.
- Stable machine names are `requirements_confirmation`, `implementation_approval`, `change_approval`, `change_request`, `change_request_id`, and `approved_change_requests`.
- Change Request IDs use `CR-NN`; filenames use `FEATURE-crNN-SHORT-NAME.md`; commit trailers use `Change-Requests`.
- User labels are English or Simplified Chinese according to the dominant language of the latest user message; ambiguous or unsupported input falls back to English.
- README files, maintained documentation, templates, JSON, YAML, filenames, and commit trailers are English.
- The four exact Simplified Chinese label literals are localized data and are the only permitted non-English text in maintained documentation examples.
- This is a breaking migration: no compatibility aliases, fallback parsing, migration readers, or dual writes.
- Do not rewrite Git history, use the network, install dependencies, or claim external client verification.
- Preserve the user-owned client-verification boundary and recorded zero-result summary.
- Before M06 execution, land the reviewed M05 administrative completion changes as a predecessor commit, then capture a fresh M06 dirty-path baseline.
- Use one scoped milestone commit after all five tasks pass; do not create intermediate implementation commits.
- Give every task a worker packet and read-only spec review; add a read-only code-quality review for Tasks 1, 2, and 4.

---

## Tasks

### M06-T01 — Canonical Artifact and Approval Contract

**Objective:** Make configuration, artifact discovery, metadata parsing, and repository validation accept only the canonical contract.
**Requirements:** REQ-TS2C-017, REQ-TS2C-016.

**Files:**
- Modify `skills/tracing-spec-to-code/scripts/tstc/config.py`, `artifacts.py`, `validation.py`, and `skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py`.
- Rename the current change-record template to `skills/tracing-spec-to-code/assets/templates/change-request.md`; modify `config.json`, `spec.md`, `roadmap.md`, and `milestone-plan.md` in that template directory.
- Modify `tests/test_config.py`, `tests/test_artifacts.py`, `tests/test_validation.py`, `tests/test_cli.py`, and all `tests/fixtures/` artifacts; rename the valid record to `tests/fixtures/valid-project/docs/changes/sample-cr01-traceability.md`.

**Interfaces:**
- Produce `DEFAULT_CHANGE_REQUEST_FILENAME_TEMPLATE`, `ResolvedConfig.change_request_filename_template`, `ArtifactKind.CHANGE_REQUEST`, `ApprovalRef(name: str, status: str, line: int)`, and `ArtifactRef.approval_refs: tuple[ApprovalRef, ...]`.
- Metadata labels are exactly `Requirements confirmation`, `Implementation approval`, and `Change approval`.
- Validation codes are `REQUIREMENTS_CONFIRMATION_MISSING`, `IMPLEMENTATION_APPROVAL_MISSING`, and `CHANGE_REQUEST_PENDING`.

- [ ] **Step 1: Write canonical-contract tests and run RED.** Run `.venv\Scripts\python.exe -m unittest tests.test_config tests.test_artifacts tests.test_validation tests.test_cli -v`; expect failures because the new fields, enum member, labels, and issue codes do not exist.
- [ ] **Step 2: Implement the minimal parser and template migration.** Rename every affected symbol and field, use `{change_request}` and `{change_request_slug}`, and remove superseded parser branches.
- [ ] **Step 3: Run the focused suite GREEN.** Re-run the Task 1 command; expect all tests PASS and the valid fixture to produce no validation issues.
- [ ] **Step 4: Review the Task 1 diff.** Confirm one artifact model, one approval metadata grammar, no alias path, and no files outside scope.

### M06-T02 — Canonical Evidence and Commit Contract

**Objective:** Carry Change Request IDs through evidence, precommit scope validation, and commit-message validation without legacy fields or trailers.
**Requirements:** REQ-TS2C-017, REQ-TS2C-016.

**Files:**
- Modify `skills/tracing-spec-to-code/scripts/tstc/evidence.py`, `precommit.py`, `git_checks.py`, and `skills/tracing-spec-to-code/assets/templates/milestone-plan.md`.
- Modify `tests/test_evidence.py` and `tests/test_git_checks.py`.

**Interfaces:**
- `EvidenceRecord.approved_change_requests: tuple[str, ...]`.
- `_change_request_id_from_filename(...) -> str` returns `CR-NN`; evidence headings use `Approved Change Requests`.
- Commit messages accept one optional `Change-Requests` trailer equal to the approved Change Request IDs in evidence.

- [ ] **Step 1: Write evidence and commit tests and run RED.** Run `.venv\Scripts\python.exe -m unittest tests.test_evidence tests.test_git_checks -v`; expect failures on the renamed field, ID grammar, heading, and trailer.
- [ ] **Step 2: Implement the canonical evidence flow.** Rename dataclass fields and helpers, use `CR-\d+`, derive IDs from `crNN` filenames, and remove obsolete keys.
- [ ] **Step 3: Run the focused suite GREEN.** Re-run the Task 2 command; expect all evidence, staged-scope, and commit-message cases PASS.
- [ ] **Step 4: Review the Task 2 diff.** Verify duplicate IDs, missing evidence, extra staged paths, and malformed trailers still fail closed.

### M06-T03 — Localized User Prompt Policy and Packaged Skill

**Objective:** Make the distributed Skill use descriptive localized labels for routine user interaction while keeping maintained package content English.
**Requirements:** REQ-TS2C-017, REQ-TS2C-016.

**Files:**
- Modify `skills/tracing-spec-to-code/SKILL.md`, `references/workflow.md`, `references/task-execution.md`, `references/milestone-commit.md`, and `agents/openai.yaml`.
- Rename the current M02 change-authorization scenario to `tests/scenarios/m02/change-approval.md`; modify the remaining files under `tests/scenarios/m02/` and `tests/scenarios/m03/`.
- Modify `tests/test_distribution.py` and `tests/test_install_cli.py`.

**Interfaces:**
- Semantic prompt keys are the three approval machine names in Global Constraints.
- English labels are `Requirements confirmation`, `Implementation approval`, `Change approval`, and `Change request`; Simplified Chinese labels are `需求确认`, `实施批准`, `变更批准`, and `变更申请`.
- Normal prompts omit internal IDs unless needed for disambiguation or explicitly requested; language choice cannot change authorization state.

- [ ] **Step 1: Add packaged-content and bilingual-policy tests and run RED.** Run `.venv\Scripts\python.exe -m unittest tests.test_distribution tests.test_install_cli -v`; expect missing canonical labels and language-selection policy.
- [ ] **Step 2: Rewrite the Skill package and scenarios.** Use semantic workflow terms, add the exact rendering table and latest-message rule, keep machine output English, and remove IDs from routine prompt examples.
- [ ] **Step 3: Run package verification GREEN.** Re-run Task 3 tests, then `.venv\Scripts\python.exe C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\tracing-spec-to-code`; expect all tests PASS and `Skill is valid!`.
- [ ] **Step 4: Review the Task 3 diff.** Confirm message-by-message language switching, English fallback, and identical authorization semantics in both languages.

### M06-T04 — Evaluation Schema and Evidence Migration

**Objective:** Migrate the maintained evaluation registry, CLI, evidence, and integrity checks to the canonical Change Request contract.
**Requirements:** REQ-TS2C-017, REQ-TS2C-016.

**Files:**
- Modify `tools/evaluate.py`, `evaluation/cases.json`, `evaluation/README.md`, and `tests/test_evaluation.py`.
- Move the archived rerun set to `evaluation/archive/cr09/`; rename its confirmation files to `baseline-requirements-confirmation-01.json` and `loaded-requirements-confirmation-01.json`.
- Modify every JSON file in `evaluation/archive/cr09/` and `evaluation/evidence/`; rename active confirmation files to `baseline-requirements-confirmation-02.json` and `loaded-requirements-confirmation-02.json`.

**Interfaces:**
- `tools.evaluate.EvidenceRecord.change_request: str | None`; rationale review uses `change_request_id`; template CLI flag is `--change-request`.
- Registry discovery is `_approved_change_requests(...) -> set[str]`; rerun mappings and integrity constants use `CR09` and `CR10` names with regenerated semantic digests.

- [ ] **Step 1: Update evaluation tests and run RED.** Run `.venv\Scripts\python.exe -m unittest tests.test_evaluation -v`; expect schema-key, identifier, filename, mapping, and digest failures.
- [ ] **Step 2: Migrate code and JSON atomically.** Rename fields, CLI options, case IDs, filenames, and directories; regenerate digests and retain every recorded outcome and the zero-client-result boundary.
- [ ] **Step 3: Run evaluation verification GREEN.** Run the focused suite, `.venv\Scripts\python.exe tools\evaluate.py validate --run-type baseline --run-type pressure --run-type wording`, and `.venv\Scripts\python.exe tools\evaluate.py summary --run-type baseline --run-type pressure --run-type wording --format json`; expect PASS with unchanged outcome counts and zero client passes.
- [ ] **Step 4: Review the Task 4 diff.** Confirm every active and archived record uses the new schema, digests are derived, and no historical result was upgraded.

### M06-T05 — Current-Tree Documentation Migration and Milestone Gate

**Objective:** Finish the breaking migration across maintained documentation and filenames, prove current-tree consistency, and prepare the single M06 commit.
**Requirements:** REQ-TS2C-017, REQ-TS2C-016.

**Files:**
- Modify `README.md`, `CONTEXT.md`, `docs/specs/tracing-spec-to-code-spec.md`, every file under `docs/design/`, and `docs/plans/tracing-spec-to-code-roadmap.md` plus M01 through M06 plan files.
- Rename all 12 maintained records under `docs/changes/` to the same descriptive suffix with IDs `cr01` through `cr12`, then rewrite them in English.
- Create `tests/test_repository_vocabulary.py`; modify any remaining Markdown, JSON, Python, or YAML fixture that fails canonical vocabulary or English documentation checks.

**Interfaces:**
- Add approved `REQ-TS2C-017` to the spec and trace it to M06.
- The vocabulary test scans `git ls-files` current-tree text, rejects superseded workflow tokens and non-English documentation prose, allowlists only the four localized labels, and permits unchanged Git history.
- The completed M06 plan records actual targeted/full verification, exact commit scope, and the milestone commit draft.

- [ ] **Step 1: Add the repository vocabulary test and run RED.** Run `.venv\Scripts\python.exe -m unittest tests.test_repository_vocabulary -v`; expect findings in not-yet-migrated documentation and filenames.
- [ ] **Step 2: Rename and rewrite remaining artifacts.** Translate maintained documents to English, update inbound links and discovery references, add REQ-TS2C-017, and preserve prior decisions and recorded status.
- [ ] **Step 3: Run the full gate.** Expect every command below to PASS:

  ```text
  .venv\Scripts\python.exe -m unittest discover -s tests -v
  .venv\Scripts\python.exe tools\evaluate.py validate --run-type baseline --run-type pressure --run-type wording
  .venv\Scripts\python.exe tools\evaluate.py summary --run-type baseline --run-type pressure --run-type wording --format json
  .venv\Scripts\python.exe skills\tracing-spec-to-code\scripts\tracing_spec_to_code.py validate --repo tests\fixtures\valid-project
  .venv\Scripts\python.exe C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\tracing-spec-to-code
  git -c safe.directory=D:/Project/tracing-spec-to-code diff --check
  ```
- [ ] **Step 4: Verify boundaries and current-tree cleanliness.** Confirm only canonical workflow names, no non-allowlisted Han text in maintained Markdown, 8×2 installer coverage, no invented client PASS, and unchanged Git history.
- [ ] **Step 5: Record evidence and commit once.** Update M06 evidence with actual results, verify staged paths equal its scope, commit with `Milestone`, `Requirements`, and optional `Change-Requests` trailers, then stop without remote operations.

## Acceptance Criteria

1. The tracked current tree uses only the canonical workflow vocabulary and machine contract.
2. No parser, alias, fixture, document, or evaluator preserves the superseded contract.
3. Routine prompts render descriptive English or Simplified Chinese labels from the most recent user message, with English fallback.
4. README files and maintained project documents are English.
5. Change Request identifiers, filenames, JSON fields, evidence, and commit trailers are consistent.
6. Targeted tests, the full suite, repository validation, evaluation integrity, installer coverage, Skill validation, and Git checks pass.
7. External client verification remains user-owned and unclaimed.

## Traceability

| Task | Requirements | Implementation | Tests |
|---|---|---|---|
| `M06-T01` | `REQ-TS2C-017, REQ-TS2C-016` | `skills/tracing-spec-to-code/scripts/tstc/config.py, skills/tracing-spec-to-code/scripts/tstc/artifacts.py, skills/tracing-spec-to-code/scripts/tstc/validation.py` | `tests/test_config.py, tests/test_artifacts.py, tests/test_validation.py` |
| `M06-T02` | `REQ-TS2C-017, REQ-TS2C-016` | `skills/tracing-spec-to-code/scripts/tstc/evidence.py, skills/tracing-spec-to-code/scripts/tstc/precommit.py, skills/tracing-spec-to-code/scripts/tstc/git_checks.py` | `tests/test_evidence.py, tests/test_git_checks.py` |
| `M06-T03` | `REQ-TS2C-017, REQ-TS2C-016` | `skills/tracing-spec-to-code/SKILL.md, skills/tracing-spec-to-code/references/workflow.md, tests/scenarios/m02/change-approval.md` | `tests/test_distribution.py` |
| `M06-T04` | `REQ-TS2C-017, REQ-TS2C-016` | `tools/evaluate.py, evaluation/cases.json, evaluation/evidence/baseline-requirements-confirmation-02.json` | `tests/test_evaluation.py` |
| `M06-T05` | `REQ-TS2C-017, REQ-TS2C-016` | `README.md, CONTEXT.md, docs/specs/tracing-spec-to-code-spec.md, docs/plans/tracing-spec-to-code-roadmap.md, docs/changes/tracing-spec-to-code-cr01-config-filename-templates.md` | `tests/test_repository_vocabulary.py` |

## Evidence and commit

### Task status

| Task | Status | Actual verification |
|---|---|---|
| `M06-T01` | `Completed` | `PASS` |
| `M06-T02` | `Completed` | `PASS` |
| `M06-T03` | `Completed` | `PASS` |
| `M06-T04` | `Completed` | `PASS` |
| `M06-T05` | `Completed` | `PASS` |

- Approved Change Requests: None
- Deviations: the inherited M06 planning files were retained as authorized M06 scope; CR-01 through CR-12 remain historical migration inputs; the external client-verification boundary remains user-owned with zero client PASS records; the Skill validator ran with the user-installed Python runtime because the bundled runtime did not include PyYAML.
- Baseline dirty paths: None

### Verification

| Scope | Command | Expected | Actual | Result |
|---|---|---|---|---|
| Targeted | `python -m unittest tests.test_config tests.test_artifacts tests.test_validation tests.test_cli -v` | All pass | `PASS` | PASS |
| Targeted | `python -m unittest tests.test_evidence tests.test_git_checks -v` | All pass | `PASS` | PASS |
| Targeted | `python -m unittest tests.test_distribution.PackagedPolicyTests tests.test_install_cli -v` | All pass | `PASS` | PASS |
| Targeted | `python -m unittest tests.test_evaluation -v` | All pass | `PASS` | PASS |
| Targeted | `python -m unittest tests.test_repository_vocabulary -v` | All pass | `PASS` | PASS |
| Broader | `python -m unittest discover -s tests -v` | All pass | `PASS` | PASS |
| Evaluation | filtered `tools/evaluate.py validate` | Valid local matrix | `PASS` | PASS |
| Evaluation | filtered `tools/evaluate.py summary --format json` | Stable summary | `PASS` | PASS |
| Fixture | repository validator on `tests/fixtures/valid-project` | No issues | `PASS` | PASS |
| Repository | repository self-validator | No issues | `PASS` | PASS |
| Skill | `quick_validate.py skills/tracing-spec-to-code` | `Skill is valid!` | `PASS` | PASS |
| Diff | `git diff --check` | No errors | `PASS` | PASS |

### Commit scope

| Path | Purpose |
|---|---|
| `README.md` | M06 canonical terminology migration |
| `docs/changes/tracing-spec-to-code-cp01-config-filename-templates.md` | Removed superseded record path |
| `docs/changes/tracing-spec-to-code-cp02-missing-reference-code.md` | Removed superseded record path |
| `docs/changes/tracing-spec-to-code-cp03-current-milestone-reference-scope.md` | Removed superseded record path |
| `docs/changes/tracing-spec-to-code-cp04-inter-milestone-awaiting-state.md` | Removed superseded record path |
| `docs/changes/tracing-spec-to-code-cp05-defer-npx-distribution.md` | Removed superseded record path |
| `docs/changes/tracing-spec-to-code-cp06-safe-publication-semantics.md` | Removed superseded record path |
| `docs/changes/tracing-spec-to-code-cp07-ownership-aware-staging.md` | Removed superseded record path |
| `docs/changes/tracing-spec-to-code-cp08-cooperative-filesystem-threat-model.md` | Removed superseded record path |
| `docs/changes/tracing-spec-to-code-cp09-reproducible-evaluation-reruns.md` | Removed superseded record path |
| `docs/changes/tracing-spec-to-code-cp10-authority-channel-wording-rebuild.md` | Removed superseded record path |
| `docs/changes/tracing-spec-to-code-cp11-user-owned-client-verification.md` | Removed superseded record path |
| `docs/changes/tracing-spec-to-code-cp12-administrative-completion-waiver.md` | Removed superseded record path |
| `docs/design/2026-07-29-tracing-spec-to-code-design.md` | M06 canonical terminology migration |
| `docs/design/2026-07-30-tracing-spec-to-code-m03-evidence-commit-design.md` | M06 canonical terminology migration |
| `docs/design/2026-07-30-tracing-spec-to-code-m04-client-distribution-design.md` | M06 canonical terminology migration |
| `docs/design/2026-07-30-tracing-spec-to-code-m05-evaluation-release-design.md` | M06 canonical terminology migration |
| `docs/plans/tracing-spec-to-code-m01-artifact-contracts.md` | M06 canonical terminology migration |
| `docs/plans/tracing-spec-to-code-m02-workflow-core.md` | M06 canonical terminology migration |
| `docs/plans/tracing-spec-to-code-m03-evidence-commit.md` | M06 canonical terminology migration |
| `docs/plans/tracing-spec-to-code-m04-client-distribution.md` | M06 canonical terminology migration |
| `docs/plans/tracing-spec-to-code-m05-evaluation-release.md` | M06 canonical terminology migration |
| `docs/plans/tracing-spec-to-code-roadmap.md` | M06 canonical terminology migration |
| `docs/specs/tracing-spec-to-code-spec.md` | M06 canonical terminology migration |
| `evaluation/README.md` | M06 canonical terminology migration |
| `evaluation/archive/cp09/baseline-context-01.json` | Removed superseded archive path |
| `evaluation/archive/cp09/baseline-gate-01.json` | Removed superseded archive path |
| `evaluation/archive/cp09/baseline-verification-git-01.json` | Removed superseded archive path |
| `evaluation/archive/cp09/loaded-context-01.json` | Removed superseded archive path |
| `evaluation/archive/cp09/loaded-gate-01.json` | Removed superseded archive path |
| `evaluation/archive/cp09/loaded-verification-git-01.json` | Removed superseded archive path |
| `evaluation/archive/cp09/wording-commit-boundary-01.json` | Removed superseded archive path |
| `evaluation/archive/cp09/wording-commit-boundary-02.json` | Removed superseded archive path |
| `evaluation/archive/cp09/wording-commit-boundary-03.json` | Removed superseded archive path |
| `evaluation/archive/cp09/wording-commit-boundary-04.json` | Removed superseded archive path |
| `evaluation/archive/cp09/wording-commit-boundary-05.json` | Removed superseded archive path |
| `evaluation/archive/cp09/wording-semantic-scope-01.json` | Removed superseded archive path |
| `evaluation/archive/cp09/wording-semantic-scope-02.json` | Removed superseded archive path |
| `evaluation/archive/cp09/wording-semantic-scope-03.json` | Removed superseded archive path |
| `evaluation/archive/cp09/wording-semantic-scope-04.json` | Removed superseded archive path |
| `evaluation/archive/cp09/wording-semantic-scope-05.json` | Removed superseded archive path |
| `evaluation/cases.json` | M06 canonical terminology migration |
| `evaluation/evidence/baseline-context-02.json` | M06 canonical terminology migration |
| `evaluation/evidence/baseline-gate-02.json` | M06 canonical terminology migration |
| `evaluation/evidence/baseline-verification-git-02.json` | M06 canonical terminology migration |
| `evaluation/evidence/loaded-context-02.json` | M06 canonical terminology migration |
| `evaluation/evidence/loaded-gate-02.json` | M06 canonical terminology migration |
| `evaluation/evidence/loaded-verification-git-02.json` | M06 canonical terminology migration |
| `evaluation/evidence/wording-commit-boundary-06.json` | M06 canonical terminology migration |
| `evaluation/evidence/wording-commit-boundary-07.json` | M06 canonical terminology migration |
| `evaluation/evidence/wording-commit-boundary-08.json` | M06 canonical terminology migration |
| `evaluation/evidence/wording-commit-boundary-09.json` | M06 canonical terminology migration |
| `evaluation/evidence/wording-commit-boundary-10.json` | M06 canonical terminology migration |
| `evaluation/evidence/wording-commit-boundary-11.json` | M06 canonical terminology migration |
| `evaluation/evidence/wording-commit-boundary-12.json` | M06 canonical terminology migration |
| `evaluation/evidence/wording-commit-boundary-13.json` | M06 canonical terminology migration |
| `evaluation/evidence/wording-commit-boundary-14.json` | M06 canonical terminology migration |
| `evaluation/evidence/wording-commit-boundary-15.json` | M06 canonical terminology migration |
| `evaluation/evidence/wording-semantic-scope-06.json` | M06 canonical terminology migration |
| `evaluation/evidence/wording-semantic-scope-07.json` | M06 canonical terminology migration |
| `evaluation/evidence/wording-semantic-scope-08.json` | M06 canonical terminology migration |
| `evaluation/evidence/wording-semantic-scope-09.json` | M06 canonical terminology migration |
| `evaluation/evidence/wording-semantic-scope-10.json` | M06 canonical terminology migration |
| `skills/tracing-spec-to-code/SKILL.md` | M06 canonical terminology migration |
| `skills/tracing-spec-to-code/assets/templates/change-proposal.md` | Removed superseded template path |
| `skills/tracing-spec-to-code/assets/templates/config.json` | M06 canonical terminology migration |
| `skills/tracing-spec-to-code/assets/templates/milestone-plan.md` | M06 canonical terminology migration |
| `skills/tracing-spec-to-code/assets/templates/roadmap.md` | M06 canonical terminology migration |
| `skills/tracing-spec-to-code/assets/templates/spec.md` | M06 canonical terminology migration |
| `skills/tracing-spec-to-code/references/milestone-commit.md` | M06 canonical terminology migration |
| `skills/tracing-spec-to-code/references/task-execution.md` | M06 canonical terminology migration |
| `skills/tracing-spec-to-code/references/workflow.md` | M06 canonical terminology migration |
| `skills/tracing-spec-to-code/scripts/tstc/artifacts.py` | M06 canonical terminology migration |
| `skills/tracing-spec-to-code/scripts/tstc/config.py` | M06 canonical terminology migration |
| `skills/tracing-spec-to-code/scripts/tstc/evidence.py` | M06 canonical terminology migration |
| `skills/tracing-spec-to-code/scripts/tstc/git_checks.py` | M06 canonical terminology migration |
| `skills/tracing-spec-to-code/scripts/tstc/precommit.py` | M06 canonical terminology migration |
| `skills/tracing-spec-to-code/scripts/tstc/validation.py` | M06 canonical terminology migration |
| `tests/fixtures/duplicate-requirement/docs/plans/sample-m01-contracts.md` | M06 canonical terminology migration |
| `tests/fixtures/duplicate-requirement/docs/plans/sample-roadmap.md` | M06 canonical terminology migration |
| `tests/fixtures/duplicate-requirement/docs/specs/sample-spec.md` | M06 canonical terminology migration |
| `tests/fixtures/unknown-reference/docs/plans/sample-m01-contracts.md` | M06 canonical terminology migration |
| `tests/fixtures/unknown-reference/docs/plans/sample-roadmap.md` | M06 canonical terminology migration |
| `tests/fixtures/unknown-reference/docs/specs/sample-spec.md` | M06 canonical terminology migration |
| `tests/fixtures/valid-project/docs/plans/sample-m01-contracts.md` | M06 canonical terminology migration |
| `tests/fixtures/valid-project/docs/plans/sample-roadmap.md` | M06 canonical terminology migration |
| `tests/fixtures/valid-project/docs/specs/sample-spec.md` | M06 canonical terminology migration |
| `tests/scenarios/m02/next-milestone.md` | M06 canonical terminology migration |
| `tests/scenarios/m03/scope-pressure.md` | M06 canonical terminology migration |
| `tests/test_artifacts.py` | M06 canonical terminology migration |
| `tests/test_cli.py` | M06 canonical terminology migration |
| `tests/test_config.py` | M06 canonical terminology migration |
| `tests/test_distribution.py` | M06 canonical terminology migration |
| `tests/test_evaluation.py` | M06 canonical terminology migration |
| `tests/test_evidence.py` | M06 canonical terminology migration |
| `tests/test_git_checks.py` | M06 canonical terminology migration |
| `tests/test_validation.py` | M06 canonical terminology migration |
| `tools/evaluate.py` | M06 canonical terminology migration |
| `CONTEXT.md` | M06 canonical terminology migration |
| `docs/changes/tracing-spec-to-code-cr01-config-filename-templates.md` | M06 canonical terminology migration |
| `docs/changes/tracing-spec-to-code-cr02-missing-reference-code.md` | M06 canonical terminology migration |
| `docs/changes/tracing-spec-to-code-cr03-current-milestone-reference-scope.md` | M06 canonical terminology migration |
| `docs/changes/tracing-spec-to-code-cr04-inter-milestone-awaiting-state.md` | M06 canonical terminology migration |
| `docs/changes/tracing-spec-to-code-cr05-defer-npx-distribution.md` | M06 canonical terminology migration |
| `docs/changes/tracing-spec-to-code-cr06-safe-publication-semantics.md` | M06 canonical terminology migration |
| `docs/changes/tracing-spec-to-code-cr07-ownership-aware-staging.md` | M06 canonical terminology migration |
| `docs/changes/tracing-spec-to-code-cr08-cooperative-filesystem-threat-model.md` | M06 canonical terminology migration |
| `docs/changes/tracing-spec-to-code-cr09-reproducible-evaluation-reruns.md` | M06 canonical terminology migration |
| `docs/changes/tracing-spec-to-code-cr10-authority-channel-wording-rebuild.md` | M06 canonical terminology migration |
| `docs/changes/tracing-spec-to-code-cr11-user-owned-client-verification.md` | M06 canonical terminology migration |
| `docs/changes/tracing-spec-to-code-cr12-administrative-completion-waiver.md` | M06 canonical terminology migration |
| `docs/plans/tracing-spec-to-code-m06-readable-localized-terminology.md` | M06 canonical terminology migration |
| `evaluation/archive/cr09/baseline-context-01.json` | M06 canonical terminology migration |
| `evaluation/archive/cr09/baseline-requirements-confirmation-01.json` | M06 canonical terminology migration |
| `evaluation/archive/cr09/baseline-verification-git-01.json` | M06 canonical terminology migration |
| `evaluation/archive/cr09/loaded-context-01.json` | M06 canonical terminology migration |
| `evaluation/archive/cr09/loaded-requirements-confirmation-01.json` | M06 canonical terminology migration |
| `evaluation/archive/cr09/loaded-verification-git-01.json` | M06 canonical terminology migration |
| `evaluation/archive/cr09/wording-commit-boundary-01.json` | M06 canonical terminology migration |
| `evaluation/archive/cr09/wording-commit-boundary-02.json` | M06 canonical terminology migration |
| `evaluation/archive/cr09/wording-commit-boundary-03.json` | M06 canonical terminology migration |
| `evaluation/archive/cr09/wording-commit-boundary-04.json` | M06 canonical terminology migration |
| `evaluation/archive/cr09/wording-commit-boundary-05.json` | M06 canonical terminology migration |
| `evaluation/archive/cr09/wording-semantic-scope-01.json` | M06 canonical terminology migration |
| `evaluation/archive/cr09/wording-semantic-scope-02.json` | M06 canonical terminology migration |
| `evaluation/archive/cr09/wording-semantic-scope-03.json` | M06 canonical terminology migration |
| `evaluation/archive/cr09/wording-semantic-scope-04.json` | M06 canonical terminology migration |
| `evaluation/archive/cr09/wording-semantic-scope-05.json` | M06 canonical terminology migration |
| `evaluation/evidence/baseline-requirements-confirmation-02.json` | M06 canonical terminology migration |
| `evaluation/evidence/loaded-requirements-confirmation-02.json` | M06 canonical terminology migration |
| `skills/tracing-spec-to-code/assets/templates/change-request.md` | M06 canonical terminology migration |
| `tests/fixtures/valid-project/docs/changes/sample-cr01-traceability.md` | M06 canonical terminology migration |
| `tests/fixtures/valid-project/docs/changes/sample-cp01-traceability.md` | Removed superseded fixture path |
| `tests/scenarios/m02/change-approval.md` | M06 canonical terminology migration |
| `tests/scenarios/m02/gate-delta.md` | Removed superseded scenario path |
| `tests/test_repository_vocabulary.py` | M06 canonical terminology migration |

### Commit draft

```text
feat(terminology): migrate workflow vocabulary and localization

Milestone: M06 Readable localized terminology
Requirements: REQ-TS2C-017, REQ-TS2C-016
```
