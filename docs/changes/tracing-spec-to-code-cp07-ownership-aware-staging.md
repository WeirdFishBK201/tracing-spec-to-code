# CP-07 — Ownership-aware staging transaction

- 状态：Approved
- 日期：2026-07-30
- Gate Δ：Approved on 2026-07-30
- 触发：M04 final cleanup review
- Requirements：REQ-TS2C-013, REQ-TS2C-014, REQ-TS2C-016
- 影响 Milestone：M04 — Client distribution
- 影响 Task：M04-T02, M04-T03

## Trigger and evidence

M04 staging 当前使用 `shutil.copytree`。它能复制完整目录，但不返回每个
新建目录/文件的 identity ownership。cleanup 因此只能按 allowlist 删除：
若外部 actor 在允许路径替换 staged file，cleanup 会误删该替换；若完全
停止 cleanup，则 partial staging 会留下 installer 自己的内容。

独立 Windows probe 已复现外部替换被删除。此前 parent、target publication
已改为逐项 exclusive create 并记录 identity；继续为 `copytree` 添加局部
例外会形成两套不一致的 ownership 模型。

## Proposed delta

1. staging 不再调用 `shutil.copytree`；在 pinned private workspace 内
   exclusive 创建 staged root，并复用 ownership-recording tree copier。
2. source snapshot 决定要复制的完整 distributable topology/files，因此
   runtime cache 仍被过滤，source mutation 仍在发布前复验。
3. 每个 staged directory/file 在创建后记录 identity；partial failure、
   verification failure 和 interruption 只逆序清理 identity 仍匹配的条目。
4. 外部替换、额外路径、非空或 identity 变化的内容不删除；原始错误附带
   cleanup failure 后返回。
5. CLI、registry、8×2 paths、exit code、manifest、`SKILL.md`-last final
   publication 和 CP-06 threat model 均不改变；该 threat model 随后由
   CP-08 基于 create-to-first-pin evidence 明确收窄。

## Impact

- Architecture：staging 与 final publication 使用同一个 exclusive
  ownership model，移除无 ownership evidence 的 `copytree` 边界。
- Implementation：调整 staging orchestration，并让 workspace cleanup
  始终消费精确 identity map。
- Tests：把 copy failure injection 移到 ownership-aware staging boundary；
  新增 partial staging rollback 和 staged external replacement preservation。
- Compatibility：无用户迁移、无 CLI 变化。
- Dependencies/network：不新增依赖、native API 或网络访问。
- Scope：M04 在 Gate Δ、全量回归和最终双重复审通过前不得 commit。

## Alternatives

1. 把 private workspace 内所有 allowlisted path 都视为 installer-owned：
   改动较小，但会删除外部 replacement，违反当前 approved design。
2. 只在完整 copy 后扫描 identity：能保护后续替换，但无法证明 partial-copy
   failure 中已存在条目的 ownership。
3. 缩小 contract，允许 cleanup 删除 private workspace 的外部替换：
   行为更弱，需要另行批准，且与 target/parent ownership 模型不一致。

## Gate Δ

Approved explicitly by the user on 2026-07-30.

## Implementation outcome

M04 staging 复用 exclusive ownership-recording copier；staged root、目录和
文件在创建时记录 identity，partial ownership 即使发生异常也进入 cleanup
map。验证阶段的外部 replacement 会被识别为非本次 ownership，保留原内容
并附加 cleanup failure。原 `shutil.copytree` 边界及其 allowlist-only
cleanup 已移除；CLI、registry、manifest 和依赖边界未改变。
