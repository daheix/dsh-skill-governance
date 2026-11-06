# 描述 SOP v1（description hygiene）— dsh-skill-governance

> 生效 2026-11-06 ｜ 依据：paper-ai-00001 §5.3 P2 + SkillRouter（metadata 通道结构不足）+ ToolRet（描述可检索性）

## 三规则（lint 即此三条）

1. **R1 长度预算**：200–480 字符（harness 目录条目截断宽限 500）。
2. **R2 信号词前置**：含"使用时机：/Use when/触发/接到…时"一类触发面词，且置于句首。
3. **R3 排除句**：含一句硬边界（"排除：…；已明确指定其他技能时不重复加载"）。

## 入池门禁（新技能强制）

- [ ] lint 通过（三规则全绿）
- [ ] 家族地图登记（skill-directory 的家族表加一行：家族/前缀/触发词例）
- [ ] 触发词与既有技能去重（同族 ≥2 词交叠的考虑合并）
- [ ] 进入零调用复审周期（30 天）

## 复审节律

- 每批改造后：audit 复扫 → Δ(invocations)/Δ(gray-rate)/Δ(catalog chars) 三指标入档
- 零调用榜 top-20 每月人工过一遍：改 desc / 合并入家族 / 下池三选一
- 目录字符预算：每轮 ≤ 8k 字符（超出即触发挂载收敛复议）

## 批量改造纪律（dsh-skill-desc-rewrite.py）

- 只动 frontmatter 的 description 字段，正文一字不碰
- 每文件先写 `.descbak-<ts>` 备份；回滚 = 拷回
- 符号链接一律跳过（保护真本）；sci-* 真本永不在改造范围
- dry-run 报告先行，`--apply` 才落盘；改前/改后 lint 快照都进论文 data/
