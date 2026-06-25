import asyncio
import secrets
import time
from dataclasses import dataclass
from typing import Optional

from fastapi import APIRouter, HTTPException, Header
from loguru import logger

from src.agents.automation import automation_agent
from src.agents.brain import brain_agent
from src.agents.logger import logger_agent
from src.api.auth import hash_password, verify_password, create_jwt, decode_jwt
from src.api.socketio import socket_server
from src.config.firebase import verify_firebase_token
from src.models import Bot
from src.seed import seed_bots, seed_default_user

router = APIRouter()


@dataclass
class BotActionRequest:
    bot_id: str


@dataclass
class CallLogCreate:
    bot_id: str
    phone_number: str
    lead_id: Optional[str] = None


@dataclass
class BotAddRequest:
    name: str
    campaign: str = ""


@dataclass
class SettingUpdate:
    key: str
    value: str


@dataclass
class LoginRequest:
    username: str
    password: str


@dataclass
class RegisterRequest:
    username: str
    password: str


@dataclass
class FirebaseAuthRequest:
    id_token: str


@dataclass
class ProfileUpdateRequest:
    display_name: str | None = None
    username: str | None = None
    avatar_url: str | None = None
    phone: str | None = None
    role: str | None = None
    company: str | None = None
    timezone: str | None = None


@dataclass
class CompleteRegistrationRequest:
    display_name: str
    username: str
    phone: str
    role: str = "agent"
    company: str = ""
    timezone: str = "America/New_York"


# ── Lifecycle callbacks ──────────────────────────────────────────

async def on_live_call(bot_id: str):
    call_id = f"call_{bot_id}_{int(time.time())}"
    logger.info(f"[{call_id}] |+|+|+ LIVE CALL DETECTED for {bot_id} +|+|+|+")
    _, _ = await brain_agent.start_call_with_greeting(call_id)
    await socket_server.emit_call_update({
        "bot_id": bot_id,
        "call_id": call_id,
        "event": "call_started",
        "stage": "greeting_playing",
    })


async def startup_handler():
    await seed_default_user(logger_agent.db)
    await seed_bots(logger_agent.db)


# ── Agent Control ────────────────────────────────────────────────

@router.post("/agents/automation/login")
async def agent_login(req: BotActionRequest):
    success = await automation_agent.login_bot(req.bot_id)
    if not success:
        raise HTTPException(500, "VICIdial login failed")
    return {"status": "ok", "bot_id": req.bot_id}


@router.post("/agents/automation/logout")
async def agent_logout(req: BotActionRequest):
    await automation_agent.logout_bot(req.bot_id)
    return {"status": "ok", "bot_id": req.bot_id}


@router.post("/agents/automation/restart")
async def agent_restart(req: BotActionRequest):
    success = await automation_agent.restart_bot(req.bot_id)
    return {"status": "ok" if success else "failed", "bot_id": req.bot_id}


@router.post("/agents/automation/pause")
async def agent_pause(req: BotActionRequest):
    await automation_agent.pause_bot(req.bot_id)
    return {"status": "ok", "bot_id": req.bot_id}


@router.post("/agents/automation/resume")
async def agent_resume(req: BotActionRequest):
    await automation_agent.resume_bot(req.bot_id)
    return {"status": "ok", "bot_id": req.bot_id}


# ─── Status ────────────────────────────────────────────────────────

@router.get("/status")
async def status():
    return {
        "automation_agent": automation_agent.is_running,
        "brain_agent": brain_agent.is_running,
        "logger_agent": logger_agent.is_running,
    }


@router.get("/status/bot/{bot_id}")
async def bot_status(bot_id: str):
    status = await automation_agent.get_bot_status(bot_id)
    return {"bot_id": bot_id, "vicidial_status": status}


# ─── Call Logs ────────────────────────────────────────────────────

