# CP-05 — Defer npx and remote distribution

- 状态：Approved
- 日期：2026-07-30
- Gate Δ：Approved on 2026-07-30
- 触发：M04 design clarification
- Requirements：REQ-TS2C-012, REQ-TS2C-013, REQ-TS2C-014, REQ-TS2C-016
- 影响 Milestone：M04 — Client distribution
- 影响 Task：M04 planning

## Trigger and evidence

M04 brainstorming 曾考虑把第三方 `npx skills` CLI 作为主要 installer，并在当前 milestone 从公开 GitHub repository 执行远程安装矩阵。该方向尚未写入事实源、未实现，也未产生远端操作。

用户随后明确要求先完成本地开发和测试，把 `npx` 测试放入长期目标。继续把 `npx`、npm registry 或 GitHub source 纳入 M04 会违反这一范围决定，并为当前交付引入不必要的网络和第三方 CLI 依赖。

## Proposed delta

1. M04 保留总体设计已定义的 Python 标准库 registry installer：`tools/clients.json` + `tools/install.py`。
2. M04 只从 `skills/tracing-spec-to-code/` 复制到本地目标；测试中的 project root、home root 和客户端目录全部位于临时目录。
3. M04 不运行 `npx`，不下载 npm package，不访问 GitHub，不 push，也不启动真实 agent 客户端。
4. `npx`、公开 GitHub source、固定第三方 CLI 版本、project/user 远程安装矩阵和 clean-environment 验证进入 M05 之后的长期目标；未来必须重新提案和批准。
5. M05 的 Level 1 runtime discovery/minimal workflow 与 Level 2 smoke evidence 边界不变。

## Impact

- Requirements：REQ-TS2C-013–014 继续由 canonical source、registry 和完整目录复制满足；REQ-TS2C-012 的 no-push 边界保持；REQ-TS2C-016 隔离约束不变。
- Milestones/tasks：M04 只规划本地 installer、registry 和隔离测试；不提前详细规划长期目标。
- Implementation：预计新增 `tools/clients.json`、`tools/distribution.py`、`tools/install.py`，不新增 Node/npm package。
- Tests：使用 Python unittest 和临时目录覆盖 8 个客户端的 project/user matrix、内容一致性、冲突保护和失败清理。
- Evidence：M04 不把 `npx`、远程 clone/install 或 GitHub 状态作为完成证据。
- Compatibility/migration：无已发布 installer 或 registry，不需要迁移。
- Security/privacy：测试不读取或写入真实 home/client 目录；不产生网络或远端 mutation。

## Alternatives

1. M04 直接采用第三方 `npx skills`：减少自有安装代码，但引入当前不需要的 Node 版本、网络、上游映射和远程一致性风险。
2. M04 只做 registry validator，不提供复制能力：范围更小，但无法完整验收 REQ-TS2C-014 的 installer 行为。
3. 完全取消跨客户端分发：无法满足已批准 spec。

## Gate Δ

Approved by the user on 2026-07-30.
