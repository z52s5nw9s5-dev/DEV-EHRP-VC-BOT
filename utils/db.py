from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from config import DB_PATH


def _connect() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with _connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS settings (
            guild_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            PRIMARY KEY (guild_id, key)
        );
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL,
            undone INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(guild_id, name)
        );
        CREATE TABLE IF NOT EXISTS absences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            reason TEXT,
            until_at TEXT,
            created_at TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS temp_voice (
            channel_id INTEGER PRIMARY KEY,
            guild_id INTEGER NOT NULL,
            owner_id INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS changelog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            author_id INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        """)


def set_setting(guild_id: int, key: str, value: str | int | None) -> None:
    with _connect() as con:
        con.execute(
            "INSERT INTO settings(guild_id,key,value) VALUES(?,?,?) ON CONFLICT(guild_id,key) DO UPDATE SET value=excluded.value",
            (guild_id, key, None if value is None else str(value)),
        )


def get_setting(guild_id: int, key: str, default: str | None = None) -> str | None:
    with _connect() as con:
        row = con.execute("SELECT value FROM settings WHERE guild_id=? AND key=?", (guild_id, key)).fetchone()
        return row["value"] if row else default


def all_settings(guild_id: int) -> dict[str, str | None]:
    with _connect() as con:
        return {r["key"]: r["value"] for r in con.execute("SELECT key,value FROM settings WHERE guild_id=?", (guild_id,))}


def record_action(guild_id: int, user_id: int, action: str, payload: dict) -> int:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as con:
        cur = con.execute(
            "INSERT INTO actions(guild_id,user_id,action,payload,created_at) VALUES(?,?,?,?,?)",
            (guild_id, user_id, action, json.dumps(payload, ensure_ascii=False), now),
        )
        return int(cur.lastrowid)


def last_action(guild_id: int):
    with _connect() as con:
        return con.execute(
            "SELECT * FROM actions WHERE guild_id=? AND undone=0 ORDER BY id DESC LIMIT 1", (guild_id,)
        ).fetchone()


def mark_undone(action_id: int) -> None:
    with _connect() as con:
        con.execute("UPDATE actions SET undone=1 WHERE id=?", (action_id,))


def save_template(guild_id: int, name: str, payload: dict, created_by: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as con:
        con.execute(
            "INSERT INTO templates(guild_id,name,payload,created_by,created_at) VALUES(?,?,?,?,?) ON CONFLICT(guild_id,name) DO UPDATE SET payload=excluded.payload,created_by=excluded.created_by,created_at=excluded.created_at",
            (guild_id, name, json.dumps(payload, ensure_ascii=False), created_by, now),
        )


def get_template(guild_id: int, name: str):
    with _connect() as con:
        row = con.execute("SELECT payload FROM templates WHERE guild_id=? AND name=?", (guild_id, name)).fetchone()
        return json.loads(row["payload"]) if row else None


def list_templates(guild_id: int) -> list[str]:
    with _connect() as con:
        return [r["name"] for r in con.execute("SELECT name FROM templates WHERE guild_id=? ORDER BY name", (guild_id,))]


def delete_template(guild_id: int, name: str) -> bool:
    with _connect() as con:
        cur = con.execute("DELETE FROM templates WHERE guild_id=? AND name=?", (guild_id, name))
        return cur.rowcount > 0


def add_absence(guild_id: int, user_id: int, reason: str, until_at: str | None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as con:
        con.execute("UPDATE absences SET active=0 WHERE guild_id=? AND user_id=? AND active=1", (guild_id, user_id))
        con.execute(
            "INSERT INTO absences(guild_id,user_id,reason,until_at,created_at) VALUES(?,?,?,?,?)",
            (guild_id, user_id, reason, until_at, now),
        )


def end_absence(guild_id: int, user_id: int) -> bool:
    with _connect() as con:
        cur = con.execute("UPDATE absences SET active=0 WHERE guild_id=? AND user_id=? AND active=1", (guild_id, user_id))
        return cur.rowcount > 0


def active_absences(guild_id: int):
    with _connect() as con:
        return con.execute("SELECT * FROM absences WHERE guild_id=? AND active=1 ORDER BY created_at DESC", (guild_id,)).fetchall()


def save_temp_voice(channel_id: int, guild_id: int, owner_id: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as con:
        con.execute("INSERT OR REPLACE INTO temp_voice(channel_id,guild_id,owner_id,created_at) VALUES(?,?,?,?)", (channel_id,guild_id,owner_id,now))


def get_temp_voice(channel_id: int):
    with _connect() as con:
        return con.execute("SELECT * FROM temp_voice WHERE channel_id=?", (channel_id,)).fetchone()


def delete_temp_voice(channel_id: int) -> None:
    with _connect() as con:
        con.execute("DELETE FROM temp_voice WHERE channel_id=?", (channel_id,))


def save_changelog(guild_id: int, title: str, body: str, author_id: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as con:
        con.execute("INSERT INTO changelog(guild_id,title,body,author_id,created_at) VALUES(?,?,?,?,?)", (guild_id,title,body,author_id,now))
