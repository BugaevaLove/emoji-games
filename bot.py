import asyncio
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
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())