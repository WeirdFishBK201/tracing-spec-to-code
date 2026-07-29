# tracing-spec-to-code

`tracing-spec-to-code` is a portable agent skill with a deterministic validator for Spec → Plan artifact contracts. M01 validates configured Markdown artifacts, stable Requirement IDs, task IDs, and cross-artifact references using Python's standard library.

## Requirements

- Python 3.10 or newer
- No validator runtime packages

## Run the validator

From this repository:

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo tests/fixtures/valid-project
```

Validate another repository after installing or copying the complete canonical skill directory:

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo <repository>
```

Use JSON for CI:

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo <repository> --format json
```

Use an explicitly declared non-default config:

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo <repository> --config config/artifacts.json
```

An invalid or missing explicit config fails closed; the validator does not fall back to guessed paths.

## Default artifact contract

Without `.tracing-spec-to-code.json`, the validator uses:

```text
docs/specs/<feature>-spec.md
docs/plans/<feature>-roadmap.md
docs/plans/<feature>-mNN-<milestone-slug>.md
docs/changes/<feature>-cpNN-<proposal-slug>.md
```

`<feature>` defaults to the repository directory name. Copy and edit `skills/tracing-spec-to-code/assets/templates/config.json` to override directories, the feature slug, or filename templates. Configured directories must remain inside the repository, and filename templates must remain Markdown basenames with the required placeholders.

Canonical Markdown templates are under `skills/tracing-spec-to-code/assets/templates/`.

## Results

| Exit code | Meaning | Streams |
|---|---|---|
| `0` | Validation completed with no issues | Result on stdout |
| `1` | Validation completed and found issues | Issues on stdout |
| `2` | Arguments, configuration, or runtime failed | Diagnostic on stderr |

JSON results contain:

```json
{
  "issues": [
    {
      "code": "REQ_REFERENCE_UNKNOWN",
      "line": 7,
      "message": "unknown requirement reference: REQ-SAMPLE-999",
      "path": "docs/plans/sample-roadmap.md"
    }
  ],
  "valid": false
}
```

Stable M01 codes:

- Config: `CFG_INVALID_JSON`, `CFG_UNKNOWN_KEY`, `CFG_PATH_OUTSIDE_REPO`, `CFG_TEMPLATE_INVALID`
- Artifacts: `ARTIFACT_MISSING`, `ARTIFACT_PARSE_ERROR`
- Requirements: `REQ_ID_INVALID`, `REQ_ID_DUPLICATE`, `REQ_REFERENCE_UNKNOWN`, `REQ_REFERENCE_MISSING`
- Tasks: `TASK_ID_INVALID`, `TASK_ID_DUPLICATE`

## M01 boundaries

The validator checks deterministic paths, filename templates, required Markdown sections, IDs, current-milestone coverage, and references. It does not judge requirement quality, implementation correctness, test adequacy, approve gates, rewrite facts, install dependencies, or perform Git operations.

The repository is independent of other projects and does not read or modify them.

## Development verification

```text
python -m unittest discover -s tests -v
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo tests/fixtures/valid-project
python C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tracing-spec-to-code
git diff --check
```
