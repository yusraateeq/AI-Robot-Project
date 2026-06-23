import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CANDIDATES = [
    _PROJECT_ROOT / ".env",
    Path.cwd() / ".env",
    _PROJECT_ROOT / ".env.txt",
    _PROJECT_ROOT / "..env",
]

_loaded = False
for p in _CANDIDATES:
    if p.exists():
        load_dotenv(dotenv_path=p, override=True)
        _loaded = True
        break

if not _loaded:
    print(
        f"[config] WARNING: No .env file found. "
        f"Searched: {_PROJECT_ROOT / '.env'}, CWD, .env.txt, ..env. "
        f"Copy .env.example -> .env and add your API keys.",
        file=sys.stderr,
    )


@dataclass
class Settings:
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    api_port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "3002")))
    socket_port: int = field(default_factory=lambda: int(os.getenv("SOCKET_PORT", "3001")))

    database_url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite+aiosqlite:///redstone_crm.db")
    )

    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    openai_voice: str = field(default_factory=lambda: os.getenv("OPENAI_VOICE", "alloy"))

    elevenlabs_api_key: str = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))
    elevenlabs_voice_id: str = field(
        default_factory=lambda: os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    )

    vicidial_url: str = field(default_factory=lambda: os.getenv("VICIDIAL_URL", "http://localhost:80"))
    vicidial_user: str = field(default_factory=lambda: os.getenv("VICIDIAL_USER", "admin"))
    vicidial_pass: str = field(default_factory=lambda: os.getenv("VICIDIAL_PASS", ""))
    vicidial_campaign: str = field(default_factory=lambda: os.getenv("VICIDIAL_CAMPAIGN", "RedstoneCampaign"))
    phone_ext: str = field(default_factory=lambda: os.getenv("PHONE_EXT", ""))
    phone_pass: str = field(default_factory=lambda: os.getenv("PHONE_PASS", ""))

    sip_bypass: bool = field(default_factory=lambda: os.getenv("SIP_BYPASS", "False").lower() in ("true", "1", "yes"))
    sip_server_ip: str = field(default_factory=lambda: os.getenv("SIP_SERVER_IP", ""))
    sip_extension: str = field(default_factory=lambda: os.getenv("SIP_EXTENSION", ""))
    sip_registration_password: str = field(
        default_factory=lambda: os.getenv("SIP_REGISTRATION_PASSWORD", "")
    )

    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", "change-me-in-production"))
    jwt_algorithm: str = field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))

    greeting_recording: str = field(
        default_factory=lambda: os.getenv("GREETING_RECORDING", "Recording11")
    )
    transfer_number: str = field(
        default_factory=lambda: os.getenv("TRANSFER_NUMBER", "")
    )
    silence_timeout: float = field(
        default_factory=lambda: float(os.getenv("SILENCE_TIMEOUT", "3.0"))
    )
    no_response_action: str = field(
        default_factory=lambda: os.getenv("NO_RESPONSE_ACTION", "hangup")
    )


settings = Settings()
