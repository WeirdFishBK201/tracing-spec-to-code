# tracing-spec-to-code Specification

- Status: Approved
- Requirements confirmation: Approved
- Approval date: 2026-07-29
- Change approval: CR-13 approved on 2026-07-31
- Design basis: `docs/design/2026-07-29-tracing-spec-to-code-design.md`
- Product boundary: an independent skill project; it does not read, depend on, or modify VGCCoach2

## 1. Product goal

`tracing-spec-to-code` provides agents with a lightweight, inspectable Spec → Plan → Code workflow. Stable IDs, human approval, constrained context, behavioral verification, and milestone commits keep sources of truth aligned with implementation while avoiding a heavyweight state machine and process-document growth.

## 2. Requirements

### REQ-TS2C-001 — Fixed and configurable artifacts

The system must provide fixed default paths and names for the spec, roadmap, current milestone plan, and Change Request, while allowing a root-level JSON configuration to override their locations.

Acceptance criteria:

- Without configuration, use the defaults defined by the design document.
- Valid configuration can override documentation directories and naming templates.
- Configuration cannot disable IDs, approvals, traceability, or the no-silent-deviation rule.
- Invalid configuration produces a clear, actionable error instead of guessed values.

### REQ-TS2C-002 — Stable end-to-end traceability

The system must use stable Requirement IDs to connect the spec, roadmap milestones, plan tasks, implementation paths, and test/verification evidence.

Acceptance criteria:

- The default Requirement ID format is `REQ-<FEATURE>-NNN`; IDs are never renumbered or reused after creation.
- The default plan task ID format is `MNN-TNN`.
- The validator detects duplicate, missing, and unknown references.
- A completed requirement can be traced to tasks, implementation paths, and actual verification results.
- Requirement ID comments are not required in every source file.

### REQ-TS2C-003 — No silent deviation

When the spec, plan, code, or tests materially disagree, the agent must pause and update the sources of truth through a Change Request and Change Approval first.

Acceptance criteria:

- The agent explicitly reports the inconsistency and evidence.
- Impact analysis lists affected requirements, milestones, tasks, implementation, and tests.
- Without user approval, the agent does not modify high-level sources of truth or continue related implementation.
- User silence is not approval.
- Only approved Change Requests are persisted as sources of truth.

### REQ-TS2C-004 — Detail only the next milestone

The roadmap may summarize every milestone; a detailed plan may cover only the next milestone to execute.

Acceptance criteria:

- The roadmap contains only milestone outcomes, dependencies, requirements, and verification gates.
- At most one unfinished detailed milestone plan exists for a feature.
- Each milestone has 2–5 tasks, with 3 as the target and 5 as the hard maximum.
- Detailed tasks for later milestones are not expanded before the preceding milestone is complete.

### REQ-TS2C-005 — Independently runnable and verifiable

Each milestone and task must leave the repository runnable and independently verifiable.

Acceptance criteria:

- Each task has one outcome, an exact scope, and targeted verification.
- Each milestone has an observable outcome that does not depend on future implementation.
- Broader verification runs before milestone completion.
- Completion is not claimed when verification fails.

### REQ-TS2C-006 — Adaptive testing strategy

The system must select lightweight behavioral verification, behavioral tests, or TDD according to risk.

Acceptance criteria:

- One-off scripts, configuration, and low-risk glue changes may use genuine lightweight behavioral verification.
- Core business logic, public APIs, complex state, or complex bugs use behavioral tests or TDD.
- The plan records the strategy, rationale, commands, expected results, and actual results.
- A RED result consisting only of missing files, symbols, or text is invalid.

### REQ-TS2C-007 — Task-level context limits

While executing a task, load only the relevant requirements, current plan task, necessary code/tests, and the compressed result of the previous task.

Acceptance criteria:

- By default, do not load the complete discussion history, future milestone details, or unrelated spec sections.
- Pass from the previous task only changed paths, interface changes, verification results, and risks.
- When context keeps expanding, split the task again instead of loading unlimited context.

### REQ-TS2C-008 — Lightweight approvals, impact analysis, and evidence

The system must provide Requirements Confirmation, Implementation Approval, Change Approval, impact analysis, and completion evidence without introducing the heavyweight W-series state machine.

Acceptance criteria:

- Requirements Confirmation approves the spec; Implementation Approval approves the roadmap and current milestone plan; Change Approval approves changes to the sources of truth.
- The milestone plan persistently records task status, traceability, actual verification, approved Change Requests, deviations, and commit metadata.
- Unknown or uncertain states fail closed.
- Do not create a separate state document for every action.

### REQ-TS2C-009 — Delivery summary is display-only

A milestone delivery summary is displayed to the user by default and does not create a separate report document.

Acceptance criteria:

- Persistent evidence is written to the milestone plan.
- The user summary includes the outcome, requirements, major changes, verification, limitations, and commit.
- The summary may show the next milestone name but does not expand its detailed plan.

### REQ-TS2C-010 — Automatic milestone commit

After all milestone tasks are complete and verified, the system must create one accurately scoped Git commit.

Acceptance criteria:

- Before committing, confirm that all tasks, verification, traceability, and evidence are complete.
- Stage only current-milestone files; exclude unrelated user changes.
- Do not commit when Change Approval is pending or verification has failed.
- By default, each milestone has one automatic commit.

### REQ-TS2C-011 — Accurate, concise commit message

