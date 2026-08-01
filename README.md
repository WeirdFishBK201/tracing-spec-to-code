# tracing-spec-to-code

`tracing-spec-to-code` is a portable agent skill and deterministic validator
for keeping requirements, plans, implementation, tests, and delivery evidence
aligned throughout agent-assisted development.

It gives coding agents a lightweight Spec → Plan → Code workflow with explicit
human approval at the decisions that matter. The result is less scope drift,
smaller execution steps, and a reviewable trail from each requirement to the
code and verification that delivered it.

## Why use it?

Long-running agent tasks often fail in predictable ways:

- **Requirements drift away from the code.** Stable Requirement IDs connect the
  spec, roadmap, milestone tasks, implementation paths, and test evidence.
- **Plans become too large to execute reliably.** The roadmap stays short while
  only the next milestone receives a detailed, bounded plan.
- **Agents silently change scope when reality differs from the plan.** Material
  deviations pause execution and require an explicit Change Request and human
  approval before the source of truth changes.
- **“Done” is claimed without enough evidence.** Every task records its actual
  verification, and unknown, missing, or conflicting state fails closed.
- **Delivery picks up unrelated work.** A completed milestone stages only its
  declared files and creates one traceable local commit. It never pushes,
  creates a PR, or merges automatically.

## What it provides

- **Requirements confirmation** for approving stable product facts and
  acceptance criteria.
- **A short roadmap** that shows milestone outcomes, dependencies, requirement
  coverage, and verification gates without detailing the whole project.
- **One current milestone plan** with 2–5 independently verifiable tasks, exact
  file scope, and targeted checks.
- **Risk-based verification** that selects lightweight behavioral checks,
  behavioral tests, or TDD according to the change being made.
- **Controlled Change Requests** with impact analysis across requirements,
  milestones, tasks, implementation, tests, and evidence.
- **Persistent delivery evidence** in the milestone plan instead of a growing
  collection of status documents.
- **A deterministic validator** for structural and traceability contracts.

## How the workflow fits together

```text
Approved Spec
    ↓ stable Requirement IDs
Short Roadmap
    ↓ detail only the next milestone
Current Milestone Plan
    ↓ one bounded task at a time
Code + Tests
    ↓ actual verification results
Evidence + Scoped Local Commit
```

Three explicit gates keep the human in control:

1. **Requirements confirmation** approves the spec.
2. **Implementation approval** approves the roadmap and current milestone plan.
3. **Change approval** approves a material change to an accepted fact or scope.

Silence, a passing test, or work already invested never counts as approval.

## Quick Start

```text
npx skills@latest add WeirdFishBK201/tracing-spec-to-code
```

Then ask your coding agent to use the Skill, for example:

```text
Use $tracing-spec-to-code to turn this feature request into an approved spec,
a short roadmap, and a detailed plan for only the next milestone.
```

## Good fit

This Skill is most useful when a change spans several tasks, requirements may
evolve, multiple artifacts must stay aligned, or completion needs defensible
verification evidence. It is intentionally lightweight enough to keep those
controls in Markdown and Git rather than introducing a project-management
platform or a separate workflow database.

It is not an issue tracker, a replacement for code review, or an automatic
release system. It does not install dependencies, rewrite approved facts,
perform remote Git operations, or hide uncertainty behind a guessed result.

## License

MIT. See [`LICENSE`](LICENSE).
