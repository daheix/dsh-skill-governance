#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dsh-skill-memory.py — P4 技能记忆索引构建器 (M20, paper-ai-00001)

从 audit 快照（skill_audit_*.json）构建 SQLite 记忆索引：
  tables:
    audit_runs(run_ts, generated_at, totals_json)
    skill_names(name, stores, mentions, invoked, invoked_stores, attempt_count)
    invocations(name, count, stores)
    models(provider_model, calls)
    meta(key, value)
用法:
  dsh-skill-memory.py build  <audit_json> [--db PATH]
  dsh-skill-memory.py query  <skill-name> [--db PATH]
  dsh-skill-memory.py stats  [--db PATH]
默认 DB: $DSH_MEMORY_DB（默认 ~/.dsh/skill-memory.db）
用途：会话开始时供 memory 工具按技能名查询"上次何时/是否被真实加载过"，
给模型跨会话先验（"你上次用 X 干这类活"），无需任何 embedding 模型。
"""
import glob
import json
import os
import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = os.environ.get("DSH_MEMORY_DB", "/home/wsc/.dsh/skill-memory.db")
DATA_DIR = os.environ.get("DSH_AUDIT_OUT", "/home/wsc/wsc/sci/paper-ai-00001/data")

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_runs(
  run_ts TEXT PRIMARY KEY, generated_at TEXT, totals_json TEXT);
CREATE TABLE IF NOT EXISTS skill_names(
  name TEXT PRIMARY KEY, stores INTEGER, mentions INTEGER,
  invoked INTEGER DEFAULT 0, invoked_stores INTEGER DEFAULT 0,
  attempt_count INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS invocations(
  name TEXT PRIMARY KEY, count INTEGER, stores INTEGER);
CREATE TABLE IF NOT EXISTS models(
  provider_model TEXT PRIMARY KEY, calls INTEGER);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
"""


def latest_audit():
    ps = sorted(glob.glob(str(Path(DATA_DIR) / "skill_audit_2*.json")))
    if not ps:
        sys.exit("no audit json found in " + DATA_DIR)
    return ps[-1]


def build(audit_path: str, db_path: str):
    d = json.loads(Path(audit_path).read_text(encoding="utf-8"))
    t = d["totals"]
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    run_ts = Path(audit_path).stem.replace("skill_audit_", "")
    con.execute("INSERT OR REPLACE INTO audit_runs VALUES(?,?,?)",
                (run_ts, d.get("generated_at", ""), json.dumps(t, ensure_ascii=False)))
    zero = d.get("zero_call_leaderboard", {})
    inv = d.get("invoked_names", {})
    att = d.get("attempted_names", {})
    # union of all names
    names = set(zero) | set(inv) | set(att)
    for name in names:
        z = zero.get(name, {})
        con.execute("INSERT OR REPLACE INTO skill_names VALUES(?,?,?,?,?,?)",
                    (name, z.get("stores", 0), z.get("mentions", 0),
                     inv.get(name, 0), len(inv) and inv.get(name, 0) and 1 or 0,
                     att.get(name, 0)))
    for name, c in inv.items():
        con.execute("INSERT OR REPLACE INTO invocations VALUES(?,?,?)",
                    (name, c, 1))
    for mk, c in d.get("model_attribution", {}).items():
        con.execute("INSERT OR REPLACE INTO models VALUES(?,?)", (mk, c))
    con.execute("INSERT OR REPLACE INTO meta VALUES('source',?)", (audit_path,))
    con.execute("INSERT OR REPLACE INTO meta VALUES('files_scanned',?)",
                (str(t.get("stores", 0)),))
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM skill_names").fetchone()[0]
    g = con.execute("SELECT COUNT(*) FROM models").fetchone()[0]
    print(f"built {db_path}: skill_names={n} models={g} run={run_ts}")
    con.close()


def query(name: str, db_path: str):
    con = sqlite3.connect(db_path)
    row = con.execute("SELECT * FROM skill_names WHERE name=?", (name,)).fetchone()
    if not row:
        print(json.dumps({"name": name, "known": False}))
        return
    cols = ["name", "stores", "mentions", "invoked", "invoked_stores", "attempt_count"]
    print(json.dumps(dict(zip(cols, row)), ensure_ascii=False))


def stats(db_path: str):
    con = sqlite3.connect(db_path)
    runs = con.execute("SELECT run_ts, generated_at FROM audit_runs").fetchall()
    total = con.execute("SELECT COUNT(*) FROM skill_names").fetchone()[0]
    inv = con.execute("SELECT COUNT(*) FROM skill_names WHERE invoked>0").fetchone()[0]
    models = con.execute("SELECT provider_model, calls FROM models ORDER BY calls DESC").fetchall()
    print(json.dumps({"runs": runs, "names": total, "with_invocations": inv,
                      "models": models}, ensure_ascii=False, indent=1))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    db = DEFAULT_DB
    if "--db" in sys.argv:
        db = sys.argv[sys.argv.index("--db") + 1]
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    if cmd == "build":
        build(sys.argv[2], db)
    elif cmd == "query" and len(sys.argv) > 2:
        query(sys.argv[2], db)
    else:
        stats(db)


if __name__ == "__main__":
    main()
