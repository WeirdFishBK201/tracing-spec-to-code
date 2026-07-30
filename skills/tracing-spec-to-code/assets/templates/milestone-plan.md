# <Feature> M01 <Milestone name> Plan

- Status: Draft — Awaiting Gate P
- Milestone: M01 — <Milestone name>
- Spec: `docs/specs/<feature>-spec.md`
- Roadmap: `docs/plans/<feature>-roadmap.md`
- Requirements: REQ-<FEATURE>-001
- Gate P: Pending

## Goal

<One independently verifiable outcome>

## Tasks

### M01-T01 — <Task name>

- Objective: <Single testable result>
- Requirements: REQ-<FEATURE>-001
- Files: `<exact/path>`
- Verify: `<targeted command and expected result>`

### M01-T02 — <Task name>

- Objective: <Single testable result>
- Requirements: REQ-<FEATURE>-001
- Files: `<exact/path>`
- Verify: `<targeted command and expected result>`

## Milestone verification

```text
<broader verification command>
```

## Traceability

| Task | Requirements | Implementation | Tests |
|---|---|---|---|
| `M01-T01` | `REQ-<FEATURE>-001` | `<exact/path>` | `tests/<test_file>::<test_name>` |
| `M01-T02` | `REQ-<FEATURE>-001` | `<exact/path>` | `tests/<test_file>::<test_name>` |

## Evidence and commit

### Task status

| Task | Status | Actual verification |
|---|---|---|
| `M01-T01` | Pending | Pending |
| `M01-T02` | Pending | Pending |

- Approved proposals: None
- Deviations: None
- Baseline dirty paths: None

### Verification

| Scope | Command | Expected | Actual | Result |
|---|---|---|---|---|
| Targeted | `<targeted test command>` | All pass | Pending | Pending |
| Broader | `<full test command>` | All pass | Pending | Pending |

### Commit scope

| Path | Purpose |
|---|---|
| `<exact/path>` | <Why this file belongs to the milestone> |

### Commit draft

```text
type(scope): outcome

Milestone: M01 <Milestone name>
Requirements: REQ-<FEATURE>-001
```
