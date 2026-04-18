"""Default System Parameters schema (merged with Firestore `settings/system_parameters`)."""

from copy import deepcopy


def _field(key, label, ftype, value, **extra):
    row = {"key": key, "label": label, "type": ftype, "value": value}
    row.update(extra)
    return row


SYSTEM_SETTINGS_DEFAULT = {
    "activeCategoryId": "general",
    "categories": [
        {
            "id": "general",
            "title": "GENERAL CONFIGURATION",
            "description": "Store identity and global locale settings.",
            "icon": "general",
            "panelTitle": "General Control Matrix",
            "fields": [
                _field(
                    "marketplaceIdentity",
                    "MARKETPLACE IDENTITY",
                    "text",
                    "Maher Executive Luxury Fashion",
                ),
                _field(
                    "primaryLocale",
                    "PRIMARY LOCALE",
                    "select",
                    "IN (INR)",
                    options=["GLOBAL (USD)", "IN (INR)", "EU (EUR)", "UK (GBP)"],
                ),
                _field(
                    "brandManifesto",
                    "BRAND MANIFESTO (DESCRIPTION)",
                    "textarea",
                    "Redefining modern luxury through intentional design and artisanal integrity.",
                ),
                _field(
                    "productionMode",
                    "PRODUCTION MODE",
                    "boolean",
                    True,
                    help="TOGGLING THIS WILL AFFECT LIVE API ENDPOINTS.",
                ),
            ],
        },
        {
            "id": "visuals",
            "title": "VISUALS CONFIGURATION",
            "description": "Brand colors, typography and theme selection.",
            "icon": "visuals",
            "panelTitle": "Visual Control Matrix",
            "fields": [
                _field("primaryAccentHex", "PRIMARY ACCENT (HEX)", "text", "#C9A96E"),
                _field(
                    "themeMode",
                    "THEME MODE",
                    "select",
                    "Dark Luxury",
                    options=["Dark Luxury", "Midnight Editorial", "Minimal Light"],
                ),
                _field(
                    "displayFontStack",
                    "DISPLAY TYPOGRAPHY",
                    "text",
                    "Playfair Display, serif",
                ),
            ],
        },
        {
            "id": "security",
            "title": "SECURITY CONFIGURATION",
            "description": "API authentication and access protocols.",
            "icon": "security",
            "panelTitle": "Security Control Matrix",
            "fields": [
                _field("sessionTimeoutMinutes", "SESSION TIMEOUT (MIN)", "number", 45),
                _field("requireMfaForAdmin", "REQUIRE MFA FOR ADMIN", "boolean", False),
                _field(
                    "apiRateLimitPerMinute",
                    "API RATE LIMIT / MIN",
                    "number",
                    120,
                ),
            ],
        },
        {
            "id": "integration",
            "title": "INTEGRATION CONFIGURATION",
            "description": "Third-party services and ERP connectivity.",
            "icon": "integration",
            "panelTitle": "Integration Control Matrix",
            "fields": [
                _field("erpWebhookUrl", "ERP WEBHOOK URL", "text", ""),
                _field(
                    "paymentGatewayMode",
                    "PAYMENT GATEWAY MODE",
                    "select",
                    "Razorpay",
                    options=["Razorpay", "Stripe", "Sandbox"],
                ),
                _field("cloudinaryFolder", "CLOUDINARY FOLDER KEY", "text", "clothesecommerce"),
            ],
        },
        {
            "id": "alerts",
            "title": "ALERTS CONFIGURATION",
            "description": "System log notifications and SMTP.",
            "icon": "alerts",
            "panelTitle": "Alerts Control Matrix",
            "fields": [
                _field("smtpRelayHost", "SMTP RELAY HOST", "text", ""),
                _field("operationsAlertEmail", "OPERATIONS ALERT EMAIL", "text", ""),
                _field(
                    "notifyOnFailedPayments",
                    "NOTIFY ON FAILED PAYMENTS",
                    "boolean",
                    True,
                ),
            ],
        },
        {
            "id": "localization",
            "title": "LOCALIZATION CONFIGURATION",
            "description": "Currency matrix and shipping zones.",
            "icon": "localization",
            "panelTitle": "Localization Control Matrix",
            "fields": [
                _field("defaultCurrencyCode", "DEFAULT CURRENCY", "text", "INR"),
                _field(
                    "shippingZonesNote",
                    "SHIPPING ZONES MATRIX",
                    "textarea",
                    "Metro: 24–48h. Tier-2: 3–5 business days. International on request.",
                ),
                _field(
                    "taxDisplayMode",
                    "TAX DISPLAY MODE",
                    "select",
                    "Inclusive",
                    options=["Inclusive", "Exclusive"],
                ),
            ],
        },
    ],
}


def _merge_fields(default_fields, remote_fields):
    by_key = {f.get("key"): f for f in (remote_fields or []) if f.get("key")}
    out = []
    for df in default_fields:
        k = df.get("key")
        if k in by_key:
            rf = by_key[k]
            merged = {**df, **rf}
            if "value" in rf:
                merged["value"] = rf["value"]
            if "options" in rf:
                merged["options"] = rf["options"]
            out.append(merged)
        else:
            out.append(deepcopy(df))
    return out


def merge_system_settings(remote):
    """Merge Firestore document onto defaults so schema stays complete."""
    base = deepcopy(SYSTEM_SETTINGS_DEFAULT)
    if not remote or not isinstance(remote, dict):
        return base
    if remote.get("activeCategoryId"):
        base["activeCategoryId"] = str(remote["activeCategoryId"])

    default_by_id = {c["id"]: c for c in base["categories"]}
    remote_cats = remote.get("categories") or []
    remote_by_id = {c["id"]: c for c in remote_cats if c.get("id")}

    merged_list = []
    for cid, d_cat in default_by_id.items():
        if cid in remote_by_id:
            rc = remote_by_id[cid]
            mc = deepcopy(d_cat)
            if rc.get("title"):
                mc["title"] = rc["title"]
            if rc.get("description"):
                mc["description"] = rc["description"]
            if rc.get("panelTitle"):
                mc["panelTitle"] = rc["panelTitle"]
            if rc.get("icon"):
                mc["icon"] = rc["icon"]
            mc["fields"] = _merge_fields(d_cat["fields"], rc.get("fields"))
            merged_list.append(mc)
        else:
            merged_list.append(deepcopy(d_cat))

    for cid, rc in remote_by_id.items():
        if cid not in default_by_id:
            merged_list.append(deepcopy(rc))

    order = [c["id"] for c in SYSTEM_SETTINGS_DEFAULT["categories"]]
    merged_list.sort(key=lambda c: order.index(c["id"]) if c["id"] in order else 99)
    base["categories"] = merged_list
    return base
