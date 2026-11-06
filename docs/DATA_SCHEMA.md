# DATA_SCHEMA — audit/lint 数据字典（数据留存规范 v1）

> 本文件是公开仓库的数据契约：任何快照只要给出本文件即可独立解读。

## skill_audit_<ts>.json（全局聚合）

| 字段 | 含义 | 计数口径 |
|---|---|---|
| totals.stores / store_lines / decompressed_bytes | 扫描面 | 全部 session.v4.jsonl.zstd 解压后 |
| totals.catalog_msgs | 目录消息总数 | 行含 `<available_skills>` 且 JSON 结构可解析（或退化行） |
| totals.catalog_update_msgs | 其中 update 变体 | 含 "replaces every earlier available-skills list" |
| totals.catalog_entry_mentions | 条目曝光总次数 | 目录正文内 `- \`name\`: ` 行计数（re.M） |
| totals.unique_entry_names | 唯一技能名数 | 跨全部目录消息去重 |
| totals.catalog_chars_total | 目录正文字符总量 | 诚实单位=字符；token 一律 chars÷4 估算并显式标注 |
| totals.max_catalog_chars_single | 单条目录最大字符数 | |
| totals.skill_defs_occurrences | `"name":"skill"` 结构出现次数 | 工具定义+调用记录混合口径（谨慎解释） |
| totals.skill_tool_calls | skill 工具调用记录数 | 仅 `type=tool/call` 且 name=skill 的记录 |
| totals.skill_content_blocks / user / tool | 直调正文块 | 排除目录提醒文本中的字样（分消息类型计数） |
| totals.invocations / unique_invoked_names | 成功加载 | tool 结果标题 `Load skill <name>`（含口头语假阳上界，正文显式声明） |
| totals.distinct_models | 去重请求模型数 | provider/model |
| store_presence.* | 有目录/有调用/有调用记录/有正文块的 store 数 | |
| zero_call_leaderboard | 零调用榜 | name → {stores, mentions}；与 invoked 集合作差 |
| model_attribution | 模型归因 | provider/model → 请求轮次（`type=request/context` 记录） |
| parse_failures / degraded_catalog_lines | 诚实性计数 | JSON 解析失败/退化行 |

## skill_audit_<ts>_stores.csv（每 store 一行）

store_id, scope, session, lines, raw_bytes, catalog_msgs, catalog_update_msgs,
catalog_entry_mentions, unique_entries, catalog_chars_total, max_catalog_chars,
skill_defs, skill_tool_calls, skill_content_blocks, skill_content_user_blocks,
skill_content_tool_blocks, degraded_catalog_lines, invocations, models(分号连接),
model_calls, zstd_exit

## desc_lint_<ts>.json

pool_size / sop_pass(_rate) / r1_length_split{pass,short,over} / r2_signal_rate /
r3_exclude_rate / violations[]（skill, desc_chars, r1/r2/r3, head）

## desc_rewrite_<ts>_{dryrun,applied}.json

scanned / changed / rows[]（skill, old_chars, new_chars, changed | skip 原因）；
applied=true 时同 ts 的 SKILL.md.descbak-<ts> 备份与池内文件一一对应。

## 留存纪律

- 快照带 UTC 时间戳，**永不覆盖、永不删除**； Corrections 走"新快照 + 台账注记"，旧件保留作修正链证据。
- 每次公开提交附 SHA256SUMS；session 标识为伪匿名 UUID。
