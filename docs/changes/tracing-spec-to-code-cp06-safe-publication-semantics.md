# CP-06 — Safe local publication semantics

- 状态：Approved
- 日期：2026-07-30
- Gate Δ：Approved on 2026-07-30
- 触发：M04-T02 adversarial publication review
- Requirements：REQ-TS2C-013, REQ-TS2C-014, REQ-TS2C-016
- 影响 Milestone：M04 — Client distribution
- 影响 Task：M04-T02, M04-T03

## Trigger and evidence

批准的 M04 design 要求把完整验证后的 sibling staging directory rename
为最终目标，以获得原子发布。同时，批准的 collision contract 要求任何已
存在目标都不得覆盖。

Python 标准库没有跨平台的“directory rename 且 no-replace”统一语义：
POSIX `rename` 可以替换竞态中创建的空目录。adversarial test 证明直接
rename 会违反更强的 existing-target preservation contract。当前实现改为
先用 `mkdir` 独占最终目标，再用 exclusive create 发布内容；这避免覆盖，
但最终目录在完成前可能短暂为空或不完整。该用户可见 atomicity 变化尚未
获得 Gate Δ。

## Proposed delta

1. 保留完整 sibling staging copy 和发布前 manifest/topology 验证。
2. 最终目标只允许通过 exclusive `mkdir` 从不存在状态创建；竞态中出现
   的任何文件或目录都拒绝并保留。
3. staged directories/files 使用 no-overwrite exclusive publication；
   `SKILL.md` 最后发布，降低客户端在内容未齐全时把目标识别为 Skill 的
   可能性。
4. 成功返回前重建并比较完整 final manifest/topology。失败只清理本次
   创建且 identity 仍匹配的内容；外部替换或新增内容不删除。
5. 明确 M04 保证“verified before success”和“never overwrite”，不再
   保证最终目录在整个发布阶段不可见。安装时不应让客户端并发扫描同一
   目标 root。

## Impact

- Behavior：安全优先级从“目录不可见直到单次 rename”调整为“目标绝不
  覆盖，成功前严格验证”；短暂可见窗口会在 README 说明。
- Implementation：保留当前 ownership、junction、TOCTOU 和 cleanup
  防护，新增 `SKILL.md` 最后发布的确定性顺序。
- Tests：增加发布顺序测试；保留 raced empty target、partial failure、
  final verification 和外部替换保护测试。
- Compatibility：CLI、registry、8×2 路径、exit code 和 manifest contract
  不变。
- Dependencies/network：不新增依赖、native extension 或网络访问。
- Milestone：M04 在 Gate Δ 批准和复审通过前不得 commit 或标记交付。
- Threat model：Windows 标准库 path-based create 无法阻止恶意并发替换
  在检测前触发瞬时外部 create；installer 必须检测并 identity-safe 回滚，
  保证返回后不留下本次调用拥有的外部 artifact。要求 zero-transient
  syscall 需要 alternative 2 的 native handle API，不属于本次批准范围。
  CP-08 后续以可复现的 create-to-first-pin 证据收窄此表述：上述 cleanup
  保证只适用于首次 ownership identity 已记录后的可检测 replacement。

## Alternatives

1. 恢复直接 `os.rename`：能缩短可见窗口，但 POSIX 上可能覆盖竞态创建
   的空目标，违反 approved collision contract。
2. 为各 OS 调用不同 native no-replace API：可同时满足两项语义，但扩大
   M04 平台代码和测试矩阵，不适合当前零依赖边界。
3. 只加 advisory lock：外部客户端和非本 installer 进程不会遵守，不能
   提供所需保证。

## Gate Δ

Approved explicitly by the user on 2026-07-30.
