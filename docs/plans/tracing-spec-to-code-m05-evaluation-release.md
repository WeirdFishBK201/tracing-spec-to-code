# tracing-spec-to-code M05 Evaluation and Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

- Status: Approved — In Progress
- Milestone: M05 — Evaluation and release
- Spec: `docs/specs/tracing-spec-to-code-spec.md`
- Roadmap: `docs/plans/tracing-spec-to-code-roadmap.md`
- Design: `docs/design/2026-07-30-tracing-spec-to-code-m05-evaluation-release-design.md`
- Requirements: REQ-TS2C-015, REQ-TS2C-016
- Gate P: Approved on 2026-07-30

**Goal:** Produce reproducible Codex behavior, eight-client compatibility, and staged-candidate clean-clone evidence without publishing or mutating a remote.

**Architecture:** Reuse `tools/clients.json`, add one versioned case file and one standard-library evaluation CLI, and store one immutable JSON file per real run. Generate summaries from evidence on demand; client actions follow a uniform runbook and remain manual unless a later Gate Δ approves an adapter.

**Tech Stack:** Python 3.10+ standard library (`argparse`, `dataclasses`, `datetime`, `json`, `pathlib`, `re`, `secrets`, `unittest`), existing local Git, and explicitly approved client CLIs/GUI sessions.

## Global Constraints

- Implement only M05; `npx`, remote-source installation, native-handle hardening, tag, Release, PR, merge and push remain out of scope.
- Do not install, log in, access the network, or invoke an external client without a separate just-in-time approval.
- Never write a real home/client root; use isolated project roots and synthetic repository fixtures.
- Store only reviewed evidence with no secrets, real-home paths, repository-external paths, `VGCCoach2`, or legacy `agentic-workflow` content.
- Reuse `tools/clients.json`; do not create another client registry, adapter framework, or persisted summary.
- Use TDD for deterministic code. Create one M05 milestone commit only after every gate passes; do not make per-task implementation commits or push.

## File map and contracts

- Create `evaluation/cases.json`: three paired baseline/pressure scenarios, two wording variants, and Level 1/2 case templates.
- Create `evaluation/README.md`: exact prompt execution, rationale review, client runbook, evidence recording, and approval boundaries.
- Create `tools/evaluate.py`: `prepare`, `record`, `validate`, and `summary` commands.
- Create `tests/test_evaluation.py`: case/evidence/CLI/summary and candidate-snapshot integration tests.
- Create the 24 exact JSON files listed under Commit scope; no optional rerun/CP file joins scope without Gate Δ.
- Modify `README.md`, this plan, and the roadmap for user commands, actual evidence, final status, and commit facts.

Library contracts in `tools/evaluate.py`:

```text
CaseSpec(id, scenario_id, run_type, prompt, skill_loaded, expected_decision, pressures, variant_group)
EvidenceRecord(schema_version, run_id, case_id, client_id, skill_loaded, client_version, model, config, recorded_at, prompt, actual_decision, verbatim_rationale, outcome, rationale_review, supersedes_run_ids)
EvaluationSummary(baseline_observed, pressure_passed, wording_groups, level1_passed, level2_passed, blocked_runs, failed_runs, open_rationales)
EvaluationError(code, message, path=None)
load_cases(path: Path) -> tuple[CaseSpec, ...]
load_evidence(path: Path) -> EvidenceRecord
record_evidence(input_path: Path, evidence_dir: Path, cases_path: Path, registry_path: Path) -> Path
validate_suite(cases_path: Path, registry_path: Path, evidence_dir: Path) -> EvaluationSummary
```

Stable policy codes: `CASE_INVALID`, `RUN_EXISTS`, `EVIDENCE_INVALID`, `SENSITIVE_CONTENT`, `EVALUATION_INCOMPLETE`, `EVALUATION_FAILED`. CLI returns `0` for a successful requested operation, `1` for policy failure/blocker, and `2` for invalid arguments or unexpected runtime failure.

## Tasks

### M05-T01 — Minimal evaluation contract and CLI

