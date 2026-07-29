# tracing-spec-to-code 设计

- 状态：已批准
- 日期：2026-07-29
- 批准日期：2026-07-29
- 项目：`tracing-spec-to-code`
- 设计范围：独立 Codex skill 及其跨客户端分发方式

## 1. 背景

`tracing-spec-to-code` 用于约束并协助 agent 完成 Spec → Plan → Code 流程。它是一个全新、独立的项目，不读取、不依赖、也不修改 VGCCoach2。

现有工作流需要解决以下问题：

- spec、plan、code 容易在执行中逐渐偏离，且偏离可能未被明确告知用户。
- 全项目详细规划会快速过时，也会让上下文和文档规模失控。
- requirement、plan task、实现和测试之间缺少稳定、可检查的连接。
- 固定测试流程会在简单改动上过重，在复杂业务上又可能不足。
- 不同 agent 客户端的 skill 目录、安装方式和能力不同。
- 旧式重型状态机与大量过程文档提高了使用成本，却不一定提高正确性。

## 2. 目标

### 2.1 核心目标

1. 提供固定默认值且可配置的 spec、roadmap、milestone plan 和 change proposal 结构。
2. 使用稳定 Requirement ID 建立 spec → plan task → implementation/tests 的可追溯关系。
3. 禁止静默偏离；发现事实源与当前工作不一致时，必须暂停并走变更流程。
4. 只详细规划下一个 milestone；每个 milestone 独立可运行、可验证。
5. 根据风险自适应选择行为验证、行为测试或 TDD。
6. 每个 task 仅加载完成它所需的 requirement、plan task 和代码。
7. 保留必要的人工 gate、影响分析、完成证据和交付摘要。
8. milestone 验证通过后自动创建一个范围准确的 Git commit，但不自动 push。
9. 同一份 canonical skill 可分发到 Codex、Claude Code、GitHub Copilot CLI 等客户端。

### 2.2 非目标

- 不建立通用项目管理系统。
- 不维护旧 W-series 风格的重型状态机。
- 不为每个操作生成独立状态文档或交付报告文件。
- 不一次性详细规划全部 milestone。
- 不用“文件或符号尚不存在”充当业务行为的失败测试。
- 不自动 push、创建 PR、合并分支或修改远端。
- 不在本项目中兼容或迁移 VGCCoach2 的历史工作流。

## 3. 架构选择

### 3.1 方案 A：纯提示词 skill

所有规则都写在 `SKILL.md` 和 references 中，由 agent 自行遵守。

优点：

- 实现简单，客户端适配成本低。
- 不需要运行时依赖。

缺点：

- 文件命名、ID 唯一性和追溯完整性无法稳定检查。
- 压力场景下容易被 agent 合理化绕过。
- 不同客户端的执行一致性较弱。

### 3.2 方案 B：强制工作流 CLI

所有状态变更都通过 CLI 完成，CLI 管理 spec、plan、gate、验证和 commit。

优点：

- 规则强制力和可重复性高。
- 机器可检查的行为边界清晰。

缺点：

- 容易演化成重型状态机。
- 对简单项目和不支持完整工具调用的客户端不友好。
- CLI 会成为工作流瓶颈，并增加维护和安装成本。

### 3.3 方案 C：政策核心 + 确定性 validator

skill 负责判断、协作和流程约束；一个仅依赖 Python 标准库的 validator 负责确定性检查。Git 负责版本边界与 milestone commit。

优点：

- 关键规则既可读又可验证。
- 不需要管理完整运行状态。
- 可以渐进支持不同客户端。
- 用户仍然控制 spec、plan 和变更批准。

缺点：

- 客户端必须能够运行 Git，完整体验还需要可用的 Python 运行时。
- skill 与 validator 的职责边界必须保持清晰。

### 3.4 决策

采用方案 C。

政策核心只处理需要语义判断的事项，例如需求澄清、milestone 拆分、测试策略、影响分析和是否需要 Gate Δ。Validator 只处理确定性规则，例如文件路径、ID 格式、引用完整性、任务数量上限和 gate 标记。

Validator 不替用户批准，不推断需求意图，也不自动改写事实源。

## 4. 事实源与文件结构

### 4.1 默认项目文件

使用 skill 的项目默认采用：

