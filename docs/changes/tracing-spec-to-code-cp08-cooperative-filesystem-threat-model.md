# CP-08 — Cooperative filesystem threat model

- 状态：Approved
- 日期：2026-07-30
- Gate Δ：Approved on 2026-07-30
- 触发：M04 final adversarial code-quality review
- Requirements：REQ-TS2C-013, REQ-TS2C-014, REQ-TS2C-016
- 影响 Milestone：M04 — Client distribution
- 影响 Task：M04-T02, M04-T03

## Trigger and evidence

CP-06 和 CP-07 要求 installer 只清理 identity 仍匹配的自有内容，并保留
外部 replacement。最终 quality probe 发现 Python 标准库 path-based API
存在更早的无法封闭窗口：`mkdtemp` 或 `mkdir` 返回后、installer 首次读取
并记录新目录 identity 前，恶意并发 actor 可以移动新目录，并在原路径放入
另一个空目录。

probe 在该窗口移动 workspace 后放入外部 replacement；installer 随后把
replacement 当作自有 workspace，成功安装并在 cleanup 中删除 replacement，
而原 workspace 留在被移动的位置。staged root、parent 和 final target 的
首次 identity capture 具有同类 create-to-first-pin 窗口。

根因不是缺少后续 `stat`：Python 标准库的跨平台 path API 不会在创建目录时
同时返回一个可用于后续 handle-relative 操作的 durable identity。增加更多
path 检查只能移动竞态窗口，不能证明刚创建的 path 未在首次 pin 前被替换。

## Proposed delta

1. M04 的支持边界是 cooperative filesystem：安装期间不得有其他进程或
   agent 恶意或主动变更显式 root、其 parent chain、installer workspace、
   staging 或 final target。
2. installer 继续拒绝已有目标和可检测 collision；首次 pin 后发现 identity
   变化时，只清理仍匹配已记录 ownership 的内容，并保留 replacement 或新增
   内容。
3. installer 不再声称能保护“刚创建 path 在首次 identity capture 前被外部
   替换”的场景；该场景超出 M04 threat model。
4. README 明确要求安装期间不要同时运行会修改相同 root 的客户端 discovery、
   cleanup 工具、文件同步任务或其他 installer。
5. 跨 create-to-first-pin 窗口的恶意并发防护需要 platform-specific native
   directory handles 与 handle-relative operations，作为后续安全强化单独
   提案，不属于 M04。

## Impact

- Behavior：普通单 installer、已有目标、正常 collision 和首次 pin 后可检测
  replacement 的行为不变；恶意并发 filesystem mutation 明确不受支持。
- Architecture：M04 保留零第三方依赖和跨平台 Python 标准库实现，不引入
  native API、extension、advisory lock 或平台分支。
- Tests：保留所有 deterministic race injection、junction、collision、
  ownership cleanup 和 replacement-preservation 测试；不把无法由 path API
  保证的 create-to-first-pin adversarial window 写成虚假通过条件。
- Documentation：收窄 CP-06/CP-07 中过度宽泛的 identity-safe cleanup 表述，
  并记录精确 unsupported boundary。
- Dependencies/network：不新增依赖、网络访问、GitHub 操作或真实客户端写入。
- Milestone：M04 在更新契约、复审和全量验证通过前不得 commit。

## Alternatives

1. 使用 Windows native handles 与 POSIX `mkdirat`/`openat` 风格的
   handle-relative 实现：能建立更强 identity chain，但需要新的跨平台设计、
   代码和测试矩阵，应作为独立安全 milestone。
2. 要求调用者预先创建全部 parent：只能消除部分 parent creation，workspace、
   staging 和 target 仍有 create-to-first-pin 窗口。
3. 继续宣称所有恶意 replacement 都会保留：与可复现证据冲突，不接受。

## Gate Δ

Approved explicitly by the user on 2026-07-30.

## Implementation outcome

M04 production code保持现有 standard-library ownership model。design、README、
plan 和 proposal evidence 现已明确：首次 identity capture 后的 replacement
仍按记录 identity fail closed；首次 capture 前的恶意并发 path replacement
不在 M04 支持范围内。native handle 强化留给后续单独提案。
