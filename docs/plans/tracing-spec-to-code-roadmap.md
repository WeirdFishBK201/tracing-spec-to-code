# tracing-spec-to-code Roadmap

- Status: Completed — M06 Readable localized terminology
- Spec: `docs/specs/tracing-spec-to-code-spec.md`
- Requirements confirmation: Approved on 2026-07-29
- Implementation approval: Approved on 2026-07-31
- Change approval: CR-01 through CR-08 approved on 2026-07-30; CR-09 through CR-12 approved on 2026-07-31
- Current milestone: M06
- Current detailed plan: `docs/plans/tracing-spec-to-code-m06-readable-localized-terminology.md`
- M06 design: `docs/superpowers/specs/2026-07-31-readable-localized-workflow-terminology-design.md`

## Rules

- The roadmap records only milestone outcomes, dependencies, requirements, and
  verification gates.
- Maintain a detailed plan only for the next milestone.
- Every milestone leaves the repository runnable and independently verifiable.
- After completing a milestone, create one scoped commit and stop for the next
  approval.
- REQ-TS2C-016 is the global isolation constraint for every milestone.

## Milestones

| Milestone | Outcome | Primary requirements | Dependencies | Verification gate |
| --- | --- | --- | --- | --- |
| M01 — Artifact contracts | A runnable zero-third-party-dependency validator parses configuration, discovers artifacts, and checks ID and structural traceability | REQ-TS2C-001, REQ-TS2C-002 | Requirements confirmation | Unit tests, CLI behavior tests, template validation, Skill structure check |
| M02 — Workflow core | The Skill enforces confirmation and approval states, current-milestone scope, constrained context, and adaptive test decisions | REQ-TS2C-003–009 | M01 | Pressure scenarios, workflow fixtures, behavior tests |
| M03 — Evidence and commit | The Skill validates evidence, isolates staged scope, and safely creates a milestone commit | REQ-TS2C-010–012 | M02 | Temporary Git repository integration tests, failure-path tests |
| M04 — Client distribution | The canonical Skill can be distributed to Level 1 and Level 2 clients through the registry installer | REQ-TS2C-013–014 | M03 | 8×2 installer matrix, complete content and structure validation, Level 1/2 mapping contract |
| M05 — Evaluation and release | Baseline, pressure-scenario, wording, and release checks produce reproducible evidence | REQ-TS2C-015 | M04 | Baseline/loaded comparison, five-run wording checks, candidate clean-clone release verification; CR-12 administratively waives recorded Level 1/2 results without claiming PASS |
| M06 — Readable localized terminology | The current tree uses one descriptive English workflow contract and user prompts select English or Simplified Chinese from the latest user message | REQ-TS2C-017 | M05, approved M06 design | Canonical-contract tests, bilingual prompt-policy tests, migrated evidence integrity, tracked-tree vocabulary scan, full local suite |

## Long-Term Goals

- Remote package distribution requires a separately approved Change Request
  after M06. It must install from a public GitHub source and verify a pinned CLI
  version, project/user scope, canonical-content equality, and clean-environment
  behavior.
- That goal does not authorize network access, dependency downloads, GitHub
  mutation, or push.
- Native-handle security hardening requires a separate Change Request to assess
  Windows and POSIX handle-relative APIs against malicious replacement between
  path creation and first identity capture.

## Requirement Coverage

| Requirement | Planned milestone |
| --- | --- |
| REQ-TS2C-001 | M01 |
| REQ-TS2C-002 | M01 |
| REQ-TS2C-003 | M02 |
| REQ-TS2C-004 | M02 |
| REQ-TS2C-005 | M02 |
| REQ-TS2C-006 | M02 |
| REQ-TS2C-007 | M02 |
| REQ-TS2C-008 | M02 |
| REQ-TS2C-009 | M02 |
| REQ-TS2C-010 | M03 |
| REQ-TS2C-011 | M03 |
| REQ-TS2C-012 | M03 |
| REQ-TS2C-013 | M04 |
| REQ-TS2C-014 | M04 |
| REQ-TS2C-015 | M05 |
| REQ-TS2C-016 | M01–M06 |
| REQ-TS2C-017 | M06 |

## Implementation Approval

M01–M05 are delivered. The M04 implementation commit is
`a6ef478aaf927399f9439fecf473845a248e9c3e`, and the M05 implementation commit
is `95f4c36a8af1581f307ba9e6186236f7e15d04e7`. The independent reruns,
deterministic wording contract, fresh rebuilds, recorded-evidence review, and
M05 clean-clone candidate gate passed.

The user owns the eight-client discovery and smoke checks. CR-12
administratively completed M05 without claiming those client results. The
repository contains no `client-*.json` evidence, so it must not claim
`5/5 + 3/3`; unfiltered evaluation remains fail closed with
`level1_passed: 0` and `level2_passed: 0`.

M06 implementation commit: `d5ca133`.
