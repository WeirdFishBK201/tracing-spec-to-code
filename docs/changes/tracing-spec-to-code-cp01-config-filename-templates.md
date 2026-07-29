# CP-01 — Configurable filename templates

- 状态：Approved
- 日期：2026-07-30
- Gate Δ：Approved on 2026-07-30
- 触发：M01-T01 implementation preflight
- Requirements：REQ-TS2C-001
- 影响 Milestone：M01 — Artifact contracts
- 影响 Task：M01-T01, M01-T02

## Trigger and evidence

REQ-TS2C-001 的验收条件要求根目录 JSON 配置能够覆盖文档目录和命名模板，设计文档也声明 `.tracing-spec-to-code.json` 可覆盖两者。已批准的 M01 plan 将 `ResolvedConfig` 定义为：

```text
ResolvedConfig(repo_root, spec_dir, plan_dir, change_dir, feature_slug)
```

该接口没有 filename template 字段。按现有 plan 实现只能覆盖目录，无法满足已批准 Spec；未经 Gate Δ 扩展接口则会静默偏离 plan。

## Proposed delta

保持 M01 的三个 task 和 Python 标准库边界不变，扩展配置契约：

```text
ResolvedConfig(
  repo_root,
  spec_dir,
  plan_dir,
  change_dir,
  feature_slug,
  spec_filename_template,
  roadmap_filename_template,
  milestone_plan_filename_template,
  change_proposal_filename_template,
)
```

默认值：

```text
{feature}-spec.md
{feature}-roadmap.md
{feature}-m{milestone}-{milestone_slug}.md
{feature}-cp{proposal}-{proposal_slug}.md
```

模板规则：

- 模板只能生成单个 Markdown 文件名，不能包含绝对路径、目录分隔符或 `..`。
- 每类模板只能使用其声明的 placeholder。
- spec/roadmap 必须包含 `{feature}`。
- milestone plan 必须包含 `{feature}`、`{milestone}`、`{milestone_slug}`。
- change proposal 必须包含 `{feature}`、`{proposal}`、`{proposal_slug}`。
- 无效模板通过新增稳定配置错误码 `CFG_TEMPLATE_INVALID` fail closed。
- `discover_artifacts` 使用解析后的模板匹配 artifact 文件名；不回退到猜测命名。

对应更新：

- M01 plan 的 Interfaces、stable issue codes、T01/T02 测试范围和 traceability。
- `assets/templates/config.json` 展示全部默认 key。
- `tests/test_config.py` 覆盖合法 override、未知/缺失 placeholder、路径注入和非 Markdown 后缀。
- `tests/test_artifacts.py` 覆盖默认与自定义命名发现。

## Impact

- **Spec**：不修改；该 delta 使 M01 plan 能满足现有 REQ-TS2C-001。
- **Roadmap**：不修改 milestone outcome、依赖或 requirement coverage。
- **Implementation**：只扩大 `config.py` 的已计划数据契约，并让 `artifacts.py` 消费模板。
- **Tests**：增加配置模板和自定义命名的行为测试。
- **CLI**：命令、JSON 输出和 exit codes 不变；模板错误仍属于 exit code `2`。
- **Dependencies/network**：不新增第三方依赖，不需要网络。
- **Schedule/scope**：仍为三个 task；不提前实现 Gate workflow、commit automation 或 installer。

## Alternatives

1. **修改 Spec，只允许覆盖目录。** 实现更小，但削弱已批准 REQ-TS2C-001，不推荐。
2. **推迟到后续 milestone。** M01 将无法宣称完成 REQ-TS2C-001，不可接受。
3. **只允许配置四个具体文件名。** 实现简单，但不满足 milestone/change proposal 的递增命名模板语义，不推荐。

## Migration

当前尚无发布配置或实现，无数据迁移。未配置这些 key 的项目继续使用默认模板。

## Gate Δ

Gate Δ 已于 2026-07-30 批准。先更新 M01 plan，再继续 M01-T01 的 RED/GREEN。
