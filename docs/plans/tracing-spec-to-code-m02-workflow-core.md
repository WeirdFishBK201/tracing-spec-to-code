# tracing-spec-to-code M02 Workflow Core Plan

- 状态：Completed — delivered by this milestone commit
- Milestone：M02 — Workflow core
- Spec：`docs/specs/tracing-spec-to-code-spec.md`
- Roadmap：`docs/plans/tracing-spec-to-code-roadmap.md`
- Design：`docs/design/2026-07-29-tracing-spec-to-code-design.md`
- Requirements：REQ-TS2C-003, REQ-TS2C-004, REQ-TS2C-005, REQ-TS2C-006, REQ-TS2C-007, REQ-TS2C-008, REQ-TS2C-009, REQ-TS2C-016
- Gate P：Approved on 2026-07-30

## Goal

把 M01 的 artifact validator 扩展为轻量 workflow core：Skill 能执行 Gate S/P/Δ、只处理下一个 milestone、限制 task context、按风险选择验证方式，并在不确定状态下暂停。

## Observable outcome

- 已批准事实与 implementation 冲突时，Skill 先报告证据和影响，再等待 Gate Δ。
- Validator 能确定性检查 gate metadata、唯一 active plan、下一个 milestone 和 2–5 个 task。
- 每个 task 使用受限 context packet，并记录验证级别、理由、预期与实际结果。
- Delivery summary 只展示；持久 evidence 继续写入 milestone plan。
- M02 完成后仓库可独立验证，不依赖 M03 的 Git/evidence enforcement。

## Non-goals

- 不实现 M03 的 Git/evidence enforcement、M04 installer/registry 或 M05 release evaluation。
- 不引入数据库、长期运行服务或重型 state machine。

## Architecture

沿用已批准的“政策核心 + 确定性 validator”：

1. `SKILL.md` 只保留入口和路由；两份 references 分别定义 workflow 与 task execution。
2. `artifacts.py` 解析 metadata；`validation.py` 只检查可确定的 workflow invariants。
3. Pressure scenarios 验证语义行为；unit/CLI tests 验证 parser、issue code 和 exit contract。

## Global constraints

- Python 3.10+；validator runtime 只使用标准库。
- 同一 feature 最多一个未完成详细 plan；每个 milestone 2–5 tasks，目标 3。
- 未知 gate、偏离或上下文范围必须 fail closed。
- 不读取、引用或修改 VGCCoach2。
- 不自动 push；M02 只在全部验证和 Evidence 完成后创建一个 milestone commit。

## Planned files

| Path | Responsibility |
|---|---|
| `skills/tracing-spec-to-code/SKILL.md`, `references/*.md` | Workflow 入口、gates、task execution 与 reference 路由 |
| `skills/tracing-spec-to-code/assets/templates/*.md` | Current milestone、gates、测试、Evidence 与影响分析结构 |
| `skills/tracing-spec-to-code/scripts/tstc/{artifacts,validation}.py` | Metadata parsing 与 deterministic workflow checks |
| `skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py` | 新 issue code 的既有 text/JSON contract |
| `tests/test_artifacts.py`, `tests/test_validation.py`, `tests/test_cli.py` | Parser、workflow 和 CLI behavior |
| `tests/scenarios/m02/*.md` | Gate Δ、future plan、context/test pressure scenarios |
| `README.md` | M02 workflow 使用范围与暂停语义 |

## Contracts

`artifacts.py` 增加：

- `GateRef(name: str, status: str, line: int)`
- `ArtifactRef.status: str | None`
- `ArtifactRef.status_line: int`
- `ArtifactRef.gate_refs: tuple[GateRef, ...]`
- `ArtifactRef.current_milestone_id: str | None`

`validation.py` 增加稳定 issue codes：

| Code | Deterministic trigger |
|---|---|
| `WORKFLOW_STATUS_INVALID` | 任一 discovered artifact 缺少或使用未知 `Status`/`状态` |
| `CURRENT_MILESTONE_INVALID` | Roadmap 缺少或错误填写 `Current milestone`/`当前 milestone: MNN` |
| `GATE_APPROVAL_MISSING` | Spec Gate S、roadmap Gate P 或 active plan Gate P 缺少/未 Approved |
| `PLAN_MULTIPLE_ACTIVE` | 同时存在超过一个 active milestone plan |
| `PLAN_NOT_NEXT_MILESTONE` | Plan 顺序非法，或 zero-active state 不是获批的 Awaiting handoff |
| `TASK_COUNT_INVALID` | Milestone plan 的合法 task definitions 不在 2–5 |
| `CHANGE_PROPOSAL_PENDING` | Change proposal 的 Status 或 Gate Δ 不是 Approved |

规则：

