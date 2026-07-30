# tracing-spec-to-code M04 Client Distribution Design

- 状态：Approved design
- 日期：2026-07-30
- Milestone：M04 — Client distribution
- Requirements：REQ-TS2C-013, REQ-TS2C-014, REQ-TS2C-016
- Roadmap：`docs/plans/tracing-spec-to-code-roadmap.md`
- Change proposal：`docs/changes/tracing-spec-to-code-cp05-defer-npx-distribution.md`
- Gate Δ：Approved on 2026-07-30
- Gate P：Pending

## Goal

提供一个零第三方运行时依赖的本地 installer，将唯一 canonical Skill 完整复制到 Level 1/2 客户端的 project 或 user 目录，并在隔离临时目录中确定性验证分发结果。

M04 完成后，开发者能够离线验证“registry mapping → 安全复制 → 内容校验”的完整链路；真实客户端启动、远程 source 和 `npx` 不属于本 milestone。

## Scope

M04 包含：

- `skills/tracing-spec-to-code/` 继续作为唯一 canonical source。
- registry 声明 8 个客户端的稳定 ID、支持级别、project/user 相对路径和能力元数据。
- Python 标准库 installer 解析 registry、解析安全目标、复制完整目录并验证结果。
- 临时 project/home roots 下的 8 clients × 2 scopes 安装矩阵。
- 已有目标保护、无效 registry、路径逃逸、source 异常和部分复制失败处理。
- README 中的本地安装、边界和验证命令。

M04 不包含：

- `npx`、npm package、自有 Node wrapper 或第三方 installer 集成。
- GitHub remote install、clone、fetch、push、PR、release 或远程一致性检查。
- 安装或升级 Python、Git、Node 或 agent 客户端。
- 启动真实 agent，或写入开发机真实 project/home/client 配置。
- M05 的基线、压力场景、5x wording 和 runtime release evidence。

## Architecture

```text
skills/tracing-spec-to-code/  canonical source
              |
              v
tools/clients.json  -->  tools/distribution.py  <--  tools/install.py
                              |
                              v
                 <selected root>/<client path>/
                       tracing-spec-to-code/
```

组件职责：

1. `tools/clients.json` 只保存分发数据，不保存 workflow 内容。
2. `tools/distribution.py` 负责 registry 校验、安全路径解析、canonical manifest、复制事务和安装后校验。
3. `tools/install.py` 是薄 CLI，只解析参数、调用 library，并用稳定 exit code 报告结果。
4. tests 直接测试 library，并通过 subprocess 覆盖 CLI observable behavior。

新增客户端原则上只修改 registry 和对应测试数据，不修改 canonical Skill 或 workflow core。

## Registry contract

Registry 顶层包含 schema version 和 clients 数组。每个 client 必须包含：

- 唯一、稳定的 `id`。
- `level`，只能是 `1` 或 `2`。
- 非空显示名称。
- `project_path` 和 `user_path`，均为相对于调用者提供 root 的安全目录。
- 最小 capability metadata，用于区分结构验证与后续 runtime 验证，不驱动 workflow。

固定客户端集合：

- Level 1：Codex、Claude Code、GitHub Copilot CLI、Antigravity、Gemini CLI。
- Level 2：Cursor、Windsurf/Cascade、Cline。

Registry 遇到未知 key、重复 ID、缺字段、未知 level、绝对路径、空路径、`.`、`..` 或解析后逃逸 root 时 fail closed。客户端路径变化属于兼容性变化，必须更新测试并在 M04 plan evidence 中说明。

## Installer interface

CLI 目标接口：

```text
python tools/install.py --client <id> --scope project --project-root <path>
python tools/install.py --client <id> --scope user --home-root <path>
```

规则：

- `--client` 必须存在于 registry；`--scope` 只能是 `project` 或 `user`。
- project scope 只使用显式 `--project-root`；user scope 只使用显式 `--home-root`。
- 目标固定为 `<resolved client path>/tracing-spec-to-code/`。
- M04 不默认推断或写入真实 home；README 要求调用者明确提供 root。
- 目标不存在时才允许安装；任何已存在文件或目录都拒绝，M04 不提供 `--force`。
- 成功输出 client、scope 和目标路径；不输出不必要的环境信息。

Exit code 与现有 CLI 约定一致：

- `0`：安装和内容校验成功。
- `1`：registry、source、目标冲突或 policy 校验失败。
- `2`：参数错误或不可恢复的运行时错误。

## Copy and integrity flow

1. 加载并完整校验 registry。
2. 构建 canonical manifest：排序后的相对文件路径、文件大小和 SHA-256。
3. 拒绝 canonical source 中的 symlink、路径逃逸和非普通文件。
4. 解析 root 与 registry 相对路径，确认目标仍位于显式 root 内。
5. 确认最终目标不存在，在同一父目录创建唯一临时目录。
6. 用 `shutil.copytree` 复制完整 canonical directory。
7. 重建临时副本 manifest；缺失、额外或 hash 不一致都失败。
8. 把验证后的临时目录 rename 为最终目标，再验证最终 manifest。

失败时只能清理本次创建且已精确解析的临时目录。不得删除或修改已有目标、canonical source、root 其他内容或 Git 状态；无法安全清理时报告准确路径并停止。

## Testing

Targeted suite 使用 Python `unittest` 和 `tempfile`，不需要网络：

- registry schema、固定 client set、level 和路径校验。
- 重复 ID、未知 key、缺字段、绝对路径及 `..` 逃逸失败。
- canonical manifest 对缺失、额外、内容变化和 symlink fail closed。
- 8 clients × project/user 的 16 个安装组合全部复制完整目录。
- 已有目标包含 sentinel 时安装失败，sentinel 内容保持不变。
- 模拟复制或验证失败后最终目标不存在，只清理本次临时目录。
- CLI 成功输出、未知 client、冲突和 exit `0/1/2`。
- 测试显式传入临时 project/home roots，并断言真实 home 未被触碰。

M04 gate：

```text
python -m unittest tests.test_distribution tests.test_install_cli -v
python -m unittest discover -s tests -v
python skills/tracing-spec-to-code/scripts/tracing_spec_to_code.py validate --repo .
python C:\Users\Yuchen\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tracing-spec-to-code
git diff --check
```

Level 1 在 M04 验证完整本地安装结构、metadata 与 registry discovery data；Level 2 验证完整结构和内容 smoke。真实客户端 discovery/minimal workflow 证据仍在 M05。

## Acceptance criteria

- 仓库只有一份 canonical workflow source。
- registry 精确覆盖批准的 5 个 Level 1 和 3 个 Level 2 客户端。
- installer 完整复制 canonical directory，复制后 manifest 完全一致。
- 16 个隔离安装组合通过，已有目标从不被静默覆盖。
- 所有失败路径 fail closed，不触碰真实 home、真实客户端、网络或 Git remote。
- M04 可以只用 Python 标准库、Git 和仓库现有验证命令完成。
- `npx` 与公开 GitHub source 已记录为 M05 之后的长期目标，不是 M04 completion gate。

## Approved decision

用户于 2026-07-30 批准本地 Python installer 方案，并要求把 `npx` 测试延后到长期目标。M04 implementation 仍需独立详细 plan 和 Gate P；本设计不授权提前实现。
