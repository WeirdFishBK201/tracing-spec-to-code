# tracing-spec-to-code M07 GitHub npx Distribution Plan

- Status: In Progress
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

- [ ] **Step 1: Add documentation contract tests and run RED.** Assert the two
  exact `skills@latest` commands, fixed version, Node floor, repository source,
  offline installer section, absence of the old deferral claim, and MIT
  copyright; run the focused unittest and require behavioral failures against
  the current README and missing license.
- [ ] **Step 2: Rewrite the README and add MIT license.** Lead with product value
  and Quick Start, keep detailed internals in existing docs, preserve accurate
  validator/evaluation boundaries, and add the standard MIT text for
  `Copyright (c) 2026 WeirdFishBK201`.
- [ ] **Step 3: Run documentation GREEN.** Run
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

- [ ] **Step 1: Add tool contract tests and run RED.** Cover exact command
  tuples, isolated HOME/USERPROFILE/XDG/APPDATA values, scope target paths,
  runtime-cache exclusion, mismatch diagnostics, subprocess failure, and CLI
  exit mapping; run the focused tool tests and require failure because the
  module does not exist.
- [ ] **Step 2: Implement the minimal acceptance tool.** Resolve `npx` without a
  shell, create independent temporary roots, force `--copy --yes`, invoke one
  or both scopes, reuse canonical manifest hashing, and emit concise deterministic
  success or error lines without logging unrelated environment values.
- [ ] **Step 3: Run tool GREEN and regression tests.** Run the focused module,
  `python -m unittest tests.test_distribution tests.test_install_cli -v`, and
  `git diff --check`; expect all offline tests to pass without invoking the
  network, followed by read-only spec and code-quality reviews with no blocking
  findings.

### M07-T03 — Fixed-version release acceptance and delivery

**Objective:** Verify the complete local candidate, publish it by normal fast-forward to public `main`, and prove the public GitHub source installs with canonical equality.

**Requirements:** REQ-TS2C-005, REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016, REQ-TS2C-018.

**Files:** Modify
`docs/plans/tracing-spec-to-code-m07-npx-github-distribution.md` with actual
evidence and commit metadata and
`docs/plans/tracing-spec-to-code-roadmap.md` with M07 completion. Git remote
configuration and npm cache entries are external state, not repository files.

**Consumes:** T01 public documentation, T02 acceptance CLI, approved SSH remote,
and the verification commands below.

**Produces:** Local-source and public-source project/global acceptance evidence,
a scoped M07 implementation commit, remote `main` fast-forward delivery, and a
post-push verification result reported to the user.

- [ ] **Step 1: Run pinned local-source acceptance.** With explicit network
  permission, run `python tools/verify_npx_install.py --source . --scope all`;
  expect `skills@1.5.21` project and global copies to match the canonical
  manifest in isolated roots.
- [ ] **Step 2: Run the complete local verification gate.** Run the focused and
  full unittest suites, filtered evaluation validate/summary, valid-fixture and
  repository validation, Skill structure validation, tracked-tree vocabulary
  scan, Python 3.10 grammar check, and `git diff --check`; require all applicable
  checks to pass and preserve zero claimed client results, followed by a final
  read-only spec review with no blocking findings.
- [ ] **Step 3: Record evidence and create the scoped M07 commit.** Update this
  plan with actual commands/results, validate exact staged scope, and commit
  with the approved draft below; do not include unrelated paths.
- [ ] **Step 4: Verify remote ancestry and deliver main.** Configure `origin` as
  `git@github.com:WeirdFishBK201/tracing-spec-to-code.git`, fetch it, require
  the push to be a normal fast-forward, and push the current HEAD to remote
  `main` without force; stop on divergence or authentication failure.
- [ ] **Step 5: Run public GitHub acceptance.** Run
  `python tools/verify_npx_install.py --source WeirdFishBK201/tracing-spec-to-code --scope all`;
  require both isolated scopes and canonical manifests to pass. Report this
  post-push result in the delivery summary; do not fabricate success or create
  another repository artifact solely to record the display result.

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
- `skills@1.5.21` maps Codex global scope to `.codex/skills`; the Python offline
  registry remains unchanged and continues to use its approved explicit-root
  mapping.
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
| `M07-T03` | `REQ-TS2C-005, REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016, REQ-TS2C-018` | `docs/plans/tracing-spec-to-code-m07-npx-github-distribution.md, docs/plans/tracing-spec-to-code-roadmap.md, Git remote main` | Full suite and fixed-version local/public acceptance |

## Evidence and commit

### Task status

| Task | Status | Actual verification |
|---|---|---|
| `M07-T01` | Pending | Pending |
| `M07-T02` | Pending | Pending |
| `M07-T03` | Pending | Pending |

- Approved Change Requests: CR-13
- Deviations: None
- Baseline dirty paths: None

### Verification

| Scope | Command | Expected | Actual | Result |
|---|---|---|---|---|
| Targeted | `python -m unittest tests.test_npx_distribution -v` | All pass | Pending | Pending |
| Distribution | `python -m unittest tests.test_distribution tests.test_install_cli -v` | All pass | Pending | Pending |
| Broader | `python -m unittest discover -s tests -v` | All pass | Pending | Pending |
| Evaluation | Filtered validate and summary | Stable local matrix; zero client PASS | Pending | Pending |
| Validators | Fixture, repository, Skill structure | All valid | Pending | Pending |
| Local npx | Fixed `skills@1.5.21`, local source, both scopes | Canonical equality | Pending | Pending |
| Public npx | Fixed `skills@1.5.21`, GitHub source, both scopes | Canonical equality | Pending | Pending |
| Git | Scope, whitespace, ancestry, non-force push | Exact scope and fast-forward | Pending | Pending |

### Commit scope

| Path | Purpose |
|---|---|
| `LICENSE` | MIT license for public reuse |
| `README.md` | Public Quick Start, offline fallback, and verification contract |
| `docs/plans/tracing-spec-to-code-m07-npx-github-distribution.md` | M07 tasks, evidence, and commit metadata |
| `docs/plans/tracing-spec-to-code-roadmap.md` | M07 sequence and status |
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
