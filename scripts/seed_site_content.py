#!/usr/bin/env python3
import os
import sys

from _load_env import load_repo_env

load_repo_env()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import firebase_admin
from firebase_admin import credentials, firestore

from clothing_store.content_defaults import CONTENT_DEFAULTS


def main():
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not cred_path or not os.path.isfile(cred_path):
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS missing or invalid")

    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(cred_path))

    db = firestore.client()
    for page_key, payload in CONTENT_DEFAULTS.items():
        db.collection("content_pages").document(page_key).set(
            {
                **payload,
                "pageKey": page_key,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )
    print(f"Seeded content_pages docs: {len(CONTENT_DEFAULTS)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
