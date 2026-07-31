# CR-13 — Implement public GitHub npx distribution

- Status: Approved
- Change approval: Approved on 2026-07-31
- Date: 2026-07-31
- Requirements: REQ-TS2C-013, REQ-TS2C-014, REQ-TS2C-016, REQ-TS2C-018
- Affected milestone: M07 — GitHub npx distribution
- Affected tasks: M07-T01, M07-T02, M07-T03

## Trigger and evidence

M04 deliberately deferred `npx` and GitHub-source installation through CR-05.
The completed roadmap retained remote package distribution as a long-term goal
requiring a separately approved Change Request after M06. The repository is now
public at `WeirdFishBK201/tracing-spec-to-code`, and the user explicitly asked
to make the Skill installable through the standard `skills` CLI.

The canonical Skill already lives at the discoverable path
`skills/tracing-spec-to-code/SKILL.md`. The selected external CLI supports a
GitHub source, project and global scopes, Codex targeting, copy installation,
and non-interactive execution. Version `1.5.21` is the approved reproducible
acceptance pin; the README may use `@latest` for normal user installation.

Execution evidence confirmed that `skills@1.5.21 --agent codex --global`
copies the Skill to the isolated user's shared
`~/.agents/skills/tracing-spec-to-code/` directory. This corrects the design's
initial `.codex/skills` assumption without changing the approved command,
scope, canonical source, or Python offline-installer contract.

## Proposed change

- Add REQ-TS2C-018 and M07 for public GitHub npx distribution.
- Rewrite the README around the public `npx skills` Quick Start while retaining
  the Python installer as the offline path.
- Add a standard-library acceptance tool that invokes the pinned external CLI
  in isolated project and user roots and compares canonical manifests.
- Add an MIT license with copyright assigned to `WeirdFishBK201`.
- Configure the approved SSH remote and push the verified M07 commits directly
  to `main` only when the update is a normal fast-forward.

## Impact

- Requirements: add REQ-TS2C-018; preserve REQ-TS2C-013, REQ-TS2C-014, and
  REQ-TS2C-016.
- Milestones: reopen the completed roadmap for M07 without rewriting M01-M06
  outcomes or evidence.
- Implementation: add `tools/verify_npx_install.py`; do not modify the Skill
  workflow core or create a project-owned npm package.
- Documentation: update the public README, specification, roadmap, and add the
  M07 plan, this Change Request, design, and MIT license.
- Tests: add offline unit coverage for command, isolation, target, and manifest
  contracts; run real pinned local-source and public-GitHub acceptance
  separately because they require network access.
- Delivery: user-authorized remote configuration, fetch, non-force push to
  `main`, and post-push public-source acceptance are limited to M07.
- Existing boundaries: the Python offline installer remains explicit-root and
  no-overwrite; missing external-client evidence remains unclaimed.

## Alternatives

1. Document `npx skills@latest` without pinned acceptance. Rejected because it
   cannot prove clean project/global installation or canonical equality.
2. Publish a project-owned npm package. Rejected because it duplicates an
   established installer and adds unnecessary release and dependency upkeep.
3. Retain local-clone-only installation. Rejected because it does not meet the
   approved public GitHub installation outcome.

## Migration

No installed Skill or repository artifact migration is required. Existing
local installations continue to work. The README changes the primary public
installation path; the offline installer remains available under a dedicated
section.

## Change approval

Approved by the user on 2026-07-31 after reviewing the complete design. The
approval authorizes M07 planning, implementation, fixed-version network
acceptance, configuration of
`git@github.com:WeirdFishBK201/tracing-spec-to-code.git`, and non-force push to
remote `main`. It does not authorize force push, history rewrite, npm publish,
GitHub Release creation, PR creation, or fabricated client evidence.