```text
.tracing-spec-to-code.json
docs/
├── specs/
│   └── <feature>-spec.md
├── plans/
│   ├── <feature>-roadmap.md
│   └── <feature>-mNN-<milestone-slug>.md
└── changes/
    └── <feature>-cpNN-<change-slug>.md
```

规则：

- `.tracing-spec-to-code.json` 可覆盖文档根目录和命名模板。
- 未提供配置时使用上述固定默认值。
- 配置改变存放位置，不改变 ID、gate、traceability 和禁止静默偏离等语义规则。
- 同一 feature 的文件名使用同一个稳定 `<feature>` slug。
- `NN` 为从 `01` 开始、只递增不复用的两位序号。

### 4.2 事实源层级

事实源优先级从高到低为：

1. 已获批准的 spec。
2. 已获批准的 roadmap。
3. 当前已获批准的 milestone plan。
4. 当前 task 的 implementation 和 tests。

低层内容不得静默改变高层事实。发现不一致时，进入 Gate Δ，不继续实现。

### 4.3 文档职责

**Spec**

- 定义范围、行为需求、约束、验收条件和明确非目标。
- 每项可实现需求都有稳定 Requirement ID。
- 记录 Gate S 的批准状态。

**Roadmap**

- 仅记录 milestone 名称、预期 outcome、依赖和验证 gate。
- 不包含未来 milestone 的详细 task。
- 记录 roadmap 与 Requirement ID 的覆盖关系。

**Milestone plan**

- 只描述当前下一个 milestone。
- 包含 objective、acceptance criteria、2–5 个 task、目标文件、接口约束和验证命令。
- 包含 traceability、完成 evidence、偏差记录和 commit metadata。
- 记录 Gate P 的批准状态。

**Change proposal**

- 只在发现或请求实质变更时创建。
- 描述触发原因、拟议 delta、影响范围、替代方案和迁移影响。
- 只有用户批准后才成为持久事实源，并更新受影响的 spec、roadmap 或 milestone plan。
- 被拒绝或未决的提议不伪装成已批准事实。

## 5. 稳定 ID 与追溯

### 5.1 Requirement ID

默认格式：

```text
REQ-<FEATURE>-NNN
```

示例：

```text
REQ-AUTH-001
REQ-AUTH-002
```

规则：

- ID 创建后不重编号、不复用。
- 需求被替代或废弃时保留 ID，并明确标记状态和替代关系。
- 文案微调不改变 ID；可观察行为或约束变化需要 Gate Δ。
- Validator 检查格式、唯一性和引用是否存在，不判断需求是否正确。

### 5.2 Plan task ID

默认格式：

```text
MNN-TNN
```

示例：

```text
M01-T01
M01-T02
```

每个 task 必须显式列出它消费的 Requirement ID，并给出独立可验证的 outcome。

### 5.3 Implementation 与 tests 的连接

追溯关系集中记录在当前 milestone plan 的 traceability/evidence 表中：

| Task | Requirements | Implementation paths | Test/verification evidence |
|---|---|---|---|
| `M01-T01` | `REQ-AUTH-001` | 精确文件或目录 | 命令、测试名与实际结果 |

原则：

- 不要求在每个源码文件中加入 Requirement ID 注释。
- 测试框架适合时，可在测试名或 metadata 中加入 ID；否则记录精确测试路径和测试名。
- 每个 Requirement ID 必须至少被 roadmap milestone 覆盖。
- 当前 milestone 内声称完成的 Requirement ID 必须连接到 task 和可观察 evidence。
- 路径或测试改变时更新索引，ID 保持稳定。

## 6. 工作流与人工 gates

### 6.1 正常流程

1. 澄清需求并形成 spec。
2. **Gate S**：用户批准 spec。
3. 创建或更新简短 roadmap。
4. 只为下一个 milestone 创建详细 plan。
5. **Gate P**：用户批准 roadmap 和当前 milestone plan。
6. 按 task 逐个执行，每次只加载受限上下文。
7. 完成 milestone 级验证并写入实际 evidence。
8. 检查 traceability、偏差和工作树范围。
9. 自动创建一个 milestone commit。
10. 向用户展示 delivery summary，然后停止。

进入下一 milestone 时使用新的任务或 Goal，重新加载该 milestone 所需事实，不继承完整执行上下文。

