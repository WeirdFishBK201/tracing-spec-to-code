# tracing-spec-to-code M01 Artifact Contracts Plan

- 状态：Completed — delivered by this milestone commit
- Milestone：M01 — Artifact contracts
- Spec：`docs/specs/tracing-spec-to-code-spec.md`
- Roadmap：`docs/plans/tracing-spec-to-code-roadmap.md`
- Requirements：REQ-TS2C-001, REQ-TS2C-002, REQ-TS2C-016
- Gate P：Approved on 2026-07-30
- Gate Δ：CP-01, CP-02, and CP-03 Approved on 2026-07-30

## Goal

交付一个最小、可运行、零第三方 Python 依赖的 artifact validator：解析默认或自定义配置，读取四类文档，并用稳定错误代码报告路径、ID 与引用问题。

## Architecture and constraints

Canonical skill 位于 `skills/tracing-spec-to-code/`。入口脚本把配置、Markdown artifact 解析和规则检查委托给同目录 `tstc` 包；模板位于 `assets/templates/`。M01 不实现 Gate 对话、上下文编排、自动 commit 或客户端 installer。

- Python 3.10+ standard library、`unittest`、JSON、Markdown、Git。
- 不读取、不依赖、不修改 VGCCoach2。
- 不静默修复无效配置、重复 ID 或未知引用。
- RED 必须证明解析或校验行为缺失，不能只检查文件/符号不存在。
- 每个 task 后仓库可运行；只在 M01 全部验证通过后创建一个 commit。

## Planned files

| Path | Responsibility |
|---|---|
| `skills/tracing-spec-to-code/SKILL.md` | M01 触发条件、validator 用法和失败边界，少于 500 行 |
| `skills/tracing-spec-to-code/agents/openai.yaml` | Codex 展示 metadata，不承载 workflow 规则 |
| `skills/tracing-spec-to-code/assets/templates/{config.json,spec.md,roadmap.md,milestone-plan.md,change-proposal.md}` | Canonical artifact templates |
| `skills/tracing-spec-to-code/scripts/tstc/config.py` | 默认值、JSON 配置与安全路径解析 |
| `skills/tracing-spec-to-code/scripts/tstc/artifacts.py` | Markdown headings、ID、task 和引用解析 |
| `skills/tracing-spec-to-code/scripts/tstc/validation.py` | 纯规则检查与稳定 issue codes |
| `skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py` | CLI、text/JSON 输出与 exit code |
| `tests/fixtures/{valid-project,duplicate-requirement,unknown-reference}/` | 端到端行为输入 |
| `tests/test_{config,artifacts,validation,cli}.py` | Unit 与 CLI behavior tests |
| `README.md` | M01 安装前运行方式与 validator 示例 |

## Interfaces

`config.py`：

- `ResolvedConfig(repo_root, spec_dir, plan_dir, change_dir, feature_slug, spec_filename_template, roadmap_filename_template, milestone_plan_filename_template, change_proposal_filename_template)`
- `load_config(repo_root: Path, config_path: Path | None = None) -> ResolvedConfig`
- `ConfigError(code, path, message)`

`artifacts.py`：

- `ArtifactKind`: `SPEC`, `ROADMAP`, `MILESTONE_PLAN`, `CHANGE_PROPOSAL`
- `ArtifactRef(kind, path, requirement_ids, task_ids, referenced_ids)`
- `discover_artifacts(config: ResolvedConfig) -> list[ArtifactRef]`
- `ArtifactParseError(code, path, line, message)`

`validation.py`：

- `ValidationIssue(code, path, line, message)`
- `validate_repository(repo_root: Path, config_path: Path | None = None) -> list[ValidationIssue]`
- Issues 按 `path`, `line`, `code` 稳定排序。

CLI：

```text
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate [--repo PATH] [--config PATH] [--format text|json]
```

Exit codes：`0` 无 issues；`1` 有 validation issues；`2` 参数、配置或运行环境错误。

Stable issue codes：`CFG_INVALID_JSON`, `CFG_UNKNOWN_KEY`, `CFG_PATH_OUTSIDE_REPO`, `CFG_TEMPLATE_INVALID`, `ARTIFACT_MISSING`, `ARTIFACT_PARSE_ERROR`, `REQ_ID_INVALID`, `REQ_ID_DUPLICATE`, `REQ_REFERENCE_UNKNOWN`, `REQ_REFERENCE_MISSING`, `TASK_ID_INVALID`, `TASK_ID_DUPLICATE`。

