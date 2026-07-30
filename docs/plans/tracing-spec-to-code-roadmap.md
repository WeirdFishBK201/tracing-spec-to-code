# tracing-spec-to-code Roadmap

- 状态：In Progress — M03 Evidence and commit
- Spec：`docs/specs/tracing-spec-to-code-spec.md`
- Gate S：Approved on 2026-07-29
- Gate P：Approved — M01, M02, and M03 on 2026-07-30
- Gate Δ：CP-01, CP-02, CP-03, and CP-04 Approved on 2026-07-30
- Current milestone：M03
- 当前详细计划：`docs/plans/tracing-spec-to-code-m03-evidence-commit.md`

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
| M04 — Client distribution | Canonical skill 可通过 registry installer 分发到 Level 1/2 客户端 | REQ-TS2C-013–014 | M03 | Installer matrix、Level 1 install/discovery、Level 2 smoke tests |
| M05 — Evaluation and release | 基线、压力场景、wording micro-tests 和发布检查形成可复现证据 | REQ-TS2C-015 | M04 | Baseline/loaded comparison、5x wording runs、clean-clone release verification |

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

M01 与 M02 已交付。M03 Gate P 已于 2026-07-30 批准；只执行 M03。M04–M05 尚未展开详细 task。
