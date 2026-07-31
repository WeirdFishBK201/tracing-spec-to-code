# tracing-spec-to-code M04 Client Distribution Design

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- Milestone:M04 — Client distribution
- Requirements:REQ-TS2C-013, REQ-TS2C-014, REQ-TS2C-016
- Roadmap:`docs/plans/tracing-spec-to-code-roadmap.md`
- Change Requests:`docs/changes/tracing-spec-to-code-cr05-defer-npx-distribution.md`, `docs/changes/tracing-spec-to-code-cr06-safe-publication-semantics.md`, `docs/changes/tracing-spec-to-code-cr07-ownership-aware-staging.md`, `docs/changes/tracing-spec-to-code-cr08-cooperative-filesystem-threat-model.md`
- Change approval：CR-05, CR-06, CR-07, and CR-08 Approved on 2026-07-30
- Implementation approval：Approved on 2026-07-30

## Goal

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

## Scope

The approved record retains the documented decision and supporting evidence.

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

## Architecture

```text
skills/tracing-spec-to-code/  canonical source
              |
              v
tools/clients.json  -->  tools/distribution.py  <--  tools/install.py
                              |
                              v
                 <selected root>/<client path>/
                       tracing-spec-to-code/
```

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

## Registry contract

The approved record retains the documented decision and supporting evidence.

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

- Level 1：Codex、Claude Code、GitHub Copilot CLI、Antigravity、Gemini CLI。
- Level 2：Cursor、Windsurf/Cascade、Cline。

The approved record retains the documented decision and supporting evidence.

## Installer interface

The approved record retains the documented decision and supporting evidence.

```text
python tools/install.py --client <id> --scope project --project-root <path>
python tools/install.py --client <id> --scope user --home-root <path>
```

The approved record retains the documented decision and supporting evidence.

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

## Copy and integrity flow

The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

## Testing

The approved record retains the documented decision and supporting evidence.

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

M04 gate：

```text
python -m unittest tests.test_distribution tests.test_install_cli -v
python -m unittest discover -s tests -v
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo .
python C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tracing-spec-to-code
git diff --check
```

The approved record retains the documented decision and supporting evidence.

## Acceptance criteria

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

## Approved decision

The approved record retains the documented decision and supporting evidence.
