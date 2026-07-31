# Milestone commit policy

Use this policy only after all tasks in the one active milestone are complete.
The selected milestone plan is the canonical source for evidence, exact commit
scope, and the approved commit draft.

## Establish preconditions

Before any Git mutation:

1. Read the current roadmap and the exact active milestone plan.
2. Confirm Implementation approval is `Approved`, no Change approval is pending, every task is
   `Completed`, and the plan records targeted and broader verification as
   `PASS`.
3. Confirm `Approved requests`, `Deviations`, `Baseline dirty paths`,
   traceability, verification, commit scope, and commit draft are complete.
4. Compare the milestone-start baseline dirty paths with the commit scope. Any
   overlap blocks delivery; do not guess which hunks belong to whom.
5. Obtain any approval required by the environment for index and ref writes.

Unknown, incomplete, or conflicting state blocks the commit. Deadline,
authority, sunk effort, or a request to “commit anyway” does not replace a
recorded gate or passing evidence.

## Stage and validate

1. Record the current HEAD.
2. Read the exact file paths from the plan's `Commit scope` table.
3. Stage only those literal paths with
   `git --literal-pathspecs add -- <exact paths>`. The global
   `--literal-pathspecs` option must appear before `add`.
4. Never use ordinary pathspec interpretation, `git add .`, `git add -A`, a
   directory, or a glob. Leave unrelated staged, unstaged, and untracked user
   changes untouched.
5. Run the bundled read-only check after staging:

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py precommit \
  --repo . --plan <exact-milestone-plan> --format json
```

A nonzero exit blocks the commit. Do not reinterpret an issue as a warning or
substitute a manual scope check.

## Create and verify one commit

When `precommit` exits `0`:

1. Execute exactly one normal `git commit` using the plan's approved draft.
2. Do not use `--no-verify`, disable hooks or signing, change identity to evade
   a failure, or amend another commit.
3. Re-read HEAD. It must differ from the recorded HEAD by exactly one commit.
4. Read the created commit without mutating it. Its full message and trailers
   must equal the approved draft, and its committed path set must equal the
   plan's exact commit scope.
5. Report the actual hash only in the delivery summary. Do not write the hash
   back into the same commit.

Do not push, fetch, pull, create a PR, merge, modify remotes, or mutate remote
refs. A local milestone commit does not authorize a remote operation.

## Fail closed and report state

If staging, `precommit`, `git commit`, or post-commit verification fails, stop
and do not claim delivery. Do not reset, checkout, restore, unstage, delete, or
make a compensating commit.

Report, in this order:

1. failed step, exit status, and diagnostic;
2. recorded HEAD and current HEAD;
3. current staged paths and worktree status;
4. whether a commit was created and whether verification passed;
5. the exact user decision or environment fix required next.

Preserve the real index and worktree so the user can inspect and choose the
recovery action.
