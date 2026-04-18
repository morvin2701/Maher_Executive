from copy import deepcopy

from firebase_admin import firestore

from clothing_store.content_defaults import CONTENT_DEFAULTS
from clothing_store.firebase_init import get_firestore


def _deep_merge(base, incoming):
    if not isinstance(base, dict) or not isinstance(incoming, dict):
        return deepcopy(incoming)
    merged = deepcopy(base)
    for key, value in incoming.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _fallback(page_key: str):
    base = CONTENT_DEFAULTS.get(
        page_key,
        {
            "title": page_key.replace("_", " ").title(),
            "subtitle": "Premium content placeholder.",
            "highlights": [
                "This section is ready for Firestore CMS content.",
                "Update content_pages collection to customize text.",
                "Defaults render automatically for new deployments.",
            ],
        },
    )
    return deepcopy(base)


def get_page_content(page_key: str):
    data = _fallback(page_key)
    try:
        db = get_firestore()
        ref = db.collection("content_pages").document(page_key)
        snap = ref.get()
        if snap.exists:
            remote = snap.to_dict() or {}
            return _deep_merge(data, remote)

        ref.set(
            {
                **data,
                "pageKey": page_key,
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )
    except Exception:
        return data
    return data
