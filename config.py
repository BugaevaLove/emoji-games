import os

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")

# Название файла базы данных
DB_NAME = "users.db"