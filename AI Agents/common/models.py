from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Bot:
    id: str
    name: str
    status: str = "idle"
    campaign_id: Optional[str] = None
    extension: Optional[str] = None
    active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class CallLog:
    id: str
    bot_id: str
    phone_number: str
    lead_id: Optional[str] = None
    status: str = "pending"
    duration: Optional[float] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    disposition: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class Setting:
    key: str
    value: str
    updated_at: Optional[str] = None
