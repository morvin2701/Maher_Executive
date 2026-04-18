import csv
import hashlib
import hmac
import io
import json
import uuid
from datetime import datetime, timedelta, timezone

import razorpay
from firebase_admin import firestore
from flask import Blueprint, current_app, jsonify, request, Response

from clothing_store.auth_utils import (
    admin_required_json,
    ensure_user_document,
    get_user_role,
    login_required_json,
    verify_id_token_required,
)
from clothing_store.content_service import get_page_content
from clothing_store.demo_data import DEMO_PRODUCTS
from clothing_store.firebase_init import get_firestore
from clothing_store.system_settings_defaults import SYSTEM_SETTINGS_DEFAULT, merge_system_settings

bp = Blueprint("api", __name__, url_prefix="/api")


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _serialize(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    return value


def _as_datetime(value):
    if isinstance(value, datetime):
        return value
    return None


def _slugify(value: str) -> str:
    text = (value or "").strip().lower()
    out = []
    prev_dash = False
    for ch in text:
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        elif not prev_dash:
            out.append("-")
            prev_dash = True
    slug = "".join(out).strip("-")
    return slug or "category"


@bp.get("/config")
def public_config():
    """Client-safe Firebase + Cloudinary settings (no secrets)."""
    cfg = current_app.config
    return jsonify(
        {
            "firebase": {
                "apiKey": cfg["FIREBASE_API_KEY"],
                "authDomain": cfg["FIREBASE_AUTH_DOMAIN"],
                "projectId": cfg["FIREBASE_PROJECT_ID"],
                "storageBucket": cfg["FIREBASE_STORAGE_BUCKET"],
                "messagingSenderId": cfg["FIREBASE_MESSAGING_SENDER_ID"],
                "appId": cfg["FIREBASE_APP_ID"],
                "measurementId": cfg.get("FIREBASE_MEASUREMENT_ID", ""),
            },
            "cloudinary": {
                "cloudName": cfg["CLOUDINARY_CLOUD_NAME"],
                "uploadPreset": cfg["CLOUDINARY_UPLOAD_PRESET"],
                "folder": cfg["CLOUDINARY_FOLDER"],
            },
        }
    )


@bp.get("/content/<page_key>")
def page_content(page_key):
    return jsonify(get_page_content(page_key))


@bp.post("/auth/session")
def auth_session():
    data = request.get_json(force=True, silent=True) or {}
    id_token = data.get("idToken")
    if not id_token:
        return jsonify({"error": "idToken required"}), 400
    from firebase_admin import auth as fb_auth

    try:
        decoded = fb_auth.verify_id_token(id_token)
    except Exception as e:
        current_app.logger.exception("Firebase token verification failed")
        return (
            jsonify(
                {
                    "error": str(e),
                    "hint": "Check GOOGLE_APPLICATION_CREDENTIALS path and Firebase project alignment.",
                }
            ),
            401,
        )

    uid = decoded["uid"]
    email = decoded.get("email") or ""
    name = decoded.get("name") or decoded.get("email", "").split("@")[0]
    warning = None
    try:
        ensure_user_document(uid, email, name)
    except Exception as e:
        warning = str(e)
    role = get_user_role(uid)
    return jsonify({"ok": True, "uid": uid, "email": email, "role": role, "warning": warning})


@bp.get("/me")
@login_required_json
def me(decoded):
    uid = decoded["uid"]
    db = get_firestore()
    doc = db.collection("users").document(uid).get()
    data = doc.to_dict() if doc.exists else {}
    return jsonify(_serialize({"uid": uid, **(data or {})}))


@bp.patch("/me")
@login_required_json
def update_me(decoded):
    uid = decoded["uid"]
    payload = request.get_json(force=True, silent=True) or {}
    allowed = {"name", "phone", "avatar"}
    patch = {k: v for k, v in payload.items() if k in allowed}
    if not patch:
        return jsonify({"error": "No editable fields provided"}), 400
    patch["updatedAt"] = firestore.SERVER_TIMESTAMP
    db = get_firestore()
    db.collection("users").document(uid).set(patch, merge=True)
    doc = db.collection("users").document(uid).get()
    data = doc.to_dict() if doc.exists else {}
    return jsonify(_serialize({"ok": True, "user": {"uid": uid, **(data or {})}}))


@bp.get("/products")
def list_products():
    category = request.args.get("category")
    items = []
    try:
        db = get_firestore()
        limit = min(int(request.args.get("limit", 200)), 500)
        docs = db.collection("products").where("isPublished", "==", True).limit(limit).stream()
        for d in docs:
            row = d.to_dict() or {}
            if category and row.get("category") != category:
                continue
            row["id"] = d.id
            items.append(row)
    except Exception:
        items = [p for p in DEMO_PRODUCTS if (not category or p.get("category") == category)]
    if not items:
        items = [p for p in DEMO_PRODUCTS if (not category or p.get("category") == category)]
    return jsonify({"products": items})


@bp.get("/products/slug/<slug>")
def product_by_slug(slug):
    try:
        db = get_firestore()
        for d in db.collection("products").where("slug", "==", slug).limit(5).stream():
            row = d.to_dict() or {}
            if not row.get("isPublished", True):
                continue
            row["id"] = d.id
            return jsonify(row)
    except Exception:
        pass
    for row in DEMO_PRODUCTS:
        if row.get("slug") == slug:
            return jsonify(row)
    return jsonify({"error": "Not found"}), 404


@bp.post("/admin/products")
@admin_required_json
def admin_create_product(decoded):
    data = request.get_json(force=True, silent=True) or {}
    if "images" not in data:
        return jsonify({"error": "missing images"}), 400
    required = ["name", "slug", "description", "brand", "price"]
    for k in required:
        if k not in data:
            return jsonify({"error": f"missing {k}"}), 400
    images = data.get("images")
    if not isinstance(images, list):
        return jsonify({"error": "images must be an array"}), 400
    is_published = bool(data.get("isPublished", True))
    if is_published and len(images) == 0:
        return jsonify({"error": "published products require at least one image"}), 400
    db = get_firestore()
    pid = data.get("id") or uuid.uuid4().hex[:20]
    doc = {
        "name": data["name"],
        "slug": data["slug"],
        "description": data["description"],
        "brand": data.get("brand", ""),
        "category": data.get("category", ""),
        "subcategory": data.get("subcategory", ""),
        "price": float(data["price"]),
        "comparePrice": float(data.get("comparePrice") or 0),
        "discount": float(data.get("discount") or 0),
        "images": images,
        "variants": data.get("variants") or [],
        "tags": data.get("tags") or [],
        "rating": float(data.get("rating") or 0),
        "reviewCount": int(data.get("reviewCount") or 0),
        "isFeatured": bool(data.get("isFeatured")),
        "isNew": bool(data.get("isNew")),
        "isBestseller": bool(data.get("isBestseller")),
        "isPublished": is_published,
        "sku": str(data.get("sku") or ""),
        "metaTitle": str(data.get("metaTitle") or ""),
        "metaDescription": str(data.get("metaDescription") or ""),
        "composition": str(data.get("composition") or ""),
        "colorway": str(data.get("colorway") or ""),
        "createdAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }
    db.collection("products").document(pid).set(doc)
    return jsonify({"id": pid})


@bp.put("/admin/products/<product_id>")
@admin_required_json
def admin_update_product(decoded, product_id):
    data = request.get_json(force=True, silent=True) or {}
    db = get_firestore()
    ref = db.collection("products").document(product_id)
    if not ref.get().exists:
        return jsonify({"error": "not found"}), 404
    allowed = {
        "name",
        "slug",
        "description",
        "brand",
        "category",
        "subcategory",
        "price",
        "comparePrice",
        "discount",
        "images",
        "variants",
        "tags",
        "rating",
        "reviewCount",
        "isFeatured",
        "isNew",
        "isBestseller",
        "isPublished",
        "sku",
        "metaTitle",
        "metaDescription",
        "composition",
        "colorway",
    }
    patch = {k: v for k, v in data.items() if k in allowed}
    cur = ref.get().to_dict() or {}
    merged_pub = patch["isPublished"] if "isPublished" in patch else cur.get("isPublished", False)
    merged_images = patch["images"] if "images" in patch else cur.get("images") or []
    if merged_pub and not merged_images:
        return jsonify({"error": "published products require at least one image"}), 400
    patch["updatedAt"] = firestore.SERVER_TIMESTAMP
    ref.update(patch)
    return jsonify({"ok": True})


@bp.delete("/admin/products/<product_id>")
@admin_required_json
def admin_delete_product(decoded, product_id):
    db = get_firestore()
    db.collection("products").document(product_id).delete()
    return jsonify({"ok": True})


@bp.get("/admin/products")
@admin_required_json
def admin_list_products(decoded):
    db = get_firestore()
    docs = db.collection("products").stream()
    items = []
    for d in docs:
        row = d.to_dict() or {}
        row["id"] = d.id
        items.append(row)
    return jsonify({"products": items})


@bp.get("/admin/dashboard")
@admin_required_json
def admin_dashboard_data(decoded):
    db = get_firestore()
    orders = []
    products = []
    users = []

    try:
        for d in db.collection("orders").stream():
            row = d.to_dict() or {}
            row["id"] = d.id
            orders.append(row)
    except Exception:
        orders = []

    try:
        for d in db.collection("products").stream():
            row = d.to_dict() or {}
            row["id"] = d.id
            products.append(row)
    except Exception:
        products = []

    try:
        for d in db.collection("users").stream():
            row = d.to_dict() or {}
            row["id"] = d.id
            users.append(row)
    except Exception:
        users = []

    now = datetime.now(timezone.utc)
    revenue_total = sum(float(o.get("total") or 0) for o in orders)
    total_orders = len(orders)
    active_customers = len({o.get("userId") for o in orders if o.get("userId")})
    low_stock_items = 0
    for p in products:
        variants = p.get("variants") or []
        for v in variants:
            stock = int(v.get("stock") or 0)
            if stock <= 5:
                low_stock_items += 1
    if low_stock_items == 0:
        low_stock_items = len([p for p in products if not p.get("isPublished", True)])

    def period_revenue(start_dt, end_dt):
        total = 0.0
        for o in orders:
            created = _as_datetime(o.get("createdAt"))
            if not created:
                continue
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if start_dt <= created < end_dt:
                total += float(o.get("total") or 0)
        return total

    current_start = now - timedelta(days=7)
    prev_start = now - timedelta(days=14)
    current_revenue = period_revenue(current_start, now)
    prev_revenue = period_revenue(prev_start, current_start)
    revenue_change = ((current_revenue - prev_revenue) / prev_revenue * 100.0) if prev_revenue > 0 else 0.0

    current_orders = len(
        [o for o in orders if (_as_datetime(o.get("createdAt")) and current_start <= (_as_datetime(o.get("createdAt")) or now) < now)]
    )
    prev_orders = len(
        [o for o in orders if (_as_datetime(o.get("createdAt")) and prev_start <= (_as_datetime(o.get("createdAt")) or now) < current_start)]
    )
    orders_change = ((current_orders - prev_orders) / prev_orders * 100.0) if prev_orders > 0 else 0.0

    status_counts = {"delivered": 0, "pending": 0, "shipped": 0, "cancelled": 0}
    for o in orders:
        status = str(o.get("status") or "pending").lower()
        if "deliver" in status:
            status_counts["delivered"] += 1
        elif "ship" in status or "transit" in status:
            status_counts["shipped"] += 1
        elif "cancel" in status:
            status_counts["cancelled"] += 1
        else:
            status_counts["pending"] += 1

    total_ord = len(orders)
    delivered_n = status_counts["delivered"]
    cancelled_n = status_counts["cancelled"]
    pipeline_n = status_counts["pending"] + status_counts["shipped"]
    completion_pct = round((delivered_n / total_ord * 100.0), 1) if total_ord else 0.0
    cancel_pct = round((cancelled_n / total_ord * 100.0), 1) if total_ord else 0.0

    fulfillment_daily = []
    for offset in range(6, -1, -1):
        day_start = (now - timedelta(days=offset)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        placed_day = 0
        completed_day = 0
        for o in orders:
            created = _as_datetime(o.get("createdAt"))
            if created:
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                if day_start <= created < day_end:
                    placed_day += 1
        for o in orders:
            st = str(o.get("status") or "pending").lower()
            if "deliver" not in st:
                continue
            ut = _as_datetime(o.get("updatedAt")) or _as_datetime(o.get("createdAt"))
            if ut:
                if ut.tzinfo is None:
                    ut = ut.replace(tzinfo=timezone.utc)
                if day_start <= ut < day_end:
                    completed_day += 1
        fulfillment_daily.append(
            {
                "label": day_start.strftime("%a"),
                "placed": placed_day,
                "completed": completed_day,
            }
        )

    placed_last_7 = sum(int(x.get("placed") or 0) for x in fulfillment_daily)
    completed_last_7 = sum(int(x.get("completed") or 0) for x in fulfillment_daily)

    series = []
    for offset in range(6, -1, -1):
        day_start = (now - timedelta(days=offset)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_total = period_revenue(day_start, day_end)
        series.append({"label": day_start.strftime("%a"), "value": day_total})

    users_by_id = {u.get("id"): u for u in users}
    sorted_orders = sorted(
        orders,
        key=lambda x: _as_datetime(x.get("createdAt")) or datetime(1970, 1, 1, tzinfo=timezone.utc),
        reverse=True,
    )
    recent = []
    for o in sorted_orders[:6]:
        uid = o.get("userId")
        user = users_by_id.get(uid or "", {})
        recent.append(
            _serialize(
                {
                    "id": o.get("id"),
                    "customerName": user.get("name") or "Customer",
                    "date": o.get("createdAt"),
                    "amount": float(o.get("total") or 0),
                    "status": o.get("status") or "pending",
                }
            )
        )

    return jsonify(
        {
            "kpis": {
                "revenue": {"value": revenue_total, "change": revenue_change},
                "orders": {"value": total_orders, "change": orders_change},
                "customers": {"value": active_customers, "change": 0},
                "lowStock": {"value": low_stock_items, "critical": low_stock_items >= 5},
            },
            "revenueSeries": series,
            "fulfillment": status_counts,
            "fulfillmentMetrics": {
                "completionRate": completion_pct,
                "cancellationRate": cancel_pct,
                "activePipeline": pipeline_n,
                "placedLast7": placed_last_7,
                "completedLast7": completed_last_7,
            },
            "fulfillmentDaily": fulfillment_daily,
            "recentOrders": recent,
        }
    )


@bp.get("/admin/categories")
@admin_required_json
def admin_list_categories(decoded):
    db = get_firestore()
    categories = []
    products = []
    try:
        for d in db.collection("products").stream():
            row = d.to_dict() or {}
            row["id"] = d.id
            products.append(row)
    except Exception:
        products = []

    counts_by_slug = {}
    for p in products:
        slug = _slugify(str(p.get("category") or ""))
        if not slug:
            continue
        counts_by_slug[slug] = counts_by_slug.get(slug, 0) + 1

    try:
        for d in db.collection("categories").stream():
            row = d.to_dict() or {}
            row["id"] = d.id
            categories.append(row)
    except Exception:
        categories = []

    if not categories and counts_by_slug:
        for slug, count in counts_by_slug.items():
            cid = uuid.uuid4().hex[:14]
            doc = {
                "name": slug.replace("-", " ").title(),
                "slug": slug,
                "status": "active",
                "productCount": count,
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            }
            db.collection("categories").document(cid).set(doc)
            categories.append({"id": cid, **doc})

    shaped = []
    for c in categories:
        slug = _slugify(str(c.get("slug") or c.get("name") or ""))
        shaped.append(
            _serialize(
                {
                    "id": c.get("id"),
                    "name": c.get("name") or slug.replace("-", " ").title(),
                    "slug": slug,
                    "status": c.get("status") or "active",
                    "productCount": counts_by_slug.get(slug, int(c.get("productCount") or 0)),
                    "updatedAt": c.get("updatedAt") or c.get("createdAt"),
                }
            )
        )

    shaped.sort(key=lambda x: str(x.get("name") or ""))
    return jsonify({"categories": shaped})


@bp.post("/admin/categories")
@admin_required_json
def admin_create_category(decoded):
    data = request.get_json(force=True, silent=True) or {}
    name = str(data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    slug = _slugify(str(data.get("slug") or name))
    status = "active" if str(data.get("status") or "active").lower() == "active" else "draft"
    db = get_firestore()
    exists = list(db.collection("categories").where("slug", "==", slug).limit(1).stream())
    if exists:
        return jsonify({"error": "slug already exists"}), 409
    cid = uuid.uuid4().hex[:14]
    doc = {
        "name": name,
        "slug": slug,
        "status": status,
        "productCount": int(data.get("productCount") or 0),
        "createdAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }
    db.collection("categories").document(cid).set(doc)
    return jsonify({"id": cid})


@bp.put("/admin/categories/<category_id>")
@admin_required_json
def admin_update_category(decoded, category_id):
    data = request.get_json(force=True, silent=True) or {}
    db = get_firestore()
    ref = db.collection("categories").document(category_id)
    snap = ref.get()
    if not snap.exists:
        return jsonify({"error": "not found"}), 404
    patch = {}
    if "name" in data:
        patch["name"] = str(data.get("name") or "").strip()
    if "slug" in data:
        patch["slug"] = _slugify(str(data.get("slug") or ""))
    if "status" in data:
        patch["status"] = "active" if str(data.get("status") or "").lower() == "active" else "draft"
    if "productCount" in data:
        patch["productCount"] = int(data.get("productCount") or 0)
    patch["updatedAt"] = firestore.SERVER_TIMESTAMP
    ref.set(patch, merge=True)
    return jsonify({"ok": True})


@bp.delete("/admin/categories/<category_id>")
@admin_required_json
def admin_delete_category(decoded, category_id):
    db = get_firestore()
    ref = db.collection("categories").document(category_id)
    if not ref.get().exists:
        return jsonify({"error": "not found"}), 404
    ref.delete()
    return jsonify({"ok": True})


@bp.get("/admin/inventory")
@admin_required_json
def admin_inventory_data(decoded):
    db = get_firestore()
    products = []
    try:
        for d in db.collection("products").stream():
            row = d.to_dict() or {}
            row["id"] = d.id
            products.append(row)
    except Exception:
        products = []

    rows = []
    asset_value = 0.0
    out_of_stock = 0
    low_stock = 0
    bespoke_orders = len([p for p in products if p.get("isBestseller")])

    for p in products:
        variants = p.get("variants") or []
        if variants:
            units = sum(int(v.get("stock") or 0) for v in variants)
        else:
            units = 0
        price = float(p.get("price") or 0)
        line_value = units * price
        asset_value += line_value

        if units <= 0:
            out_of_stock += 1
            status = "out_of_stock"
        elif units <= 3:
            low_stock += 1
            status = "critical"
        elif units <= 8:
            low_stock += 1
            status = "low_stock"
        else:
            status = "in_stock"

        sku_seed = str(p.get("slug") or p.get("name") or p.get("id") or "SKU").upper().replace("-", "")[:3]
        sku = "ME-" + sku_seed + "-" + str(p.get("id") or "")[:3].upper()
        rows.append(
            {
                "id": p.get("id"),
                "productLine": p.get("name") or "Untitled Product",
                "sku": sku,
                "stock": units,
                "status": status,
                "costValue": line_value,
            }
        )

    rows.sort(key=lambda x: x.get("stock", 0))
    return jsonify(
        {
            "kpis": {
                "assetValuation": asset_value,
                "outOfStockSkus": out_of_stock,
                "lowStockSkus": low_stock,
                "bespokeOrders": bespoke_orders,
            },
            "rows": rows,
        }
    )


@bp.get("/admin/orders")
@admin_required_json
def admin_list_orders(decoded):
    db = get_firestore()
    docs = db.collection("orders").stream()
    orders = []
    user_ids = set()
    for d in docs:
        row = d.to_dict() or {}
        row["id"] = d.id
        uid = row.get("userId")
        if uid:
            user_ids.add(uid)
        orders.append(row)

    users = {}
    for uid in user_ids:
        try:
            snap = db.collection("users").document(uid).get()
            if snap.exists:
                users[uid] = snap.to_dict() or {}
        except Exception:
            users[uid] = {}

    def normalize_status(value):
        text = str(value or "pending").lower()
        if "process" in text:
            return "processing"
        if "payment" in text:
            return "payment_pending"
        if "ready" in text:
            return "ready_to_ship"
        if "ship" in text or "transit" in text:
            return "shipped"
        if "deliver" in text or "confirm" in text:
            return "delivered"
        if "cancel" in text:
            return "cancelled"
        return "pending"

    items = []
    for row in orders:
        uid = row.get("userId")
        user = users.get(uid, {})
        order_status = normalize_status(row.get("status"))
        items.append(
            _serialize(
                {
                    "id": row.get("id"),
                    "orderCode": "ORD-" + str(row.get("id") or "").upper()[:4],
                    "placedAt": row.get("createdAt"),
                    "customer": user.get("name") or "Customer",
                    "lineItems": len(row.get("items") or []),
                    "totalValue": float(row.get("total") or 0),
                    "status": order_status,
                    "gateway": row.get("paymentMethod") or "N/A",
                }
            )
        )

    q = str(request.args.get("q") or "").strip().lower()
    status = str(request.args.get("status") or "all").strip().lower()
    if q:
        items = [
            i
            for i in items
            if q in str(i.get("orderCode") or "").lower()
            or q in str(i.get("customer") or "").lower()
            or q in str(i.get("gateway") or "").lower()
        ]
    if status and status != "all":
        items = [i for i in items if str(i.get("status") or "").lower() == status]

    items.sort(key=lambda x: str(x.get("placedAt") or ""), reverse=True)
    return jsonify({"orders": items})


@bp.put("/admin/orders/<order_id>")
@admin_required_json
def admin_update_order(decoded, order_id):
    data = request.get_json(force=True, silent=True) or {}
    status = str(data.get("status") or "").strip().lower()
    allowed = {"processing", "payment_pending", "ready_to_ship", "shipped", "delivered", "cancelled", "pending"}
    if status not in allowed:
        return jsonify({"error": "invalid status"}), 400
    db = get_firestore()
    ref = db.collection("orders").document(order_id)
    if not ref.get().exists:
        return jsonify({"error": "not found"}), 404
    ref.set({"status": status, "updatedAt": firestore.SERVER_TIMESTAMP}, merge=True)
    return jsonify({"ok": True})


@bp.get("/admin/returns")
@admin_required_json
def admin_list_returns(decoded):
    db = get_firestore()
    docs = db.collection("returns").stream()
    records = []
    user_ids = set()
    for d in docs:
        row = d.to_dict() or {}
        row["id"] = d.id
        if row.get("userId"):
            user_ids.add(row.get("userId"))
        records.append(row)

    users = {}
    for uid in user_ids:
        try:
            snap = db.collection("users").document(uid).get()
            if snap.exists:
                users[uid] = snap.to_dict() or {}
        except Exception:
            users[uid] = {}

    # Fallback demo-style rows if collection is empty
    if not records:
        sample_orders = []
        for d in db.collection("orders").limit(4).stream():
            row = d.to_dict() or {}
            row["id"] = d.id
            sample_orders.append(row)
        reasons = ["Size Mismatch", "Defective Fabric", "Changed Mind", "Different from image"]
        statuses = ["pending_inspection", "approved", "refunded", "rejected"]
        for idx, o in enumerate(sample_orders):
            records.append(
                {
                    "id": f"ret-sample-{idx+1}",
                    "orderId": o.get("id"),
                    "userId": o.get("userId"),
                    "reason": reasons[idx % len(reasons)],
                    "status": statuses[idx % len(statuses)],
                    "refundAmount": float(o.get("total") or 0) * 0.4,
                    "createdAt": o.get("createdAt"),
                }
            )

    def normalize_status(value):
        text = str(value or "pending_inspection").lower()
        if "pending" in text or "inspect" in text:
            return "pending_inspection"
        if "approve" in text:
            return "approved"
        if "refund" in text:
            return "refunded"
        if "reject" in text:
            return "rejected"
        return "pending_inspection"

    rows = []
    pending_count = 0
    refunded_amount = 0.0
    approved_or_refunded = 0
    for r in records:
        st = normalize_status(r.get("status"))
        if st == "pending_inspection":
            pending_count += 1
        if st == "refunded":
            refunded_amount += float(r.get("refundAmount") or 0)
        if st in {"approved", "refunded"}:
            approved_or_refunded += 1
        uid = r.get("userId")
        u = users.get(uid, {})
        rows.append(
            _serialize(
                {
                    "id": r.get("id"),
                    "returnCode": "RET-" + str(r.get("id") or "").upper()[:3],
                    "date": r.get("createdAt"),
                    "acquisitionId": "ORD-" + str(r.get("orderId") or "").upper()[:4],
                    "initiatedBy": u.get("name") or "Client",
                    "justification": r.get("reason") or "N/A",
                    "status": st,
                    "refundAmount": float(r.get("refundAmount") or 0),
                }
            )
        )

    total_rows = len(rows) or 1
    approval_rate = (approved_or_refunded / total_rows) * 100.0
    rows.sort(key=lambda x: str(x.get("date") or ""), reverse=True)
    return jsonify(
        {
            "kpis": {
                "pendingInspection": pending_count,
                "refundedThisMonth": refunded_amount,
                "qualityApprovalRate": approval_rate,
            },
            "returns": rows,
        }
    )


@bp.put("/admin/returns/<return_id>")
@admin_required_json
def admin_update_return(decoded, return_id):
    data = request.get_json(force=True, silent=True) or {}
    status = str(data.get("status") or "").strip().lower()
    allowed = {"pending_inspection", "approved", "refunded", "rejected"}
    if status not in allowed:
        return jsonify({"error": "invalid status"}), 400
    db = get_firestore()
    ref = db.collection("returns").document(return_id)
    if not ref.get().exists:
        return jsonify({"error": "not found"}), 404
    patch = {"status": status, "updatedAt": firestore.SERVER_TIMESTAMP}
    if "refundAmount" in data:
        patch["refundAmount"] = float(data.get("refundAmount") or 0)
    ref.set(patch, merge=True)
    return jsonify({"ok": True})


@bp.get("/admin/customers")
@admin_required_json
def admin_list_customers(decoded):
    db = get_firestore()
    users = []
    orders = []
    try:
        for d in db.collection("users").stream():
            row = d.to_dict() or {}
            row["id"] = d.id
            users.append(row)
    except Exception:
        users = []

    try:
        for d in db.collection("orders").stream():
            row = d.to_dict() or {}
            row["id"] = d.id
            orders.append(row)
    except Exception:
        orders = []

    stats = {}
    for o in orders:
        uid = o.get("userId")
        if not uid:
            continue
        cur = stats.setdefault(uid, {"orders": 0, "spend": 0.0, "memberSince": o.get("createdAt")})
        cur["orders"] += 1
        cur["spend"] += float(o.get("total") or 0)
        created = _as_datetime(o.get("createdAt"))
        existing = _as_datetime(cur.get("memberSince"))
        if created and (not existing or created < existing):
            cur["memberSince"] = created

    def tier_by_spend(spend):
        if spend >= 50000:
            return "private"
        if spend >= 10000:
            return "gold"
        return "signature"

    rows = []
    for u in users:
        uid = u.get("id")
        s = stats.get(uid, {"orders": 0, "spend": 0.0, "memberSince": u.get("createdAt")})
        rows.append(
            _serialize(
                {
                    "id": uid,
                    "name": u.get("name") or "Client",
                    "email": u.get("email") or "",
                    "tier": tier_by_spend(float(s.get("spend") or 0)),
                    "orders": int(s.get("orders") or 0),
                    "totalSpend": float(s.get("spend") or 0),
                    "memberSince": s.get("memberSince") or u.get("createdAt"),
                }
            )
        )

    q = str(request.args.get("q") or "").strip().lower()
    vip_only = str(request.args.get("vipOnly") or "").strip().lower() in {"1", "true", "yes"}
    if q:
        rows = [r for r in rows if q in (str(r.get("name") or "") + " " + str(r.get("email") or "")).lower()]
    if vip_only:
        rows = [r for r in rows if str(r.get("tier")) in {"private", "gold"}]

    rows.sort(key=lambda x: float(x.get("totalSpend") or 0), reverse=True)
    return jsonify({"customers": rows})


@bp.get("/admin/coupons")
@admin_required_json
def admin_list_coupons(decoded):
    db = get_firestore()
    docs = db.collection("coupons").stream()
    coupons = []
    now = datetime.now(timezone.utc)
    for d in docs:
        row = d.to_dict() or {}
        row["id"] = d.id
        expires = _as_datetime(row.get("expiresAt"))
        status = str(row.get("status") or "active").lower()
        if expires and expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if status == "active" and expires and expires < now:
            status = "expired"
        coupons.append(
            _serialize(
                {
                    "id": row.get("id"),
                    "code": str(row.get("code") or "").upper(),
                    "type": row.get("type") or "percentage",
                    "value": float(row.get("value") or 0),
                    "usedCount": int(row.get("usedCount") or 0),
                    "usageLimit": int(row.get("usageLimit") or 0),
                    "expiresAt": row.get("expiresAt"),
                    "status": status,
                }
            )
        )

    coupons.sort(key=lambda x: str(x.get("code") or ""))
    return jsonify({"coupons": coupons})


@bp.post("/admin/coupons")
@admin_required_json
def admin_create_coupon(decoded):
    data = request.get_json(force=True, silent=True) or {}
    code = str(data.get("code") or "").strip().upper()
    if not code:
        return jsonify({"error": "code required"}), 400
    ctype = str(data.get("type") or "percentage").strip().lower()
    if ctype not in {"percentage", "fixed"}:
        return jsonify({"error": "invalid type"}), 400
    value = float(data.get("value") or 0)
    if value <= 0:
        return jsonify({"error": "value must be positive"}), 400
    usage_limit = int(data.get("usageLimit") or 100)
    status = str(data.get("status") or "active").lower()
    if status not in {"active", "scheduled", "expired"}:
        status = "active"
    db = get_firestore()
    existing = list(db.collection("coupons").where("code", "==", code).limit(1).stream())
    if existing:
        return jsonify({"error": "code already exists"}), 409
    cid = uuid.uuid4().hex[:14]
    expires_iso = data.get("expiresAt")
    expires_dt = None
    if expires_iso:
        try:
            expires_dt = datetime.fromisoformat(str(expires_iso).replace("Z", "+00:00"))
        except Exception:
            expires_dt = None
    doc = {
        "code": code,
        "type": ctype,
        "value": value,
        "usedCount": 0,
        "usageLimit": usage_limit,
        "expiresAt": expires_dt or (datetime.now(timezone.utc) + timedelta(days=90)),
        "status": status,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }
    db.collection("coupons").document(cid).set(doc)
    return jsonify({"id": cid})


@bp.put("/admin/coupons/<coupon_id>")
@admin_required_json
def admin_update_coupon(decoded, coupon_id):
    data = request.get_json(force=True, silent=True) or {}
    db = get_firestore()
    ref = db.collection("coupons").document(coupon_id)
    snap = ref.get()
    if not snap.exists:
        return jsonify({"error": "not found"}), 404
    patch = {}
    if "status" in data:
        status = str(data.get("status") or "").lower()
        if status in {"active", "scheduled", "expired"}:
            patch["status"] = status
    if "usageLimit" in data:
        patch["usageLimit"] = int(data.get("usageLimit") or 0)
    if "value" in data:
        patch["value"] = float(data.get("value") or 0)
    if "type" in data:
        ctype = str(data.get("type") or "").lower()
        if ctype in {"percentage", "fixed"}:
            patch["type"] = ctype
    patch["updatedAt"] = firestore.SERVER_TIMESTAMP
    ref.set(patch, merge=True)
    return jsonify({"ok": True})


@bp.delete("/admin/coupons/<coupon_id>")
@admin_required_json
def admin_delete_coupon(decoded, coupon_id):
    db = get_firestore()
    ref = db.collection("coupons").document(coupon_id)
    if not ref.get().exists:
        return jsonify({"error": "not found"}), 404
    ref.delete()
    return jsonify({"ok": True})


@bp.get("/admin/banners")
@admin_required_json
def admin_list_banners(decoded):
    db = get_firestore()
    docs = db.collection("banners").stream()
    rows = []
    for d in docs:
        row = d.to_dict() or {}
        row["id"] = d.id
        rows.append(
            _serialize(
                {
                    "id": row.get("id"),
                    "title": row.get("title") or "Untitled Banner",
                    "subtitle": row.get("subtitle") or "",
                    "placement": row.get("placement") or "home",
                    "status": str(row.get("status") or "draft").lower(),
                    "image": row.get("image") or "",
                    "engagement": float(row.get("engagement") or 0),
                }
            )
        )

    if not rows:
        sample = [
            {
                "title": "Winter Edit 2026",
                "subtitle": "Hero Main - Home Page",
                "placement": "home_hero",
                "status": "live",
                "image": "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?auto=format&fit=crop&w=1200&q=80",
                "engagement": 14.2,
            },
            {
                "title": "Silk Capsule Collection",
                "subtitle": "Mid Section - Home Page",
                "placement": "home_mid",
                "status": "live",
                "image": "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?auto=format&fit=crop&w=1200&q=80",
                "engagement": 4.8,
            },
            {
                "title": "Archival Accessories",
                "subtitle": "Category Top - Listing Page",
                "placement": "category_top",
                "status": "draft",
                "image": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=1200&q=80",
                "engagement": 0,
            },
            {
                "title": "Member Early Access",
                "subtitle": "Overlay - Carousel",
                "placement": "overlay",
                "status": "scheduled",
                "image": "https://images.unsplash.com/photo-1585487000143-ef1f9a6be3e2?auto=format&fit=crop&w=1200&q=80",
                "engagement": 0,
            },
        ]
        for item in sample:
            bid = uuid.uuid4().hex[:14]
            doc = {
                **item,
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            }
            db.collection("banners").document(bid).set(doc)
            rows.append({"id": bid, **item})

    rows.sort(key=lambda x: float(x.get("engagement") or 0), reverse=True)
    return jsonify({"banners": rows})


@bp.post("/admin/banners")
@admin_required_json
def admin_create_banner(decoded):
    data = request.get_json(force=True, silent=True) or {}
    title = str(data.get("title") or "").strip()
    image = str(data.get("image") or "").strip()
    if not title or not image:
        return jsonify({"error": "title and image required"}), 400
    status = str(data.get("status") or "draft").lower()
    if status not in {"live", "draft", "scheduled"}:
        status = "draft"
    doc = {
        "title": title,
        "subtitle": str(data.get("subtitle") or "").strip(),
        "placement": str(data.get("placement") or "home").strip(),
        "status": status,
        "image": image,
        "engagement": float(data.get("engagement") or 0),
        "createdAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }
    db = get_firestore()
    bid = uuid.uuid4().hex[:14]
    db.collection("banners").document(bid).set(doc)
    return jsonify({"id": bid})


@bp.put("/admin/banners/<banner_id>")
@admin_required_json
def admin_update_banner(decoded, banner_id):
    data = request.get_json(force=True, silent=True) or {}
    db = get_firestore()
    ref = db.collection("banners").document(banner_id)
    if not ref.get().exists:
        return jsonify({"error": "not found"}), 404
    patch = {}
    for key in {"title", "subtitle", "placement", "image"}:
        if key in data:
            patch[key] = str(data.get(key) or "").strip()
    if "status" in data:
        status = str(data.get("status") or "").lower()
        if status in {"live", "draft", "scheduled"}:
            patch["status"] = status
    if "engagement" in data:
        patch["engagement"] = float(data.get("engagement") or 0)
    patch["updatedAt"] = firestore.SERVER_TIMESTAMP
    ref.set(patch, merge=True)
    return jsonify({"ok": True})


@bp.delete("/admin/banners/<banner_id>")
@admin_required_json
def admin_delete_banner(decoded, banner_id):
    db = get_firestore()
    ref = db.collection("banners").document(banner_id)
    if not ref.get().exists:
        return jsonify({"error": "not found"}), 404
    ref.delete()
    return jsonify({"ok": True})


@bp.get("/admin/reviews")
@admin_required_json
def admin_list_reviews(decoded):
    db = get_firestore()
    docs = db.collection("reviews").stream()
    reviews = []
    user_ids = set()
    for d in docs:
        row = d.to_dict() or {}
        row["id"] = d.id
        uid = row.get("userId")
        if uid:
            user_ids.add(uid)
        reviews.append(row)

    users = {}
    for uid in user_ids:
        try:
            snap = db.collection("users").document(uid).get()
            if snap.exists:
                users[uid] = snap.to_dict() or {}
        except Exception:
            users[uid] = {}

    def normalize_status(value):
        text = str(value or "pending").lower()
        if "approve" in text:
            return "approved"
        if "escal" in text:
            return "escalated"
        if "reject" in text:
            return "rejected"
        return "pending"

    rows = []
    for r in reviews:
        uid = r.get("userId")
        u = users.get(uid, {})
        rows.append(
            _serialize(
                {
                    "id": r.get("id"),
                    "name": u.get("name") or r.get("name") or "",
                    "email": u.get("email") or r.get("email") or "",
                    "productName": r.get("productName") or "",
                    "rating": int(r.get("rating") or 0),
                    "comment": r.get("comment") or "",
                    "status": normalize_status(r.get("status")),
                    "createdAt": r.get("createdAt"),
                }
            )
        )
    rows.sort(key=lambda x: str(x.get("createdAt") or ""), reverse=True)
    return jsonify({"reviews": rows})


@bp.put("/admin/reviews/<review_id>")
@admin_required_json
def admin_update_review(decoded, review_id):
    data = request.get_json(force=True, silent=True) or {}
    status = str(data.get("status") or "").strip().lower()
    allowed = {"approved", "pending", "escalated", "rejected"}
    if status not in allowed:
        return jsonify({"error": "invalid status"}), 400
    db = get_firestore()
    ref = db.collection("reviews").document(review_id)
    if not ref.get().exists:
        return jsonify({"error": "not found"}), 404
    patch = {"status": status, "updatedAt": firestore.SERVER_TIMESTAMP}
    if "comment" in data:
        patch["comment"] = str(data.get("comment") or "").strip()
    ref.set(patch, merge=True)
    return jsonify({"ok": True})


@bp.delete("/admin/reviews/<review_id>")
@admin_required_json
def admin_delete_review(decoded, review_id):
    db = get_firestore()
    ref = db.collection("reviews").document(review_id)
    if not ref.get().exists:
        return jsonify({"error": "not found"}), 404
    ref.delete()
    return jsonify({"ok": True})


@bp.get("/admin/notifications")
@admin_required_json
def admin_list_notifications(decoded):
    db = get_firestore()
    docs = db.collection("admin_notifications").stream()
    rows = []

    for d in docs:
        row = d.to_dict() or {}
        row["id"] = d.id
        rows.append(row)

    def normalize_status(value):
        text = str(value or "live").strip().lower()
        if text in {"live", "paused", "draft", "scheduled", "archived"}:
            return text
        return "live"

    payload = []
    for r in rows:
        reach = int(r.get("reach") or 0)
        opened = int(r.get("openedCount") or 0)
        open_rate = float(r.get("openRate") or 0)
        if not open_rate and reach > 0:
            open_rate = (opened / reach) * 100
        payload.append(
            _serialize(
                {
                    "id": r.get("id"),
                    "title": str(r.get("title") or "").strip(),
                    "message": str(r.get("message") or "").strip(),
                    "segment": str(r.get("segment") or "").strip(),
                    "reach": reach,
                    "status": normalize_status(r.get("status")),
                    "medium": str(r.get("medium") or "").strip(),
                    "openRate": round(open_rate, 2),
                    "scheduledAt": r.get("scheduledAt"),
                    "createdAt": r.get("createdAt"),
                }
            )
        )

    payload.sort(key=lambda x: str(x.get("createdAt") or ""), reverse=True)

    total_reach = sum(int(x.get("reach") or 0) for x in payload)
    live_campaigns = sum(1 for x in payload if x.get("status") == "live")
    avg_open_rate = 0.0
    if payload:
        avg_open_rate = round(sum(float(x.get("openRate") or 0) for x in payload) / len(payload), 2)

    return jsonify(
        {
            "kpis": {
                "totalReach": total_reach,
                "activeCampaigns": live_campaigns,
                "avgOpenRate": avg_open_rate,
            },
            "notifications": payload,
        }
    )


@bp.post("/admin/notifications")
@admin_required_json
def admin_create_notification(decoded):
    data = request.get_json(force=True, silent=True) or {}
    title = str(data.get("title") or "").strip()
    message = str(data.get("message") or "").strip()
    if not title or not message:
        return jsonify({"error": "title and message are required"}), 400

    oid = uuid.uuid4().hex[:14]
    status = str(data.get("status") or "live").strip().lower()
    if status not in {"live", "paused", "draft", "scheduled", "archived"}:
        status = "live"

    doc = {
        "title": title,
        "message": message,
        "segment": str(data.get("segment") or "All App Users").strip(),
        "reach": int(data.get("reach") or 0),
        "openedCount": int(data.get("openedCount") or 0),
        "openRate": float(data.get("openRate") or 0),
        "medium": str(data.get("medium") or "global_in-app").strip(),
        "status": status,
        "scheduledAt": data.get("scheduledAt") or None,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }
    db = get_firestore()
    db.collection("admin_notifications").document(oid).set(doc)
    return jsonify({"id": oid})


@bp.put("/admin/notifications/<notification_id>")
@admin_required_json
def admin_update_notification(decoded, notification_id):
    data = request.get_json(force=True, silent=True) or {}
    db = get_firestore()
    ref = db.collection("admin_notifications").document(notification_id)
    if not ref.get().exists:
        return jsonify({"error": "not found"}), 404

    patch = {"updatedAt": firestore.SERVER_TIMESTAMP}
    if "status" in data:
        status = str(data.get("status") or "").strip().lower()
        if status not in {"live", "paused", "draft", "scheduled", "archived"}:
            return jsonify({"error": "invalid status"}), 400
        patch["status"] = status
    if "title" in data:
        patch["title"] = str(data.get("title") or "").strip()
    if "message" in data:
        patch["message"] = str(data.get("message") or "").strip()
    if "segment" in data:
        patch["segment"] = str(data.get("segment") or "").strip()
    if "medium" in data:
        patch["medium"] = str(data.get("medium") or "").strip()
    if "reach" in data:
        patch["reach"] = int(data.get("reach") or 0)
    if "openRate" in data:
        patch["openRate"] = float(data.get("openRate") or 0)
    if "openedCount" in data:
        patch["openedCount"] = int(data.get("openedCount") or 0)

    ref.set(patch, merge=True)
    return jsonify({"ok": True})


@bp.delete("/admin/notifications/<notification_id>")
@admin_required_json
def admin_delete_notification(decoded, notification_id):
    db = get_firestore()
    ref = db.collection("admin_notifications").document(notification_id)
    if not ref.get().exists:
        return jsonify({"error": "not found"}), 404
    ref.delete()
    return jsonify({"ok": True})


def _treasury_gateway_meta():
    cfg = current_app.config
    db = get_firestore()
    try:
        snap = db.collection("settings").document("treasury").get()
        if snap.exists:
            data = snap.to_dict() or {}
            return {
                "connected": bool(data.get("gatewayConnected", False)),
                "label": str(data.get("gatewayLabel") or "").strip(),
            }
    except Exception:
        pass
    key_ok = bool(cfg.get("RAZORPAY_KEY_ID") and cfg.get("RAZORPAY_KEY_SECRET"))
    return {
        "connected": key_ok,
        "label": "RAZORPAY CONNECTED" if key_ok else "GATEWAY OFFLINE",
    }


@bp.get("/admin/treasury")
@admin_required_json
def admin_treasury(decoded):
    db = get_firestore()
    seen_ids = set()
    rows_raw = []
    for coll_name in ("admin_transactions", "transactions"):
        try:
            for d in db.collection(coll_name).stream():
                if d.id in seen_ids:
                    continue
                seen_ids.add(d.id)
                row = d.to_dict() or {}
                row["id"] = d.id
                row["_collection"] = coll_name
                rows_raw.append(row)
        except Exception:
            continue

    def norm_status(v):
        s = str(v or "processing").strip().lower()
        if s in {"succeeded", "processing", "refunded", "failed"}:
            return s
        if "success" in s:
            return "succeeded"
        if "refund" in s:
            return "refunded"
        return "processing"

    def row_amount(r):
        for k in ("amountInr", "amount_inr", "amount", "value", "total"):
            if k in r and r.get(k) is not None:
                try:
                    return float(r.get(k))
                except (TypeError, ValueError):
                    continue
        return 0.0

    def row_settlement_status(r):
        for k in ("settlementStatus", "settlement_status", "status", "paymentStatus"):
            if r.get(k) is not None:
                return r.get(k)
        return ""

    settled = 0.0
    pending = 0.0
    succeeded_charge_count = 0
    settled_positive_total = 0.0
    dispute_count = 0
    positive_charge_rows = 0

    for r in rows_raw:
        amt = row_amount(r)
        st = norm_status(row_settlement_status(r))
        if amt > 0:
            positive_charge_rows += 1
        if st == "succeeded" and amt > 0:
            settled += amt
            settled_positive_total += amt
            succeeded_charge_count += 1
        elif st == "processing" and amt > 0:
            pending += amt
        if r.get("isDispute"):
            dispute_count += 1

    avg_sale = round(settled_positive_total / succeeded_charge_count, 2) if succeeded_charge_count else 0.0
    dispute_rate = round((dispute_count / max(1, positive_charge_rows)) * 100, 4) if rows_raw else 0.0

    payload = []
    for r in rows_raw:
        amt = row_amount(r)
        st = norm_status(row_settlement_status(r))
        ref_trace = (
            str(r.get("referenceTrace") or r.get("reference_trace") or r.get("referenceId") or "").strip()
            or f"#{r.get('id')}"
        )
        payload.append(
            _serialize(
                {
                    "id": r.get("id"),
                    "referenceTrace": ref_trace,
                    "amountInr": amt,
                    "gatewayType": str(
                        r.get("gatewayType") or r.get("gateway_type") or ""
                    ).strip().lower(),
                    "gatewayDisplay": str(
                        r.get("gatewayDisplay") or r.get("gateway_display") or r.get("gateway") or ""
                    ).strip(),
                    "settlementStatus": st,
                    "acquisitionId": str(
                        r.get("acquisitionId") or r.get("acquisition_id") or r.get("orderId") or ""
                    ).strip(),
                    "createdAt": r.get("createdAt")
                    or r.get("created_at")
                    or r.get("timestamp"),
                }
            )
        )

    payload.sort(key=lambda x: str(x.get("createdAt") or ""), reverse=True)

    gateway = _treasury_gateway_meta()
    body = {
        "kpis": {
            "settledFunds": round(settled, 2),
            "pendingPayouts": round(pending, 2),
            "disputeRate": dispute_rate,
            "avgSaleValue": avg_sale,
        },
        "gateway": gateway,
        "transactions": payload,
    }

    if request.args.get("format") == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            [
                "reference_trace",
                "amount_inr",
                "gateway",
                "settlement_status",
                "acquisition_id",
                "created_at",
            ]
        )
        for t in payload:
            writer.writerow(
                [
                    t.get("referenceTrace") or "",
                    t.get("amountInr") or 0,
                    t.get("gatewayDisplay") or "",
                    t.get("settlementStatus") or "",
                    t.get("acquisitionId") or "",
                    str(t.get("createdAt") or ""),
                ]
            )
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=treasury-ledger.csv"},
        )

    return jsonify(body)


@bp.post("/admin/treasury/payout-request")
@admin_required_json
def admin_treasury_payout_request(decoded):
    data = request.get_json(force=True, silent=True) or {}
    note = str(data.get("note") or "").strip()
    amount = data.get("amountInr")
    try:
        amount_val = float(amount) if amount is not None else None
    except (TypeError, ValueError):
        amount_val = None
    pid = uuid.uuid4().hex[:16]
    db = get_firestore()
    db.collection("payout_requests").document(pid).set(
        {
            "requestedByUid": decoded.get("uid"),
            "amountInr": amount_val,
            "note": note,
            "status": "pending",
            "createdAt": firestore.SERVER_TIMESTAMP,
        }
    )
    return jsonify({"id": pid})


def _staff_telemetry_display(row):
    txt = row.get("lastTelemetry") or row.get("telemetry")
    if txt is not None and str(txt).strip():
        return str(txt).strip()
    ts = row.get("lastActiveAt")
    if ts is None:
        return ""
    try:
        if isinstance(ts, datetime):
            dt = ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
        elif hasattr(ts, "timestamp"):
            dt = datetime.fromtimestamp(ts.timestamp(), tz=timezone.utc)
        else:
            return ""
        delta = datetime.now(timezone.utc) - dt
        secs = max(0, int(delta.total_seconds()))
        if secs < 120:
            return "ACTIVE NOW"
        if secs < 3600:
            return str(max(1, secs // 60)) + "M AGO"
        if secs < 86400:
            return str(max(1, secs // 3600)) + "H AGO"
        return str(max(1, secs // 86400)) + "D AGO"
    except Exception:
        return ""


def _staff_normalize_status(v):
    s = str(v or "offline").strip().lower()
    if s in {"online", "offline", "away"}:
        return s
    return "offline"


def _staff_clearance_tag_class(level):
    text = str(level or "").upper()
    if "SUPER" in text and "ADMIN" in text:
        return "admin-staff-tag--super"
    return "admin-staff-tag--standard"


def _staff_status_dot_class(status):
    s = _staff_normalize_status(status)
    if s == "online":
        return "admin-staff-dot--online"
    if s == "away":
        return "admin-staff-dot--away"
    return "admin-staff-dot--offline"


@bp.get("/admin/staff")
@admin_required_json
def admin_list_staff(decoded):
    db = get_firestore()
    rows_out = []
    try:
        for d in db.collection("staff").stream():
            row = d.to_dict() or {}
            row["id"] = d.id
            clearance = str(row.get("clearanceLevel") or row.get("clearance") or row.get("role") or "").strip()
            telemetry = _staff_telemetry_display(row)
            rows_out.append(
                _serialize(
                    {
                        "id": row["id"],
                        "name": str(row.get("name") or "").strip(),
                        "email": str(row.get("email") or "").strip(),
                        "clearanceLevel": clearance,
                        "clearanceTagClass": _staff_clearance_tag_class(clearance),
                        "status": _staff_normalize_status(row.get("status")),
                        "statusDotClass": _staff_status_dot_class(row.get("status")),
                        "lastTelemetry": telemetry,
                        "isActive": bool(row.get("isActive", True)),
                        "createdAt": row.get("createdAt"),
                        "updatedAt": row.get("updatedAt"),
                    }
                )
            )
    except Exception as exc:
        current_app.logger.exception("admin staff list failed: %s", exc)
        rows_out = []

    rows_out.sort(key=lambda x: (not x.get("isActive", True), str(x.get("name") or "").lower()))
    active_seats = sum(1 for x in rows_out if x.get("isActive", True))
    return jsonify({"staff": rows_out, "activeSeats": active_seats})


@bp.post("/admin/staff")
@admin_required_json
def admin_create_staff(decoded):
    data = request.get_json(force=True, silent=True) or {}
    name = str(data.get("name") or "").strip()
    email = str(data.get("email") or "").strip().lower()
    clearance = str(data.get("clearanceLevel") or data.get("clearance") or "").strip()
    if not name or not email:
        return jsonify({"error": "name and email required"}), 400
    sid = uuid.uuid4().hex[:12]
    db = get_firestore()
    db.collection("staff").document(sid).set(
        {
            "name": name,
            "email": email,
            "clearanceLevel": clearance or "STAFF",
            "status": _staff_normalize_status(data.get("status")),
            "lastTelemetry": str(data.get("lastTelemetry") or "").strip() or "—",
            "isActive": bool(data.get("isActive", True)),
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
    )
    return jsonify({"id": sid})


@bp.put("/admin/staff/<staff_id>")
@admin_required_json
def admin_update_staff(decoded, staff_id):
    data = request.get_json(force=True, silent=True) or {}
    db = get_firestore()
    ref = db.collection("staff").document(staff_id)
    if not ref.get().exists:
        return jsonify({"error": "not found"}), 404
    patch = {"updatedAt": firestore.SERVER_TIMESTAMP}
    if "name" in data:
        patch["name"] = str(data.get("name") or "").strip()
    if "email" in data:
        patch["email"] = str(data.get("email") or "").strip().lower()
    if "clearanceLevel" in data or "clearance" in data:
        patch["clearanceLevel"] = str(
            data.get("clearanceLevel") or data.get("clearance") or ""
        ).strip()
    if "status" in data:
        patch["status"] = _staff_normalize_status(data.get("status"))
    if "lastTelemetry" in data:
        patch["lastTelemetry"] = str(data.get("lastTelemetry") or "").strip()
    if "isActive" in data:
        patch["isActive"] = bool(data.get("isActive"))
    ref.set(patch, merge=True)
    return jsonify({"ok": True})


@bp.delete("/admin/staff/<staff_id>")
@admin_required_json
def admin_delete_staff(decoded, staff_id):
    db = get_firestore()
    ref = db.collection("staff").document(staff_id)
    if not ref.get().exists:
        return jsonify({"error": "not found"}), 404
    ref.delete()
    return jsonify({"ok": True})


_SYS_SETTINGS_DOC = "system_parameters"


@bp.get("/admin/system-settings")
@admin_required_json
def admin_get_system_settings(decoded):
    db = get_firestore()
    remote = {}
    try:
        snap = db.collection("settings").document(_SYS_SETTINGS_DOC).get()
        if snap.exists:
            remote = snap.to_dict() or {}
    except Exception as exc:
        current_app.logger.exception("system-settings read: %s", exc)
        remote = {}
    merged = merge_system_settings(remote)
    return jsonify(_serialize(merged))


@bp.put("/admin/system-settings")
@admin_required_json
def admin_put_system_settings(decoded):
    data = request.get_json(force=True, silent=True) or {}
    cats = data.get("categories")
    active_id = data.get("activeCategoryId")
    if not isinstance(cats, list):
        return jsonify({"error": "categories array required"}), 400
    baseline = merge_system_settings({})
    incoming_by_id = {str(c.get("id")): c for c in cats if c.get("id")}
    sanitized = []
    for base_cat in baseline["categories"]:
        cid = base_cat["id"]
        cat = incoming_by_id.get(cid, {})
        fields_out = []
        remote_fields = {f.get("key"): f for f in cat.get("fields") or [] if f.get("key")}
        for bf in base_cat["fields"]:
            key = bf.get("key")
            rf = remote_fields.get(key, {})
            ft = bf.get("type")
            raw_val = rf.get("value", bf.get("value"))
            if ft == "boolean":
                val = bool(raw_val)
            elif ft == "number":
                try:
                    val = int(raw_val)
                except (TypeError, ValueError):
                    try:
                        val = float(raw_val)
                    except (TypeError, ValueError):
                        val = bf.get("value") if bf.get("value") is not None else 0
            else:
                val = raw_val if raw_val is not None else ""
                val = str(val)
            nf = {**bf, "value": val}
            if isinstance(rf.get("options"), list):
                nf["options"] = rf["options"]
            fields_out.append(nf)
        sanitized.append(
            {
                **base_cat,
                "title": str(cat.get("title") or base_cat["title"]).strip(),
                "description": str(cat.get("description") or base_cat["description"]).strip(),
                "panelTitle": str(cat.get("panelTitle") or base_cat.get("panelTitle") or "").strip()
                or base_cat.get("panelTitle"),
                "icon": str(cat.get("icon") or base_cat.get("icon") or "").strip()
                or base_cat.get("icon"),
                "fields": fields_out,
            }
        )
    allowed_ids = {c["id"] for c in baseline["categories"]}
    payload = {"categories": sanitized}
    if active_id and str(active_id) in allowed_ids:
        payload["activeCategoryId"] = str(active_id)
    merged_remote = merge_system_settings(payload)
    db = get_firestore()
    db.collection("settings").document(_SYS_SETTINGS_DOC).set(
        {
            **merged_remote,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "updatedByUid": decoded.get("uid"),
        },
        merge=False,
    )
    return jsonify({"ok": True, "settings": _serialize(merged_remote)})


@bp.post("/orders")
@login_required_json
def create_order(decoded):
    data = request.get_json(force=True, silent=True) or {}
    uid = decoded["uid"]
    items = data.get("items") or []
    if not items:
        return jsonify({"error": "items required"}), 400
    payment_method = data.get("paymentMethod", "COD")
    payment_status = data.get("paymentStatus", "pending")
    subtotal = float(data.get("subtotal", 0))
    shipping = float(data.get("shipping", 0))
    tax = float(data.get("tax", 0))
    total = float(data.get("total", subtotal + shipping + tax))
    oid = uuid.uuid4().hex[:16]
    db = get_firestore()
    order = {
        "userId": uid,
        "items": items,
        "status": "confirmed" if payment_status == "paid" else "pending",
        "shippingAddress": data.get("shippingAddress") or {},
        "billingAddress": data.get("billingAddress") or {},
        "paymentMethod": payment_method,
        "paymentId": data.get("paymentId") or "",
        "paymentStatus": payment_status,
        "subtotal": subtotal,
        "discount": float(data.get("discount") or 0),
        "shipping": shipping,
        "tax": tax,
        "total": total,
        "trackingNumber": "",
        "courier": "",
        "createdAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }
    db.collection("orders").document(oid).set(order)
    return jsonify({"orderId": oid})


@bp.get("/orders")
@login_required_json
def list_my_orders(decoded):
    uid = decoded["uid"]
    db = get_firestore()
    docs = db.collection("orders").where("userId", "==", uid).stream()
    orders = []
    for d in docs:
        row = d.to_dict() or {}
        row["id"] = d.id
        orders.append(_serialize(row))
    orders.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
    return jsonify({"orders": orders})


@bp.get("/orders/<order_id>")
@login_required_json
def get_my_order(decoded, order_id):
    uid = decoded["uid"]
    db = get_firestore()
    doc = db.collection("orders").document(order_id).get()
    if not doc.exists:
        return jsonify({"error": "Order not found"}), 404
    row = doc.to_dict() or {}
    if row.get("userId") != uid:
        return jsonify({"error": "Forbidden"}), 403
    row["id"] = doc.id
    return jsonify(_serialize(row))


@bp.get("/addresses")
@login_required_json
def list_addresses(decoded):
    uid = decoded["uid"]
    db = get_firestore()
    docs = db.collection("users").document(uid).collection("addresses").stream()
    addresses = []
    for d in docs:
        row = d.to_dict() or {}
        row["id"] = d.id
        addresses.append(_serialize(row))
    addresses.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
    return jsonify({"addresses": addresses})


@bp.post("/addresses")
@login_required_json
def create_address(decoded):
    uid = decoded["uid"]
    data = request.get_json(force=True, silent=True) or {}
    required = ["label", "name", "line1", "city", "state", "pincode", "country"]
    for key in required:
        if not str(data.get(key, "")).strip():
            return jsonify({"error": f"missing {key}"}), 400
    db = get_firestore()
    aid = uuid.uuid4().hex[:14]
    doc = {
        "label": data.get("label"),
        "name": data.get("name"),
        "line1": data.get("line1"),
        "line2": data.get("line2", ""),
        "city": data.get("city"),
        "state": data.get("state"),
        "pincode": data.get("pincode"),
        "country": data.get("country"),
        "phone": data.get("phone", ""),
        "isDefault": bool(data.get("isDefault")),
        "createdAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }
    ref = db.collection("users").document(uid).collection("addresses").document(aid)
    ref.set(doc)
    return jsonify({"id": aid})


@bp.put("/addresses/<address_id>")
@login_required_json
def update_address(decoded, address_id):
    uid = decoded["uid"]
    data = request.get_json(force=True, silent=True) or {}
    allowed = {
        "label",
        "name",
        "line1",
        "line2",
        "city",
        "state",
        "pincode",
        "country",
        "phone",
        "isDefault",
    }
    patch = {k: v for k, v in data.items() if k in allowed}
    if not patch:
        return jsonify({"error": "No editable fields provided"}), 400
    patch["updatedAt"] = firestore.SERVER_TIMESTAMP
    db = get_firestore()
    ref = db.collection("users").document(uid).collection("addresses").document(address_id)
    if not ref.get().exists:
        return jsonify({"error": "Address not found"}), 404
    ref.set(patch, merge=True)
    return jsonify({"ok": True})


@bp.delete("/addresses/<address_id>")
@login_required_json
def delete_address(decoded, address_id):
    uid = decoded["uid"]
    db = get_firestore()
    ref = db.collection("users").document(uid).collection("addresses").document(address_id)
    if not ref.get().exists:
        return jsonify({"error": "Address not found"}), 404
    ref.delete()
    return jsonify({"ok": True})


@bp.post("/payments/razorpay/create-order")
@login_required_json
def razorpay_create_order(decoded):
    cfg = current_app.config
    key_id = cfg.get("RAZORPAY_KEY_ID") or ""
    key_secret = cfg.get("RAZORPAY_KEY_SECRET") or ""
    if not key_id or not key_secret:
        return jsonify({"error": "Razorpay not configured on server"}), 503
    data = request.get_json(force=True, silent=True) or {}
    amount_paise = int(data.get("amountPaise", 0))
    currency = data.get("currency", "INR")
    if amount_paise < 100:
        return jsonify({"error": "invalid amount"}), 400
    client = razorpay.Client(auth=(key_id, key_secret))
    receipt = data.get("receipt") or f"rcpt_{uuid.uuid4().hex[:10]}"
    order = client.order.create({"amount": amount_paise, "currency": currency, "receipt": receipt})
    return jsonify({"orderId": order["id"], "amount": order["amount"], "currency": order["currency"], "keyId": key_id})


@bp.post("/payments/razorpay/verify")
@login_required_json
def razorpay_verify(decoded):
    cfg = current_app.config
    key_secret = cfg.get("RAZORPAY_KEY_SECRET") or ""
    data = request.get_json(force=True, silent=True) or {}
    order_id = data.get("razorpay_order_id")
    payment_id = data.get("razorpay_payment_id")
    signature = data.get("razorpay_signature")
    if not all([order_id, payment_id, signature, key_secret]):
        return jsonify({"error": "missing fields"}), 400
    message = f"{order_id}|{payment_id}".encode()
    expected = hmac.new(key_secret.encode(), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return jsonify({"ok": False, "error": "invalid signature"}), 400
    return jsonify({"ok": True})


@bp.post("/webhooks/razorpay")
def razorpay_webhook():
    cfg = current_app.config
    secret = cfg.get("RAZORPAY_WEBHOOK_SECRET") or ""
    body = request.get_data()
    sig = request.headers.get("X-Razorpay-Signature", "")
    if secret:
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            return jsonify({"error": "bad signature"}), 400
    payload = json.loads(body.decode() or "{}")
    event = payload.get("event")
    payment_entity = (payload.get("payload") or {}).get("payment") or {}
    entity = payment_entity.get("entity") or {}
    payment_id = entity.get("id")
    order_id = entity.get("order_id")
    if event == "payment.captured" and order_id:
        db = get_firestore()
        q = db.collection("orders").where("paymentId", "==", payment_id).limit(1).stream()
        for _ in q:
            break
        else:
            pass
    return jsonify({"received": True})
