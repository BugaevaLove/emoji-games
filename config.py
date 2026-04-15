import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

DB_NAME = "bot.db"

# Лимиты ставок (USDT)
MIN_BET = 0.1
MAX_BET = 75.0

# Целевой RTP
TARGET_RTP = 0.95

# VIP‑уровни
VIP_LEVELS = [
    {"turnover": 0,      "cashback": 3,  "rakeback": 1,   "reward": 0},
    {"turnover": 50,     "cashback": 4,  "rakeback": 2,   "reward": 2},
    {"turnover": 150,    "cashback": 5,  "rakeback": 3,   "reward": 3},
    {"turnover": 300,    "cashback": 6,  "rakeback": 4,   "reward": 5},
    {"turnover": 500,    "cashback": 7,  "rakeback": 5,   "reward": 8},
    {"turnover": 1000,   "cashback": 8,  "rakeback": 6,   "reward": 12},
    {"turnover": 2000,   "cashback": 9,  "rakeback": 7,   "reward": 18},
    {"turnover": 3500,   "cashback": 10, "rakeback": 8,   "reward": 25},
    {"turnover": 5500,   "cashback": 11, "rakeback": 9,   "reward": 35},
    {"turnover": 8000,   "cashback": 12, "rakeback": 10,  "reward": 50},
    {"turnover": 12000,  "cashback": 13, "rakeback": 11,  "reward": 70},
    {"turnover": 17000,  "cashback": 14, "rakeback": 11.5,"reward": 100},
    {"turnover": 25000,  "cashback": 15, "rakeback": 12,  "reward": 150},
]

REF_DEPOSIT_BONUS = 0.10
REF_TURNOVER_BONUS = 0.12
WAGER_MULTIPLIER = 3
MAX_GAMES_PER_MINUTE = 20
