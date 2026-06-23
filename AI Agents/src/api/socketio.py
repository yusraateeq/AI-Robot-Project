import asyncio
from loguru import logger
import socketio

from src.config.settings import settings


class AgentSocketServer:

    def __init__(self):
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins=["http://localhost:3000"],
        )
        self.app = socketio.ASGIApp(self.sio)
        self._server: asyncio.Server | None = None

    async def start(self):
        self._register_handlers()
        logger.info(f"Socket.IO server ready on port {settings.socket_port}")

    async def run(self):
        import uvicorn
        config = uvicorn.Config(
            self.app,
            host=settings.api_host,
            port=settings.socket_port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        await server.serve()

    def _register_handlers(self):
        @self.sio.event
        async def connect(sid, environ):
            logger.debug(f"Dashboard client connected: {sid}")

        @self.sio.event
        async def disconnect(sid):
            logger.debug(f"Dashboard client disconnected: {sid}")

    async def emit_dashboard_update(self, data: dict):
        await self.sio.emit("update-dashboard", data)

    async def emit_call_update(self, data: dict):
        await self.sio.emit("call-update", data)

    async def emit_agent_status(self, data: dict):
        await self.sio.emit("agent-status", data)


socket_server = AgentSocketServer()
