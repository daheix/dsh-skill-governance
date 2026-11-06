# PROVENANCE · 模型与工具链真实记录 — paper-ai-00001

> 建档 2026-11-06 ｜ 纪律：所有参与研究/部署的模型、工具版本逐项留痕；随每批数据更新

## 1. 研究执行环境（论文撰写与工具开发）

| 角色 | 模型/工具 | 版本/提供方 | 时间窗 |
|---|---|---|---|
| 论文撰写、检索、工具开发 | **GLM-5.3-Flash** | provider `zai-coding-plan`；harness：OpenCode | 2026-11-06（00029/00030/00031 会话） |
| 检索通道 | websearch（harness 内建）+ webfetch | — | 同上 |

## 2. 被测部署（遥测数据来源）的模型归因

audit v2（M20）起逐 store 记录 `request/context` 的 provider/model。快照 `skill_audit_20261106_115000.json` 的 `model_attribution`（真实轮次）：

| provider/model | 请求轮次 |
|---|---|
| zai/glm-5.3-flash | 1,308 |
| nvidia/deepseek-ai/deepseek-v4.1-flash | 11 |
| nvidia/z-ai/glm-5.3-flash | 9 |
| zai/glm-5.3-flashx | 2 |
| zai/glm-5.3 | 2 |
| nvidia/stepfun-ai/step-5-preview | 2 |
| openai/gpt-6-luna | 1 |
| nvidia/google/codegemma-7b | 1 |
| nvidia/minimaxai/minimax-m3.1-flash | 1 |
| nvidia/nvidia/llama-3.1-nemotron-ultra-253b-v1 | 1 |

harness：**dsh 0.2.1-rc.5**（web 实例，cordis 容器；技能机制 `@deepseek-ai/dsh-tool-skill`，catalogDescriptionMaxLength 默认 500）。

## 3. 工具链版本（全部入库 mydsh，commit 可溯）

| 工具 | 版本 | commit | 作用 |
|---|---|---|---|
| dsh-skill-audit.py/.sh | M18 → **v2(M20)** | 8eea0b7 → 本次 M20 | 遥测审计（v2 增加模型归因/模型轮次字段） |
| dsh-skill-desc-lint.py | M19 | 43d28c2 | 描述 SOP 三规则 lint |
| dsh-skill-desc-rewrite.py | **M20** | 本次 | P2 批量改造（family 模板+备份+dry-run） |
| dsh-skill-memory.py | **M20** | 本次 | P4 记忆索引（audit→SQLite） |
| 公开插件包 | **M20** | 本次 | plugins/dsh-skill-governance/（bin×5+skill×1+docs×2+LICENSE） |

## 4. L3 批次一改造记录（P2 落地）

- 池结构真相：`.agents/skills` 115 项中 108 个 SKILL.md 为符号链接 → 真本库 `ChinaSimStdio/.dsh/skills`（147 项，全真身）
- 改造范围：`.dsh/skills` 内 88 个 SKILL.md（sci-* 真本保护跳过；链接自动生效）
- 备份：每个文件 `.descbak-20261106_114930` 同目录留存，可整体回滚
- **前后对比（lint）**：SOP 通过率 **0.87%（1/115）→ 95.45%（84/88）**；短描述 109→0；余 4 条 >480 待微调
- 证据链：`data/desc_lint_20261106_112124.json`（前）→ `data/desc_rewrite_20261106_114930_applied.json` → `data/desc_lint_*_1149 后`（后）

## 5. 数据留存纪律（对"所有有效数据必须记录"的落实）

1. 快照带 UTC 时间戳，永不覆盖/删除；更正走"新快照+台账注记"，旧件保留（104459 初扫版即范例）。
2. 每次公开提交附 `SHA256SUMS`；session 标识伪匿名（UUID）。
3. 模型归因从 v2 起为审计必选字段；后续每批 L3 数据必须含模型表。
4. 后续公开 GitHub 仓：插件包 `dsh-skill-governance/` 为主体 + 匿名化数据快照 + 本 PROVENANCE 模板。
