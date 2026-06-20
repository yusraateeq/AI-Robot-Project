import re

from loguru import logger
from openai import AsyncOpenAI

from common.config import settings


class ConversationEngine:
    """
    Manages OpenAI chat completions for AI voice conversations.
    Maintains conversation history per call session and generates
    context-aware responses, summaries, and dispositions.
    Can load and follow a structured call script from resources/script.txt.
    """

    SYSTEM_PROMPT = (
        "You are an AI voice assistant for a sales outreach campaign. "
        "Your name is Mary. You are professional, warm, and concise. "
        "Keep responses under 30 words. Ask qualifying questions. "
        "If the prospect is not interested, politely end the call."
    )

    SCRIPT_PROMPT = (
        "You are an AI voice assistant named Mary running a Medicare benefits "
        "outreach call. Follow the script exactly. Speak naturally and concisely. "
        "Start with the [GREETING] section. After the prospect responds, "
        "ask the [QUALIFICATION_QUESTION]. If they confirm having Medicare Part A "
        "and Part B, proceed with [TRANSFER_PROCESS]. Otherwise politely end the call."
    )

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._sessions: dict[str, list[dict]] = {}
        self.script_sections: dict[str, str] = {}
        self._script_loaded = False

    def _session_key(self, call_id: str) -> str:
        return call_id

    def create_session(self, call_id: str):
        self._sessions[self._session_key(call_id)] = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]

    def add_message(self, call_id: str, role: str, content: str):
        key = self._session_key(call_id)
        if key not in self._sessions:
            self.create_session(call_id)
        self._sessions[key].append({"role": role, "content": content})

    async def generate_response(self, call_id: str, user_text: str) -> str:
        self.add_message(call_id, "user", user_text)
        messages = self._sessions.get(self._session_key(call_id), [])

        completion = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            max_tokens=150,
            temperature=0.7,
        )

        reply = completion.choices[0].message.content or ""
        self.add_message(call_id, "assistant", reply)
        return reply

    async def generate_summary(self, call_id: str) -> str:
        messages = self._sessions.get(self._session_key(call_id), [])
        if not messages:
            return ""

        transcript = "\n".join(
            f"{m['role']}: {m['content']}" for m in messages if m["role"] != "system"
        )

        completion = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "Summarize this sales call transcript in 2-3 sentences. "
                    "Include the prospect's interest level and any follow-up needed.",
                },
                {"role": "user", "content": transcript},
            ],
            max_tokens=200,
        )
        return completion.choices[0].message.content or ""

    async def determine_disposition(self, call_id: str) -> str:
        messages = self._sessions.get(self._session_key(call_id), [])
        transcript = "\n".join(
            f"{m['role']}: {m['content']}" for m in messages if m["role"] != "system"
        )

        completion = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "Classify this call into exactly one: "
                    "INTERESTED, NOT_INTERESTED, CALLBACK, WRONG_NUMBER, VOICEMAIL, DISCONNECTED",
                },
                {"role": "user", "content": transcript},
            ],
            max_tokens=20,
            temperature=0,
        )
        return (completion.choices[0].message.content or "UNKNOWN").strip()

    # ── Script management ──────────────────────────────────────────

    def load_script(self, filepath: str):
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        parts = re.split(r"^\[(\w+)\]\s*$", content, flags=re.MULTILINE)
        parts = [p.strip() for p in parts if p.strip()]

        self.script_sections = {}
        for i in range(0, len(parts) - 1, 2):
            key = parts[i]
            val = parts[i + 1] if i + 1 < len(parts) else ""
            self.script_sections[key] = val

        if not self.script_sections:
            self.script_sections["SCRIPT"] = content

        self._script_loaded = True
        logger.info(
            f"Script loaded — sections: {list(self.script_sections.keys())}"
        )

    def get_section(self, name: str) -> str:
        return self.script_sections.get(name, "")

    def set_script_mode(self, call_id: str):
        script_context = "\n\n".join(
            f"[{k}]\n{v}" for k, v in self.script_sections.items()
        )
        prompt = (
            f"{self.SCRIPT_PROMPT}\n\n"
            f"CALL SCRIPT:\n{script_context}\n\n"
            "Remember: speak naturally and keep responses brief."
        )
        self._sessions[self._session_key(call_id)] = [
            {"role": "system", "content": prompt}
        ]

    @property
    def script_loaded(self) -> bool:
        return self._script_loaded

    def clear_session(self, call_id: str):
        self._sessions.pop(self._session_key(call_id), None)
