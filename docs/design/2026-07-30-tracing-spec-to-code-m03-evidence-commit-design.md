# M03 Evidence and Commit Design

- Status: Approved — reviewed on 2026-07-30
- Date: 2026-07-30
- Milestone: M03 — Evidence and commit
- Requirements: REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016
- Depends on: M02 — Workflow core

## Goal

让 canonical Skill 在 milestone 完成时验证持久 evidence、隔离 staged scope，并安全创建一个可追溯 Git commit；任何 evidence、gate、scope 或 Git 失败都停止，且永不自动 push。

## Approved decisions

1. 采用“只读 validator + Skill 执行 commit”，不把 CLI 扩展为会修改 Git 的工作流引擎。
2. Milestone plan 是 evidence、commit scope 和 commit draft 的唯一机器可检查事实源。
3. Skill 只 stage 明确列出的 milestone paths；范围外 staged files 阻止 commit，无关 unstaged files 保持不变。
4. Commit hash 不写回同一个 milestone commit，避免自引用；实际 hash 只展示在 delivery summary。

## Non-goals

- 不自动 push、创建 PR、merge 或修改远端 refs。
- 不安装或分发 Skill；这些属于 M04。
- 不执行 release evaluation 或客户端矩阵；这些属于 M05。
- 不把所有 Git 操作收进强制状态机，也不自动恢复失败的 index。

## Architecture

### Read-only validator

现有入口增加只读子命令：

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py precommit --repo . --plan docs/plans/tracing-spec-to-code-m03-evidence-commit.md --format json
```

`--plan` 必须是仓库内已发现的 milestone plan，避免 Awaiting handoff 下误选历史 plan。`precommit` 复用现有 artifact/workflow validation，再检查该 plan 的 evidence、commit scope、当前 Git index 和 commit draft。它不执行 `git add`、`git commit` 或任何远端操作。

Exit contract 保持一致：

- `0`：全部确定性检查通过。
- `1`：发现 evidence、verification、scope 或 message issue；结果写 stdout。
- `2`：参数、配置、Git invocation 或 runtime 无法完成；诊断写 stderr。

### Skill orchestration

Skill 负责人工 gate、权限协作和 Git mutation：

1. 确认当前 milestone plan 已获 Gate P，且没有 pending Gate Δ。
2. 在 milestone 开始时记录 baseline dirty paths；运行现有 repository validation 和 evidence validation。
3. 从 plan 的 `Commit scope` 读取精确 paths，只 stage 这些 paths。
4. 运行只读 `precommit` 检查实际 index。
5. 全部通过后执行一次批准的 `git commit`。
6. 读取实际 HEAD 和 commit message，向用户展示 delivery summary。
7. 不 push；任何 Git 失败都停止并报告真实 index/working-tree 状态。

## Milestone plan evidence contract

### Traceability

`## Traceability` 使用一张表，每个 task 恰好一行：

| Task | Requirements | Implementation | Tests |
|---|---|---|---|
| `M03-T01` | `REQ-TS2C-010` | `exact/path.py` | `tests/test_file.py::test_name` |

规则：

- 每个 plan task 都有对应行，不允许未知或重复 task。
- Requirements 必须来自 plan 已声明 requirements。
- Implementation 和 Tests 至少各有一个仓库内相对路径或精确 test reference。
- 路径只作 evidence/allowlist 输入，不要求源码内重复 Requirement ID。

### Task status and verification

`## Evidence and commit` 包含 task status 与 verification tables：

| Task | Status | Actual verification |
|---|---|---|
| `M03-T01` | `Completed` | `tests.test_example`: PASS |

| Scope | Command | Expected | Actual | Result |
|---|---|---|---|---|
| Targeted | `python -m unittest ...` | All pass | 10/10 pass | PASS |
| Broader | `python -m unittest discover -s tests -v` | All pass | 70/70 pass | PASS |

规则：

- 所有 task 必须为 `Completed`。
- 至少一条 targeted 和一条 broader verification 必须显式记录 `PASS`。
- `Pending`、`Skipped`、缺失结果或失败结果都阻止 commit。
- Validator 检查记录是否完整，不判断测试语义是否充分。

### Proposals and deviations

Evidence 必须包含：

```text
Approved proposals: None
Deviations: None
Baseline dirty paths: None
```

存在已批准 proposal 时列出每个 proposal ID；它们必须对应已发现且 `Approved` 的 change proposal。任何 pending proposal 继续由 workflow validation 阻止。

### Commit scope

Evidence 使用精确路径表：

| Path | Purpose |
|---|---|
| `skills/tracing-spec-to-code/scripts/tstc/evidence.py` | Evidence validation |
| `docs/plans/tracing-spec-to-code-m03-evidence-commit.md` | Milestone facts and evidence |

