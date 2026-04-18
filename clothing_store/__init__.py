import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template

from clothing_store.api import bp as api_bp
from clothing_store.config import Config
from clothing_store.content_service import get_page_content
from clothing_store.firebase_init import init_firebase


def create_app():
    load_dotenv()
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    app = Flask(
        __name__,
        template_folder=os.path.join(base, "templates"),
        static_folder=os.path.join(base, "static"),
    )
    app.config.from_object(Config)

    init_firebase(app)
    app.register_blueprint(api_bp)

    def render_with_content(template_name, page_key, **kwargs):
        return render_template(
            template_name,
            page_content=get_page_content(page_key),
            page_key=page_key,
            **kwargs,
        )

    @app.context_processor
    def inject_client_config():
        cfg = app.config
        return {
            "firebase_web": {
                "apiKey": cfg["FIREBASE_API_KEY"],
                "authDomain": cfg["FIREBASE_AUTH_DOMAIN"],
                "projectId": cfg["FIREBASE_PROJECT_ID"],
                "storageBucket": cfg["FIREBASE_STORAGE_BUCKET"],
                "messagingSenderId": cfg["FIREBASE_MESSAGING_SENDER_ID"],
                "appId": cfg["FIREBASE_APP_ID"],
            },
            "cloudinary_client": {
                "cloudName": cfg["CLOUDINARY_CLOUD_NAME"],
                "uploadPreset": cfg["CLOUDINARY_UPLOAD_PRESET"],
                "folder": cfg["CLOUDINARY_FOLDER"],
            },
        }

    # ——— User pages ———
    @app.get("/")
    def page_home():
        return render_with_content("home.html", "home")

    @app.get("/shop")
    def page_shop():
        return redirect("/")

    @app.get("/women")
    def page_women():
        return render_with_content("women.html", "women_section")

    @app.get("/men")
    def page_men():
        return render_with_content("men.html", "men_section")

    @app.get("/search")
    def page_search():
        return render_with_content("search.html", "search")

    @app.get("/product/<slug>")
    def page_product(slug):
        return render_with_content("product.html", "product", slug=slug)

    @app.get("/cart")
    def page_cart():
        return render_with_content("cart.html", "cart")

    @app.get("/wishlist")
    def page_wishlist():
        return render_with_content("wishlist.html", "wishlist")

    @app.get("/checkout")
    def page_checkout():
        return render_with_content("checkout.html", "checkout")

    @app.get("/order-confirmation/<order_id>")
    def page_order_confirmation(order_id):
        return render_with_content(
            "order_confirmation.html", "order_confirmation", order_id=order_id
        )

    @app.get("/auth")
    def page_auth():
        return render_with_content("auth.html", "auth")

    @app.get("/account/profile")
    def page_account_profile():
        return render_with_content("account_profile.html", "account_profile")

    @app.get("/account/orders")
    def page_account_orders():
        return render_with_content("account_orders.html", "account_orders")

    @app.get("/account/orders/<order_id>")
    def page_account_order_detail(order_id):
        return render_with_content(
            "account_order_detail.html", "account_order_detail", order_id=order_id
        )

    @app.get("/account/addresses")
    def page_account_addresses():
        return render_with_content("account_addresses.html", "account_addresses")

    @app.get("/account/returns")
    def page_account_returns():
        return render_with_content("account_returns.html", "account_returns")

    @app.get("/size-guide")
    def page_size_guide():
        return render_with_content("size_guide.html", "size_guide")

    @app.get("/help")
    def page_help():
        return render_with_content("help.html", "help")

    @app.get("/contact")
    def page_contact():
        return render_with_content("contact.html", "contact")

    @app.get("/about")
    def page_about():
        return render_with_content("about.html", "about")

    @app.get("/privacy-policy")
    def page_privacy():
        return render_with_content("privacy_policy.html", "privacy_policy")

    @app.get("/terms")
    def page_terms():
        return render_with_content("terms.html", "terms")

    @app.get("/shipping-policy")
    def page_shipping_policy():
        return render_with_content("shipping_policy.html", "shipping_policy")

    @app.get("/return-policy")
    def page_return_policy():
        return render_with_content("return_policy.html", "return_policy")

    # ——— Admin ———
    @app.get("/admin")
    def admin_home():
        return render_with_content("admin/dashboard.html", "admin_dashboard")

    @app.get("/admin/products")
    def admin_products():
        return render_with_content("admin/products.html", "admin_products")

    @app.get("/admin/products/new")
    def admin_products_new():
        return render_with_content("admin/product_form.html", "admin_product_form", product_id=None)

    @app.get("/admin/products/<product_id>/edit")
    def admin_products_edit(product_id):
        return render_with_content(
            "admin/product_form.html", "admin_product_form", product_id=product_id
        )

    @app.get("/admin/categories")
    def admin_categories():
        return render_with_content("admin/categories.html", "admin_categories")

    @app.get("/admin/inventory")
    def admin_inventory():
        return render_with_content("admin/inventory.html", "admin_inventory")

    @app.get("/admin/orders")
    def admin_orders():
        return render_with_content("admin/orders.html", "admin_orders")

    @app.get("/admin/orders/<order_id>")
    def admin_order_detail(order_id):
        return render_with_content(
            "admin/order_detail.html", "admin_order_detail", order_id=order_id
        )

    @app.get("/admin/returns")
    def admin_returns():
        return render_with_content("admin/returns.html", "admin_returns")

    @app.get("/admin/customers")
    def admin_customers():
        return render_with_content("admin/customers.html", "admin_customers")

    @app.get("/admin/coupons")
    def admin_coupons():
        return render_with_content("admin/coupons.html", "admin_coupons")

    @app.get("/admin/banners")
    def admin_banners():
        return render_with_content("admin/banners.html", "admin_banners")

    @app.get("/admin/reviews")
    def admin_reviews():
        return render_with_content("admin/reviews.html", "admin_reviews")

    @app.get("/admin/notifications")
    def admin_notifications():
        return render_with_content("admin/notifications.html", "admin_notifications")

    @app.get("/admin/payments")
    def admin_payments():
        return render_with_content("admin/payments.html", "admin_payments")

    @app.get("/admin/staff")
    def admin_staff():
        return render_with_content("admin/staff.html", "admin_staff")

    @app.get("/admin/settings")
    def admin_settings():
        return render_with_content("admin/settings.html", "admin_settings")

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_err(_e):
        return render_template("errors/500.html"), 500

    return app
