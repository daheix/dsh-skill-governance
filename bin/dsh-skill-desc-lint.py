#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dsh-skill-desc-lint.py — 技能 description 卫生 lint (M19, paper-ai-00001 §5.3 P2)

只读扫描技能池（默认 ChinaSimStdio/.agents/skills/），对每个 SKILL.md 的 frontmatter
description 检查三条 SOP 规则：
  R1 长度预算：200–480 字符（目录条目截断宽限 500）
  R2 信号词前置：含"使用时机/Use when/触发/接到/需要…时"一类触发面词
  R3 排除句：含"排除/不用/除外/不适用/not for"一类硬边界句
输出 JSON（OUT/desc_lint_<ts>.json）+ stdout 摘要；绝不改写技能文件。
"""
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

POOL = Path(os.environ.get(
    "SKILL_POOL",
    "/home/wsc/wsc/ChinaSimStdio/.agents/skills"))
OUT = Path(os.environ.get("DSH_LINT_OUT",
                          "/home/wsc/wsc/sci/paper-ai-00001/data"))

FM_RE = re.compile(r"(?m)^---\s*\n(.*?)\n---", re.S)
DESC_RE = re.compile(r"(?m)^description:\s*(.+?)(?=^\w+:|\Z)", re.S | re.M)
SIGNAL_RE = re.compile(r"使用时机|使用：|触发|Use when|when |接到|需要.{0,12}时|适用[於于]|用于|用來|用来")
EXCLUDE_RE = re.compile(r"排除|不用[於于]|不适用|不索引|不重复|not for|不要|除外|先走|改用|crosses|改投")
HARD_RE = re.compile(r"^---\s*$", re.M)


def first_fm_block(text: str):
    m = FM_RE.search(text)
    return m.group(1) if m else None


def lint_one(skill_dir: Path):
    md = skill_dir / "SKILL.md"
    if not md.exists():
        return {"skill": skill_dir.name, "error": "no SKILL.md"}
    text = md.read_text(encoding="utf-8", errors="replace")
    fm = first_fm_block(text)
    d = {"skill": skill_dir.name, "ok": False}
    if fm is None:
        d["error"] = "no frontmatter"
        return d
    dm = DESC_RE.search(fm)
    if not dm:
        d["error"] = "no description"
        return d
    desc = " ".join(dm.group(1).split())
    d["desc_chars"] = len(desc)
    d["r1_length"] = "pass" if 200 <= len(desc) <= 480 else (
        "short" if len(desc) < 200 else "over")
    d["r2_signal"] = bool(SIGNAL_RE.search(desc))
    d["r3_exclude"] = bool(EXCLUDE_RE.search(desc))
    d["ok"] = (d["r1_length"] == "pass" and d["r2_signal"] and d["r3_exclude"])
    d["head"] = desc[:80]
    return d


def main():
    dirs = sorted(p for p in POOL.iterdir() if p.is_dir())
    rows = [lint_one(p) for p in dirs]
    n = len(rows)
    ok = sum(1 for r in rows if r.get("ok"))
    by_r1 = {"pass": 0, "short": 0, "over": 0, "n/a": 0}
    for r in rows:
        v = r.get("r1_length", "n/a")
        if v == "n/a" or r.get("error"):
            by_r1["n/a"] += 1
        else:
            by_r1[v] += 1
    r2 = sum(1 for r in rows if r.get("r2_signal"))
    r3 = sum(1 for r in rows if r.get("r3_exclude"))
    fails = [r for r in rows if not r.get("ok")]
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"desc_lint_{ts}.json"
    report = {
        "tool": "dsh-skill-desc-lint.py M19",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pool": str(POOL),
        "pool_size": n,
        "sop_pass": ok,
        "sop_pass_rate": round(ok / n, 4) if n else 0,
        "r1_length_split": by_r1,
        "r2_signal_rate": round(r2 / n, 4) if n else 0,
        "r3_exclude_rate": round(r3 / n, 4) if n else 0,
        "violations": fails,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "violations"},
                     ensure_ascii=False, indent=2))
    print("violations:", len(fails))
    for r in fails[:12]:
        print("  -", r["skill"], r.get("r1_length"),
              "sig" if r.get("r2_signal") else "NOSIG",
              "exc" if r.get("r3_exclude") else "NOEXC",
              r.get("desc_chars", r.get("error")))
    print("JSON:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
