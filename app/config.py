import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./shevaldina.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Админка (НОВОЕ)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# CORS_ORIGINS
_raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5500")
CORS_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]