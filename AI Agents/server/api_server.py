import hashlib
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from automation_agent.main import automation_agent
from brain_agent.main import brain_agent
from common.config import settings
from common.models import Bot
from logger_agent.main import logger_agent
from server.socket_server import socket_server

# ─── Password helpers ─────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    return salt + ":" + hashlib.sha256((salt + password).encode()).hexdigest()

def verify_password(password: str, pw_hash: str) -> bool:
    salt, stored = pw_hash.split(":")
    return stored == hashlib.sha256((salt + password).encode()).hexdigest()

def create_jwt(user_id: int, username: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


app = FastAPI(title="Redstone CRM — AI Agents API", version="1.0.0")

# ─── CORS ─────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Schemas ──────────────────────────────────────────────────────

@dataclass
class BotActionRequest:
    bot_id: str


@dataclass
class CallLogCreate:
    bot_id: str
    phone_number: str
    lead_id: Optional[str] = None


@dataclass
class SettingUpdate:
    key: str
    value: str

@dataclass
class BotAddRequest:
    name: str
    campaign: str = ""


# ─── Lifecycle ────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    await logger_agent.start()
    await brain_agent.start()
    await automation_agent.start()

    brain_agent.load_script()
    automation_agent.register_live_callback(on_live_call)
    await seed_default_user()
    await seed_bots()


async def on_live_call(bot_id: str):
    call_id = f"call_{bot_id}_{int(time.time())}"
    logger.info(f"[{call_id}] |+|+|+ LIVE CALL DETECTED for {bot_id} +|+|+|+")

    # Initialize conversation session for the brain agent
    _, _ = await brain_agent.start_call_with_greeting(call_id)

    await socket_server.emit_call_update({
        "bot_id": bot_id,
        "call_id": call_id,
        "event": "call_started",
        "stage": "greeting_playing",
    })


@app.on_event("shutdown")
async def shutdown():
    await automation_agent.stop()
    await brain_agent.stop()
    await logger_agent.stop()


# ─── Agent Control ────────────────────────────────────────────────

@app.post("/agents/automation/login")
async def agent_login(req: BotActionRequest):
    success = await automation_agent.login_bot(req.bot_id)
    if not success:
        raise HTTPException(500, "VICIdial login failed")
    return {"status": "ok", "bot_id": req.bot_id}


@app.post("/agents/automation/logout")
async def agent_logout(req: BotActionRequest):
    await automation_agent.logout_bot(req.bot_id)
    return {"status": "ok", "bot_id": req.bot_id}


@app.post("/agents/automation/restart")
async def agent_restart(req: BotActionRequest):
    success = await automation_agent.restart_bot(req.bot_id)
    return {"status": "ok" if success else "failed", "bot_id": req.bot_id}


@app.post("/agents/automation/pause")
async def agent_pause(req: BotActionRequest):
    await automation_agent.pause_bot(req.bot_id)
    return {"status": "ok", "bot_id": req.bot_id}


@app.post("/agents/automation/resume")
async def agent_resume(req: BotActionRequest):
    await automation_agent.resume_bot(req.bot_id)
    return {"status": "ok", "bot_id": req.bot_id}


# ─── Status ────────────────────────────────────────────────────────

@app.get("/status")
async def status():
    return {
        "automation_agent": automation_agent.is_running,
        "brain_agent": brain_agent.is_running,
        "logger_agent": logger_agent.is_running,
    }


@app.get("/status/bot/{bot_id}")
async def bot_status(bot_id: str):
    status = await automation_agent.get_bot_status(bot_id)
    return {"bot_id": bot_id, "vicidial_status": status}


# ─── Call Logs ────────────────────────────────────────────────────

@app.get("/logs")
async def get_logs(limit: int = 50, offset: int = 0):
    logs = await logger_agent.logger.get_recent_calls(limit)
    return {"logs": logs, "count": len(logs)}


@app.post("/logs")
async def create_log(req: CallLogCreate):
    call_id = await logger_agent.logger.start_call(
        bot_id=req.bot_id,
        phone_number=req.phone_number,
        lead_id=req.lead_id,
    )
    return {"call_id": call_id, "status": "in_progress"}


# ─── Settings ─────────────────────────────────────────────────────

@app.get("/settings/{key}")
async def get_setting(key: str):
    value = await logger_agent.db.get_setting(key)
    return {"key": key, "value": value}


@app.put("/settings")
async def update_setting(req: SettingUpdate):
    await logger_agent.db.set_setting(req.key, req.value)
    return {"status": "ok", "key": req.key}


# ─── Dashboard API (frontend-facing) ───────────────────────────

@app.get("/api/stats")
async def api_stats():
    db_bots = await logger_agent.db.get_all_bots()
    total_calls = await logger_agent.db.get_total_calls()
    transfers = await logger_agent.db.get_transferred_calls()
    success_rate = round((transfers / total_calls * 100) if total_calls > 0 else 0, 1)
    active_bots = 0
    for db_bot in db_bots:
        if db_bot.id in automation_agent._monitor_tasks:
            vic_status = await automation_agent.get_bot_status(db_bot.id)
            if vic_status and "READY" in vic_status.upper():
                active_bots += 1

    hourly_volume = await logger_agent.db.get_hourly_call_volume()

    labels = [f"{int(h['hour']):02d}:00" for h in hourly_volume]
    data = [h["calls"] for h in hourly_volume]
    if not labels:
        labels = ["9am", "11am", "1pm", "3pm", "5pm"]
        data = [0, 0, 0, 0, 0]

    return {
        "total_calls": total_calls,
        "transfers": transfers,
        "success_rate": success_rate,
        "active_bots": active_bots,
        "call_volume": {"labels": labels, "data": data},
    }

@app.get("/api/bots")
async def api_bots():
    db_bots = await logger_agent.db.get_all_bots()
    active_ids = set(automation_agent.active_bot_ids)
    result = []
    for bot in db_bots:
        vic_status = None
        if bot.id in active_ids:
            vic_status = await automation_agent.get_bot_status(bot.id)
        is_active = vic_status is not None and "READY" in vic_status.upper()
        calls_today = await logger_agent.db.get_bot_calls_today(bot.id)
        result.append({
            "id": bot.id,
            "name": bot.name,
            "campaign": bot.campaign_id or "—",
            "vicidial_status": vic_status,
            "active": is_active,
            "status": "active" if is_active else "offline",
            "callsToday": calls_today,
        })
    return {"bots": result}


# ─── Bot API (frontend-facing) ──────────────────────────────────

@app.post("/api/bots/{bot_id}/login")
async def api_bot_login(bot_id: str):
    await automation_agent.start_login_bot(bot_id)
    return {"status": "pending", "bot_id": bot_id}

@app.get("/api/bots/{bot_id}/login-status")
async def api_bot_login_status(bot_id: str):
    return {"bot_id": bot_id, **automation_agent.get_login_status(bot_id)}

@app.post("/api/bots/{bot_id}/logout")
async def api_bot_logout(bot_id: str):
    await automation_agent.logout_bot(bot_id)
    return {"status": "ok", "bot_id": bot_id}

@app.post("/api/bots/{bot_id}/restart")
async def api_bot_restart(bot_id: str):
    success = await automation_agent.restart_bot(bot_id)
    return {"status": "ok" if success else "failed", "bot_id": bot_id}

@app.get("/api/bots/{bot_id}/status")
async def api_bot_status(bot_id: str):
    vicidial_status = await automation_agent.get_bot_status(bot_id)
    return {"bot_id": bot_id, "vicidial_status": vicidial_status}

@app.post("/api/bots/add")
async def api_bot_add(req: BotAddRequest):
    if not req.name.strip():
        raise HTTPException(400, "Bot name is required")
    bot_id = req.name.lower().replace(" ", "-").replace("_", "-")
    existing = await logger_agent.db.get_all_bots()
    if any(b.id == bot_id for b in existing):
        raise HTTPException(409, f"Bot '{bot_id}' already exists")

    bot = Bot(
        id=bot_id,
        name=req.name.strip(),
        status="offline",
        campaign_id=req.campaign.strip() or None,
    )
    config = {
        "sip_extension": f"10{len(existing) + 1:03d}",
        "sip_password": secrets.token_hex(8),
        "proxy_server": "localhost:5060",
        "script_path": "resources/script.txt",
    }
    await logger_agent.db.create_bot(bot, config)
    logger.info(f"Bot created: {bot_id} (sip={config['sip_extension']})")
    return {
        "bot": {
            "id": bot.id,
            "name": bot.name,
            "campaign": bot.campaign_id or "—",
            "status": "offline",
            "active": False,
        },
        "config": config,
    }

@app.delete("/api/bots/{bot_id}")
async def api_bot_delete(bot_id: str):
    # Debug: check if bot exists first
    all_bots = await logger_agent.db.get_all_bots()
    all_ids = [b.id for b in all_bots]
    logger.info(f"DELETE /api/bots/{bot_id} — existing bots: {all_ids}")
    if bot_id not in all_ids:
        raise HTTPException(404, f"Bot '{bot_id}' not found in DB (available: {all_ids})")
    deleted = await logger_agent.db.delete_bot(bot_id)
    if not deleted:
        raise HTTPException(500, f"Bot '{bot_id}' found but delete returned 0 rows")
    if bot_id in automation_agent._monitor_tasks:
        await automation_agent.logout_bot(bot_id)
    logger.info(f"Bot deleted: {bot_id}")
    return {"status": "ok", "bot_id": bot_id}


# ─── Auth ─────────────────────────────────────────────────────────

@dataclass
class LoginRequest:
    username: str
    password: str

@dataclass
class RegisterRequest:
    username: str
    password: str

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    user = await logger_agent.db.get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid username or password")
    token = create_jwt(user["id"], user["username"])
    return {
        "token": token,
        "user": {"id": user["id"], "username": user["username"]},
    }

@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    existing = await logger_agent.db.get_user_by_username(req.username)
    if existing:
        raise HTTPException(409, "Username already taken")
    pw_hash = hash_password(req.password)
    user_id = await logger_agent.db.create_user(req.username, pw_hash)
    token = create_jwt(user_id, req.username)
    return {
        "token": token,
        "user": {"id": user_id, "username": req.username},
    }


# ─── Seed bots ──────────────────────────────────────────────────

SEED_BOTS_DATA = [
    {"id": "mary-01", "name": "Mary-01", "campaign_id": "Medicare 2026"},
    {"id": "mary-02", "name": "Mary-02", "campaign_id": "Callback 55+"},
    {"id": "mary-03", "name": "Mary-03", "campaign_id": "Outreach Q3"},
    {"id": "mary-04", "name": "Mary-04", "campaign_id": None},
]

async def seed_bots():
    existing = await logger_agent.db.get_all_bots()
    existing_ids = {b.id for b in existing}
    for data in SEED_BOTS_DATA:
        if data["id"] not in existing_ids:
            bot = Bot(
                id=data["id"],
                name=data["name"],
                status="offline",
                campaign_id=data["campaign_id"],
            )
            await logger_agent.db.upsert_bot(bot)
            logger.info(f"Seeded bot: {data['id']}")


# ─── Seed default user ───────────────────────────────────────────

async def seed_default_user():
    user = await logger_agent.db.get_user_by_username("admin")
    if not user:
        pw_hash = hash_password("admin123")
        await logger_agent.db.create_user("admin", pw_hash)
        logger.info("Seeded default user: admin / admin123")
