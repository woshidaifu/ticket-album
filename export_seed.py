#!/usr/bin/env python3
"""把 tickets.db 导出为纯文本快照 seed.sql（可重复运行的维护工具）。

用法: python3 export_seed.py [输出路径]     # 默认写 resource/db/seed.sql
重建: sqlite3 resource/db/tickets.db < resource/db/seed.sql  # 对空库执行，旧库请先备份

说明: 只导出结构化数据。票面图片是 resource/pic/ 下的独立 jpg 文件，
      不包含在 SQL 里，重建时需要一并保留图片文件。
"""
import os
import sqlite3
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "resource", "db", "tickets.db")
TABLES = ["tickets", "ticket_fields", "ticket_images", "trips"]


def literal(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, bytes):
        return "X'" + v.hex() + "'"
    return "'" + str(v).replace("'", "''") + "'"


def main(out_path):
    con = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    counts = {t: con.execute("SELECT COUNT(*) FROM " + t).fetchone()[0] for t in TABLES}

    lines = [
        "-- 门票收藏册 · SQLite 全库快照",
        "-- 生成时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "-- 来源: tickets.db  (" + ", ".join(str(counts[t]) + " " + t for t in TABLES) + ")",
        "-- 重建: sqlite3 resource/db/tickets.db < resource/db/seed.sql  （对空库执行；旧库请先备份）",
        "-- 说明: 只含结构化数据，图片在 resource/pic/ 下，需另行保留。",
        "",
        "PRAGMA foreign_keys=OFF;",
        "BEGIN;",
        "",
    ]

    for t in TABLES:
        row = con.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)
        ).fetchone()
        if not row or not row[0]:
            raise RuntimeError("缺少表定义: " + t)
        lines.append(row[0].strip() + ";")
    lines.append("")

    for t in TABLES:
        rows = con.execute("SELECT * FROM " + t + " ORDER BY id").fetchall()
        cols = [d[0] for d in con.execute("SELECT * FROM " + t + " LIMIT 0").description]
        col_sql = ", ".join('"' + c + '"' for c in cols)
        lines.append("-- " + t + " (" + str(len(rows)) + " 行)")
        for r in rows:
            vals = ", ".join(literal(r[c]) for c in cols)
            lines.append("INSERT INTO " + t + " (" + col_sql + ") VALUES (" + vals + ");")
        lines.append("")

    has_seq = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'"
    ).fetchone()
    if has_seq:
        seq = con.execute("SELECT name, seq FROM sqlite_sequence ORDER BY name").fetchall()
        if seq:
            lines.append("DELETE FROM sqlite_sequence;")
            for r in seq:
                lines.append(
                    "INSERT INTO sqlite_sequence (name,seq) VALUES ("
                    + literal(r["name"]) + "," + literal(r["seq"]) + ");"
                )
            lines.append("")

    for r in con.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY name"
    ):
        lines.append(r[0].strip() + ";")
    lines += ["", "COMMIT;", ""]

    con.close()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("written:", out_path, os.path.getsize(out_path), "bytes")
    print("rows:", counts)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1
         else os.path.join(BASE, "resource", "db", "seed.sql"))
