import os

from google.oauth2 import id_token
from google.auth.transport import requests

from src.config.settings import settings


_PROJECT_ID = (
    os.getenv("FIREBASE_PROJECT_ID")
    or os.getenv("NEXT_PUBLIC_FIREBASE_PROJECT_ID")
    or ""
)

_REQUEST = requests.Request()


async def verify_firebase_token(firebase_token: str) -> dict:
    if not _PROJECT_ID:
        raise ValueError(
            "Firebase project ID is not configured. "
            "Set FIREBASE_PROJECT_ID or NEXT_PUBLIC_FIREBASE_PROJECT_ID in .env"
        )

    try:
        decoded = id_token.verify_firebase_token(
            firebase_token, request=_REQUEST, audience=_PROJECT_ID
        )
        return decoded
    except ValueError as e:
        raise ValueError(f"Invalid Firebase token: {e}")
