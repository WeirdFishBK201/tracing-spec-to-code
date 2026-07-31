# GitHub npx Distribution Design

- Status: Approved design
- Date: 2026-07-31
- Repository: `WeirdFishBK201/tracing-spec-to-code`
- Distribution CLI: `skills`
- Verified CLI version: `1.5.21`

## Context

The repository already maintains one canonical Skill at
`skills/tracing-spec-to-code/` and a zero-third-party-dependency Python
installer for offline installation from a local clone. Remote GitHub and
`npx` distribution were explicitly deferred during M04. The repository is now
public, and users need a conventional one-command installation path without a
project-owned npm package.

The public `skills` CLI discovers `SKILL.md` files under a repository's
`skills/` directory and supports GitHub sources, project and global scopes,
agent selection, copy installation, and non-interactive execution. The current
repository layout is compatible with that discovery model.

## Goals

1. Make the public repository installable through
   `npx skills@latest add WeirdFishBK201/tracing-spec-to-code`.
2. Provide a deterministic acceptance command pinned to `skills@1.5.21`.
3. Verify project-scope and Codex global-scope installation in isolated roots.
4. Prove that each installed Skill matches the canonical distributable content
   by relative path, byte size, and SHA-256 digest.
5. Present the repository as a user-oriented public GitHub project while
   preserving the offline Python installer and its safety contract.
6. Add an MIT license with copyright assigned to `WeirdFishBK201`.

## Non-goals

- Do not create or publish a project-owned npm package.
- Do not add a Node.js runtime dependency to the Skill or validator.
- Do not replace or weaken the existing Python offline installer.
- Do not install into a real user or project Skill directory during acceptance.
- Do not claim unperformed installation results for other clients.
- Do not create compatibility aliases, duplicate Skill trees, or generated
  distribution copies in the repository.
- Do not force-push, rewrite history, create a GitHub Release, or publish to the
  npm registry.

## Public installation contract

The README leads with the interactive source command:

```text
npx skills@latest add WeirdFishBK201/tracing-spec-to-code
```

It also provides a non-interactive Codex global command:

```text
npx skills@latest add WeirdFishBK201/tracing-spec-to-code --skill tracing-spec-to-code --agent codex --global --copy --yes
```

`@latest` is the user-facing convenience channel. Repository acceptance pins
`skills@1.5.21`; a future pin change requires an intentional documentation and
verification update. The verified pin requires Node.js 22.20.0 or newer.

The third-party CLI owns its client destination mapping. At version 1.5.21 it
uses `.agents/skills/tracing-spec-to-code/` for Codex project scope and
`~/.agents/skills/tracing-spec-to-code/` for Codex global scope. The existing
Python installer retains its registry-driven paths and explicit-root contract.

## Acceptance architecture

A zero-third-party-dependency Python acceptance tool orchestrates the fixed CLI
without reimplementing installation:

1. Create a temporary project root and a separate temporary user root.
2. Set user-home environment variables to the temporary user root and override
   Git `core.autocrlf=false` for the child process.
3. Invoke `npx --yes skills@1.5.21 add <source>` with the exact Skill, Codex,
   copy, and non-interactive flags.
4. Run once in project scope and once with `--global`.
5. Locate the expected installed Skill directory for each scope.
6. Compare its distributable manifest with
   `skills/tracing-spec-to-code/`, excluding runtime-only Python cache files.
7. Return failure if the CLI exits nonzero, the target is absent, or any
   relative path, size, or digest differs.

The repository marks `skills/tracing-spec-to-code/**` as `text eol=lf` in
`.gitattributes`. Together with the isolated child Git override, this preserves
repository blob bytes across Windows GitHub clones so manifest verification
remains byte-exact rather than normalizing content during comparison.

The tool accepts a source argument so the same contract covers two gates:

- Pre-push gate: install from the local repository path without GitHub access.
- Post-push gate: install from `WeirdFishBK201/tracing-spec-to-code` to exercise
  public GitHub discovery and download.

The normal Python unit suite remains network-free. Unit tests cover command
construction, isolated environment construction, target resolution, result
classification, and manifest mismatch reporting. Real fixed-version npx
acceptance is an explicit verification command because it downloads and
executes an external CLI.

## Failure and safety behavior

- Every acceptance run uses newly created temporary roots.
- `--copy` prevents symlink behavior from obscuring manifest equality.
- No acceptance command points at the real home directory or current project's
  agent directories.
- The tool reports the failed scope, command exit, missing target, or manifest
  difference and exits nonzero.
- Temporary data is cleaned by the standard-library temporary-directory
  lifecycle.
- Existing Python installer collision refusal and transactional publication are
  unchanged.
- Network, npm package download, remote Git inspection, and Git push remain
  explicit execution-time operations.

## Repository documentation

The README is reorganized around user outcomes:

1. Product summary and supported workflow.
2. Quick Start through the public GitHub source.
3. Codex global and project installation examples.
4. Requirements and verified-version distinction.
5. Validator usage and artifact contract.
6. Offline installation from a local clone.
7. Supported-client and external-verification boundaries.
8. Development and remote acceptance commands.
9. License.

Internal milestone history and low-level installer threat-model detail remain
available in maintained design, plan, and Change Request documents instead of
dominating the public landing page.

## Traceability and change control

M07 adds `REQ-TS2C-018` for public GitHub installation and pinned acceptance.
CR-13 records the approved transition from deferred remote distribution to M07
implementation. The roadmap marks M06 complete and adds M07 as the current
milestone. No M01-M06 historical evidence is rewritten.

## Git delivery

Implementation starts from local `main` commit `db982c5`. The repository remote
is configured as:

```text
git@github.com:WeirdFishBK201/tracing-spec-to-code.git
```

Before pushing, fetch the remote and require the proposed update to be a normal
fast-forward. Run the complete local verification set, push without force to
remote `main`, then run the fixed-version public GitHub acceptance. If the
remote cannot fast-forward safely or remote acceptance fails, stop and report
the exact blocker; do not overwrite remote history or claim completion.

## Verification gates

- Focused unit tests for the npx acceptance tool pass.
- Existing distribution and installer tests pass unchanged.
- The complete Python unit suite passes offline.
- Filtered evaluation validation and summary pass with zero invented client
  results.
- Valid fixture and repository validation pass.
- Skill structure validation passes.
- Local-path fixed-version project and global acceptance pass with canonical
  manifest equality.
- `git diff --check` and tracked-tree vocabulary checks pass.
- Remote `main` is updated without force.
- Public GitHub fixed-version project and global acceptance pass after push.
