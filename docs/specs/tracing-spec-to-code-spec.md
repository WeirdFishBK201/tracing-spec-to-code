# tracing-spec-to-code Specification

- 状态：Approved
- Gate S：Approved
- 批准日期：2026-07-29
- 设计依据：`docs/design/2026-07-29-tracing-spec-to-code-design.md`
- 产品边界：独立 skill 项目，不读取、不依赖、不修改 VGCCoach2

## 1. 产品目标

`tracing-spec-to-code` 为 agent 提供轻量、可检查的 Spec → Plan → Code 工作流。它通过稳定 ID、人工 gate、受限上下文、行为验证和 milestone commit 保持事实源与实现一致，同时避免重型状态机和过程文档膨胀。

## 2. Requirements

### REQ-TS2C-001 — 固定且可配置的 artifacts

系统必须为 spec、roadmap、当前 milestone plan 和 change proposal 提供固定默认路径与命名，并允许通过根目录 JSON 配置覆盖存放位置。

验收条件：

- 无配置时使用设计文档定义的默认路径。
- 合法配置能够覆盖文档目录和命名模板。
- 配置不能关闭 ID、gate、traceability 或禁止静默偏离规则。
- 无效配置产生明确、可定位的错误，不回退为猜测值。

### REQ-TS2C-002 — 稳定的端到端追溯

系统必须使用稳定 Requirement ID 连接 spec、roadmap milestone、plan task、implementation paths 和 test/verification evidence。

验收条件：

- Requirement ID 默认格式为 `REQ-<FEATURE>-NNN`，创建后不重编号、不复用。
- Plan task ID 默认格式为 `MNN-TNN`。
- Validator 能发现重复、缺失和未知引用。
- 已完成 requirement 能追溯到 task、实现路径和实际验证结果。
- 不强制在每个源码文件中添加 Requirement ID 注释。

### REQ-TS2C-003 — 禁止静默偏离

当 spec、plan、code 或 tests 出现实质不一致时，agent 必须暂停，通过 change proposal 与 Gate Δ 先更新事实源。

验收条件：

- Agent 明确报告不一致及证据。
- 影响分析列出受影响的 requirement、milestone、task、实现和 tests。
- 未经用户批准，不修改高层事实源或继续相关实现。
- 用户沉默不视为批准。
- 仅已批准 proposal 持久化为事实源。

### REQ-TS2C-004 — 只详细规划下一个 milestone

Roadmap 只能简述所有 milestone；详细 plan 只能对应下一个待执行 milestone。

验收条件：

- Roadmap 只包含 milestone outcome、依赖、requirements 和 verification gate。
- 同一 feature 同时最多存在一个未完成的详细 milestone plan。
- 每个 milestone 包含 2–5 个 task，目标值为 3 个，硬上限为 5 个。
- 后续 milestone 在前一 milestone 完成前不展开详细 task。

### REQ-TS2C-005 — 独立可运行与可验证

每个 milestone 和 task 必须留下可运行、可独立验证的仓库状态。

验收条件：

- 每个 task 有单一 outcome、精确范围和 targeted verification。
- 每个 milestone 有不依赖未来实现的 observable outcome。
- Milestone 完成前运行 broader verification。
- 验证失败时不得声明完成。

### REQ-TS2C-006 — 自适应测试策略

系统必须按风险选择轻量行为验证、行为测试或 TDD。

验收条件：

- 一次性脚本、配置和低风险胶水改动可使用真实的轻量行为验证。
- 核心业务、公共 API、复杂状态或复杂 bug 使用行为测试或 TDD。
- Plan 记录策略、理由、命令、预期结果和实际结果。
- 仅测试文件、符号或文本不存在不能构成有效 RED。

### REQ-TS2C-007 — Task 级上下文限制

执行 task 时只加载相关 requirements、当前 plan task、必要代码/tests 和上一 task 的压缩结果。

验收条件：

- 默认不加载完整历史讨论、未来 milestone 细节或无关 spec。
- 上一 task 只传递改动路径、接口变化、验证结果和风险。
- 上下文持续扩大时先重新拆分 task，不无限加载内容。

### REQ-TS2C-008 — 轻量 gates、影响分析与 evidence

系统必须提供 Gate S、Gate P、Gate Δ、影响分析和完成 evidence，但不得引入旧 W-series 式重型状态机。

验收条件：

- Gate S 批准 spec；Gate P 批准 roadmap 与当前 milestone plan；Gate Δ 批准事实变化。
- Milestone plan 持久记录 task 状态、追溯、实际验证、批准的 proposal、偏差和 commit metadata。
- 未知或不确定状态 fail closed。
- 不为每个动作生成独立状态文档。

