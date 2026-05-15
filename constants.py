import os

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "temp-vote-secret-key"
)

ADMIN_KEY = os.environ.get(
    "ADMIN_KEY",
    "temp-admin-2026"
)

MIN_TEMP = 18
MAX_TEMP = 30

RETRAIN_THRESHOLD = 10