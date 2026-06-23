import hashlib
import secrets

from loguru import logger

from src.models import Bot


SEED_BOTS_DATA = [
    {"id": "mary-01", "name": "Mary-01", "campaign_id": "Medicare 2026"},
    {"id": "mary-02", "name": "Mary-02", "campaign_id": "Callback 55+"},
    {"id": "mary-03", "name": "Mary-03", "campaign_id": "Outreach Q3"},
    {"id": "mary-04", "name": "Mary-04", "campaign_id": None},
]


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    return salt + ":" + hashlib.sha256((salt + password).encode()).hexdigest()


async def seed_bots(db):
    existing = await db.get_all_bots()
    existing_ids = {b.id for b in existing}
    for data in SEED_BOTS_DATA:
        if data["id"] not in existing_ids:
            bot = Bot(
                id=data["id"],
                name=data["name"],
                status="offline",
                campaign_id=data["campaign_id"],
            )
            await db.upsert_bot(bot)
            logger.info(f"Seeded bot: {data['id']}")


async def seed_default_user(db):
    user = await db.get_user_by_username("admin")
    if not user:
        pw_hash = _hash_password("admin123")
        await db.create_user("admin", pw_hash)
        logger.info("Seeded default user: admin / admin123")
