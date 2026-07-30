# tracing-spec-to-code Roadmap

- 状态：Awaiting Gate P — M05 Evaluation and release
- Spec：`docs/specs/tracing-spec-to-code-spec.md`
- Gate S：Approved on 2026-07-29
- Gate P：Approved — M01 through M04 on 2026-07-30; M05 awaiting detailed plan
- Gate Δ：CP-01 through CP-08 Approved on 2026-07-30
- Current milestone：M05
- 当前详细计划：Awaiting M05 plan approval
- M05 design：`docs/design/2026-07-30-tracing-spec-to-code-m05-evaluation-release-design.md`

## 规则

- Roadmap 只记录 milestone outcome、依赖、requirements 和 verification gate。
- 只为下一个 milestone 维护详细 plan。
- 每个 milestone 独立可运行、可验证。
- 每个 milestone 完成后自动创建一个 commit，并停止等待下一步批准。
- REQ-TS2C-016 是所有 milestone 的全局隔离约束。

## Milestones

| Milestone | Outcome | Primary requirements | Dependencies | Verification gate |
|---|---|---|---|---|
| M01 — Artifact contracts | 一个可运行的零第三方依赖 validator 能解析配置、识别 artifacts，并检查 ID 与结构追溯 | REQ-TS2C-001, REQ-TS2C-002 | Gate S | Unit tests、CLI behavior tests、template validation、skill structure check |
| M02 — Workflow core | Skill 能执行 Gate S/P/Δ、当前 milestone 限制、受限上下文和自适应测试决策 | REQ-TS2C-003–009 | M01 | Pressure scenarios、workflow fixtures、behavior tests |
| M03 — Evidence and commit | Skill 能验证 evidence、隔离 stage 范围并安全创建 milestone commit | REQ-TS2C-010–012 | M02 | Temporary Git repo integration tests、failure-path tests |
| M04 — Client distribution | Canonical skill 可通过 registry installer 分发到 Level 1/2 客户端 | REQ-TS2C-013–014 | M03 | 8×2 installer matrix、完整内容/结构校验、Level 1/2 mapping contract |
| M05 — Evaluation and release | 基线、压力场景、wording micro-tests 和发布检查形成可复现证据 | REQ-TS2C-015 | M04 | Baseline/loaded comparison、5x wording runs、Level 1 discovery、Level 2 smoke、candidate clean-clone release verification |

## Long-term goals

- npx 与远程分发：M05 之后再提案立项；从公开 GitHub source 安装，在隔离环境验证固定 CLI 版本、project/user scope、远程与 canonical 内容一致性及 clean-environment 行为。
- 该目标不属于 M04 Gate P，不授权网络访问、依赖下载、GitHub mutation 或 push。
- Native handle 安全强化：另行提案评估 Windows/POSIX handle-relative API，覆盖 path creation 到首次 identity capture 的恶意并发 replacement；不属于 M04。

## Requirement coverage

| Requirement | Planned milestone |
|---|---|
| REQ-TS2C-001 | M01 |
| REQ-TS2C-002 | M01 |
| REQ-TS2C-003 | M02 |
| REQ-TS2C-004 | M02 |
| REQ-TS2C-005 | M02 |
| REQ-TS2C-006 | M02 |
| REQ-TS2C-007 | M02 |
| REQ-TS2C-008 | M02 |
| REQ-TS2C-009 | M02 |
| REQ-TS2C-010 | M03 |
| REQ-TS2C-011 | M03 |
| REQ-TS2C-012 | M03 |
| REQ-TS2C-013 | M04 |
| REQ-TS2C-014 | M04 |
| REQ-TS2C-015 | M05 |
| REQ-TS2C-016 | M01–M05 |

## Gate P

M01–M04 已交付，M04 implementation commit 为 `a6ef478aaf927399f9439fecf473845a248e9c3e`。M05 design 已于 2026-07-30 获得用户批准，当前等待详细 plan 与新的 Gate P；长期目标不得提前展开详细 task。
