# tracing-spec-to-code M02 Workflow Core Plan

- Status: Completed
- Milestone: M02 — Workflow core
- Spec: `docs/specs/tracing-spec-to-code-spec.md`
- Roadmap: `docs/plans/tracing-spec-to-code-roadmap.md`
- Design: `docs/design/2026-07-29-tracing-spec-to-code-design.md`
- Requirements: REQ-TS2C-003, REQ-TS2C-004, REQ-TS2C-005, REQ-TS2C-006, REQ-TS2C-007, REQ-TS2C-008, REQ-TS2C-009, REQ-TS2C-016
- Implementation approval: Approved on 2026-07-30

## Goal

The approved record retains the documented decision and supporting evidence.

## Observable outcome

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

## Non-goals

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

## Architecture

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.

## Global constraints

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

## Planned files

| Path | Responsibility |
|---|---|
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| `tests/scenarios/m02/*.md` | Change approval、future plan、context/test pressure scenarios |
| Approved record | The documented decision and supporting evidence are retained. |

## Contracts

The approved record retains the documented decision and supporting evidence.

- `GateRef(name: str, status: str, line: int)`
- `ArtifactRef.status: str | None`
- `ArtifactRef.status_line: int`
- `ArtifactRef.gate_refs: tuple[GateRef, ...]`
- `ArtifactRef.current_milestone_id: str | None`

The approved record retains the documented decision and supporting evidence.

| Code | Deterministic trigger |
|---|---|
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |

The approved record retains the documented decision and supporting evidence.

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

## Tasks

### M02-T01 — Workflow metadata and deterministic blockers

The approved record retains the documented decision and supporting evidence.

**Requirements:** REQ-TS2C-004, REQ-TS2C-005, REQ-TS2C-008, REQ-TS2C-016

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.

### M02-T02 — Skill policy, context budget, and adaptive testing

The approved record retains the documented decision and supporting evidence.

**Requirements:** REQ-TS2C-003, REQ-TS2C-005, REQ-TS2C-006, REQ-TS2C-007, REQ-TS2C-008, REQ-TS2C-009, REQ-TS2C-016

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.

### M02-T03 — CLI integration and milestone verification

The approved record retains the documented decision and supporting evidence.

**Requirements:** REQ-TS2C-003, REQ-TS2C-004, REQ-TS2C-005, REQ-TS2C-006, REQ-TS2C-007, REQ-TS2C-008, REQ-TS2C-009, REQ-TS2C-016

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.

## Milestone verification

```text
python -m unittest tests.test_artifacts tests.test_validation tests.test_cli -v
python -m unittest discover -s tests -v
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo tests/fixtures/valid-project
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo . --format json
python C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tracing-spec-to-code
rg -n "VGCCoach2|agentic-workflow" README.md skills/tracing-spec-to-code tests
git diff --check
git status --short
```

The approved record retains the documented decision and supporting evidence.

## Traceability target

| Task | Requirements | Implementation | Verification |
|---|---|---|---|
| M02-T01 | 004, 005, 008, 016 | parser、validator、templates | artifact/validation tests |
| M02-T02 | 003, 005–009, 016 | SKILL、references、scenarios | baseline/loaded behavior |
| M02-T03 | 003–009, 016 | CLI、README、Evidence | CLI/full/self validation |

## Evidence and commit

The approved record retains the documented decision and supporting evidence.

- The approved record retains the documented decision and supporting evidence.

### Baseline controls

The approved record retains the documented decision and supporting evidence.

| Scenario | Decision | Verbatim rationale excerpt |
|---|---|---|
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |

The approved record retains the documented decision and supporting evidence.

### Loaded-skill behavior

The approved record retains the documented decision and supporting evidence.

| Scenario | Decision | Verbatim rationale excerpt |
|---|---|---|
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

### Task status

| Task | Status | Actual verification |
|---|---|---|
| M02-T01 | Completed | TDD RED confirmed missing workflow decisions; targeted 35/35 PASS; full 54/54 PASS; repository self-validation `valid: true`; spec and code-quality reviews PASS |
| M02-T02 | Completed | Strengthened controls exposed 2 failures; loaded Skill 3/3 PASS after Gate wording RED/GREEN; final spec and quality reviews PASS |
| M02-T03 | Completed | Characterization test initial PASS; CLI 7/7 and full 55/55 PASS; Skill validation, spec review, and quality review PASS |

### M02-T01 deviations

- The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

```text
feat(workflow): enforce gated milestone execution

Milestone: M02 Workflow core
Requirements: REQ-TS2C-003, REQ-TS2C-004, REQ-TS2C-005, REQ-TS2C-006, REQ-TS2C-007, REQ-TS2C-008, REQ-TS2C-009, REQ-TS2C-016
```

The approved record retains the documented decision and supporting evidence.

## Risks and Implementation approval

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
