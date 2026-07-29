---
name: tracing-spec-to-code
description: Use when a repository needs deterministic validation of spec, roadmap, milestone plan, or change proposal Markdown artifacts, including configured paths, filename templates, Requirement IDs, task IDs, references, JSON output, or CI exit codes.
---

# Tracing Spec to Code

## Overview

Run the bundled validator instead of guessing repository conventions or substituting ad hoc Markdown searches. M01 validates artifact contracts only; it does not approve gates, rewrite facts, create commits, or install dependencies.

## Validate a repository

From the target repository root, run:

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo .
```

Use a non-default config path only when the repository declares one:

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo . --config config/artifacts.json
```

For CI or other machine consumers, request JSON:

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo . --format json
```

Keep stdout available for the result. Treat stderr as argument, configuration, or runtime diagnostics.

## Interpret the result

| Exit code | Meaning | Next action |
|---|---|---|
| `0` | Validation completed with no issues | Continue the caller's workflow |
| `1` | Validation completed and found issues | Report the stable issue codes and locations |
| `2` | Arguments, configuration, or runtime failed | Report the diagnostic; do not claim artifact validity |

Issues are ordered by path, line, and code. Do not reinterpret a nonzero result as a warning or silently fall back to conventional paths.

## Configuration contract

The default root config is `.tracing-spec-to-code.json`. Omit it to use:

- `docs/specs`, `docs/plans`, and `docs/changes`
- the repository directory name as `feature_slug`
- the filename templates in `assets/templates/config.json`

Configured directories must remain inside the repository. Filename templates must be Markdown basenames with their required placeholders. Invalid JSON, unknown keys, unsafe paths, and invalid templates fail closed.

## Boundaries

- Use Python 3.10+ and the standard library; do not install packages for the validator.
- If the bundled script is missing or cannot run, report that exact blocker. Do not invent a replacement command or infer a pass from manual inspection.
- The validator checks deterministic structure, IDs, and references. It does not judge requirement quality, implementation correctness, test adequacy, or whether a change should be approved.
- Do not read, depend on, or modify unrelated repositories.

## Common mistakes

- Grepping ID-like tokens is not equivalent to running the parser and cross-artifact index.
- Falling back after an invalid config hides configuration defects.
- Exit code `2` means validation did not complete; it is neither pass nor validation issue.
- A clean artifact result is not evidence that product behavior or tests are correct.
