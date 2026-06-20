from datetime import datetime
from typing import Optional

from common.database import get_connection, init_db
from common.models import Bot, CallLog, Setting


class DatabaseManager:

    async def initialize(self):
        await init_db()

    # ── Bots ──────────────────────────────────────────────────────

    async def get_all_bots(self) -> list[Bot]:
        conn = await get_connection()
        try:
            cursor = await conn.execute("SELECT * FROM bots ORDER BY name")
            rows = await cursor.fetchall()
            return [Bot(**dict(row)) for row in rows]
        finally:
            await conn.close()

    async def upsert_bot(self, bot: Bot):
        conn = await get_connection()
        try:
            await conn.execute("""
                INSERT INTO bots (id, name, status, campaign_id, extension, active)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    status = excluded.status,
                    campaign_id = excluded.campaign_id,
                    updated_at = datetime('now')
            """, (bot.id, bot.name, bot.status, bot.campaign_id, bot.extension, 1))
            await conn.commit()
        finally:
            await conn.close()

    async def create_bot(self, bot: Bot, config: Optional[dict] = None) -> Bot:
        conn = await get_connection()
        try:
            await conn.execute("""
                INSERT INTO bots (id, name, status, campaign_id, extension, active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (bot.id, bot.name, "offline", bot.campaign_id, bot.extension))
            if config:
                await conn.execute("""
                    INSERT INTO bot_config (bot_id, sip_extension, sip_password, proxy_server, script_path)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    bot.id,
                    config.get("sip_extension"),
                    config.get("sip_password"),
                    config.get("proxy_server", "localhost:5060"),
                    config.get("script_path", "resources/script.txt"),
                ))
            await conn.commit()
            return bot
        finally:
            await conn.close()

    async def delete_bot(self, bot_id: str) -> bool:
        conn = await get_connection()
        try:
            await conn.execute("DELETE FROM call_logs WHERE bot_id = ?", (bot_id,))
            await conn.execute("DELETE FROM bot_config WHERE bot_id = ?", (bot_id,))
            cursor = await conn.execute("DELETE FROM bots WHERE id = ?", (bot_id,))
            await conn.commit()
            return cursor.rowcount > 0
        finally:
            await conn.close()

    async def get_bot_config(self, bot_id: str) -> Optional[dict]:
        conn = await get_connection()
        try:
            cursor = await conn.execute("SELECT * FROM bot_config WHERE bot_id = ?", (bot_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()

    async def update_bot_status(self, bot_id: str, status: str):
        conn = await get_connection()
        try:
            await conn.execute(
                "UPDATE bots SET status = ?, updated_at = datetime('now') WHERE id = ?",
                (status, bot_id),
            )
            await conn.commit()
        finally:
            await conn.close()

    # ── Call Logs ─────────────────────────────────────────────────

    async def create_call_log(self, log: CallLog) -> str:
        conn = await get_connection()
        try:
            await conn.execute(
                """INSERT INTO call_logs
                   (id, bot_id, phone_number, lead_id, status, started_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
                (log.id, log.bot_id, log.phone_number, log.lead_id, log.status, log.started_at),
            )
            await conn.commit()
            return log.id
        finally:
            await conn.close()

    async def get_call_logs(self, limit: int = 50, offset: int = 0) -> list[CallLog]:
        conn = await get_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM call_logs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            rows = await cursor.fetchall()
            return [CallLog(**dict(row)) for row in rows]
        finally:
            await conn.close()

    async def update_call_log(self, call_id: str, **kwargs):
        if not kwargs:
            return
        sets = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [call_id]
        conn = await get_connection()
        try:
            await conn.execute(
                f"UPDATE call_logs SET {sets} WHERE id = ?",
                values,
            )
            await conn.commit()
        finally:
            await conn.close()

    # ── Users (auth) ──────────────────────────────────────────────

    async def create_user(self, username: str, password_hash: str) -> int:
        conn = await get_connection()
        try:
            cursor = await conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash),
            )
            await conn.commit()
            return cursor.lastrowid
        finally:
            await conn.close()

    async def get_user_by_username(self, username: str) -> Optional[dict]:
        conn = await get_connection()
        try:
            cursor = await conn.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (username,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()

    # ── Stats ────────────────────────────────────────────────────

    async def get_bot_calls_today(self, bot_id: str) -> int:
        conn = await get_connection()
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as cnt FROM call_logs WHERE bot_id = ? AND date(started_at) = date('now')",
                (bot_id,),
            )
            row = await cursor.fetchone()
            return row["cnt"]
        finally:
            await conn.close()

    async def get_total_calls(self) -> int:
        conn = await get_connection()
        try:
            cursor = await conn.execute("SELECT COUNT(*) as cnt FROM call_logs")
            row = await cursor.fetchone()
            return row["cnt"]
        finally:
            await conn.close()

    async def get_transferred_calls(self) -> int:
        conn = await get_connection()
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as cnt FROM call_logs WHERE disposition = 'transferred'"
            )
            row = await cursor.fetchone()
            return row["cnt"]
        finally:
            await conn.close()

    async def get_hourly_call_volume(self) -> list[dict]:
        conn = await get_connection()
        try:
            cursor = await conn.execute("""
                SELECT strftime('%H', started_at) as hour,
                       COUNT(*) as calls
                FROM call_logs
                WHERE started_at IS NOT NULL
                GROUP BY hour
                ORDER BY hour
            """)
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            await conn.close()

    # ── Settings ──────────────────────────────────────────────────

    async def get_setting(self, key: str) -> str | None:
        conn = await get_connection()
        try:
            cursor = await conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            )
            row = await cursor.fetchone()
            return row["value"] if row else None
        finally:
            await conn.close()

    async def set_setting(self, key: str, value: str):
        conn = await get_connection()
        try:
            await conn.execute(
                """INSERT INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))
                   ON CONFLICT(key) DO UPDATE SET value = excluded.value,
                                                  updated_at = datetime('now')""",
                (key, value),
            )
            await conn.commit()
        finally:
            await conn.close()
