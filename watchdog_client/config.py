import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 10))
