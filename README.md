# tracing-spec-to-code

`tracing-spec-to-code` is a portable agent skill and deterministic validator
for Spec → Plan → Evidence contracts. It helps teams keep requirements,
implementation plans, verification evidence, and delivery policy traceable.

## Quick Start

Install the public GitHub Skill interactively:

```text
npx skills@latest add WeirdFishBK201/tracing-spec-to-code
```

Install it for Codex globally without prompts:

```text
npx skills@latest add WeirdFishBK201/tracing-spec-to-code --skill tracing-spec-to-code --agent codex --global --copy --yes
```

The commands use the public repository source
`WeirdFishBK201/tracing-spec-to-code`. The repository acceptance contract is
verified with `skills@1.5.21`, which requires Node.js 22.20.0 or newer. The
user-facing commands intentionally use `skills@latest`; the fixed acceptance
version changes only through an intentional documentation and verification
update.

## Requirements

- Node.js 22.20.0 or newer for the verified `skills` CLI path
- Python 3.10 or newer for the validator and offline installer
- No validator runtime packages

## Offline installation from a local clone

Use the standard-library installer when the repository is already available
locally or network access is not appropriate. Project scope requires the
project root explicitly:

```text
python tools/install.py --client codex --scope project --project-root <project-directory>
```

User scope requires the intended home root explicitly:

```text
python tools/install.py --client codex --scope user --home-root <home-directory>
```

The installer never infers a home directory, contacts the network, installs
dependencies, or writes to a real client root unless that root is supplied. It
copies the complete distributable tree from `skills/tracing-spec-to-code/`,
excluding runtime-only `__pycache__`, `.pyc`, and `.pyo` entries. It verifies a
deterministic SHA-256 manifest and refuses to replace an existing
`tracing-spec-to-code/` target. There is no `--force` option.

For cross-platform no-overwrite safety, the installer claims an absent target
before publishing verified staged content. The directory can therefore be
briefly visible before success; `SKILL.md` is published last. Do not run
client discovery, another installer, a cleanup tool, or a file-sync task that
modifies the same explicit root concurrently with installation.

The installer assumes a cooperative filesystem. It detects identity changes
after recording ownership and preserves non-owned replacements, but Python's
cross-platform standard-library path APIs cannot close the interval between
creating a path and first recording its identity. Protection against a
malicious concurrent filesystem writer requires native handle-relative APIs and
is deferred to a separate security-hardening request.

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
Level 2 describe compatibility evidence, not a promise that every client has
completed live runtime discovery. Live evaluation remains environment-specific.

Installer exit codes:

| Exit code | Meaning |
|---|---|
| `0` | The complete copy was verified |
| `1` | A stable policy error occurred, such as an invalid target or collision |
| `2` | Arguments were invalid or an unexpected runtime error occurred |

## Run the validator

From this repository:

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo tests/fixtures/valid-project
```

Validate another repository after installing or copying the complete canonical
Skill directory:

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

An invalid or missing explicit config fails closed; the validator does not fall
back to guessed paths.

## Evaluation boundaries

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

Detailed offline preparation, immutable recording, CR-09 archive, CR-10
replacement, and external-client boundaries are documented in
`evaluation/README.md`. Client discovery and smoke execution remain
environment-specific verification; this repository does not manufacture a
passing record when a client run was not performed.

## Current boundaries

The validator checks deterministic paths, filename templates, required Markdown
sections, IDs, workflow metadata, references, recorded evidence, staged scope,
and commit message contracts. It reports recorded state but does not grant
approval, judge requirement quality, implementation correctness, test adequacy,
or rewrite facts. The Skill does not perform remote Git operations or claim
external-client results that were not recorded.

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

The canonical Skill source is `skills/tracing-spec-to-code/`. The repository
does not create a project-owned npm package or add runtime dependencies.

## License

MIT. See [`LICENSE`](LICENSE).