@router.get("/logs")
async def get_logs(limit: int = 50, offset: int = 0):
    logs = await logger_agent.logger.get_recent_calls(limit)
    return {"logs": logs, "count": len(logs)}


@router.post("/logs")
async def create_log(req: CallLogCreate):
    call_id = await logger_agent.logger.start_call(
        bot_id=req.bot_id,
        phone_number=req.phone_number,
        lead_id=req.lead_id,
    )
    return {"call_id": call_id, "status": "in_progress"}


# ─── Settings ─────────────────────────────────────────────────────

@router.get("/settings/{key}")
async def get_setting(key: str):
    value = await logger_agent.db.get_setting(key)
    return {"key": key, "value": value}


@router.put("/settings")
async def update_setting(req: SettingUpdate):
    await logger_agent.db.set_setting(req.key, req.value)
    return {"status": "ok", "key": req.key}


# ─── Dashboard API ─────────────────────────────────────────────

@router.get("/api/stats")
async def api_stats():
    db = logger_agent.db
    bots = await db.get_all_bots()
    total_calls = await db.get_total_calls()
    transfers = await db.get_transferred_calls()
    success_rate = round((transfers / total_calls * 100) if total_calls > 0 else 0, 1)
    active_bots = sum(
        1 for bot in bots
        if automation_agent.bot_statuses.get(bot.id) in ("active", "online")
    )

    hourly_volume = await db.get_hourly_call_volume()

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


@router.get("/api/bots")
async def api_bots():
    db = logger_agent.db
    bots = await db.get_all_bots()
    active_ids = set(automation_agent.active_bot_ids)
    result = []
    for bot in bots:
        vic_status = None
        if bot.id in active_ids:
            vic_status = await automation_agent.get_bot_status(bot.id)
        is_active = vic_status is not None and "READY" in vic_status.upper()
        overall_status = automation_agent.bot_statuses.get(bot.id, "offline")
        calls_today = await db.get_bot_calls_today(bot.id)
        result.append({
            "id": bot.id,
            "name": bot.name,
            "campaign": bot.campaign_id or "—",
            "vicidial_status": vic_status,
            "active": is_active,
            "status": overall_status,
            "callsToday": calls_today,
        })
    return {"bots": result}


# ─── Bot API ──────────────────────────────────────────────────

@router.post("/api/bots/{bot_id}/login")
async def api_bot_login(bot_id: str):
    await automation_agent.start_login_bot(bot_id)
    return {"status": "pending", "bot_id": bot_id}


@router.get("/api/bots/{bot_id}/login-status")
async def api_bot_login_status(bot_id: str):
    return {"bot_id": bot_id, **automation_agent.get_login_status(bot_id)}


@router.post("/api/bots/{bot_id}/logout")
async def api_bot_logout(bot_id: str):
    await automation_agent.logout_bot(bot_id)
    return {"status": "ok", "bot_id": bot_id}


@router.post("/api/bots/{bot_id}/restart")
async def api_bot_restart(bot_id: str):
    success = await automation_agent.restart_bot(bot_id)
    return {"status": "ok" if success else "failed", "bot_id": bot_id}


@router.get("/api/bots/{bot_id}/status")
async def api_bot_status(bot_id: str):
    vicidial_status = await automation_agent.get_bot_status(bot_id)
    overall = automation_agent.bot_statuses.get(bot_id, "offline")
    return {"bot_id": bot_id, "vicidial_status": vicidial_status, "status": overall}


@router.post("/api/login")
async def api_login(req: BotActionRequest):
    try:
        asyncio.create_task(automation_agent.start_login_bot(req.bot_id))
        return {"status": "online", "bot_id": req.bot_id}
    except Exception as e:
        raise HTTPException(500, f"Login failed: {e}")


@router.post("/api/bots/add")
async def api_bot_add(req: BotAddRequest):
    if not req.name.strip():
        raise HTTPException(400, "Bot name is required")
    bot_id = req.name.lower().replace(" ", "-").replace("_", "-")
    db = logger_agent.db
    existing = await db.get_all_bots()
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
    await db.create_bot(bot, config)
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