**Objective:** Produce a strict offline case/evidence validator and CLI without invoking any real client.

**Requirements:** REQ-TS2C-015, REQ-TS2C-016.

**Files:** Create `evaluation/cases.json`, `evaluation/README.md`, `tools/evaluate.py`, `tests/test_evaluation.py`.

**Consumes:** Approved M05 design, `tools/clients.json`, and `tools.distribution.load_registry`.

**Produces:** The contracts and stable codes above plus deterministic human/JSON summaries.

- [ ] Write focused tests for unknown/duplicate fields, scenario pairing, controlled three-pressure excerpts, run IDs, no-overwrite recording, expected decisions, blocked runs, 5x config consistency, rationale closure, client levels, sensitive content, stable summaries, and CLI exits.
- [ ] Run `python -m unittest tests.test_evaluation.CaseTests tests.test_evaluation.EvidenceTests tests.test_evaluation.CliTests -v`; confirm RED is caused by missing `tools.evaluate`/case assets rather than malformed tests.
- [ ] Implement the minimal single-file CLI and approved cases; `prepare` emits a reviewed template, `record` validates before exclusive write, and `validate`/`summary` never mutate evidence.
- [ ] Re-run the targeted command and `python -m unittest tests.test_evaluation -v`; require PASS, then obtain independent spec and code-quality reviews before real runs.

### M05-T02 — Codex baseline, pressure, and wording evidence

**Objective:** Record the approved 3 baseline + 3 loaded pressure + 10 wording runs with reviewable choices and verbatim rationales.

**Requirements:** REQ-TS2C-015, REQ-TS2C-016.

**Files:** Create the 16 Codex evidence files named under Commit scope; modify `evaluation/README.md` only when recording exact approved execution commands.

**Consumes:** T01 CLI/cases; fresh Codex sessions with fixed client/model/version/config for each 5x group.

**Produces:** Three scenario pairs, two `5/5 PASS` wording groups, and persisted rationale dispositions.

- [ ] Use `prepare` for the three baseline case IDs, run each in a fresh Codex session without loading the Skill after just-in-time approval, review rationale, then `record` the three `baseline-*.json` files as `observed` or `blocked`.
- [ ] Repeat the paired cases with the Skill loaded; record `loaded-*.json` and require all three actual decisions to match their cases.
- [ ] Run `wording-semantic-scope` and `wording-commit-boundary` five times each with identical recorded configuration; record runs `01`–`05`.
- [ ] Review every rationale. Any new rationale stops T02 for an approved change proposal and superseding reruns; otherwise run `python tools/evaluate.py validate --run-type baseline --run-type pressure --run-type wording` and require `3 observed, 3/3 pressure PASS, 5/5 + 5/5 wording PASS`.

### M05-T03 — Eight-client discovery and smoke evidence

**Objective:** Complete real Level 1 discovery/minimal-flow and Level 2 structure/smoke evidence in isolated project roots.

**Requirements:** REQ-TS2C-015, REQ-TS2C-016.

**Files:** Create the 8 `client-*.json` files under Commit scope; modify `evaluation/README.md` with exact version/help-derived commands.

**Consumes:** T01 CLI, M04 installer, canonical registry, and separately approved client installation/login/network operations.

**Produces:** Five Level 1 passing records and three Level 2 passing records with real observable output.

- [ ] Capture each client’s installed version and local help before defining its command; request separate approval before installing, logging in, networking, or launching it. Record an unavailable prerequisite as `blocked`, never as pass.
- [ ] For Codex, Claude Code, GitHub Copilot CLI, Antigravity and Gemini CLI, install into an isolated project root with `python tools/install.py --client <id> --scope project --project-root <root>`, prove Skill discovery, and run the minimal valid-fixture validator flow.
- [ ] For Cursor, Windsurf and Cline, install into an isolated project root, verify the complete canonical structure, and execute the capability-appropriate smoke step documented from actual help/UI.
- [ ] Review and record all eight outputs, then run `python tools/evaluate.py validate --run-type level1 --run-type level2`; require `5/5 Level 1 PASS, 3/3 Level 2 PASS`, followed by independent spec and quality reviews.

