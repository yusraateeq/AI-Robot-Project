import os

from loguru import logger

from brain_agent.conversation_engine import ConversationEngine
from brain_agent.speech_handler import SpeechHandler
from brain_agent.voice_manager import VoiceManager
from common.config import settings


class BrainAgent:
    """
    Brain Agent — conversational AI core.
    Orchestrates STT (Whisper), LLM reasoning (OpenAI), and TTS (ElevenLabs)
    to power natural voice conversations for active calls.
    Integrates with a structured call script for Medicare outreach.
    """

    def __init__(self):
        self.conversation = ConversationEngine()
        self.speech = SpeechHandler()
        self.voice = VoiceManager()
        self._running = False
        self._script_filepath: str | None = None

    async def start(self):
        self._running = True
        logger.info("Brain Agent started — ready for conversations")

    async def stop(self):
        self._running = False
        logger.info("Brain Agent stopped")

    # ── Script loading ─────────────────────────────────────────────

    def load_script(self, filepath: str | None = None):
        if filepath is None:
            filepath = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "resources",
                "script.txt",
            )
        self._script_filepath = filepath
        self.conversation.load_script(filepath)
        logger.info(f"Call script loaded from {filepath}")

    # ── Script-guided call flow ────────────────────────────────────

    async def start_call_with_greeting(self, call_id: str):
        """Set up scripted session, return the greeting text + audio."""
        if not self.conversation.script_loaded:
            self.load_script()

        self.conversation.set_script_mode(call_id)

        raw = self.conversation.get_section("GREETING")
        greeting = raw.replace("[AGENT_NAME]", "Mary")

        self.conversation.add_message(call_id, "assistant", greeting)
        audio = await self.speech.synthesize(greeting)

        logger.info(f"[{call_id}] *** GREETING DELIVERED ***")
        return greeting, audio

    async def check_medicare_qualification(
        self, call_id: str, user_text: str
    ):
        """
        Analyze the user's response to the Part A & B question.
        Returns (decision, next_text, audio).
        decision is 'YES', 'NO', or 'UNCLEAR'.
        """
        self.conversation.add_message(call_id, "user", user_text)

        analysis = await self.conversation.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Determine if the prospect confirmed they have "
                        "Medicare Part A and Part B. Reply with exactly "
                        "one word: YES, NO, or UNCLEAR."
                    ),
                },
                {"role": "user", "content": user_text},
            ],
            max_tokens=10,
            temperature=0,
        )
        decision = (
            (analysis.choices[0].message.content or "UNCLEAR")
            .strip()
            .upper()
        )

        if decision == "YES":
            transfer = self.conversation.get_section("TRANSFER_PROCESS")
            if "(If YES):" in transfer:
                transfer = (
                    transfer.split("(If YES):")[1]
                    .split("(If NO")[0]
                    .strip()
                )
            self.conversation.add_message(call_id, "assistant", transfer)
            audio = await self.speech.synthesize(transfer)
            logger.info(
                f"[{call_id}] *** MEDICARE QUALIFIED *** "
                f"-> TRANSFER_PROCESS triggered"
            )
            return decision, transfer, audio

        no_text = "I understand. Thank you for your time, have a great day."
        transfer = self.conversation.get_section("TRANSFER_PROCESS")
        if "(If NO/OTHER):" in transfer:
            no_text = transfer.split("(If NO/OTHER):")[1].strip()

        self.conversation.add_message(call_id, "assistant", no_text)
        audio = await self.speech.synthesize(no_text)
        logger.info(
            f"[{call_id}] *** MEDICARE NOT CONFIRMED ({decision}) *** "
            f"-> call ended politely"
        )
        return decision, no_text, audio

    # ── Standard audio pipeline ────────────────────────────────────

    async def process_audio(self, call_id: str, audio_bytes: bytes) -> bytes | None:
        if not self._running:
            return None

        transcript = await self.speech.transcribe(audio_bytes)
        if not transcript:
            return None

        logger.debug(f"[{call_id}] STT: {transcript}")

        reply = await self.conversation.generate_response(call_id, transcript)

        audio_response = await self.speech.synthesize(reply)
        logger.debug(f"[{call_id}] TTS: {reply}")

        return audio_response

    async def finalize_call(self, call_id: str) -> dict:
        summary = await self.conversation.generate_summary(call_id)
        disposition = await self.conversation.determine_disposition(call_id)
        self.conversation.clear_session(call_id)
        self.voice.unregister_call(call_id)

        return {
            "call_id": call_id,
            "summary": summary,
            "disposition": disposition,
        }

    @property
    def is_running(self) -> bool:
        return self._running


# Singleton
brain_agent = BrainAgent()
