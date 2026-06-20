import sqlite3
from pathlib import Path

import aiosqlite

from common.config import settings


def _db_path() -> str:
    url = settings.database_url
    if url.startswith("sqlite+aiosqlite:///"):
        return url[len("sqlite+aiosqlite:///"):]
    return "redstone_crm.db"


DB_PATH = _db_path()


async def get_connection() -> aiosqlite.Connection:
    db_dir = Path(DB_PATH).parent
    if db_dir != Path("."):
        db_dir.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")
    return conn


async def init_db():
    conn = await get_connection()
    try:
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS bots (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'idle',
                campaign_id TEXT,
                extension   TEXT,
                active      INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS call_logs (
                id              TEXT PRIMARY KEY,
                bot_id          TEXT NOT NULL REFERENCES bots(id),
                phone_number    TEXT NOT NULL,
                lead_id         TEXT,
                status          TEXT NOT NULL DEFAULT 'pending',
                duration        REAL,
                recording_url   TEXT,
                transcript      TEXT,
                summary         TEXT,
                disposition     TEXT,
                started_at      TEXT,
                ended_at        TEXT,
                created_at      TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS settings (
                key         TEXT PRIMARY KEY,
                value       TEXT NOT NULL,
                updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS bot_config (
                bot_id          TEXT PRIMARY KEY REFERENCES bots(id) ON DELETE CASCADE,
                sip_extension   TEXT,
                sip_password    TEXT,
                proxy_server    TEXT DEFAULT 'localhost:5060',
                script_path     TEXT DEFAULT 'resources/script.txt',
                created_at      TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        await conn.commit()
    finally:
        await conn.close()