### 6.2 Gate Δ：变更与偏离

下列情况必须暂停：

- 用户请求的行为与已批准 spec 不一致。
- plan task 无法满足其引用的 requirement。
- 实现需要修改未计划的公共接口、数据模型或跨模块边界。
- 测试揭示已批准验收条件互相矛盾或不可实现。
- 代码现状使 plan 的关键假设失效。
- 为完成 task 必须扩大 milestone 范围。

暂停后的顺序：

1. 明确指出不一致及其证据。
2. 做影响分析，列出受影响的 Requirement ID、milestone、task、实现和 tests。
3. 提交简洁 change proposal。
4. 等待用户批准、修改或拒绝。
5. 批准后先更新事实源，再继续实现。

不得先改代码、事后补 proposal，也不得把用户沉默视为批准。

### 6.3 非实质偏差

不改变行为、接口、验收条件或范围的小型实现调整，可以记录在 milestone plan 的 deviation/evidence 区域，不触发 Gate Δ。例如同一模块内的文件重排或等价命令替换。

若无法确定偏差是否实质，按实质偏差处理并暂停。

## 7. Milestone 与 task 规模

### 7.1 Milestone 边界

每个 milestone 必须：

- 产生一个用户或开发者可观察的完整 outcome。
- 完成后仓库仍可运行。
- 有独立验证 gate。
- 不依赖未来 milestone 才能证明当前 outcome。
- 包含 2–5 个 task，目标值为 3 个，硬上限为 5 个。

应拆分 milestone 的信号：

- 同时跨越多个独立业务 outcome。
- 需要加载多个无关子系统。
- 预计 task 超过 5 个。
- 验证必须依赖尚未实现的未来能力。
- plan 接近 200 行或 2,500 词并开始损害可读性。

### 7.2 Task 边界

每个 task 应满足：

- 只服务一个明确 outcome。
- 通常聚焦一个模块或一条端到端行为切片。
- 列出精确的相关 Requirement ID 和预期修改范围。
- 有 targeted verification，可单独判断成功或失败。
- 完成后仓库保持可运行、可验证。

如果一个 task 需要同时理解多个无关模块，或无法用一个简短结果描述，应拆分 task 或调整 milestone。

### 7.3 上下文预算

执行 task 时只加载：

1. task 引用的 Requirement ID 及必要上下文。
2. 当前 task 条目和直接依赖的 plan 条目。
3. 实现该 task 必需的代码、tests 和项目规则。
4. 上一 task 的压缩结果：改动路径、接口变化、验证结果和未决风险。

默认不加载：

- 全部历史讨论。
- 未来 milestone 的详细内容。
- 与当前 Requirement ID 无关的 spec 段落。
- 已完成 task 的完整执行记录。

如果完成 task 所需上下文持续扩大，应先检查 task 边界，而不是无限增加上下文。

## 8. 自适应测试策略

### 8.1 风险分类

**轻量行为验证**

适用于一次性脚本、静态配置、简单文档生成或低风险胶水改动。验证必须执行真实行为，例如运行脚本并检查输出、解析配置或执行 smoke test。

**行为测试**

适用于可复用逻辑、集成边界、数据转换和中等风险 bug。测试验证用户或调用方可观察结果，不只检查实现细节。

**TDD**

适用于核心业务规则、公共 API、复杂状态变化、高风险回归和复杂 bug。先构造能因缺少所需行为而失败的测试，再实现最小变更并重构。

### 8.2 禁止形式主义 RED

以下内容不能单独构成有效的 RED：

- 只断言目标文件不存在。
- 只断言函数、类或符号尚未定义。
- 只检查尚未创建的文本片段。
- 测试因导入错误、语法错误或测试环境损坏而失败。

有效 RED 必须证明缺少的是目标行为，且失败原因与 Requirement ID 的验收条件直接相关。

### 8.3 记录方式

每个 task 在 plan 中记录：

- 选择的验证级别。
- 选择理由。
- targeted command 与预期可观察结果。
- 实际 command、结果和必要输出摘要。

Milestone 完成前还要运行 plan 中定义的 broader verification。

## 9. Evidence 与 delivery summary

### 9.1 持久 evidence

实际完成证据追加到当前 milestone plan，而不是创建单独 delivery report。最少包括：

