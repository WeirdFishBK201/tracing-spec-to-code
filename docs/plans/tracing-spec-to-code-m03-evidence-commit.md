# tracing-spec-to-code M03 Evidence and Commit Plan

> **For agentic workers:** Execute only one task at a time with a fresh bounded context packet and independent spec/quality review at each checkpoint.

- Status: Completed
- Milestone: M03 — Evidence and commit
- Spec: `docs/specs/tracing-spec-to-code-spec.md`
- Roadmap: `docs/plans/tracing-spec-to-code-roadmap.md`
- Design: `docs/design/2026-07-30-tracing-spec-to-code-m03-evidence-commit-design.md`
- Requirements: REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016
- Gate P: Approved on 2026-07-30

## Goal

让 canonical Skill 在 evidence、verification、Gate 和 staged scope 全部通过时创建一个范围准确、可追溯的 milestone commit；任何检查或 Git 操作失败都停止，且永不自动 push。

## Observable outcome

- 只读 `precommit` 能确定性检查 M03 plan evidence、commit scope、Git index 和 commit draft。
- Skill 只 stage plan allowlist 中的精确文件，保留无关 unstaged changes。
- Git identity、权限、hook 或签名失败时不伪造交付、不自动清理 index。
- 成功路径只创建一个 milestone commit，message/trailers 准确，不产生远端操作。

## Non-goals

- 不实现 M04 installer/registry 或客户端分发。
- 不实现 M05 release evaluation、5x wording matrix 或 clean-clone release。
- 不把 validator 变成会执行 `git add`/`git commit` 的强制工作流 CLI。
- 不自动 push、PR、merge、fetch、pull、reset、checkout 或修改远端 refs。

## Architecture and contracts

M03 继续使用“政策核心 + 确定性 validator”：

1. `evidence.py` 解析 milestone plan 的 Traceability、Evidence、Commit scope 和 Commit draft。
2. `git_checks.py` 只读 Git index，并验证 staged set、baseline dirty conflicts 和 message/trailers。
3. `precommit.py` 组合现有 repository validation 与 M03 checks；CLI 只展示 issues。
4. `milestone-commit.md` 指导 Skill 精确 stage、执行一次 commit、验证 HEAD，并 fail closed。

共享接口：

```text
ValidationIssue(code: str, path: Path, line: int, message: str)
EvidenceRecord(plan_path, milestone_id, traceability, task_statuses,
               verifications, approved_proposals, deviations,
               baseline_dirty_paths, commit_scope, commit_message)
parse_evidence(repo_root: Path, plan_path: Path) -> EvidenceRecord
validate_evidence(record: EvidenceRecord, known_plan, approved_proposals) -> list[ValidationIssue]
get_staged_paths(repo_root: Path) -> tuple[Path, ...]
validate_staged_scope(record: EvidenceRecord, staged_paths: tuple[Path, ...]) -> list[ValidationIssue]
validate_commit_message(record: EvidenceRecord) -> list[ValidationIssue]
validate_precommit(repo_root: Path, plan_path: Path, config_path: Path | None = None) -> list[ValidationIssue]
```

CLI contract：

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py precommit \
  --repo . \
  --plan docs/plans/tracing-spec-to-code-m03-evidence-commit.md \
  --format json
