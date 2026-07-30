# CP-04 — Inter-milestone awaiting state

- 状态：Approved
- 日期：2026-07-30
- Gate Δ：Approved on 2026-07-30
- 触发：M02 final delivery validation
- Requirements：REQ-TS2C-004, REQ-TS2C-005, REQ-TS2C-008
- 影响 Milestone：M02 — Workflow core, M03 — Evidence and commit
- 影响 Task：M02-T01, M02-T03

## Trigger and evidence

M02 全部 task 与 verification 已完成，但将 M02 plan 标记为 `Completed` 后，validator 会把 M03 识别为 next incomplete milestone，并因不存在 active M03 plan 报告 `PLAN_NOT_NEXT_MILESTONE`。

这与已批准工作流的交付边界冲突：

- M02 必须以 Completed plan、通过的 repository self-validation 和单一 milestone commit 结束。
- M03 详细 plan 只能在 M02 完成后创建，并需要新的 Gate P。
- 当前 validator 要求 next milestone 始终已有 active plan，因此无法表示“上一 milestone 已完成、下一 milestone 等待规划/批准”的合法状态。

## Proposed delta

增加一个确定性的 inter-milestone awaiting state，不新增 issue code：

1. 当没有 active milestone plan 时，仅在 roadmap `Status`/`状态` 归一化为 `Awaiting`，且 `Current milestone` 等于 roadmap 中 next incomplete milestone 时允许 validation 通过。
2. 其他缺少 active plan 的状态继续报告 `PLAN_NOT_NEXT_MILESTONE`。
3. 一旦 next milestone plan 存在，它仍必须是唯一 active plan，匹配 current/next milestone，并满足现有 roadmap 与 plan Gate P approval checks。
4. M02 交付时把 M02 plan 标记为 `Completed`，roadmap 标记为 `Awaiting Gate P — M03`，只保留 M03 的 roadmap-level 信息；不创建 M03 详细 plan。

## Impact

- Requirements：REQ-TS2C-004 的“最多一个未完成详细 plan”、REQ-TS2C-005 的独立可验证交付、REQ-TS2C-008 的 fail-closed gate 状态。
- Milestones/tasks：M02-T01 validator contract、M02-T03 self-validation，以及 M03 Gate P 前的 handoff。
- Implementation：`skills/tracing-spec-to-code/scripts/tstc/validation.py` 的 zero-active-plan branch；稳定 issue schema 不变。
- Tests：增加合法 Awaiting handoff、非法非 Awaiting zero-active 和后续 active-plan Gate P 回归；重跑 targeted/full/self validation。
- Evidence：M02 plan 记录 CP-04、RED/GREEN、最终验证和 commit metadata。
- Compatibility/migration：现有 active-plan repositories 行为不变；只有此前被拒绝的明确 `Awaiting` handoff 状态变为合法，无数据迁移。
- Security/privacy：无影响。

## Alternatives

1. 在 M02 commit 前创建并批准 M03 详细 plan：违反 next-milestone/Gate P 边界，并把两个 milestone 生命周期耦合。
2. 接受 M02 完成时 self-validation exit `1`：削弱 fail-closed validator 与独立可验证交付。
3. 让 Completed plan 继续伪装为 active：artifact 状态与实际交付不一致，不可接受。

## Gate Δ

Approved by the user on 2026-07-30.
