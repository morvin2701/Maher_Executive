from functools import wraps
from typing import Optional

from firebase_admin import auth
from firebase_admin import firestore
from flask import jsonify, request

from clothing_store.firebase_init import get_firestore


def verify_id_token_required():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    try:
        return auth.verify_id_token(token)
    except Exception:
        return None


def get_user_role(uid: str) -> str:
    try:
        db = get_firestore()
        doc = db.collection("users").document(uid).get()
    except Exception:
        return "user"
    if not doc.exists:
        return "user"
    return (doc.to_dict() or {}).get("role", "user")


def ensure_user_document(uid: str, email: str, name: Optional[str] = None):
    try:
        db = get_firestore()
        ref = db.collection("users").document(uid)
        snap = ref.get()
        if snap.exists:
            ref.update({"lastLogin": firestore.SERVER_TIMESTAMP})
            return
        ref.set(
            {
                "name": name or email.split("@")[0],
                "email": email,
                "phone": "",
                "avatar": "",
                "role": "user",
                "createdAt": firestore.SERVER_TIMESTAMP,
                "lastLogin": firestore.SERVER_TIMESTAMP,
                "isActive": True,
            }
        )
    except Exception:
        # Keep auth flow working even if Firestore admin credentials are missing.
        return


def login_required_json(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        decoded = verify_id_token_required()
        if not decoded:
            return jsonify({"error": "Unauthorized"}), 401
        return f(decoded, *args, **kwargs)

    return wrapper


def admin_required_json(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        decoded = verify_id_token_required()
        if not decoded:
            return jsonify({"error": "Unauthorized"}), 401
        uid = decoded["uid"]
        if get_user_role(uid) != "admin":
            return jsonify({"error": "Forbidden"}), 403
        return f(decoded, *args, **kwargs)

    return wrapper
