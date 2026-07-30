# Task execution policy

Use this policy after Gate P approves the current milestone plan. Execute only
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
   Gate Δ; record non-material deviations.
3. Run targeted verification and capture the actual result.
4. Keep the repository runnable. Use a spec-compliance checkpoint before the
   next task and broader verification before milestone completion.
5. Do not mark a task or milestone complete while required verification is
   missing or failing.
6. When the milestone is complete, read and follow
   [milestone-commit.md](milestone-commit.md) before staging, committing, or
   reporting delivery.

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
- optionally, the next milestone name without a detailed plan.

The displayed summary is not the evidence source and does not authorize the
next milestone or any remote Git operation.