```

Exit `0/1/2` 与现有 `validate` 一致；`precommit` 不修改 worktree、index、refs 或 remotes。

稳定 blockers：

| Code | Trigger |
|---|---|
| `EVIDENCE_INCOMPLETE` | Task/traceability/proposal/deviation/baseline evidence 缺失或冲突 |
| `VERIFICATION_NOT_PASSED` | Targeted/broader verification 缺失、失败或未明确 PASS |
| `STAGED_SCOPE_INVALID` | Scope path 非法、与 baseline dirty path 冲突或 staged set 不相等 |
| `COMMIT_MESSAGE_INVALID` | Subject/trailers 格式错误或与 plan/proposals 不匹配 |

## Planned files

实现限于 validator/evidence/Git policy、canonical Skill 路由与文档、M03 scenarios/tests，以及本 plan 和 roadmap；最终精确路径见 Commit scope。

## Tasks

### M03-T01 — Deterministic evidence contract

**Objective:** 解析 milestone evidence，并用稳定 issues 阻止缺失 traceability、未完成 task 或未通过 verification。

**Requirements:** REQ-TS2C-010, REQ-TS2C-016

**Files:** 创建 `scripts/tstc/issues.py`, `scripts/tstc/evidence.py`, `tests/test_evidence.py`；修改 `scripts/tstc/validation.py`, `assets/templates/milestone-plan.md`, `tests/test_validation.py`。

**Interfaces:** 产出共享 `ValidationIssue`、`EvidenceRecord`、`parse_evidence` 和 `validate_evidence`；T02 只消费这些只读结果。

**Testing strategy:** TDD；公共 parser、表格组合和 completion states 属于多状态核心逻辑。

1. 写行为 tests 覆盖完整 evidence、缺失/重复 task rows、unknown Requirement/task、非法 paths、proposal mismatch、targeted/broader PASS/FAIL；确认 RED 来自错误 decision/code。
2. 抽取共享 issue 类型并实现严格 section/table parser；不从任意 prose 猜测 evidence。
3. 实现 `EVIDENCE_INCOMPLETE` 与 `VERIFICATION_NOT_PASSED`，保持 path/line/code 稳定排序。
4. 更新 template，运行 `python -m unittest tests.test_evidence tests.test_validation -v`；预期全部 PASS，旧 M01/M02 validation 不回归。

### M03-T02 — Read-only precommit and staged-scope checks

**Objective:** 在不修改 Git 的前提下验证准确 staged scope、baseline conflicts 和批准的 commit message。

**Requirements:** REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016

**Files:** 创建 `scripts/tstc/git_checks.py`, `scripts/tstc/precommit.py`, `tests/test_git_checks.py`；修改 CLI 与 `tests/test_cli.py`。

**Interfaces:** 消费 T01 `EvidenceRecord`；产出 `get_staged_paths`, `validate_staged_scope`, `validate_commit_message`, `validate_precommit` 和 `precommit --plan`。

**Testing strategy:** TDD + temporary Git integration；Git index、path normalization 和 message trailers 是公共安全边界。

1. 在临时 repositories 写 tests 覆盖 exact staged set、范围外 staged、缺失 scope path、baseline overlap、无关 unstaged preservation、invalid/non-Git repo 和 stable ordering；确认行为 RED。
2. 实现只读 Git subprocess adapter，使用 `-z` 输出和仓库内规范化 paths；Git 无法检查时走 exit `2`，不降级猜测。
3. 实现四类 blocker 与 `precommit --plan` text/JSON schema；验证 subject、Milestone/Requirements/Change-Proposals trailers。
4. 运行 `python -m unittest tests.test_git_checks tests.test_cli -v`；预期全部 PASS，CLI exit `0/1/2` 与 stdout/stderr contract 不回归。

### M03-T03 — Skill commit orchestration and milestone delivery

**Objective:** 让加载 Skill 的 agent 在压力下只 stage 当前 scope、安全 commit，并在 Git 失败时保持未交付。

**Requirements:** REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016

**Files:** 创建 `references/milestone-commit.md`, `tests/scenarios/m03/{scope-pressure,verification-failure,git-failure}.md`；修改 `SKILL.md`, `references/task-execution.md`, `README.md`, `agents/openai.yaml` 和本 plan Evidence。

**Interfaces:** Skill 运行 T02 `precommit --plan`，从批准 plan 读取 exact scope/message，执行 `git --literal-pathspecs add -- <exact paths>` 与一次 `git commit`，再验证 HEAD；禁止普通 pathspec 解释且不调用 remote operations。

**Testing strategy:** Fresh-agent behavior + temporary Git integration；真实执行成功/失败路径，不以 source-token presence 代替行为。

1. 运行未加载新 policy 的加强 controls，记录 scope 混入、跳过 verification 或 Git 失败后的实际 decision/rationale。
2. 编写 commit policy：baseline conflict、精确 staging、precommit gate、一次 commit、HEAD 验证、失败后状态报告、禁止 push/reset。
3. Fresh agents 加载 Skill 在隔离临时 repos 重跑相同场景；成功路径验证一个准确 commit，失败路径验证无 commit/无 push/无自动 index 清理。
4. 更新 README/metadata 和 plan Evidence；运行 Skill validation、targeted/full suite、valid fixture、repository self-validation、隔离扫描和 `git diff --check`。
5. 完成全 milestone spec/quality reviews，核对 staged scope，创建唯一 M03 commit；不 push。

## Milestone verification

```text
python -m unittest tests.test_evidence tests.test_git_checks tests.test_cli tests.test_validation -v
python -m unittest discover -s tests -v
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo tests/fixtures/valid-project
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo . --format json
python C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tracing-spec-to-code
rg -n "VGCCoach2|agentic-workflow" README.md skills/tracing-spec-to-code tests
git diff --check
git status --short
```

预期：tests、Skill validation、valid fixture 和 repository self-validation PASS；隔离扫描无匹配；Git 仅含 M03 scope；不产生 remote operation。

## Traceability

| Task | Requirements | Implementation | Tests |
|---|---|---|---|
| `M03-T01` | `REQ-TS2C-010, REQ-TS2C-016` | `skills/tracing-spec-to-code/scripts/tstc/issues.py, skills/tracing-spec-to-code/scripts/tstc/evidence.py, skills/tracing-spec-to-code/scripts/tstc/validation.py, skills/tracing-spec-to-code/assets/templates/milestone-plan.md` | `tests/test_evidence.py` |
| `M03-T02` | `REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016` | `skills/tracing-spec-to-code/scripts/tstc/git_checks.py, skills/tracing-spec-to-code/scripts/tstc/precommit.py, skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py` | `tests/test_git_checks.py, tests/test_cli.py` |
| `M03-T03` | `REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016` | `skills/tracing-spec-to-code/references/milestone-commit.md, skills/tracing-spec-to-code/SKILL.md, skills/tracing-spec-to-code/references/task-execution.md, README.md, skills/tracing-spec-to-code/agents/openai.yaml` | `tests/scenarios/m03/scope-pressure.md, tests/scenarios/m03/verification-failure.md, tests/scenarios/m03/git-failure.md` |

## Evidence and commit

### Task status

| Task | Status | Actual verification |
|---|---|---|
| `M03-T01` | `Completed` | `58/58 PASS` |
| `M03-T02` | `Completed` | `96/96 PASS` |
| `M03-T03` | `Completed` | `fresh-agents: PASS` |

- Approved proposals: None
- Deviations: None
- Baseline dirty paths: None

### Verification

| Scope | Command | Expected | Actual | Result |
|---|---|---|---|---|
| Targeted | `python -m unittest tests.test_git_checks tests.test_cli tests.test_evidence tests.test_validation` | All pass | `97/97 PASS` | `PASS` |
| Broader | `python -m unittest discover -s tests` | All pass | `117/117 PASS` | `PASS` |
| Skill | `quick_validate.py skills/tracing-spec-to-code` | Valid Skill | `PASS` | `PASS` |
| Fixture | `tracing_spec_to_code.py validate --repo tests/fixtures/valid-project` | No issues | `PASS` | `PASS` |
| Repository | `tracing_spec_to_code.py validate --repo . --format json` | Valid JSON | `PASS` | `PASS` |
| Isolation | `rg -n "VGCCoach2|agentic-workflow" README.md skills/tracing-spec-to-code tests` | No matches | `PASS` | `PASS` |
| Behavior | `fresh-agent M03 pressure scenarios` | Exact success and safe failures | `3/3 PASS` | `PASS` |
| Diff | `git diff --check` | No errors | `PASS` | `PASS` |

### Commit scope

| Path | Purpose |
|---|---|
| `README.md` | Document M03 usage, codes, and boundaries |
| `docs/plans/tracing-spec-to-code-m03-evidence-commit.md` | Persist milestone evidence and commit facts |
| `docs/plans/tracing-spec-to-code-roadmap.md` | Persist approved current milestone state |
| `skills/tracing-spec-to-code/SKILL.md` | Route milestone delivery to commit policy |
| `skills/tracing-spec-to-code/agents/openai.yaml` | Update M03 discovery prompt |
| `skills/tracing-spec-to-code/assets/templates/milestone-plan.md` | Provide canonical evidence tables |
| `skills/tracing-spec-to-code/references/milestone-commit.md` | Define exact safe commit sequence |
| `skills/tracing-spec-to-code/references/task-execution.md` | Invoke milestone commit policy |
| `skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py` | Expose read-only precommit CLI |
| `skills/tracing-spec-to-code/scripts/tstc/evidence.py` | Parse and validate milestone evidence |
| `skills/tracing-spec-to-code/scripts/tstc/git_checks.py` | Inspect staged state and commit draft |
| `skills/tracing-spec-to-code/scripts/tstc/issues.py` | Share stable validation issues |
| `skills/tracing-spec-to-code/scripts/tstc/precommit.py` | Compose repository/evidence/Git checks |
| `skills/tracing-spec-to-code/scripts/tstc/validation.py` | Reuse shared issue sorting |
| `tests/scenarios/m03/git-failure.md` | Pressure-test Git failure behavior |
| `tests/scenarios/m03/scope-pressure.md` | Pressure-test exact scope behavior |
| `tests/scenarios/m03/verification-failure.md` | Pressure-test failed verification behavior |
| `tests/test_cli.py` | Verify precommit CLI exits and schema |
| `tests/test_evidence.py` | Verify canonical evidence behavior |
| `tests/test_git_checks.py` | Verify read-only Git boundaries |

### Commit draft

```text
feat(evidence): enforce safe milestone commits

Milestone: M03 Evidence and commit
Requirements: REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016
```
