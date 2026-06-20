import io

from elevenlabs import AsyncElevenLabs
from openai import AsyncOpenAI

from common.config import settings


class SpeechHandler:
    """
    Handles Speech-to-Text (OpenAI Whisper) and Text-to-Speech (ElevenLabs).
    Provides raw audio bytes that the VoiceManager streams during calls.
    """

    def __init__(self):
        self.stt_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.tts_client = AsyncElevenLabs(api_key=settings.elevenlabs_api_key)

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
