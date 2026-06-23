import io

from elevenlabs import AsyncElevenLabs
from openai import AsyncOpenAI

from src.config.settings import settings


class SpeechHandler:
    def __init__(self):
        self._stt: AsyncOpenAI | None = None
        self._tts: AsyncElevenLabs | None = None

    @property
    def stt_client(self) -> AsyncOpenAI:
        if self._stt is None:
            self._stt = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._stt

    @property
    def tts_client(self) -> AsyncElevenLabs:
        if self._tts is None:
            self._tts = AsyncElevenLabs(api_key=settings.elevenlabs_api_key)
        return self._tts

    async def transcribe(self, audio_bytes: bytes) -> str:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"

        transcript = await self.stt_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",
            language="en",
        )
        return transcript.strip()

    async def synthesize(self, text: str) -> bytes:
        audio_stream = await self.tts_client.text_to_speech.convert(
            voice_id=settings.elevenlabs_voice_id,
            model_id="eleven_turbo_v2_5",
            text=text,
            output_format="ulaw_8000",
        )
        if isinstance(audio_stream, bytes):
            return audio_stream
        return b"".join(chunk async for chunk in audio_stream)
