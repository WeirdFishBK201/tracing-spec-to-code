# CR-12 — Administrative completion waiver

- Status: Approved
- Change approval: Approved on 2026-07-31
- Date: 2026-07-31
- Requirements: REQ-TS2C-016
- Affected milestone: M05 — Evaluation and release
- Affected tasks: M05-T03, M05-T04

## Trigger and evidence

The user directed that M05 and the roadmap be marked complete after retaining
ownership of the eight-client live discovery/smoke work:

The approved record retains the documented decision and supporting evidence.

The repository currently contains no `client-*.json` evidence. Unfiltered
evaluation therefore correctly returns
`EVALUATION_INCOMPLETE: level1 clients are incomplete`.

This requested state conflicts with two approved facts:

- The specification completion definition requires Level 1 clients to pass
  and Level 2 smoke tests to have actual records.
- Approved CR-11 permits T04 closeout before those results but explicitly
  keeps M05 and the roadmap in progress until the user-owned evidence exists.

## Proposed change

- Treat the user's explicit administrative waiver as a terminal substitute for
  repository-recorded Level 1/2 evidence when determining M05 and roadmap
  status.
- Mark the M05 plan and roadmap `Completed`.
- Amend the specification completion definition so the client requirement can
  be satisfied either by committed evidence or by an explicitly approved
  administrative waiver.
- Preserve the unfiltered evaluation fail-closed behavior and the absence of
  `client-*.json`; do not report `5/5`, `3/3`, or any client PASS result.
- Record the final state as completed with an unverified external-client
  limitation, not as a fully evidenced client-compatibility result.

## Impact

- Requirements: REQ-TS2C-016 completion semantics are weakened; repository
  evidence is no longer mandatory for the Level 1/2 portion when a user waiver
  is approved.
- Fact sources: update the specification, M05 plan, roadmap, CR-11 status
  consequence, and user-facing release boundary.
- Implementation: no evaluator, validator, installer, registry, Skill, or
  evidence JSON behavior changes.
- Tests: deterministic suites remain unchanged; repository validation must
  pass after fact-source updates, while unfiltered evaluation must continue to
  exit 1 for missing client evidence.
- Release semantics: the project can be administratively complete while the
  external-client matrix remains unverified and reproducible summary fields
  remain `level1_passed: 0` and `level2_passed: 0`.

## Alternatives

1. Keep M05 and the roadmap in progress until the user records all eight
   results. This preserves the approved specification and CR-11.
2. Accept a concise user-provided result table and record real evidence before
   completion. This preserves evidence-based completion but requires the
   missing test details.
3. Mark client checks as PASS without evidence. Rejected because it would
   fabricate results and contradict the fail-closed evaluation contract.

## Migration

If approved, update the authoritative fact sources in precedence order:
specification, roadmap, M05 plan, CR-11 consequence text, README boundary, and
this request's approval record. Do not create client result files.

## Change approval

The approved record retains the documented decision and supporting evidence.
this request. The approval authorizes administrative completion only and does
not assert any Level 1 or Level 2 client PASS.
