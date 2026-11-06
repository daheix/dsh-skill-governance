#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dsh-skill-audit.py — dsh 技能目录落灰审计遥测 (M18, paper-ai-00001 S3 数据生产器)

单进程遍历 $DSH_SESSIONS/**/session.v4.jsonl.zstd，逐行流式解压统计：
  - 技能目录消息（<available_skills>，catalog 快照与 update 变体）条数、每条字符数、最大值
  - 目录条目（- `name`: descr）逐名统计——得出"目录暴露过的技能全集"及每名被目录多少次
  - 技能调用痕迹（tool 结果标题 `Load skill <name>`）按名计数
  - skill 工具定义出现次数（`"name":"skill"` 结构）与 <skill_content> 直调块次数
输出：
  OUT/skill_audit_<ts>.json          全局聚合（含零调用榜）
  OUT/skill_audit_<ts>_stores.csv    每个 store 一行明细
  DSH_AUDIT_LOG（默认 ~/.dsh/logs/skill-audit.log）追加一行摘要
诚实性：所有计数来自真实解压后的字节与 JSON 字段；范式外的守门（JSON 解析失败）退化为
整行正则计数并在 parse_failures 记录；token 数字只做 chars/4 估算并显式标注为估算值。
"""
import csv
import glob
import json
import os
import re
import subprocess
import sys
import time
import traceback
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("DSH_SESSIONS", "/home/wsc/.dsh/sessions"))
OUT = Path(os.environ.get("DSH_AUDIT_OUT", "/home/wsc/wsc/sci/paper-ai-00001/data"))
LOG = Path(os.environ.get("DSH_AUDIT_LOG", "/home/wsc/.dsh/logs/skill-audit.log"))

CATALOG_MARK = "<available_skills>"          # 目录消息正文标记（catalog/update 共用）
CAT_UPDATE_MARK = "replaces every earlier available-skills list"
ENTRY_RE = re.compile(r"^- `([^`\n]+)`: ", re.M)   # 条目行：- `skill-name`: 描述…（多行标志必须）
INVOKE_RE = re.compile(r"\bLoad skill ([A-Za-z0-9][A-Za-z0-9_.+-]*)")
CONTENT_MARK = b"skill_content"              # 用户直调技能时注入的正文块
SKILLDEF_RE = re.compile(r'"name"\s*:\s*"skill"(?=[,\}])')


def _add_blocks(content, out):
    """把 content（块列表或纯字符串）里的 text 全部收进 out。"""
    if isinstance(content, str):
        out.append(content)
    elif isinstance(content, list):
        for b in content:
            if isinstance(b, dict) and isinstance(b.get("text"), str):
                out.append(b["text"])


def record_texts(rec):
    """兼容 v3/v4 两种记录形状，收集一行 JSON 记录里的全部 text。"""
    out = []
    data = rec.get("data") or {}
    _add_blocks(data.get("content"), out)              # user/message: data.content
    msg = data.get("message") or {}
    _add_blocks(msg.get("content"), out)               # 嵌套变体: data.message.content
    return "\n".join(out)


def extract_catalog_text(raw_line: str):
    """从 JSONL 行提取目录正文；解析失败退回到仅反转义 \\n 的整行（退化计数，不丢样本）。"""
    try:
        rec = json.loads(raw_line)
        joined = record_texts(rec)
        if CATALOG_MARK in joined:
            return joined
    except Exception:
        pass
    if CATALOG_MARK in raw_line:
        return re.sub(r"\\n", "\n", raw_line.replace("\\\\n", "\\n"))  # 退化路径
    return None


def scan_store(zstd_path: Path):
    """返回 (统计dict, 本store目录暴露名集合)。内存常数，逐行。"""
    st = {
        "scope": zstd_path.parts[-3] if len(zstd_path.parts) >= 3 else "",
        "session": zstd_path.parent.name,
        "lines": 0,
        "raw_bytes": 0,          # 解压后 JSONL 总字节
        "catalog_msgs": 0,
        "catalog_update_msgs": 0,
        "catalog_entry_mentions": 0,
        "unique_entries": 0,
        "skill_defs": 0,
        "skill_tool_calls": 0,
        "skill_content_blocks": 0,
        "skill_content_user_blocks": 0,
        "skill_content_tool_blocks": 0,
        "degraded_catalog_lines": 0,
        "invocations": 0,
        "max_catalog_chars": 0,  # 单条目录消息最大字符数
        "catalog_chars_total": 0,
    }
    entry_counter = Counter()    # 本 store 内条目名 → 出现次数
    inv_counter = Counter()      # 本 store 内成功加载名（Load skill 标题） → 次数
    call_counter = Counter()     # 本 store 内 skill 工具调用名（含失败） → 次数
    model_counter = Counter()    # 本 store 内请求模型（provider/model）→ 轮次（模型归因）
    content_counter = Counter()  # 本 store 内按名交付正文（skill_content tool 结果）→ 次数
    proc = subprocess.Popen(
        ["zstd", "-dc", str(zstd_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=1024 * 1024,
    )
    assert proc.stdout is not None
    try:
        for raw in proc.stdout:
            rb = len(raw)
            st["lines"] += 1
            st["raw_bytes"] += rb
            if not raw.strip():
                continue
            if b"<available_skills>" in raw:
                line = raw.decode("utf-8", errors="replace")
                text = extract_catalog_text(line)
                if text is not None:
                    st["catalog_msgs"] += 1
                    if CAT_UPDATE_MARK in text:
                        st["catalog_update_msgs"] += 1
                    for name in ENTRY_RE.findall(text):
                        entry_counter[name] += 1
                    st["catalog_chars_total"] += len(text)
                    if len(text) > st["max_catalog_chars"]:
                        st["max_catalog_chars"] = len(text)
                    if '"' in text and "\\n" in text:   # JSON 退化行（哈希标题可辨）
                        st["degraded_catalog_lines"] += 1
                continue
            if b"Load skill " in raw:
                for h in INVOKE_RE.findall(raw.decode("utf-8", errors="replace")):
                    inv_counter[h] += 1
                continue
            if CONTENT_MARK in raw:
                n = raw.count(b"<skill_content")
                st["skill_content_blocks"] += n
                if b'"type":"user/message"' in raw:
                    st["skill_content_user_blocks"] += n
                elif b'"type":"tool/result"' in raw:
                    st["skill_content_tool_blocks"] += n
                    for m in re.findall(rb'<skill_content[^>]*name=\\?"([^"\\]+)\\?"', raw):
                        content_counter[m.decode("utf-8", errors="replace")] += 1
                continue
            if b'"type":"request/context"' in raw:
                try:
                    rec = json.loads(raw.decode("utf-8", errors="replace"))
                    d = rec.get("data", {})
                    pv, mo = d.get("provider"), d.get("model")
                    if pv or mo:
                        model_counter[f"{pv}/{mo}"] += 1
                except Exception:
                    pass
                continue
            if b'"name": "skill"' in raw or b'"name":"skill"' in raw:
                line = raw.decode("utf-8", errors="replace")
                st["skill_defs"] += len(SKILLDEF_RE.findall(line))
                if b"tool/call" in raw or b"tool_call" in raw:
                    try:
                        rec = json.loads(line)
                        d = rec.get("data", {})
                        if d.get("name") == "skill":
                            st["skill_tool_calls"] += 1
                            args = d.get("arguments")
                            try:
                                a = (json.loads(args) if isinstance(args, str)
                                     else args if isinstance(args, dict) else {})
                                nm = a.get("name")
                            except Exception:
                                nm = None
                            if isinstance(nm, str) and nm:
                                call_counter[nm] += 1
                    except Exception:
                        pass
                continue
    finally:
        try:
            proc.stdout.close()
        finally:
            ret = proc.wait()
            if ret != 0:
                st["zstd_exit"] = ret
    st["unique_entries"] = len(entry_counter)
    st["catalog_entry_mentions"] = sum(entry_counter.values())
    st["invocations"] = sum(inv_counter.values())
    st["entry_counter"] = entry_counter
    st["invoked_names"] = inv_counter
    st["call_counter"] = call_counter
    st["model_counter"] = model_counter
    st["content_counter"] = content_counter
    return st


def main():
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    files = sorted(Path(p) for p in glob.glob(str(ROOT / "**" / "session.v4.jsonl.zstd"),
                                              recursive=True))
    if not files:
        print("no session.v4.jsonl.zstd found under", ROOT, file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)

    global_entry = Counter()          # 条目名 → 全部目录消息累计条数
    entry_stores = defaultdict(set)   # 条目名 → 出现过的 store_id
    global_inv = Counter()            # 成功加载名 → 次数
    inv_stores = defaultdict(set)
    global_call = Counter()           # skill 工具调用名（含失败） → 次数
    call_stores = defaultdict(set)
    global_model = Counter()          # provider/model → 请求轮次（模型归因）
    global_content = Counter()        # 按名交付正文（skill_content tool 结果） → 次数
    global_model = Counter()          # provider/model → 请求轮次（模型归因）
    rows = []
    parse_failures = 0
    t0 = time.time()

    for i, zp in enumerate(files, 1):
        sid = f"s{i:04d}"
        try:
            st = scan_store(zp)
        except Exception:
            parse_failures += 1
            print(f"WARN parse fail {zp}\n{traceback.format_exc()}", file=sys.stderr)
            continue
        for name, c in st["entry_counter"].items():
            global_entry[name] += c
            entry_stores[name].add(sid)
        for name, c in st["invoked_names"].items():
            global_inv[name] += c
            inv_stores[name].add(sid)
        for name, c in st["call_counter"].items():
            global_call[name] += c
            call_stores[name].add(sid)
        for mk, c in st["model_counter"].items():
            global_model[mk] += c
        for ck, c in st["content_counter"].items():
            global_content[ck] += c
        ec = st.pop("entry_counter")
        ic = st.pop("invoked_names")
        cc = st.pop("call_counter")
        mc = st.pop("model_counter")
        kc = st.pop("content_counter")
        row = {"store_id": sid, **st,
               "models": ";".join(sorted(mc)),
               "model_calls": sum(mc.values()),
               "content_loads": sum(kc.values())}
        rows.append(row)

    csv_path = OUT / f"skill_audit_{ts}_stores.csv"
    fields = ["store_id", "scope", "session", "lines", "raw_bytes",
              "catalog_msgs", "catalog_update_msgs", "catalog_entry_mentions",
              "unique_entries", "catalog_chars_total", "max_catalog_chars",
              "skill_defs", "skill_tool_calls", "skill_content_blocks",
              "skill_content_user_blocks", "skill_content_tool_blocks",
              "degraded_catalog_lines", "invocations", "models",
              "model_calls", "content_loads", "zstd_exit"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    invoked = set(global_inv)
    delivered = set(global_content)
    loaded_any = invoked | delivered
    zero_call = sorted(
        ({name: {"stores": len(entry_stores[name]), "mentions": global_entry[name]}
          for name in global_entry if name not in loaded_any}).items(),
        key=lambda kv: -kv[1]["mentions"])
    top_stores = sorted(rows, key=lambda r: -r["catalog_msgs"])[:20]
    catalog_chars = sum(r["catalog_chars_total"] for r in rows)
    summary = {
        "tool": "dsh-skill-audit.py M18",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(ROOT),
        "files_found": len(files),
        "files_scanned": len(rows),
        "parse_failures": parse_failures,
        "elapsed_seconds": round(time.time() - t0, 1),
        "totals": {
            "stores": len(rows),
            "store_lines": sum(r["lines"] for r in rows),
            "decompressed_bytes": sum(r["raw_bytes"] for r in rows),
            "catalog_msgs": sum(r["catalog_msgs"] for r in rows),
            "catalog_update_msgs": sum(r["catalog_update_msgs"] for r in rows),
            "catalog_entry_mentions": sum(r["catalog_entry_mentions"] for r in rows),
            "unique_entry_names": len(global_entry),
            "catalog_chars_total": catalog_chars,
            "catalog_tokens_char_div4_estimate": catalog_chars // 4,
            "max_catalog_chars_single": max((r["max_catalog_chars"] for r in rows), default=0),
            "skill_defs_occurrences": sum(r["skill_defs"] for r in rows),
            "skill_tool_calls": sum(r["skill_tool_calls"] for r in rows),
            "skill_content_blocks": sum(r["skill_content_blocks"] for r in rows),
            "skill_content_user_blocks": sum(r["skill_content_user_blocks"] for r in rows),
            "skill_content_tool_blocks": sum(r["skill_content_tool_blocks"] for r in rows),
            "degraded_catalog_lines": sum(r["degraded_catalog_lines"] for r in rows),
            "invocations": sum(r["invocations"] for r in rows),
            "unique_invoked_names": len(global_inv),
            "distinct_models": len(global_model),
            "content_loads_delivered": sum(r["content_loads"] for r in rows),
            "unique_content_loaded_names": len(global_content),
            "unique_loaded_names_union": len(loaded_any),
        },
        "store_presence": {
            "stores_with_catalog": sum(1 for r in rows if r["catalog_msgs"] > 0),
            "stores_with_invocation": sum(1 for r in rows if r["invocations"] > 0),
            "stores_with_tool_calls": sum(1 for r in rows if r["skill_tool_calls"] > 0),
            "stores_with_skill_content": sum(1 for r in rows if r["skill_content_blocks"] > 0),
        },
        "top_stores_by_catalog_msgs": [
            {k: r[k] for k in fields if k in r} for r in top_stores],
        "invoked_names": dict(global_inv.most_common()),
        "attempted_names": dict(global_call.most_common()),
        "model_attribution": dict(global_model.most_common()),
        "content_loaded_names": dict(global_content.most_common()),
        "zero_call_leaderboard": dict(zero_call),
        "zero_call_count": len(zero_call),
    }
    json_path = OUT / f"skill_audit_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1, default=str)

    t = summary["totals"]
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(
            f"[{ts}] stores={t['stores']}/{summary['files_found']} "
            f"catalog_msgs={t['catalog_msgs']} unique_entry_names={t['unique_entry_names']} "
            f"entry_mentions={t['catalog_entry_mentions']} "
            f"catalog_chars={t['catalog_chars_total']} "
            f"max_catalog_chars={t['max_catalog_chars_single']} "
            f"tool_calls={t['skill_tool_calls']} "
            f"invocations={t['invocations']} invoked_names={t['unique_invoked_names']} "
            f"zero_call={summary['zero_call_count']} "
            f"parse_fail={parse_failures} elapsed={summary['elapsed_seconds']}s "
            f"json={json_path.name}\n")

    print(json.dumps(summary["totals"], ensure_ascii=False, indent=2))
    print("zero-call leaderboard:", summary["zero_call_count"], "names")
    print("JSON:", json_path)
    print("CSV :", csv_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
