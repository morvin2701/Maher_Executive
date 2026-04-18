import os


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-change-me")
    FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "clothesecommerce-6e490")
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

    # Public Firebase Web SDK (injected into templates)
    FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "")
    FIREBASE_AUTH_DOMAIN = os.environ.get(
        "FIREBASE_AUTH_DOMAIN", "clothesecommerce-6e490.firebaseapp.com"
    )
    FIREBASE_STORAGE_BUCKET = os.environ.get(
        "FIREBASE_STORAGE_BUCKET", "clothesecommerce-6e490.appspot.com"
    )
    FIREBASE_MESSAGING_SENDER_ID = os.environ.get("FIREBASE_MESSAGING_SENDER_ID", "")
    FIREBASE_APP_ID = os.environ.get("FIREBASE_APP_ID", "")
    FIREBASE_MEASUREMENT_ID = os.environ.get("FIREBASE_MEASUREMENT_ID", "")

    # Cloudinary (unsigned upload from browser — no Firebase Storage)
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "dpp3e46eh")
    CLOUDINARY_UPLOAD_PRESET = os.environ.get("CLOUDINARY_UPLOAD_PRESET", "flutterflow_upload")
    CLOUDINARY_FOLDER = os.environ.get("CLOUDINARY_FOLDER", "clothesecommerce")

    # Razorpay (India)
    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
