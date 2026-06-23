import asyncio
from dataclasses import dataclass, field

from loguru import logger


@dataclass
class ActiveCall:
    call_id: str
    bot_id: str
    phone_number: str
    stream_sid: str | None = None
    audio_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    _done: bool = False


class VoiceManager:
    def __init__(self):
        self._calls: dict[str, ActiveCall] = {}

    def register_call(self, call_id: str, bot_id: str, phone_number: str) -> ActiveCall:
        call = ActiveCall(call_id=call_id, bot_id=bot_id, phone_number=phone_number)
        self._calls[call_id] = call
        logger.info(f"Voice call registered: {call_id} -> {phone_number}")
        return call

    def get_call(self, call_id: str) -> ActiveCall | None:
        return self._calls.get(call_id)

    def unregister_call(self, call_id: str):
        self._calls.pop(call_id, None)
        logger.info(f"Voice call unregistered: {call_id}")

    async def push_audio(self, call_id: str, audio_chunk: bytes):
        call = self._calls.get(call_id)
        if call and not call._done:
            await call.audio_queue.put(audio_chunk)

    async def stream_audio(self, call_id: str):
        call = self._calls.get(call_id)
        if not call:
            return
        while not call._done:
            try:
                chunk = await asyncio.wait_for(call.audio_queue.get(), timeout=1.0)
                yield chunk
            except asyncio.TimeoutError:
                continue

    def mark_done(self, call_id: str):
        call = self._calls.get(call_id)
        if call:
            call._done = True

    @property
    def active_calls(self) -> list[ActiveCall]:
        return list(self._calls.values())
