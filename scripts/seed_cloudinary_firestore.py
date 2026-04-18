#!/usr/bin/env python3
import os
import sys
import uuid

import requests
from _load_env import load_repo_env

load_repo_env()

import firebase_admin
from firebase_admin import credentials, firestore

CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
UPLOAD_PRESET = os.environ.get("CLOUDINARY_UPLOAD_PRESET", "")
FOLDER = os.environ.get("CLOUDINARY_FOLDER", "clothesecommerce")
LOCAL_IMAGE = (os.environ.get("SEED_LOCAL_IMAGE_PATH") or "").strip()


def init_firebase_admin():
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not cred_path or not os.path.isfile(cred_path):
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS must point to a valid service account JSON")
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(cred_path))


def upload_image(path):
    if not os.path.isfile(path):
        raise RuntimeError(f"Image not found: {path}")
    url = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/image/upload"
    with open(path, "rb") as f:
        files = {"file": f}
        data = {"upload_preset": UPLOAD_PRESET, "folder": FOLDER}
        r = requests.post(url, files=files, data=data, timeout=60)
    if r.status_code >= 300:
        raise RuntimeError(f"Cloudinary upload failed: {r.status_code} {r.text}")
    payload = r.json()
    return payload["secure_url"]


def seed_products(img_url):
    db = firestore.client()
    products = [
        {
            "name": "ME Signature Noir Blazer",
            "slug": "me-signature-noir-blazer",
            "description": "Tailored statement blazer in premium matte finish.",
            "brand": "ME",
            "category": "women",
            "subcategory": "blazers",
            "price": 12999,
            "comparePrice": 15999,
            "discount": 19,
            "images": [{"url": img_url, "alt": "Noir blazer"}],
            "variants": [{"size": "S", "color": "Black", "stock": 14, "sku": "ME-W-BLZ-001-S-BLK"}],
            "tags": ["luxury", "new"],
            "rating": 4.8,
            "reviewCount": 12,
            "isFeatured": True,
            "isNew": True,
            "isBestseller": True,
            "isPublished": True,
        },
        {
            "name": "ME Street Premium Hoodie",
            "slug": "me-street-premium-hoodie",
            "description": "Heavyweight brushed fleece hoodie with subtle branding.",
            "brand": "ME Street",
            "category": "men",
            "subcategory": "hoodies",
            "price": 5499,
            "comparePrice": 6999,
            "discount": 21,
            "images": [{"url": img_url, "alt": "Premium hoodie"}],
            "variants": [{"size": "M", "color": "Graphite", "stock": 26, "sku": "ME-M-HOD-018-M-GPH"}],
            "tags": ["street", "new"],
            "rating": 4.6,
            "reviewCount": 19,
            "isFeatured": True,
            "isNew": True,
            "isBestseller": False,
            "isPublished": True,
        },
    ]

    for p in products:
        pid = uuid.uuid4().hex[:16]
        db.collection("products").document(pid).set(
            {
                **p,
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            }
        )


if __name__ == "__main__":
    try:
        if not CLOUD_NAME or not UPLOAD_PRESET:
            raise RuntimeError(
                "Set CLOUDINARY_CLOUD_NAME and CLOUDINARY_UPLOAD_PRESET in .env (required for upload)."
            )
        if not LOCAL_IMAGE or not os.path.isfile(LOCAL_IMAGE):
            raise RuntimeError(
                "Set SEED_LOCAL_IMAGE_PATH in .env to a readable image file for the sample seed."
            )
        init_firebase_admin()
        image_url = upload_image(LOCAL_IMAGE)
        seed_products(image_url)
        print("Seeded Firestore products with Cloudinary image:")
        print(image_url)
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