## Tasks

### M01-T01 — Configuration and template contract

**Objective:** 建立 canonical scaffold、模板和安全配置解析，使默认路径与合法 override 产生确定结果。

**Requirements:** REQ-TS2C-001, REQ-TS2C-016

**Files:** 创建 `SKILL.md`, `agents/openai.yaml`, 五个 templates, `scripts/tstc/{__init__.py,config.py}`, `tests/test_config.py`。

**Produces:** `ResolvedConfig`, `load_config`, `ConfigError` 和 canonical templates，供 T02 使用。

1. 用本机 `skill-creator/init_skill.py` 生成 scaffold；立即收敛为 M01 有效内容，不保留占位文本。
2. 写配置行为测试：默认值、合法 directory/filename template override、未知 key、非法 JSON、绝对路径、逃出 repo root、未知或缺失 placeholder、路径注入和非 Markdown 后缀。
3. 运行 targeted test，确认 RED 来自缺失行为或错误分类。
4. 实现最小 contract/templates，重跑测试和 skill 结构校验。

**Verify:**

```text
python -m unittest tests.test_config -v
python C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tracing-spec-to-code
```

预期：config behavior tests PASS；skill structure validation 成功。

### M01-T02 — Artifact parsing and traceability rules

**Objective:** 从 Markdown fixture 解析 Requirement ID、task ID 和引用，以稳定 issue code 报告结构错误。

**Requirements:** REQ-TS2C-001, REQ-TS2C-002

**Files:** 创建 `artifacts.py`, `validation.py`, 三组 fixtures, `tests/test_artifacts.py`, `tests/test_validation.py`。

**Consumes/produces:** 消费 `ResolvedConfig` 和 templates；产出 `ArtifactKind`, `ArtifactRef`, `discover_artifacts`, `ValidationIssue`, `validate_repository`。

1. 写 fixtures 和行为测试：默认/自定义命名的有效项目、重复 requirement、未知 requirement 引用、当前 milestone roadmap/plan/task 缺失引用、future milestone 无详细 plan、无效 task ID 和重复 task ID。
2. 运行 targeted tests，确认每个 RED 对应解析或校验行为。
3. 实现 heading-aware parser、跨 artifact 索引和稳定排序；不推断 prose 语义。
4. 重跑测试，确认有效 fixture 无 issue，无效 fixture 只返回约定 code 且位置可定位。

**Verify:**

```text
python -m unittest tests.test_artifacts tests.test_validation -v
```

预期：全部 PASS；issue 顺序在重复运行中一致。

### M01-T03 — CLI behavior and integration

**Objective:** 提供可运行的 `validate` CLI，用端到端测试证明 text/JSON 输出和 exit code。

**Requirements:** REQ-TS2C-001, REQ-TS2C-002

**Files:** 创建 `tracing_spec_to_code.py`, `tests/test_cli.py`, `README.md`；更新 `SKILL.md`, `openai.yaml` 和本 plan Evidence。

**Consumes/produces:** 消费 `load_config`、`validate_repository`；产出 `main(argv: Sequence[str] | None = None) -> int` 和稳定 CLI contract。

1. 写 subprocess tests：有效 fixture 返回 `0`，validation issue 返回 `1`，配置/参数错误返回 `2`，JSON 可被标准库解析。
2. 运行 targeted test，确认 RED 来自 CLI 未满足 output/exit contract。
3. 实现 CLI 和 M01 范围说明；错误写 stderr，JSON 字段保持稳定。
4. 运行 targeted/broader verification，把实际结果、traceability 和偏差写入 Evidence。

**Verify:**

```text
python -m unittest tests.test_cli -v
```

预期：全部 PASS；stdout、stderr 与 exit codes 符合 contract。

## Milestone verification

```text
python -m unittest discover -s tests -v
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo tests/fixtures/valid-project
python C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tracing-spec-to-code
git diff --check
git status --short
```

预期：tests 全部 PASS；valid fixture 返回 `0`；skill validation 成功；无 whitespace error；Git 只含 M01 范围内文件。

## Traceability target

