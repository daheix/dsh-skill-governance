# P4 · 记忆索引接线说明（dsh-skill-memory → 会话先验）

> M20 ｜ DB 默认 `~/.dsh/skill-memory.db`

## 数据流

```
每周 cron（dsh-skill-audit-weekly.sh）
  └─ 全量 audit 快照 → data/skill_audit_<ts>.json
       └─ python3 bin/dsh-skill-memory.py build <json>   # 重建索引
            └─ ~/.dsh/skill-memory.db (skill_names/invocations/models/audit_runs)
```

## 会话先验注入（两种接法）

1. **手动/提示词式（现已可用）**：会话开始或用户问"上次用了哪些技能"时，执行：
   ```bash
   python3 ~/mydsh/bin/dsh-skill-memory.py query <skill-name>
   # → {"name":..., "stores":..., "mentions":..., "invoked":0/1, "attempt_count":...}
   ```
   把结果贴给模型即可形成先验（"此技能 1,411 次曝光 0 加载——目录里的名字，慎直接信任"）。
2. **工具式（后续）**：把 query 封装为 dsh memory 工具的数据源（memory-recall 类技能读同一 SQLite），实现会话开场自动注入 top 先验。

## 维护

- 索引随每周 audit 自动重建（幂等）；快照原始 JSON 永久留存于论文 data/。
- 隐私：仅含技能名与计数，无会话内容。
