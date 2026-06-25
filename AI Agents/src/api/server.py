from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.agents.automation import automation_agent
from src.agents.brain import brain_agent
from src.api.routes import router, startup_handler, on_live_call
from src.api.socketio import socket_server


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.agents.logger import logger_agent

    await logger_agent.start()
    await brain_agent.start()
    await automation_agent.start()

    brain_agent.load_script()
    automation_agent.register_live_callback(on_live_call)
    await startup_handler()

    logger.info("Redstone AI Agents — fully operational")
    yield

    await automation_agent.stop()
    await brain_agent.stop()
    await logger_agent.stop()
    logger.info("Redstone AI Agents — shut down")


app = FastAPI(
    title="Redstone CRM — AI Agents API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="")
