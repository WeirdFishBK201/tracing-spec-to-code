# tracing-spec-to-code M03 Evidence and Commit Plan

> **For agentic workers:** Execute only one task at a time with a fresh bounded context packet and independent spec/quality review at each checkpoint.

- Status: Completed
- Milestone: M03 — Evidence and commit
- Spec: `docs/specs/tracing-spec-to-code-spec.md`
- Roadmap: `docs/plans/tracing-spec-to-code-roadmap.md`
- Design: `docs/design/2026-07-30-tracing-spec-to-code-m03-evidence-commit-design.md`
- Requirements: REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016
- Implementation approval: Approved on 2026-07-30

## Goal

The approved record retains the documented decision and supporting evidence.

## Observable outcome

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

## Non-goals

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

## Architecture and contracts

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

```text
ValidationIssue(code: str, path: Path, line: int, message: str)
EvidenceRecord(plan_path, milestone_id, traceability, task_statuses,
               verifications, approved_requests, deviations,
               baseline_dirty_paths, commit_scope, commit_message)
parse_evidence(repo_root: Path, plan_path: Path) -> EvidenceRecord
validate_evidence(record: EvidenceRecord, known_plan, approved_requests) -> list[ValidationIssue]
get_staged_paths(repo_root: Path) -> tuple[Path, ...]
validate_staged_scope(record: EvidenceRecord, staged_paths: tuple[Path, ...]) -> list[ValidationIssue]
validate_commit_message(record: EvidenceRecord) -> list[ValidationIssue]
validate_precommit(repo_root: Path, plan_path: Path, config_path: Path | None = None) -> list[ValidationIssue]
```

CLI contract：

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py precommit \
  --repo . \
  --plan docs/plans/tracing-spec-to-code-m03-evidence-commit.md \
  --format json
```

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

| Code | Trigger |
|---|---|
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |

## Planned files

The approved record retains the documented decision and supporting evidence.

## Tasks

### M03-T01 — Deterministic evidence contract

The approved record retains the documented decision and supporting evidence.

**Requirements:** REQ-TS2C-010, REQ-TS2C-016

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.

### M03-T02 — Read-only precommit and staged-scope checks

The approved record retains the documented decision and supporting evidence.

**Requirements:** REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.

### M03-T03 — Skill commit orchestration and milestone delivery

The approved record retains the documented decision and supporting evidence.

**Requirements:** REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.

## Milestone verification

```text
python -m unittest tests.test_evidence tests.test_git_checks tests.test_cli tests.test_validation -v
python -m unittest discover -s tests -v
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo tests/fixtures/valid-project
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo . --format json
python C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tracing-spec-to-code
rg -n "VGCCoach2|agentic-workflow" README.md skills/tracing-spec-to-code tests
git diff --check
git status --short
```

The approved record retains the documented decision and supporting evidence.

## Traceability

| Task | Requirements | Implementation | Tests |
|---|---|---|---|
| `M03-T01` | `REQ-TS2C-010, REQ-TS2C-016` | `skills/tracing-spec-to-code/scripts/tstc/issues.py, skills/tracing-spec-to-code/scripts/tstc/evidence.py, skills/tracing-spec-to-code/scripts/tstc/validation.py, skills/tracing-spec-to-code/assets/templates/milestone-plan.md` | `tests/test_evidence.py` |
| `M03-T02` | `REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016` | `skills/tracing-spec-to-code/scripts/tstc/git_checks.py, skills/tracing-spec-to-code/scripts/tstc/precommit.py, skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py` | `tests/test_git_checks.py, tests/test_cli.py` |
| `M03-T03` | `REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016` | `skills/tracing-spec-to-code/references/milestone-commit.md, skills/tracing-spec-to-code/SKILL.md, skills/tracing-spec-to-code/references/task-execution.md, README.md, skills/tracing-spec-to-code/agents/openai.yaml` | `tests/scenarios/m03/scope-pressure.md, tests/scenarios/m03/verification-failure.md, tests/scenarios/m03/git-failure.md` |

## Evidence and commit

### Task status

| Task | Status | Actual verification |
|---|---|---|
| `M03-T01` | `Completed` | `58/58 PASS` |
| `M03-T02` | `Completed` | `96/96 PASS` |
| `M03-T03` | `Completed` | `fresh-agents: PASS` |

- Approved requests: None
- Deviations: None
- Baseline dirty paths: None

### Verification

| Scope | Command | Expected | Actual | Result |
|---|---|---|---|---|
| Targeted | `python -m unittest tests.test_git_checks tests.test_cli tests.test_evidence tests.test_validation` | All pass | `97/97 PASS` | `PASS` |
| Broader | `python -m unittest discover -s tests` | All pass | `117/117 PASS` | `PASS` |
| Skill | `quick_validate.py skills/tracing-spec-to-code` | Valid Skill | `PASS` | `PASS` |
| Fixture | `tracing_spec_to_code.py validate --repo tests/fixtures/valid-project` | No issues | `PASS` | `PASS` |
| Repository | `tracing_spec_to_code.py validate --repo . --format json` | Valid JSON | `PASS` | `PASS` |
| Isolation | `rg -n "VGCCoach2|agentic-workflow" README.md skills/tracing-spec-to-code tests` | No matches | `PASS` | `PASS` |
| Behavior | `fresh-agent M03 pressure scenarios` | Exact success and safe failures | `3/3 PASS` | `PASS` |
| Diff | `git diff --check` | No errors | `PASS` | `PASS` |

### Commit scope

| Path | Purpose |
|---|---|
| `README.md` | Document M03 usage, codes, and boundaries |
| `docs/plans/tracing-spec-to-code-m03-evidence-commit.md` | Persist milestone evidence and commit facts |
| `docs/plans/tracing-spec-to-code-roadmap.md` | Persist approved current milestone state |
| `skills/tracing-spec-to-code/SKILL.md` | Route milestone delivery to commit policy |
| `skills/tracing-spec-to-code/agents/openai.yaml` | Update M03 discovery prompt |
| `skills/tracing-spec-to-code/assets/templates/milestone-plan.md` | Provide canonical evidence tables |
| `skills/tracing-spec-to-code/references/milestone-commit.md` | Define exact safe commit sequence |
| `skills/tracing-spec-to-code/references/task-execution.md` | Invoke milestone commit policy |
| `skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py` | Expose read-only precommit CLI |
| `skills/tracing-spec-to-code/scripts/tstc/evidence.py` | Parse and validate milestone evidence |
| `skills/tracing-spec-to-code/scripts/tstc/git_checks.py` | Inspect staged state and commit draft |
| `skills/tracing-spec-to-code/scripts/tstc/issues.py` | Share stable validation issues |
| `skills/tracing-spec-to-code/scripts/tstc/precommit.py` | Compose repository/evidence/Git checks |
| `skills/tracing-spec-to-code/scripts/tstc/validation.py` | Reuse shared issue sorting |
| `tests/scenarios/m03/git-failure.md` | Pressure-test Git failure behavior |
| `tests/scenarios/m03/scope-pressure.md` | Pressure-test exact scope behavior |
| `tests/scenarios/m03/verification-failure.md` | Pressure-test failed verification behavior |
| `tests/test_cli.py` | Verify precommit CLI exits and schema |
| `tests/test_evidence.py` | Verify canonical evidence behavior |
| `tests/test_git_checks.py` | Verify read-only Git boundaries |

### Commit draft

```text
feat(evidence): enforce safe milestone commits

Milestone: M03 Evidence and commit
Requirements: REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016
```
