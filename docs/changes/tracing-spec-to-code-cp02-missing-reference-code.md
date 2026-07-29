# CP-02 — Missing reference issue code

- 状态：Approved
- 日期：2026-07-30
- Gate Δ：Approved on 2026-07-30
- 修正：Rule 2 的范围由已批准 CP-03 限定为 roadmap 分配给当前 milestone 的 requirements。
- 触发：M01-T02 validation contract review
- Requirements：REQ-TS2C-002
- 影响 Milestone：M01 — Artifact contracts
- 影响 Task：M01-T02, M01-T03

## Trigger and evidence

REQ-TS2C-002 明确要求 validator 发现重复、缺失和未知引用。已批准 M01 plan 提供 `REQ_ID_DUPLICATE` 和 `REQ_REFERENCE_UNKNOWN`，但没有能表示缺失追溯关系的稳定 issue code。

将缺失引用复用为 `REQ_REFERENCE_UNKNOWN` 会混淆两个不同事实：

- **Unknown**：artifact 引用了 spec 中不存在的 Requirement ID。
- **Missing**：spec 已定义 Requirement ID，但 roadmap/plan 没有建立要求的引用，或 plan task 没有引用任何已知 requirement。

## Proposed delta

新增稳定 validation issue code：

```text
REQ_REFERENCE_MISSING
```

M01 中只做确定性检查：

1. 每个 spec requirement 必须被 roadmap 引用。
2. 每个 spec requirement 必须被至少一个 milestone plan task 引用。
3. 每个 milestone plan task 必须在自身 heading 区段内引用至少一个 spec 中已知的 Requirement ID。
4. 缺失 issue 定位到 spec requirement 定义行或 task heading 行；message 指明缺失的目标关系。
5. 当对应 artifact 整体缺失时，只报告 `ARTIFACT_MISSING`，不追加由该缺失 artifact 派生的 coverage 噪声。

`REQ_REFERENCE_UNKNOWN` 保持原语义：引用的合法格式 ID 在 spec 定义索引中不存在。

对应更新：

- M01 plan 的 stable issue codes 和 T02 测试范围。
- `tests/test_validation.py` 增加 roadmap coverage、plan task coverage 和 task-without-requirement 行为测试。
- CLI JSON/text 只透传新 code，不改变 schema 或 exit code。

## Impact

- **Spec/Roadmap**：不修改 requirement 或 milestone coverage。
- **Parser**：保留 ID occurrence 的 artifact、line、definition 和 task-section 上下文，供纯 validation 规则消费。
- **Validation**：增加一种 issue code 和三个确定性 missing-reference checks。
- **CLI**：发现该 issue 时仍返回 exit code `1`。
- **Dependencies/network**：无新增依赖或网络需求。
- **Scope**：仍为 M01 的三个 task；不检查 implementation/test evidence 的语义充分性，该部分仍由后续 evidence milestone 负责。

## Alternatives

1. **复用 `REQ_REFERENCE_UNKNOWN`。** 错误分类不准确，CI 无法区分“错误 ID”与“漏建关系”，不推荐。
2. **只在 message 中描述缺失，不提供稳定 code。** 迫使机器消费者解析文案，不推荐。
3. **推迟到后续 milestone。** M01 将无法满足 REQ-TS2C-002 的明确验收条件，不可接受。

## Migration

当前 validator 尚未发布，无数据迁移。未来 CI 需要允许新的 `REQ_REFERENCE_MISSING` code。

## Gate Δ

Gate Δ 已于 2026-07-30 批准。先更新 M01 plan，再继续 `tests/test_validation.py` 的 RED/GREEN。