- 每个 task 的完成状态。
- Requirement ID 到实现路径和 tests 的最终映射。
- 实际执行的验证命令及通过/失败结果。
- 已批准 change proposal 的引用。
- 非实质偏差及其理由。
- 最终 commit metadata。

### 9.2 用户可见 delivery summary

Delivery summary 只展示给用户，默认不单独落盘。它包括：

- 完成的 milestone outcome。
- 覆盖的 Requirement ID。
- 主要改动。
- 验证及结果。
- 已知限制或未运行项。
- 自动创建的 commit hash 与 message。
- 下一 milestone 名称，但不展开其详细 plan。

## 10. Milestone 自动 commit

### 10.1 前置条件

只有全部满足时才自动 commit：

- milestone 的所有 task 完成。
- targeted 和 broader verification 均达到 plan 约定。
- traceability 和 evidence 已更新。
- 没有未决 Gate Δ。
- 工作树中的待提交修改均属于当前 milestone。
- 用户的无关改动未被 stage。

任何检查失败都必须停止，不创建部分 commit，也不静默跳过 commit。

### 10.2 Commit message

格式：

```text
type(scope): outcome

Milestone: MNN <milestone-name>
Requirements: REQ-...[, REQ-...]
Change-Proposals: CP-...[, CP-...]
```

规则：

- subject 描述完成后的 outcome，不罗列文件操作。
- `type` 使用项目已有约定；没有约定时采用常见值，如 `feat`、`fix`、`docs`、`refactor`、`test` 或 `chore`。
- `scope` 使用稳定 feature 或模块名。
- `Milestone` 和 `Requirements` trailer 必填。
- 没有 change proposal 时省略对应 trailer。
- subject 与 trailer 在 Gate P 时确定草案，完成时按已批准事实做最小校正。

示例：

```text
feat(auth): enforce session expiry

Milestone: M02 Session expiry
Requirements: REQ-AUTH-004, REQ-AUTH-006
Change-Proposals: CP-01
```

Skill 不自动 push。若 Git 写入权限、身份、hook 或签名失败，工作流保持未完成状态，报告准确错误并等待用户处理。

## 11. Skill 项目结构

GitHub 仓库采用：

```text
tracing-spec-to-code/
├── skills/
│   └── tracing-spec-to-code/
│       ├── SKILL.md
│       ├── agents/
│       │   └── openai.yaml
│       ├── references/
│       ├── assets/
│       │   └── templates/
│       └── scripts/
│           └── tracing_spec_to_code.py
├── tools/
│   ├── install.py
│   └── clients.json
├── docs/
│   └── design/
├── tests/
├── evals/
├── README.md
└── LICENSE
```

`skills/tracing-spec-to-code/` 是唯一 canonical skill source。客户端适配器不得复制并独立维护 workflow 内容。

## 12. 跨客户端兼容

### 12.1 支持级别

**Level 1：发布时验证**

- Codex
- Claude Code
- GitHub Copilot CLI
- Antigravity
- Gemini CLI

**Level 2：结构兼容并进行 smoke test**

- Cursor
- Windsurf/Cascade
- Cline

“支持”表示能安装或发现 skill、加载核心说明并执行最小工作流；不承诺每个客户端具备完全相同的自动化和权限模型。

### 12.2 可移植性约束

- `SKILL.md` frontmatter 只使用广泛支持的 `name` 和 `description`。
- 核心说明不依赖某个客户端独有的 prompt 指令或绝对路径。
- skill 内资源只用相对路径。
- Validator 只依赖 Python 标准库和 Git。
- 客户端不支持自动 hook 时，skill 显式调用 validator。
- 客户端不允许自动 commit 时，必须报告能力降级并请求用户完成 commit；不得声称 milestone 已完整交付。

### 12.3 安装模型

仓库提供 data-driven installer：

- `tools/clients.json` 定义客户端名称、user/project 安装路径和能力。
- `tools/install.py` 将 canonical skill 安装到目标位置。
- 新客户端优先通过 registry 增加适配，不修改 workflow core。
- installer 默认复制完整 skill 目录，不只复制 `SKILL.md`。
- 安装前验证目标，已有内容不静默覆盖。

GitHub Copilot CLI 的推荐 GitHub 安装方式为：

