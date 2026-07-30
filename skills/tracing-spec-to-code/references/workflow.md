# Workflow policy

Use this policy when establishing facts, planning milestones, crossing gates,
or handling deviations. Keep state in the spec, roadmap, current milestone
plan, and approved change proposals; do not create a document for each action.

## Fact precedence

Use the most specific approved source without contradicting a higher source:

1. The approved spec defines product facts and requirements.
2. The approved roadmap sequences milestone outcomes, dependencies,
   requirements, and verification gates.
3. The approved current milestone plan defines task scope and verification.
4. Implementation and tests realize those facts; they do not silently redefine
   them.
5. An approved change proposal amends affected sources through Gate Δ.

Conversation, existing code, elapsed effort, deadlines, and assumptions are
evidence or constraints, not approval. If sources disagree or approval is
unknown, stop affected work and report the state.

## Normal flow and gates

1. Draft the spec, assign stable Requirement IDs, and obtain **Gate S**.
   Gate S approves the spec.
2. Draft a short roadmap and only the next executable milestone plan, then
   obtain **Gate P**. Gate P approves both artifacts for that milestone.
3. Execute one plan task at a time using the task-execution policy. Keep the
   repository runnable and independently verifiable at each checkpoint.
4. Before milestone completion, run the recorded broader verification and
   persist actual evidence in the milestone plan.
5. Mark the milestone complete only when its outcome, tasks, traceability, and
   verification are complete. The next milestone may then receive a detailed
   plan and a new Gate P.

Approval must be explicit and recorded. Silence, an ambiguous response, a
passing validator, or prior approval of a different artifact is not approval.

## Plan exactly the next milestone

- Keep every milestone in the roadmap to outcome, dependencies, requirements,
  and verification gate.
- Maintain at most one unfinished detailed milestone plan for a feature.
- Detail only the roadmap's next unfinished milestone after its dependencies
  are complete.
- Give that milestone 2–5 independently verifiable tasks; target 3.
- Do not create future task breakdowns, interface designs, or implementation
  instructions. Record only roadmap-level information until the prior
  milestone completes.
- Treat urgency, spare time, or a request to “prepare ahead” as insufficient to
  bypass this boundary.

## Deviations and Gate Δ

A **material deviation** changes an approved product fact or the observable
contract: requirement meaning or acceptance criteria, milestone outcome or
sequence, task outcome or allowed scope, public interface, persisted data,
security/privacy behavior, or the verification needed to establish completion.

A **non-material deviation** preserves approved outcomes and contracts, such as
an implementation detail within task scope, a path correction caused by the
actual repository layout that keeps the same approved component and scope
boundary, or extra verification that does not weaken the approved test
strategy. A path change that crosses a component or scope boundary is material
and requires Gate Δ. Record a non-material deviation in the milestone plan
with evidence; it does not need Gate Δ.

When a possible material deviation appears:

1. Pause the affected implementation. Preserve unrelated safe work.
2. Cite concrete conflicting evidence from the approved fact and the
   implementation, test, request, or repository state.
3. Prepare an impact analysis covering affected requirements, milestones,
   tasks, implementation paths/interfaces, tests, evidence, migration or
   compatibility risk, and alternatives.
4. In the same response that pauses the work, draft a change proposal
   containing that impact analysis without rewriting the approved fact
   sources. Do not merely ask the user to prepare or request the analysis or
   proposal.
5. Ask for explicit **Gate Δ** approval. Do not treat silence as approval.
6. If approved, record the approval and update every affected source in
   precedence order before resuming. If rejected, follow the approved facts.

If materiality, source precedence, or approval status is uncertain, fail
closed: explain the uncertainty and wait for a decision. Do not use already
invested effort, schedule pressure, or a locally passing test to justify
continuing.

## Checkpoints

At each task checkpoint, update the current milestone plan with task status,
Requirement IDs, changed paths or interfaces, verification strategy and
reason, commands, expected and actual results, risks, and deviations. Before
milestone delivery, also record broader verification, approved proposals, and
known limitations. Record commit metadata when a milestone commit exists. Do
not claim completion when required verification failed or did not run.
