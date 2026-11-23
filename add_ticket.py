#!/usr/bin/env python3
"""一键入库+重生成：python3 add_ticket.py record.json
record.json 为 upsert 所需的 dict（含 fields）。
"""
import json, os, subprocess, sys
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from album_db import upsert, stats

def main():
    if len(sys.argv) != 2:
        print("用法: python3 add_ticket.py record.json"); return 1
    with open(sys.argv[1], encoding="utf-8") as f:
        rec = json.load(f)
    upsert(rec)
    subprocess.run([sys.executable, os.path.join(BASE, "build_album.py")], check=True)
    print("入库完成:", stats())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
