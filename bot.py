import asyncio
import sys
from telegram.ext import Application
from config import BOT_TOKEN
from database import db
from handlers import handlers

async def main():
    await db.init()
    app = Application.builder().token(BOT_TOKEN).build()
    for h in handlers:
        app.add_handler(h)
    
    print("Бот запущен...")
    
    # Запускаем polling с явным указанием stop_signals
    await app.run_polling(stop_signals=None)

if __name__ == "__main__":
    # Используем более надёжный способ запуска, совместимый с разными средами
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")
        sys.exit(0)