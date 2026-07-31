# tracing-spec-to-code

`tracing-spec-to-code` is a portable agent skill with a deterministic validator for Spec → Plan → Evidence contracts. M05 adds reproducible baseline, pressure, and wording evaluation evidence while retaining the M04 verified offline installation, M01 artifact validation, M02 gated workflow, and M03 evidence/commit policy.

## Requirements

- Python 3.10 or newer
- No validator runtime packages

## Install into a local client

Run the installer from a local clone of this repository. Project scope requires
the project root explicitly:

```text
python tools/install.py --client codex --scope project --project-root <project-directory>
```

User scope requires the intended home root explicitly:

```text
python tools/install.py --client codex --scope user --home-root <home-directory>
```

The installer never infers a home directory, contacts the network, installs
dependencies, or writes to a real client root unless that root is supplied.
It copies the complete distributable tree from
`skills/tracing-spec-to-code/`, excluding runtime-only `__pycache__`, `.pyc`,
and `.pyo` entries. It verifies a deterministic SHA-256 manifest and refuses
to replace an existing `tracing-spec-to-code/` target. Remove or relocate an
existing target yourself only after confirming that is intended; there is no
`--force` option.

For cross-platform no-overwrite safety, the installer claims an absent target
before publishing verified staged content. The directory can therefore be
briefly visible before success; `SKILL.md` is published last. Do not run client
discovery, another installer, a cleanup tool, or a file-sync task that modifies
the same explicit root concurrently with installation.

M04 assumes a cooperative filesystem: no other process or agent deliberately
replaces installer-created paths while installation is running. The installer
detects identity changes after it first records ownership and preserves
non-owned replacements, but Python's cross-platform standard-library path APIs
cannot close the interval between creating a path and first recording its
identity. Protection against a malicious concurrent filesystem writer requires
native handle-relative APIs and is deferred to a separate security-hardening
proposal.

Supported client IDs and local layouts:

| Client ID | Level | Project layout | User layout | M04 evidence |
|---|---:|---|---|---|
| `codex` | 1 | `.agents/skills` | `.agents/skills` | Install/discovery-ready layout |
| `claude-code` | 1 | `.claude/skills` | `.claude/skills` | Install/discovery-ready layout |
| `github-copilot` | 1 | `.github/skills` | `.copilot/skills` | Install/discovery-ready layout |
| `antigravity` | 1 | `.agent/skills` | `.gemini/antigravity/skills` | Install/discovery-ready layout |
| `gemini-cli` | 1 | `.gemini/skills` | `.gemini/skills` | Install/discovery-ready layout |
| `cursor` | 2 | `.cursor/skills` | `.cursor/skills` | Structure smoke-tested |
| `windsurf` | 2 | `.windsurf/skills` | `.codeium/windsurf/skills` | Structure smoke-tested |
| `cline` | 2 | `.cline/skills` | `.cline/skills` | Structure smoke-tested |

The final directory is always `<layout>/tracing-spec-to-code/`. Level 1 and
Level 2 describe the M04 compatibility evidence, not a promise that every
client has completed live runtime discovery; live evaluation belongs to M05.

Installer exit codes:

| Exit code | Meaning |
|---|---|
| `0` | The complete copy was verified |
| `1` | A stable policy error occurred, such as an invalid target or collision |
| `2` | Arguments were invalid or an unexpected runtime error occurred |

`npx` and GitHub-source installation are intentionally deferred to a separate
post-M05 long-term goal. M04 performs local, offline installation only.

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

## Run the evaluation checks

Validate the complete recorded evidence set:

```text
python tools/evaluate.py validate
```

The complete command fails closed until every required client record exists.
To reproduce the locally completed baseline, pressure, and wording matrix
without treating unrecorded external-client checks as passing, use:

```text
python tools/evaluate.py validate --run-type baseline --run-type pressure --run-type wording
python tools/evaluate.py summary --run-type baseline --run-type pressure --run-type wording --format json
```

The detailed offline preparation, immutable recording, CP-09 archive, CP-10
replacement, and external-client boundaries are documented in
`evaluation/README.md`. Client discovery and smoke execution remain
environment-specific verification; this repository does not manufacture a
passing record when a client run was not performed.

Before committing a completed milestone, stage only the exact paths recorded in
its approved plan, then run:

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py precommit --repo <repository> --plan <exact-milestone-plan> --format json
```

`precommit` validates canonical traceability, task completion, targeted and
broader verification, approved proposals, baseline dirty paths, exact staged
scope, and the commit draft. It is read-only: the Skill performs the separately
approved `git --literal-pathspecs add -- <exact paths>` and one normal
`git commit`; ordinary pathspec interpretation is prohibited.

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

## M02 workflow contract

The validator checks deterministic workflow metadata and blockers:

- Every artifact has exactly one known `Status`.
- The roadmap has one valid `Current milestone`; Gate S and the roadmap Gate P are `Approved`.
- When an active milestone plan exists, its Gate P is also `Approved`; without one, only the explicit `Awaiting` handoff to the next incomplete milestone is valid.
- At most one unfinished milestone plan exists, and it is the roadmap's next incomplete milestone.
- Every milestone plan defines 2–5 valid task headings under `## Tasks`.
- A change proposal remains blocking until both its status and Gate Δ are `Approved`.

The Skill policy complements these mechanical checks. It requires explicit Gate S/P/Δ approval, pauses material deviations for impact analysis and a change proposal, loads only a bounded task context, chooses behavioral verification or TDD by risk, rejects invalid RED results, and records evidence in the milestone plan while delivering only a summary by default.

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

Stable M02 workflow codes:

- `WORKFLOW_STATUS_INVALID`
- `CURRENT_MILESTONE_INVALID`
- `GATE_APPROVAL_MISSING`
- `PLAN_MULTIPLE_ACTIVE`
- `PLAN_NOT_NEXT_MILESTONE`
- `TASK_COUNT_INVALID`
- `CHANGE_PROPOSAL_PENDING`

Stable M03 evidence and commit codes:

- `EVIDENCE_INCOMPLETE`
- `VERIFICATION_NOT_PASSED`
- `STAGED_SCOPE_INVALID`
- `COMMIT_MESSAGE_INVALID`

## Current boundaries

The validator checks deterministic paths, filename templates, required Markdown sections, IDs, workflow metadata, references, recorded evidence, staged scope, and commit message contracts. It reports recorded state but does not grant approval, judge requirement quality, implementation correctness, test adequacy, or rewrite facts.

The Skill refuses broad staging, failed verification, baseline overlap, Git bypasses, automatic cleanup, and remote operations. A successful local milestone commit does not authorize push, PR, merge, fetch, pull, or remote mutation.

M04 installs the Skill from a local clone without installing dependencies.
M05 records the completed local evaluation matrix and release-candidate
verification. Eight-client live discovery/smoke remains an explicitly
user-owned external verification boundary and is not claimed by the repository.

The repository is independent of other projects and does not read or modify them.

## Development verification

```text
python -m unittest tests.test_distribution tests.test_install_cli -v
python -m unittest tests.test_evaluation -v
python -m unittest discover -s tests -v
python tools/evaluate.py validate --run-type baseline --run-type pressure --run-type wording
python tools/evaluate.py summary --run-type baseline --run-type pressure --run-type wording --format json
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo tests/fixtures/valid-project
python C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tracing-spec-to-code
git diff --check
```
