from dotenv import load_dotenv
import os

load_dotenv()

SERP_API_KEY = os.getenv("SERP_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")