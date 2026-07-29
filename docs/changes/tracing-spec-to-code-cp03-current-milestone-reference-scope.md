# CP-03 — Current milestone reference scope

- 状态：Approved
- 日期：2026-07-30
- Gate Δ：Approved on 2026-07-30
- 触发：M01-T03 repository self-validation
- Requirements：REQ-TS2C-002, REQ-TS2C-004
- 影响 Milestone：M01 — Artifact contracts
- 影响 Task：M01-T02, M01-T03
- 修正：CP-02 rule 2

## Trigger and evidence

首次运行真实 self-validation：

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo . --format json
```

返回 exit code `1`，并对 REQ-TS2C-003 至 REQ-TS2C-016 产生 14 个 `REQ_REFERENCE_MISSING`。这些 requirements 被 roadmap 分配给 M02–M05；根据 REQ-TS2C-004，当前只能存在 M01 详细 plan，因此这些 issues 是 false positive。

根因是已批准 CP-02 rule 2 要求“每个 spec requirement 必须被至少一个 milestone plan task 引用”，错误地把未来 milestone requirements 纳入当前 plan 的责任。

## Proposed delta

保留 `REQ_REFERENCE_MISSING` code，修正 missing-reference 范围：

1. 每个 spec requirement 仍必须被 roadmap 引用。
2. Parser 从 roadmap milestone table 提取 `MNN → Requirement IDs` 映射。
3. Parser 从 milestone plan metadata（`Milestone: MNN`，兼容 `:`/`：`）识别当前 milestone。
4. 只要求 roadmap 分配给当前 milestone 的 requirements 被当前 plan 的至少一个 task 引用。
5. 每个当前 plan task 仍必须在自身 heading 区段内引用至少一个 spec 中已知的 Requirement ID。
6. 未进入当前 milestone 的 future requirements 不因缺少详细 plan/task 而产生 issue。

对应验证：

- valid fixture 增加一个仅分配到 M02 的 requirement；没有 M02 详细 plan 时仍应 PASS。
- 当前 M01 分配的 requirement 若未被 M01 task 引用，仍返回 `REQ_REFERENCE_MISSING`。
- 仓库 self-validation 应返回 exit code `0`。

## Impact

- **Spec/Roadmap**：不修改；该 delta 使 REQ-TS2C-002 与 REQ-TS2C-004 同时成立。
- **Parser**：增加 roadmap milestone mapping 和 plan milestone metadata 的确定性解析。
- **Validation**：缩小 CP-02 rule 2 的量化范围；task-without-known-requirement 规则不变。
- **CLI/schema/issue codes**：不变。
- **Dependencies/network**：不变。
- **Scope**：仍在 M01-T02/T03；不创建未来 milestone plan。

## Alternatives

1. **保留 CP-02 全量规则并为 M02–M05 提前创建详细 plan。** 直接违反 REQ-TS2C-004，不可接受。
2. **删除 plan coverage missing check。** 会漏掉当前 milestone 的真实 traceability 缺口，不推荐。
3. **仅依赖 milestone plan 顶部 Requirements 列表。** 无法验证 roadmap→plan 的漏项，不推荐。

## Migration

当前 validator 尚未发布。现有 roadmap 和 M01 plan 已包含可解析的 milestone ID 与 requirement mapping，无数据迁移。

## Gate Δ

Gate Δ 已于 2026-07-30 批准。先更新 M01 plan 和 CP-02 的修正引用，再用 failing self-scope test 驱动实现。
