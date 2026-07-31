# tracing-spec-to-code M01 Artifact Contracts Plan

- Status: Completed
- Milestone: M01 — Artifact contracts
- Spec: `docs/specs/tracing-spec-to-code-spec.md`
- Roadmap: `docs/plans/tracing-spec-to-code-roadmap.md`
- Requirements: REQ-TS2C-001, REQ-TS2C-002, REQ-TS2C-016
- Implementation approval: Approved on 2026-07-30
- Change approval: CR-01, CR-02, and CR-03 Approved on 2026-07-30

## Goal

The approved record retains the documented decision and supporting evidence.

## Architecture and constraints

The approved record retains the documented decision and supporting evidence.

- Python 3.10+ standard library、`unittest`、JSON、Markdown、Git。
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

## Planned files

| Path | Responsibility |
|---|---|
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| `skills/tracing-spec-to-code/assets/templates/{config.json,spec.md,roadmap.md,milestone-plan.md,change-request.md}` | Canonical artifact templates |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |

## Interfaces

`config.py`：

- `ResolvedConfig(repo_root, spec_dir, plan_dir, change_dir, feature_slug, spec_filename_template, roadmap_filename_template, milestone_plan_filename_template, change_request_filename_template)`
- `load_config(repo_root: Path, config_path: Path | None = None) -> ResolvedConfig`
- `ConfigError(code, path, message)`

`artifacts.py`：

- `ArtifactKind`: `SPEC`, `ROADMAP`, `MILESTONE_PLAN`, `CHANGE_REQUEST`
- `ArtifactRef(kind, path, requirement_ids, task_ids, referenced_ids)`
- `discover_artifacts(config: ResolvedConfig) -> list[ArtifactRef]`
- `ArtifactParseError(code, path, line, message)`

`validation.py`：

- `ValidationIssue(code, path, line, message)`
- `validate_repository(repo_root: Path, config_path: Path | None = None) -> list[ValidationIssue]`
- The approved record retains the documented decision and supporting evidence.

CLI：

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate [--repo PATH] [--config PATH] [--format text|json]
```

The approved record retains the documented decision and supporting evidence.

Stable issue codes：`CFG_INVALID_JSON`, `CFG_UNKNOWN_KEY`, `CFG_PATH_OUTSIDE_REPO`, `CFG_TEMPLATE_INVALID`, `ARTIFACT_MISSING`, `ARTIFACT_PARSE_ERROR`, `REQ_ID_INVALID`, `REQ_ID_DUPLICATE`, `REQ_REFERENCE_UNKNOWN`, `REQ_REFERENCE_MISSING`, `TASK_ID_INVALID`, `TASK_ID_DUPLICATE`。

## Tasks

### M01-T01 — Configuration and template contract

The approved record retains the documented decision and supporting evidence.

**Requirements:** REQ-TS2C-001, REQ-TS2C-016

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.

**Verify:**

```text
python -m unittest tests.test_config -v
python C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tracing-spec-to-code
```

The approved record retains the documented decision and supporting evidence.

### M01-T02 — Artifact parsing and traceability rules

The approved record retains the documented decision and supporting evidence.

**Requirements:** REQ-TS2C-001, REQ-TS2C-002

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.

**Verify:**

```text
python -m unittest tests.test_artifacts tests.test_validation -v
```

The approved record retains the documented decision and supporting evidence.

### M01-T03 — CLI behavior and integration

The approved record retains the documented decision and supporting evidence.

**Requirements:** REQ-TS2C-001, REQ-TS2C-002

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.
The approved record retains the documented decision and supporting evidence.

**Verify:**

```text
python -m unittest tests.test_cli -v
```

The approved record retains the documented decision and supporting evidence.

## Milestone verification

```text
python -m unittest discover -s tests -v
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo tests/fixtures/valid-project
python C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tracing-spec-to-code
git diff --check
git status --short
```

The approved record retains the documented decision and supporting evidence.

## Traceability target

| Task | Requirements | Implementation | Tests |
|---|---|---|---|
| M01-T01 | REQ-TS2C-001, REQ-TS2C-016 | templates, `config.py`, metadata | `test_config.py` |
| M01-T02 | REQ-TS2C-001, REQ-TS2C-002 | `artifacts.py`, `validation.py` | parser/validator tests、fixtures |
| M01-T03 | REQ-TS2C-001, REQ-TS2C-002 | CLI、SKILL、README | `test_cli.py`、full suite |

## Evidence and commit

The approved record retains the documented decision and supporting evidence.

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

### Task status

| Task | Status | Actual verification |
|---|---|---|
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |
| Approved record | The documented decision and supporting evidence are retained. |

### Final verification

- `.venv\Scripts\python.exe -m unittest discover -s tests -v`：39 tests PASS（Python 3.14.5）。
- `tracing_spec_to_code.py validate --repo tests/fixtures/valid-project`：exit `0`，`OK: no validation issues`。
- `tracing_spec_to_code.py validate --repo . --format json`：exit `0`，`{"issues": [], "valid": true}`。
- `quick_validate.py skills/tracing-spec-to-code`：`Skill is valid!`。
- `ast.parse(..., feature_version=(3, 10))`：10 Python files PASS。
- Independent spec review：PASS；independent code quality review：PASS。
- The approved record retains the documented decision and supporting evidence.

### Deviations

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.

```text
feat(contracts): validate spec-to-code artifacts

Milestone: M01 Artifact contracts
Requirements: REQ-TS2C-001, REQ-TS2C-002, REQ-TS2C-016
Change-Requests: CR-01, CR-02, CR-03
```

The approved record retains the documented decision and supporting evidence.

## Risks and Implementation approval

- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.
- The approved record retains the documented decision and supporting evidence.

The approved record retains the documented decision and supporting evidence.