| Task | Requirements | Implementation | Tests |
|---|---|---|---|
| M01-T01 | REQ-TS2C-001, REQ-TS2C-016 | templates, `config.py`, metadata | `test_config.py` |
| M01-T02 | REQ-TS2C-001, REQ-TS2C-002 | `artifacts.py`, `validation.py` | parser/validator tests、fixtures |
| M01-T03 | REQ-TS2C-001, REQ-TS2C-002 | CLI、SKILL、README | `test_cli.py`、full suite |

## Evidence and commit

执行时在本节追加 task 状态、最终路径/test names、实际命令与结果、批准的 change proposal、偏差、commit hash/message；不创建单独 delivery report。

- Gate P：用户于 2026-07-30 批准执行 M01。
- Gate Δ：用户于 2026-07-30 批准 `docs/changes/tracing-spec-to-code-cp01-config-filename-templates.md`；配置接口、错误码和 T01/T02 测试范围已按 CP-01 更新。
- Gate Δ：用户于 2026-07-30 批准 `docs/changes/tracing-spec-to-code-cp02-missing-reference-code.md`；新增 `REQ_REFERENCE_MISSING` 及 roadmap/plan/task coverage checks。
- Gate Δ：用户于 2026-07-30 批准 `docs/changes/tracing-spec-to-code-cp03-current-milestone-reference-scope.md`；plan coverage 仅量化 roadmap 分配给当前 milestone 的 requirements。

### Task status

| Task | Status | Actual verification |
|---|---|---|
| M01-T01 | Completed | `python -m unittest tests.test_config -v`：13 tests PASS；`quick_validate.py skills/tracing-spec-to-code`：PASS；3 个 baseline 与 3 个 loaded-skill 场景均记录，loaded skill 全部 fail closed |
| M01-T02 | Completed | `python -m unittest tests.test_artifacts tests.test_validation -v`：20 tests PASS；覆盖 spec-only definitions、task section、milestone table/range 和 current/future milestone scope |
| M01-T03 | Completed | `python -m unittest tests.test_cli -v`：6 tests PASS；full suite 39 tests PASS；valid fixture 与 repository self-validation 均 exit `0` |

### Final verification

- `.venv\Scripts\python.exe -m unittest discover -s tests -v`：39 tests PASS（Python 3.14.5）。
- `tracing_spec_to_code.py validate --repo tests/fixtures/valid-project`：exit `0`，`OK: no validation issues`。
- `tracing_spec_to_code.py validate --repo . --format json`：exit `0`，`{"issues": [], "valid": true}`。
- `quick_validate.py skills/tracing-spec-to-code`：`Skill is valid!`。
- `ast.parse(..., feature_version=(3, 10))`：10 Python files PASS。
- Independent spec review：PASS；independent code quality review：PASS。
- `git diff --check`：无 whitespace error；仅 Git 的 LF→CRLF warning。

### Deviations

- 本机 `.venv` 为执行官方 `quick_validate.py` 安装了 PyYAML 6.0.3；该目录被忽略，validator 代码和项目依赖仍为 Python 标准库。
- CP-01 安全边界补充了 `feature_slug`/config path 注入、非字符串目录值和非 UTF-8 JSON 的 fail-closed 检查；不改变已批准配置 key 或 CLI schema。
- 当前机器只有 Python 3.14.5 runtime；已通过 Python 3.10 grammar 检查，但未在真实 Python 3.10 runtime 执行测试。

Gate P 批准并按已批准事实最小校正后的 commit：

```text
feat(contracts): validate spec-to-code artifacts

Milestone: M01 Artifact contracts
Requirements: REQ-TS2C-001, REQ-TS2C-002, REQ-TS2C-016
Change-Proposals: CP-01, CP-02, CP-03
```

Commit hash：本文件包含在该 milestone commit 内，无法在不改变自身 hash 的前提下嵌入其字面值；最终交付摘要记录实际 hash，也可用 `git log -1 --format=%H` 解析。不会自动 push。

## Risks and Gate P

- Python 3.10 runtime 尚未实机验证；当前 Python 3.14.5 tests 与 Python 3.10 grammar 检查均通过。
- Parser 只识别模板 headings、表格字段和 ID token，不理解任意 prose。
- M01 的 `SKILL.md` 只公开 artifact validation；不得提前宣称完整 workflow。

批准 M01 表示确认：完成 REQ-TS2C-001/002，并遵守全局 REQ-TS2C-016；使用 3 个 task；接受 Python 3.10+ 与上述 commit 草案；不提前实现 M02–M05。
