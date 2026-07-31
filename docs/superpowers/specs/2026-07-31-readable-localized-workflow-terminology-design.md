# Readable Localized Workflow Terminology Design

- Status: Approved design
- Date: 2026-07-31
- Target milestone: M06
- Proposed requirement: REQ-TS2C-017
- Design approval: Approved by the user on 2026-07-31

## Goal

Replace the current workflow vocabulary throughout the tracked repository with
descriptive canonical English terms. Present workflow prompts to users in the
language of their most recent message, while keeping documentation, templates,
machine contracts, and stored artifacts in English.

This is a breaking migration for a new, unreleased Skill. It does not preserve
or parse artifacts that use the superseded vocabulary.

## Decisions

1. The migration is atomic across code, tests, templates, documentation,
   examples, and tracked evidence.
2. No compatibility aliases, fallback parser branches, or dual-write behavior
   will be added.
3. Git history will not be rewritten. The acceptance boundary is the tracked
   content at the completed M06 revision.
4. Canonical internal terminology and machine contracts are English.
5. User-facing workflow prompts are localized at render time.
6. README files and all other project documentation remain English.

## Canonical Vocabulary

| Workflow concept | Canonical term | Stable machine representation |
| --- | --- | --- |
| Confirming the requested outcome and constraints | Requirements confirmation | `requirements_confirmation` |
| Authorizing implementation to begin | Implementation approval | `implementation_approval` |
| Authorizing a material change to an approved scope | Change approval | `change_approval` |
| Recording a proposed change | Change Request | `change_request` |
| Identifying a proposed change | Change Request ID | `change_request_id`, formatted as `CR-01` |
| Listing approved changes | Approved Change Requests | `approved_change_requests` |
| Linking a commit to approved changes | Change Requests trailer | `Change-Requests` |

Change Request document filenames use the
`FEATURE-crNN-SHORT-NAME.md` pattern, for example
`checkout-cr01-add-tax-region.md`.

Identifiers remain visible in internal artifacts and machine-readable output.
Normal user prompts use only descriptive localized labels unless an identifier
is necessary to resolve an ambiguity or the user explicitly asks for technical
details.

## User-Facing Localization

The renderer determines the prompt language from the dominant language of the
most recent user message:

| Canonical concept | English | Simplified Chinese |
| --- | --- | --- |
| Requirements confirmation | Requirements confirmation | 需求确认 |
| Implementation approval | Implementation approval | 实施批准 |
| Change approval | Change approval | 变更批准 |
| Change Request | Change request | 变更申请 |

English is the fallback when the language is ambiguous or unsupported. The
decision is message-scoped rather than operating-system-, repository-, or
session-locale-based, so a user can switch languages naturally during a
conversation.

Localization applies only to user-facing explanatory text and prompts. Stable
JSON fields, validation codes, filenames, templates, evidence, and commit
trailers use the canonical English contract.

## Architecture

### Domain and Artifact Contract

The parser and domain model expose only the canonical concepts and field names.
Templates generate only the canonical headings, identifiers, filenames, JSON
fields, and commit trailers. Unknown or superseded workflow structures fail
normal validation instead of entering a compatibility path.

### Conversation Rendering

Workflow logic produces semantic prompt keys rather than preformatted text. A
small language selector reads the most recent user message, and a renderer maps
each semantic key to the supported language. Workflow state and authorization
rules remain independent of display language.

```text
latest user message
        |
        v
language selector -----> fallback: English
        |
        v
semantic workflow state
        |
        v
localized user prompt
```

### Repository Migration

M06 updates every tracked current-tree reference as one coordinated change:

- parser constants, domain fields, validation messages, and public interfaces;
- Skill instructions, templates, README files, specifications, and plans;
- test names, fixtures, assertions, snapshots, and evaluation scenarios;
- Change Request documents, filenames, links, and commit-trailer examples;
- machine-readable evidence, generated summaries, mappings, and integrity
  metadata.

Renamed documents must have all inbound links and discovery rules updated.
Evidence derived from repository content must be regenerated so hashes,
digests, counts, and manifests remain valid.

## Validation and Error Handling

- Ambiguous or unsupported user language selects English without blocking the
  workflow.
- Missing localization entries fail tests; they do not silently expose an
  internal key to the user.
- Invalid machine fields, identifiers, filenames, and trailers fail existing
  strict validation.
- A partially migrated repository is not accepted. Validators and tests must
  run against one canonical contract.
- Stored user-authored prose is not translated or otherwise rewritten unless
  it is a maintained project example or fixture.

## Test Strategy

Implementation follows test-driven development:

1. Add or update focused tests for the canonical parser and artifact contract.
2. Add language-selection and rendering tests for English, Simplified Chinese,
   mixed-language messages, and ambiguous input.
3. Assert that normal user prompts contain descriptive localized labels and do
   not expose internal identifiers unnecessarily.
4. Update fixtures and evidence tests to the canonical machine contract.
5. Run the repository validator, evaluation summary checks, evidence integrity
   checks, installer matrix, quick validation, and the full local test suite.
6. Scan all tracked current-tree text for the superseded vocabulary and reject
   remaining matches.

No external client verification is required for M06; the user retains ownership
of that separate validation.

## Risks and Controls

| Risk | Control |
| --- | --- |
| A filename is renamed without updating a link or discovery rule | Validate links, discovery output, and artifact counts after the atomic migration |
| Evidence becomes internally inconsistent | Regenerate derived evidence and rerun all integrity checks |
| Localization changes authorization behavior | Keep semantic workflow state separate from rendering and test both languages against the same transitions |
| Mixed-language input selects an unexpected label | Define dominant-language fixtures and use English for ambiguous cases |
| Internal identifiers leak into routine prompts | Test rendered user output independently from machine-readable output |

## Out of Scope

- Rewriting Git history.
- Reading artifacts created with the superseded contract.
- Selecting language from the operating system, terminal, or repository locale.
- Translating arbitrary user-authored stored content.
- Adding languages beyond English and Simplified Chinese in M06.
- External client verification.

## Acceptance Criteria

1. All tracked current-tree workflow terminology uses the canonical vocabulary
   and machine contract defined here.
2. No parser, alias, fixture, or documentation path preserves the superseded
   contract.
3. Normal workflow prompts display descriptive English or Simplified Chinese
   labels based on the most recent user message, with English fallback.
4. README files, maintained documentation, templates, and machine artifacts are
   English.
5. Change Request filenames, identifiers, JSON fields, and commit trailers use
   the new contract consistently.
6. All targeted checks, repository validators, evidence integrity checks, and
   the full local test suite pass.
7. Git history remains unchanged except for normal forward commits.

## Delivery Boundary

This document defines M06. Implementation begins only after the user reviews
this written design and explicitly authorizes the milestone plan.
