# Task execution policy

Use this policy after Implementation approval approves the current milestone plan. Execute only
the current task and stop when its outcome is independently verifiable.

## Build a bounded context packet

Load only:

- applicable authoritative repository instructions, such as the nearest
  `AGENTS.md`;
- the relevant approved requirements and acceptance criteria;
- the current milestone task: outcome, allowed scope, contracts, and
  verification;
- the minimum implementation and test files needed for that task;
- current working-tree status and the minimum build or package metadata needed
  to identify dependency, test, network, and permission requirements;
- a compressed handoff from the previous task containing only changed paths,
  interface changes, verification results, and unresolved risks.

Do not load the complete conversation history, detailed future milestones,
unrelated spec sections, or broad repository content by default. Discover a
specific dependency when evidence requires it and record why it entered scope.
If the packet keeps expanding or the task has multiple independent outcomes,
pause and split the task or request a scope decision instead of loading
indefinitely.

## Choose verification by behavior and risk

Record the selected level, why it fits, the command or observation, expected
result, and actual result in the milestone plan.

### Lightweight behavioral verification

Use for one-off scripts, configuration, documentation mechanics, or low-risk
glue changes where a real invocation or inspection exercises the changed
behavior. Verify the produced output or state, not merely that a file or token
exists.

### Behavioral test

Use for stable behavior that warrants regression coverage but does not require
a test-first design cycle. Assert externally observable input/output, state
transition, or error handling.

### TDD

Use for core logic, public APIs, complex state, material bug fixes, or risky
behavior:

1. Write one focused test for the missing or incorrect behavior.
2. Run it and confirm RED for the intended behavioral reason.
3. Implement the smallest production change.
4. Run the focused test and relevant targeted suite until GREEN.
5. Refactor only while tests stay green.

A RED is invalid when it proves only that a file, symbol, fixture, string, or
test helper is absent; fails from syntax, import, setup, or environment error;
or asserts implementation shape instead of behavior. If a new test passes
immediately, classify it as coverage of existing behavior and do not claim a
TDD RED.

## Execute and checkpoint

1. Confirm the task scope, working tree, dependencies, network and permission
   needs before changing files.
2. Make only in-scope changes. If reality requires a material change, follow
   Change approval; record non-material deviations.
   Do not add or change `Baseline ownership transfers` after implementation
   approval; doing so requires renewed explicit approval of the plan.
   When an approved Change Request modifies the authoritative spec, keep the
   task paused through the separately authorized fact-change checkpoint in
   `workflow.md`. Before resuming, run the read-only `change-resume` gate with
   the exact current plan and Change Request. A nonzero result, missing command,
   or unknown checkpoint state blocks all affected implementation and testing.
3. Run targeted verification and capture the actual result.
4. Keep the repository runnable. Use a spec-compliance checkpoint before the
   next task and broader verification before milestone completion.
5. Do not mark a task or milestone complete while required verification is
   missing or failing.
6. When the milestone is complete, read and follow
   [milestone-commit.md](milestone-commit.md) before staging, committing, or
   reporting delivery. Plan completion is not milestone delivery: keep the
   roadmap's `Current milestone` unchanged until the commit and post-commit
   verification succeed. Then follow the milestone-commit policy to mark the
   plan `Delivered` and enter the next roadmap milestone's `Awaiting` state.
   Delivery remains pending until the separately authorized lifecycle
   checkpoint commit records that transition. Do not stage it without current
   user authorization, and do not treat its authorization as permission to
   push or perform another remote operation.

After a valid fact-change checkpoint, treat its commit as the task's new fact
baseline. Do not re-stage unchanged checkpoint artifacts during milestone
delivery. The later milestone commit contains only implementation, tests, and
milestone evidence changed after that checkpoint. The current plan belongs in
that commit when its task status, traceability, verification, risks, deviations,
or commit evidence changed; an unchanged roadmap or Change Request does not.

The authoritative spec remains excluded from milestone scope. If it differs
from HEAD after the checkpoint, stop: milestone `precommit` must still return
`SPEC_INDEX_DIRTY` or `SPEC_WORKTREE_DIRTY`. Do not use a baseline ownership
transfer or a meaningless edit to move the spec or an already committed Change
Request into the milestone commit.

## Record verification evidence canonically

For comma-separated `Requirements`, `Implementation`, `Tests`, `Baseline dirty
paths`, and `Baseline ownership transfers`, parse each literal-comma item
independently. An item is either plain text or is enclosed by one complete pair
of backticks. Reject empty list items, duplicates, and any other backtick use;
do not repair or guess malformed values.

Every `Implementation` item is one repository-relative canonical file path.
Every `Tests` item is either `<repository-relative-path>` or
`<repository-relative-path>::<selector>`, with exactly one non-empty selector.
Absolute paths, `..`, backslashes, pathspec magic, globs, directories, duplicate
identities, empty items, and descriptive prose are invalid. Repository-root
files such as `README.md` and `LICENSE` are valid.

Command-only, temporary-installation, and manual-observation evidence has one
canonical representation and no aliases:
`<current-milestone-plan-path>::Verification`. For Draft or approval-awaiting
plans, ordinary validation checks syntax and permits future paths before file
creation. For a `Completed` plan awaiting delivery, each Traceability
implementation and test path must map to Commit scope, recorded complete
fact-change checkpoint artifacts, or that exact plan evidence reference. Clean
artifacts already recorded by a fact-change checkpoint are not added back to
milestone scope.

Task status `Actual verification` is machine-readable. Use this exact grammar:

```text
[label: ] [passed/total ] PASS|PASSED[. non-empty evidence]
```

The label is a single token made from letters, digits, `_`, `.`, `-`, `/`, or
backticks. Counts must be positive and equal. A detail suffix, when present,
starts with a period followed by whitespace and non-empty evidence. Examples:
`GREEN: 7/7 PASS. Additional evidence...`, `PASS. Valid skill:
skills/example`, and `PASS. {"issues": [], "valid": true}`. Do not use a
semicolon or free-form success phrase in place of this grammar.

The Verification table has an independent `Result` column. When `Result` is
exactly `PASS` (case-insensitive), `Actual` records the non-empty command
output verbatim; it is opaque evidence and is not parsed as a success phrase.
`None`, `Pending`, `Skipped`, and an empty value are invalid. The agent setting
`Result` remains responsible for matching the output to the expected result.

## Deliver without a report artifact

Persist evidence in the current milestone plan. By default, display the
milestone delivery summary to the user and do not create a separate delivery
report.

Include:

- delivered outcome and covered Requirement IDs;
- main behavioral and artifact changes;
- verification commands and actual results;
- known limitations, skipped checks, and unresolved risks;
- the milestone commit when one exists;
- optionally, the next milestone name from the roadmap table; lifecycle state
  changes follow the milestone-commit policy and do not authorize its plan.

The displayed summary is not the evidence source and does not authorize the
next milestone or any remote Git operation.