```text
gh skill preview OWNER/tracing-spec-to-code tracing-spec-to-code
gh skill install OWNER/tracing-spec-to-code tracing-spec-to-code --agent github-copilot --scope user
```

项目级安装使用 `--scope project`；正式发布后推荐用 `--pin <tag>` 固定版本。

## 13. Validator 边界与失败策略

Validator 计划检查：

- 配置文件和文档路径是否符合解析后的规则。
- Requirement ID 与 task ID 格式及唯一性。
- roadmap、milestone plan 和 evidence 的引用是否存在。
- 当前详细 milestone plan 是否唯一。
- task 数量是否为 2–5。
- gate 状态是否允许进入下一阶段。
- 完成声明是否具有验证和 traceability evidence。
- commit 前是否存在未决 change proposal 或范围外 staged 文件。

Validator 不检查：

- spec 内容是否符合用户真实意图。
- task 拆分是否在语义上最佳。
- 测试是否充分覆盖所有风险。
- change proposal 是否应获批准。
- commit message 的业务措辞是否优雅。

所有未知或不确定状态都 fail closed：暂停并显示问题，不自动猜测或修复事实源。

## 14. Skill 验证设计

实现 skill 时遵循 `skill-creator` 与 `writing-skills` 的验证规范。

### 14.1 无指导基线

在编写 workflow 指令前，用未加载 skill 的 agent 执行压力场景，记录它的实际选择和逐字合理化理由。基线必须至少暴露一个目标失败行为，否则场景不足以验证 skill。

### 14.2 加载后压力测试

同一场景在加载 skill 后重复，检查 agent 是否：

- 识别 spec/plan/code 不一致并暂停。
- 拒绝跳过 Gate Δ。
- 不提前详细规划未来 milestone。
- 不把形式主义检查当作有效 RED。
- 不加载或修改 task 范围外内容。
- 不在验证失败时 commit。

每个场景组合至少三种压力，例如时间压力、沉没成本、权威指令、疲劳或“只是小改动”的诱因。

### 14.3 合理化闭环

对基线和加载后测试中出现的新借口：

1. 记录逐字表述。
2. 增加明确反例或禁止条款。
3. 重跑相关场景。
4. 检查新文字是否引入可绕过的歧义。

关键规则的 wording micro-test 每个变体至少重复 5 次，以区分稳定改进与偶然服从。

### 14.4 确定性验证

实现阶段还需要：

- `skill-creator` 的结构与 metadata 校验。
- Validator 单元测试和 fixture。
- 跨平台路径与 Git 状态测试。
- Level 1 客户端安装/发现/最小流程验证。
- Level 2 客户端安装结构和 smoke test。
- 无网络环境下的核心流程验证。

## 15. 高层交付顺序

只维护短 roadmap；每次仅详细规划并执行下一个 milestone。

1. **M01 — Artifact contracts**：确定模板、ID、配置和 validator 的最小契约。
2. **M02 — Workflow core**：实现 gates、受限上下文、偏离处理和测试策略说明。
3. **M03 — Evidence and commit**：实现 evidence 校验与安全的 milestone commit 流程。
4. **M04 — Client distribution**：实现 registry installer 和各客户端适配。
5. **M05 — Evaluation and release**：完成基线、压力场景、客户端验证与发布准备。

每个 milestone 必须独立可运行、可验证；后续 milestone 的详细 plan 只能在前一 milestone 完成后创建。

## 16. 设计验收标准

设计获批需确认：

- 架构采用政策核心 + 确定性 validator。
- 文件默认值、可配置边界和事实源层级清晰。
- Requirement ID、task ID 和 evidence 追溯规则可执行。
- Gate S、Gate P、Gate Δ 的暂停与批准语义明确。
- milestone/task 规模和上下文上限能控制执行范围。
- 测试策略能区分轻量验证、行为测试和 TDD。
- milestone commit 的触发、范围、message 和失败行为明确。
- delivery summary 不单独落盘，完成 evidence 写入 milestone plan。
- canonical skill 与客户端 registry 避免多份 workflow 漂移。
- 验证方案包含无指导基线、加载后压力测试和合理化闭环。

本设计已于 2026-07-29 获用户批准。实现仍需先通过 roadmap 与当前 milestone plan 的 Gate P；在此之前不实现 `SKILL.md`、validator、installer 或测试。
