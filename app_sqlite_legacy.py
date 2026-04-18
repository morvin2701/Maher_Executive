import json
import os
import sqlite3
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "me_luxury_kids.db")

COUNTRY_CONFIG = {
    "in": {
        "label": "India",
        "currency": "INR",
        "symbol": "₹",
        "free_shipping_threshold": 2999,
        "payment_methods": ["COD", "UPI", "Card", "Net Banking"],
    },
    "us": {
        "label": "USA",
        "currency": "USD",
        "symbol": "$",
        "free_shipping_threshold": 120,
        "payment_methods": ["Card", "PayPal"],
    },
}

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key-before-production"


@app.template_filter("from_json")
def from_json_filter(value):
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            collection TEXT NOT NULL,
            description TEXT NOT NULL,
            sku TEXT NOT NULL UNIQUE,
            stock INTEGER NOT NULL DEFAULT 0,
            sizes_json TEXT NOT NULL,
            image_url TEXT NOT NULL,
            price_inr REAL NOT NULL,
            price_usd REAL NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            country TEXT NOT NULL,
            total_amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            shipping_cost REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'confirmed',
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )

    cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@mekids.com",))
    if not cursor.fetchone():
        cursor.execute(
            """
            INSERT INTO users (full_name, email, password_hash, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "ME Admin",
                "admin@mekids.com",
                generate_password_hash("Admin@123"),
                1,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        seed_products = [
            (
                "Royal Wedding Kurta Set",
                "royal-wedding-kurta-set",
                "Royal Collection",
                "Hand-finished kurta set designed for wedding ceremonies with premium woven texture.",
                "ME-RYL-001",
                15,
                json.dumps(["2-3Y", "4-5Y", "6-7Y", "8-9Y"]),
                "https://images.unsplash.com/photo-1516257984-b1b4d707412e?auto=format&fit=crop&w=1000&q=80",
                5899,
                179,
                1,
                datetime.now(timezone.utc).isoformat(),
            ),
            (
                "ME Street Signature Hoodie",
                "me-street-signature-hoodie",
                "ME Street",
                "Minimal luxury hoodie with structured silhouette and soft premium cotton blend.",
                "ME-STR-014",
                24,
                json.dumps(["3-4Y", "5-6Y", "7-8Y", "9-10Y"]),
                "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=1000&q=80",
                3499,
                110,
                1,
                datetime.now(timezone.utc).isoformat(),
            ),
            (
                "Festive Gold Layer Dress",
                "festive-gold-layer-dress",
                "Royal Collection",
                "Premium festive dress with delicate layers and luxury gold detailing for statement occasions.",
                "ME-RYL-029",
                11,
                json.dumps(["2-3Y", "4-5Y", "6-7Y"]),
                "https://images.unsplash.com/photo-1469334031218-e382a71b716b?auto=format&fit=crop&w=1000&q=80",
                4699,
                145,
                1,
                datetime.now(timezone.utc).isoformat(),
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO products
            (name, slug, collection, description, sku, stock, sizes_json, image_url, price_inr, price_usd, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            seed_products,
        )

    db.commit()
    db.close()


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Admin login required.", "warning")
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)

    return wrapper


def format_price(product, country):
    if country == "in":
        return product["price_inr"]
    return product["price_usd"]


def cart_totals(country):
    cart = session.get("cart", {})
    db = get_db()
    subtotal = 0
    lines = []
    for product_id, qty in cart.items():
        product = db.execute(
            "SELECT * FROM products WHERE id = ? AND is_active = 1", (int(product_id),)
        ).fetchone()
        if not product:
            continue
        unit_price = format_price(product, country)
        line_total = unit_price * qty
        subtotal += line_total
        lines.append(
            {
                "product": product,
                "qty": qty,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

    config = COUNTRY_CONFIG[country]
    shipping = 0 if subtotal >= config["free_shipping_threshold"] else (99 if country == "in" else 9)
    total = subtotal + shipping
    return lines, subtotal, shipping, total


@app.context_processor
def inject_globals():
    return {
        "selected_country": session.get("country"),
        "country_config": COUNTRY_CONFIG,
        "auth_user": current_user(),
        "cart_count": sum(session.get("cart", {}).values()),
    }


@app.get("/")
def landing():
    return render_template("index.html")


@app.post("/set-country")
def set_country():
    country = request.form.get("country")
    if country not in COUNTRY_CONFIG:
        flash("Invalid country selection.", "danger")
        return redirect(url_for("landing"))
    session["country"] = country
    return redirect(url_for("country_store", country=country))


@app.get("/<country>/")
def country_store(country):
    if country not in COUNTRY_CONFIG:
        return redirect(url_for("landing"))
    session["country"] = country
    db = get_db()
    products = db.execute(
        "SELECT * FROM products WHERE is_active = 1 ORDER BY created_at DESC"
    ).fetchall()
    return render_template("storefront.html", products=products, country=country)


@app.get("/<country>/product/<int:product_id>")
def product_detail(country, product_id):
    if country not in COUNTRY_CONFIG:
        return redirect(url_for("landing"))
    db = get_db()
    product = db.execute(
        "SELECT * FROM products WHERE id = ? AND is_active = 1", (product_id,)
    ).fetchone()
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("country_store", country=country))
    return render_template("product.html", product=product, country=country)


@app.post("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    country = session.get("country", "in")
    qty = int(request.form.get("qty", 1))
    qty = max(1, min(10, qty))
    cart = session.get("cart", {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + qty
    session["cart"] = cart
    flash("Added to cart.", "success")
    return redirect(request.referrer or url_for("country_store", country=country))


@app.post("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    flash("Removed from cart.", "info")
    return redirect(url_for("cart_view"))


@app.get("/cart")
def cart_view():
    country = session.get("country", "in")
    lines, subtotal, shipping, total = cart_totals(country)
    return render_template(
        "cart.html",
        country=country,
        lines=lines,
        subtotal=subtotal,
        shipping=shipping,
        total=total,
    )


@app.post("/checkout")
@login_required
def checkout():
    country = session.get("country", "in")
    payment_method = request.form.get("payment_method")
    if payment_method not in COUNTRY_CONFIG[country]["payment_methods"]:
        flash("Invalid payment method.", "danger")
        return redirect(url_for("cart_view"))
    lines, subtotal, shipping, total = cart_totals(country)
    if not lines:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart_view"))
    db = get_db()
    db.execute(
        """
        INSERT INTO orders (user_id, country, total_amount, payment_method, shipping_cost, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            session["user_id"],
            country,
            total,
            payment_method,
            shipping,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    db.commit()
    session["cart"] = {}
    flash("Order placed successfully.", "success")
    return redirect(url_for("country_store", country=country))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(full_name) < 2 or "@" not in email or len(password) < 6:
            flash("Enter valid details.", "danger")
            return redirect(url_for("register"))
        db = get_db()
        try:
            db.execute(
                """
                INSERT INTO users (full_name, email, password_hash, is_admin, created_at)
                VALUES (?, ?, ?, 0, ?)
                """,
                (full_name, email, generate_password_hash(password), datetime.now(timezone.utc).isoformat()),
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("Email already registered.", "warning")
            return redirect(url_for("register"))
        flash("Account created. Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            flash("Welcome back.", "success")
            country = session.get("country", "in")
            return redirect(url_for("country_store", country=country))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")


@app.get("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out.", "info")
    return redirect(url_for("landing"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        db = get_db()
        admin = db.execute(
            "SELECT * FROM users WHERE email = ? AND is_admin = 1", (email,)
        ).fetchone()
        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["id"]
            flash("Admin signed in.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.", "danger")
    return render_template("admin_login.html")


@app.get("/admin/logout")
def admin_logout():
    session.pop("admin_id", None)
    flash("Admin logged out.", "info")
    return redirect(url_for("landing"))


@app.get("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    products = db.execute("SELECT * FROM products ORDER BY created_at DESC").fetchall()
    orders = db.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 10").fetchall()
    return render_template("admin_dashboard.html", products=products, orders=orders)


@app.route("/admin/product/new", methods=["GET", "POST"])
@admin_required
def admin_product_new():
    if request.method == "POST":
        return save_product()
    return render_template("admin_product_form.html", product=None)


@app.route("/admin/product/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_product_edit(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        return save_product(product_id)
    return render_template("admin_product_form.html", product=product)


@app.post("/admin/product/<int:product_id>/delete")
@admin_required
def admin_product_delete(product_id):
    db = get_db()
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    flash("Product deleted.", "info")
    return redirect(url_for("admin_dashboard"))


def save_product(product_id=None):
    db = get_db()
    name = request.form.get("name", "").strip()
    slug = request.form.get("slug", "").strip()
    collection = request.form.get("collection", "").strip()
    description = request.form.get("description", "").strip()
    sku = request.form.get("sku", "").strip()
    stock = int(request.form.get("stock", 0))
    sizes = request.form.get("sizes", "").strip()
    image_url = request.form.get("image_url", "").strip()
    price_inr = float(request.form.get("price_inr", 0))
    price_usd = float(request.form.get("price_usd", 0))
    is_active = 1 if request.form.get("is_active") == "on" else 0

    if not all([name, slug, collection, description, sku, sizes, image_url]):
        flash("Please fill all required fields.", "danger")
        return redirect(request.url)

    sizes_json = json.dumps([s.strip() for s in sizes.split(",") if s.strip()])

    try:
        if product_id is None:
            db.execute(
                """
                INSERT INTO products
                (name, slug, collection, description, sku, stock, sizes_json, image_url, price_inr, price_usd, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    slug,
                    collection,
                    description,
                    sku,
                    stock,
                    sizes_json,
                    image_url,
                    price_inr,
                    price_usd,
                    is_active,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        else:
            db.execute(
                """
                UPDATE products
                SET name=?, slug=?, collection=?, description=?, sku=?, stock=?, sizes_json=?,
                    image_url=?, price_inr=?, price_usd=?, is_active=?
                WHERE id=?
                """,
                (
                    name,
                    slug,
                    collection,
                    description,
                    sku,
                    stock,
                    sizes_json,
                    image_url,
                    price_inr,
                    price_usd,
                    is_active,
                    product_id,
                ),
            )
        db.commit()
    except sqlite3.IntegrityError:
        flash("Slug or SKU already exists.", "warning")
        return redirect(request.url)

    flash("Product saved.", "success")
    return redirect(url_for("admin_dashboard"))


@app.get("/api/config/<country>")
def country_config_api(country):
    if country not in COUNTRY_CONFIG:
        return jsonify({"error": "invalid country"}), 404
    return jsonify(COUNTRY_CONFIG[country])


@app.get("/sitemap.xml")
def sitemap():
    db = get_db()
    products = db.execute("SELECT id FROM products WHERE is_active = 1").fetchall()
    return render_template("sitemap.xml", products=products)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
