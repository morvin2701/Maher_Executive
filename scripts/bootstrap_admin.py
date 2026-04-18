#!/usr/bin/env python3
"""
One-time helper: create or update an admin Firebase Auth user and Firestore profile.
Requires GOOGLE_APPLICATION_CREDENTIALS and bootstrap env vars (see .env.example).
"""
import os
import sys

from _load_env import load_repo_env

load_repo_env()

import firebase_admin
from firebase_admin import auth, credentials, firestore

EMAIL = (os.environ.get("BOOTSTRAP_ADMIN_EMAIL") or "").strip()
PASSWORD = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD") or ""


def init_admin():
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not cred_path or not os.path.isfile(cred_path):
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS must point to a valid service account JSON")
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(cred_path))


def ensure_admin_user(db):
    if not EMAIL:
        raise RuntimeError("Set BOOTSTRAP_ADMIN_EMAIL in .env")
    if not PASSWORD or len(PASSWORD) < 6:
        raise RuntimeError("Set BOOTSTRAP_ADMIN_PASSWORD in .env (min 6 characters)")
    try:
        user = auth.get_user_by_email(EMAIL)
        uid = user.uid
        auth.update_user(uid, password=PASSWORD)
    except auth.UserNotFoundError:
        user = auth.create_user(email=EMAIL, password=PASSWORD, email_verified=True)
        uid = user.uid

    db.collection("users").document(uid).set(
        {
            "name": os.environ.get("BOOTSTRAP_ADMIN_NAME") or "Admin",
            "email": EMAIL,
            "phone": "",
            "avatar": "",
            "role": "admin",
            "isActive": True,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "lastLogin": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )
    return uid


if __name__ == "__main__":
    try:
        init_admin()
        db = firestore.client()
        uid = ensure_admin_user(db)
        print(f"Admin ready: {EMAIL} (uid={uid})")
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
