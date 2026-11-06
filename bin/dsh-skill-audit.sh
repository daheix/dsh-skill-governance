#!/usr/bin/env bash
# dsh-skill-audit.sh — 技能目录落灰审计（M18，paper-ai-00001 真数据生产器）
# 扫 ~/.dsh/sessions/**/session.v4.jsonl.zstd，输出落 dsh-skill-audit.py 同目录说明
#   数据目录: DSH_AUDIT_OUT（默认 ~/wsc/wsc/sci/paper-ai-00001/data）
#   日志:     DSH_AUDIT_LOG（默认 ~/.dsh/logs/skill-audit.log）
# 用法: dsh-skill-audit.sh           # 全量扫描
# 说明: 整个逻辑在 dsh-skill-audit.py，此处只做入口，避免复制逻辑。
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/dsh-skill-audit.py" "$@"
