# CR-11 — User-owned client verification

- Status: Approved
- Change approval: Approved by explicit user direction on 2026-07-31
- Date: 2026-07-31
- Requirements: REQ-TS2C-015, REQ-TS2C-016
- Affected milestone: M05 — Evaluation and release
- Affected tasks: M05-T03, M05-T04

## Trigger and evidence

The approved M05 plan sequences eight-client live discovery/smoke evidence
before the release-candidate closeout. On 2026-07-31 the user explicitly
directed:

The approved record retains the documented decision and supporting evidence.

No eight-client result had been recorded when this direction was received.
Treating the omitted runs as passing would conflict with the evaluation
fail-closed policy and the specification completion definition.

## Proposed change

- Transfer execution and review of the five Level 1 and three Level 2 live
  client checks to the user.
- Permit M05-T04 local candidate verification and one local milestone commit
  before those external results are added.
- Exclude all eight `client-*.json` paths from this candidate.
- Keep unfiltered evaluation validation fail closed. At CR-11 approval, the
  roadmap and overall project completion continued to await the user-owned
  client evidence; CR-12 later superseded only that status consequence.
- Describe the T04 result as a locally verified release candidate, not as proof
  of `5/5` Level 1 or `3/3` Level 2 completion.

## Impact

- Requirements: REQ-TS2C-015 local baseline, pressure, and wording evidence
  remains verified. At CR-11 approval, REQ-TS2C-016 project completion
  remained open until the user-owned client evidence satisfied the
  specification; Approved CR-12 later introduced an administrative completion
  waiver.
- Milestone: CR-11 permitted M05-T04 to complete before external M05-T03
  evidence while M05 and the roadmap remained in progress. Approved CR-12
  later superseded that status consequence without adding client evidence.
- Implementation: update `README.md`, `evaluation/README.md`, the M05 plan, and
  the roadmap; do not change the evaluation schema, validator, registry, or
  client mappings.
- Tests: run the filtered local matrix, require the unfiltered matrix to fail
  closed, and retain every deterministic repository and clean-clone gate.
- Compatibility: no runtime or persisted evidence format changes.

## Alternatives

1. Wait for all eight client runs before T04. This preserves the original
   sequence but conflicts with the user's instruction to proceed directly.
2. Record placeholder or inferred client PASS results. Rejected because it
   fabricates evidence and defeats the fail-closed contract.
3. Remove client completion from the specification. Rejected because the user
   retained the work rather than cancelling the product requirement.

## Migration

None. Future user-produced client records continue to use the existing
schema-v2 cases and immutable `evaluate.py record` flow.

## Change approval

Approved by the user's explicit 2026-07-31 direction quoted above. The approval
changes ownership and sequencing only; it does not assert that any client run
passed.

## Subsequent Change approval

Approved CR-12 marks M05 and the roadmap administratively complete without
client evidence. It does not alter CR-11's ownership transfer, create a client
PASS result, or change the unfiltered evaluation failure.
