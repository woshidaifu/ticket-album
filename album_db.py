"""门票收藏册的数据层：SQLite 为唯一数据源。"""
import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "resource", "db", "tickets.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
  id          TEXT PRIMARY KEY,
  date        TEXT NOT NULL,
  date_label  TEXT NOT NULL,
  sub         TEXT,
  name        TEXT NOT NULL,
  short       TEXT,
  badge       TEXT,
  price       REAL DEFAULT 0,
  type        TEXT,
  place       TEXT,
  city        TEXT,
  province    TEXT,
  transport   INTEGER DEFAULT 0,
  transport_mode TEXT DEFAULT '',
  transport_from TEXT DEFAULT '',
  transport_to   TEXT DEFAULT '',
  lat         REAL,
  lng         REAL,
  img_file    TEXT NOT NULL,
  note        TEXT,
  date_source TEXT DEFAULT 'ticket',
  user_supplement TEXT DEFAULT '',
  created_at  TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS ticket_fields (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  ticket_id  TEXT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
  label      TEXT NOT NULL,
  value      TEXT,
  sort       INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS ticket_images (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  ticket_id  TEXT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
  side       TEXT NOT NULL DEFAULT '正面',
  img_file   TEXT NOT NULL,
  sort       INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_tickets_date ON tickets(date DESC);
CREATE INDEX IF NOT EXISTS idx_fields_ticket ON ticket_fields(ticket_id, sort);
CREATE INDEX IF NOT EXISTS idx_images_ticket ON ticket_images(ticket_id, sort);
"""


def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    # 旧库缺列时自动补上
    cols = {r[1] for r in conn.execute("PRAGMA table_info(tickets)").fetchall()}
    if "date_source" not in cols:
        conn.execute("ALTER TABLE tickets ADD COLUMN date_source TEXT DEFAULT 'ticket'")
    if "user_supplement" not in cols:
        conn.execute("ALTER TABLE tickets ADD COLUMN user_supplement TEXT DEFAULT ''")
    if "city" not in cols:
        conn.execute("ALTER TABLE tickets ADD COLUMN city TEXT DEFAULT ''")
    if "province" not in cols:
        conn.execute("ALTER TABLE tickets ADD COLUMN province TEXT DEFAULT ''")
    if "transport" not in cols:
        conn.execute("ALTER TABLE tickets ADD COLUMN transport INTEGER DEFAULT 0")
    if "transport_mode" not in cols:
        conn.execute("ALTER TABLE tickets ADD COLUMN transport_mode TEXT DEFAULT ''")
    if "transport_from" not in cols:
        conn.execute("ALTER TABLE tickets ADD COLUMN transport_from TEXT DEFAULT ''")
    if "transport_to" not in cols:
        conn.execute("ALTER TABLE tickets ADD COLUMN transport_to TEXT DEFAULT ''")
    conn.commit()
    # 迁移：旧票没有 ticket_images 记录的，把 img_file 作为"正面"补进去
    need = conn.execute(
        "SELECT COUNT(*) FROM tickets t WHERE NOT EXISTS "
        "(SELECT 1 FROM ticket_images i WHERE i.ticket_id=t.id)"
    ).fetchone()[0]
    if need:
        conn.execute(
            "INSERT INTO ticket_images (ticket_id,side,img_file,sort) "
            "SELECT id,'正面',img_file,0 FROM tickets t WHERE NOT EXISTS "
            "(SELECT 1 FROM ticket_images i WHERE i.ticket_id=t.id)"
        )
        conn.commit()
    return conn


def upsert(t):
    """t: dict，含 tickets 表字段 + fields=[(label, value), ...]"""
    conn = connect()
    cols = ["id", "date", "date_label", "sub", "name", "short", "badge",
            "price", "type", "place", "city", "province", "transport", "transport_mode",
            "transport_from", "transport_to", "lat", "lng", "img_file", "note",
            "date_source", "user_supplement"]
    vals = [t.get(c) for c in cols]
    placeholders = ",".join("?" for _ in cols)
    conn.execute(
        f"INSERT OR REPLACE INTO tickets ({','.join(cols)}) VALUES ({placeholders})",
        vals,
    )
    conn.execute("DELETE FROM ticket_fields WHERE ticket_id=?", (t["id"],))
    for i, (label, value) in enumerate(t.get("fields", [])):
        conn.execute(
            "INSERT INTO ticket_fields (ticket_id,label,value,sort) VALUES (?,?,?,?)",
            (t["id"], label, value, i),
        )
    # 图片：优先用 images 列表；没给就用 img_file 兜底当作"正面"
    conn.execute("DELETE FROM ticket_images WHERE ticket_id=?", (t["id"],))
    images = t.get("images") or [{"img_file": t.get("img_file"), "side": "正面"}]
    for i, im in enumerate(images):
        if isinstance(im, str):
            img_file, side = im, "正面"
        else:
            img_file, side = im.get("img_file"), im.get("side", "正面")
        if img_file:
            conn.execute(
                "INSERT INTO ticket_images (ticket_id,side,img_file,sort) VALUES (?,?,?,?)",
                (t["id"], side, img_file, i),
            )
    conn.commit()
    conn.close()


def all_tickets():
    conn = connect()
    rows = conn.execute("SELECT * FROM tickets ORDER BY date DESC").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["fields"] = [
            (x["label"], x["value"])
            for x in conn.execute(
                "SELECT label,value FROM ticket_fields WHERE ticket_id=? ORDER BY sort",
                (d["id"],),
            ).fetchall()
        ]
        imgs = [
            {"side": x["side"], "img_file": x["img_file"]}
            for x in conn.execute(
                "SELECT side,img_file FROM ticket_images WHERE ticket_id=? ORDER BY sort",
                (d["id"],),
            ).fetchall()
        ]
        d["images"] = imgs or [{"side": "正面", "img_file": d["img_file"]}]
        out.append(d)
    conn.close()
    return out


def remove(ticket_id):
    conn = connect()
    conn.execute("DELETE FROM tickets WHERE id=?", (ticket_id,))
    conn.execute("DELETE FROM ticket_fields WHERE ticket_id=?", (ticket_id,))
    conn.commit()
    conn.close()


def apply_supplements(supplements):
    """把用户在册子里填的补充写回库。supplements: {id: {date, note}}

    date 未变时不动 date_label（避免把「2019年7月」这类票面写法改掉）；
    note 显式传空串表示清空备注，未传则保留原值。
    """
    conn = connect()
    for tid, s in supplements.items():
        row = conn.execute(
            "SELECT date, date_label, note FROM tickets WHERE id=?", (tid,)
        ).fetchone()
        if not row:
            continue
        date = s.get("date") or row["date"]
        note = s["note"] if "note" in s else (row["note"] or "")
        if date != row["date"]:
            date_label = date.replace("-", ".") if date else ""
        else:
            date_label = row["date_label"]
        conn.execute(
            "UPDATE tickets SET date=?, date_label=?, note=?, date_source='user' WHERE id=?",
            (date, date_label, note, tid),
        )
    conn.commit()
    conn.close()


def stats():
    rows = all_tickets()
    dated = [r["date"] for r in rows if r["date"]]
    span = dated[-1][:4] + "–" + dated[0][2:4] if dated else ""
    return {
        "count": len(rows),
        "spots": len({r["name"] for r in rows}),
        "total": sum(r["price"] or 0 for r in rows),
        "span": span,
        "pending": len(rows) - len(dated),
    }


if __name__ == "__main__":
    for t in all_tickets():
        print(t["date"], t["name"], t["price"], "字段数:", len(t["fields"]))
    print(stats())