规则：

- 只允许仓库内、规范化后的相对文件路径；不接受目录、glob、`..` 或绝对路径。
- 每个 staged file 必须在表中，每个 scope path 必须实际 staged。
- Plan、roadmap 和当前 milestone 已批准 proposals 必须显式列入 scope。
- Baseline dirty path 与 commit scope 重叠时自动 commit 失败；Skill 不尝试猜测或混合 stage 同一文件中的用户旧改动。
- 范围外 unstaged user changes 可以保留；Skill 不读取、修改、stage 或恢复它们。

### Commit draft

Plan 在 Gate P 前记录：

```text
feat(evidence): enforce safe milestone commits

Milestone: M03 Evidence and commit
Requirements: REQ-TS2C-010, REQ-TS2C-011, REQ-TS2C-012, REQ-TS2C-016
Change-Proposals: CP-05
```

规则：

- Subject 必须符合 `type(scope): outcome`，描述 outcome 而不是文件操作。
- `Milestone` 与 `Requirements` trailers 必填，并匹配当前 plan。
- 仅在存在已批准 proposals 时要求 `Change-Proposals`，且集合必须准确。
- 完成时只允许按已批准事实做最小措辞校正；实质变化需要 Gate Δ。

## Stable issues

M03 增加四个稳定 blocker codes：

| Code | Trigger |
|---|---|
| `EVIDENCE_INCOMPLETE` | Task status、traceability、proposal/deviation 或必需字段缺失/冲突 |
| `VERIFICATION_NOT_PASSED` | Targeted/broader verification 缺失、未 PASS 或记录失败 |
| `STAGED_SCOPE_INVALID` | Commit scope 非法、与 baseline dirty path 冲突，或 staged set 与 scope set 不一致 |
| `COMMIT_MESSAGE_INVALID` | Subject/trailers 缺失、格式错误或与 plan/proposals 不匹配 |

Issues 继续按 path、line、code 稳定排序。

## Git failure behavior

- `git add` 只接收 validator 已解析的精确 paths，并使用参数终止符 `--`。
- Milestone preflight 记录 baseline dirty paths；与计划 scope 重叠时暂停并请求隔离或用户决定。
- Stage 后必须重新读取 index；不依赖预期 scope 推断成功。
- Commit identity、权限、hook、签名、锁或其他失败都原样报告，不声明 milestone delivered。
- Commit 失败后不自动 unstage、reset、checkout 或删除文件；向用户报告 staged/unstaged 状态和下一步。
- Commit 成功后验证 HEAD 已变化，subject/trailers 与批准 draft 一致。
- 不调用 push、PR、merge、fetch、pull 或远端 ref mutation。

## Testing strategy

### Unit and CLI behavior

- Evidence parser 覆盖完整/缺失/重复 task rows、非法 paths、proposal mismatch 和 verification states。
- CLI 覆盖 `precommit` 的 exit `0/1/2`、JSON schema、stdout/stderr 和稳定 issue ordering。
- 公共 parser、Git index 状态与多分支规则使用 TDD。

### Temporary Git integration

每个 test 创建独立临时 repository，并设置本地 test identity：

- 合法 scope 与 evidence 通过只读 `precommit`。
- 范围外 staged file 触发 `STAGED_SCOPE_INVALID`。
- Baseline dirty path 与 milestone scope 重叠时触发 `STAGED_SCOPE_INVALID`，不进行整文件 staging。
- 无关 unstaged file 保持未修改、未 staged。
- 非法 message、pending proposal 或 failed verification 阻止 commit。
- 模拟 failing hook/identity/signing path，验证不伪造 commit，不自动清理 index。
- 成功路径只创建一个 commit，message/trailers 准确，且没有 remote operation。

### Skill pressure behavior

Fresh-agent scenarios 至少组合三种压力，验证 Skill：

- 不因 deadline 或“只是文档”跳过 failed verification。
- 不把无关 user changes 加入 scope。
- 不在 hook/identity 失败后声称 delivered 或尝试 push。

## Acceptance criteria

- 完整 evidence 与精确 staged scope 可由只读 `precommit` 确定性验证。
- 缺失 evidence、失败 verification、pending proposal、范围外 staged file 或非法 message 都返回稳定 blocker。
- Skill 只 stage 当前 milestone paths，成功时创建一个 commit，失败时 fail closed。
- 无关 unstaged changes 保持原样。
- 里程碑开始前已脏且与 scope 重叠的文件不会被自动混入 commit。
- Commit message 满足 subject/trailers contract；实际 hash 只在 delivery summary 展示。
- 没有自动 push、PR、merge 或远端 ref mutation。
- M03 完成时 full suite、temporary Git integrations、Skill validation 和 repository self-validation 全部通过。
