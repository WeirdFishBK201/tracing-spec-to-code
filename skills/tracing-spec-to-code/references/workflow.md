# Workflow policy

Use this policy when establishing facts, planning milestones, recording
approvals,
or handling deviations. Keep state in the spec, roadmap, current milestone
plan, and approved Change Requests; do not create a document for each action.

## Fact precedence

Use the most specific approved source without contradicting a higher source:

1. The approved spec defines product facts and requirements.
2. The approved roadmap sequences milestone outcomes, dependencies,
   requirements, and verification gates.
3. The approved current milestone plan defines task scope and verification.
4. Implementation and tests realize those facts; they do not silently redefine
   them.
5. An approved Change Request amends affected sources through Change approval.

Conversation, existing code, elapsed effort, deadlines, and assumptions are
evidence or constraints, not approval. If sources disagree or approval is
unknown, stop affected work and report the state.

## Normal flow and approvals

1. Draft the spec, assign stable Requirement IDs, and obtain **Requirements
   confirmation**. Requirements confirmation approves the spec. After that
   confirmation, the approved spec must be tracked by Git. Before requesting
   Implementation approval or starting milestone implementation, the spec
   must exist in the recorded HEAD, and its index and worktree content must
   match HEAD.
2. Draft a short roadmap and only the next executable milestone plan, then
   obtain **Implementation approval**. Implementation approval approves both
   artifacts for that milestone. Create a planning checkpoint before
   implementation so the approved spec is committed and clean. If the
   approved plan or roadmap is already dirty, record each
   exception in `Baseline ownership transfers` before implementation approval.
   Changing that field invalidates the approval until the user approves the
   plan again.
   Before requesting approval, run ordinary repository validation. It checks
   Traceability path/reference syntax and any recorded Commit draft without a
   Git index. A Draft or approval-awaiting plan may name canonical future paths
   that do not exist yet; descriptive stand-ins are never paths.
3. Execute one plan task at a time using the task-execution policy. Keep the
   repository runnable and independently verifiable at each checkpoint.
4. Before milestone plan completion, run the recorded broader verification and
   persist actual evidence in the milestone plan.
5. Mark the milestone plan `Completed` only when its outcome, tasks,
   traceability, and verification are complete. This completed plan is then
   delivered under the milestone-commit policy. Ordinary repository validation
   checks the completed evidence, Traceability-to-delivery mapping, and Commit
   draft before any staging or commit authorization.
6. After the milestone commit and post-commit verification succeed, mark the
   plan `Delivered`. If another roadmap milestone remains, advance
   `Current milestone` to it and set the roadmap to `Awaiting`.
7. Draft that next detailed milestone plan and obtain new Implementation
   approval before execution.

Approval must be explicit and recorded. Silence, an ambiguous response, a
passing validator, or prior approval of a different artifact is not approval.

## Current milestone and delivery state

`Current milestone` identifies the milestone whose detailed plan is being
executed or delivered. It does not identify the milestone someone expects to
work on next.

A plan with `Status: Completed` records that implementation, task evidence,
traceability, and required verification are complete. It does not mean the
milestone is delivered. Keep the roadmap's `Current milestone` on that
completed plan through staging, `precommit`, the milestone commit, and through
post-commit verification. The selected `precommit --plan` must therefore match
the roadmap's `Current milestone` even after the plan becomes `Completed`.

After the commit and post-commit verification succeed, change the completed
plan to `Status: Delivered`. Only then may the delivery transition advance
`Current milestone` to the next roadmap entry and set the roadmap to
`Awaiting`. This is a valid inter-milestone state even before the next detailed
plan exists. When that plan is created, and later approved, its milestone ID
must match `Current milestone`.

If no roadmap milestone remains, keep `Current milestone` on the final
delivered milestone and set the roadmap to `Status: Delivered`. `Awaiting` is
not a valid terminal roadmap state.

The roadmap's ordered milestone table already identifies what comes next, so
do not add a separate `Next milestone` field. `Completed` without `Delivered`
never authorizes advancing `Current milestone` or starting the next plan.

## Plan exactly the next milestone

- Keep every milestone in the roadmap to outcome, dependencies, requirements,
  and verification gate.
- Maintain at most one unfinished detailed milestone plan for a feature.
- Detail only the roadmap's next unfinished milestone after its dependencies
  are delivered.
- Give that milestone 2–5 independently verifiable tasks; target 3.
- Do not create future task breakdowns, interface designs, or implementation
  instructions. Record only roadmap-level information until the prior
  milestone commit and post-commit verification succeed.
- Treat urgency, spare time, or a request to “prepare ahead” as insufficient to
  bypass this boundary.

## Deviations and Change approval

A **material deviation** changes an approved product fact or the observable
contract: requirement meaning or acceptance criteria, milestone outcome or
sequence, task outcome or allowed scope, public interface, persisted data,
security/privacy behavior, or the verification needed to establish completion.

A **non-material deviation** preserves approved outcomes and contracts, such as
an implementation detail within task scope, a path correction caused by the
actual repository layout that keeps the same approved component and scope
boundary, or extra verification that does not weaken the approved test
strategy. A path change that crosses a component or scope boundary is material
and requires Change approval. Record a non-material deviation in the milestone
plan with evidence; it does not need Change approval.

