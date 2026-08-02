# CR-01 — <Change title>

- Status: Pending
- Change approval: Pending
- Date: <YYYY-MM-DD>
- Requirements: REQ-<FEATURE>-001
- Affected milestone: M01
- Affected tasks: M01-T01
- Authoritative spec change: No
<!-- When the approved change modifies the authoritative spec, set the field
above to Yes and uncomment all three canonical checkpoint fields below. Change
approval must approve the exact artifact list. The spec and this Change Request
are mandatory; include the roadmap and current plan only when affected. -->
<!-- - Fact-change artifacts: `docs/specs/<feature>-spec.md`, `docs/changes/<feature>-cr01-<slug>.md` -->
<!-- - Fact-change commit authorization: Pending -->
<!-- - Fact-change base commit: <full-lowercase-HEAD-commit-id> -->

## Trigger and evidence

<Observed mismatch and precise evidence>

## Proposed change

<Smallest fact-source change that resolves the mismatch>

## Impact

- Requirements: <affected IDs>
- Implementation: <affected paths or interfaces>
- Tests: <affected commands or cases>

## Alternatives

1. <Alternative and trade-off>

## Migration

<Migration or “None”>

## Change approval

Pending user approval. Silence is not approval.

## Fact-change checkpoint

If `Authoritative spec change` is `Yes`, keep the affected task paused after
Change approval. Update every artifact in the approved exact scope, record the
base HEAD, and obtain separate explicit current-user authorization for the one
local fact-change commit. Change approval does not authorize that commit or any
remote operation. Run `change-precommit`, create the normal commit only after a
pass, then run `change-resume`; resume the task only after that gate passes.
