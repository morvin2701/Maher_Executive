# ME Clothing — Python + HTML/CSS/JS + Firebase + Cloudinary

Premium e-commerce stack:

- **Frontend:** HTML (Jinja2 templates), CSS, JavaScript (no React requirement for the main app).
- **Backend:** Python **Flask** with **Firebase Admin SDK** (Firestore writes that bypass security rules for trusted server logic).
- **Auth & database:** **Firebase Authentication** + **Cloud Firestore** (real-time data from the browser where rules allow).
- **Images:** **Cloudinary** for product media (configure cloud name, upload preset, and folder in `.env`). **Firebase Storage is not used.**

The previous SQLite demo is preserved as `app_sqlite_legacy.py`. A `node_modules/` directory may exist if npm packages were installed locally; it is gitignored and not required to run the Flask app.

## Quick start

1. **Python 3.11+** recommended.

2. Clone the repo and create a virtualenv:

```bash
git clone <your-repo-url>
cd ECommerce_Vikas
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in:

   - **Firebase Web SDK** keys (Firebase Console → Project settings → Your apps → Web).
   - **Service account JSON** path as `GOOGLE_APPLICATION_CREDENTIALS` (Project settings → Service accounts → Generate new private key). **Keep this file out of git** (see `.gitignore`). Required for the Flask API and seed scripts.

4. **Deploy Firestore rules** from `firestore.rules` in the Firebase console (Firestore → Rules).

5. **Seed sample data** (optional):

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/serviceAccount.json"
python scripts/seed_firestore.py
```

6. **Seed premium page content** (recommended):

```bash
python scripts/seed_site_content.py
```

This writes default content for all major pages to Firestore collection `content_pages`.

7. **Grant admin** (pick one):

   - In Firestore, open `users/{yourAuthUid}` and set `role` to `"admin"`, **or**
   - Set `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD` (and optional `BOOTSTRAP_ADMIN_NAME`) in `.env`, then run:
     `python scripts/bootstrap_admin.py`

8. Run the app:

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Cloudinary

- Configure `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_UPLOAD_PRESET`, and `CLOUDINARY_FOLDER` in `.env`.
- Admin product form (`/admin/products/new`) opens the Cloudinary widget; returned HTTPS URLs are stored in Firestore under `products.images`.

Optional script `scripts/seed_cloudinary_firestore.py` uploads a **local** image: set `SEED_LOCAL_IMAGE_PATH` in `.env` to a file on disk.

## Pushing to GitHub (security)

- **Never commit** `.env`, Firebase **service account JSON** (`*-firebase-adminsdk-*.json`), or other secrets. They are listed in `.gitignore`.
- If a secret was ever committed, remove it from git history and **rotate** keys in Firebase / Razorpay / Cloudinary.
- Copy only from **`.env.example`** when sharing; use placeholders for all real keys.

## Razorpay

- Set `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and `RAZORPAY_WEBHOOK_SECRET`.
- API routes: `/api/payments/razorpay/create-order`, `/api/payments/razorpay/verify`, `/api/webhooks/razorpay`.
- Checkout demo uses **COD** without Razorpay keys.

## Vercel deployment (important for login)

1. Add these Vercel Environment Variables for Production/Preview:
   - `FLASK_SECRET_KEY`
   - `FIREBASE_API_KEY`
   - `FIREBASE_AUTH_DOMAIN`
   - `FIREBASE_PROJECT_ID`
   - `FIREBASE_STORAGE_BUCKET`
   - `FIREBASE_MESSAGING_SENDER_ID`
   - `FIREBASE_APP_ID`
   - `FIREBASE_MEASUREMENT_ID` (optional)
   - `FIREBASE_SERVICE_ACCOUNT_JSON` **or** `FIREBASE_SERVICE_ACCOUNT_B64` (preferred on Vercel)
2. Do **not** use a local file path for `GOOGLE_APPLICATION_CREDENTIALS` on Vercel.
3. In Firebase Console → Authentication → Settings → Authorized domains:
   - add your Vercel domain (e.g. `your-app.vercel.app`)
   - add custom domain too (if any)
4. Redeploy after changing env vars.

## API highlights

| Endpoint | Purpose |
|----------|---------|
| `GET /api/config` | Firebase + Cloudinary public config for the browser |
| `POST /api/auth/session` | Verify Firebase ID token; sync user doc |
| `GET /api/products` | List published products |
| `GET /api/products/slug/<slug>` | Product by slug |
| `POST /api/orders` | Create order (Bearer token required) |
| `POST /api/admin/products` | Create product (admin Bearer token) |

## Pages

All user and admin routes from your spec are registered. Core flows (home, shop, PDP, cart, checkout, auth, admin products with Cloudinary) are implemented; remaining sections ship as styled stubs you can connect to Firestore the same way as products.