### M05-T04 — Release-ready candidate, documentation, and milestone commit

**Objective:** Prove the exact staged candidate is reproducible from a clean local clone and create one verified M05 commit.

**Requirements:** REQ-TS2C-015, REQ-TS2C-016.

**Files:** Modify `README.md`, this plan, and the roadmap; stage the exact Commit scope below.

**Consumes:** T01–T03 passing evidence, design acceptance criteria, and M03 exact-scope/precommit policy.

**Produces:** Completed evidence tables, candidate tree hash, clean-clone results, final matching commit, and clean local status.

- [ ] Document evaluation commands and boundaries; record actual task/review/evidence results, four platform skips if unchanged, baseline dirty paths, exact scope, and commit draft in this plan.
- [ ] Run the targeted evaluation suite, full repository suite, fixture/repository/Skill validators, installer matrix, Python 3.10 grammar, isolation scan, and `git diff --check`; require all applicable checks PASS.
- [ ] Obtain final independent spec and code-quality reviews, update all task/review rows to PASS, stage only the exact Commit scope with literal pathspecs, run `precommit --repo . --plan docs/plans/tracing-spec-to-code-m05-evaluation-release.md --format json`, and record `git write-tree` as the final candidate hash.
- [ ] Export that index with `git checkout-index --all --prefix=<candidate>/source/`; configure the temp repo identity plus `core.autocrlf=false`, make a throwaway commit, require its `HEAD^{tree}` to equal the candidate hash, then `git clone --local` it and rerun tests, validators, installer matrix, README help commands, metadata checks, and evaluation summary.
- [ ] Create one local `feat(evaluation): add reproducible release evidence` commit; confirm `HEAD^{tree}` equals the candidate tree hash, status is clean, and no remote mutation occurred. Stop without push.

## Milestone verification

```text
python -m unittest tests.test_evaluation -v
python -m unittest discover -s tests -v
python tools/evaluate.py validate
python tools/evaluate.py summary --format json
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo tests/fixtures/valid-project
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo . --format json
python C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tracing-spec-to-code
rg -n "VGCCoach2|agentic-workflow" README.md skills/tracing-spec-to-code tools tests evaluation
git diff --check
```

Expected: deterministic tests/validators PASS; Codex `3 observed + 3/3 + 5/5 + 5/5`; clients `5/5 + 3/3`; isolation has no matches; candidate clean clone matches the staged/final tree.

## Traceability

| Task | Requirements | Implementation/evidence | Verification |
|---|---|---|---|
| `M05-T01` | `REQ-TS2C-015, REQ-TS2C-016` | `evaluation/cases.json, evaluation/README.md, tools/evaluate.py` | `tests/test_evaluation.py` |
| `M05-T02` | `REQ-TS2C-015, REQ-TS2C-016` | `evaluation/evidence/baseline-*.json, loaded-*.json, wording-*.json` | `evaluate.py validate/summary` |
| `M05-T03` | `REQ-TS2C-015, REQ-TS2C-016` | `evaluation/evidence/client-*.json, evaluation/README.md` | `evaluate.py validate/summary` |
| `M05-T04` | `REQ-TS2C-015, REQ-TS2C-016` | `README.md, M05 plan, roadmap` | full suite, candidate clean clone, precommit |

## Evidence and commit

### Task status

| Task | Status | Actual verification |
|---|---|---|
| `M05-T01` | `Pending` | `Pending` |
| `M05-T02` | `Pending` | `Pending` |
| `M05-T03` | `Pending` | `Pending` |
| `M05-T04` | `Pending` | `Pending` |

- Approved proposals: None
- Deviations: None
- Baseline dirty paths: None

### Verification

