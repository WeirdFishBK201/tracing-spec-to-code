# tracing-spec-to-code M07 GitHub npx Distribution Plan

- Status: Completed
- Milestone: M07 — GitHub npx distribution
- Spec: `docs/specs/tracing-spec-to-code-spec.md`
- Roadmap: `docs/plans/tracing-spec-to-code-roadmap.md`
- Design: `docs/superpowers/specs/2026-07-31-npx-github-distribution-design.md`
- Requirements: REQ-TS2C-013, REQ-TS2C-014, REQ-TS2C-016, REQ-TS2C-018
- Change approval: CR-13 approved on 2026-07-31
- Implementation approval: Approved on 2026-07-31

## Goal

Make the public GitHub repository installable through the standard `skills` CLI, with a user-focused README, MIT license, and pinned isolated acceptance that proves project and Codex global copies equal the canonical Skill.

## Global constraints

- Keep `skills/tracing-spec-to-code/` as the only canonical Skill source.
- Use `skills@latest` only in user-facing install commands; pin repository acceptance to `skills@1.5.21`, which requires Node.js 22.20.0 or newer.
- Do not create a project-owned npm package or add runtime dependencies.
- Keep the normal Python unit suite offline and Windows-compatible.
- Real npx acceptance may write only newly created temporary project and user roots and the external npm cache; it must not use a real Skill directory.
- Preserve the Python offline installer, all external-client evidence boundaries, and REQ-TS2C-016 isolation.
- Execute each task with a fresh scoped worker packet, then a read-only spec review; add code-quality review for T01 and T02 before advancing.
- Configure and push only the approved SSH remote, require a normal fast-forward, and never force-push or rewrite history.

## Tasks

### M07-T01 — Public GitHub installation documentation

**Objective:** Present an accurate public project landing page with standard GitHub npx installation, offline fallback, verified requirements, and MIT licensing.

**Requirements:** REQ-TS2C-013, REQ-TS2C-016, REQ-TS2C-018.

**Files:** Create `LICENSE`; modify `README.md`; create `tests/test_npx_distribution.py`.

**Consumes:** The approved public commands and documentation structure in the M07 design.

**Produces:** Exact README contracts for interactive GitHub installation, non-interactive Codex global installation, `skills@1.5.21` verification, the offline Python installer, and MIT license metadata.

- [x] **Step 1: Add documentation contract tests and run RED.** Assert the two
  exact `skills@latest` commands, fixed version, Node floor, repository source,
  offline installer section, absence of the old deferral claim, and MIT
  copyright; run the focused unittest and require behavioral failures against
  the current README and missing license.
- [x] **Step 2: Rewrite the README and add MIT license.** Lead with product value
  and Quick Start, keep detailed internals in existing docs, preserve accurate
  validator/evaluation boundaries, and add the standard MIT text for
  `Copyright (c) 2026 WeirdFishBK201`.
- [x] **Step 3: Run documentation GREEN.** Run
  `python -m unittest tests.test_npx_distribution.ReadmeContractTests -v`,
  `python tools/install.py --help`, and `git diff --check`; expect all contract
  assertions and existing offline help behavior to pass, followed by read-only
  spec and code-quality reviews with no blocking findings.

### M07-T02 — Pinned isolated npx acceptance tool

**Objective:** Provide a standard-library CLI that verifies fixed-version project and Codex global installations without touching real Skill roots.

**Requirements:** REQ-TS2C-013, REQ-TS2C-014, REQ-TS2C-016, REQ-TS2C-018.

**Files:** Create `tools/verify_npx_install.py`; modify `tests/test_npx_distribution.py`.

**Consumes:** `tools.distribution.build_manifest`, canonical source `skills/tracing-spec-to-code/`, `skills@1.5.21`, and the source argument.

**Produces:** `VERIFIED_SKILLS_VERSION`, `build_command(source, scope, npx_executable)`, `build_isolated_environment(base, user_root)`, `expected_target(project_root, user_root, scope)`, `compare_manifests(source, target)`, `run_scope(source, scope)`, and CLI `--source <value> [--scope project|global|all]` with exit `0` for verified equality, `1` for acceptance failure, and `2` for argument or unexpected runtime failure.

- [x] **Step 1: Add tool contract tests and run RED.** Cover exact command
  tuples, isolated HOME/USERPROFILE/XDG/APPDATA values, scope target paths,
  runtime-cache exclusion, mismatch diagnostics, subprocess failure, and CLI
  exit mapping; run the focused tool tests and require failure because the
  module does not exist.
