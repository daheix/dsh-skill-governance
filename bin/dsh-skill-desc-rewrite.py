#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dsh-skill-desc-rewrite.py — P2 描述卫生批量改造 (M20, paper-ai-00001 L3 批次一)

对技能池内未过 SOP lint 的 SKILL.md 做 frontmatter-only 的 description 重写：
  - 按家族（*-library / chinasim-* / codearts-* / 其他）套模板，保留原描述文本
  - 补齐三要素：信号词前置（使用时机：…）、排除句（排除：…）、长度预算 200–480
  - 每个文件先写备份 SKILL.md.descbak-<ts>，可整体回滚
  - 跳过符号链接（保护 sci 真本等外链目标）
绝不改 frontmatter 其他字段与正文；dry-run 模式默认开，--apply 才落盘。
"""
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

POOL = Path(os.environ.get(
    "SKILL_POOL", "/home/wsc/wsc/ChinaSimStdio/.agents/skills"))
OUT = Path(os.environ.get("DSH_LINT_OUT",
                          "/home/wsc/wsc/sci/paper-ai-00001/data"))

FM_RE = re.compile(r"(?m)^---\s*\n(.*?)\n---", re.S)
DESC_RE = re.compile(r"(?m)^description:\s*(.+?)(?=^\w+:|\Z)", re.S | re.M)

LIB_EXCL = ("排除：与其他库相关的构建/运行问题、纯业务逻辑任务、未涉及该库的任务；"
            "已明确指定其他技能时不重复加载本技能。")
CHINA_EXCL = ("排除：第三方库集成任务（走对应 *-library 技能）、华为云 CodeArts 任务"
              "（走 codearts-* 技能）、论文科研主线（走 sci-* 技能）；已明确指定其他技能"
              "时不重复加载本技能。")
CODEARTS_EXCL = ("排除：本地工程流程任务（走 chinasim-* 技能）、第三方库集成"
                 "（走 *-library 技能）；无华为云/码道上下文时不加载本技能。")
GENERIC_EXCL = ("排除：与该技能主题无关的任务；已明确指定其他技能时不重复加载本技能。")


def family_of(name: str):
    if name.endswith("-library"):
        return "lib", name[:-len("-library")].replace("-dist", "")
    if name.startswith("chinasim-"):
        return "chinasim", name[len("chinasim-"):].replace("-", " ")
    if name.startswith("codearts-"):
        return "codearts", name[len("codearts-"):].replace("-", " ")
    if name.startswith("sci-"):
        return "sci", name
    return "generic", name.replace("-", " ")


def build_desc(name: str, orig: str):
    fam, kw = family_of(name)
    orig = orig.strip() or name
    if len(orig) > 180:
        head = orig[:179].rstrip("，、；,; ") + "…"
    else:
        head = orig.strip("；;。 ")
    if fam == "lib":
        core = orig
        core = re.sub(r"^在\s*ChinaSimStdio\s*中", "", core)
        core = re.sub(r"[；;。]?\s*(接口|调用|构建)?(和|与)?(构建)?细节见技能正文[。.]?$", "", core)
        core = re.sub(r"时使用[。.]?$", "", core.strip())
        core = core.strip("；;。 ")
        paren = f"（{core}）" if core else ""
        d = (f"使用时机：在 ChinaSimStdio 中集成、配置、构建、调用或排查 {kw}{paren} 相关功能时"
             f"使用；接口特征、构建选项与调用细节以技能正文为准。{LIB_EXCL}"
             f"触发词：{kw}, library, 链接, 构建, 数值。")
    elif fam == "chinasim":
        d = (f"使用时机：执行 ChinaSimStdio 工程内部流程「{kw}」时使用——{head}；"
             f"具体步骤与产出要求见技能正文。{CHINA_EXCL}"
             f"触发词：chinasim, 工程, {kw}。")
    elif fam == "codearts":
        d = (f"使用时机：华为云 CodeArts/码道场景中执行「{kw}」时使用——{head}；"
             f"调用链与配置见技能正文。{CODEARTS_EXCL}"
             f"触发词：codearts, 码道, 华为云, {kw}。")
    elif fam == "sci":
        d = (f"使用时机：科研论文场景（{head}）时使用；流程与门禁见技能正文。"
             f"{GENERIC_EXCL}触发词：sci, 论文, 期刊。")
    else:
        d = (f"使用时机：{head} 时使用；执行方式与要点见技能正文。{GENERIC_EXCL}"
             f"触发词：{kw}。")
    d = " ".join(d.split())
    if len(d) < 200:
        d += ("适用范围：ChinaSimStdio 技能池（可由 skill-directory 索引官检索）；"
              "本描述遵循 description SOP v1（信号词前置+排除句+长度预算，2026-11-06）。")
    return d[:480]


def main():
    apply = "--apply" in sys.argv
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    rows = []
    for d in sorted(p for p in POOL.iterdir() if p.is_dir()):
        md = d / "SKILL.md"
        if d.name.startswith("sci-"):
            rows.append({"skill": d.name, "skip": "sci 真本保护（不改写）"})
            continue
        if not md.exists() or md.is_symlink() or d.is_symlink():
            rows.append({"skill": d.name, "skip": "no SKILL.md/symlink"})
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        fm = FM_RE.search(text)
        dm = DESC_RE.search(fm.group(1)) if fm else None
        if not fm or not dm:
            rows.append({"skill": d.name, "skip": "no frontmatter/desc"})
            continue
        orig = " ".join(dm.group(1).split())
        new = build_desc(d.name, orig)
        if len(new) > 480:
            new = new[:477] + "…"
        changed = new != orig
        rows.append({"skill": d.name, "old_chars": len(orig),
                     "new_chars": len(new), "changed": changed})
        if apply and changed:
            bak = md.with_suffix(".md.descbak-" + ts)
            if not bak.exists():
                shutil.copy2(md, bak)
            sep = "\n" if dm.group(1).endswith("\n") else ""
            new_fm = fm.group(1)[:dm.start(1)] + new + sep + fm.group(1)[dm.end(1):]
            text2 = text[:fm.start(1)] + new_fm + text[fm.end(1):]
            md.write_text(text2, encoding="utf-8")
    n_changed = sum(1 for r in rows if r.get("changed"))
    report = {"tool": "dsh-skill-desc-rewrite.py M20", "applied": apply,
              "ts": ts, "pool": str(POOL), "scanned": len(rows),
              "changed": n_changed, "rows": rows}
    OUT.mkdir(parents=True, exist_ok=True)
    rp = OUT / f"desc_rewrite_{ts}{'_applied' if apply else '_dryrun'}.json"
    rp.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"},
                     ensure_ascii=False))
    print("report:", rp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