@router.delete("/api/bots/{bot_id}")
async def api_bot_delete(bot_id: str):
    db = logger_agent.db
    all_bots = await db.get_all_bots()
    all_ids = [b.id for b in all_bots]
    logger.info(f"DELETE /bots/{bot_id} — existing bots: {all_ids}")
    if bot_id not in all_ids:
        raise HTTPException(404, f"Bot '{bot_id}' not found in DB (available: {all_ids})")
    deleted = await db.delete_bot(bot_id)
    if not deleted:
        raise HTTPException(500, f"Bot '{bot_id}' found but delete returned 0 rows")
    if bot_id in automation_agent._monitor_tasks:
        await automation_agent.logout_bot(bot_id)
    logger.info(f"Bot deleted: {bot_id}")
    return {"status": "ok", "bot_id": bot_id}


# ─── Bot activation / deactivation ───────────────────────────────


@router.post("/api/activate-bot")
async def api_activate_bot(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1]
    try:
        decoded = await verify_firebase_token(token)
    except ValueError as e:
        raise HTTPException(401, str(e))

    if not automation_agent._running:
        await automation_agent.start()

    bots = await logger_agent.db.get_all_bots()
    for bot in bots:
        if bot.id not in automation_agent._monitor_tasks:
            await automation_agent.start_login_bot(bot.id)

    logger.info(f"Bot activation triggered by firebase_uid={decoded.get('uid', 'unknown')}")
    return {"status": "online", "automation_agent": True}


