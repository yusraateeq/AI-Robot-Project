import asyncio
from loguru import logger

from common.config import settings
from logger_agent.db_manager import DatabaseManager
from logger_agent.call_logger import CallLogger


class LoggerAgent:
    """
    Logger Agent — responsible for all database operations and call log management.
    Runs as a background service that provides DB access to other agents via shared
    DatabaseManager and CallLogger instances.
    """

    def __init__(self):
        self.db = DatabaseManager()
        self.logger = CallLogger(self.db)
        self._running = False

    async def start(self):
        logger.info("Logger Agent initializing database...")
        await self.db.initialize()
        self._running = True
        logger.info("Logger Agent started — database ready")

    async def stop(self):
        self._running = False
        logger.info("Logger Agent stopped")

    @property
    def is_running(self) -> bool:
        return self._running


# Singleton for shared access across agents
logger_agent = LoggerAgent()
