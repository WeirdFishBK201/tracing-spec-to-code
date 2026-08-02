# Milestone commit policy

Use this policy only after all tasks in the one active milestone are complete.
The selected milestone plan is the canonical source for evidence, exact commit
scope, and the approved commit draft.

## Commit an approved fact change before task resume

This checkpoint is separate from milestone delivery. When an approved Change
Request modifies the authoritative spec, keep the affected task paused and
follow the fact-change checkpoint in `workflow.md` before further
implementation or testing.

Change approval does not authorize the local checkpoint commit. After all
approved fact sources are updated, report the exact `Fact-change artifacts`
paths and exact `docs(change): checkpoint <CR-NN> fact change` message, then
obtain explicit authorization from the current user for that one local commit.
That authorization does not apply to the milestone commit, lifecycle checkpoint
commit, push, fetch, pull, PR, merge, or any other remote operation.

After authorization, stage only the exact literal metadata scope with
`git --literal-pathspecs add -- <exact paths>` and run `change-precommit`. The
scope always contains the authoritative spec and selected Change Request. It
contains the current roadmap or selected plan only when the approved Change
Request's exact artifact list names it. It must never contain implementation,
tests, unrelated evidence, or user files. A nonzero gate blocks the commit.

Create one normal commit only after the gate passes. Then run `change-resume`.
That post-commit gate verifies the recorded base-to-HEAD increment, normal
single-parent shape, exact message, exact committed path set, and clean spec.
Do not resume the task unless it exits `0`. On failure, preserve the real index,
worktree, and HEAD; do not reset, restore, clean, amend, or compensate.

## Establish preconditions

Before any Git mutation:

1. Read the current roadmap and the exact active milestone plan.
2. Confirm the selected plan's milestone ID must equal the roadmap's
   `Current milestone`. A `Completed` plan remains current while it is being
   delivered.
3. Confirm Implementation approval is `Approved`, no Change approval is pending, every task is
   `Completed`, and the plan records targeted and broader verification as
   `PASS`.
4. Confirm `Approved Change Requests`, `Deviations`, `Baseline dirty paths`,
   traceability, verification, commit scope, and commit draft are complete.
   When `Baseline ownership transfers` is present, confirm it is complete too;
   an absent field grants no transfer.
5. Compare the milestone-start baseline dirty paths with the commit scope. An
   overlap blocks delivery unless the same canonical path is explicitly listed
   in `Baseline ownership transfers`, appears in both baseline and commit
   scope, and exactly equals the selected milestone plan or its one discovered
   roadmap. Absence or `None` grants no transfer. All implementation, test,
   ordinary user, and other-file overlap remains blocked.
6. Confirm every approved spec-changing Change Request has a valid recorded
   fact-change checkpoint. The selected plan may cite the Change Request and
   commit trailer without re-staging its unchanged file.
7. Obtain any approval required by the environment for index and ref writes.

Do not advance `Current milestone` before staging, during `precommit`, after
the commit command, or before post-commit verification completes. Advancing it
early makes the selected completed plan historical and must fail closed.

Unknown, incomplete, or conflicting state blocks the commit. Deadline,
authority, sunk effort, or a request to “commit anyway” does not replace a
recorded gate or passing evidence.

## Stage and validate

1. Record the current HEAD.
2. Read the exact file paths from the plan's `Commit scope` table. Include only
   milestone implementation, tests, and evidence changed after the latest
   fact-change checkpoint. Include a planning or Change Request artifact only
   when its content actually differs from HEAD. Omit every unchanged fact
   artifact already recorded by the checkpoint; do not manufacture an edit to
   make it stageable.
3. Stage only those literal paths with
   `git --literal-pathspecs add -- <exact paths>`. The global
   `--literal-pathspecs` option must appear before `add`.
4. Never use ordinary pathspec interpretation, `git add .`, `git add -A`, a
   directory, or a glob. Leave unrelated staged, unstaged, and untracked user
   changes untouched.
5. Confirm ordinary repository validation already accepts the completed task
   and verification evidence, Traceability paths/references, delivery mapping,
   and Commit draft. `precommit` reuses those same pure artifact checks; it does
   not maintain a second interpretation.
6. Run the bundled read-only check after staging:

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py precommit \
  --repo . --plan <exact-milestone-plan> --format json
```

A nonzero exit blocks the commit. Do not reinterpret an issue as a warning or
substitute a manual scope check.

Only Git-dependent checks wait for `precommit`: the exact staged path set,
unstaged overlap, authoritative-spec index/worktree state, staged scope, HEAD,
and fact-change checkpoint identity. Artifact path/reference and Commit draft
defects must already be visible through ordinary validation.

`precommit` still rejects a dirty or staged authoritative spec with
`SPEC_WORKTREE_DIRTY` or `SPEC_INDEX_DIRTY`. A baseline ownership transfer can
never bypass that invariant, and the spec never belongs in milestone scope.

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
6. Only after all post-commit verification succeeds, mark the completed plan
   `Delivered`. If another roadmap milestone remains, advance
   `Current milestone` to it and set the roadmap to `Awaiting`; ordinary
   validation accepts this state without a detailed next plan. If this was the
   final milestone, keep it as `Current milestone` and set the roadmap to
   `Delivered`.
7. Creating and approving the next detailed plan happens after that delivery
   transition. This delivery state update does not belong to the preceding
   milestone commit; record it in a separate lifecycle checkpoint commit.

## Commit the lifecycle transition separately

After updating the lifecycle state, report the exact transition scope. It is
normally only the just-delivered milestone plan and its one corresponding
roadmap. The agent must not claim the milestone delivery workflow is complete
while this lifecycle transition is uncommitted.

Request explicit authorization from the current user for the separate
lifecycle checkpoint commit. Do not stage or commit the transition before that
authorization. Without authorization, preserve the worktree, do not stage or
commit any transition path, and report the lifecycle checkpoint as pending.

After authorization:

1. Stage only the exact plan and roadmap with
   `git --literal-pathspecs add -- <exact plan> <exact roadmap>`. Do not include
   any other staged, unstaged, deleted, or untracked path.
2. Run the read-only gate with the exact deterministic message:

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py \
  transition-precommit --repo . --plan <exact-milestone-plan> \
  --message "chore(plan): record M01 delivery and advance to M02" \
  --format json
```

3. For a non-final milestone, the message is exactly
   `chore(plan): record <delivered milestone> delivery and advance to <next milestone>`.
   For the final milestone, it is exactly
   `chore(plan): record <delivered milestone> delivery and close roadmap`.
4. A nonzero result blocks the commit. On success, create exactly one normal
   commit with that message and verify its committed paths and message.

Lifecycle checkpoint authorization does not authorize push, PR creation, or
any other remote operation.

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
