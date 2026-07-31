# CP-09 — Reproducible evaluation reruns

- Status: Approved
- Gate Δ: Approved on 2026-07-31
- Date: 2026-07-30
- Trigger: M05-T02 independent code/evidence quality review
- Requirements: REQ-TS2C-015, REQ-TS2C-016
- Affected milestone: M05 — Evaluation and release
- Affected tasks: M05-T01, M05-T02, M05-T04

## Trigger and evidence

M05-T02 的 deterministic validator 接受了当前 16 份 Codex evidence，spec
review 也确认其满足已批准的机械契约；独立 quality review 随后发现该契约不足以
证明 `5x` wording evidence 来自独立运行，也不足以把 baseline/loaded 差异可靠
归因于 Skill：

1. 同一 wording group 的五份记录可以具有相同毫秒时间戳和完全相同的逐字理由；
   当前 validator 只检查数量与环境字段相等，复制一份结果也能形成 `5/5 PASS`。
2. `gate` baseline/loaded pair 使用了不同 runtime surface、model 标识、sandbox
   与 config；当前 validator 不检查 pair 的环境可比性。
3. 两个 wording prompt 是规则陈述，不要求 agent 在压力下完成明确的行为选择；
   规则复述也能被人工记录为目标 decision。
4. 多数记录以 `precise version unavailable` 作为 client/model 身份；字符串相等
   不能证明运行环境固定或支持复现。
5. M05 最终 isolation 命令扫描 `tools` 与 `tests`，但安全检测实现和测试必须包含
   被禁止 token 的字面量，因此该命令会固定误报。

现有 evidence 不覆盖、不删除。T02 在新的 quality gate 通过前不得标记完成，
T03 不得提前开始。

## Proposed delta

### 1. Execution identity

Evidence schema 升级为 version 2，并为每个真实运行增加：

- `attempt_id`：由 `prepare` 使用标准库安全随机源生成，整个 evidence suite 唯一。
- `prepared_at`：`prepare` 生成 template 的 UTC 时间。
- `session_ref`：运行者记录的非敏感、opaque fresh-session 引用；suite 内唯一。
- `runtime_surface`：实际调用 surface，例如固定版本的 Codex CLI。

`recorded_at` 必须晚于 `prepared_at`。同一 wording group 的五次运行必须具有不同
的 `attempt_id`、`session_ref` 和 `recorded_at`；validator 对缺失、重复或时间
逆序 fail closed。

### 2. Comparable environments

T02 rerun 统一使用一个显式 Codex CLI executable、精确 `codex --version`、显式
model selection 和相同 config snapshot。每个 baseline/loaded pair 必须在以下
字段完全相同，仅允许 `skill_loaded` 和运行身份不同：

- `client_id`
- `client_version`
- `model`
- `config`
- `runtime_surface`

同一 wording group 继续要求相同环境，并新增独立运行身份约束。缺少精确版本、
显式 model 或可记录 config 时记为 `blocked`，不得用 `unavailable` 占位后计作
pass。

### 3. Behavioral wording cases

两个 wording cases 改为具体行动请求，并包含：

- 至少三种受控 pressure。
- 明确、有限的 decision options。
- 要求 agent 只返回一个 decision 和理由的 response contract。

Case validator 要求 wording case 声明 decision options、包含 expected decision，
并证明所有 option 与 response contract 均逐字出现在 prompt；仅陈述规则的 prompt
不再满足 schema。

### 4. Archive and rerun

现有 16 份 schema-v1 evidence 保持内容不变，移动到
`evaluation/archive/cp09/` 作为历史记录。Archive 不参与 active suite 计数，
也不得被 `record` 覆盖。

新增 16 份 schema-v2 evidence：

- 三个 baseline 使用 `-02`，各自通过 `rerun_of` 指向对应 `-01`。
- 三个 loaded pressure 使用 `-02`，各自通过 `rerun_of` 指向对应 `-01`。
- 两个 wording group 各新增 `-06` 至 `-10` 五次运行，并按
  `06→01, 07→02, 08→03, 09→04, 10→05` 记录 `rerun_of`。
- 每个 rerun 同时记录 `change_proposal: "CP-09"`。

Validator 只读取 `evaluation/evidence/*.json` 的 active records，不递归读取
archive。它只校验本次 CP-09 的单层 `rerun_of` 映射、archive 原记录存在且内容
仍能按 schema v1 解析；不实现通用 supersession graph。

### 5. Isolation verification

最终 isolation scan 只扫描会携带用户/运行内容的 README、Skill 内容、
evaluation case/runbook 和 evidence。`tools/evaluate.py` 与
`tests/test_evaluation.py` 中的检测器字面量改由 focused unit tests 验证，不再
要求源码对其自身拒绝的 token 零匹配。

## Impact

- Requirements: 不改变 REQ-TS2C-015/016 的产品范围，只强化“可复现证据”和
  isolation gate 的可证明性。
- Implementation: 修改 `evaluation/cases.json`、`tools/evaluate.py`、
  `tests/test_evaluation.py` 和 `evaluation/README.md`。
- Evidence: 原 16 份文件内容不变地移入 `evaluation/archive/cp09/`，active
  evidence 新增 16 份 rerun；archive 与 rerun 都进入 M05 exact commit scope。
- Plan: 更新 M05-T01/T02/T04 contract、验证命令、evidence 表和 commit scope。
- Tests: 先增加复制运行、重复 session、时间逆序、pair 环境不一致、placeholder
  环境、非行为 wording case、archive 误计数和非法 `rerun_of` 的 RED tests。
- External operations: 代码和 fixture 工作保持 offline；16 次真实 Codex CLI
  rerun 在调用前另行申请登录、model/provider、网络和外部 client 执行批准。
- Git: 不创建单独 CP commit；继续遵守 M05 只创建一个最终 milestone commit，
  不 stage、push、PR、merge 或发布。

## Alternatives

1. 只重跑 evidence，不强化 validator：成本较低，但复制记录和不可比 pair 仍能
   通过，缺陷会重复出现，不接受。
2. 接受现有 evidence 并记录例外：无法通过独立 quality review，也不能支持
   release-ready 声明，不接受。
3. 实现通用 supersession graph：可支持未来多轮替换，但 M05 只需要一次确定的
   quality rerun，复杂度和测试面不必要。
4. 删除或覆盖原 16 份 evidence 后重跑：破坏 immutable evidence contract，
   不接受。

## Migration

Schema-v1 evidence 移入 archive 后继续可解析，但不参与 active summary。
Schema-v2 rerun 全部记录并通过前，T02 summary 必须返回
`EVALUATION_INCOMPLETE`；通过后只把 16 个 active reruns 计入 T02 acceptance
count。Archive 的历史数量与 CP-09 关联记录在本提案和 evaluation runbook 中，
不新增 audit summary 命令。

## Gate Δ

Strict rerun direction was approved on 2026-07-30. The simplified
archive-based written proposal was explicitly approved by the user on
2026-07-31.