### REQ-TS2C-009 — Delivery summary 只展示

Milestone delivery summary 默认只展示给用户，不创建单独报告文档。

验收条件：

- 持久 evidence 写入 milestone plan。
- 用户摘要包含 outcome、requirements、主要改动、验证、限制和 commit。
- 摘要可显示下一 milestone 名称，但不展开其详细 plan。

### REQ-TS2C-010 — Milestone 自动 commit

Milestone 全部完成并验证后，系统必须自动创建一个范围准确的 Git commit。

验收条件：

- Commit 前确认所有 task、验证、traceability 和 evidence 完成。
- 只 stage 当前 milestone 文件，不包含用户无关改动。
- 存在未决 Gate Δ 或验证失败时不 commit。
- 每个 milestone 默认只有一个自动 commit。

### REQ-TS2C-011 — 准确简洁的 commit message

Milestone commit 必须使用 `type(scope): outcome`，并包含可追溯 trailers。

验收条件：

- Subject 描述 outcome，不罗列文件操作。
- `Milestone` 与 `Requirements` trailers 必填。
- 存在已批准 proposal 时加入 `Change-Proposals` trailer。
- Gate P 批准 message 草案；完成时只按已批准事实最小校正。

### REQ-TS2C-012 — Git 操作 fail closed

系统不得自动 push；commit 权限、身份、hook 或签名失败时必须停止并报告。

验收条件：

- 不执行自动 push、PR、merge 或远端 ref 修改。
- Git 失败后不伪造成功状态。
- 未完成 commit 时 milestone 保持未交付。

### REQ-TS2C-013 — 单一 canonical skill source

仓库必须只维护一份 canonical skill，客户端适配器不得复制并独立演化 workflow 内容。

验收条件：

- Canonical source 位于 `skills/tracing-spec-to-code/`。
- `SKILL.md` 仅使用广泛支持的 `name` 和 `description` frontmatter。
- 内部资源使用相对路径。
- Validator 只依赖 Python 标准库和 Git。

### REQ-TS2C-014 — 多客户端分发

系统必须支持 registry 驱动的多客户端安装，并区分发布验证与结构兼容级别。

验收条件：

- Level 1：Codex、Claude Code、GitHub Copilot CLI、Antigravity、Gemini CLI。
- Level 2：Cursor、Windsurf/Cascade、Cline。
- Installer 复制完整 canonical skill 目录，已有目标不静默覆盖。
- 新客户端主要通过 registry 增加，不修改 workflow core。

### REQ-TS2C-015 — 无指导基线与压力验证

Skill 发布前必须经过未加载 skill 的基线和加载后的压力场景验证。

验收条件：

- 基线记录 agent 的实际选择和逐字合理化理由。
- 每个压力场景组合至少三种压力。
- 新借口进入规则修订与重测闭环。
- 关键 wording 变体至少重复 5 次。
- Level 1 完成安装、发现和最小流程验证；Level 2 完成结构与 smoke test。

### REQ-TS2C-016 — 项目隔离

本项目必须始终独立于 VGCCoach2。

验收条件：

- 实现、tests、fixtures 和文档不读取或引用 VGCCoach2 的项目内容。
- 不把 VGCCoach2 路径加入工具默认值或测试输入。
- 不以兼容旧 agentic-workflow 为由扩大当前项目范围。

## 3. 非目标

- 通用 issue tracker、项目管理平台或状态数据库。
- 全项目一次性详细实施计划。
- 自动修改已批准事实源。
- 只为留下记录而创建的 delivery report。
- 自动安装 Python、Git 或其他系统依赖。
- 自动 push、PR、merge 或 release。

## 4. 全局约束

- 每次只执行一个 milestone plan。
- 每个 milestone 结束时仓库必须可运行、可验证。
- 未通过人工 gate 不进入下一阶段。
- 所有未知状态默认暂停，不自动猜测。
- 文档与实现使用 UTF-8；命令和路径必须兼容 Windows。
- Python 最低版本建议为 3.10，最终以 Gate P 批准值为准。

## 5. 完成定义

项目完成需要：

- REQ-TS2C-001 至 REQ-TS2C-016 均有 milestone、task、implementation 和 verification evidence。
- Level 1 客户端验证通过且 Level 2 smoke test 有实际记录；或者由 Approved Gate Δ 明确记录行政完成豁免、未验证边界和不得声称的客户端结果。
- 无指导基线、加载后压力测试和 wording micro-tests 完成。
- Canonical skill、validator、installer、文档和发布元数据可从干净 clone 使用。
- 不存在未决 Gate Δ、未解释偏差或未验证完成声明。
