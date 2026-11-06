# data/ 数据留存说明 — paper-ai-00001

> 纪律：快照永不覆盖删除；SHA256SUMS 随每次公开提交更新；模型归因见 PROVENANCE.md

## 文件清单（2026-11-06 时点）

| 文件 | 内容 | 地位 |
|---|---|---|
| skill_audit_20261106_104459.json/.csv | 初扫（提取层 bug 期） | L1 修正链证据，保留 |
| skill_audit_20261106_104835.json/.csv | 上午正式版（论文正文引用口径） | S3 基线 |
| skill_audit_20261106_115000.json/.csv | **audit v2 + L3 批次一部署后首扫（含模型归因 10 项）** | L3 批次一 T0 |
| desc_lint_20261106_112124.json | 改造前 lint（SOP 通过率 0.87%） | P2 前测 |
| desc_rewrite_20261106_114700_dryrun.json | 改造 dry-run（首版模板） | 过程留痕 |
| desc_rewrite_20261106_114831_dryrun.json | 改造 dry-run（真本池 88 条） | 过程留痕 |
| desc_rewrite_20261106_114930_applied.json | 改造落盘（88 条，备份 .descbak 同名 ts） | P2 部署证据 |
| desc_lint_20261106_114930.json | 改造后 lint（SOP 通过率 95.45%） | P2 后测 |
| PROVENANCE.md | 模型/工具链/批次记录（滚动更新） | 诚信档案 |
| SHA256SUMS | 本目录全部文件哈希（每次新增数据后重算） | 完整性 |

## 解读入口

字段口径见 `~/mydsh/plugins/dsh-skill-governance/docs/DATA_SCHEMA.md`（公开包同文）。