The milestone commit must use `type(scope): outcome` and include traceable trailers.

Acceptance criteria:

- The subject describes the outcome rather than listing file operations.
- `Milestone` and `Requirements` trailers are required.
- When approved Change Requests exist, add the `Change-Requests` trailer.
- Implementation Approval approves the message draft; at completion, make only the smallest correction required by approved facts.

### REQ-TS2C-012 — Fail-closed Git operations

The system must not push automatically; it must stop and report when commit permission, identity, hooks, or signing fails.

Acceptance criteria:

- Do not automatically push, create a PR, merge, or modify remote refs.
- Do not fabricate success after a Git failure.
- Keep the milestone undelivered when the commit is incomplete.

### REQ-TS2C-013 — One canonical skill source

The repository must maintain one canonical skill; client adapters must not copy and independently evolve workflow content.

Acceptance criteria:

- The canonical source is `skills/tracing-spec-to-code/`.
- `SKILL.md` uses only broadly supported `name` and `description` frontmatter.
- Internal resources use relative paths.
- The validator depends only on the Python standard library and Git.

### REQ-TS2C-014 — Multi-client distribution

The system must support registry-driven installation for multiple clients and distinguish release verification from structural compatibility levels.

Acceptance criteria:

- The registry defines the approved clients and their Level 1 or Level 2 support.
- The installer copies the complete canonical skill directory and never silently overwrites an existing target.
- New clients are added primarily through the registry without modifying the workflow core.

### REQ-TS2C-015 — Unguided baseline and pressure verification

Before release, the skill must undergo an unloaded-skill baseline and loaded-skill pressure-scenario verification.

Acceptance criteria:

- The baseline records the agent’s actual choice and verbatim rationale.
- Each pressure scenario combines at least three pressure types.
- New rationalizations enter a rule-revision and retest loop.
- Key wording variants are repeated at least five times.
- Level 1 completes installation, discovery, and a minimal workflow; Level 2 completes structural and smoke verification.

### REQ-TS2C-016 — Project isolation

This project must remain independent of VGCCoach2 at all times.

Acceptance criteria:

- Implementation, tests, fixtures, and documentation do not read or reference VGCCoach2 project content.
- Do not add VGCCoach2 paths to tool defaults or test inputs.
- Do not expand the current project to preserve compatibility with the legacy `agentic-workflow`.

### REQ-TS2C-017 — Readable localized workflow terminology

The maintained repository must use one descriptive English workflow contract, while user-facing approval labels may be selected in English or Simplified Chinese according to the latest user message.

Acceptance criteria:

- Maintained prose, documentation, templates, filenames, JSON, YAML, and commit trailers use the descriptive English terms Requirements Confirmation, Implementation Approval, Change Approval, and Change Request.
- Stable machine names are `requirements_confirmation`, `implementation_approval`, `change_approval`, `change_request`, `change_request_id`, and `approved_change_requests`; Change Request IDs use `CR-NN` and commit trailers use `Change-Requests`.
- User-facing labels use English or Simplified Chinese according to the dominant language of the latest user message; ambiguous or unsupported input falls back to English.
- The four exact Simplified Chinese labels are localized data and the only permitted non-English text in maintained documentation examples.
- This is a breaking migration: no compatibility aliases, fallback parsing, migration readers, or dual writes are retained.

### REQ-TS2C-018 — Public GitHub npx distribution

The canonical Skill must be installable from the public GitHub repository with
the standard `skills` CLI, with a pinned acceptance path that proves isolated
project and Codex global installations match the canonical content.

Acceptance criteria:

- The user-facing Quick Start uses
  `npx skills@latest add WeirdFishBK201/tracing-spec-to-code`.
- Repository acceptance pins `skills@1.5.21` and records its Node.js minimum.
- Project and Codex global acceptance run only in isolated temporary roots and
  force copy installation.
- Each installed Skill matches `skills/tracing-spec-to-code/` by relative path,
  byte size, and SHA-256 digest after excluding runtime-only Python cache files.
- The normal unit suite remains offline; real local-source and public-GitHub
  acceptance are explicit network-enabled verification commands.
- The existing Python offline installer and the user-owned external client
  verification boundary remain unchanged.

## 3. Non-goals

- A general issue tracker, project-management platform, or status database.
- One detailed implementation plan for the entire project.
- Automatic modification of approved sources of truth.
- A delivery report created only to leave a record.
- Automatic installation of Python, Git, or other system dependencies.
- Automatic push, PR, merge, or release.

## 4. Global constraints

- Execute only one milestone plan at a time.
- At the end of each milestone, the repository must be runnable and verifiable.
- Do not enter the next stage without human approval.
- Pause on all unknown states; do not guess automatically.
- Documentation and implementation use UTF-8; commands and paths must be Windows-compatible.
- Python 3.10 is the recommended minimum; the final value is determined by Implementation Approval.

## 5. Definition of done

Project completion requires:

- REQ-TS2C-001 through REQ-TS2C-018 each have milestone, task, implementation, and verification evidence.
- Level 1 client verification passes and Level 2 smoke tests have actual records, or an Approved Change Request explicitly records an administrative completion waiver, the unverified boundary, and client results that must not be claimed.
- The unguided baseline, loaded pressure tests, and wording micro-tests are complete.
- The canonical skill, validator, installer, documentation, and release metadata work from a clean clone.
- No pending Change Approval, unexplained deviation, or unverified completion claim remains.
