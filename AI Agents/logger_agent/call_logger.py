import uuid
from datetime import datetime

from common.models import CallLog
from logger_agent.db_manager import DatabaseManager


class CallLogger:
    def __init__(self, db: DatabaseManager):
        self.db = db

    async def start_call(
        self,
        bot_id: str,
        phone_number: str,
        lead_id: str | None = None,
    ) -> str:
        log = CallLog(
            id=str(uuid.uuid4()),
            bot_id=bot_id,
            phone_number=phone_number,
            lead_id=lead_id,
            status="in_progress",
            started_at=datetime.utcnow().isoformat(),
        )
        call_id = await self.db.create_call_log(log)
        return call_id

    async def end_call(
        self,
        call_id: str,
        status: str,
        duration: float | None = None,
        recording_url: str | None = None,
        disposition: str | None = None,
    ):
        await self.db.update_call_log(
            call_id,
            status=status,
            duration=duration,
            recording_url=recording_url,
            disposition=disposition,
            ended_at=datetime.utcnow().isoformat(),
        )

    async def attach_transcript(self, call_id: str, transcript: str):
        await self.db.update_call_log(call_id, transcript=transcript)

    async def attach_summary(self, call_id: str, summary: str):
        await self.db.update_call_log(call_id, summary=summary)

    async def get_recent_calls(self, limit: int = 50) -> list[CallLog]:
        return await self.db.get_call_logs(limit=limit)
