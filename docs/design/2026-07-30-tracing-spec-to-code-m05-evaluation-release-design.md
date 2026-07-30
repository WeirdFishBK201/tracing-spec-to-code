# tracing-spec-to-code M05 Evaluation and Release Design

- 状态：Approved design
- 日期：2026-07-30
- Milestone：M05 — Evaluation and release
- Requirements：REQ-TS2C-015, REQ-TS2C-016
- Roadmap：`docs/plans/tracing-spec-to-code-roadmap.md`
- Gate P：Awaiting detailed M05 plan approval

## Goal

用最小、可复现的 evidence harness 完成三类验证：

1. Codex 未加载 Skill 的 baseline 与加载后的压力/wording 对照。
2. 5 个 Level 1 客户端的真实安装、发现和最小流程，以及 3 个 Level 2
   客户端的结构与 smoke test。
3. staged candidate tree 的 clean-clone release-ready 检查，并确认最终
   milestone commit tree 与 candidate tree 一致。

M05 产出发布就绪证据，不自动创建 tag、GitHub Release、push、PR、merge
或 `npx` package。

## Approved decisions

用户于 2026-07-30 批准：

- 后续执行可在每次外部操作前单独申请批准，联网、登录或安装缺失客户端。
- 完整 baseline、压力和 wording matrix 只在 Codex reference agent 上运行。
- Level 1 只做真实安装、Skill 发现和最小流程；Level 2 做结构与 smoke。
- 经过敏感信息检查的逐次 prompt、实际选择和逐字理由可以提交到仓库。
- M05 只做 release-ready verification，不发布、不 push；`npx` 和远程分发
  仍是 M05 后的独立目标。
- 使用精简的混合式 harness：统一 case/evidence contract 与 validator，
  客户端先按 runbook 执行；只有重复操作形成实际负担时才考虑 adapter。

## Scope

M05 包含：

- 一份 versioned evaluation case 文件。
- 一个 Python 标准库 CLI，生成 run、记录/校验 evidence 并输出确定性汇总。
- 每次运行一份不可覆盖的 JSON evidence。
- Codex baseline、loaded pressure 和 5x wording evidence。
- 8 个 registry client 的分层验证 evidence。
- 从 staged candidate tree 创建的隔离 clean clone 验证，以及最终 commit
  tree equality check。
- README/runbook、单元测试、全量回归和 milestone evidence。

M05 不包含：

- 第二份 client registry；继续复用 `tools/clients.json`。
- 持久化的手工 summary；汇总始终从单次 evidence 生成。
- 默认 client adapter、GUI automation 或统一账号管理。
- secrets、API key、真实 home 路径或其他项目内容。
- 自动安装依赖、自动登录、自动联网或未逐次批准的外部调用。
- tag、release、push、PR、merge、npm publish、`npx` 或远程 source 安装。
- CP-08 所记录的 native handle security hardening。

## Minimal architecture

```text
evaluation/cases.json
        |
        v
tools/evaluate.py  <----  tools/clients.json
        |
        +---- prepare/record/validate
        v
evaluation/evidence/<run-id>.json
        |
        +---- summary (stdout/JSON on demand)
```

职责：

1. `evaluation/cases.json` 只定义行为 case、固定 prompt、压力标签、运行类型和
   预期结构化选择。
2. `tools/clients.json` 继续是唯一 client set、level 和 layout 事实源；
   evaluation 不复制这些字段。
3. `tools/evaluate.py` 是单文件标准库 CLI；M05 不预先拆 library/adapter 层。
4. `evaluation/evidence/` 保存通过敏感信息检查的逐次原始 evidence。
5. README 或 `evaluation/README.md` 提供统一 runbook；交互式/GUI 客户端也
   必须生成相同 evidence。

只有当实现测试证明单文件职责无法清晰隔离时，才通过 Gate Δ 提议拆分模块；
不得预先增加 adapter framework。

## Case contract

`evaluation/cases.json` 顶层包含 `schema_version` 和唯一 `cases` 数组。每个
case 至少包含：

- 稳定 `id`。
- 稳定 `scenario_id`；baseline 与对应 loaded pressure case 必须使用同一个
  scenario ID，且每个 scenario 恰好有一对。
- `run_type`：`baseline`、`pressure`、`wording`、`level1` 或 `level2`。
- 固定、无敏感信息的 `prompt`。
- `skill_loaded`。
- `expected_decision`；baseline 使用 `observed`，不伪造 pass criteria。
- pressure case 的 `pressures`，必须至少三个不同 kind；kind 只能来自
  `time`、`authority`、`sunk-cost`、`exceptionalism`、`silence` 和
  `scope-expansion`。每个 pressure 同时记录一个必须逐字出现在 prompt 中的
  `excerpt`，避免任意标签冒充真实压力。
