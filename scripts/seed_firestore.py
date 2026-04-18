#!/usr/bin/env python3
"""
Populate Firestore with sample categories, products, and banners.
Requires: GOOGLE_APPLICATION_CREDENTIALS pointing to a service account JSON
with Cloud Datastore / Firestore permissions.
"""
import os
import sys
import uuid

_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir)
sys.path.insert(0, _root)
sys.path.insert(0, _script_dir)

from _load_env import load_repo_env

load_repo_env()

import firebase_admin
from firebase_admin import credentials, firestore


def main():
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path or not os.path.isfile(cred_path):
        print("Set GOOGLE_APPLICATION_CREDENTIALS to your Firebase service account JSON path.")
        sys.exit(1)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(cred_path))

    db = firestore.client()

    categories = [
        {"name": "Women", "slug": "women", "isVisible": True, "sortOrder": 1},
        {"name": "Men", "slug": "men", "isVisible": True, "sortOrder": 2},
        {"name": "Kids", "slug": "kids", "isVisible": True, "sortOrder": 3},
    ]
    for c in categories:
        db.collection("categories").document(c["slug"]).set(
            {
                **c,
                "parentId": None,
                "description": "",
                "image": "",
            }
        )

    sample_img = (
        "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab"
        "?auto=format&fit=crop&w=800&q=80"
    )

    products = [
        {
            "name": "Merino Crew Knit",
            "slug": "merino-crew-knit",
            "description": "Fine-gauge merino with a clean shoulder line and soft drape.",
            "brand": "ME",
            "category": "women",
            "subcategory": "knitwear",
            "price": 8999,
            "comparePrice": 10999,
            "discount": 18,
            "images": [{"url": sample_img, "alt": "Merino crew"}],
            "variants": [{"size": "S", "color": "Black", "stock": 12, "sku": "ME-W-KN-001-S-BLK"}],
            "tags": ["winter", "knit"],
            "rating": 4.7,
            "reviewCount": 32,
            "isFeatured": True,
            "isNew": True,
            "isBestseller": True,
            "isPublished": True,
        },
        {
            "name": "Tailored Wool Coat",
            "slug": "tailored-wool-coat",
            "description": "Double-faced wool in a relaxed tailored block.",
            "brand": "ME",
            "category": "women",
            "subcategory": "outerwear",
            "price": 24999,
            "comparePrice": 27999,
            "discount": 11,
            "images": [{"url": sample_img, "alt": "Wool coat"}],
            "variants": [{"size": "M", "color": "Camel", "stock": 6, "sku": "ME-W-OT-014-M-CML"}],
            "tags": ["coat", "wool"],
            "rating": 4.9,
            "reviewCount": 18,
            "isFeatured": True,
            "isNew": False,
            "isBestseller": True,
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

    db.collection("banners").document("hero-1").set(
        {
            "title": "Winter Edit",
            "subtitle": "Refined layers",
            "image": sample_img,
            "link": "/shop",
            "position": "hero",
            "isActive": True,
            "sortOrder": 1,
            "startDate": None,
            "endDate": None,
        }
    )

    db.collection("settings").document("store").set(
        {
            "name": "ME Clothing",
            "currency": "INR",
            "freeShippingThreshold": 2999,
            "taxRate": 0,
        }
    )

    print("Seed complete. Set your Firebase user document role to 'admin' for your UID in Firestore.")


if __name__ == "__main__":
    main()