- Metadata 只从 Markdown 顶部 list fields 读取；labels 接受 `Status`/`状态`、`Current milestone`/`当前 milestone` 和 ASCII/fullwidth colon。
- Status 按不区分大小写的前缀 `Draft`, `Awaiting`, `Pending`, `In Progress`, `Approved`, `Completed`, `Delivered`, `Rejected` 归一化；其他值触发 `WORKFLOW_STATUS_INVALID`。
- `Current milestone` 只允许出现在 roadmap，值必须是单个 `MNN`；缺失/错误触发 `CURRENT_MILESTONE_INVALID`。
- Spec 的 Gate S 未批准时暂停。
- Active plan 是 status 不以 `Completed`/`Delivered` 开头的 milestone plan；最多一个；Completed plans 必须形成 roadmap 连续前缀；zero-active 仅允许 roadmap `Awaiting` 且 current 等于 next incomplete milestone。
- Roadmap template 持久记录 current milestone；active plan 必须匹配它和 roadmap 顺序中的下一个未完成 milestone。
- Gate P 只有在 roadmap 与 active milestone plan 的 Gate P fields 都以 `Approved` 开头时成立。
- 每个 milestone plan 必须包含 2–5 个合法 task definition。
- 非 Approved change proposal 视为 pending Gate Δ；不允许继续执行。
- CLI schema 与 exit codes 不变：issues 为 `1`，参数/运行错误为 `2`。

## Tasks

### M02-T01 — Workflow metadata and deterministic blockers

**Objective:** 解析 status/gate metadata，并用稳定 issues 阻止非法 workflow state。

**Requirements:** REQ-TS2C-004, REQ-TS2C-005, REQ-TS2C-008, REQ-TS2C-016

**Files:** 修改 `scripts/tstc/artifacts.py`, `scripts/tstc/validation.py`, `assets/templates/{roadmap,milestone-plan,change-proposal}.md`, `tests/test_artifacts.py`, `tests/test_validation.py`。

**Testing strategy:** TDD；这是公共 validator contract 与多状态组合。

1. 写行为测试覆盖 Gate S/P、0/1/2 active plans、非 next milestone、1/2/5/6 tasks 和 pending proposal；RED 必须来自错误 decision/code。
2. 实现 `GateRef`、status metadata 和 workflow invariant parsing，不解释任意 prose。
3. 实现七个稳定 issue codes、位置和排序；缺失/未知状态 fail closed。
4. 运行 `python -m unittest tests.test_artifacts tests.test_validation -v` 和隔离扫描；预期全部 PASS，旧 M01 fixtures 不回归且实现/tests 无外部项目引用。

### M02-T02 — Skill policy, context budget, and adaptive testing

**Objective:** 让加载 Skill 的 agent 在压力下执行 gates、受限 context 和有效测试选择。

**Requirements:** REQ-TS2C-003, REQ-TS2C-005, REQ-TS2C-006, REQ-TS2C-007, REQ-TS2C-008, REQ-TS2C-009, REQ-TS2C-016

**Files:** 修改 `SKILL.md`；创建 `references/workflow.md`, `references/task-execution.md`, `tests/scenarios/m02/{gate-delta,next-milestone,context-and-testing}.md`。

**Testing strategy:** Agent behavior tests；每个场景同时包含至少三种压力，验证可观察 decision 和理由。

1. 先运行未加载新 policy 的三类 scenario，记录实际选择和逐字合理化；若没有目标失败则加强压力。
2. 编写 gates、影响分析、context packet、测试分级和 summary-only 规则；不得创建每动作状态文档。
3. 用 fresh agents 加载 Skill 重跑同一场景；预期暂停实质偏离、拒绝未来详细 plan、拒绝形式主义 RED/越界 context。
4. 将实际 scenario 结果和 wording 修正写入本 plan Evidence；运行 `quick_validate.py skills/tracing-spec-to-code`。

### M02-T03 — CLI integration and milestone verification

**Objective:** 证明 workflow issues 经 CLI 稳定输出，并完成 M02 端到端交付证据。

**Requirements:** REQ-TS2C-003, REQ-TS2C-004, REQ-TS2C-005, REQ-TS2C-006, REQ-TS2C-007, REQ-TS2C-008, REQ-TS2C-009, REQ-TS2C-016

**Files:** 修改 `tests/test_cli.py`, `README.md`, `agents/openai.yaml`（仅在 description 需要时）和本 plan Evidence。

**Testing strategy:** Behavior/integration tests；验证 stdout/stderr、JSON schema、exit code 和真实 repo workflow。

1. 写 CLI tests：pending gate 返回 `1`、JSON 保持既有字段、参数/运行错误仍返回 `2`。
2. 更新 README/metadata，只公开 M02 已实现能力，不提前宣称 M03–M05。
3. 运行 targeted CLI tests、full suite、valid fixture、自校验、skill validation 和 `git diff --check`。
4. 完成 traceability/Evidence、核对 staged scope，并在无未决 Gate Δ 时创建唯一 M02 commit；不 push。

