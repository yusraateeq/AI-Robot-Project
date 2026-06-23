from pathlib import Path

import aiosqlite

from src.config.settings import settings


def _resolve_db_path() -> str:
    url = settings.database_url
    if url.startswith("sqlite+aiosqlite:///"):
        return url[len("sqlite+aiosqlite:///"):]
    return "redstone_crm.db"


DB_PATH = _resolve_db_path()


async def get_connection() -> aiosqlite.Connection:
    db_dir = Path(DB_PATH).parent
    if db_dir != Path("."):
        db_dir.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")
    return conn