- [x] **Step 2: Implement the minimal acceptance tool.** Resolve `npx` without a
  shell, create independent temporary roots, force `--copy --yes`, invoke one
  or both scopes, reuse canonical manifest hashing, and emit concise deterministic
  success or error lines without logging unrelated environment values.
- [x] **Step 3: Run tool GREEN and regression tests.** Run the focused module,
  `python -m unittest tests.test_distribution tests.test_install_cli -v`, and
  `git diff --check`; expect all offline tests to pass without invoking the
  network, followed by read-only spec and code-quality reviews with no blocking
  findings.

### M07-T03 — Fixed-version release acceptance and delivery preparation

**Objective:** Verify the complete local candidate and prepare the one scoped
implementation commit for normal fast-forward delivery to public `main`.

**Requirements:** REQ-TS2C-005, REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016, REQ-TS2C-018.

**Files:** Modify
`docs/plans/tracing-spec-to-code-m07-npx-github-distribution.md` with actual
evidence and commit metadata and
`docs/plans/tracing-spec-to-code-roadmap.md` with M07 completion; correct the
observed fixed-version global destination in
`docs/superpowers/specs/2026-07-31-npx-github-distribution-design.md`, and
record that execution evidence in
`docs/changes/tracing-spec-to-code-cr13-github-npx-distribution.md`. Git remote
configuration and npm cache entries are external state, not repository files.

**Consumes:** T01 public documentation, T02 acceptance CLI, approved SSH remote,
and the verification commands below.

**Produces:** Local-source project/global acceptance evidence, a complete local
verification gate, and a scoped M07 implementation commit ready for the
post-commit delivery tail.

- [x] **Step 1: Run pinned local-source acceptance.** With explicit network
  permission, run `python tools/verify_npx_install.py --source . --scope all`;
  expect `skills@1.5.21` project and global copies to match the canonical
  manifest in isolated roots.
- [x] **Step 2: Run the complete local verification gate.** Run the focused and
  full unittest suites, filtered evaluation validate/summary, valid-fixture and
  repository validation, Skill structure validation, tracked-tree vocabulary
  scan, Python 3.10 grammar check, and `git diff --check`; require all applicable
  checks to pass and preserve zero claimed client results, followed by a final
  read-only spec review with no blocking findings.
- [x] **Step 3: Record evidence and prepare the scoped M07 commit.** Update this
  plan with actual commands/results, validate exact staged scope, and use the
  approved draft below for the one implementation commit; do not include
  unrelated paths.

## Post-commit delivery tail

These external actions necessarily follow the commit and are reported only in
the delivery summary so the repository neither predicts their result nor adds
a second evidence-only commit:

1. Configure `origin` as
   `git@github.com:WeirdFishBK201/tracing-spec-to-code.git`, fetch it, require
   the push to be a normal fast-forward, and push the current HEAD to remote
   `main` without force; stop on divergence or authentication failure.
2. Run
   `python tools/verify_npx_install.py --source WeirdFishBK201/tracing-spec-to-code --scope all`;
   require both isolated scopes and canonical manifests to pass. Report the
   actual post-push result without fabricating success or creating another
   repository artifact solely to record it.

## Milestone verification

```text
python -m unittest tests.test_npx_distribution -v
python -m unittest tests.test_distribution tests.test_install_cli -v
python -m unittest discover -s tests -v
python tools/evaluate.py validate --run-type baseline --run-type pressure --run-type wording
python tools/evaluate.py summary --run-type baseline --run-type pressure --run-type wording --format json
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo tests/fixtures/valid-project
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo . --format json
python C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tracing-spec-to-code
python -m compileall -q tools tests skills/tracing-spec-to-code/scripts
python tools/verify_npx_install.py --source . --scope all
python tools/verify_npx_install.py --source WeirdFishBK201/tracing-spec-to-code --scope all
git diff --check
```

Expected observable result: offline tests and validators pass; the pinned CLI
installs project and Codex global copies only into isolated roots; each copy
matches the canonical manifest; the external client summary still records zero
client PASS results; remote `main` advances without force; the public GitHub
source passes the same fixed-version acceptance after push.

## Risks and decisions

- `skills@latest` may change behavior; repository acceptance remains pinned to
  `1.5.21` until an approved update changes the pin and evidence.
- `skills@1.5.21` maps Codex global scope to the isolated user's
  `.agents/skills`; the Python offline registry remains unchanged and
  continues to use its approved explicit-root mapping.
- First acceptance may download the external CLI into npm cache. No npm package
  is added to this repository.
- Public acceptance cannot complete before remote delivery. A passing local
  acceptance does not substitute for the final public-source run.