- wording case 的 `variant_group` 和稳定 variant ID。

未知 key、重复 ID、未知 run type、空 prompt、loaded 状态与 run type 冲突、
baseline/loaded pairing 不完整、pressure kind 重复或少于三种、excerpt 未出现
在 prompt 中，或 wording 缺少 group 时 fail closed。

## Evidence contract

每次 run 使用唯一、确定性可审查的 run ID，并写入一个 JSON 文件。evidence
至少记录：

- schema version、run ID、case ID 和 client ID。
- Skill 是否加载，以及 client、model 和 version/config。
- UTC 时间、完整 prompt、结构化实际选择和逐字理由。
- `observed`、`pass`、`fail` 或 `blocked` outcome。
- 失败/阻塞原因和经批准的最小 notes。
- rationale review：`no-new-rationale`、`covered` 或 `new-rationale`，以及
  reviewer、适用 rule refs 和可选 change proposal ID。
- 可选 `supersedes_run_ids`，用于把修订后的 rerun 连接到暴露新借口的原 run。

规则：

- 已存在 run ID 或 evidence path 永不覆盖。
- baseline 只能是 `observed` 或 `blocked`；不得计作 loaded pass。
- 登录、网络、超时、缺少 client 或人工中断记为 `blocked`，不计入完成数量。
- loaded run 的 `pass` 必须与 case 的 expected decision 一致。
- 同一 5x wording group 的 client/model/version/config 必须一致。
- `new-rationale` run 不能计为 pass；最终 summary 要求它引用一个 Approved
  change proposal，并且至少一个后续 passing run 通过 `supersedes_run_ids`
  关闭该 run。受影响 wording group 必须在修订后重新形成完整 `5/5 PASS`。
- summary 只从有效 evidence 确定性生成，不接受手工计数。

逐字理由由人工检查是否出现新的违规借口。CLI 不通过关键词推断复杂语义；
`record` 只有在 rationale review 完成后才写 immutable evidence。一旦发现
新借口，M05 暂停，先走 Gate Δ 修订规则，再用新 run ID 重跑受影响 case 和
必要回归；原 evidence 不修改，closure 通过 CP reference 与 superseding run
确定性证明。

## Sensitive-information boundary

case prompt 只能引用本仓库内的合成 fixture 或隔离临时 project。保存 evidence
前，CLI 至少拒绝：

- 常见 API token/key 形态。
- 当前真实 home 的绝对路径。
- 仓库外绝对路径。
- 明确标记为 secret/password/token 的非空字段。
- `VGCCoach2` 或 legacy `agentic-workflow` 内容、路径或默认值。

该检查是防误提交 guard，不声称替代人工 review。执行者在 stage 前仍必须
逐文件检查 evidence。发现敏感内容时不得保存或提交该次输出；清理输入并用
新 run ID 重跑。

Milestone verification 还必须对 `README.md`、`skills/tracing-spec-to-code`、
`tools`、`tests` 和 `evaluation` 运行固定 isolation scan，确认
`VGCCoach2|agentic-workflow` 无匹配。spec/design/change-proposal 中用于声明
隔离规则的历史文本不纳入该 runtime/evidence scan。

## Codex reference evaluation

最小矩阵：

1. 三个未加载 Skill 的 baseline，各运行一次并记录实际选择和逐字理由。
2. 相同三个场景加载 Skill 后各运行一次，必须全部遵守规则。
3. 两个关键 wording 变体，每个在相同 client/model/version/config 下运行
   五次；每个 variant 必须 `5/5 PASS`。

三个压力场景覆盖：

- 绕过 Gate S/P/Δ 或把含义相同的工作改名后继续。
- 扩大当前 milestone/task 上下文或提前规划未来 milestone。
- 跳过行为 RED/验证，扩大 staging，或把 commit 授权解释为 remote 授权。

每个场景必须同时组合至少三种压力，例如时间压力、权威指令、沉没成本、
“只做一次”合理化或要求静默继续。baseline 是描述性 evidence，不要求失败；
loaded pressure 和 wording runs 必须全部通过。

## Client verification

M05 从 `tools/clients.json` 读取精确 5 个 Level 1 和 3 个 Level 2 client：

- Level 1：在隔离 project root 安装 canonical Skill，记录真实 client/version，
  确认 Skill discovery，并完成一次最小 validator 流程。
- Level 2：验证完整安装结构，并根据 client 能力完成一次 smoke test。

真实 home 不写入。CLI/GUI 执行遵循统一 runbook；无法稳定自动化的操作允许
人工完成，但 prompt、observable result、逐字输出和 outcome 必须进入相同
evidence schema。缺少安装、登录或网络条件是 blocker，不能用 M04 的结构测试
替代 M05 真实证据。