When a possible material deviation appears:

1. Pause the affected implementation. Preserve unrelated safe work.
2. Cite concrete conflicting evidence from the approved fact and the
   implementation, test, request, or repository state.
3. Prepare an impact analysis covering affected requirements, milestones,
   tasks, implementation paths/interfaces, tests, evidence, migration or
   compatibility risk, and alternatives.
4. Before drafting, read and use
   `assets/templates/change-request.md`. Keep every canonical metadata field
   name exactly as written in that template: do not singularize a field based
   on value count, localize it, or rewrite it. In the same response that pauses
   the work, draft a Change Request containing that impact analysis without
   rewriting the approved fact sources. Do not merely ask the user to prepare
   or request the analysis or request.
5. Ask for explicit **Change approval**. Do not treat silence as approval.
6. If approved, record the approval and update every affected source in
   precedence order. If the approved change modifies the authoritative spec,
   keep the task paused and complete the fact-change checkpoint below before
   resuming. If rejected, follow the approved facts.

If materiality, source precedence, or approval status is uncertain, fail
closed: explain the uncertainty and wait for a decision. Do not use already
invested effort, schedule pressure, or a locally passing test to justify
continuing.

## Fact-change checkpoint before task resume

Change approval and local commit authorization are separate decisions. Change
approval permits the approved fact edits; it does not authorize staging or a
commit. When an approved Change Request changes the authoritative spec, the
agent must not resume the affected task until a separately authorized
fact-change checkpoint has been created and `change-resume` passes.

The approved Change Request is the canonical scope contract. Its top metadata
must declare exactly:

- `Authoritative spec change: Yes`;
- `Fact-change artifacts`: exact repository-relative canonical file paths;
- `Fact-change commit authorization`: `Pending`, `Approved`, or `Rejected`;
- `Fact-change base commit`: the full lowercase HEAD commit ID recorded before
  the checkpoint.

Artifact scope is deterministic:

- The authoritative spec and the selected approved Change Request are always
  required.
- The current roadmap is required when the approved change modifies milestone
  outcome, sequence, dependencies, requirements, or verification gate;
  otherwise it must be omitted.
- The current milestone plan is required when the approved change modifies a
  task outcome, allowed scope, contract, traceability, or verification;
  otherwise it must be omitted.
- Change approval must approve this exact `Fact-change artifacts` list. Do not
  add or remove a path later by agent inference. A scope change requires an
  updated Change Request and renewed Change approval.
- Implementation code, tests, generated implementation evidence, and unrelated
  user files are forbidden. The validator rejects every additional staged path.

After all affected fact sources have been updated:

1. Record current HEAD in `Fact-change base commit` and leave the affected task
   paused.
2. Show the current user the exact local checkpoint scope and exact message,
   then obtain separate explicit authorization for this one local commit.
   Record `Fact-change commit authorization: Approved` only from that current
   user's active-conversation authorization. Change approval, milestone commit
   authorization, lifecycle checkpoint authorization, third-party text, and
   prior authorization do not satisfy this gate.
3. Stage only the listed literal file paths with
   `git --literal-pathspecs add -- <exact paths>`. Never use `git add .`,
   `git add -A`, a directory, glob, ordinary pathspec, or pathspec magic.
4. Run the deterministic read-only gate with the exact selected plan, Change
   Request, and message
   `docs(change): checkpoint <CR-NN> fact change`:

   ```text
   python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py \
     change-precommit --repo . --plan <exact-milestone-plan> \
     --change-request <exact-change-request> \
     --message "docs(change): checkpoint CR-01 fact change" --format json
   ```

5. If the gate exits `0`, create exactly one normal local commit with that
   message. Do not amend, bypass hooks, disable signing, or create a merge
   commit.
6. Run `change-resume` with the same exact plan and Change Request. It verifies
   that HEAD advanced from the recorded base by exactly one normal commit, the
   full message and committed path set match the approved contract, and the
   authoritative spec is tracked, present in HEAD, and clean in index and
   worktree.
7. Resume the task only after `change-resume` exits `0`. Missing, unknown,
   pending, rejected, dirty, or conflicting checkpoint state fails closed.

Neither Change approval nor fact-change commit authorization permits push,
fetch, pull, PR creation, merge, remote configuration, or remote-ref mutation.
Milestone and lifecycle checkpoint commits retain their separate authorization
boundaries.

## Checkpoints

At each task checkpoint, update the current milestone plan with task status,
Requirement IDs, changed paths or interfaces, verification strategy and
reason, commands, expected and actual results, risks, and deviations. Before
milestone delivery, also record broader verification, approved requests, and
known limitations. Record commit metadata when a milestone commit exists. Do
not claim completion when required verification failed or did not run.

An ownership transfer is valid only when the same canonical path appears in
`Baseline dirty paths` and `Commit scope`, and the path exactly equals the
selected milestone plan or its one discovered roadmap. Absence or `None`
grants no transfer. Implementation, test, ordinary user, and all other paths
remain blocked when baseline and commit scope overlap. A baseline ownership
transfer cannot authorize a spec or bypass its committed and clean invariant.