- Remote divergence, SSH failure, package-download failure, or manifest drift is
  a blocker; do not force, retry with weaker verification, or claim completion.

## Traceability

| Task | Requirements | Implementation | Tests |
|---|---|---|---|
| `M07-T01` | `REQ-TS2C-013, REQ-TS2C-016, REQ-TS2C-018` | `README.md, LICENSE` | `tests/test_npx_distribution.py::ReadmeContractTests` |
| `M07-T02` | `REQ-TS2C-013, REQ-TS2C-014, REQ-TS2C-016, REQ-TS2C-018` | `tools/verify_npx_install.py` | `tests/test_npx_distribution.py::NpxAcceptanceToolTests` |
| `M07-T03` | `REQ-TS2C-005, REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016, REQ-TS2C-018` | `docs/plans/tracing-spec-to-code-m07-npx-github-distribution.md, docs/plans/tracing-spec-to-code-roadmap.md, docs/superpowers/specs/2026-07-31-npx-github-distribution-design.md, docs/changes/tracing-spec-to-code-cr13-github-npx-distribution.md` | `tests/test_npx_distribution.py::NpxAcceptanceToolTests` |

## Evidence and commit

### Task status

| Task | Status | Actual verification |
|---|---|---|
| `M07-T01` | Completed | 7/7 PASS |
| `M07-T02` | Completed | 17/17 PASS |
| `M07-T03` | Completed | 270/270 PASS |

- Approved Change Requests: CR-13
- Deviations: The approved design expected `skills@1.5.21` Codex global scope
  under `.codex/skills`; live isolated acceptance showed the CLI's actual
  Codex-targeted global copy is `~/.agents/skills`. The design, test, and
  verifier were corrected to the observed fixed-version contract without
  changing the documented install command or Python offline registry.
- Baseline dirty paths: None

### Verification

| Scope | Command | Expected | Actual | Result |
|---|---|---|---|---|
| Targeted | `python -m unittest tests.test_npx_distribution -v` | All pass | 17/17 PASS | PASS |
| Distribution | `python -m unittest tests.test_distribution tests.test_install_cli -v` | All pass | 67/67 PASS | PASS |
| Broader | `python -m unittest discover -s tests -v` | All pass | 270/270 PASS | PASS |
| Evaluation | Filtered validate and summary | Stable local matrix; zero client PASS | PASS | PASS |
| Validators | Fixture, repository, Skill structure, vocabulary, Python 3.10 grammar | All valid | PASS | PASS |
| Local npx | Fixed `skills@1.5.21`, local source, both scopes | Canonical equality | PASS | PASS |
| Git | Exact scope, whitespace, and precommit | Exact scope and clean checks | PASS | PASS |

Verification details: distribution and broader suites each had 4 expected
Windows capability skips; evaluation recorded baseline 3, pressure 3, wording
groups 5+5, blocked/failed/open 0, and Level 1/2 client PASS 0/0. The Skill
validator used the existing Python 3.14.5 environment with YAML; Python 3.10
grammar compatibility parsed 26 files through `feature_version=(3, 10)`.
Pinned local npx acceptance emitted `VERIFIED project` and `VERIFIED global`.
The staged scope and `git diff --check` passed; precommit is the final
read-only gate before the commit.

### Commit scope

| Path | Purpose |
|---|---|
| `LICENSE` | MIT license for public reuse |
| `README.md` | Public Quick Start, offline fallback, and verification contract |
| `docs/plans/tracing-spec-to-code-m07-npx-github-distribution.md` | M07 tasks, evidence, and commit metadata |
| `docs/plans/tracing-spec-to-code-roadmap.md` | M07 sequence and status |
| `docs/superpowers/specs/2026-07-31-npx-github-distribution-design.md` | Correct the fixed-version Codex global target to the observed shared Skill directory |
| `docs/changes/tracing-spec-to-code-cr13-github-npx-distribution.md` | Record the observed fixed-version Codex global destination |
| `tests/test_npx_distribution.py` | README and acceptance-tool regression coverage |
| `tools/verify_npx_install.py` | Pinned isolated npx acceptance CLI |

The separately committed design and the CR-13/specification/planning changes
are planning history and are not restaged in the implementation commit unless
their approved status or evidence fields require an M07 completion update.

### Commit draft

```text
feat(distribution): verify public npx skill installation

Milestone: M07 GitHub npx distribution
Requirements: REQ-TS2C-013, REQ-TS2C-014, REQ-TS2C-016, REQ-TS2C-018
Change-Requests: CR-13
```
