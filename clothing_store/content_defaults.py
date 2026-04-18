CONTENT_DEFAULTS = {
    "home": {
        "title": "Elegance Noire: The Winter Edit",
        "subtitle": "High-fashion silhouettes with sculpted tailoring, restrained palettes, and artisanal precision.",
        "highlights": [
            "Collections built with premium material behavior",
            "Campaign-level visuals with editorial composition",
            "Craft-first design language inspired by global luxury houses",
        ],
        "hero": {
            "eyebrow": "MAHER EXECUTIVE SIGNATURE EDIT",
            "headline": "ÉLÉGANCE NOIRE:\nTHE WINTER EDIT",
            "description": "A directional capsule where quiet luxury meets modern proportion. Crafted to look timeless in every frame.",
            "primaryCtaText": "Shop The Collection",
            "primaryCtaLink": "/shop",
            "secondaryCtaText": "Explore Lookbook",
            "secondaryCtaLink": "/about",
        },
        "curation": {
            "eyebrow": "Discovery",
            "title": "Shop By Curation",
            "viewAllText": "View All Categories",
            "items": [
                {
                    "name": "Ready-to-Wear",
                    "pieces": 124,
                    "image": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=1200&q=80",
                    "link": "/shop?category=women",
                },
                {
                    "name": "Leather Goods",
                    "pieces": 45,
                    "image": "https://images.unsplash.com/photo-1551232864-3f0890e580d9?auto=format&fit=crop&w=1200&q=80",
                    "link": "/shop?category=accessories",
                },
                {
                    "name": "Accessories",
                    "pieces": 89,
                    "image": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=1200&q=80",
                    "link": "/shop?category=accessories",
                },
                {
                    "name": "Footwear",
                    "pieces": 67,
                    "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=1200&q=80",
                    "link": "/shop?category=footwear",
                },
            ],
        },
        "arrivals": {
            "title": "New Arrivals",
            "subtitle": "Fresh seasonal drops curated for top-tier wardrobe building.",
        },
        "heritage": {
            "eyebrow": "Heritage",
            "title": "Crafted For The",
            "accent": "Uncompromising",
            "description": "Maher Executive was founded on a singular principle: luxury must be felt, not just seen. Every stitch, fiber, and finish is obsessively considered to ensure longevity and elevated form.",
            "ctaText": "Our Craftsmanship",
            "ctaLink": "/about",
            "image": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=1600&q=80",
        },
        "homeFooter": {
            "brandTitle": "Maher Executive",
            "brandText": "Defining the future of high-fashion through minimal design and artisanal excellence.",
            "columns": [
                {
                    "title": "Collections",
                    "links": ["Ready-to-Wear", "Accessories", "Footwear", "Exclusives"],
                },
                {
                    "title": "Client Service",
                    "links": ["Shipping & Returns", "FAQ", "Size Guide", "Contact Us"],
                },
            ],
            "newsletterTitle": "Newsletter",
            "newsletterText": "Join for exclusive early access and luxury insights.",
        },
    },
    "shop": {
        "title": "Shop Collection",
        "subtitle": "Curated menswear and womenswear designed for modern premium wardrobes.",
        "highlights": [
            "Filter by category, size, and fit profile",
            "Cloudinary-backed high-resolution media",
            "Live inventory from Firestore products",
        ],
    },
    "women_section": {
        "title": "Ready-to-Wear",
        "subtitle": "Showing exquisite pieces",
        "highlights": [
            "Editorial women collection with seasonal curation",
            "Interactive filtering across style, size, color, and price",
            "Wishlist and cart interactions stored locally and ready for sync",
        ],
        "filters": {
            "categories": ["Ready-to-Wear", "Leather Goods", "Accessories", "Footwear"],
            "sizes": ["XS", "S", "M", "L", "XL", "OS"],
            "colors": ["Black", "White", "Beige", "Gold", "Silver"],
            "prices": ["Under ₹5,000", "₹5,000 - ₹10,000", "₹10,000 - ₹20,000", "Over ₹20,000"],
        },
    },
    "men_section": {
        "title": "Menswear Selection",
        "subtitle": "Showing precision-crafted essentials",
        "highlights": [
            "Premium menswear collection with modern tailoring",
            "Interactive filtering across category, size, color, and price",
            "Wishlist and bag actions fully functional for fast shopping",
        ],
        "filters": {
            "categories": ["Ready-to-Wear", "Outerwear", "Knitwear", "Footwear"],
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "colors": ["Black", "White", "Navy", "Olive", "Brown"],
            "prices": ["Under ₹5,000", "₹5,000 - ₹10,000", "₹10,000 - ₹20,000", "Over ₹20,000"],
        },
    },
    "kids_section": {
        "title": "Little Luxuries",
        "subtitle": "Showing playful, premium pieces for young wardrobes",
        "highlights": [
            "Kids collection with the same editorial quality as adult lines",
            "Filter by category, size, color, and price tier",
            "Cart and wishlist work the same as Women and Men",
        ],
        "filters": {
            "categories": ["Ready-to-Wear", "Outerwear", "Accessories", "Footwear"],
            "sizes": ["2Y", "4Y", "6Y", "8Y", "10Y", "12Y", "14Y"],
            "colors": ["Pink", "Blue", "Ivory", "Navy", "Mint", "Beige"],
            "prices": ["Under ₹5,000", "₹5,000 - ₹10,000", "₹10,000 - ₹20,000", "Over ₹20,000"],
        },
    },
    "search": {
        "title": "Search",
        "subtitle": "Find exact pieces by style, category, and product name.",
        "highlights": [
            "Fast keyword lookup across the catalog",
            "Popular searches and suggestions",
            "Fallback recommendations for no-results",
        ],
    },
    "product": {
        "title": "Product Detail",
        "subtitle": "Complete fashion metadata with editorial imagery and premium descriptions.",
        "highlights": [
            "High-resolution gallery and pricing intelligence",
            "Cloudinary media optimized for storefront",
            "Structured data for SEO-ready PDP",
        ],
    },
    "cart": {
        "title": "Shopping Bag",
        "subtitle": "Review items, pricing, and delivery before secure checkout.",
        "highlights": [
            "Persistent client cart state",
            "Smart subtotal and shipping estimate",
            "Fast transition into checkout flow",
        ],
    },
    "wishlist": {
        "title": "Wishlist",
        "subtitle": "Save and revisit premium items before purchase.",
        "highlights": [
            "User-specific saved product collection",
            "Quick move-to-cart actions",
            "Firestore-powered persistence",
        ],
    },
    "checkout": {
        "title": "Checkout",
        "subtitle": "Structured three-step checkout with reliable order creation.",
        "highlights": [
            "Delivery details capture",
            "Payment method handling (Razorpay/COD)",
            "Order document created in Firestore",
        ],
    },
    "order_confirmation": {
        "title": "Order Confirmation",
        "subtitle": "Clear post-purchase summary and next steps.",
        "highlights": [
            "Reference order ID for tracking",
            "Direct links to order history",
            "Ready for notification automation",
        ],
    },
    "auth": {
        "title": "Authentication",
        "subtitle": "Secure login and signup via Firebase email/password and Google.",
        "highlights": [
            "Role-aware redirect after session sync",
            "Google popup plus redirect fallback",
            "Firestore user document bootstrap",
        ],
    },
    "account_profile": {
        "title": "My Profile",
        "subtitle": "Manage account identity and personal profile settings.",
        "highlights": [
            "Cloudinary-ready avatar references",
            "User document updates in Firestore",
            "Account security controls",
        ],
    },
    "account_orders": {
        "title": "My Orders",
        "subtitle": "Track all purchase history with timeline-ready statuses.",
        "highlights": [
            "Newest-first order listing",
            "Status and payment visibility",
            "Expandable order details",
        ],
    },
    "account_order_detail": {
        "title": "Order Detail",
        "subtitle": "A complete view of purchased items, shipping, and status.",
        "highlights": [
            "Timeline-based order progression",
            "Courier and tracking integration ready",
            "Return and support entry points",
        ],
    },
    "account_addresses": {
        "title": "Saved Addresses",
        "subtitle": "Store and manage reusable shipping and billing addresses.",
        "highlights": [
            "Multiple address profiles",
            "Default address preferences",
            "Firestore subcollection support",
        ],
    },
    "account_returns": {
        "title": "Returns and Refunds",
        "subtitle": "Request and monitor return workflows with clear statuses.",
        "highlights": [
            "Reason and item-level request flow",
            "Status updates from requested to refunded",
            "Admin approval integration",
        ],
    },
    "size_guide": {
        "title": "Size Guide",
        "subtitle": "Measurement references tailored for premium fit confidence.",
        "highlights": [
            "Category-based sizing tables",
            "Unit conversion support",
            "Visual measurement instructions",
        ],
    },
    "help": {
        "title": "Help Center",
        "subtitle": "Answers for shipping, orders, payments, and account support.",
        "highlights": [
            "Category-based FAQs",
            "Quick issue discovery",
            "Escalation to direct support",
        ],
    },
    "contact": {
        "title": "Contact Us",
        "subtitle": "Reach the support team for order, product, or account help.",
        "highlights": [
            "Structured contact form intake",
            "Email and phone support channels",
            "Ready for Cloud Function notification triggers",
        ],
    },
    "about": {
        "title": "About ME Clothing",
        "subtitle": "A premium fashion brand focused on clean confidence and crafted detail.",
        "highlights": [
            "Editorial identity and values",
            "Material and craftsmanship standards",
            "Long-term global expansion vision",
        ],
    },
    "privacy_policy": {
        "title": "Privacy Policy",
        "subtitle": "How user data is handled, protected, and processed.",
        "highlights": [
            "Data collection and usage practices",
            "Retention and security principles",
            "User rights and support channels",
        ],
    },
    "terms": {
        "title": "Terms and Conditions",
        "subtitle": "Usage rules and purchase terms for this platform.",
        "highlights": [
            "Order and payment terms",
            "User obligations and restrictions",
            "Liability and dispute framework",
        ],
    },
    "shipping_policy": {
        "title": "Shipping Policy",
        "subtitle": "Delivery methods, timelines, and region-based shipping rules.",
        "highlights": [
            "Standard and express options",
            "Threshold-based free shipping logic",
            "Operational coverage details",
        ],
    },
    "return_policy": {
        "title": "Return Policy",
        "subtitle": "Guidelines for eligibility, timelines, and refund processing.",
        "highlights": [
            "Return window and criteria",
            "Inspection and approval stages",
            "Refund method clarification",
        ],
    },
    "admin_dashboard": {
        "title": "Admin Dashboard",
        "subtitle": "Top-level operational visibility across sales, orders, and stock.",
        "highlights": [
            "KPI snapshot and trend widgets",
            "Low-stock and order-action priorities",
            "Quick access to core admin workflows",
        ],
    },
    "admin_products": {
        "title": "Products Management",
        "subtitle": "Create, update, publish, and monitor the full product catalog.",
        "highlights": [
            "Cloudinary media-backed product records",
            "Firestore CRUD with role checks",
            "Catalog quality and visibility control",
        ],
    },
    "admin_product_form": {
        "title": "New Masterpiece",
        "subtitle": "Registry of an exquisite new piece for the catalog.",
        "highlights": [],
    },
    "admin_categories": {
        "title": "Categories",
        "subtitle": "Maintain category architecture and storefront navigation structure.",
        "highlights": [
            "Hierarchical category model",
            "Visibility and sort controls",
            "Consistency across search and listing pages",
        ],
    },
    "admin_inventory": {
        "title": "Inventory",
        "subtitle": "Track variant-level stock and prevent unavailable purchases.",
        "highlights": [
            "SKU and variant stock monitoring",
            "Low-stock operational alerts",
            "Replenishment planning support",
        ],
    },
    "admin_orders": {
        "title": "Orders",
        "subtitle": "Operational order management with lifecycle status controls.",
        "highlights": [
            "Filter by status, method, and customer",
            "Update shipping and fulfillment state",
            "Issue operational actions from one table",
        ],
    },
    "admin_order_detail": {
        "title": "Order Operations",
        "subtitle": "Granular order record for support, logistics, and payment actions.",
        "highlights": [
            "Complete address and item audit trail",
            "Tracking and courier metadata",
            "Refund and support action history",
        ],
    },
    "admin_returns": {
        "title": "Returns Management",
        "subtitle": "Evaluate and process customer return requests with consistency.",
        "highlights": [
            "Reason-based review and decisioning",
            "Status transitions and notes",
            "Refund coordination pipeline",
        ],
    },
    "admin_customers": {
        "title": "Customers",
        "subtitle": "View customer profiles, purchase behavior, and support context.",
        "highlights": [
            "Account status and activity visibility",
            "Order and spend context for support",
            "Customer segmentation-ready structure",
        ],
    },
    "admin_coupons": {
        "title": "Coupons and Discounts",
        "subtitle": "Control campaign codes and discount rules from one panel.",
        "highlights": [
            "Flat/percent discount strategies",
            "Validity and usage limit controls",
            "Campaign performance-ready structure",
        ],
    },
    "admin_banners": {
        "title": "Banners and Content",
        "subtitle": "Manage homepage and campaign visuals with Cloudinary assets.",
        "highlights": [
            "Position-aware banner records",
            "Date-based activation control",
            "Storefront messaging consistency",
        ],
    },
    "admin_reviews": {
        "title": "Reviews Moderation",
        "subtitle": "Approve and curate customer feedback for trust and quality.",
        "highlights": [
            "Rating and content review controls",
            "Approval and rejection workflow",
            "Brand-safe public review quality",
        ],
    },
    "admin_notifications": {
        "title": "Notifications and Emails",
        "subtitle": "Manage user communications and campaign messaging.",
        "highlights": [
            "Segmented broadcast capability",
            "Triggered communication logs",
            "Operational and marketing announcements",
        ],
    },
    "admin_payments": {
        "title": "Treasury",
        "subtitle": "Monitor financial health and transaction processing.",
        "highlights": [
            "Encrypted transaction ledger from Firestore",
            "Settlement KPIs computed live from gateway data",
            "Export financials and payout request workflow",
        ],
    },
    "admin_staff": {
        "title": "Operational Core",
        "subtitle": "Manage administrative privileges and access control.",
        "highlights": [
            "Provision seats and clearance levels from Firestore",
            "Live status telemetry and security actions",
            "Role-based accountability aligned with Firebase staff records",
        ],
    },
    "admin_settings": {
        "title": "System Parameters",
        "subtitle": "Manage the technical foundation of the Maher Executive platform.",
        "highlights": [
            "Category navigation and matrices loaded from Firestore",
            "Persist all changes with validation and revision timestamps",
            "Schema-driven fields — extend categories without code changes",
        ],
    },
}
