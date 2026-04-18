import os

import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase(app):
    project_id = app.config.get("FIREBASE_PROJECT_ID") or os.environ.get("FIREBASE_PROJECT_ID")
    cred_path = app.config.get("GOOGLE_APPLICATION_CREDENTIALS") or os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )
    options = {"projectId": project_id} if project_id else None
    if cred_path and os.path.isfile(cred_path):
        cred = credentials.Certificate(cred_path)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, options=options)
    else:
        if not firebase_admin._apps:
            # Falls back to Application Default Credentials.
            # If ADC is unavailable, token verification / Firestore writes may fail.
            firebase_admin.initialize_app(options=options)


def get_firestore():
    return firestore.client()