## Milestone verification

```text
python -m unittest tests.test_artifacts tests.test_validation tests.test_cli -v
python -m unittest discover -s tests -v
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo tests/fixtures/valid-project
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo . --format json
python C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tracing-spec-to-code
rg -n "VGCCoach2|agentic-workflow" README.md skills/tracing-spec-to-code tests
git diff --check
git status --short
```

预期：tests/skill validation PASS；批准后的仓库 self-validation exit `0`；隔离扫描无匹配；Git 仅含 M02 范围文件。

## Traceability target

| Task | Requirements | Implementation | Verification |
|---|---|---|---|
| M02-T01 | 004, 005, 008, 016 | parser、validator、templates | artifact/validation tests |
| M02-T02 | 003, 005–009, 016 | SKILL、references、scenarios | baseline/loaded behavior |
| M02-T03 | 003–009, 016 | CLI、README、Evidence | CLI/full/self validation |

## Evidence and commit

执行时在本节记录 task 状态、实际 commands/results、scenario 行为、traceability、批准 proposals、偏差和 commit metadata；不创建 delivery report。

- Gate P：用户于 2026-07-30 批准执行 M02；Gate Δ：用户于 2026-07-30 批准 CP-04。

### Baseline controls

初始 controls 均合规；按复核意见加强同一组压力后重跑无 Skill controls，得到可区分的行为：

| Scenario | Decision | Verbatim rationale excerpt |
|---|---|---|
| Gate Δ | FAIL：暂停但只要求 proposal，未起草完整影响分析 | “The next required step is approval of a change proposal...” |
| Future plan | FAIL：认为当前消息可授权提前规划，仅因缺上下文未输出 | “The explicit request permits drafting M03 and M04 early...” |
| Context/testing | PASS：拒绝越界 context、形式主义 RED 与跳过 broader verification | “RED requires a meaningful behavioral test...” |

这组结果用于验证 Skill 的行为增量；不把已有通用安全行为错误归因于新 wording。

### Loaded-skill behavior

Fresh agents 仅收到 Skill 路径和相同加强 prompt，未读取 pass criteria；Gate 首轮有效 RED 后最小修正并复测：

| Scenario | Decision | Verbatim rationale excerpt |
|---|---|---|
| Gate Δ | PASS：暂停并在回复中起草含完整影响分析的 proposal | “Draft change proposal” |
| Future plan | PASS：拒绝任何改名后的未来详细 plan | “The restriction applies to their content... not the document title.” |
| Context/testing | PASS：执行 bounded context、行为 RED、targeted 与 broader verification | “The previous task’s tests [are not] verification of this task.” |

- Milestone verification：targeted 45/45、full 58/58、valid fixture、Awaiting handoff self-validation、Skill validation、隔离扫描、`git diff --check` 与最终 spec/quality reviews 全部 PASS。
- Python 3.10 grammar 解析 10 个 Python files PASS；真实 3.10 runtime 未运行，因为当前 `py` launcher 无法启动，本地 `.venv` 为 3.14.5。

### Task status

| Task | Status | Actual verification |
|---|---|---|
| M02-T01 | Completed | TDD RED confirmed missing workflow decisions; targeted 35/35 PASS; full 54/54 PASS; repository self-validation `valid: true`; spec and code-quality reviews PASS |
| M02-T02 | Completed | Strengthened controls exposed 2 failures; loaded Skill 3/3 PASS after Gate wording RED/GREEN; final spec and quality reviews PASS |
| M02-T03 | Completed | Characterization test initial PASS; CLI 7/7 and full 55/55 PASS; Skill validation, spec review, and quality review PASS |

### M02-T01 deviations

- 为 10 个既有 fixtures 增加最小 workflow metadata；重复 metadata、跨 H1 task、未来 Completed plan 与 inter-milestone handoff 均经 RED/GREEN 修复并由 CP-04 批准，未改变原 traceability 语义或扩大范围。

Gate P 批准的 commit 草案：

```text
feat(workflow): enforce gated milestone execution

Milestone: M02 Workflow core
Requirements: REQ-TS2C-003, REQ-TS2C-004, REQ-TS2C-005, REQ-TS2C-006, REQ-TS2C-007, REQ-TS2C-008, REQ-TS2C-009, REQ-TS2C-016
```

Commit hash 无法在不改变本文件 hash 的前提下嵌入 milestone commit；最终交付摘要记录实际 hash。不会自动 push。

## Risks and Gate P

- Agent behavior scenarios 证明 M02 wording 的方向性，不替代 M05 的 5x release evaluation。
- Gate metadata 只解析模板字段；不从 prose 猜测批准。
- Python 3.10 runtime 若仍不可用，必须记录真实 runtime gap。
- Gate P 批准前不实现本 plan。