@router.post("/api/stop-bot")
async def api_stop_bot(authorization: str | None = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            await verify_firebase_token(token)
        except ValueError:
            pass  # allow unauthenticated stop as well

    for bot_id in list(automation_agent._monitor_tasks.keys()):
        await automation_agent.logout_bot(bot_id)

    await automation_agent.stop()
    logger.info("All bots stopped via /api/stop-bot")
    return {"status": "offline", "automation_agent": False}


@router.post("/api/restart-bot")
async def api_restart_bot(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1]
    try:
        await verify_firebase_token(token)
    except ValueError as e:
        raise HTTPException(401, str(e))

    bots = await logger_agent.db.get_all_bots()
    for bot in bots:
        if bot.id in automation_agent._monitor_tasks:
            await automation_agent.restart_bot(bot.id)
        else:
            await automation_agent.start_login_bot(bot.id)

    logger.info("Bot restart triggered")
    return {"status": "online", "automation_agent": True}


# ─── Firebase Auth ───────────────────────────────────────────────

@router.post("/api/auth/firebase")
async def firebase_auth(req: FirebaseAuthRequest):
    try:
        decoded = await verify_firebase_token(req.id_token)
    except ValueError as e:
        raise HTTPException(401, str(e))

    print("[firebase_auth] Decoded token payload:", decoded)

    firebase_uid = None
    for key in ("uid", "user_id", "sub"):
        if key in decoded:
            firebase_uid = decoded[key]
            break

    if not firebase_uid:
        raise HTTPException(
            401,
            "Invalid Firebase token structure: none of ['uid', 'user_id', 'sub'] found in decoded payload",
        )

    logger.info(f"[firebase_auth] Extracted user ID '{firebase_uid}' from key '{key}'")

    email = decoded.get("email", "")
    name = decoded.get("name", "")
    picture = decoded.get("picture", "")

    db = logger_agent.db
    profile = await db.get_profile(firebase_uid)

    if not profile:
        username = email.split("@")[0] if email else firebase_uid[:8]
        try:
            profile = await db.create_profile(
                firebase_uid=firebase_uid,
                email=email,
                username=username,
                display_name=name or None,
                avatar_url=picture or None,
            )
        except Exception as e:
            raise HTTPException(500, f"Failed to create profile: {e}")

    token = create_jwt(0, profile["username"], firebase_uid=profile["firebase_uid"])
    return {
        "token": token,
        "registration_complete": bool(profile.get("registration_complete", 0)),
        "profile": {
            "firebase_uid": profile["firebase_uid"],
            "email": profile["email"],
            "username": profile["username"],
            "display_name": profile.get("display_name"),
            "avatar_url": profile.get("avatar_url"),
            "phone": profile.get("phone"),
            "role": profile.get("role", "agent"),
            "company": profile.get("company"),
            "timezone": profile.get("timezone", "America/New_York"),
            "registration_complete": bool(profile.get("registration_complete", 0)),
        },
    }


# ─── Profile ──────────────────────────────────────────────────────

def _get_firebase_uid(auth_header: str | None) -> str:
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")
    payload = decode_jwt(auth_header.split(" ", 1)[1])
    if not payload or "firebase_uid" not in payload:
        raise HTTPException(401, "Invalid token or missing firebase_uid")
    return payload["firebase_uid"]


@router.get("/api/profile")
async def get_profile(authorization: str | None = Header(None)):
    firebase_uid = _get_firebase_uid(authorization)
    profile = await logger_agent.db.get_profile(firebase_uid)
    if not profile:
        raise HTTPException(404, "Profile not found")
    return {
        **profile,
        "registration_complete": bool(profile.get("registration_complete", 0)),
    }


@router.put("/api/profile")
async def update_profile(req: ProfileUpdateRequest, authorization: str | None = Header(None)):
    firebase_uid = _get_firebase_uid(authorization)
    updated = await logger_agent.db.update_profile(
        firebase_uid,
        display_name=req.display_name,
        username=req.username,
        avatar_url=req.avatar_url,
        phone=req.phone,
        role=req.role,
        company=req.company,
        timezone=req.timezone,
    )
    if not updated:
        raise HTTPException(404, "Profile not found")
    return updated


@router.post("/api/auth/complete-registration")
async def complete_registration(req: CompleteRegistrationRequest, authorization: str | None = Header(None)):
    firebase_uid = _get_firebase_uid(authorization)

    errors = []
    if not req.display_name or not req.display_name.strip():
        errors.append("Display name is required")
    if not req.username or not req.username.strip():
        errors.append("Username is required")
    if not req.phone or not req.phone.strip():
        errors.append("Phone number is required")
    if errors:
        raise HTTPException(400, {"errors": errors})

    db = logger_agent.db
    profile = await db.get_profile(firebase_uid)
    if not profile:
        raise HTTPException(404, "Profile not found")
    if profile.get("registration_complete"):
        return {"status": "already_complete", "profile": profile}

    await db.update_profile(
        firebase_uid,
        display_name=req.display_name.strip(),
        username=req.username.strip(),
        phone=req.phone.strip(),
        role=req.role,
        company=req.company.strip() if req.company else "",
        timezone=req.timezone,
        registration_complete=1,
    )
    updated = await db.get_profile(firebase_uid)
    return {"status": "ok", "profile": updated}


# ─── Auth ─────────────────────────────────────────────────────────

@router.post("/api/auth/login")
async def login(req: LoginRequest):
    db = logger_agent.db
    user = await db.get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid username or password")
    token = create_jwt(user["id"], user["username"])
    return {
        "token": token,
        "user": {"id": user["id"], "username": user["username"]},
    }


@router.post("/api/auth/register")
async def register(req: RegisterRequest):
    db = logger_agent.db
    existing = await db.get_user_by_username(req.username)
    if existing:
        raise HTTPException(409, "Username already taken")
    pw_hash = hash_password(req.password)
    user_id = await db.create_user(req.username, pw_hash)
    token = create_jwt(user_id, req.username)
    return {
        "token": token,
        "user": {"id": user_id, "username": req.username},
    }
