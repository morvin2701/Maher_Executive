import json
import os

import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase(app):
    project_id = app.config.get("FIREBASE_PROJECT_ID") or os.environ.get("FIREBASE_PROJECT_ID")
    cred_path = app.config.get("GOOGLE_APPLICATION_CREDENTIALS") or os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )
    cred_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "")
    cred_json_b64 = os.environ.get("FIREBASE_SERVICE_ACCOUNT_B64", "")
    options = {"projectId": project_id} if project_id else None
    if firebase_admin._apps:
        return

    if cred_path and os.path.isfile(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, options=options)
        return

    if cred_json:
        cred = credentials.Certificate(json.loads(cred_json))
        firebase_admin.initialize_app(cred, options=options)
        return

    if cred_json_b64:
        import base64

        payload = base64.b64decode(cred_json_b64).decode("utf-8")
        cred = credentials.Certificate(json.loads(payload))
        firebase_admin.initialize_app(cred, options=options)
        return

    # Falls back to Application Default Credentials.
    # If ADC is unavailable (common on Vercel), token verification / Firestore writes may fail.
    firebase_admin.initialize_app(options=options)


def get_firestore():
    return firestore.client()
