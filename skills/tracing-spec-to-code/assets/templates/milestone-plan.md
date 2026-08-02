# <Feature> M01 <Milestone name> Plan

- Status: Draft — Awaiting implementation approval
- Milestone: M01 — <Milestone name>
- Spec: `docs/specs/<feature>-spec.md`
- Roadmap: `docs/plans/<feature>-roadmap.md`
- Requirements: REQ-<FEATURE>-001
- Implementation approval: Pending

`Status: Completed` means implementation and verification are ready for
delivery. Keep this plan as the roadmap's `Current milestone` through staging,
`precommit`, commit, and post-commit verification. After they succeed, change
the plan to `Status: Delivered` before advancing the roadmap.

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
| `M01-T02` | `REQ-<FEATURE>-001` | `<exact/path>` | `docs/plans/<this-plan>.md::Verification` |

Every comma-separated `Implementation` item is one repository-relative
canonical file path. Every `Tests` item is either a canonical file path or one
path followed by exactly one non-empty `::<selector>`. Command-only, temporary
installation, and manual-observation evidence has exactly one representation:
this plan's canonical path followed by `::Verification`. Descriptive aliases
such as `Spec`, `roadmap`, `this plan`, or `verification commands` are invalid.
Root files such as `README.md` and `LICENSE` remain valid.

## Evidence and commit

### Task status

| Task | Status | Actual verification |
|---|---|---|
| `M01-T01` | Pending | Pending |
| `M01-T02` | Pending | Pending |

For a completed task, write `Actual verification` as `[label: ]
[passed/total ] PASS|PASSED[. non-empty evidence]`; for example, `GREEN: 7/7
PASS. Targeted suite completed`. Counts, when present, must be positive and
equal.

- Approved Change Requests: None
- Deviations: None
- Baseline dirty paths: None
- Baseline ownership transfers: None

The approved spec must already be tracked, present in recorded HEAD, and clean
in both index and worktree before Implementation approval or implementation.
A transfer must be recorded before Implementation approval when the approved
plan or roadmap is already dirty, and the exact same canonical path must appear
in `Baseline dirty paths` and `Commit scope`. Only this plan and its one roadmap
are eligible. A transfer cannot authorize the spec. Changing the transfer field
requires renewed approval; all implementation, test, user, and other-file
overlap remains blocked.

After milestone commit and post-commit verification, record `Delivered` and the
roadmap advance in a separate lifecycle checkpoint commit. Report its exact
two-path scope and request current-user authorization before staging it.

### Verification

| Scope | Command | Expected | Actual | Result |
|---|---|---|---|---|
| Targeted | `<targeted test command>` | All pass | Pending | Pending |
| Broader | `<full test command>` | All pass | Pending | Pending |

When `Result` is `PASS`, replace `Actual` with the non-empty command output
verbatim. `None`, `Pending`, `Skipped`, and empty output are invalid; `Actual`
does not need to repeat the Task status PASS grammar.

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

When approved Change Requests affect this milestone, add exactly one canonical
plural trailer, for example `Change-Requests: CR-01, CR-02`. The subject, one
blank line, milestone name, Requirements list, and Change Requests list are
validated by ordinary repository validation before staging.
