from src.database.connection import get_connection


async def init_db():
    conn = await get_connection()
    try:
        # ── Migration: add columns that may be missing in existing DBs ──
        for migration in [
            "ALTER TABLE profiles ADD COLUMN registration_complete INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE profiles ADD COLUMN role TEXT DEFAULT 'agent'",
            "ALTER TABLE profiles ADD COLUMN company TEXT",
            "ALTER TABLE profiles ADD COLUMN timezone TEXT DEFAULT 'America/New_York'",
        ]:
            try:
                await conn.execute(migration)
            except Exception:
                pass  # column already exists

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

            CREATE TABLE IF NOT EXISTS profiles (
                firebase_uid          TEXT PRIMARY KEY,
                email                 TEXT NOT NULL,
                username              TEXT UNIQUE,
                display_name          TEXT,
                avatar_url            TEXT,
                phone                 TEXT,
                role                  TEXT DEFAULT 'agent',
                company               TEXT,
                timezone              TEXT DEFAULT 'America/New_York',
                registration_complete INTEGER NOT NULL DEFAULT 0,
                created_at            TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at            TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        await conn.commit()
    finally:
        await conn.close()
