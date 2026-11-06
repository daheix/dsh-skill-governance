# dsh-skill-governance — 技能目录治理套件（可公开发布）

> 版本 0.1.0 ｜ 2026-11-06 ｜ 许可 MIT
> 配套论文：paper-ai-00001《Governing Skill Gray-out in Production》（mydsh 私有库同行包内含匿名化数据快照）

## 这是什么

一套让 LLM 编码智能体的"技能目录"真正被用起来的治理工具链。它源于一个生产部署的真实发现：**226 个技能里 177 个被目录过，175 个从未被加载（98.87% 零调用）**。本套件提供测量（audit）、卫生（lint/rewrite）、路由（dispatcher skill）、记忆（memory index）四件套，全部离线、无模型依赖、对任何符合 Agent Skills 目录约定的工作区可用。

## 组成

```
dsh-skill-governance/
├── skills/skill-directory/SKILL.md   # 索引官技能（渐进披露路由器）
├── bin/dsh-skill-audit.py|.sh        # 遥测审计（目录消息/条目/调用/模型归因全量统计）
├── bin/dsh-skill-desc-lint.py        # 描述卫生 lint（SOP 三规则）
├── bin/dsh-skill-desc-rewrite.py     # 描述批量改造（family 模板+备份回滚）
├── bin/dsh-skill-memory.py           # P4 记忆索引（audit→SQLite，跨会话先验）
├── docs/SOP.md                       # 描述 SOP v1 + 入池门禁 + 复审节律
├── docs/DATA_SCHEMA.md               # audit JSON/CSV 字段字典（数据留存规范）
└── LICENSE                           # MIT
```

## 快速开始

```bash
# 1) 审计你的 dsh 会话库（默认 ~/.dsh/sessions）
DSH_AUDIT_OUT=./data bash bin/dsh-skill-audit.sh

# 2) 描述卫生体检
SKILL_POOL=/path/to/.dsh/skills DSH_LINT_OUT=./data python3 bin/dsh-skill-desc-lint.py

# 3) 批量改造未过 SOP 的描述（先 dry-run 看报告，再 --apply；自动写 .descbak 备份）
python3 bin/dsh-skill-desc-rewrite.py            # dry-run
python3 bin/dsh-skill-desc-rewrite.py --apply    # 落盘

# 4) 构建跨会话记忆索引
python3 bin/dsh-skill-memory.py build ./data/skill_audit_<ts>.json
python3 bin/dsh-skill-memory.py query arpack-library

# 5) 把 skills/skill-directory 放进你的 .agents/skills/（或 .dsh/skills/）
```

## 研究诚信声明

- 本套件的论文数据全部来自真实生产会话 store 的逐行解压统计，无任何估算填充（token 一类只以 chars÷4 显式标注为估算）。
- 模型归因：audit v2 起逐 store 记录请求模型（provider/model），所有参与实验的模型真实留痕。
- 数据留存：每批快照带时间戳永不覆盖，SHA256SUMS 固定，供论文评审与公开仓库核对。

## 引用

若本套件对你的研究有用，请引用配套论文（投稿中）：
Governing Skill Gray-out in Production: A Telemetry Case Study of 175/177 Zero-Invoked Skill Names in an Industrial Agentic Coding Harness, 2026.
