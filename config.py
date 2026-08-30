import os
import json
from pathlib import Path
from dotenv import load_dotenv

# .env yuklash
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

# Shaxsiy Telegram API parametrlari (my.telegram.org dan olingan)
DEFAULT_API_ID = int(os.getenv("TELEGRAM_API_ID", "32401527"))
DEFAULT_API_HASH = os.getenv("TELEGRAM_API_HASH", "c88b0711b301b60962a6bac11e6da0c2")

# Rasmiy Android parametrlari
DEVICE_MODEL = "Samsung Galaxy S24"
SYSTEM_VERSION = "Android 14"
APP_VERSION = "10.14.5"

# Bot sozlamalari
BOT_USERNAME = "XsollaRewardsBot"
BOT_APP_NAME = "app"

# Akkauntlar orasidagi kutish vaqti (soniya)
MIN_DELAY_BETWEEN_ACCOUNTS = int(os.getenv("MIN_DELAY_BETWEEN_ACCOUNTS", "15"))
MAX_DELAY_BETWEEN_ACCOUNTS = int(os.getenv("MAX_DELAY_BETWEEN_ACCOUNTS", "35"))

# Tasklar orasidagi kutish vaqti (soniya)
MIN_DELAY_BETWEEN_TASKS = int(os.getenv("MIN_DELAY_BETWEEN_TASKS", "3"))
MAX_DELAY_BETWEEN_TASKS = int(os.getenv("MAX_DELAY_BETWEEN_TASKS", "7"))

# Har kuni avtomatik ishga tushish vaqti
AUTO_RUN_TIME = os.getenv("AUTO_RUN_TIME", "03:00")

# Proxy sozlamalari fayli
PROXIES_FILE = BASE_DIR / "proxies.json"

def get_proxy_for_session(session_name: str) -> dict or None:
    """Sessiya uchun biriktirilgan proxy'ni oladi"""
    if PROXIES_FILE.exists():
        try:
            with open(PROXIES_FILE, "r", encoding="utf-8") as f:
                proxies = json.load(f)
                return proxies.get(session_name)
        except Exception:
            return None
    return None