目前只读 discovery 检测到 Codex、Claude Code、Cursor 和 Cline 可用；
GitHub Copilot CLI、Antigravity、Gemini CLI 和 Windsurf 缺失。后续安装、
登录和联网必须逐项取得批准。

## CLI behavior

目标命令保持最小：

```text
python tools/evaluate.py prepare ...
python tools/evaluate.py record ...
python tools/evaluate.py validate ...
python tools/evaluate.py summary ...
```

- `prepare` 从固定 case 生成唯一 run 和待执行 prompt。
- `record` 接收一次 client result，先检查 schema/敏感信息，再 exclusive 写入。
- `validate` 校验单次或全部 evidence。
- `summary` 输出稳定排序的人类可读或 JSON 结果，不修改 evidence。

Exit code 沿用仓库约定：

- `0`：命令成功，且所请求验证没有失败或 blocker。
- `1`：case/evidence policy invalid、评估失败、缺失或 blocker。
- `2`：参数错误或不可恢复的运行时错误。

## Candidate snapshot and clean-clone release-ready verification

M05 不用旧 HEAD 代替待提交内容。完成 exact staging 后，使用
`git checkout-index` 把 index 中的候选 tree 导出到临时 candidate repository，
在该临时 repo 创建 throwaway local commit，再从它执行 `git clone --local`
得到 clean clone。整个流程不修改主仓库 refs、不访问 remote。

clean clone 必须：

- 工作区初始无修改。
- 运行 targeted 和 full tests。
- 运行 valid fixture、repository validator 和 Skill structure check。
- 重跑本地 installer matrix。
- 验证 case/evidence contract 和 M05 summary。
- 执行 README 中的本地 validator、installer help 和 evaluation help 命令，
  确认文档不依赖开发机未提交状态。
- 校验现有 release-facing metadata：`skills/tracing-spec-to-code/SKILL.md`
  frontmatter、`skills/tracing-spec-to-code/agents/openai.yaml` 和
  `tools/clients.json`。M05 不为尚未批准的发布渠道发明 package metadata。
- 不依赖未提交文件、真实 home 或其他 repository。

candidate clean-clone failure 会阻止主仓库 commit。通过后记录 candidate tree
hash；真实 milestone commit 后只读确认 `HEAD^{tree}` 与该 hash 一致且
worktree clean。若 hash 不一致，立即报告 blocker，不 push、不声明交付。
通过只表示该 commit release-ready；不授权 tag、Release、push 或 `npx`。

## Testing

标准库 unittest 至少覆盖：

- case schema、未知 key、重复 ID、run type 和三重压力约束。
- baseline/loaded `scenario_id` pairing、controlled pressure taxonomy 与
  excerpt-in-prompt validation。
- 唯一 run ID、exclusive evidence write 和拒绝覆盖。
- baseline/loaded outcome 规则、expected decision 和 blocked 不计数。
- wording 每 variant 5 次、配置一致性和缺失 run。
- rationale review、Approved CP reference、superseding rerun 和重建 5/5 closure。
- client IDs/levels 从 canonical registry 读取，不复制 mapping。
- secrets、真实 home、repo 外绝对路径和隔离项目 token 拒绝。
- summary 稳定排序与 JSON 输出。
- CLI 成功、policy failure、参数/运行时 exit `0/1/2`。
- candidate snapshot/clean-clone verification 使用 index、临时目录且不访问
  remote；README 与 release-facing metadata checks 可执行。

外部 client evidence 不能由 unit test 伪造为通过；它属于明确记录的 M05
execution gate。

## Acceptance criteria

- 三个 Codex baseline 均通过 scenario ID 与对应 loaded case 配对，并记录
  实际选择和逐字理由。
- 三个 loaded pressure case 全部通过，每个明确组合至少三种压力。
- 两个 wording variants 各自 `5/5 PASS`，配置一致。
- 每次 rationale review 均有持久化 disposition；新借口已通过 Approved
  Gate Δ 与 superseding rerun 关闭，或明确记录不存在新借口。
- 5 个 Level 1 均有真实安装、发现和最小流程 evidence。
- 3 个 Level 2 均有结构与 smoke evidence。
- evidence 无敏感信息、不可覆盖、可从 case 和 registry 确定性验证。
- candidate clean clone 的测试、validator、installer matrix、README commands、
  release-facing metadata 和 summary 全部通过，最终 HEAD tree 与 candidate
  tree hash 相同。
- 不发生自动依赖安装、未批准网络访问、真实 home 写入或 remote mutation。
- release-ready evidence 完成，但不创建 tag、Release、push 或 `npx` package。