| Scope | Command | Expected | Actual | Result |
|---|---|---|---|---|
| Targeted | `python -m unittest tests.test_evaluation -v` | All pass | `Pending` | `PENDING` |
| Broader | `python -m unittest discover -s tests -v` | All pass | `Pending` | `PENDING` |
| Evaluation | `evaluate.py validate/summary` | Complete approved matrix | `Pending` | `PENDING` |
| Clients | `Level 1 discovery + Level 2 smoke` | `5/5 + 3/3` | `Pending` | `PENDING` |
| Candidate | `staged candidate clean-clone gate` | Full release-ready pass | `Pending` | `PENDING` |
| Reviews | `independent spec and code-quality reviews` | No blockers | `Pending` | `PENDING` |

### Commit scope

| Path | Purpose |
|---|---|
| `README.md` | Document evaluation and release-ready commands |
| `evaluation/README.md` | Define the approved execution/runbook boundary |
| `evaluation/cases.json` | Define paired scenarios and client case templates |
| `tools/evaluate.py` | Implement prepare/record/validate/summary |
| `tests/test_evaluation.py` | Verify deterministic evaluation contracts |
| `docs/plans/tracing-spec-to-code-m05-evaluation-release.md` | Record M05 plan, actual evidence, and commit facts |
| `docs/plans/tracing-spec-to-code-roadmap.md` | Record final M05 delivery state |
| `evaluation/evidence/baseline-gate-01.json` | Record unloaded gate baseline |
| `evaluation/evidence/baseline-context-01.json` | Record unloaded context baseline |
| `evaluation/evidence/baseline-verification-git-01.json` | Record unloaded verification/Git baseline |
| `evaluation/evidence/loaded-gate-01.json` | Record loaded gate pressure result |
| `evaluation/evidence/loaded-context-01.json` | Record loaded context pressure result |
| `evaluation/evidence/loaded-verification-git-01.json` | Record loaded verification/Git result |
| `evaluation/evidence/wording-semantic-scope-01.json` | Record semantic-scope wording run 1 |
| `evaluation/evidence/wording-semantic-scope-02.json` | Record semantic-scope wording run 2 |
| `evaluation/evidence/wording-semantic-scope-03.json` | Record semantic-scope wording run 3 |
| `evaluation/evidence/wording-semantic-scope-04.json` | Record semantic-scope wording run 4 |
| `evaluation/evidence/wording-semantic-scope-05.json` | Record semantic-scope wording run 5 |
| `evaluation/evidence/wording-commit-boundary-01.json` | Record commit-boundary wording run 1 |
| `evaluation/evidence/wording-commit-boundary-02.json` | Record commit-boundary wording run 2 |
| `evaluation/evidence/wording-commit-boundary-03.json` | Record commit-boundary wording run 3 |
| `evaluation/evidence/wording-commit-boundary-04.json` | Record commit-boundary wording run 4 |
| `evaluation/evidence/wording-commit-boundary-05.json` | Record commit-boundary wording run 5 |
| `evaluation/evidence/client-codex-01.json` | Record Codex Level 1 result |
| `evaluation/evidence/client-claude-code-01.json` | Record Claude Code Level 1 result |
| `evaluation/evidence/client-github-copilot-01.json` | Record GitHub Copilot CLI Level 1 result |
| `evaluation/evidence/client-antigravity-01.json` | Record Antigravity Level 1 result |
| `evaluation/evidence/client-gemini-cli-01.json` | Record Gemini CLI Level 1 result |
| `evaluation/evidence/client-cursor-01.json` | Record Cursor Level 2 result |
| `evaluation/evidence/client-windsurf-01.json` | Record Windsurf Level 2 result |
| `evaluation/evidence/client-cline-01.json` | Record Cline Level 2 result |

Blocked attempts may add immutable `blocked-<base-run-id>-NN.json` evidence and must be expanded into this exact table before staging. Any CP or superseding run must first update this plan through Gate Δ. Ranges and globs are never passed to Git or precommit.

### Commit draft

```text
feat(evaluation): add reproducible release evidence

Milestone: M05 Evaluation and release
Requirements: REQ-TS2C-015, REQ-TS2C-016
```
