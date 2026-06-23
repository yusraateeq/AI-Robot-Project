import os

import firebase_admin
from firebase_admin import credentials, auth

from src.config.settings import settings


_firebase_app = None


def get_firebase_app():
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    project_id = os.getenv("FIREBASE_PROJECT_ID", "")
    client_email = os.getenv("FIREBASE_CLIENT_EMAIL", "")
    private_key = os.getenv("FIREBASE_PRIVATE_KEY", "")

    if project_id and client_email and private_key:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": project_id,
            "private_key_id": "",
            "private_key": private_key.replace("\\n", "\n"),
            "client_email": client_email,
            "client_id": "",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{client_email}",
        })
        _firebase_app = firebase_admin.initialize_app(cred)
    else:
        _firebase_app = firebase_admin.initialize_app()

    return _firebase_app


async def verify_firebase_token(id_token: str) -> dict:
    app = get_firebase_app()
    try:
        decoded = auth.verify_id_token(id_token, app=app)
        return decoded
    except Exception as e:
        raise ValueError(f"Invalid Firebase token: {e}")
