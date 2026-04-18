#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta, timezone

from _load_env import load_repo_env

load_repo_env()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import firebase_admin
from firebase_admin import credentials, firestore


def init_db():
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not cred_path or not os.path.isfile(cred_path):
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS missing or invalid")
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(cred_path))
    return firestore.client()


def seed_banners(db):
    banners = [
        {
            "id": "banner-winter-edit",
            "title": "Winter Edit 2026",
            "subtitle": "Hero Main - Home Page",
            "placement": "home_hero",
            "status": "live",
            "image": "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?auto=format&fit=crop&w=1200&q=80",
            "engagement": 14200,
        },
        {
            "id": "banner-silk-capsule",
            "title": "Silk Capsule Collection",
            "subtitle": "Mid Section - Home Page",
            "placement": "home_mid",
            "status": "live",
            "image": "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?auto=format&fit=crop&w=1200&q=80",
            "engagement": 4800,
        },
        {
            "id": "banner-archival-acc",
            "title": "Archival Accessories",
            "subtitle": "Category Top - Listing Page",
            "placement": "category_top",
            "status": "draft",
            "image": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=1200&q=80",
            "engagement": 0,
        },
        {
            "id": "banner-member-early",
            "title": "Member Early Access",
            "subtitle": "Overlay - Carousel",
            "placement": "overlay",
            "status": "scheduled",
            "image": "https://images.unsplash.com/photo-1585487000143-ef1f9a6be3e2?auto=format&fit=crop&w=1200&q=80",
            "engagement": 0,
        },
    ]
    for b in banners:
        doc_id = b.pop("id")
        db.collection("banners").document(doc_id).set(
            {
                **b,
                "updatedAt": firestore.SERVER_TIMESTAMP,
                "createdAt": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )


def seed_coupons(db):
    now = datetime.now(timezone.utc)
    coupons = [
        {
            "id": "cpn-fall25",
            "code": "AURA-FALL25",
            "type": "percentage",
            "value": 20,
            "usedCount": 141,
            "usageLimit": 500,
            "status": "active",
            "expiresAt": now + timedelta(days=45),
        },
        {
            "id": "cpn-vip-access",
            "code": "VIP-ACCESS",
            "type": "fixed",
            "value": 500,
            "usedCount": 8,
            "usageLimit": 20,
            "status": "active",
            "expiresAt": now + timedelta(days=90),
        },
        {
            "id": "cpn-welcome10",
            "code": "WELCOME-10",
            "type": "percentage",
            "value": 10,
            "usedCount": 3,
            "usageLimit": 45,
            "status": "active",
            "expiresAt": None,
        },
        {
            "id": "cpn-winter-exp",
            "code": "WINTER-EXP",
            "type": "percentage",
            "value": 30,
            "usedCount": 8,
            "usageLimit": 10,
            "status": "scheduled",
            "expiresAt": now + timedelta(days=20),
        },
        {
            "id": "cpn-expired24",
            "code": "EXPIRED-24",
            "type": "percentage",
            "value": 15,
            "usedCount": 500,
            "usageLimit": 500,
            "status": "expired",
            "expiresAt": now - timedelta(days=30),
        },
    ]
    for c in coupons:
        doc_id = c.pop("id")
        db.collection("coupons").document(doc_id).set(
            {
                **c,
                "updatedAt": firestore.SERVER_TIMESTAMP,
                "createdAt": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )


def seed_returns(db):
    now = datetime.now(timezone.utc)
    returns = [
        {
            "id": "ret-101",
            "orderId": "ord-9202",
            "userId": "",
            "reason": "Size Mismatch",
            "status": "pending_inspection",
            "refundAmount": 2450,
            "createdAt": now - timedelta(days=2),
        },
        {
            "id": "ret-100",
            "orderId": "ord-9005",
            "userId": "",
            "reason": "Defective Fabric",
            "status": "approved",
            "refundAmount": 4100,
            "createdAt": now - timedelta(days=5),
        },
        {
            "id": "ret-099",
            "orderId": "ord-8991",
            "userId": "",
            "reason": "Changed Mind",
            "status": "refunded",
            "refundAmount": 1900,
            "createdAt": now - timedelta(days=8),
        },
        {
            "id": "ret-098",
            "orderId": "ord-8980",
            "userId": "",
            "reason": "Difference from Image",
            "status": "rejected",
            "refundAmount": 0,
            "createdAt": now - timedelta(days=10),
        },
    ]
    for r in returns:
        doc_id = r.pop("id")
        db.collection("returns").document(doc_id).set(
            {
                **r,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )


def seed_reviews(db):
    now = datetime.now(timezone.utc)
    reviews = [
        {
            "id": "rev-101",
            "name": "Sarah J.",
            "email": "sarahj@example.com",
            "productName": "Structured Wool Overcoat",
            "rating": 5,
            "comment": "Absolutely breathtaking. The drape is precisely what I expected from Maher Executive.",
            "status": "approved",
            "createdAt": now - timedelta(days=2),
        },
        {
            "id": "rev-100",
            "name": "Michael R.",
            "email": "michaelr@example.com",
            "productName": "Archival Trench",
            "rating": 4,
            "comment": "Exceptional quality, though the sizing runs slightly larger than archival pieces.",
            "status": "pending",
            "createdAt": now - timedelta(days=3),
        },
        {
            "id": "rev-099",
            "name": "Elena Q.",
            "email": "elenaq@example.com",
            "productName": "Cashmere Knit",
            "rating": 2,
            "comment": "Color was different from the editorial images. Returning for a refund.",
            "status": "escalated",
            "createdAt": now - timedelta(days=5),
        },
    ]
    for r in reviews:
        doc_id = r.pop("id")
        db.collection("reviews").document(doc_id).set(
            {
                **r,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )


def seed_notifications(db):
    now = datetime.now(timezone.utc)
    rows = [
        {
            "id": "com-private-early-access",
            "title": "Private Suite Early Access",
            "message": "Exclusive preview for private tier members with storefront unlock at 20:00.",
            "segment": "Private Tier Clients",
            "reach": 542,
            "openedCount": 293,
            "openRate": 54.06,
            "medium": "crm / push",
            "status": "live",
            "createdAt": now - timedelta(days=1, hours=5),
        },
        {
            "id": "com-winter-shipment-alert",
            "title": "Winter Shipment Alert",
            "message": "Delivery windows updated for metro lanes due to weather-routing shifts.",
            "segment": "All App Users",
            "reach": 18400,
            "openedCount": 7412,
            "openRate": 40.28,
            "medium": "global in-app",
            "status": "live",
            "createdAt": now - timedelta(days=2, hours=3),
        },
        {
            "id": "com-sustainability-update",
            "title": "Sustainability Update",
            "message": "SS26 fabric report and atelier emission footprint now published.",
            "segment": "Newsletter Opt-ins",
            "reach": 42100,
            "openedCount": 17724,
            "openRate": 42.10,
            "medium": "broadcast",
            "status": "scheduled",
            "createdAt": now - timedelta(days=4),
        },
    ]
    for row in rows:
        doc_id = row.pop("id")
        db.collection("admin_notifications").document(doc_id).set(
            {
                **row,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )


def seed_admin_transactions(db):
    now = datetime.now(timezone.utc)
    txs = [
        {
            "id": "trx-8004",
            "referenceTrace": "#TR-8004",
            "amountInr": 124999,
            "gatewayType": "amex",
            "gatewayDisplay": "AMEX •••• 1002",
            "settlementStatus": "succeeded",
            "acquisitionId": "#ORD-9204",
            "createdAt": now - timedelta(days=2, hours=5, minutes=38),
            "isDispute": False,
        },
        {
            "id": "trx-8003",
            "referenceTrace": "#TR-8003",
            "amountInr": 45999,
            "gatewayType": "apple_pay",
            "gatewayDisplay": "APPLE PAY",
            "settlementStatus": "processing",
            "acquisitionId": "#ORD-9198",
            "createdAt": now - timedelta(days=1, hours=3, minutes=12),
            "isDispute": False,
        },
        {
            "id": "trx-8002",
            "referenceTrace": "#TR-8002",
            "amountInr": -12999,
            "gatewayType": "razorpay",
            "gatewayDisplay": "UPI / RAZORPAY",
            "settlementStatus": "refunded",
            "acquisitionId": "#ORD-9181",
            "createdAt": now - timedelta(days=3, hours=8),
            "isDispute": False,
        },
        {
            "id": "trx-8001",
            "referenceTrace": "#TR-8001",
            "amountInr": 289000,
            "gatewayType": "bank_transfer",
            "gatewayDisplay": "BANK TRANSFER",
            "settlementStatus": "succeeded",
            "acquisitionId": "#ORD-9175",
            "createdAt": now - timedelta(days=5, hours=14, minutes=22),
            "isDispute": True,
        },
        {
            "id": "trx-8000",
            "referenceTrace": "#TR-8000",
            "amountInr": 8999,
            "gatewayType": "visa",
            "gatewayDisplay": "VISA •••• 4411",
            "settlementStatus": "succeeded",
            "acquisitionId": "#ORD-9162",
            "createdAt": now - timedelta(days=6, hours=11, minutes=5),
            "isDispute": False,
        },
    ]
    for row in txs:
        doc_id = row.pop("id")
        db.collection("admin_transactions").document(doc_id).set(
            {**row, "updatedAt": firestore.SERVER_TIMESTAMP},
            merge=True,
        )
    db.collection("settings").document("treasury").set(
        {
            "gatewayConnected": True,
            "gatewayLabel": "RAZORPAY CONNECTED",
            "updatedAt": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )


def seed_staff(db):
    rows = [
        {
            "id": "staff-devin-g",
            "name": "Devin G.",
            "email": "dgajjar245@gmail.com",
            "clearanceLevel": "SUPER ADMIN",
            "status": "online",
            "lastTelemetry": "ACTIVE NOW",
            "isActive": True,
        },
        {
            "id": "staff-marco-rossi",
            "name": "Marco Rossi",
            "email": "m.rossi@maher-executive.com",
            "clearanceLevel": "CATALOG MANAGER",
            "status": "offline",
            "lastTelemetry": "3H AGO",
            "isActive": True,
        },
        {
            "id": "staff-elena-vance",
            "name": "Elena Vance",
            "email": "e.vance@studio.co",
            "clearanceLevel": "SUPPORT LEAD",
            "status": "away",
            "lastTelemetry": "12M AGO",
            "isActive": True,
        },
        {
            "id": "staff-julian-voss",
            "name": "Julian Voss",
            "email": "j.voss@maher-executive.com",
            "clearanceLevel": "DIRECTOR",
            "status": "online",
            "lastTelemetry": "ACTIVE NOW",
            "isActive": True,
        },
    ]
    for row in rows:
        doc_id = row.pop("id")
        db.collection("staff").document(doc_id).set(
            {
                **row,
                "updatedAt": firestore.SERVER_TIMESTAMP,
                "createdAt": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )


def seed_system_settings(db):
    from clothing_store.system_settings_defaults import SYSTEM_SETTINGS_DEFAULT

    doc = dict(SYSTEM_SETTINGS_DEFAULT)
    db.collection("settings").document("system_parameters").set(
        {
            **doc,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "createdAt": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )


def main():
    db = init_db()
    seed_banners(db)
    seed_coupons(db)
    seed_returns(db)
    seed_reviews(db)
    seed_notifications(db)
    seed_admin_transactions(db)
    seed_staff(db)
    seed_system_settings(db)
    print(
        "Seeded admin collections: banners, coupons, returns, reviews, notifications, treasury, staff, system_parameters"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
