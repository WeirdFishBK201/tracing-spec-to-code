# CR-02 — Missing reference issue code

- Status: Approved
- Date:2026-07-30
- Change approval: Approved on 2026-07-30
- Correction: Rule 2's scope is limited by approved CR-03 to requirements assigned by the roadmap to the current milestone.
- Trigger: M01-T02 validation contract review
- Requirements:REQ-TS2C-002
- Affected milestone: M01 — Artifact contracts
- Affected tasks: M01-T02, M01-T03

## Trigger and evidence

REQ-TS2C-002 explicitly requires the validator to detect duplicate, missing, and unknown references. The approved M01 plan provides `REQ_ID_DUPLICATE` and `REQ_REFERENCE_UNKNOWN`, but no stable issue code represents a missing traceability relationship.

Reusing `REQ_REFERENCE_UNKNOWN` for missing references would conflate two different facts:

- **Unknown**: An artifact references a Requirement ID that is not defined in the spec.
- **Missing**: The spec defines the Requirement ID, but the roadmap or plan lacks the required reference, or a plan task references no known requirement.

## Proposed change

Add the stable validation issue code:

```text
REQ_REFERENCE_MISSING
```

M01 performs only deterministic checks:

1. Every spec requirement must be referenced by the roadmap.
2. Every spec requirement must be referenced by at least one milestone-plan task.
3. Every milestone-plan task must reference at least one Requirement ID known to the spec within its own heading section.
4. A missing issue points to the spec requirement definition line or task heading line, and the message identifies the missing target relationship.
5. When the corresponding artifact is entirely missing, report only `ARTIFACT_MISSING`; do not add coverage noise derived from that missing artifact.

`REQ_REFERENCE_UNKNOWN` retains its original meaning: a syntactically valid referenced ID does not exist in the spec definition index.

Required updates:

- M01 plan stable issue codes and T02 test scope.
- `tests/test_validation.py` behavioral tests for roadmap coverage, plan-task coverage, and tasks without requirements.
- CLI JSON/text passes through the new code without changing the schema or exit code.

## Impact

- **Spec/Roadmap**: Do not change requirements or milestone coverage.
- **Parser**: Retain artifact, line, definition, and task-section context for each ID occurrence so pure validation rules can consume it.
- **Validation**: Add one issue code and three deterministic missing-reference checks.
- **CLI**: Still return exit code `1` when this issue is found.
- **Dependencies/network**: No new dependency or network requirement.
- **Scope**: Still three M01 tasks; do not assess the semantic sufficiency of implementation/test evidence, which remains the responsibility of a later evidence milestone.

## Alternatives

1. **Reuse `REQ_REFERENCE_UNKNOWN`.** The classification would be inaccurate and CI could not distinguish a bad ID from a missing relationship; not recommended.
2. **Describe missing data only in the message, without a stable code.** This would force machine consumers to parse prose; not recommended.
3. **Defer to a later milestone.** M01 could not satisfy the explicit acceptance condition of REQ-TS2C-002; unacceptable.

## Migration

The validator has not been released, so no data migration is required. Future CI must allow the new `REQ_REFERENCE_MISSING` code.

## Change approval

Change approval was approved on 2026-07-30. Update the M01 plan before continuing the RED/GREEN cycle in `tests/test_validation.py`.
